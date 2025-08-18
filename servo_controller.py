#!/usr/bin/env python3
"""
Servo Controller Module
High-level controller for managing servo movements, sequences, and scheduling.
This module coordinates between the hardware interface and external commands.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import schedule

from servo_hardware import ServoHardware


@dataclass
class MovementStep:
    """Represents a single movement step in a sequence."""
    channel: int
    angle: float
    duration: float
    delay_after: float = 0.0  # Delay after this movement


@dataclass
class MovementSequence:
    """Represents a complete movement sequence."""
    name: str
    steps: List[MovementStep]
    repeat_count: int = 1
    repeat_delay: float = 0.0  # Delay between repetitions


class ServoController:
    """
    Main controller class for managing servo operations.
    Handles sequences, scheduling, and coordination of movements.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the servo controller.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize hardware interface
        self.hardware = ServoHardware(config)
        
        # Movement management
        self.sequences = {}  # Dictionary of named sequences
        self.active_movements = {}  # Currently active movements by channel
        self.movement_lock = threading.Lock()  # Thread safety for movements
        
        # Scheduling
        self.scheduler = schedule.Scheduler()
        self.schedule_thread = None
        self.schedule_running = False
        
        # Load predefined sequences from config
        self._load_sequences()
        
        # Start scheduler thread
        self._start_scheduler()
    
    def _load_sequences(self):
        """Load movement sequences from configuration."""
        try:
            if 'sequences' in self.config:
                for name, steps_data in self.config['sequences'].items():
                    steps = []
                    for step_data in steps_data:
                        step = MovementStep(
                            channel=step_data['channel'],
                            angle=step_data['angle'],
                            duration=step_data.get('duration', 0.0)
                        )
                        steps.append(step)
                    
                    sequence = MovementSequence(name=name, steps=steps)
                    self.sequences[name] = sequence
                    self.logger.info(f"Loaded sequence '{name}' with {len(steps)} steps")
            
            self.logger.info(f"Loaded {len(self.sequences)} sequences from configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to load sequences: {e}")
    
    def _start_scheduler(self):
        """Start the background scheduler thread."""
        try:
            self.schedule_running = True
            self.schedule_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
            self.schedule_thread.start()
            self.logger.info("Scheduler thread started")
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
    
    def _scheduler_worker(self):
        """Background worker for running scheduled tasks."""
        while self.schedule_running:
            try:
                self.scheduler.run_pending()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def move_servo(self, channel: int, angle: float, duration: float = 0.0) -> bool:
        """
        Move a single servo to a specified angle.
        
        Args:
            channel: Servo channel (0-15)
            angle: Target angle in degrees
            duration: Movement duration in seconds (0 = immediate)
            
        Returns:
            bool: True if movement successful, False otherwise
        """
        with self.movement_lock:
            # Check if servo is already moving
            if channel in self.active_movements:
                self.logger.warning(f"Servo {channel} is already moving, ignoring command")
                return False
            
            # Mark servo as moving
            self.active_movements[channel] = {
                'start_time': time.time(),
                'target_angle': angle,
                'duration': duration
            }
        
        try:
            # Execute movement
            success = self.hardware.move_servo(channel, angle, duration)
            
            if success:
                self.logger.info(f"Servo {channel} movement completed: {angle}°")
            else:
                self.logger.error(f"Servo {channel} movement failed")
            
            return success
            
        finally:
            # Remove from active movements
            with self.movement_lock:
                if channel in self.active_movements:
                    del self.active_movements[channel]
    
    def run_sequence(self, sequence_name: str, repeat_count: int = 1) -> bool:
        """
        Run a predefined movement sequence.
        
        Args:
            sequence_name: Name of the sequence to run
            repeat_count: Number of times to repeat the sequence
            
        Returns:
            bool: True if sequence started successfully, False otherwise
        """
        if sequence_name not in self.sequences:
            self.logger.error(f"Sequence '{sequence_name}' not found")
            return False
        
        # Start sequence in background thread
        thread = threading.Thread(
            target=self._execute_sequence,
            args=(sequence_name, repeat_count),
            daemon=True
        )
        thread.start()
        
        self.logger.info(f"Started sequence '{sequence_name}' with {repeat_count} repetitions")
        return True
    
    def _execute_sequence(self, sequence_name: str, repeat_count: int):
        """Execute a movement sequence in a background thread."""
        sequence = self.sequences[sequence_name]
        
        try:
            for repetition in range(repeat_count):
                self.logger.info(f"Executing sequence '{sequence_name}' repetition {repetition + 1}/{repeat_count}")
                
                for i, step in enumerate(sequence.steps):
                    # Check if we should stop
                    if not self.schedule_running:
                        break
                    
                    self.logger.debug(f"Executing step {i + 1}/{len(sequence.steps)}: "
                                   f"channel {step.channel} to {step.angle}°")
                    
                    # Execute movement
                    success = self.move_servo(step.channel, step.angle, step.duration)
                    
                    if not success:
                        self.logger.error(f"Step {i + 1} failed, stopping sequence")
                        break
                    
                    # Wait for specified delay after movement
                    if step.delay_after > 0:
                        time.sleep(step.delay_after)
                
                # Wait between repetitions
                if repetition < repeat_count - 1 and sequence.repeat_delay > 0:
                    time.sleep(sequence.repeat_delay)
            
            self.logger.info(f"Sequence '{sequence_name}' completed")
            
        except Exception as e:
            self.logger.error(f"Sequence '{sequence_name}' execution failed: {e}")
    
    def create_sequence(self, name: str, steps: List[Dict]) -> bool:
        """
        Create a new movement sequence dynamically.
        
        Args:
            name: Name for the new sequence
            steps: List of step dictionaries with channel, angle, duration
            
        Returns:
            bool: True if sequence created successfully, False otherwise
        """
        try:
            # Convert step dictionaries to MovementStep objects
            movement_steps = []
            for step_data in steps:
                step = MovementStep(
                    channel=step_data['channel'],
                    angle=step_data['angle'],
                    duration=step_data.get('duration', 0.0),
                    delay_after=step_data.get('delay_after', 0.0)
                )
                movement_steps.append(step)
            
            # Create and store sequence
            sequence = MovementSequence(name=name, steps=movement_steps)
            self.sequences[name] = sequence
            
            self.logger.info(f"Created new sequence '{name}' with {len(steps)} steps")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create sequence '{name}': {e}")
            return False
    
    def schedule_sequence(self, sequence_name: str, time_str: str, repeat_count: int = 1) -> bool:
        """
        Schedule a sequence to run at a specific time.
        
        Args:
            sequence_name: Name of the sequence to schedule
            time_str: Time string in HH:MM format
            repeat_count: Number of times to repeat the sequence
            
        Returns:
            bool: True if scheduled successfully, False otherwise
        """
        if sequence_name not in self.sequences:
            self.logger.error(f"Sequence '{sequence_name}' not found")
            return False
        
        try:
            # Schedule the sequence
            self.scheduler.every().day.at(time_str).do(
                self.run_sequence, sequence_name, repeat_count
            )
            
            self.logger.info(f"Scheduled sequence '{sequence_name}' at {time_str}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to schedule sequence '{sequence_name}': {e}")
            return False
    
    def schedule_recurring_sequence(self, sequence_name: str, interval_minutes: int, repeat_count: int = 1) -> bool:
        """
        Schedule a sequence to run at regular intervals.
        
        Args:
            sequence_name: Name of the sequence to schedule
            interval_minutes: Interval between runs in minutes
            repeat_count: Number of times to repeat each run
            
        Returns:
            bool: True if scheduled successfully, False otherwise
        """
        if sequence_name not in self.sequences:
            self.logger.error(f"Sequence '{sequence_name}' not found")
            return False
        
        try:
            # Schedule the sequence
            self.scheduler.every(interval_minutes).minutes.do(
                self.run_sequence, sequence_name, repeat_count
            )
            
            self.logger.info(f"Scheduled recurring sequence '{sequence_name}' every {interval_minutes} minutes")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to schedule recurring sequence '{sequence_name}': {e}")
            return False
    
    def emergency_stop(self) -> bool:
        """Emergency stop - stop all movements and release servos."""
        try:
            # Stop scheduler
            self.schedule_running = False
            
            # Clear all scheduled tasks
            self.scheduler.clear()
            
            # Stop all active movements
            with self.movement_lock:
                self.active_movements.clear()
            
            # Emergency stop hardware
            success = self.hardware.emergency_stop()
            
            if success:
                self.logger.warning("Emergency stop executed successfully")
            else:
                self.logger.error("Emergency stop failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Emergency stop error: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get comprehensive status of the controller system."""
        return {
            'controller': {
                'sequences_loaded': len(self.sequences),
                'active_movements': len(self.active_movements),
                'scheduler_running': self.schedule_running,
                'scheduled_jobs': len(self.scheduler.jobs)
            },
            'hardware': self.hardware.get_status(),
            'sequences': list(self.sequences.keys()),
            'active_movements': self.active_movements.copy()
        }
    
    def get_sequence_info(self, sequence_name: str) -> Optional[Dict]:
        """Get information about a specific sequence."""
        if sequence_name not in self.sequences:
            return None
        
        sequence = self.sequences[sequence_name]
        return {
            'name': sequence.name,
            'steps': [
                {
                    'channel': step.channel,
                    'angle': step.angle,
                    'duration': step.duration,
                    'delay_after': step.delay_after
                }
                for step in sequence.steps
            ],
            'repeat_count': sequence.repeat_count,
            'repeat_delay': sequence.repeat_delay
        }
    
    def cleanup(self):
        """Clean up controller resources."""
        try:
            # Stop scheduler
            self.schedule_running = False
            
            # Wait for scheduler thread to finish
            if self.schedule_thread and self.schedule_thread.is_alive():
                self.schedule_thread.join(timeout=5)
            
            # Clean up hardware
            self.hardware.cleanup()
            
            self.logger.info("Controller cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Controller cleanup failed: {e}")


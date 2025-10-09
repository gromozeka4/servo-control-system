#!/usr/bin/env python3
"""
XY Stepper Motor Hardware Interface Module
Handles direct communication with stepper motors and endstop switches via GPIO.
This module provides low-level control for the XY positioning system.
"""

import time
import threading
import logging
from typing import Dict, Optional, Tuple
import RPi.GPIO as GPIO


class XYStepperHardware:
    """
    Hardware interface class for controlling stepper motors and endstops.
    Handles GPIO communication, step generation, and endstop monitoring.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the XY stepper hardware interface.
        
        Args:
            config: Configuration dictionary containing hardware settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # GPIO pin configuration
        self.pins = config['xy_hardware']['pins']
        self.step_x = self.pins['step_x']
        self.dir_x = self.pins['dir_x']
        self.endstop_x = self.pins['endstop_x']
        self.step_y = self.pins['step_y']
        self.dir_y = self.pins['dir_y']
        self.endstop_y = self.pins['endstop_y']
        
        # Movement configuration
        self.step_delay = config['xy_hardware']['step_delay']
        self.homing_delay = config['xy_hardware']['homing_delay']
        self.homing_steps_back = config['xy_hardware']['homing_steps_back']
        
        # State tracking
        self.current_x = 0
        self.current_y = 0
        self.is_homed = False
        self.is_initialized = False
        self.stop_threads = False
        
        # Threading
        self.movement_lock = threading.Lock()
        self.active_movements = {'x': False, 'y': False}
        
        # Initialize hardware
        self._initialize_hardware()
    
    def _initialize_hardware(self):
        """Initialize GPIO pins and set up hardware."""
        try:
            self.logger.info("Initializing XY stepper hardware...")
            
            # Set GPIO mode
            GPIO.setmode(GPIO.BCM)
            
            # Setup step and direction pins
            GPIO.setup(self.step_x, GPIO.OUT)
            GPIO.setup(self.dir_x, GPIO.OUT)
            GPIO.setup(self.step_y, GPIO.OUT)
            GPIO.setup(self.dir_y, GPIO.OUT)
            
            # Setup endstop pins with pull-up resistors
            GPIO.setup(self.endstop_x, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.endstop_y, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Set initial directions (will be changed during homing)
            GPIO.output(self.dir_x, GPIO.LOW)
            GPIO.output(self.dir_y, GPIO.LOW)
            
            # Ensure step pins are low
            GPIO.output(self.step_x, GPIO.LOW)
            GPIO.output(self.step_y, GPIO.LOW)
            
            self.is_initialized = True
            self.logger.info("XY stepper hardware initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Hardware initialization failed: {e}")
            self.is_initialized = False
            raise
    
    def home_axes(self) -> bool:
        """
        Home both X and Y axes by moving to endstops and backing off.
        
        Returns:
            bool: True if homing successful, False otherwise
        """
        if not self.is_initialized:
            self.logger.error("Hardware not initialized")
            return False
        
        try:
            self.logger.info("Starting homing sequence...")
            self.stop_threads = False
            
            # Home X axis
            if not self._home_axis('x'):
                self.logger.error("X axis homing failed")
                return False
            
            # Home Y axis
            if not self._home_axis('y'):
                self.logger.error("Y axis homing failed")
                return False
            
            # Move back from endstops to establish home position
            self.logger.info("Moving back from endstops to establish home position...")
            self._move_axis_steps('x', -self.homing_steps_back)
            self._move_axis_steps('y', -self.homing_steps_back)
            
            # Reset position counters
            self.current_x = 0
            self.current_y = 0
            self.is_homed = True
            
            self.logger.info("Homing completed successfully - Position: (0, 0)")
            return True
            
        except Exception as e:
            self.logger.error(f"Homing failed: {e}")
            return False
    
    def _home_axis(self, axis: str) -> bool:
        """
        Home a single axis by moving until endstop is triggered.
        
        Args:
            axis: 'x' or 'y'
            
        Returns:
            bool: True if homing successful, False otherwise
        """
        step_pin = self.step_x if axis == 'x' else self.step_y
        dir_pin = self.dir_x if axis == 'x' else self.dir_y
        endstop_pin = self.endstop_x if axis == 'x' else self.endstop_y
        
        try:
            self.logger.info(f"Homing {axis.upper()} axis...")
            
            # Set direction for homing (move towards endstop)
            # X axis uses LOW, Y axis uses HIGH
            direction = GPIO.LOW if axis == 'x' else GPIO.HIGH
            GPIO.output(dir_pin, direction)
            self.logger.info(f"  Direction set to {'LOW' if direction == GPIO.LOW else 'HIGH'} for {axis.upper()} axis homing")
            
            # Move until endstop is triggered
            steps = 0
            max_steps = 10000  # Safety limit
            
            while not self.stop_threads and steps < max_steps:
                # Check if endstop is triggered (LOW = triggered due to pull-up)
                if GPIO.input(endstop_pin) == GPIO.LOW:
                    self.logger.info(f"{axis.upper()} axis endstop triggered after {steps} steps")
                    break
                
                # Generate step pulse
                GPIO.output(step_pin, GPIO.HIGH)
                time.sleep(self.homing_delay)
                GPIO.output(step_pin, GPIO.LOW)
                time.sleep(self.homing_delay)
                steps += 1
            else:
                if steps >= max_steps:
                    self.logger.error(f"{axis.upper()} axis homing timeout - max steps reached")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to home {axis.upper()} axis: {e}")
            return False
    
    def move_to(self, x: int, y: int) -> bool:
        """
        Move to absolute position (x, y) in steps.
        
        Args:
            x: Target X position in steps
            y: Target Y position in steps
            
        Returns:
            bool: True if movement successful, False otherwise
        """
        if not self.is_homed:
            self.logger.error("System not homed - cannot move to absolute position")
            return False
        
        if not self.is_initialized:
            self.logger.error("Hardware not initialized")
            return False
        
        try:
            with self.movement_lock:
                # Calculate relative movements needed
                dx = x - self.current_x
                dy = y - self.current_y
                
                self.logger.info(f"Moving to ({x}, {y}) - relative movement: ({dx}, {dy})")
                
                # Check for endstops before moving
                if self._check_endstops():
                    self.logger.error("Endstop triggered - movement aborted")
                    return False
                
                # Move both axes
                success = True
                if dx != 0:
                    success &= self._move_axis_steps('x', dx)
                if dy != 0:
                    success &= self._move_axis_steps('y', dy)
                
                if success:
                    self.current_x = x
                    self.current_y = y
                    self.logger.info(f"Movement completed - Position: ({x}, {y})")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Move to ({x}, {y}) failed: {e}")
            return False
    
    def move_relative(self, dx: int, dy: int) -> bool:
        """
        Move relative to current position.
        
        Args:
            dx: X movement in steps (positive or negative)
            dy: Y movement in steps (positive or negative)
            
        Returns:
            bool: True if movement successful, False otherwise
        """
        if not self.is_homed:
            self.logger.error("System not homed - cannot move")
            return False
        
        new_x = self.current_x + dx
        new_y = self.current_y + dy
        
        return self.move_to(new_x, new_y)
    
    def _move_axis_steps(self, axis: str, steps: int) -> bool:
        """
        Move a single axis by a specified number of steps.
        
        Args:
            axis: 'x' or 'y'
            steps: Number of steps (positive or negative)
            
        Returns:
            bool: True if movement successful, False otherwise
        """
        if steps == 0:
            return True
        
        step_pin = self.step_x if axis == 'x' else self.step_y
        dir_pin = self.dir_x if axis == 'x' else self.dir_y
        endstop_pin = self.endstop_x if axis == 'x' else self.endstop_y
        
        try:
            # Set direction based on step sign
            direction = GPIO.HIGH if steps > 0 else GPIO.LOW
            GPIO.output(dir_pin, direction)
            
            # Move the specified number of steps
            for _ in range(abs(steps)):
                if self.stop_threads:
                    self.logger.info(f"Movement stopped by user")
                    return False
                
                # Check for endstop during movement
                if GPIO.input(endstop_pin) == GPIO.LOW:
                    self.logger.warning(f"{axis.upper()} axis endstop triggered during movement")
                    return False
                
                # Generate step pulse
                GPIO.output(step_pin, GPIO.HIGH)
                time.sleep(self.step_delay)
                GPIO.output(step_pin, GPIO.LOW)
                time.sleep(self.step_delay)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move {axis.upper()} axis by {steps} steps: {e}")
            return False
    
    def _check_endstops(self) -> bool:
        """
        Check if any endstop is currently triggered.
        
        Returns:
            bool: True if any endstop is triggered, False otherwise
        """
        x_triggered = GPIO.input(self.endstop_x) == GPIO.LOW
        y_triggered = GPIO.input(self.endstop_y) == GPIO.LOW
        
        if x_triggered:
            self.logger.warning("X axis endstop is triggered")
        if y_triggered:
            self.logger.warning("Y axis endstop is triggered")
        
        return x_triggered or y_triggered
    
    def get_position(self) -> Tuple[int, int]:
        """
        Get current position.
        
        Returns:
            Tuple[int, int]: Current (x, y) position in steps
        """
        return (self.current_x, self.current_y)
    
    def is_homed(self) -> bool:
        """
        Check if system is homed.
        
        Returns:
            bool: True if system is homed, False otherwise
        """
        return self.is_homed
    
    def emergency_stop(self) -> bool:
        """Emergency stop - stop all movements immediately."""
        try:
            self.stop_threads = True
            self.logger.warning("Emergency stop executed")
            return True
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get comprehensive status of the XY hardware system."""
        return {
            'initialized': self.is_initialized,
            'homed': self.is_homed,
            'current_position': (self.current_x, self.current_y),
            'endstops': {
                'x_triggered': GPIO.input(self.endstop_x) == GPIO.LOW,
                'y_triggered': GPIO.input(self.endstop_y) == GPIO.LOW,
            },
            'pins': self.pins,
            'step_delay': self.step_delay,
            'homing_delay': self.homing_delay,
        }
    
    def cleanup(self):
        """Clean up hardware resources."""
        try:
            if self.is_initialized:
                self.stop_threads = True
                # Set all outputs to low
                GPIO.output(self.step_x, GPIO.LOW)
                GPIO.output(self.step_y, GPIO.LOW)
                GPIO.output(self.dir_x, GPIO.LOW)
                GPIO.output(self.dir_y, GPIO.LOW)
                self.logger.info("XY hardware cleanup completed")
            self.is_initialized = False
        except Exception as e:
            self.logger.error(f"XY hardware cleanup failed: {e}")

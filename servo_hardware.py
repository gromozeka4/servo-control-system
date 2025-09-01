#!/usr/bin/env python3
"""
Servo Hardware Interface Module
Handles direct communication with PCA9685 PWM controller and servo motors.
This module provides low-level control of the hardware components.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo


class ServoHardware:
    """
    Hardware interface class for controlling servos via PCA9685.
    Handles I2C communication, PWM generation, and servo movement.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the hardware interface.
        
        Args:
            config: Configuration dictionary containing hardware settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Hardware configuration
        self.i2c_bus = config['hardware']['i2c']['bus']
        self.i2c_address = config['hardware']['i2c']['address']
        self.pwm_frequency = config['hardware']['pca9685']['frequency']
        self.reference_clock = config['hardware']['pca9685']['reference_clock']
        
        # Servo configuration
        self.pulse_range = config['hardware']['servos']['pulse_range']
        self.angle_range = config['hardware']['servos']['angle_range']
        
        # Hardware objects
        self.i2c = None
        self.pca = None
        self.servos = {}  # Dictionary to store servo objects by channel
        
        # State tracking
        self.current_positions = {}  # Current angle of each servo
        self.is_initialized = False
        
        # Initialize hardware
        self._initialize_hardware()
    
    def _initialize_hardware(self):
        """Initialize I2C bus and PCA9685 controller."""
        try:
            self.logger.info(f"Initializing I2C bus {self.i2c_bus}...")
            
            # Initialize I2C bus
            if self.i2c_bus == 1:
                # Use default I2C pins (GPIO2/3)
                self.i2c = busio.I2C(board.SCL, board.SDA)
            else:
                # For custom I2C bus configuration
                self.i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
            
            self.logger.info(f"Connecting to PCA9685 at address 0x{self.i2c_address:02X}...")
            
            # Initialize PCA9685
            self.pca = PCA9685(
                self.i2c, 
                address=self.i2c_address,
                reference_clock_speed=self.reference_clock
            )
            
            # Set PWM frequency
            self.pca.frequency = self.pwm_frequency
            self.logger.info(f"PCA9685 initialized with {self.pwm_frequency}Hz PWM frequency")
            
            # Initialize servo objects for all channels (0-15)
            self._initialize_servos()
            
            self.is_initialized = True
            self.logger.info("Hardware initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Hardware initialization failed: {e}")
            self.is_initialized = False
            raise
    
    def _initialize_servos(self):
        """Initialize servo objects for all available channels."""
        try:
            for channel in range(16):  # PCA9685 has 16 channels
                # Create servo object for this channel
                servo_obj = servo.Servo(
                    self.pca.channels[channel],
                    min_pulse=self.pulse_range[0],
                    max_pulse=self.pulse_range[1],
                    actuation_range=self.angle_range[1] - self.angle_range[0]
                )
                
                self.servos[channel] = servo_obj
                self.current_positions[channel] = 0  # Default to 0 degrees
                
                # Set initial position to 0 degrees
                servo_obj.angle = 0
                
            self.logger.info(f"Initialized {len(self.servos)} servo channels")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize servos: {e}")
            raise
    
    def move_servo(self, channel: int, angle: float, duration: float = 0.0) -> bool:
        """
        Move a servo to a specific angle.
        
        Args:
            channel: Servo channel (0-15)
            angle: Target angle in degrees
            duration: Movement duration in seconds (0 = immediate)
            
        Returns:
            bool: True if movement successful, False otherwise
        """
        if not self.is_initialized:
            self.logger.error("Hardware not initialized")
            return False
        
        if channel not in self.servos:
            self.logger.error(f"Invalid servo channel: {channel}")
            return False
        
        # Validate angle range
        if not (self.angle_range[0] <= angle <= self.angle_range[1]):
            self.logger.error(f"Angle {angle}° out of range {self.angle_range}")
            return False
        
        try:
            # Get current position
            current_angle = self.current_positions.get(channel, 0)
            
            # Calculate movement parameters
            angle_diff = abs(angle - current_angle)
            
            if duration > 0:
                # Smooth movement over specified duration
                self._move_servo_smooth(channel, current_angle, angle, duration)
            else:
                # Immediate movement
                self.servos[channel].angle = angle
                self.current_positions[channel] = angle
                self.logger.info(f"Servo {channel} moved to {angle}°")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move servo {channel} to {angle}°: {e}")
            return False
    
    def _move_servo_smooth(self, channel: int, start_angle: float, end_angle: float, duration: float):
        """
        Move servo smoothly over a specified duration.
        
        Args:
            channel: Servo channel
            start_angle: Starting angle
            end_angle: Ending angle
            duration: Movement duration in seconds
        """
        steps = max(10, int(duration * 20))  # 20 steps per second minimum
        step_time = duration / steps
        
        for i in range(steps + 1):
            # Calculate intermediate angle
            progress = i / steps
            current_angle = start_angle + (end_angle - start_angle) * progress
            
            # Move servo to intermediate position
            self.servos[channel].angle = current_angle
            self.current_positions[channel] = current_angle
            
            # Wait for next step
            if i < steps:
                time.sleep(step_time)
        
        self.logger.info(f"Servo {channel} smoothly moved from {start_angle}° to {end_angle}° over {duration}s")
    
    def get_servo_position(self, channel: int) -> Optional[float]:
        """
        Get current position of a servo.
        
        Args:
            channel: Servo channel (0-15)
            
        Returns:
            float: Current angle in degrees, or None if invalid channel
        """
        if channel in self.current_positions:
            return self.current_positions[channel]
        return None
    
    def get_all_positions(self) -> Dict[int, float]:
        """Get current positions of all servos."""
        return self.current_positions.copy()
    
    def release_servo(self, channel: int) -> bool:
        """
        Release PWM signal to a servo (power off).
        
        Args:
            channel: Servo channel (0-15)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized or channel not in self.servos:
            return False
        
        try:
            # Set PWM to 0 to release servo
            self.pca.channels[channel].duty_cycle = 0
            self.logger.info(f"Released servo {channel}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to release servo {channel}: {e}")
            return False
    
    def release_all_servos(self) -> bool:
        """Release all servos (power off all PWM signals)."""
        try:
            for channel in range(16):
                self.pca.channels[channel].duty_cycle = 0
            
            self.logger.info("Released all servos")
            return True
        except Exception as e:
            self.logger.error(f"Failed to release all servos: {e}")
            return False
    
    def emergency_stop(self) -> bool:
        """Emergency stop - release all servos immediately."""
        try:
            self.release_all_servos()
            self.logger.warning("Emergency stop executed - all servos released")
            return True
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}")
            return False
    
    def is_servo_moving(self, channel: int) -> bool:
        """
        Check if a servo is currently moving.
        This is a simple implementation - you might want to enhance this.
        
        Args:
            channel: Servo channel (0-15)
            
        Returns:
            bool: True if servo is moving, False otherwise
        """
        # For now, we'll assume servos are not moving
        # You could implement actual movement detection if needed
        return False
    
    def cleanup(self):
        """Clean up hardware resources."""
        try:
            if self.is_initialized:
                self.release_all_servos()
                self.logger.info("Hardware cleanup completed")
            self.is_initialized = False
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    def get_status(self) -> Dict:
        """Get comprehensive status of the hardware system."""
        return {
            'initialized': self.is_initialized,
            'i2c_bus': self.i2c_bus,
            'i2c_address': f"0x{self.i2c_address:02X}",
            'pwm_frequency': self.pwm_frequency,
            'servo_count': len(self.servos),
            'current_positions': self.current_positions,
            'pulse_range': self.pulse_range,
            'angle_range': self.angle_range
        }


#!/usr/bin/env python3
"""
XY Positioning Controller Module
High-level controller for managing XY positioning system with stepper motors.
This module coordinates movement, homing, and position tracking.
"""

import time
import threading
import logging
from typing import Dict, Optional, Tuple

from xy_hardware import XYStepperHardware


class XYController:
    """
    Main controller class for managing XY positioning operations.
    Handles homing, movement, and button grid positioning.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the XY controller.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize hardware interface
        self.hardware = XYStepperHardware(config['xy_system'])
        
        # Movement management
        self.movement_lock = threading.Lock()
        self.is_moving = False
        
        self.logger.info("XY Controller initialized")
    
    
    def initialize_system(self) -> bool:
        """
        Initialize the XY system by homing both axes.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing XY positioning system...")
            
            # Home the axes
            if not self.hardware.home_axes():
                self.logger.error("Failed to home axes")
                return False
            
            self.logger.info("XY positioning system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
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
        with self.movement_lock:
            if self.is_moving:
                self.logger.warning("System is already moving, ignoring command")
                return False
            
            self.is_moving = True
        
        try:
            success = self.hardware.move_to(x, y)
            return success
            
        finally:
            with self.movement_lock:
                self.is_moving = False
    
    def move_relative(self, dx: int, dy: int) -> bool:
        """
        Move relative to current position.
        
        Args:
            dx: X movement in steps (positive or negative)
            dy: Y movement in steps (positive or negative)
            
        Returns:
            bool: True if movement successful, False otherwise
        """
        with self.movement_lock:
            if self.is_moving:
                self.logger.warning("System is already moving, ignoring command")
                return False
            
            self.is_moving = True
        
        try:
            success = self.hardware.move_relative(dx, dy)
            return success
            
        finally:
            with self.movement_lock:
                self.is_moving = False
    
    def get_position(self) -> Tuple[int, int]:
        """
        Get current position.
        
        Returns:
            Tuple[int, int]: Current (x, y) position in steps
        """
        return self.hardware.get_position()
    
    
    def is_system_ready(self) -> bool:
        """
        Check if the system is ready for operations.
        
        Returns:
            bool: True if system is ready, False otherwise
        """
        return self.hardware.is_system_homed() and not self.is_moving
    
    def emergency_stop(self) -> bool:
        """Emergency stop - stop all movements immediately."""
        try:
            with self.movement_lock:
                self.is_moving = False
            
            success = self.hardware.emergency_stop()
            
            if success:
                self.logger.warning("Emergency stop executed successfully")
            else:
                self.logger.error("Emergency stop failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Emergency stop error: {e}")
            return False
    
    def release_steppers(self) -> bool:
        """Release stepper motors - set all control pins low."""
        try:
            success = self.hardware.release_steppers()
            
            if success:
                self.logger.info("Stepper motors released successfully")
            else:
                self.logger.error("Failed to release stepper motors")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Release steppers error: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get comprehensive status of the XY controller system."""
        current_pos = self.get_position()
        
        return {
            'controller': {
                'initialized': True,
                'is_moving': self.is_moving,
                'is_ready': self.is_system_ready(),
            },
            'hardware': self.hardware.get_status(),
            'current_position': {
                'x': current_pos[0],
                'y': current_pos[1],
            },
        }
    
    def cleanup(self):
        """Clean up controller resources."""
        try:
            # Stop any ongoing movements
            with self.movement_lock:
                self.is_moving = False
            
            # Clean up hardware
            self.hardware.cleanup()
            
            self.logger.info("XY Controller cleanup completed")
            
        except Exception as e:
            self.logger.error(f"XY Controller cleanup failed: {e}")

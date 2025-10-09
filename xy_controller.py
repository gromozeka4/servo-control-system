#!/usr/bin/env python3
"""
XY Positioning Controller Module
High-level controller for managing XY positioning system with stepper motors.
This module coordinates movement, homing, and position tracking.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from xy_hardware import XYStepperHardware


@dataclass
class ButtonPosition:
    """Represents a button position in the grid."""
    row: int
    col: int
    x_steps: int
    y_steps: int


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
        
        # Button grid configuration
        self.grid_config = config['xy_system']['button_grid']
        self.grid_spacing_x = self.grid_config['spacing_x']
        self.grid_spacing_y = self.grid_config['spacing_y']
        self.grid_rows = self.grid_config['rows']
        self.grid_cols = self.grid_config['cols']
        self.grid_origin_x = self.grid_config.get('origin_x', 0)
        self.grid_origin_y = self.grid_config.get('origin_y', 0)
        
        # Initialize button positions
        self.button_positions = self._calculate_button_positions()
        
        self.logger.info("XY Controller initialized")
        self.logger.info(f"Button grid: {self.grid_rows}x{self.grid_cols} with spacing ({self.grid_spacing_x}, {self.grid_spacing_y})")
    
    def _calculate_button_positions(self) -> List[ButtonPosition]:
        """Calculate positions for all buttons in the grid."""
        positions = []
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x_steps = self.grid_origin_x - col * self.grid_spacing_x  # X decreases as column increases
                y_steps = self.grid_origin_y - row * self.grid_spacing_y  # Y decreases as row increases
                
                position = ButtonPosition(
                    row=row,
                    col=col,
                    x_steps=x_steps,
                    y_steps=y_steps,
                )
                positions.append(position)
        
        self.logger.info(f"Calculated {len(positions)} button positions")
        return positions
    
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
    
    def move_to_button(self, row: int, col: int) -> bool:
        """
        Move to a specific button position in the grid.
        
        Args:
            row: Button row (0-based)
            col: Button column (0-based)
            
        Returns:
            bool: True if movement successful, False otherwise
        """
        # Validate grid coordinates
        if not (0 <= row < self.grid_rows and 0 <= col < self.grid_cols):
            self.logger.error(f"Invalid button coordinates: ({row}, {col})")
            return False
        
        # Find button position
        button_pos = None
        for pos in self.button_positions:
            if pos.row == row and pos.col == col:
                button_pos = pos
                break
        
        if not button_pos:
            self.logger.error(f"Button position not found: ({row}, {col})")
            return False
        
        self.logger.info(f"Moving to button ({row}, {col}) at position ({button_pos.x_steps}, {button_pos.y_steps})")
        return self.move_to(button_pos.x_steps, button_pos.y_steps)
    
    def get_button_position(self, row: int, col: int) -> Optional[Tuple[int, int]]:
        """
        Get the step coordinates for a specific button.
        
        Args:
            row: Button row (0-based)
            col: Button column (0-based)
            
        Returns:
            Optional[Tuple[int, int]]: (x, y) step coordinates, or None if invalid
        """
        if not (0 <= row < self.grid_rows and 0 <= col < self.grid_cols):
            return None
        
        for pos in self.button_positions:
            if pos.row == row and pos.col == col:
                return (pos.x_steps, pos.y_steps)
        
        return None
    
    def get_all_button_positions(self) -> List[Dict]:
        """
        Get all button positions in the grid.
        
        Returns:
            List[Dict]: List of button position dictionaries
        """
        return [
            {
                'row': pos.row,
                'col': pos.col,
                'x_steps': pos.x_steps,
                'y_steps': pos.y_steps,
            }
            for pos in self.button_positions
        ]
    
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
            'button_grid': {
                'rows': self.grid_rows,
                'cols': self.grid_cols,
                'spacing_x': self.grid_spacing_x,
                'spacing_y': self.grid_spacing_y,
                'total_buttons': len(self.button_positions),
            },
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

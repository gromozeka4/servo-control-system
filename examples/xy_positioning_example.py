#!/usr/bin/env python3
"""
XY Positioning System Example
Demonstrates basic usage of the XY positioning system.
This example shows how to use the XY controller for simple movements.
"""

import os
import sys
import time
import logging
import yaml

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.xy_controller import XYController


def main():
    """Main example function."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Initialize XY controller
        logger.info("Initializing XY positioning system...")
        xy_controller = XYController(config)
        
        # Initialize system (home both axes)
        logger.info("Homing system...")
        if not xy_controller.initialize_system():
            logger.error("Failed to initialize XY system")
            return
        
        logger.info("System initialized successfully!")
        
        # Example 1: Move to absolute positions
        logger.info("\n--- Example 1: Absolute Movement ---")
        positions = [(100, 100), (200, 150), (50, 200), (0, 0)]
        
        for x, y in positions:
            logger.info(f"Moving to ({x}, {y})...")
            if xy_controller.move_to(x, y):
                current_pos = xy_controller.get_position()
                logger.info(f"  Current position: ({current_pos[0]}, {current_pos[1]})")
            else:
                logger.error(f"  Failed to move to ({x}, {y})")
            time.sleep(1)
        
        # Example 2: Relative movement
        logger.info("\n--- Example 2: Relative Movement ---")
        movements = [(50, 0), (0, 50), (-25, 0), (0, -25)]
        
        for dx, dy in movements:
            logger.info(f"Moving relative by ({dx}, {dy})...")
            if xy_controller.move_relative(dx, dy):
                current_pos = xy_controller.get_position()
                logger.info(f"  Current position: ({current_pos[0]}, {current_pos[1]})")
            else:
                logger.error(f"  Failed to move relative by ({dx}, {dy})")
            time.sleep(0.5)
        
        # Example 3: Button grid positioning
        logger.info("\n--- Example 3: Button Grid Positioning ---")
        buttons = [(0, 0), (1, 1), (2, 2), (3, 3), (0, 0)]
        
        for row, col in buttons:
            logger.info(f"Moving to button ({row}, {col})...")
            if xy_controller.move_to_button(row, col):
                current_pos = xy_controller.get_position()
                logger.info(f"  Current position: ({current_pos[0]}, {current_pos[1]})")
            else:
                logger.error(f"  Failed to move to button ({row}, {col})")
            time.sleep(1)
        
        # Example 4: Get system information
        logger.info("\n--- Example 4: System Information ---")
        status = xy_controller.get_status()
        logger.info(f"System ready: {status['controller']['is_ready']}")
        logger.info(f"Is homed: {status['hardware']['homed']}")
        logger.info(f"Button grid: {status['button_grid']['rows']}x{status['button_grid']['cols']}")
        
        # Get all button positions
        button_positions = xy_controller.get_all_button_positions()
        logger.info(f"Button positions:")
        for pos in button_positions:
            logger.info(f"  Button ({pos['row']}, {pos['col']}): ({pos['x_steps']}, {pos['y_steps']})")
        
        logger.info("\nExample completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Example interrupted by user")
    except Exception as e:
        logger.error(f"Example failed: {e}")
    finally:
        # Cleanup
        try:
            xy_controller.cleanup()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


if __name__ == "__main__":
    main()








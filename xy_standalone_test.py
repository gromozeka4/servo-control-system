#!/usr/bin/env python3
"""
XY Positioning System Standalone Test
This script demonstrates the XY positioning system using the same GPIO pins
as the original base script, but with the new architecture.
"""

import os
import sys
import time
import logging
import yaml
import signal

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xy_controller import XYController


def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, initiating shutdown...")
    global shutdown_requested
    shutdown_requested = True


def main():
    """Main test function."""
    global shutdown_requested
    shutdown_requested = False
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set up logging
    logger = setup_logging()
    logger.info("Starting XY Positioning System Standalone Test")
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Initialize XY controller
        logger.info("Initializing XY controller...")
        xy_controller = XYController(config)
        
        # Initialize system (home both axes)
        logger.info("Homing both axes...")
        if not xy_controller.initialize_system():
            logger.error("Failed to initialize XY system")
            return
        
        logger.info("✓ System homed successfully - Position: (0, 0)")
        
        # Test basic movements
        logger.info("\nTesting basic movements...")
        
        # Move to some test positions
        test_positions = [
            (100, 100),
            (200, 150),
            (50, 200),
            (0, 0),
        ]
        
        for x, y in test_positions:
            if shutdown_requested:
                break
                
            logger.info(f"Moving to ({x}, {y})...")
            if xy_controller.move_to(x, y):
                current_pos = xy_controller.get_position()
                logger.info(f"  Current position: ({current_pos[0]}, {current_pos[1]})")
            else:
                logger.error(f"  Failed to move to ({x}, {y})")
            time.sleep(1)
        
        # Test button grid
        logger.info("\nTesting button grid positioning...")
        buttons = [(0, 0), (1, 1), (2, 2), (3, 3), (0, 0)]
        
        for row, col in buttons:
            if shutdown_requested:
                break
                
            logger.info(f"Moving to button ({row}, {col})...")
            if xy_controller.move_to_button(row, col):
                current_pos = xy_controller.get_position()
                logger.info(f"  Current position: ({current_pos[0]}, {current_pos[1]})")
            else:
                logger.error(f"  Failed to move to button ({row}, {col})")
            time.sleep(1)
        
        # Show system status
        logger.info("\nSystem Status:")
        status = xy_controller.get_status()
        logger.info(f"  Ready: {status['controller']['is_ready']}")
        logger.info(f"  Homed: {status['hardware']['homed']}")
        logger.info(f"  Button grid: {status['button_grid']['rows']}x{status['button_grid']['cols']}")
        
        logger.info("\n✓ All tests completed successfully!")
        logger.info("Press Ctrl+C to stop safely")
        
        # Keep running until interrupted
        while not shutdown_requested:
            time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        try:
            xy_controller.cleanup()
            logger.info("✓ Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


if __name__ == "__main__":
    main()

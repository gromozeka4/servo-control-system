#!/usr/bin/env python3
"""
XY Positioning System Test Script
Tests the XY positioning system with stepper motors and endstops.
This script can be run independently to test the hardware.
"""

import os
import sys
import time
import logging
import yaml
import signal
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xy_controller import XYController


def setup_logging():
    """Set up logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def load_config():
    """Load configuration from YAML file."""
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Try to load local config if it exists
        if os.path.exists('config.local.yaml'):
            with open('config.local.yaml', 'r') as file:
                local_config = yaml.safe_load(file)
                if local_config:
                    # Simple merge for local overrides
                    for key, value in local_config.items():
                        config[key] = value
        
        return config
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, initiating shutdown...")
    global shutdown_requested
    shutdown_requested = True


def test_homing(xy_controller, logger):
    """Test the homing sequence."""
    logger.info("Testing homing sequence...")
    
    success = xy_controller.initialize_system()
    if success:
        logger.info("✓ Homing completed successfully")
        position = xy_controller.get_position()
        logger.info(f"  Current position: ({position[0]}, {position[1]})")
        return True
    else:
        logger.error("✗ Homing failed")
        return False


def test_absolute_movement(xy_controller, logger):
    """Test absolute movement commands."""
    logger.info("Testing absolute movement...")
    
    # Test movements to different positions
    test_positions = [
        (100, 100),
        (200, 150),
        (50, 200),
        (0, 0),  # Return to home
    ]
    
    for x, y in test_positions:
        logger.info(f"  Moving to ({x}, {y})...")
        success = xy_controller.move_to(x, y)
        
        if success:
            position = xy_controller.get_position()
            logger.info(f"  ✓ Moved to ({position[0]}, {position[1]})")
        else:
            logger.error(f"  ✗ Failed to move to ({x}, {y})")
            return False
        
        time.sleep(1)  # Pause between movements
    
    logger.info("✓ Absolute movement test completed")
    return True


def test_relative_movement(xy_controller, logger):
    """Test relative movement commands."""
    logger.info("Testing relative movement...")
    
    # Test relative movements
    test_movements = [
        (50, 0),   # Move right
        (0, 50),   # Move up
        (-25, 0),  # Move left
        (0, -25),  # Move down
    ]
    
    for dx, dy in test_movements:
        logger.info(f"  Moving relative by ({dx}, {dy})...")
        success = xy_controller.move_relative(dx, dy)
        
        if success:
            position = xy_controller.get_position()
            logger.info(f"  ✓ Moved to ({position[0]}, {position[1]})")
        else:
            logger.error(f"  ✗ Failed to move relative by ({dx}, {dy})")
            return False
        
        time.sleep(0.5)  # Pause between movements
    
    logger.info("✓ Relative movement test completed")
    return True


def test_button_grid(xy_controller, logger):
    """Test button grid positioning."""
    logger.info("Testing button grid positioning...")
    
    # Test moving to different buttons in the grid
    test_buttons = [
        (0, 0),  # Top-left
        (1, 1),  # Center-ish
        (2, 3),  # Bottom-right
        (3, 0),  # Bottom-left
        (0, 3),  # Top-right
        (0, 0),  # Back to home
    ]
    
    for row, col in test_buttons:
        logger.info(f"  Moving to button ({row}, {col})...")
        success = xy_controller.move_to_button(row, col)
        
        if success:
            position = xy_controller.get_position()
            logger.info(f"  ✓ Moved to button ({row}, {col}) at position ({position[0]}, {position[1]})")
        else:
            logger.error(f"  ✗ Failed to move to button ({row}, {col})")
            return False
        
        time.sleep(1)  # Pause between movements
    
    logger.info("✓ Button grid test completed")
    return True


def test_status_and_info(xy_controller, logger):
    """Test status and information retrieval."""
    logger.info("Testing status and information retrieval...")
    
    # Test status
    status = xy_controller.get_status()
    logger.info(f"  System status: {status['controller']['is_ready']}")
    logger.info(f"  Is homed: {status['hardware']['homed']}")
    logger.info(f"  Current position: {status['current_position']}")
    
    # Test button positions
    button_positions = xy_controller.get_all_button_positions()
    logger.info(f"  Button grid: {status['button_grid']['rows']}x{status['button_grid']['cols']}")
    logger.info(f"  Total buttons: {len(button_positions)}")
    
    # Show first few button positions
    for i, pos in enumerate(button_positions[:4]):
        logger.info(f"    Button ({pos['row']}, {pos['col']}): ({pos['x_steps']}, {pos['y_steps']})")
    
    logger.info("✓ Status and information test completed")
    return True


def main():
    """Main test function."""
    global shutdown_requested
    shutdown_requested = False
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set up logging
    logger = setup_logging()
    logger.info("Starting XY Positioning System Test")
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        
        # Initialize XY controller
        logger.info("Initializing XY controller...")
        xy_controller = XYController(config)
        
        # Run tests
        tests = [
            ("Homing", test_homing),
            ("Absolute Movement", test_absolute_movement),
            ("Relative Movement", test_relative_movement),
            ("Button Grid", test_button_grid),
            ("Status and Info", test_status_and_info),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if shutdown_requested:
                logger.info("Shutdown requested, stopping tests")
                break
            
            logger.info(f"\n--- Running {test_name} Test ---")
            try:
                if test_func(xy_controller, logger):
                    logger.info(f"✓ {test_name} test PASSED")
                    passed += 1
                else:
                    logger.error(f"✗ {test_name} test FAILED")
            except Exception as e:
                logger.error(f"✗ {test_name} test ERROR: {e}")
        
        # Summary
        logger.info(f"\n--- Test Summary ---")
        logger.info(f"Passed: {passed}/{total}")
        logger.info(f"Failed: {total - passed}/{total}")
        
        if passed == total:
            logger.info("🎉 All tests passed!")
        else:
            logger.warning("⚠️  Some tests failed")
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        try:
            xy_controller.cleanup()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        
        logger.info("Test completed")


if __name__ == "__main__":
    main()

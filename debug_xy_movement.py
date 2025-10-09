#!/usr/bin/env python3
"""
Debug XY Movement Test
Simple test to verify simultaneous movement is working.
"""

import os
import sys
import time
import logging
import yaml

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xy_controller import XYController


def main():
    """Debug XY movement."""
    # Set up detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Initialize XY controller
        logger.info("Initializing XY controller...")
        xy_controller = XYController(config['xy_system'])
        
        # Initialize system (home both axes)
        logger.info("Homing system...")
        if not xy_controller.initialize_system():
            logger.error("Failed to initialize XY system")
            return
        
        logger.info("System initialized successfully!")
        
        # Test 1: Move to (100, 100) - should use simultaneous movement
        logger.info("\n=== Test 1: Diagonal movement (100, 100) ===")
        logger.info("This should use simultaneous movement...")
        success = xy_controller.move_to(100, 100)
        logger.info(f"Result: {'SUCCESS' if success else 'FAILED'}")
        
        time.sleep(2)
        
        # Test 2: Move to (200, 200) - should use simultaneous movement
        logger.info("\n=== Test 2: Diagonal movement (200, 200) ===")
        logger.info("This should use simultaneous movement...")
        success = xy_controller.move_to(200, 200)
        logger.info(f"Result: {'SUCCESS' if success else 'FAILED'}")
        
        time.sleep(2)
        
        # Test 3: Move to (200, 100) - should use simultaneous movement
        logger.info("\n=== Test 3: Diagonal movement (200, 100) ===")
        logger.info("This should use simultaneous movement...")
        success = xy_controller.move_to(200, 100)
        logger.info(f"Result: {'SUCCESS' if success else 'FAILED'}")
        
        time.sleep(2)
        
        # Test 4: Move to (0, 0) - should use simultaneous movement
        logger.info("\n=== Test 4: Return to home (0, 0) ===")
        logger.info("This should use simultaneous movement...")
        success = xy_controller.move_to(0, 0)
        logger.info(f"Result: {'SUCCESS' if success else 'FAILED'}")
        
        logger.info("\n=== Debug test completed ===")
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        # Cleanup
        try:
            xy_controller.cleanup()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


if __name__ == "__main__":
    main()

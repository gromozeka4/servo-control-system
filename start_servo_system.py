#!/usr/bin/env python3
"""
Startup Script for Servo Control System
Provides options to run different components of the system.
"""

import os
import sys
import yaml
import argparse
import logging
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from servo_controller import ServoController
from xy_controller import XYController
from api_server import ServoAPIServer
from web_interface import WebInterface


def setup_logging():
    """Set up basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('servo_system.log')
        ]
    )


def load_config(config_path='config.yaml'):
    """Load configuration file."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)


def run_hardware_only(config):
    """Run only the hardware interface (no API or web interface)."""
    print("Starting hardware-only mode...")
    print("Press Ctrl+C to stop")
    
    try:
        servo_controller = ServoController(config)
        xy_controller = XYController(config)
        
        print("Initializing XY positioning system...")
        if xy_controller.initialize_system():
            print("✓ XY positioning system ready")
        else:
            print("⚠️  XY positioning system initialization failed")
        
        print("Hardware interface ready. Use Ctrl+C to stop.")
        
        # Keep running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        servo_controller.cleanup()
        xy_controller.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def run_with_api(config):
    """Run with HTTP API server."""
    print("Starting with HTTP API server...")
    print("API will be available at http://0.0.0.0:5000")
    print("Press Ctrl+C to stop")
    
    try:
        servo_controller = ServoController(config)
        xy_controller = XYController(config)
        
        print("Initializing XY positioning system...")
        if xy_controller.initialize_system():
            print("✓ XY positioning system ready")
        else:
            print("⚠️  XY positioning system initialization failed")
        
        api_server = ServoAPIServer(config, servo_controller, xy_controller)
        
        if api_server.start():
            print("API server started successfully")
        else:
            print("Failed to start API server")
            return
        
        # Keep running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        if 'api_server' in locals():
            api_server.stop()
        if 'servo_controller' in locals():
            servo_controller.cleanup()
        if 'xy_controller' in locals():
            xy_controller.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def run_with_web_interface(config):
    """Run with web interface."""
    print("Starting with web interface...")
    print("Web interface will be available at http://0.0.0.0:8080")
    print("Press Ctrl+C to stop")
    
    try:
        servo_controller = ServoController(config)
        xy_controller = XYController(config)
        
        print("Initializing XY positioning system...")
        if xy_controller.initialize_system():
            print("✓ XY positioning system ready")
        else:
            print("⚠️  XY positioning system initialization failed")
        
        web_interface = WebInterface(config, servo_controller)
        
        print("Web interface started successfully")
        web_interface.run(port=8080)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        if 'servo_controller' in locals():
            servo_controller.cleanup()
        if 'xy_controller' in locals():
            xy_controller.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def run_xy_only(config):
    """Run only the XY positioning system."""
    print("Starting XY positioning system only...")
    print("Press Ctrl+C to stop")
    
    try:
        xy_controller = XYController(config)
        
        print("Initializing XY positioning system...")
        if xy_controller.initialize_system():
            print("✓ XY positioning system ready")
            print("System is homed and ready for positioning")
        else:
            print("⚠️  XY positioning system initialization failed")
            return
        
        # Keep running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        xy_controller.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def run_full_system(config):
    """Run the full system with both API and web interface."""
    print("Starting full system...")
    print("API server: http://0.0.0.0:5000")
    print("Web interface: http://0.0.0.0:8080")
    print("Press Ctrl+C to stop")
    
    try:
        servo_controller = ServoController(config)
        xy_controller = XYController(config)
        
        print("Initializing XY positioning system...")
        if xy_controller.initialize_system():
            print("✓ XY positioning system ready")
        else:
            print("⚠️  XY positioning system initialization failed")
        
        # Start API server in background
        api_server = ServoAPIServer(config, servo_controller, xy_controller)
        if api_server.start():
            print("API server started successfully")
        else:
            print("Failed to start API server")
            return
        
        # Start web interface (this will block)
        web_interface = WebInterface(config, servo_controller)
        print("Web interface started successfully")
        web_interface.run(port=8080)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        if 'api_server' in locals():
            api_server.stop()
        if 'servo_controller' in locals():
            servo_controller.cleanup()
        if 'xy_controller' in locals():
            xy_controller.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description="Servo Control System Startup")
    parser.add_argument(
        '--mode',
        choices=['hardware', 'api', 'web', 'xy', 'full'],
        default='full',
        help='Run mode: hardware (servo only), api (servo+xy+api), web (servo+xy+web), xy (xy only), full (servo+xy+api+web) (default: full)'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run hardware test before starting'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Load configuration
    print(f"Loading configuration from {args.config}...")
    config = load_config(args.config)
    
    # Run hardware test if requested
    if args.test:
        print("Running hardware test...")
        try:
            from test_servo import main as test_main
            test_main()
            print("Hardware test completed. Starting main system...")
        except Exception as e:
            print(f"Hardware test failed: {e}")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    
    # Start system based on mode
    if args.mode == 'hardware':
        run_hardware_only(config)
    elif args.mode == 'api':
        run_with_api(config)
    elif args.mode == 'web':
        run_with_web_interface(config)
    elif args.mode == 'xy':
        run_xy_only(config)
    elif args.mode == 'full':
        run_full_system(config)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Main Application Entry Point
Initializes and runs the complete servo control system.
This is the main script to run on the Raspberry Pi.
"""

import os
import sys
import signal
import threading
import time
import logging
import yaml
import argparse
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.servo_controller import ServoController
from controllers.xy_controller import XYController
from server.api_server import ServoAPIServer
from utils.network_utils import NetworkManager


def setup_logging(config: dict) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_level = getattr(logging, config['logging']['level'].upper())
    log_file = log_dir / config['logging']['file']
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config['logging']['max_size_mb'] * 1024 * 1024,
        backupCount=config['logging']['backup_count']
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create and return main logger
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    
    return logger


def load_config(config_path: str = "config.yaml") -> dict:
    """
    Load configuration from YAML file and merge with local config.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        dict: Configuration dictionary with local overrides
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    try:
        # Load main configuration
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Validate required configuration sections
        required_sections = ['hardware', 'api', 'logging', 'safety']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Try to load and merge local configuration
        local_config_path = "config.local.yaml"
        if os.path.exists(local_config_path):
            try:
                with open(local_config_path, 'r') as file:
                    local_config = yaml.safe_load(file)
                
                if local_config:
                    # Merge local config with main config
                    config = merge_configs(config, local_config)
                    print(f"✓ Local configuration loaded from {local_config_path}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to load local config: {e}")
                print("   Continuing with main configuration only")
        
        return config
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in configuration file: {e}")


def merge_configs(main_config: dict, local_config: dict) -> dict:
    """
    Recursively merge local configuration with main configuration.
    
    Args:
        main_config: Main configuration dictionary
        local_config: Local configuration dictionary
        
    Returns:
        dict: Merged configuration
    """
    merged = main_config.copy()
    
    for key, value in local_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_configs(merged[key], value)
        else:
            # Override or add local value
            merged[key] = value
    
    return merged


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, initiating shutdown...")
    
    # Set global shutdown flag
    global shutdown_requested
    shutdown_requested = True


def main():
    """Main application entry point."""
    global shutdown_requested
    shutdown_requested = False
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Servo Control System")
    parser.add_argument(
        '--config', 
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--no-api',
        action='store_true',
        help='Run without HTTP API server'
    )
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='Run in test mode with limited functionality'
    )
    
    args = parser.parse_args()
    
    # Initialize system
    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config(args.config)
        
        # Setup logging
        logger = setup_logging(config)
        logger.info("Starting Servo Control System")
        logger.info(f"Configuration loaded from: {args.config}")
        
        # Initialize network manager
        logger.info("Initializing network manager...")
        network_manager = NetworkManager(config)
        network_info = network_manager.get_network_info()
        logger.info(f"Network configured: {network_info['current_address']} ({network_info['address_type']})")
        if network_info['resolved_ip']:
            logger.info(f"Resolved IP: {network_info['resolved_ip']}")
        
        # Initialize servo controller
        logger.info("Initializing servo controller...")
        servo_controller = ServoController(config)
        logger.info("Servo controller initialized successfully")
        
        # Initialize XY positioning controller
        logger.info("Initializing XY positioning controller...")
        xy_controller = XYController(config)
        logger.info("XY positioning controller initialized successfully")
        
        # Initialize API server (if enabled) *before* XY homing so the API is responsive immediately.
        # XY homing can block for a long time or hang if endstops are not connected.
        api_server = None
        if not args.no_api:
            logger.info("Initializing API server...")
            api_server = ServoAPIServer(config, servo_controller, xy_controller)
            if api_server.start():
                logger.info("API server started successfully")
                logger.info(f"API available at: {network_manager.get_api_base_url()}")
                logger.info(f"Web interface available at: {network_manager.get_web_url()}")
            else:
                logger.error("Failed to start API server")
                api_server = None
        
        # Initialize XY system in background so it does not block API requests.
        # If homing fails (e.g. no XY hardware or endstops), servo and API still work.
        def xy_init_background():
            logger.info("Initializing XY positioning system (background)...")
            try:
                if xy_controller.initialize_system():
                    logger.info("XY positioning system initialized successfully")
                else:
                    logger.warning("XY positioning system initialization failed; XY endpoints may be unavailable")
            except Exception as e:
                logger.warning("XY initialization error (non-fatal): %s", e)
        xy_init_thread = threading.Thread(target=xy_init_background, daemon=True)
        xy_init_thread.start()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("System initialization completed")
        logger.info("Press Ctrl+C to stop the system")
        
        # Main application loop
        while not shutdown_requested:
            try:
                # Check system health
                if api_server and not api_server.is_server_running():
                    logger.warning("API server stopped unexpectedly, attempting restart...")
                    if api_server.start():
                        logger.info("API server restarted successfully")
                    else:
                        logger.error("Failed to restart API server")
                
                # Sleep for a short interval
                time.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                time.sleep(10)  # Wait before retrying
        
        # Graceful shutdown
        logger.info("Initiating graceful shutdown...")
        
        if api_server:
            logger.info("Stopping API server...")
            api_server.stop()
        
        logger.info("Cleaning up controllers...")
        servo_controller.cleanup()
        xy_controller.cleanup()
        
        logger.info("Shutdown completed successfully")
        
    except FileNotFoundError as e:
        print(f"Configuration error: {e}")
        print("Please ensure config.yaml exists and is accessible")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Configuration file error: {e}")
        print("Please check the YAML syntax in your config.yaml file")
        sys.exit(1)
    except Exception as e:
        logger = logging.getLogger(__name__)
        if logger:
            logger.error(f"System initialization failed: {e}")
        else:
            print(f"System initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


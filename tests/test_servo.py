#!/usr/bin/env python3
"""
Test Script for Servo Control System
This script tests basic functionality of the servo control system.
Run this to verify your hardware setup is working correctly.
"""

import sys
import time
import yaml
from pathlib import Path
import os

# Add repo root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.servo_hardware import ServoHardware
from controllers.servo_controller import ServoController


def test_hardware_initialization():
    """Test basic hardware initialization."""
    print("Testing hardware initialization...")
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Test hardware interface
        hardware = ServoHardware(config)
        
        if hardware.is_initialized:
            print("✓ Hardware initialization successful")
            print(f"  - I2C Bus: {hardware.i2c_bus}")
            print(f"  - PCA9685 Address: 0x{hardware.i2c_address:02X}")
            print(f"  - PWM Frequency: {hardware.pwm_frequency}Hz")
            print(f"  - Servo Channels: {len(hardware.servos)}")
            return hardware
        else:
            print("✗ Hardware initialization failed")
            return None
            
    except Exception as e:
        print(f"✗ Hardware initialization error: {e}")
        return None


def test_servo_movement(hardware, channel=0):
    """Test basic servo movement."""
    print(f"\nTesting servo movement on channel {channel}...")
    
    try:
        # Test positions
        test_positions = [90, 0, 180, 90]  # Center, Left, Right, Center
        
        for position in test_positions:
            print(f"  Moving to {position}°...")
            success = hardware.move_servo(channel, position, duration=1.0)
            
            if success:
                print(f"    ✓ Moved to {position}°")
                time.sleep(1)  # Wait for movement to complete
            else:
                print(f"    ✗ Failed to move to {position}°")
                return False
        
        print("✓ Servo movement test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Servo movement test error: {e}")
        return False


def test_controller_functionality():
    """Test servo controller functionality."""
    print("\nTesting servo controller...")
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Test controller
        controller = ServoController(config)
        
        print(f"✓ Controller initialized")
        print(f"  - Sequences loaded: {len(controller.sequences)}")
        print(f"  - Available sequences: {list(controller.sequences.keys())}")
        
        # Test sequence execution
        if 'wave' in controller.sequences:
            print("\nTesting 'wave' sequence...")
            success = controller.run_sequence('wave', repeat_count=1)
            
            if success:
                print("✓ Wave sequence started successfully")
                time.sleep(5)  # Wait for sequence to complete
            else:
                print("✗ Failed to start wave sequence")
        
        return controller
        
    except Exception as e:
        print(f"✗ Controller test error: {e}")
        return None


def test_emergency_stop(controller):
    """Test emergency stop functionality."""
    print("\nTesting emergency stop...")
    
    try:
        success = controller.emergency_stop()
        
        if success:
            print("✓ Emergency stop executed successfully")
        else:
            print("✗ Emergency stop failed")
        
        return success
        
    except Exception as e:
        print(f"✗ Emergency stop test error: {e}")
        return False


def main():
    """Main test function."""
    print("=== Servo Control System Test ===")
    print("This script will test your hardware setup step by step.")
    print("Make sure your servos are properly connected and powered.")
    print()
    
    # Test 1: Hardware initialization
    hardware = test_hardware_initialization()
    if not hardware:
        print("\n❌ Hardware test failed. Please check your connections:")
        print("  - I2C is enabled on your Raspberry Pi")
        print("  - PCA9685 is properly connected to GPIO pins 2, 3, 5, 6")
        print("  - Servos are connected to PCA9685 channels")
        print("  - Power supply is adequate for your servos")
        return
    
    # Test 2: Basic servo movement
    if not test_servo_movement(hardware):
        print("\n❌ Servo movement test failed. Please check:")
        print("  - Servo connections and power")
        print("  - PCA9685 channel connections")
        print("  - Servo specifications (pulse range)")
        return
    
    # Test 3: Controller functionality
    controller = test_controller_functionality()
    if not controller:
        print("\n❌ Controller test failed.")
        return
    
    # Test 4: Emergency stop
    if not test_emergency_stop(controller):
        print("\n❌ Emergency stop test failed.")
        return
    
    # All tests passed
    print("\n🎉 All tests passed! Your servo control system is working correctly.")
    print("\nNext steps:")
    print("  1. Run the main application: python3 main.py")
    print("  2. Use the HTTP API to control servos remotely")
    print("  3. Create custom movement sequences")
    print("  4. Set up scheduled movements")
    
    # Cleanup
    try:
        controller.cleanup()
        print("\n✓ System cleanup completed")
    except Exception as e:
        print(f"\n⚠ Warning: Cleanup error: {e}")


if __name__ == "__main__":
    main()


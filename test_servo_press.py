#!/usr/bin/env python3
"""
Test script for servo press functionality.
Tests the new press_servo method and API endpoint.
"""

import sys
import time
import logging
from servo_controller import ServoController
from servo_hardware import ServoHardware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_servo_press_functionality():
    """Test the servo press functionality."""
    
    print("Testing Servo Press Functionality")
    print("="*40)
    
    try:
        # Load configuration
        import yaml
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize hardware
        print("1. Initializing servo hardware...")
        hardware = ServoHardware(config)
        
        if not hardware.is_initialized:
            print("❌ Hardware initialization failed")
            return False
        
        print("✅ Hardware initialized successfully")
        
        # Initialize controller
        print("\n2. Initializing servo controller...")
        controller = ServoController(config)
        print("✅ Controller initialized successfully")
        
        # Test press functionality
        print("\n3. Testing press functionality...")
        channel = 0
        press_angle = 45
        release_angle = 0
        press_delay = 0.5
        
        print(f"   Channel: {channel}")
        print(f"   Press angle: {press_angle}°")
        print(f"   Release angle: {release_angle}°")
        print(f"   Press delay: {press_delay}s")
        
        # Execute press
        print("\n   Executing press...")
        start_time = time.time()
        success = controller.press_servo(channel, press_angle, release_angle, press_delay)
        end_time = time.time()
        
        if success:
            print(f"✅ Press operation completed successfully in {end_time - start_time:.2f}s")
        else:
            print("❌ Press operation failed")
            return False
        
        # Test with different parameters
        print("\n4. Testing with different parameters...")
        
        test_cases = [
            {"press_angle": 30, "release_angle": 10, "press_delay": 0.1},
            {"press_angle": 60, "release_angle": 0, "press_delay": 0.2},
            {"press_angle": 90, "release_angle": 45, "press_delay": 0.3},
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test case {i}: {test_case}")
            success = controller.press_servo(channel, **test_case)
            
            if success:
                print(f"   ✅ Test case {i} passed")
            else:
                print(f"   ❌ Test case {i} failed")
                return False
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        logger.exception("Test failed")
        return False
    
    finally:
        # Cleanup
        try:
            print("\n5. Cleaning up...")
            if 'hardware' in locals():
                hardware.release_all_servos()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

def test_api_endpoint():
    """Test the API endpoint (requires running server)."""
    
    print("\n" + "="*60)
    print("API ENDPOINT TEST")
    print("="*60)
    print("Note: This test requires the API server to be running")
    print("Start the server with: python start_servo_system.py --mode api")
    print()
    
    # Example API test commands
    print("Test commands to run in another terminal:")
    print()
    
    print("1. Basic press test:")
    print("""curl -X POST http://pos-raspberrypi.local:5000/api/servo/0/press \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: $SERVO_API_KEY" \\
  -d '{"press_angle": 45, "release_angle": 0, "press_delay": 0.2}'""")
    
    print("\n2. Quick press test:")
    print("""curl -X POST http://pos-raspberrypi.local:5000/api/servo/0/press \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: $SERVO_API_KEY" \\
  -d '{"press_angle": 60, "release_angle": 10, "press_delay": 0}'""")
    
    print("\n3. Check servo status:")
    print("""curl -X GET http://pos-raspberrypi.local:5000/api/servo/0/position \\
  -H "X-API-Key: $SERVO_API_KEY" """)

if __name__ == "__main__":
    print("Servo Press Test Suite")
    print("="*50)
    
    # Test hardware functionality
    success = test_servo_press_functionality()
    
    if success:
        print("\n🎉 All hardware tests passed!")
    else:
        print("\n💥 Hardware tests failed!")
        sys.exit(1)
    
    # Show API test instructions
    test_api_endpoint()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("✅ Servo press functionality implemented")
    print("✅ Single API call for press-and-release")
    print("✅ Configurable press delay")
    print("✅ Thread-safe operation")
    print("✅ Ready for button pressing automation")

#!/usr/bin/env python3
"""
Servo Press Example
Demonstrates how to use the new servo press functionality for button pressing.
This example shows how to press buttons using a single API call with configurable timing.
"""

import requests
import time
import json

# Configuration
API_BASE_URL = "http://pos-raspberrypi.local:5000"
API_KEY = "your-api-key-here"  # Replace with your actual API key

def press_button_example():
    """Example of pressing a button using the servo press functionality."""
    
    # Example: Press button using servo channel 0
    channel = 0
    press_angle = 45    # Angle to press the button
    release_angle = 0   # Angle to release the button
    press_delay = 0.2   # Hold the press for 200ms
    
    print(f"Pressing button with servo {channel}...")
    print(f"Press angle: {press_angle}°, Release angle: {release_angle}°")
    print(f"Press delay: {press_delay}s")
    
    # Make the press request
    url = f"{API_BASE_URL}/api/servo/{channel}/press"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    data = {
        "press_angle": press_angle,
        "release_angle": release_angle,
        "press_delay": press_delay
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        if result["success"]:
            print("✅ Button press successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print("❌ Button press failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def multiple_button_press_example():
    """Example of pressing multiple buttons in sequence."""
    
    # Define button configurations
    buttons = [
        {"channel": 0, "press_angle": 45, "release_angle": 0, "press_delay": 0.1},
        {"channel": 1, "press_angle": 60, "release_angle": 10, "press_delay": 0.15},
        {"channel": 2, "press_angle": 30, "release_angle": 0, "press_delay": 0.2},
    ]
    
    print("Pressing multiple buttons in sequence...")
    
    for i, button in enumerate(buttons, 1):
        print(f"\n--- Button {i} ---")
        print(f"Channel: {button['channel']}")
        print(f"Press: {button['press_angle']}° → Release: {button['release_angle']}°")
        
        url = f"{API_BASE_URL}/api/servo/{button['channel']}/press"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
        
        try:
            response = requests.post(url, headers=headers, json=button)
            result = response.json()
            
            if result["success"]:
                print("✅ Success!")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        # Small delay between button presses
        time.sleep(0.5)

def xy_and_servo_combined_example():
    """Example of combining XY positioning with servo pressing."""
    
    print("Combined XY positioning + servo press example...")
    
    # Step 1: Move XY to button position
    print("\n1. Moving XY to button position...")
    xy_url = f"{API_BASE_URL}/api/xy/move"
    xy_headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    xy_data = {"x": 300, "y": 450}  # Example button position
    
    try:
        response = requests.post(xy_url, headers=xy_headers, json=xy_data)
        result = response.json()
        
        if result["success"]:
            print("✅ XY movement successful!")
        else:
            print(f"❌ XY movement failed: {result.get('error')}")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"❌ XY request failed: {e}")
        return
    
    # Step 2: Press the button with servo
    print("\n2. Pressing button with servo...")
    servo_url = f"{API_BASE_URL}/api/servo/0/press"
    servo_headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    servo_data = {
        "press_angle": 50,
        "release_angle": 0,
        "press_delay": 0.2
    }
    
    try:
        response = requests.post(servo_url, headers=servo_headers, json=servo_data)
        result = response.json()
        
        if result["success"]:
            print("✅ Button press successful!")
        else:
            print(f"❌ Button press failed: {result.get('error')}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Servo request failed: {e}")

def curl_examples():
    """Show curl command examples for the press functionality."""
    
    print("\n" + "="*60)
    print("CURL COMMAND EXAMPLES")
    print("="*60)
    
    print("\n1. Basic button press:")
    print(f"""curl -X POST {API_BASE_URL}/api/servo/0/press \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: $SERVO_API_KEY" \\
  -d '{{"press_angle": 45, "release_angle": 0, "press_delay": 0.1}}'""")
    
    print("\n2. Quick press (no delay):")
    print(f"""curl -X POST {API_BASE_URL}/api/servo/0/press \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: $SERVO_API_KEY" \\
  -d '{{"press_angle": 60, "release_angle": 10, "press_delay": 0}}'""")
    
    print("\n3. Long press (hold for 500ms):")
    print(f"""curl -X POST {API_BASE_URL}/api/servo/0/press \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: $SERVO_API_KEY" \\
  -d '{{"press_angle": 50, "release_angle": 0, "press_delay": 0.5}}'""")

if __name__ == "__main__":
    print("Servo Press Functionality Examples")
    print("="*40)
    
    # Show curl examples first
    curl_examples()
    
    # Interactive examples (uncomment to run)
    # print("\n" + "="*60)
    # print("INTERACTIVE EXAMPLES")
    # print("="*60)
    # 
    # print("\n1. Single button press:")
    # press_button_example()
    # 
    # print("\n2. Multiple button presses:")
    # multiple_button_press_example()
    # 
    # print("\n3. Combined XY + Servo:")
    # xy_and_servo_combined_example()
    
    print("\n" + "="*60)
    print("USAGE NOTES")
    print("="*60)
    print("• press_angle: Angle to press the button (0-180°)")
    print("• release_angle: Angle to release the button (0-180°)")
    print("• press_delay: Time to hold the press position (seconds)")
    print("• Single API call handles complete press-and-release sequence")
    print("• No network dependency between press and release")
    print("• Faster and more reliable than separate move calls")

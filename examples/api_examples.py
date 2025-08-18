#!/usr/bin/env python3
"""
API Usage Examples
This script demonstrates how to use the Servo Control System API
from external Python applications.
"""

import requests
import json
import time
from typing import Dict, Any


class ServoControlAPI:
    """Client class for interacting with the Servo Control System API."""
    
    def __init__(self, base_url: str = "http://YOUR_PI_IP:5000"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the API server (replace YOUR_PI_IP with actual IP)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict:
        """Get system status."""
        return self._make_request('GET', '/api/status')
    
    def move_servo(self, channel: int, angle: float, duration: float = 0.0) -> Dict:
        """Move a servo to a specific angle."""
        data = {
            'angle': angle,
            'duration': duration
        }
        return self._make_request('POST', f'/api/servo/{channel}/move', data)
    
    def get_servo_position(self, channel: int) -> Dict:
        """Get current position of a servo."""
        return self._make_request('GET', f'/api/servo/{channel}/position')
    
    def release_servo(self, channel: int) -> Dict:
        """Release a servo (power off)."""
        return self._make_request('POST', f'/api/servo/{channel}/release')
    
    def list_sequences(self) -> Dict:
        """List all available sequences."""
        return self._make_request('GET', '/api/sequences')
    
    def run_sequence(self, sequence_name: str, repeat_count: int = 1) -> Dict:
        """Run a sequence."""
        data = {'repeat_count': repeat_count}
        return self._make_request('POST', f'/api/sequences/{sequence_name}/run', data)
    
    def create_sequence(self, name: str, steps: list) -> Dict:
        """Create a new sequence."""
        data = {
            'name': name,
            'steps': steps
        }
        return self._make_request('POST', '/api/sequences', data)
    
    def schedule_daily(self, sequence_name: str, time_str: str, repeat_count: int = 1) -> Dict:
        """Schedule a sequence to run daily at a specific time."""
        data = {
            'sequence_name': sequence_name,
            'time': time_str,
            'repeat_count': repeat_count
        }
        return self._make_request('POST', '/api/schedule/daily', data)
    
    def emergency_stop(self) -> Dict:
        """Emergency stop - stop all movements and release servos."""
        return self._make_request('POST', '/api/emergency/stop')


def example_basic_servo_control():
    """Example: Basic servo control operations."""
    print("=== Basic Servo Control Example ===")
    
    api = ServoControlAPI()
    
    # Check system status
    print("Checking system status...")
    status = api.get_status()
    if status.get('success'):
        print(f"System is running with {status['data']['hardware']['servo_count']} servos")
    else:
        print("Failed to get system status")
        return
    
    # Move servo 0 to different positions
    print("\nMoving servo 0 through various positions...")
    positions = [0, 45, 90, 135, 180, 90]
    
    for pos in positions:
        print(f"Moving to {pos}°...")
        result = api.move_servo(0, pos, duration=1.0)
        
        if result.get('success'):
            print(f"  ✓ Moved to {pos}°")
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
        
        time.sleep(1.5)  # Wait for movement to complete
    
    # Get final position
    position = api.get_servo_position(0)
    if position.get('success'):
        print(f"\nFinal position: {position['data']['position']}°")
    
    # Release servo
    print("Releasing servo...")
    api.release_servo(0)


def example_sequence_management():
    """Example: Creating and running custom sequences."""
    print("\n=== Sequence Management Example ===")
    
    api = ServoControlAPI()
    
    # Create a custom sequence
    print("Creating custom sequence 'dance'...")
    dance_steps = [
        {'channel': 0, 'angle': 0, 'duration': 1.0},
        {'channel': 1, 'angle': 90, 'duration': 1.0},
        {'channel': 0, 'angle': 180, 'duration': 1.0},
        {'channel': 1, 'angle': 0, 'duration': 1.0},
        {'channel': 0, 'angle': 90, 'duration': 1.0},
        {'channel': 1, 'angle': 180, 'duration': 1.0}
    ]
    
    result = api.create_sequence('dance', dance_steps)
    if result.get('success'):
        print("✓ Dance sequence created successfully")
    else:
        print(f"✗ Failed to create sequence: {result.get('error')}")
        return
    
    # List all sequences
    print("\nAvailable sequences:")
    sequences = api.list_sequences()
    if sequences.get('success'):
        for seq in sequences['data']['sequences']:
            print(f"  - {seq}")
    
    # Run the dance sequence
    print("\nRunning dance sequence...")
    result = api.run_sequence('dance', repeat_count=2)
    
    if result.get('success'):
        print("✓ Dance sequence started")
        print("Waiting for sequence to complete...")
        time.sleep(15)  # Wait for sequence to finish
    else:
        print(f"✗ Failed to run sequence: {result.get('error')}")


def example_scheduling():
    """Example: Scheduling sequences to run automatically."""
    print("\n=== Scheduling Example ===")
    
    api = ServoControlAPI()
    
    # Schedule a sequence to run daily at 9:00 AM
    print("Scheduling 'wave' sequence to run daily at 9:00 AM...")
    result = api.schedule_daily('wave', '09:00', repeat_count=1)
    
    if result.get('success'):
        print("✓ Daily schedule created successfully")
    else:
        print(f"✗ Failed to create schedule: {result.get('error')}")
    
    # Schedule a sequence to run every 30 minutes
    print("\nScheduling 'wave' sequence to run every 30 minutes...")
    # Note: This endpoint doesn't exist in the current API, but shows the concept
    print("(Recurring schedule endpoint not implemented in this example)")


def example_emergency_control():
    """Example: Emergency stop and safety features."""
    print("\n=== Emergency Control Example ===")
    
    api = ServoControlAPI()
    
    # Start some movements
    print("Starting movements on multiple servos...")
    api.move_servo(0, 90, duration=2.0)
    api.move_servo(1, 45, duration=2.0)
    
    # Wait a moment
    time.sleep(1)
    
    # Emergency stop
    print("Executing emergency stop...")
    result = api.emergency_stop()
    
    if result.get('success'):
        print("✓ Emergency stop executed successfully")
    else:
        print(f"✗ Emergency stop failed: {result.get('error')}")


def example_monitoring():
    """Example: Continuous monitoring of servo positions."""
    print("\n=== Monitoring Example ===")
    
    api = ServoControlAPI()
    
    print("Monitoring servo positions for 10 seconds...")
    start_time = time.time()
    
    try:
        while time.time() - start_time < 10:
            # Get positions of first 3 servos
            for channel in range(3):
                position = api.get_servo_position(channel)
                if position.get('success'):
                    pos = position['data']['position']
                    print(f"Servo {channel}: {pos}°", end='  ')
                else:
                    print(f"Servo {channel}: Error", end='  ')
            
            print()  # New line
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")


def main():
    """Run all examples."""
    print("Servo Control System API Examples")
    print("Make sure the main application is running on your Raspberry Pi!")
    print("⚠️  IMPORTANT: Configure your local settings!")
    print("   1. Copy config.local.yaml template")
    print("   2. Set your API key and Pi IP address")
    print("   3. Update the base_url in this script")
    print("=" * 50)
    
            # Try to load local config and network manager
        try:
            import yaml
            with open('config.local.yaml', 'r') as f:
                local_config = yaml.safe_load(f)
            
            # Initialize network manager
            from network_utils import NetworkManager
            network_manager = NetworkManager(local_config)
            network_info = network_manager.get_network_info()
            
            api_key = local_config.get('api_keys', {}).get('team_key', 'YOUR_API_KEY')
            
            if network_info['current_address'] and api_key != 'YOUR_API_KEY':
                print(f"✅ Local config loaded:")
                print(f"   Network Address: {network_info['current_address']} ({network_info['address_type']})")
                if network_info['resolved_ip']:
                    print(f"   Resolved IP: {network_info['resolved_ip']}")
                print(f"   API Key: {api_key[:8]}...{api_key[-8:]}")
                print(f"   Base URL: {network_manager.get_api_base_url()}")
                print(f"   Web Interface: {network_manager.get_web_url()}")
                print()
                
                # Test connectivity
                connectivity = network_manager.test_connectivity()
                print("🔍 Connectivity Test:")
                print(f"   Ping: {'✅' if connectivity['ping'] else '❌'}")
                print(f"   API Server: {'✅' if connectivity['api_server'] else '❌'}")
                print(f"   Web Interface: {'✅' if connectivity['web_interface'] else '❌'}")
                print()
                
            else:
                print("❌ Please configure config.local.yaml first!")
                print("   See SETUP.md for instructions")
                return
                
        except FileNotFoundError:
            print("❌ config.local.yaml not found!")
            print("   Please copy the template and configure it")
            return
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return
    
    try:
        # Run examples
        example_basic_servo_control()
        example_sequence_management()
        example_scheduling()
        example_emergency_control()
        example_monitoring()
        
        print("\n🎉 All examples completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
    
    print("\nFor more information, see the README.md file")


if __name__ == "__main__":
    main()

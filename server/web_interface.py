#!/usr/bin/env python3
"""
Web Interface for Servo Control System
Provides a simple web-based interface for controlling servos and managing sequences.
"""

import json
import logging
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from controllers.servo_controller import ServoController
import yaml

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Servo Control System</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .auth-section {
            margin-top: 15px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }
        .api-key-input {
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            margin-right: 10px;
            width: 200px;
            font-family: monospace;
        }
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .servo-control {
            grid-column: 1 / -1;
        }
        .servo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .servo-item {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            background: #fafafa;
        }
        .servo-item.active {
            border-color: #4CAF50;
            background: #f1f8e9;
        }
        .servo-item.moving {
            border-color: #FF9800;
            background: #fff3e0;
        }
        .angle-display {
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
            margin: 10px 0;
        }
        .angle-input {
            width: 80px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
        }
        .btn {
            background: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
        }
        .btn:hover {
            background: #1976D2;
        }
        .btn.danger {
            background: #f44336;
        }
        .btn.danger:hover {
            background: #d32f2f;
        }
        .btn.success {
            background: #4CAF50;
        }
        .btn.success:hover {
            background: #388E3C;
        }
        .sequence-list {
            list-style: none;
            padding: 0;
        }
        .sequence-item {
            background: #f8f9fa;
            margin: 10px 0;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
        }
        .status {
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .emergency-section {
            grid-column: 1 / -1;
            text-align: center;
        }
        .emergency-btn {
            background: #f44336;
            color: white;
            border: none;
            padding: 20px 40px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .emergency-btn:hover {
            background: #d32f2f;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
            }
            .servo-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎮 Servo Control System</h1>
        <p>Control your servos with ease</p>
        <div class="auth-section">
            <input type="password" id="apiKeyInput" placeholder="Enter API Key" class="api-key-input">
            <button class="btn" onclick="setApiKey()">Set API Key</button>
        </div>
    </div>

    <div class="container">
        <!-- Emergency Stop Section -->
        <div class="emergency-section">
            <button class="emergency-btn" onclick="emergencyStop()">
                🚨 EMERGENCY STOP
            </button>
        </div>

        <!-- Servo Control Section -->
        <div class="card servo-control">
            <h2>🎯 Servo Control</h2>
            <div class="servo-grid" id="servoGrid">
                <!-- Servo controls will be generated here -->
            </div>
        </div>

        <!-- Sequence Management -->
        <div class="card">
            <h2>🔄 Sequences</h2>
            <div id="sequenceList">
                <!-- Sequences will be loaded here -->
            </div>
        </div>

        <!-- System Status -->
        <div class="card">
            <h2>📊 System Status</h2>
            <div id="systemStatus">
                <!-- Status will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        let servoStates = {};
        let updateInterval;
        let apiKey = '';

        // Initialize the interface
        document.addEventListener('DOMContentLoaded', function() {
            initializeServos();
            
            // Check if API key is stored
            const storedKey = localStorage.getItem('servo_api_key');
            if (storedKey) {
                apiKey = storedKey;
                document.getElementById('apiKeyInput').value = storedKey;
                loadSequences();
                loadSystemStatus();
                
                // Start periodic updates
                updateInterval = setInterval(updateServoStates, 1000);
            } else {
                showStatus('Please enter your API key to start controlling servos', 'error');
            }
        });
        
        function setApiKey() {
            const input = document.getElementById('apiKeyInput');
            const key = input.value.trim();
            
            if (!key) {
                showStatus('Please enter an API key', 'error');
                return;
            }
            
            apiKey = key;
            localStorage.setItem('servo_api_key', key);
            
            showStatus('API key set successfully', 'success');
            
            // Load data and start updates
            loadSequences();
            loadSystemStatus();
            updateInterval = setInterval(updateServoStates, 1000);
        }

        function initializeServos() {
            const grid = document.getElementById('servoGrid');
            grid.innerHTML = '';
            
            for (let i = 0; i < 16; i++) {
                const servoDiv = document.createElement('div');
                servoDiv.className = 'servo-item';
                servoDiv.id = `servo-${i}`;
                
                servoDiv.innerHTML = `
                    <h3>Servo ${i}</h3>
                    <div class="angle-display" id="angle-${i}">90°</div>
                    <input type="number" class="angle-input" id="input-${i}" 
                           min="0" max="180" value="90" step="1">
                    <br>
                    <button class="btn" onclick="moveServo(${i})">Move</button>
                    <button class="btn danger" onclick="releaseServo(${i})">Release</button>
                `;
                
                grid.appendChild(servoDiv);
                servoStates[i] = { angle: 90, moving: false };
            }
        }

        async function moveServo(channel) {
            const input = document.getElementById(`input-${channel}`);
            const angle = parseInt(input.value);
            
            if (isNaN(angle) || angle < 0 || angle > 180) {
                showStatus('Invalid angle. Please enter a value between 0 and 180.', 'error');
                return;
            }
            
            const servoDiv = document.getElementById(`servo-${channel}`);
            servoDiv.classList.add('moving');
            servoDiv.classList.add('loading');
            
            try {
                const response = await fetch(`/api/servo/${channel}/move`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-API-Key': apiKey
                    },
                    body: JSON.stringify({ angle: angle, duration: 1.0 })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    servoStates[channel] = { angle: angle, moving: false };
                    updateServoDisplay(channel);
                    showStatus(`Servo ${channel} moved to ${angle}°`, 'success');
                } else {
                    showStatus(`Failed to move servo ${channel}: ${result.error}`, 'error');
                }
            } catch (error) {
                showStatus(`Error moving servo ${channel}: ${error.message}`, 'error');
            } finally {
                servoDiv.classList.remove('moving', 'loading');
            }
        }

        async function releaseServo(channel) {
            try {
                const response = await fetch(`/api/servo/${channel}/release`, {
                    method: 'POST',
                    headers: { 'X-API-Key': apiKey }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus(`Servo ${channel} released`, 'success');
                } else {
                    showStatus(`Failed to release servo ${channel}: ${result.error}`, 'error');
                }
            } catch (error) {
                showStatus(`Error releasing servo ${channel}: ${error.message}`, 'error');
            }
        }

        async function emergencyStop() {
            if (!confirm('Are you sure you want to execute an emergency stop? This will stop all movements immediately.')) {
                return;
            }
            
            try {
                const response = await fetch('/api/emergency/stop', {
                    method: 'POST',
                    headers: { 'X-API-Key': apiKey }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Emergency stop executed successfully', 'success');
                    // Reset all servo states
                    for (let i = 0; i < 16; i++) {
                        servoStates[i] = { angle: 90, moving: false };
                        updateServoDisplay(i);
                    }
                } else {
                    showStatus(`Emergency stop failed: ${result.error}`, 'error');
                }
            } catch (error) {
                showStatus(`Error executing emergency stop: ${error.message}`, 'error');
            }
        }

        async function loadSequences() {
            try {
                const response = await fetch('/api/sequences', {
                    headers: { 'X-API-Key': apiKey }
                });
                const result = await response.json();
                
                if (result.success) {
                    const sequenceList = document.getElementById('sequenceList');
                    sequenceList.innerHTML = '';
                    
                    result.data.sequences.forEach(sequence => {
                        const div = document.createElement('div');
                        div.className = 'sequence-item';
                        div.innerHTML = `
                            <h4>${sequence}</h4>
                            <button class="btn success" onclick="runSequence('${sequence}')">Run</button>
                            <button class="btn" onclick="runSequence('${sequence}', 3)">Run 3x</button>
                        `;
                        sequenceList.appendChild(div);
                    });
                }
            } catch (error) {
                console.error('Error loading sequences:', error);
            }
        }

        async function runSequence(sequenceName, repeatCount = 1) {
            try {
                const response = await fetch(`/api/sequences/${sequenceName}/run`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-API-Key': apiKey
                    },
                    body: JSON.stringify({ repeat_count: repeatCount })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus(`Sequence '${sequenceName}' started`, 'success');
                } else {
                    showStatus(`Failed to start sequence: ${result.error}`, 'error');
                }
            } catch (error) {
                showStatus(`Error running sequence: ${error.message}`, 'error');
            }
        }

        async function loadSystemStatus() {
            try {
                const response = await fetch('/api/status', {
                    headers: { 'X-API-Key': apiKey }
                });
                const result = await response.json();
                
                if (result.success) {
                    const statusDiv = document.getElementById('systemStatus');
                    const data = result.data;
                    
                    statusDiv.innerHTML = `
                        <p><strong>Hardware:</strong> ${data.hardware.initialized ? '✅ Ready' : '❌ Not Ready'}</p>
                        <p><strong>Servos:</strong> ${data.hardware.servo_count} channels</p>
                        <p><strong>Sequences:</strong> ${data.controller.sequences_loaded} loaded</p>
                        <p><strong>Active Movements:</strong> ${data.controller.active_movements}</p>
                        <p><strong>I2C Bus:</strong> ${data.hardware.i2c_bus}</p>
                        <p><strong>PWM Frequency:</strong> ${data.hardware.pwm_frequency}Hz</p>
                    `;
                }
            } catch (error) {
                console.error('Error loading system status:', error);
            }
        }

        async function updateServoStates() {
            // Update servo positions from the API
            for (let i = 0; i < 16; i++) {
                try {
                    const response = await fetch(`/api/servo/${i}/position`, {
                        headers: { 'X-API-Key': apiKey }
                    });
                    const result = await response.json();
                    
                    if (result.success) {
                        const newAngle = result.data.position;
                        if (servoStates[i].angle !== newAngle) {
                            servoStates[i].angle = newAngle;
                            updateServoDisplay(i);
                        }
                    }
                } catch (error) {
                    // Silently handle errors for background updates
                }
            }
        }

        function updateServoDisplay(channel) {
            const angleDisplay = document.getElementById(`angle-${channel}`);
            const input = document.getElementById(`input-${channel}`);
            const servoDiv = document.getElementById(`servo-${channel}`);
            
            if (angleDisplay && input && servoDiv) {
                angleDisplay.textContent = `${servoStates[channel].angle}°`;
                input.value = servoStates[channel].angle;
                
                // Update visual state
                servoDiv.classList.remove('active', 'moving');
                if (servoStates[channel].moving) {
                    servoDiv.classList.add('moving');
                } else if (servoStates[channel].angle !== 90) {
                    servoDiv.classList.add('active');
                }
            }
        }

        function showStatus(message, type) {
            // Remove existing status messages
            const existingStatus = document.querySelector('.status');
            if (existingStatus) {
                existingStatus.remove();
            }
            
            // Create new status message
            const statusDiv = document.createElement('div');
            statusDiv.className = `status ${type}`;
            statusDiv.textContent = message;
            
            // Insert at the top of the container
            const container = document.querySelector('.container');
            container.insertBefore(statusDiv, container.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.remove();
                }
            }, 5000);
        }

        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        });
    </script>
</body>
</html>
"""


class WebInterface:
    """Web interface for the servo control system."""
    
    def __init__(self, config: dict, controller: ServoController):
        """
        Initialize the web interface.
        
        Args:
            config: Configuration dictionary
            controller: ServoController instance
        """
        self.config = config
        self.controller = controller
        self.logger = logging.getLogger(__name__)
        
        # Load API keys from environment
        self.api_keys = self._load_api_keys()
        
        # Create Flask app
        self.app = Flask(__name__)
        self.register_routes()
    
    def _load_api_keys(self):
        """Load API keys from environment variables and local config."""
        import os
        
        keys = []
        
        # 1. Try environment variables first
        if os.environ.get('SERVO_API_KEY'):
            keys.append(os.environ.get('SERVO_API_KEY'))
        
        if os.environ.get('SERVO_API_KEYS'):
            keys.extend(os.environ.get('SERVO_API_KEYS').split(','))
        
        # 2. Try local configuration file
        if 'api_keys' in self.config:
            api_keys_config = self.config['api_keys']
            
            # Single team key
            if 'team_key' in api_keys_config and api_keys_config['team_key'] != "YOUR_API_KEY_HERE":
                keys.append(api_keys_config['team_key'])
            
            # Multiple keys
            if 'keys' in api_keys_config:
                for key in api_keys_config['keys']:
                    if key and key != "YOUR_API_KEY_HERE":
                        keys.append(key)
        
        # 3. Fallback for development (WARNING: change this!)
        if not keys:
            keys = ['dev-key-change-in-production']
            self.logger.warning("⚠️  WARNING: Using default development API key!")
            self.logger.warning("   Set SERVO_API_KEY environment variable or configure config.local.yaml!")
        
        # Remove duplicates and empty keys
        keys = list(set([key.strip() for key in keys if key and key.strip()]))
        
        self.logger.info(f"Loaded {len(keys)} API key(s)")
        
        return keys
    
    def require_api_key(self, f):
        """Decorator for web interface authentication."""
        from functools import wraps
        
        @wraps(f)
        def decorated(*args, **kwargs):
            # For web interface, we can use session-based auth
            # or require API key in headers
            api_key = request.headers.get('X-API-Key')
            
            if not api_key or api_key not in self.api_keys:
                return jsonify({'error': 'Authentication required'}), 401
            
            return f(*args, **kwargs)
        return decorated
    
    def register_routes(self):
        """Register web interface routes."""
        
        @self.app.route('/')
        def index():
            """Main web interface page."""
            return HTML_TEMPLATE
        
        @self.app.route('/api/servo/<int:channel>/move', methods=['POST'])
        @self.require_api_key
        def move_servo(channel):
            """Move a servo to a specific angle."""
            try:
                data = request.get_json()
                angle = data.get('angle')
                duration = data.get('duration', 0.0)
                
                if angle is None:
                    return jsonify({'success': False, 'error': 'Angle is required'}), 400
                
                success = self.controller.move_servo(channel, angle, duration)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Servo {channel} moved to {angle}°'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to move servo {channel}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Move servo error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/servo/<int:channel>/position', methods=['GET'])
        @self.require_api_key
        def get_servo_position(channel):
            """Get current position of a servo."""
            try:
                position = self.controller.hardware.get_servo_position(channel)
                
                if position is not None:
                    return jsonify({
                        'success': True,
                        'data': {'position': position}
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid servo channel: {channel}'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"Get position error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/servo/<int:channel>/release', methods=['POST'])
        @self.require_api_key
        def release_servo(channel):
            """Release a servo (power off)."""
            try:
                success = self.controller.hardware.release_servo(channel)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Servo {channel} released'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to release servo {channel}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Release servo error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/sequences', methods=['GET'])
        @self.require_api_key
        def list_sequences():
            """List all available sequences."""
            try:
                sequences = list(self.controller.sequences.keys())
                return jsonify({
                    'success': True,
                    'data': {
                        'sequences': sequences,
                        'count': len(sequences)
                    }
                })
            except Exception as e:
                self.logger.error(f"List sequences error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/sequences/<sequence_name>/run', methods=['POST'])
        @self.require_api_key
        def run_sequence(sequence_name):
            """Run a sequence."""
            try:
                data = request.get_json() or {}
                repeat_count = data.get('repeat_count', 1)
                
                success = self.controller.run_sequence(sequence_name, repeat_count)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Sequence {sequence_name} started'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to start sequence {sequence_name}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Run sequence error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/status', methods=['GET'])
        @self.require_api_key
        def get_status():
            """Get system status."""
            try:
                status = self.controller.get_status()
                return jsonify({
                    'success': True,
                    'data': status
                })
            except Exception as e:
                self.logger.error(f"Get status error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/emergency/stop', methods=['POST'])
        @self.require_api_key
        def emergency_stop():
            """Emergency stop."""
            try:
                success = self.controller.emergency_stop()
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Emergency stop executed'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Emergency stop failed'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Emergency stop error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Run the web interface."""
        self.logger.info(f"Starting web interface on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    # Example usage
    import yaml
    
    # Load configuration
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Initialize controller
    controller = ServoController(config)
    
    # Create and run web interface
    web_interface = WebInterface(config, controller)
    web_interface.run(port=8080)

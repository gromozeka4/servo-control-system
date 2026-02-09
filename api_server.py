#!/usr/bin/env python3
"""
HTTP API Server Module
Provides REST API endpoints for controlling servos and managing sequences.
This module allows remote control of the servo system via HTTP requests.
"""

import json
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import threading
import time

from servo_controller import ServoController


class ServoAPIServer:
    """
    HTTP API server for controlling servo operations.
    Provides REST endpoints for servo control, sequence management, and system status.
    """
    
    def __init__(self, config: Dict, controller: ServoController):
        """
        Initialize the API server.
        
        Args:
            config: Configuration dictionary
            controller: ServoController instance
        """
        self.config = config
        self.controller = controller
        self.logger = logging.getLogger(__name__)
        
        # Flask app configuration
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for cross-origin requests
        
        # API configuration
        self.host = config['api']['host']
        self.port = config['api']['port']
        self.debug = config['api']['debug']
        
        # Load API keys from environment
        self.api_keys = self._load_api_keys()
        
        # Register API routes
        self._register_routes()
        
        # Server state
        self.server_thread = None
        self.is_running = False
    
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
        """Decorator to require valid API key."""
        from functools import wraps
        
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': 'API key required'
                }), 401
            
            if api_key not in self.api_keys:
                return jsonify({
                    'success': False,
                    'error': 'Invalid API key'
                }), 401
            
            return f(*args, **kwargs)
        return decorated
    
    def _register_routes(self):
        """Register all API endpoints."""
        
        # System status and health
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'service': 'servo-control-api'
            })
        
        @self.app.route('/api/status', methods=['GET'])
        @self.require_api_key
        def get_status():
            """Get comprehensive system status."""
            try:
                status = self.controller.get_status()
                return jsonify({
                    'success': True,
                    'data': status,
                    'timestamp': time.time()
                })
            except Exception as e:
                self.logger.error(f"Status request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Servo control endpoints
        @self.app.route('/api/servo/<int:channel>/move', methods=['POST'])
        @self.require_api_key
        def move_servo(channel):
            """Move a servo to a specific angle."""
            try:
                data = request.get_json() or {}
                angle = data.get('angle')
                duration = data.get('duration', 0.0)
                
                if angle is None:
                    return jsonify({
                        'success': False,
                        'error': 'Angle parameter is required'
                    }), 400
                
                # Validate parameters
                if not (0 <= channel <= 15):
                    return jsonify({
                        'success': False,
                        'error': 'Channel must be between 0 and 15'
                    }), 400
                
                if not (0 <= angle <= 180):
                    return jsonify({
                        'success': False,
                        'error': 'Angle must be between 0 and 180 degrees'
                    }), 400
                
                if duration < 0:
                    return jsonify({
                        'success': False,
                        'error': 'Duration must be non-negative'
                    }), 400
                
                # Execute movement
                success = self.controller.move_servo(channel, angle, duration)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Servo {channel} moved to {angle}°',
                        'data': {
                            'channel': channel,
                            'angle': angle,
                            'duration': duration
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to move servo {channel}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Move servo request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/servo/<int:channel>/position', methods=['GET'])
        @self.require_api_key
        def get_servo_position(channel):
            """Get current position of a servo."""
            try:
                if not (0 <= channel <= 15):
                    return jsonify({
                        'success': False,
                        'error': 'Channel must be between 0 and 15'
                    }), 400
                
                position = self.controller.hardware.get_servo_position(channel)
                
                if position is not None:
                    return jsonify({
                        'success': True,
                        'data': {
                            'channel': channel,
                            'position': position
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid servo channel: {channel}'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"Get position request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/servo/<int:channel>/release', methods=['POST'])
        @self.require_api_key
        def release_servo(channel):
            """Release a servo (power off)."""
            try:
                if not (0 <= channel <= 15):
                    return jsonify({
                        'success': False,
                        'error': 'Channel must be between 0 and 15'
                    }), 400
                
                success = self.controller.hardware.release_servo(channel)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Servo {channel} released',
                        'data': {'channel': channel}
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to release servo {channel}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Release servo request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Sequence management endpoints
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
                self.logger.error(f"List sequences request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/sequences/<sequence_name>', methods=['GET'])
        @self.require_api_key
        def get_sequence_info(sequence_name):
            """Get information about a specific sequence."""
            try:
                info = self.controller.get_sequence_info(sequence_name)
                
                if info:
                    return jsonify({
                        'success': True,
                        'data': info
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Sequence not found: {sequence_name}'
                    }), 404
                    
            except Exception as e:
                self.logger.error(f"Get sequence info request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/sequences/<sequence_name>/run', methods=['POST'])
        @self.require_api_key
        def run_sequence(sequence_name):
            """Run a sequence."""
            try:
                data = request.get_json() or {}
                repeat_count = data.get('repeat_count', 1)
                
                if repeat_count < 1:
                    return jsonify({
                        'success': False,
                        'error': 'Repeat count must be at least 1'
                    }), 400
                
                success = self.controller.run_sequence(sequence_name, repeat_count)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Sequence {sequence_name} started',
                        'data': {
                            'sequence': sequence_name,
                            'repeat_count': repeat_count
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to start sequence {sequence_name}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Run sequence request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/sequences', methods=['POST'])
        @self.require_api_key
        def create_sequence():
            """Create a new sequence."""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'Request body is required'
                    }), 400
                
                name = data.get('name')
                steps = data.get('steps')
                
                if not name or not steps:
                    return jsonify({
                        'success': False,
                        'error': 'Name and steps are required'
                    }), 400
                
                if not isinstance(steps, list) or len(steps) == 0:
                    return jsonify({
                        'success': False,
                        'error': 'Steps must be a non-empty list'
                    }), 400
                
                # Validate steps
                for i, step in enumerate(steps):
                    if not isinstance(step, dict):
                        return jsonify({
                            'success': False,
                            'error': f'Step {i} must be a dictionary'
                        }), 400
                    
                    if 'channel' not in step or 'angle' not in step:
                        return jsonify({
                            'success': False,
                            'error': f'Step {i} must have channel and angle'
                        }), 400
                    
                    if not (0 <= step['channel'] <= 15):
                        return jsonify({
                            'success': False,
                            'error': f'Step {i} channel must be between 0 and 15'
                        }), 400
                    
                    if not (0 <= step['angle'] <= 180):
                        return jsonify({
                            'success': False,
                            'error': f'Step {i} angle must be between 0 and 180'
                        }), 400
                
                success = self.controller.create_sequence(name, steps)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Sequence {name} created',
                        'data': {
                            'name': name,
                            'steps': steps
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to create sequence {name}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Create sequence request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Scheduling endpoints
        @self.app.route('/api/schedule/daily', methods=['POST'])
        @self.require_api_key
        def schedule_daily():
            """Schedule a sequence to run daily at a specific time."""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'Request body is required'
                    }), 400
                
                sequence_name = data.get('sequence_name')
                time_str = data.get('time')  # Format: "HH:MM"
                repeat_count = data.get('repeat_count', 1)
                
                if not sequence_name or not time_str:
                    return jsonify({
                        'success': False,
                        'error': 'Sequence name and time are required'
                    }), 400
                
                # Validate time format
                try:
                    hour, minute = map(int, time_str.split(':'))
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        raise ValueError()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Time must be in HH:MM format'
                    }), 400
                
                success = self.controller.schedule_sequence(sequence_name, time_str, repeat_count)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Sequence {sequence_name} scheduled daily at {time_str}',
                        'data': {
                            'sequence': sequence_name,
                            'time': time_str,
                            'repeat_count': repeat_count
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to schedule sequence {sequence_name}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Schedule daily request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/schedule/recurring', methods=['POST'])
        @self.require_api_key
        def schedule_recurring():
            """Schedule a sequence to run at regular intervals."""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'Request body is required'
                    }), 400
                
                sequence_name = data.get('sequence_name')
                interval_minutes = data.get('interval_minutes')
                repeat_count = data.get('repeat_count', 1)
                
                if not sequence_name or not interval_minutes:
                    return jsonify({
                        'success': False,
                        'error': 'Sequence name and interval_minutes are required'
                    }), 400
                
                if not isinstance(interval_minutes, int) or interval_minutes < 1:
                    return jsonify({
                        'success': False,
                        'error': 'Interval must be a positive integer'
                    }), 400
                
                success = self.controller.schedule_recurring_sequence(
                    sequence_name, interval_minutes, repeat_count
                )
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Sequence {sequence_name} scheduled every {interval_minutes} minutes',
                        'data': {
                            'sequence': sequence_name,
                            'interval_minutes': interval_minutes,
                            'repeat_count': repeat_count
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to schedule sequence {sequence_name}'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Schedule recurring request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Emergency and control endpoints
        @self.app.route('/api/emergency/stop', methods=['POST'])
        @self.require_api_key
        def emergency_stop():
            """Emergency stop - stop all movements and release servos."""
            try:
                success = self.controller.emergency_stop()
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Emergency stop executed',
                        'data': {'timestamp': time.time()}
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Emergency stop failed'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Emergency stop request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/servo/release-all', methods=['POST'])
        @self.require_api_key
        def release_all_servos():
            """Release all servos (power off)."""
            try:
                success = self.controller.hardware.release_all_servos()
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'All servos released',
                        'data': {'timestamp': time.time()}
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to release all servos'
                    }), 500
                    
            except Exception as e:
                self.logger.error(f"Release all servos request failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'Endpoint not found'
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    def start(self):
        """Start the API server in a background thread."""
        try:
            self.is_running = True
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            
            self.logger.info(f"API server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            self.is_running = False
            return False
    
    def _run_server(self):
        """Run the Flask server."""
        try:
            import warnings
            import logging
            
            # Suppress Flask development server warnings more comprehensively
            warnings.filterwarnings("ignore", message=".*development server.*")
            warnings.filterwarnings("ignore", message=".*WARNING.*development server.*")
            warnings.filterwarnings("ignore", category=UserWarning, module="werkzeug")
            
            # Also suppress werkzeug logger warnings
            werkzeug_logger = logging.getLogger('werkzeug')
            werkzeug_logger.setLevel(logging.ERROR)
            
            # Suppress the specific warning about development server
            original_warn = werkzeug_logger.warning
            def filtered_warning(msg, *args, **kwargs):
                if "development server" in str(msg).lower():
                    return
                original_warn(msg, *args, **kwargs)
            werkzeug_logger.warning = filtered_warning
            
            self.app.run(
                host=self.host,
                port=self.port,
                debug=self.debug,
                use_reloader=False  # Disable reloader in threaded mode
            )
        except Exception as e:
            self.logger.error(f"API server error: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop the API server."""
        try:
            self.is_running = False
            self.logger.info("API server stopped")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop API server: {e}")
            return False
    
    def is_server_running(self) -> bool:
        """Check if the server is running."""
        return self.is_running

# XY Positioning System

This document describes the XY positioning system extension for the servo control system. The XY system provides precise positioning control using stepper motors and endstop switches, designed for applications like button pressing or precise positioning tasks.

## Overview

The XY positioning system consists of:
- Two stepper motors (X and Y axes)
- Two endstop switches for homing
- 4x4 button grid positioning system
- REST API for remote control
- Python API for programmatic control

## Hardware Requirements

### Stepper Motors
- 2x Stepper motors with step/direction control
- Compatible stepper motor drivers (A4988, DRV8825, etc.)

### Endstop Switches
- 2x Endstop switches (normally open or normally closed)
- Pull-up resistors (handled by Raspberry Pi GPIO)

### GPIO Pin Configuration
The system uses the following GPIO pins (configurable in `config.yaml`):

| Component | GPIO Pin | Description |
|-----------|----------|-------------|
| X Step    | 23       | Step signal for X motor |
| X Dir     | 24       | Direction signal for X motor |
| X Endstop | 25       | Endstop switch for X axis |
| Y Step    | 17       | Step signal for Y motor |
| Y Dir     | 27       | Direction signal for Y motor |
| Y Endstop | 22       | Endstop switch for Y axis |

## Software Architecture

### Core Components

1. **XYStepperHardware** (`xy_hardware.py`)
   - Low-level GPIO control
   - Stepper motor step generation
   - Endstop monitoring
   - Hardware initialization and cleanup

2. **XYController** (`xy_controller.py`)
   - High-level positioning control
   - Homing sequence management
   - Button grid positioning
   - Position tracking and validation

3. **API Integration** (`api_server.py`)
   - REST API endpoints for XY control
   - Integration with existing servo API
   - Remote control capabilities

## Configuration

The XY system is configured in `config.yaml`:

```yaml
xy_system:
  # Button grid configuration
  button_grid:
    rows: 4
    cols: 4
    spacing_x: 100  # Steps between buttons horizontally
    spacing_y: 100  # Steps between buttons vertically
  
  # Hardware configuration
  xy_hardware:
    pins:
      step_x: 23
      dir_x: 24
      endstop_x: 25
      step_y: 17
      dir_y: 27
      endstop_y: 22
    
    # Timing configuration
    step_delay: 0.001  # Delay between steps in seconds
    homing_delay: 0.001  # Delay during homing sequence
    homing_steps_back: 100  # Steps to move back from endstop after homing
```

## Usage

### API Authentication

All API endpoints require authentication using an API key. Set the API key as an environment variable:

```bash
export SERVO_API_KEY="your-api-key-here"
```

Or add it to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
echo 'export SERVO_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Python API

```python
from xy_controller import XYController
import yaml

# Load configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Initialize controller
xy_controller = XYController(config)

# Initialize system (home both axes)
xy_controller.initialize_system()

# Move to absolute position
xy_controller.move_to(100, 150)

# Move relative to current position
xy_controller.move_relative(50, -25)

# Move to specific button in grid
xy_controller.move_to_button(2, 3)  # Row 2, Column 3

# Get current position
position = xy_controller.get_position()
print(f"Current position: ({position[0]}, {position[1]})")

# Get system status
status = xy_controller.get_status()
print(f"System ready: {status['controller']['is_ready']}")

# Cleanup
xy_controller.cleanup()
```

### REST API

The system provides REST API endpoints for remote control:

#### Get XY Status
```bash
GET /api/xy/status
```

#### Get Current Position
```bash
GET /api/xy/position
```

#### Move to Absolute Position
```bash
curl -X POST http://localhost:5000/api/xy/move \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SERVO_API_KEY" \
  -d '{
    "x": 100,
    "y": 150
  }'
```

#### Move Relative
```bash
curl -X POST http://localhost:5000/api/xy/move-relative \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SERVO_API_KEY" \
  -d '{
    "dx": 50,
    "dy": -25
  }'
```

#### Move to Button
```bash
curl -X POST http://localhost:5000/api/xy/button/2/3 \
  -H "X-API-Key: $SERVO_API_KEY"
```

#### Get Button Positions
```bash
curl -X GET http://localhost:5000/api/xy/buttons \
  -H "X-API-Key: $SERVO_API_KEY"
```

#### Home System
```bash
curl -X POST http://localhost:5000/api/xy/home \
  -H "X-API-Key: $SERVO_API_KEY"
```

#### Get XY Status
```bash
curl -X GET http://localhost:5000/api/xy/status \
  -H "X-API-Key: $SERVO_API_KEY"
```

#### Get Current Position
```bash
curl -X GET http://localhost:5000/api/xy/position \
  -H "X-API-Key: $SERVO_API_KEY"
```

## Homing Sequence

The system performs the following homing sequence on initialization:

1. **X Axis Homing**:
   - Set direction to clockwise
   - Move until X endstop is triggered
   - Stop movement

2. **Y Axis Homing**:
   - Set direction to clockwise
   - Move until Y endstop is triggered
   - Stop movement

3. **Home Position Setup**:
   - Move both axes back by `homing_steps_back` steps
   - Set position counters to (0, 0)
   - Mark system as homed

## Button Grid System

The system supports a configurable button grid for easy positioning:

- **Grid Size**: 4x4 by default (configurable)
- **Spacing**: Configurable step spacing between buttons
- **Coordinates**: Row/column based (0-indexed)
- **Position Calculation**: `x = col * spacing_x`, `y = row * spacing_y`

### Button Grid Layout
```
(0,0) (0,1) (0,2) (0,3)
(1,0) (1,1) (1,2) (1,3)
(2,0) (2,1) (2,2) (2,3)
(3,0) (3,1) (3,2) (3,3)
```

## Safety Features

- **Endstop Monitoring**: Continuous monitoring during movement
- **Emergency Stop**: Immediate stop of all movements
- **Position Validation**: Prevents movement outside safe ranges
- **Thread Safety**: Safe concurrent access to positioning functions
- **Graceful Shutdown**: Proper cleanup on system shutdown

## Testing

### Test Script
Run the comprehensive test script:

```bash
python tests/test_xy_system.py
```

This will test:
- Homing sequence
- Absolute movement
- Relative movement
- Button grid positioning
- Status and information retrieval

### Example Script
Run the example script to see basic usage:

```bash
python examples/xy_positioning_example.py
```

## Troubleshooting

### Common Issues

1. **Homing Fails**:
   - Check endstop wiring and pull-up resistors
   - Verify GPIO pin configuration
   - Check endstop switch functionality

2. **Motors Don't Move**:
   - Verify stepper motor driver connections
   - Check step and direction pin wiring
   - Verify power supply to motors

3. **Inaccurate Positioning**:
   - Calibrate step delays for your motors
   - Check for mechanical binding
   - Verify endstop repeatability

4. **API Errors**:
   - Check API key configuration
   - Verify network connectivity
   - Check server logs for detailed errors

### Debug Mode

Enable debug logging by setting the log level to DEBUG in `config.yaml`:

```yaml
logging:
  level: "DEBUG"
```

## Integration with Servo System

The XY positioning system integrates seamlessly with the existing servo control system:

- **Unified API**: Both systems accessible through the same API server
- **Combined Status**: Status endpoint shows both servo and XY system status
- **Shared Configuration**: Single configuration file for both systems
- **Coordinated Control**: Can control both servos and XY positioning simultaneously

## Future Enhancements

- **Z-axis Support**: Add vertical positioning capability
- **Speed Control**: Variable speed movement profiles
- **Path Planning**: Smooth curved movements
- **Collision Detection**: Prevent movements that would cause collisions
- **Calibration Tools**: Automated calibration procedures
- **Web Interface**: Visual control interface for XY positioning

## Hardware Setup Guide

### Wiring Diagram

```
Raspberry Pi Zero 2 W
├── GPIO 23 → X Step (Stepper Driver)
├── GPIO 24 → X Dir (Stepper Driver)
├── GPIO 25 → X Endstop (with pull-up)
├── GPIO 17 → Y Step (Stepper Driver)
├── GPIO 27 → Y Dir (Stepper Driver)
└── GPIO 22 → Y Endstop (with pull-up)

Stepper Drivers
├── X Driver: Step, Dir, Enable, VCC, GND
└── Y Driver: Step, Dir, Enable, VCC, GND

Endstops
├── X Endstop: Signal to GPIO 25, VCC to 3.3V, GND
└── Y Endstop: Signal to GPIO 22, VCC to 3.3V, GND
```

### Power Requirements

- **Raspberry Pi**: 5V, 2.5A (official power supply recommended)
- **Stepper Motors**: Depends on motor specifications
- **Stepper Drivers**: 12V-24V typically
- **Endstops**: 3.3V logic level

### Mechanical Considerations

- **Mounting**: Secure mounting of motors and endstops
- **Belt/Pulley System**: Ensure proper tension and alignment
- **Endstop Placement**: Position for reliable homing
- **Cable Management**: Prevent interference with movement

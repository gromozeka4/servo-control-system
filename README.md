# Servo Control System for Raspberry Pi

A comprehensive Python-based servo control system designed for Raspberry Pi with PCA9685 PWM controller. This system provides precise servo control, movement sequences, scheduling, and HTTP API access.

> **Repository**: `servo-control-system`

## Features

## Features

- **Hardware Control**: Direct control of up to 16 servos via PCA9685 I2C PWM controller
- **Movement Sequences**: Define and execute complex movement patterns
- **Scheduling**: Schedule sequences to run at specific times or intervals
- **HTTP API**: Remote control via REST API endpoints
- **Safety Features**: Emergency stop, power management, and movement limits
- **Logging**: Comprehensive logging with rotation and multiple levels
- **Modular Design**: Clean, extensible architecture for future enhancements

## Hardware Requirements

- Raspberry Pi (Zero 2 W recommended for low power consumption)
- Grove PCA9685 16-channel PWM controller
- SG90 micro servos (or compatible 3-wire servos)
- Breadboard and jumper wires
- Adequate power supply for servos

## Hardware Connections

### PCA9685 to Raspberry Pi
- **GND** → Pi GND (Pin 6)
- **VCC** → Pi 3.3V (Pin 1) 
- **SDA** → Pi GPIO2 (Pin 3)
- **SCL** → Pi GPIO3 (Pin 5)

### Servos to PCA9685
- **Brown (GND)** → PCA9685 GND
- **Red (5V)** → PCA9685 V+ (use external power supply for multiple servos)
- **Orange (Signal)** → PCA9685 channel pins (0-15)

## Installation

### 1. Prerequisites
Ensure your Raspberry Pi has:
- Raspberry Pi OS Lite (or full) with SSH enabled
- I2C enabled in `raspi-config`
- Python 3.7+ installed

### 2. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
pip3 install -r requirements.txt

# Or install manually:
pip3 install adafruit-circuitpython-pca9685
pip3 install adafruit-circuitpython-busdevice
pip3 install flask flask-cors
pip3 install schedule pyyaml colorlog
```

### 3. Verify I2C Setup
```bash
# Check if I2C is enabled
ls /dev/i2c*

# Scan for I2C devices
sudo i2cdetect -y 1

# You should see the PCA9685 at address 0x40
```

## Configuration

The system uses `config.yaml` for main configuration and `config.local.yaml` for local settings (API keys, IP addresses, domain names, etc.).

### **Main Configuration (`config.yaml`):**
Key settings include:

```yaml
hardware:
  i2c:
    bus: 1                    # I2C bus number
    address: 0x40            # PCA9685 address
  
  servos:
    pulse_range: [500, 2500] # Servo pulse width range (μs)
    angle_range: [0, 180]    # Servo angle range (degrees)

api:
  host: "0.0.0.0"           # API server host
  port: 5000                 # API server port

sequences:
  wave:                      # Example sequence
    - channel: 0
      angle: 90
      duration: 1.0
    - channel: 1
      angle: 45
      duration: 1.0
```

## Usage

### 1. Configure Local Settings
```bash
# Copy the local configuration template
cp config.local.yaml config.local.yaml

# Edit with your API key and Pi IP address
nano config.local.yaml
```

### 2. Test the System
```bash
# Run the test script to verify hardware
python3 tests/test_servo.py
```

### 3. Start the Main Application
```bash
# Start with HTTP API
python3 main.py

# Start without API (hardware only)
python3 main.py --no-api

# Use custom config file
python3 main.py --config my_config.yaml
```

**Two entry points:**

- **`main.py`** – Production entry point. Runs the full system (servo + XY + optional API) with config-driven logging, local config merge (`config.local.yaml`), and network discovery. Use this for deployment and for the systemd service. Options: `--no-api`, `--config`, `--test-mode`.
- **`start_servo_system.py`** – Flexible startup for development and testing. Choose what to run via `--mode`:
  - `hardware` – Servo + XY only (no API or web)
  - `api` – Servo + XY + HTTP API (port 5000)
  - `web` – Servo + XY + web UI (port 8080)
  - `xy` – XY positioning only
  - `full` – API + web interface (default)

  Example: `python3 start_servo_system.py --mode api --config config.yaml`

### 4. HTTP API Endpoints

**Note**: The system automatically uses your Pi's IP address from `config.local.yaml`

**Important**: All API endpoints require an API key in the `X-API-Key` header. Get your API key from `config.local.yaml`.

#### Servo Control
```bash
# Move servo to specific angle
curl -X POST http://YOUR_PI_IP:5000/api/servo/0/move \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"angle": 90, "duration": 2.0}'

# Get servo position
curl -H "X-API-Key: YOUR_API_KEY" http://YOUR_PI_IP:5000/api/servo/0/position

# Release servo (power off)
curl -X POST http://YOUR_PI_IP:5000/api/servo/0/release \
  -H "X-API-Key: YOUR_API_KEY"
```

#### Sequence Management
```bash
# List available sequences
curl http://YOUR_PI_IP:5000/api/sequences

# Run a sequence
curl -X POST http://YOUR_PI_IP:5000/api/sequences/wave/run \
  -H "Content-Type: application/json" \
  -d '{"repeat_count": 3}'

# Create new sequence
curl -X POST http://YOUR_PI_IP:5000/api/sequences \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_sequence",
    "steps": [
      {"channel": 0, "angle": 0, "duration": 1.0},
      {"channel": 1, "angle": 90, "duration": 1.0}
    ]
  }'
```

#### Scheduling
```bash
# Schedule daily sequence
curl -X POST http://YOUR_PI_IP:5000/api/schedule/daily \
  -H "Content-Type: application/json" \
  -d '{
    "sequence_name": "wave",
    "time": "09:00",
    "repeat_count": 1
  }'

# Schedule recurring sequence
curl -X POST http://YOUR_PI_IP:5000/api/schedule/recurring \
  -H "Content-Type: application/json" \
  -d '{
    "sequence_name": "wave",
    "interval_minutes": 30,
    "repeat_count": 1
  }'
```

#### System Control
```bash
# Get system status
curl http://YOUR_PI_IP:5000/api/status

# Emergency stop
curl -X POST http://YOUR_PI_IP:5000/api/emergency/stop

# Release all servos
curl -X POST http://YOUR_PI_IP:5000/api/servo/release-all
```

## Architecture

The system consists of several modular components:

- **`servo_hardware.py`**: Low-level hardware interface for PCA9685 and servos
- **`servo_controller.py`**: High-level controller for sequences and scheduling
- **`api_server.py`**: HTTP API server for remote control
- **`main.py`**: Production entry point (servo + XY + optional API; config-driven logging and network discovery)
- **`start_servo_system.py`**: Optional startup script with `--mode` (hardware / api / web / xy / full) for development and testing

## Safety Features

- **Emergency Stop**: Immediately stops all movements and releases servos
- **Movement Limits**: Prevents servos from moving beyond safe angles
- **Power Management**: Automatically releases PWM signals when not in use
- **Concurrent Movement Limits**: Prevents too many servos from moving simultaneously
- **Graceful Shutdown**: Proper cleanup on system shutdown

## Troubleshooting

### Common Issues

1. **I2C Connection Failed**
   - Verify I2C is enabled: `sudo raspi-config` → Interface Options → I2C
   - Check wiring connections
   - Verify PCA9685 address: `sudo i2cdetect -y 1`

2. **Servos Not Moving**
   - Check power supply adequacy
   - Verify servo connections (GND, V+, Signal)
   - Check pulse range settings in config
   - Ensure servos are compatible with 50Hz PWM

3. **API Server Won't Start**
   - Check if port 5000 is available
   - Verify firewall settings
   - Check logs in `logs/servo_control.log`

4. **Permission Errors**
   - Ensure user has access to I2C devices
   - May need to run with `sudo` for hardware access

### Debug Mode
```bash
# Enable debug logging in config.yaml
logging:
  level: "DEBUG"

# Check logs
tail -f logs/servo_control.log
```

## Development

### Adding New Features
The modular design makes it easy to extend:

1. **New Hardware Types**: Extend `ServoHardware` class
2. **New Movement Patterns**: Add to sequence definitions
3. **New API Endpoints**: Extend `ServoAPIServer` class
4. **New Scheduling**: Extend `ServoController` class

### Testing
```bash
# Run hardware tests
python3 tests/test_servo.py

# Run specific tests
python3 -m pytest tests/  # If using pytest
```

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs in `logs/servo_control.log`
3. Verify hardware connections
4. Test with the provided test script

## Future Enhancements

- Web-based control interface
- Mobile app support
- Advanced movement interpolation
- Machine learning for movement optimization
- Integration with home automation systems
- Support for additional servo types
- Real-time movement visualization

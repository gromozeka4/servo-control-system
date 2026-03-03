#!/bin/bash
# Installation script for Servo Control System
# Repository: servo-control-system
# Run this script on your Raspberry Pi to set up the system

set -e  # Exit on any error

echo "=== Servo Control System Installation ==="
echo "This script will install all dependencies and set up the system."
echo "Make sure you're running this on a Raspberry Pi with internet access."
echo

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi."
    echo "   The installation may not work correctly on other systems."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "❌ Please don't run this script as root (sudo)."
    echo "   Run it as a regular user instead."
    exit 1
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    i2c-tools \
    git \
    curl \
    wget

# Enable I2C interface
echo "🔌 Enabling I2C interface..."
if ! grep -q "i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
    echo "i2c_arm=on added to /boot/config.txt"
else
    echo "I2C already enabled in /boot/config.txt"
fi

# Check if I2C is loaded
if ! lsmod | grep -q "i2c_bcm2708\|i2c_bcm2835"; then
    echo "⚠️  I2C module not loaded. You may need to reboot after installation."
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv servo_env
source servo_env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Set up systemd service (optional)
echo "⚙️  Setting up systemd service..."
cat > servo-control.service << EOF
[Unit]
Description=Servo Control System
After=network.target i2c-dev.service
Wants=i2c-dev.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/servo_env/bin
ExecStart=$(pwd)/servo_env/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Install systemd service
sudo cp servo-control.service /etc/systemd/system/
sudo systemctl daemon-reload

echo
echo "✅ Installation completed successfully!"
echo
echo "Next steps:"
echo "1. Reboot your Raspberry Pi to enable I2C:"
echo "   sudo reboot"
echo
echo "2. After reboot, test the system:"
echo "   source servo_env/bin/activate"
echo "   python3 tests/test_servo.py"
echo
echo "3. Start the main application:"
echo "   source servo_env/bin/activate"
echo "   python3 main.py"
echo
echo "4. (Optional) Enable auto-start on boot:"
echo "   sudo systemctl enable servo-control"
echo "   sudo systemctl start servo-control"
echo
echo "5. Check system status:"
echo "   sudo systemctl status servo-control"
echo
echo "📖 For more information, see README.md"
echo "🐛 For troubleshooting, check logs/ directory"
echo
echo "Happy servo controlling! 🎮"


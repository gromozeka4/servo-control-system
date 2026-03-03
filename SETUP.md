# Setup Guide for Servo Control System

> **Repository**: `servo-control-system`

## 🚀 **Quick Setup for Your Team**

### **Step 1: Generate API Key**
```bash
# Generate a secure API key for your team
python3 -c "import secrets; print('Team API Key:', secrets.token_urlsafe(32))"

# Example output:
# Team API Key: k8XmP9vN2qR7sL4wE1hJ6gF3dA8zC5xV9bN1mK4pQ7sL2wE5hJ8gF3dA6zC9xV
```

### **Step 2: Configure Local Settings**
1. **Copy the template file:**
   ```bash
   cp config.local.yaml config.local.yaml
   ```

2. **Edit the file with your settings:**
   ```bash
   nano config.local.yaml
   ```

3. **Fill in your details:**
   ```yaml
   api_keys:
     team_key: "YOUR_ACTUAL_API_KEY_HERE"
   
   local_network:
     # Option 1: Use IP address
     pi_ip_address: "192.168.1.100"  # Your Pi's actual IP
     
     # Option 2: Use domain name (recommended)
     pi_domain_name: "raspberrypi.local"  # mDNS (Bonjour)
     # OR
     pi_domain_name: "servo-pi.yourcompany.com"  # Custom domain
   ```

### **Step 3: Deploy to Raspberry Pi**
```bash
# SSH into your Pi
ssh pi@<your-pi-ip>

# Clone the repository
git clone <your-repo-url>
cd servo-control-system

# Copy and configure local settings
cp config.local.yaml config.local.yaml
nano config.local.yaml  # Edit with your API key and Pi IP

# Run installation
chmod +x install.sh
./install.sh
```

## 🔑 **API Key Management**

### **Single Team Key (Recommended):**
```yaml
# config.local.yaml
api_keys:
  team_key: "your-secure-api-key-here"
```

### **Multiple Individual Keys:**
```yaml
# config.local.yaml
api_keys:
  keys:
    - "johns-personal-key-here"
    - "sarahs-personal-key-here"
    - "mikes-personal-key-here"
```

### **Environment Variables (Alternative):**
```bash
# On your Pi, set environment variables
export SERVO_API_KEY="your-api-key-here"
echo 'export SERVO_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## 🌐 **Network Configuration**

### **Option 1: IP Address (Simple)**
```bash
# On your Raspberry Pi
hostname -I

# Or check your router's admin panel
# Look for "Raspberry Pi" in connected devices
```

### **Option 2: Domain Name (Recommended)**
Domain names are more reliable than IP addresses because they don't change when your network configuration changes.

#### **mDNS (Bonjour) - Automatic:**
```bash
# On your Pi, enable mDNS
sudo apt install avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Your Pi will be available at:
# raspberrypi.local (default hostname)
# OR your-custom-hostname.local
```

#### **Custom Domain:**
```bash
# In your company's DNS, add:
# servo-pi.yourcompany.com -> 192.168.1.100
# OR use a subdomain like:
# pi.yourcompany.com -> 192.168.1.100
```

### **Update Local Config:**
```yaml
# config.local.yaml
local_network:
  # Use either IP or domain (domain takes precedence)
  pi_ip_address: "192.168.1.100"  # Fallback IP
  pi_domain_name: "raspberrypi.local"  # Primary address
```

## 🔒 **Security Setup**

### **Company VPN + API Key:**
1. **VPN Layer**: Controls network access (company managed)
2. **API Key Layer**: Controls application access (your team)

### **Access Control:**
```yaml
# config.local.yaml
local_security:
  require_api_key: true
  
  # Optional: restrict to your network
  ip_whitelist:
    - "192.168.1.0/24"  # Your local network
```

## 📱 **Usage Examples**

### **From Your Computer (connected to company VPN):**
```bash
# Replace YOUR_PI_IP with actual IP from config.local.yaml
curl -H "X-API-Key: your-api-key" \
     http://YOUR_PI_IP:5000/api/status

# Move servo
curl -X POST http://YOUR_PI_IP:5000/api/servo/0/move \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"angle": 90, "duration": 2.0}'
```

### **Web Interface:**
1. Open `http://YOUR_PI_IP:8080`
2. Enter your API key
3. Start controlling servos!

### **Python Scripts:**
```python
import requests

headers = {'X-API-Key': 'your-api-key'}
response = requests.get('http://YOUR_PI_IP:5000/api/status', headers=headers)
```

## 🚨 **Important Security Notes**

### **Never Commit Secrets:**
- ✅ `config.local.yaml` is in `.gitignore`
- ✅ API keys are not stored in the repository
- ✅ Each team member has their own local config

### **Key Security:**
- 🔑 **Use strong keys** (32+ characters)
- 🔑 **Rotate keys regularly** (monthly recommended)
- 🔑 **Don't share keys** outside your team
- 🔑 **Revoke access immediately** if needed

### **Network Security:**
- 🌐 **Company VPN** controls network access
- 🌐 **API keys** control application access
- 🌐 **Both layers** provide comprehensive security

## 🔧 **Troubleshooting**

### **API Key Not Working:**
```bash
# Check if key is loaded
python3 -c "
import yaml
with open('config.local.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print('API Keys:', config.get('api_keys', {}))
"

# Check environment variables
echo $SERVO_API_KEY
```

### **Can't Connect to Pi:**
```bash
# Check Pi's IP address
ssh pi@<your-pi-hostname>
hostname -I

# Test connectivity
ping <pi-ip-address>

# Check if services are running
sudo systemctl status servo-control
```

### **Permission Denied:**
```bash
# Check I2C permissions
ls -la /dev/i2c*
sudo usermod -a -G i2c $USER
# Log out and back in
```

## 📋 **Team Setup Checklist**

### **For Each Team Member:**
- [ ] **Copy** `config.local.yaml` template
- [ ] **Generate** secure API key
- [ ] **Configure** Pi IP address
- [ ] **Test** API access
- [ ] **Test** web interface
- [ ] **Verify** servo control

### **For System Administrator:**
- [ ] **Deploy** to Raspberry Pi
- [ ] **Configure** local settings
- [ ] **Test** all functionality
- [ ] **Share** setup instructions
- [ ] **Monitor** system logs
- [ ] **Backup** configuration

## 🎯 **Quick Test Commands**

```bash
# Test API access (replace with your actual address)
curl -H "X-API-Key: your-key" http://YOUR_PI_IP:5000/api/health
# OR if using domain:
curl -H "X-API-Key: your-key" http://raspberrypi.local:5000/api/health

# Test servo movement
curl -X POST http://YOUR_PI_IP:5000/api/servo/0/move \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"angle": 90, "duration": 1.0}'

# Test web interface
open http://YOUR_PI_IP:8080
# OR if using domain:
open http://raspberrypi.local:8080
```

### **Test Domain Resolution:**
```bash
# Test if domain resolves
nslookup raspberrypi.local
ping raspberrypi.local

# Test from your computer (connected to company VPN)
curl -H "X-API-Key: your-key" http://raspberrypi.local:5000/api/health
```

## 📞 **Need Help?**

1. **Check logs**: `tail -f logs/servo_control.log`
2. **Verify config**: `python3 -c "import yaml; print(yaml.safe_load(open('config.local.yaml')))"`
3. **Test hardware**: `python3 tests/test_servo.py`
4. **Check status**: `sudo systemctl status servo-control`

---

**Remember**: Keep your `config.local.yaml` file secure and never commit it to version control! 🔒

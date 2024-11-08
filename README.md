# Internet Radio for Raspberry Pi
A web-configurable internet radio system running on Raspberry Pi with physical controls and web interface.

## System Requirements & Dependencies

### Raspberry Pi Configuration
- **Operating System**: Raspberry Pi OS (Debian Bullseye) 64-bit
- **Recommended Model**: Raspberry Pi 4 Model B
- **Minimum Storage**: 8GB
- **Recommended Storage**: 16GB or larger

### System Packages
```bash
python3-venv (3.9.2-3)
python3-pip (20.3.4-4)
vlc (3.0.16-1)
pulseaudio (14.2-2)
pigpiod (1.79-1)
git (2.30.2-1)
unattended-upgrades (2.8)
dos2unix (7.4.1-1)
wireless-tools (30~pre9-13.1)
network-manager (1.30.6-1)
alsa-utils (1.2.4-1)
```

### Python Dependencies
```bash
flask==2.0.1
werkzeug==2.0.3
flask-cors==3.0.10
gpiozero==1.6.2
python-vlc==3.0.16120
pigpio==1.78
toml==0.10.2
```

### Hardware Requirements
- Raspberry Pi 4
- Audio output device (configured as card 2)
- 3 push buttons for stream selection
- 1 rotary encoder with push button for volume/reboot
- WiFi connectivity
- Power supply

### GPIO Pin Configuration
- Button 1: GPIO17
- Button 2: GPIO16
- Button 3: GPIO26
- Rotary Encoder:
  - CLK: GPIO11
  - DT: GPIO9
  - SW: GPIO10
- Status LED: GPIO4

## Software Components

### Core Application
- `main.py`: Main application handling GPIO inputs and stream management
- `app.py`: Flask web application setup
- `stream_manager.py`: Radio stream playback handler
- `wifi_manager.py`: WiFi connection manager
- `sounds.py`: System sound effects handler

### Web Interface
- Access via: `radio@{hostname}.local:5000`
- Pages:
  - Main control page (`/`)
  - WiFi settings (`/wifi-setup`)
  - Stream selection (`/stream-select`)
  - WiFi debugging (`/wifi-debug`)

### System Scripts
Located in `/scripts/`:
- `install_radio.sh`: Full system installation
- `uninstall_radio.sh`: Complete system removal
- `reinstall_radio.sh`: System reinstallation
- `monitor_radio.sh`: System monitoring
- `check_radio.sh`: System diagnostics
- `hardware_test.sh`: Hardware testing
- `update_radio.sh`: Software updates
- `runApp.sh`: Application startup

## System Services

### Created Services
The installation creates and manages the following systemd services:

1. **internetradio.service**
   - Main radio application service
   - Starts after network and pigpiod
   - Commands:
     ```bash
     sudo systemctl start internetradio
     sudo systemctl stop internetradio
     sudo systemctl restart internetradio
     sudo systemctl status internetradio
     ```
   - View logs:
     ```bash
     journalctl -u internetradio -f
     ```

2. **pigpiod.service**
   - GPIO interface daemon
   - Required for button and encoder functionality
   - Commands:
     ```bash
     sudo systemctl start pigpiod
     sudo systemctl stop pigpiod
     sudo systemctl restart pigpiod
     sudo systemctl status pigpiod
     ```

3. **network-manager.service**
   - Handles WiFi connections
   - Pre-installed but configured by installation
   - Commands:
     ```bash
     sudo systemctl start NetworkManager
     sudo systemctl stop NetworkManager
     sudo systemctl restart NetworkManager
     sudo systemctl status NetworkManager
     ```

### Service Dependencies
```
internetradio.service
└─ pigpiod.service
└─ network-manager.service
```

## WiFi Connection Process

### Normal Connection Flow
1. **Initial Boot**
   - System attempts to connect to previously saved networks
   - Makes 3 connection attempts for each saved network
   - Each attempt includes:
     - Connection attempt (2s timeout)
     - Internet verification (5s timeout)
     - Delay between attempts (2s)
   - Total maximum time until AP mode: ~27 seconds

2. **Connection Verification**
   - Checks if connection is established using `nmcli`
   - Verifies internet connectivity by pinging 8.8.8.8
   - Logs all connection attempts and results

3. **AP Mode Fallback**
   If no connection can be established:
   - System creates its own Access Point
   - SSID: "InternetRadio"
   - Password: "radiopassword"
   - Interface: wlan0
   - IP Address: Automatically assigned

### Access Point (AP) Mode
When in AP mode:
1. **Network Configuration**
   - Creates a WiFi network other devices can connect to
   - Uses NetworkManager for AP configuration
   - Provides DHCP for connected devices

2. **Web Interface Access**
   - Connect to "InternetRadio" WiFi network
   - Use password: "radiopassword"
   - Access web interface at: radio@{hostname}.local:5000
   - Example: If your radio's hostname is "{hostname}", use: radio@{hostname}.local:5000

3. **WiFi Setup**
   - Use web interface to scan for available networks
   - Select desired network and enter credentials
   - System will attempt to connect to new network
   - On success, AP mode is disabled automatically

### Network Management
- All WiFi credentials are stored by NetworkManager
- Previous connections are remembered and tried first
- System logs all connection attempts in `/logs/wifi.log`
- Web interface provides real-time connection status

## Monitoring and Maintenance

### System Monitoring
```bash
sudo ./scripts/monitor_radio.sh
```
Shows:
- Network status
- Service status
- Audio configuration
- Current stream

### Logs
Located in `/logs/`:
- `installation.log`: Installation process
- `app.log`: Runtime logs
- `wifi.log`: WiFi connection logs
- System service: `journalctl -u internetradio`

## Troubleshooting

### Common Issues
1. No Audio
   - Check audio device configuration in `/etc/asound.conf`
   - Verify volume settings
   - Check audio hardware connections

2. WiFi Issues
   - Use WiFi debug page: `http://<raspberry-pi-ip>:5000/wifi-debug`
   - Check network manager status
   - Verify WiFi credentials

3. Button/Encoder Not Responding
   - Run hardware test: `sudo ./scripts/hardware_test.sh`
   - Check GPIO connections
   - Verify pigpiod service is running

### Service Recovery
```bash
# Complete restart
sudo systemctl stop internetradio
sudo systemctl stop pigpiod
sudo systemctl start pigpiod
sudo systemctl start internetradio

# Check all services
systemctl is-active internetradio
systemctl is-active pigpiod
systemctl is-active NetworkManager
```
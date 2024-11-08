echo '# Internet Radio for Raspberry Pi
A web-configurable internet radio system running on Raspberry Pi with physical controls and web interface.

## Overview
This project turns a Raspberry Pi into an internet radio player with both physical controls and a web interface. Users can:
- Switch between radio streams using physical buttons
- Control volume using a rotary encoder
- Configure radio stations and WiFi through a web interface
- Reboot system using the rotary encoder'\''s push button

## Hardware Requirements
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
- Access via: `http://<raspberry-pi-ip>:5000`
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

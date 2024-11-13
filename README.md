# Internet Radio for Raspberry Pi

A Python-based internet radio player designed for Raspberry Pi, featuring GPIO controls, web interface, and automatic WiFi/Access Point management.

## Hardware Requirements

- Raspberry Pi (tested on Pi 3B+ and Pi 4)
- LED (connected to GPIO17)
- Rotary Encoder (connected to GPIO22, GPIO23)
- Push Button (connected to GPIO27)
- Audio output (bcm2835 Headphones - card 2)

## Software Requirements

### System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv alsa-utils hostapd dnsmasq vlc
```

### Python Dependencies
```requirements.txt
gpiozero
flask
python-vlc
toml
requests
netifaces
pytest
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/internetRadio.git
cd internetRadio
```

2. Set up ALSA configuration:
```bash
sudo bash -c 'echo -e "defaults.pcm.card 2\ndefaults.pcm.device 0\ndefaults.ctl.card 2" > /etc/asound.conf'
```

3. Run the installation script:
```bash
sudo ./scripts/install.sh
```

## Features

- [x] Audio System
  - [x] Hardware audio configuration (bcm2835)
  - [x] Volume control via ALSA
  - [x] VLC media player integration
  - [x] Sound file playback
  - [x] Stream playback
  - [x] Direct volume control
  - [x] Error handling and logging
- [ ] Web interface for control and configuration
- [ ] GPIO controls
  - [ ] LED status
  - [ ] Rotary encoder for volume
  - [ ] Button for play/pause
- [ ] Network Management
  - [ ] WiFi connection
  - [ ] Access Point fallback
- [ ] System monitoring

## GPIO Pin Configuration

- LED: GPIO17
- Rotary Encoder: GPIO22 (A), GPIO23 (B)
- Push Button: GPIO27

## Directory Structure

```
internetRadio/
├── config/             # Configuration files
├── logs/              # Application logs
├── scripts/           # Installation and maintenance scripts
│   ├── install.sh     # Installation script
│   ├── health_check.sh # System health monitoring
├── sounds/            # System sound files
├── src/               # Source code
│   ├── audio/         # Audio playback management ✓
│   ├── controllers/   # Main controllers
│   ├── hardware/      # GPIO management
│   ├── network/       # Network management
│   ├── utils/         # Utilities
│   └── web/           # Web interface
├── static/            # Web static files
└── tests/             # Unit and integration tests
```

## Testing

### Running Tests
Run the test suite:
```bash
python3 -m pytest tests/ -v
```

Run specific tests:
```bash
python3 -m pytest tests/test_audio_manager.py -v
python3 -m pytest tests/test_main.py -v
```

### Test Coverage
Current test coverage includes:

#### Main Application (test_main.py)
- Network initialization scenarios
- Radio controller initialization
- WiFi connection handling
- Signal handling and cleanup
- Resource management

#### Audio System (test_audio_manager.py)
- Hardware audio configuration
- Volume control and boundaries
- Stream playback
- Sound file playback
- Error handling and logging
- Resource cleanup
- ALSA error suppression
- Direct volume control

### Running Tests with Coverage Report
```bash
python3 -m pytest --cov=src tests/ --cov-report=term-missing
```

### Test Development
Tests follow these principles:
- Test-Driven Development (TDD)
- Single Responsibility
- Proper resource cleanup
- Mocking of hardware dependencies
- Isolation between test cases

## Service Management

```bash
# Start the service
sudo systemctl start internetradio

# Stop the service
sudo systemctl stop internetradio

# Check status
sudo systemctl status internetradio

# View logs
journalctl -u internetradio
```

## Health Check

Run the system health check:
```bash
sudo bash scripts/health_check.sh
```

## Troubleshooting

### Audio Issues
1. Check ALSA configuration:
```bash
cat /etc/asound.conf
```
2. Verify audio device:
```bash
amixer -c 2 controls
amixer -c 2 sget 'PCM'
```
3. Test audio:
```bash
aplay -l  # List audio devices
aplay /usr/share/sounds/alsa/Front_Center.wav  # Test playback
```

### DNS Issues
If DNS resolution stops working:
1. Check if /etc/resolv.conf exists and contains correct nameservers
2. Verify file permissions: `ls -la /etc/resolv.conf`
3. Check if file is immutable: `lsattr /etc/resolv.conf`
4. Run WiFiManager's configure_dns() method to reset configuration
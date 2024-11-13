# Internet Radio for Raspberry Pi

A Python-based internet radio player designed for Raspberry Pi, featuring GPIO controls, web interface, and automatic WiFi/Access Point management.

## Hardware Requirements

- Raspberry Pi (tested on Pi 3B+ and Pi 4)
- LED (connected to GPIO17)
- Rotary Encoder (connected to GPIO22, GPIO23)
- Push Button (connected to GPIO27)
- Audio output (3.5mm jack or HDMI)

## Software Requirements

### System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv alsa-utils hostapd dnsmasq
```

### Python Dependencies
- gpiozero
- flask
- vlc-python
- toml
- requests
- netifaces

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/internetRadio.git
cd internetRadio
```

2. Run the installation script:
```bash
sudo ./scripts/install.sh
```

## Features

- Web interface for control and configuration
- GPIO controls (LED status, rotary encoder for volume, button for play/pause)
- Automatic WiFi connection with fallback to Access Point mode
- Stream management and playback control
- Volume control
- System status monitoring

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
├── sounds/            # System sound files
├── src/               # Source code
│   ├── audio/         # Audio playback management
│   ├── controllers/   # Main controllers
│   ├── hardware/      # GPIO management
│   ├── network/       # Network management
│   ├── utils/         # Utilities
│   └── web/           # Web interface
├── static/            # Web static files
└── tests/             # Unit and integration tests
```

## Testing

Run the test suite:
```bash
python3 -m pytest tests/ -v
```

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

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here] 
Internet Radio for Raspberry Pi
=============================

A web-based internet radio player designed for Raspberry Pi. This application allows you to manage and play internet radio streams through a simple web interface, with persistent configuration and state management.

Features
--------
- Web-based interface for controlling radio playback
- Persistent station configuration and state
- Volume control with ALSA integration
- Automatic service management with systemd
- Configurable radio stations via TOML files
- Rotating log management

Installation
-----------
1. Clone the repository:
   git clone https://github.com/yourusername/internetRadio.git
   cd internetRadio

2. Make installation scripts executable:
   chmod +x scripts/*.sh

3. Run the installation script:
   sudo ./scripts/install.sh

Service Management
----------------
The radio runs as a systemd service. Here are the common commands:

# Start the service
sudo systemctl start radio

# Stop the service
sudo systemctl stop radio

# Restart the service
sudo systemctl restart radio

# Check service status
sudo systemctl status radio

# View logs
journalctl -u radio -f

# Enable service to start on boot
sudo systemctl enable radio

# Disable service from starting on boot
sudo systemctl disable radio

Architecture
-----------
The application follows a modular architecture:

internetRadio/
├── src/                    # Source code
│   ├── app/               # Flask application
│   │   ├── routes.py      # Web routes and API endpoints
│   │   └── service.py     # Radio service management
│   ├── player/            # Radio player implementation
│   │   └── radio_player.py
│   └── utils/             # Utility modules
│       ├── state_manager.py   # State persistence
│       └── stream_manager.py  # Stream configuration
├── static/                # Static web assets
├── templates/             # HTML templates
├── config/               # Configuration files
├── logs/                 # Application logs
├── scripts/              # Installation scripts
└── systemd/              # Service configuration

Dependencies
-----------
System Dependencies:
- python3: Runtime environment
- vlc: Media player backend
- alsa-utils: Audio system utilities
- git: Version control

Python Dependencies:
- flask: Web framework for the interface
- python-vlc: VLC media player bindings
- requests: HTTP client for stream testing
- tomli: TOML file parsing

Configuration
------------
Radio Stations:
Radio stations are configured in config/streams.toml:

[[links]]
name = "Station Name"
url = "http://stream.url"
description = "Station description"
country = "Country"

Default Settings:
Default settings are in config/config.toml:

default_volume = 80
default_stations = [
    "Station 1",
    "Station 2"
]

Development
----------
Running in Development Mode:
# Set Flask development mode
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run the application
python3 main.py

Log Files:
Logs are stored in logs/radio.log with automatic rotation:
- Maximum file size: 1MB
- Keeps 5 backup files
- Automatic compression of old logs

Testing:
Run unit tests:
python3 -m pytest tests/

Troubleshooting
--------------
Audio Issues:
1. Check ALSA device configuration:
   aplay -l

2. Verify volume levels:
   amixer -c 2

Service Issues:
1. Check service status:
   sudo systemctl status radio

2. View detailed logs:
   journalctl -u radio -f

Uninstallation
-------------
To remove the application:
sudo ./scripts/uninstall.sh

Contributing
-----------
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

License
-------
[Your License Here]

Authors
-------
[Your Name]

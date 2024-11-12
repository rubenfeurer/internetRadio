## Overview
A Raspberry Pi-based Internet Radio project with physical controls (buttons, encoder) and web interface. The project uses Python for the backend, Flask for the web interface, and handles both WiFi and Access Point modes.

## Current State
- Main application structure implemented
- Core controllers designed and partially implemented:
  - WebController (implemented with tests)
  - RadioController (implemented)
  - NetworkController (needs implementation)
- Hardware integration:
  - GPIO controls (implemented)
  - Audio playback (implemented)
  - LED status indicators (implemented)

## Project Structure
internetRadio/
├── config/
│ └── streams.json # Radio stream configurations
├── logs/ # Application logs
├── scripts/
│ └── various system scripts
├── sounds/ # System sound effects
├── src/
│ ├── audio/
│ │ └── audio_manager.py
│ ├── controllers/
│ │ ├── radio_controller.py
│ │ ├── network_controller.py
│ │ └── web_controller.py
│ ├── hardware/
│ │ └── gpio_manager.py
│ ├── network/
│ │ └── wifi_manager.py
│ ├── utils/
│ │ └── logger.py
│ └── web/
│ └── templates/
├── static/
│ └── css/
├── templates/
│ ├── index.html
│ ├── stream_select.html
│ └── wifi_settings.html
├── tests/
│ ├── test_audio_manager.py
│ ├── test_gpio_manager.py
│ ├── test_radio_controller.py
│ └── test_web_controller.py
├── main.py
└── runApp.sh


# Add Dependencies section
echo '
## Dependencies
- Python 3.11+
- Flask
- pigpio
- VLC
- Network management tools (iwconfig, ifconfig)

## Core Components

### RadioController
Manages audio playback, GPIO interactions, and stream handling.
- Status: Implemented
- Features:
  - Stream playback control
  - Volume control
  - Physical button handling
  - LED status indication
  - Stream configuration management

### WebController
Handles web interface and API endpoints.
- Status: Implemented with tests
- Features:
  - Stream selection/control
  - WiFi configuration
  - Status monitoring
  - API endpoints for all functions

### NetworkController
Manages network connectivity and AP mode.
- Status: Needs implementation
- Features:
  - WiFi scanning/connection
  - AP mode management
  - Network status monitoring' >> README.md

# Add Hardware Setup and Implementation Details
echo '
## Hardware Setup
- Raspberry Pi (tested on Pi 4)
- Rotary Encoder (Volume control)
- Push Buttons (Stream control)
- LED (Status indicator)
- Audio output (3.5mm jack or HDMI)

## Current Implementation Details

### Main Application Flow
python
def main():
# Initialize controllers
radio = RadioController()
network = NetworkController()
web = WebController(radio, network)
# Setup network
wifi_connected = network.check_and_setup_network()
# Start web interface
web.start()
# Main loop
while True:
# Monitor states
radio.monitor()
network.monitor()


# Add Web Routes and Next Steps
echo '
### Web Routes
- `/` - Main interface
- `/stream-select/<channel>` - Stream selection
- `/wifi-settings` - Network configuration
- `/wifi-scan` - Network scanning
- `/connect` - WiFi connection
- `/play-stream` - Stream control
- `/stream-status` - Playback status

## Next Steps
1. Implement NetworkController
2. Add tests for NetworkController
3. Implement stream configuration handling
4. Add system startup/shutdown handlers
5. Implement error recovery mechanisms

## Testing
- Unit tests implemented for WebController
- Test coverage needed for:
  - RadioController
  - NetworkController
  - Integration tests

## Notes
- Project uses Flask development server - production deployment needs consideration
- WiFi/AP mode switching needs careful handling to prevent lockouts
- Stream configuration should be persisted across reboots
- Error handling and recovery mechanisms are crucial for stability

## Configuration Files
streams.json format:
json
[
{
"name": "Stream Name",
"url": "http://stream.url",
"country": "Country",
"location": "Location"
}
]
# Internet Radio Project

## Overview
A Raspberry Pi-based Internet Radio project with physical controls (buttons, encoder) and web interface. The project uses Python for the backend, Flask for the web interface, and handles both WiFi and Access Point modes.

## Current State
- All core components implemented and tested
- Full test coverage achieved (75 passing tests)
- Components integrated and verified:
  - WebController (implemented with tests)
  - RadioController (implemented with tests)
  - NetworkController (implemented with tests)
  - Logger (implemented with tests)
  - StreamManager (implemented with tests)

## Project Structure
internetRadio/
├── config/
│   ├── default.toml      # Default configurations
│   └── streams.toml      # Radio stream configurations
├── logs/                 # Application logs
├── src/
│   ├── audio/
│   │   └── audio_manager.py
│   ├── controllers/
│   │   ├── radio_controller.py
│   │   ├── network_controller.py
│   │   └── web_controller.py
│   ├── hardware/
│   │   └── gpio_manager.py
│   ├── models/
│   │   └── radio_stream.py
│   ├── network/
│   │   ├── wifi_manager.py
│   │   └── ap_manager.py
│   ├── utils/
│   │   ├── logger.py
│   │   ├── config_manager.py
│   │   └── stream_manager.py
│   └── web/
│       └── templates/
├── static/
│   └── css/
├── templates/
│   ├── index.html
│   ├── stream_select.html
│   └── wifi_settings.html
├── tests/
│   ├── integration/
│   │   └── test_system_integration.py
│   ├── test_audio_manager.py
│   ├── test_gpio_manager.py
│   └── ... (other test files)
├── main.py
└── runApp.sh

## Dependencies
- Python 3.11+
- Flask
- pigpio
- VLC
- toml
- Network management tools (iwconfig, ifconfig)

## Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install flask pigpio python-vlc toml
   ```
3. Start pigpiod service:
   ```bash
   sudo systemctl enable pigpiod
   sudo systemctl start pigpiod
   ```

## Running the Application
```bash
chmod +x runApp.sh
./runApp.sh
```

## Core Components

### RadioController
Manages audio playback, GPIO interactions, and stream handling.
- Status: Fully implemented and tested
- Features:
  - Stream playback control
  - Volume control
  - Physical button handling
  - LED status indication
  - Stream configuration management

### WebController
Handles web interface and API endpoints.
- Status: Fully implemented and tested
- Features:
  - Stream selection/control
  - WiFi configuration
  - Status monitoring
  - API endpoints for all functions

### NetworkController
Manages network connectivity and AP mode.
- Status: Fully implemented and tested
- Features:
  - WiFi scanning/connection
  - AP mode management
  - Network status monitoring
  - Automatic fallback to AP mode

### Logger
Handles application logging.
- Status: Fully implemented and tested
- Features:
  - Singleton pattern
  - Multiple log files
  - Dynamic log levels
  - Test mode support

## Hardware Setup
- Raspberry Pi (tested on Pi 4)
- Rotary Encoder (Volume control)
- Push Buttons (Stream control)
- LED (Status indicator)
- Audio output (3.5mm jack or HDMI)

## Configuration
### streams.toml format:
```toml
[[links]]
name = "Stream Name"
url = "http://stream.url"
country = "Country"
location = "Location"
description = "Optional description"
genre = "Optional genre"
language = "Optional language"
bitrate = 128  # Optional bitrate
```

## Testing
- 75 passing tests covering all components
- Integration tests implemented
- Test coverage includes:
  - Unit tests for all components
  - Integration tests for system flow
  - Error handling scenarios
  - Network fallback scenarios

## Production Notes
- Currently uses Flask development server
- For production:
  1. Consider using Gunicorn or uWSGI
  2. Set up systemd service
  3. Configure proper logging rotation
  4. Implement proper security measures

## Error Recovery
- Automatic network fallback to AP mode
- Hardware component reinitializing
- Logging for debugging
- Graceful error handling

## Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License
MIT License

## API Endpoints

### Stream Control
- `GET /stream-status` - Get current stream playback status
- `POST /play-stream` - Start playing a stream (body: `url`)
- `POST /stop-stream` - Stop current stream playback
- `POST /update-stream` - Update stream configuration (body: `channel`, `selected_link`)

### WiFi Management
- `GET /wifi-scan` - Scan for available WiFi networks
- `POST /connect` - Connect to WiFi network (body: `ssid`, `password`)
- `POST /forget_network` - Remove saved network (body: `ssid`)
- `GET /network-status` - Get current network status

### Web Interface Routes
- `GET /` - Main interface
- `GET /stream_select/<channel>` - Stream selection page
- `GET /wifi_settings` - WiFi configuration page
- `GET /wifi_debug` - Network debugging information

## Using the Services

### Web Interface
1. Access the radio interface:
   - If connected to WiFi: `http://<raspberry-pi-ip>:5000`
   - In AP mode: Connect to "InternetRadio" network, then visit `http://192.168.4.1:5000`

2. Stream Control:
   - Click stream buttons to play/pause
   - Use "Select Stream" to change radio stations
   - Physical buttons correspond to web interface buttons

3. WiFi Setup:
   - Click "WiFi Settings" to manage connections
   - Available networks are automatically scanned
   - Saved networks show "Saved" label
   - Current connection shows "Connected" label

### Physical Controls
1. Buttons:
   - Button 1-3: Play/pause corresponding streams
   - Long press: Stop current playback
   - Double press: Next stream in current channel

2. Rotary Encoder:
   - Rotate clockwise: Volume up
   - Rotate counter-clockwise: Volume down
   - Press: Mute/unmute

3. LED Indicators:
   - Solid: Connected to WiFi
   - Fast blink: AP mode active
   - Slow blink: Playing stream
   - Off: No network connection

## Running Tests

### Unit Tests
Run all tests:
```bash
python3 -m pytest tests/ -v
```

Run specific test file:
```bash
python3 -m pytest tests/test_logger.py -v
```

Run tests with coverage:
```bash
python3 -m pytest tests/ --cov=src/
```

### Integration Tests
Run integration tests:
```bash
python3 -m pytest tests/integration/ -v
```

## Scripts and Utilities

### runApp.sh
Main application startup script:
```bash
chmod +x runApp.sh
./runApp.sh
```
Features:
- Creates log directories
- Sets initial audio volume
- Starts pigpiod daemon
- Launches main application
- Redirects output to logs

### Development Scripts
1. `tests/integration/test_system_integration.py`:
   - Full system integration tests
   - Tests component interactions
   - Verifies startup/shutdown sequences

2. `src/utils/config_migration.py`:
   - Handles configuration file updates
   - Migrates old settings
   - Validates configuration format

3. `src/utils/logger.py`:
   - Manages application logging
   - Supports multiple log files
   - Handles log rotation

### Configuration Files
1. `config/default.toml`:
   ```toml
   [audio]
   default_volume = 70
   volume_step = 5

   [network]
   ap_ssid = "InternetRadio"
   ap_password = "radiopassword"
   ```

2. `streams/default.toml`:
   ```toml
   [[links]]
   name = "Example Radio"
   url = "http://example.com/stream"
   country = "Example Country"
   ```

### Log Files
- `logs/app.log`: Main application logs
- `logs/radio.log`: Stream playback logs
- `logs/wifi.log`: Network connection logs
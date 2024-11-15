# Internet Radio for Raspberry Pi

A Python-based internet radio player designed for Raspberry Pi, featuring GPIO controls, web interface, and automatic WiFi/Access Point management.

## Hardware Requirements

- Raspberry Pi (tested on Pi 3B+ and Pi 4)
- LED (connected to GPIO17)
- Rotary Encoder (connected to GPIO22, GPIO23)
- Push Button (connected to GPIO27)
- Audio output (bcm2835 Headphones - card 2)

## Audio System

### Sound Players
The system uses VLC for audio playback in two contexts:

1. **Main Audio Player (VLC)**
   - Used for streaming radio stations
   - Handles volume control
   - Manages main audio output
   - Location: `src/audio/audio_manager.py`

2.  **System Sounds**
   - Uses the same AudioManager for consistency
   - Plays notification sounds (success.wav, error.wav, etc.)
   - Handles system events and feedback
   - Sound files location: `sounds/`

### Sound Files
System sound files are located in the `sounds/` directory:
- `success.wav` - Played when operations (like WiFi connection) are successful
- `error.wav` - Played when operations fail

### Testing Sounds
Test the audio system using:
```bash
python3 scripts/test_sounds.py
```

## Software Requirements

### System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv alsa-utils hostapd dnsmasq vlc xterm network-manager
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
│   └── health_check.sh # System health monitoring
├── services/          # Service configuration files
│   ├── internetradio.service  # Main radio service
│   ├── radiomonitor.service   # System monitor service
│   ├── logrotate.conf        # Log rotation config
│   └── network.conf         # Network configuration
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

## Testing Best Practices

### Mocking Loggers and File Handlers

When testing components that use Python's logging system, follow these guidelines:

1. **Logger Cleanup**
   - Clear existing loggers before each test
   - Reset logger instances between tests
   ```python
   logging.getLogger().handlers = []
   logging.Logger.manager.loggerDict.clear()
   if hasattr(Logger, '_instances'):
       Logger._instances = {}
   ```

2. **Mocking StreamHandler**
   - Use NullHandler instead of mocking StreamHandler directly
   - Patch at the module level where StreamHandler is used
   ```python
   @patch('src.utils.logger.logging.StreamHandler', return_value=logging.NullHandler())
   ```

3. **Mocking RotatingFileHandler**
   - Patch at the module level, not logging.handlers
   - Create mock instance with proper configuration
   ```python
   @patch('src.utils.logger.RotatingFileHandler')
   def test_method(self, mock_handler):
       mock_instance = MagicMock()
       mock_handler.return_value = mock_instance
   ```

4. **Testing Singletons**
   - Reset singleton instances before each test
   - Verify handler creation happens only once
   - Test both logger reuse and handler creation
   ```python
   def test_singleton_behavior(self):
       logger1 = Logger('test')
       self.mock_rotating.reset_mock()
       logger2 = Logger('test')
       self.mock_rotating.assert_not_called()
   ```

5. **Resource Cleanup**
   - Close file handlers in tearDown
   - Remove test log files
   - Reset all mocks between tests
   ```python
   def tearDown(self):
       logging.getLogger().handlers = []
       for filename in os.listdir(self.test_log_dir):
           try:
               os.unlink(os.path.join(self.test_log_dir, filename))
           except Exception:
               pass
   ```

### Common Mocking Issues

1. **"not readable" Error**
   - Cause: Trying to mock StreamHandler directly
   - Solution: Use NullHandler or patch at correct module level

2. **Unclosed File Handlers**
   - Cause: Not properly cleaning up file handlers
   - Solution: Clear handlers in setUp and tearDown

3. **Invalid Spec Error**
   - Cause: Trying to spec a mock object
   - Solution: Create mock instance first, then configure return value

4. **Multiple Handler Creation**
   - Cause: Not resetting singleton instances
   - Solution: Clear _instances dict between tests

5. **Resource Warnings**
   - Cause: Unclosed file handlers
   - Solution: Proper cleanup in tearDown

### Test Isolation Best Practices

1. **Use setUp/tearDown**
   - Initialize test environment
   - Clean up resources
   - Reset mocks and instances

2. **Mock Dependencies**
   - Patch at module level
   - Use proper return values
   - Reset mocks between tests

3. **Handle File Operations**
   - Use temporary directories
   - Clean up files after tests
   - Close all handlers

4. **Test Singleton Pattern**
   - Reset instance cache
   - Verify handler creation
   - Test instance reuse

5. **Resource Management**
   - Track created resources
   - Clean up in reverse order
   - Handle exceptions in cleanup

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

## Core Components

### Main Application Files
- `main.py` - Application entry point, initializes and coordinates all components
- `src/app.py` - Main RadioApp class that handles core radio functionality

### Controllers
- `src/controllers/radio_controller.py` - Manages radio operations (playback, stations)
- `src/controllers/network_controller.py` - Handles network connectivity and mode switching
- `src/web/web_controller.py` - Manages web interface and API endpoints

### Audio System
- `src/audio/audio_manager.py` - Handles all audio playback (VLC-based):
  - Radio stream playback
  - System sound notifications
  - Volume control
  - Audio device management

### Network Management
- `src/network/wifi_manager.py` - Manages WiFi connections
- `src/network/ap_manager.py` - Handles Access Point mode operations

### Network Connection Strategy
The system uses a robust retry mechanism for network connections:
- Maximum 10 retry attempts
- 5-second delay for first 5 attempts
- 60-second delay for subsequent attempts
- Automatic fallback to AP mode if no networks available
- DNS configuration verification
- Internet connectivity check using multiple test hosts

### Network Retry Logic
```python
# Example retry pattern
retry_count = 0
max_retries = 10
delay = 5  # Initial delay in seconds

while retry_count < max_retries:
    if connection_successful:
        break
    delay = 60 if retry_count >= 5 else 5
    time.sleep(delay)
    retry_count += 1
```

### Hardware Interface
- `src/hardware/gpio_manager.py` - Manages GPIO pins and hardware interactions
- `src/hardware/button_controller.py` - Handles button input
- `src/hardware/rotary_encoder.py` - Manages volume control encoder

### Utilities
- `src/utils/config_manager.py` - Handles configuration file operations
- `src/utils/logger.py` - Centralized logging system
- `src/utils/stream_manager.py` - Manages radio stream sources
- `src/utils/config_migration.py` - Handles config file version updates

### Service Scripts
- `scripts/install.sh` - Installation and setup script
- `scripts/health_check.sh` - System health monitoring
- `scripts/test_sounds.py` - Audio system testing
- `runApp.sh` - Main service startup script

## Network Management

### Access Point (AP) Mode Triggers
AP mode is automatically started in the following scenarios:

1. **Initial Setup**
   - When no WiFi networks are configured
   - During first boot/installation
   - When configuration file is missing/corrupted

2. **Connection Failures**
   - After multiple failed attempts to connect to saved WiFi networks
   - When DNS resolution fails persistently
   - When internet connectivity check fails repeatedly

3. **Manual Triggers**
   - Through web interface request
   - Via GPIO button combination (long press)
   - Through API endpoint call

4. **Recovery Scenarios**
   - After power failure with network issues
   - When WiFi hardware issues are detected
   - When network configuration becomes invalid

### AP Mode Behavior
When AP mode is activated:
1. Creates "InternetRadio" WiFi network
2. Assigns static IP (192.168.4.1)
3. Starts DHCP server
4. Enables web interface for configuration
5. Plays audio notification
6. Indicates status via LED

### AP Mode Exit Conditions
AP mode is deactivated when:
1. Successfully connected to a configured WiFi network
2. Manual exit through web interface
3. System reboot after successful configuration
4. Timeout period reached with valid network configuration

### Network Mode State Machine
```
WiFi Mode ⟷ AP Mode
   ↑          ↑
   └──────────┘
  (Auto-switching)
```

## System Monitoring

### Live System Monitor
The system includes a real-time monitoring display that shows:
- CPU Usage
- Memory Usage
- Disk Usage
- Temperature
- Network Status
  - WiFi Network (Currently connected to)
  - Internet Connection (Yes/No)
- Radio Status
  - Service Status (Running/Stopped)
  - Current Station
  - Volume Level
- Last System Events

### Dependencies
The monitor requires:
- xterm (installed automatically by install.sh)
- Python system monitoring libraries (included in requirements.txt)

### Monitor Service Management
```bash
# Start the monitor
sudo systemctl start radiomonitor

# Stop the monitor
sudo systemctl stop radiomonitor

# Check monitor status
sudo systemctl status radiomonitor

# View monitor logs
journalctl -u radiomonitor -f
```

### Monitor Display
The monitor automatically launches in an xterm window and updates every second, showing:
- System metrics in real-time
- Network connectivity status with current WiFi SSID
- Internet connection status
- Radio service status and playback information
- Recent system events

Note: Only one instance can run at a time (singleton pattern implemented).

### Service Files
All service configurations are stored in the `services/` directory:
- `internetradio.service`: Main radio service configuration
- `radiomonitor.service`: System monitor service configuration
- `logrotate.conf`: Log rotation settings
- `network.conf`: Network interface configuration

## Development Workflow

### Branch Protection
The repository is configured with branch protection rules:
- Direct pushes to `main` and `develop` branches are prohibited
- Pull requests require passing tests before merging
- Branches must be up to date before merging

### Git Hooks
Local git hooks are installed to prevent commits with failing tests:
```bash
# The pre-commit hook runs all tests
# Commits are blocked if tests fail
git commit -m "your message"
```

### Continuous Integration
GitHub Actions run the test suite on:
- All pull requests to main/develop
- All pushes to main/develop

The CI pipeline:
1. Runs all unit tests
2. Checks test coverage (minimum 80% required)
3. Blocks merging if any checks fail

### Development Process
1. Create a feature branch from `develop`
2. Make changes and commit (tests run automatically)
3. Push branch and create pull request
4. Wait for CI checks to pass
5. Request review
6. Merge only after approval and passing tests

### Network Management Tools
The system exclusively uses `nmcli` (NetworkManager Command Line Interface) for all network operations:
- Network scanning: `nmcli device wifi list`
- Connection management: `nmcli connection add/up/down`
- WiFi operations: `nmcli radio wifi on/off`
- Network status: `nmcli device status`
- Saved networks: `nmcli connection show`

This standardization ensures consistent behavior and reliable network management across different Raspberry Pi models and OS versions.

## Development Notes

### Important Setup Considerations
1. **Config File Initialization**
   - Config files must be initialized before running tests
   - Default config location: `config/config.toml`
   - Test config uses temporary directory
   - Config migration handles version updates

2. **Test Dependencies**
   - Run tests in virtual environment
   - Mock hardware in tests (GPIO, audio)
   - Use `conftest.py` for shared fixtures
   - Respect test isolation

3. **Audio System Requirements**
   - Verify bcm2835 card number (default: card 2)
   - Check ALSA configuration before tests
   - Mock VLC in tests
   - Handle audio device permissions

4. **Network Testing**
   - Mock NetworkManager calls
   - Use test WiFi configurations
   - Handle DNS test timeouts
   - Mock AP mode operations

### Common Issues
1. **Permission Problems**
   - Run service as 'radio' user
   - Add user to required groups (audio, gpio)
   - Check log file permissions
   - Verify config directory ownership

2. **Audio Device Issues**
   - Verify card number in /etc/asound.conf
   - Check user audio group membership
   - Test with aplay before running service
   - Handle device busy errors

3. **Network Configuration**
   - NetworkManager must be installed and running
   - DNS configuration needs immutable flag
   - Handle multiple network interfaces
   - Check AP mode dependencies

## Function Documentation

### RadioApp Class
Main application class managing radio functionality and hardware controls.
- Initializes radio, button, and encoder controllers
- Handles hardware events (button press, rotation)
- Manages volume control and station switching
- Provides cleanup and monitoring capabilities

#### Methods:
- `initialize()`: Sets up all components and binds event handlers
- `handle_button_press()`: Switches to next radio station
- `handle_button_hold()`: Resets to first station
- `handle_rotation(direction)`: Controls volume based on encoder rotation
- `cleanup()`: Releases all hardware resources
- `run()`: Executes main application loop

### RadioController Class
Controls radio playback and hardware interaction.
- Manages audio playback
- Controls LED indicators
- Handles volume adjustments
- Monitors radio state

#### Methods:
- `initialize()`: Sets up audio and GPIO managers
- `start_playback(url)`: Begins streaming from URL
- `stop_playback()`: Stops current stream
- `volume_up/down()`: Adjusts volume level
- `set_led_state(blink)`: Controls LED indicator
- `monitor()`: Updates LED based on playback state

### Logger Class
Singleton logger managing application-wide logging.
- Handles log file rotation
- Filters ALSA-related messages
- Manages multiple log streams
- Provides debug/info/error logging

#### Methods:
- `setup_logging()`: Configures log files and formats
- `get_logger(name)`: Returns named logger instance
- `set_level(level)`: Updates logging verbosity
- `reset()`: Cleans up logging state

### Controllers

#### ButtonController Class
Manages hardware button interactions and event handling.
- Initializes GPIO button with debounce
- Handles press, hold, and release events
- Manages callback registration
- Provides cleanup for GPIO resources

##### Methods:
- `when_pressed(callback)`: Registers press event handler
- `when_held(callback)`: Registers long-press event handler
- `when_released(callback)`: Registers release event handler
- `cleanup()`: Releases GPIO resources

#### RotaryEncoderController Class
Manages rotary encoder for volume and menu navigation.
- Tracks encoder rotation steps
- Handles clockwise/counterclockwise events
- Provides debounced input handling
- Manages rotation callbacks

##### Methods:
- `when_rotated(callback)`: Registers rotation event handler
- `get_steps()`: Returns current step count
- `reset_steps()`: Resets step counter
- `cleanup()`: Releases encoder resources

#### WebController Class
Handles web interface and API endpoints.
- Manages HTTP routes and requests
- Handles network configuration
- Controls stream playback
- Provides system status

##### Methods:
- `index_route()`: Serves main web interface
- `network_status()`: Returns current network state
- `connect_wifi()`: Handles WiFi connection requests
- `stream_control()`: Manages radio stream playback
- `stop()`: Gracefully shuts down web server

### Network Components

#### WiFiManager Class
Manages WiFi connections and network modes.
- Handles network scanning and connections
- Manages saved networks
- Controls AP/Client mode switching
- Configures DNS and network settings

##### Methods:
- `scan_networks()`: Returns available WiFi networks
- `connect_to_network(ssid, password)`: Connects to specified network
- `enable_ap_mode()`: Activates Access Point mode
- `enable_client_mode()`: Switches to client mode
- `check_internet_connection()`: Verifies connectivity
- `configure_dns()`: Sets up DNS configuration
- `cleanup()`: Releases network resources

#### NetworkController Class
High-level network management and coordination.
- Coordinates WiFi and AP mode operations
- Handles network state transitions
- Manages connection retries
- Provides network status monitoring

##### Methods:
- `initialize()`: Sets up network components
- `check_and_setup_network()`: Ensures network connectivity
- `get_connection_status()`: Returns current network state
- `cleanup()`: Releases all network resources
- `monitor()`: Continuously monitors network health

#### APManager Class
Manages Access Point mode configuration and operation.
- Configures hostapd and dnsmasq
- Handles AP mode activation/deactivation
- Manages AP network settings
- Provides AP status monitoring

##### Methods:
- `initialize()`: Sets up AP dependencies
- `setup_ap_mode()`: Configures and starts AP
- `stop_ap_mode()`: Disables AP mode
- `is_ap_mode_active()`: Checks current AP state
- `configure_interface()`: Sets up network interface

### System Components

#### StreamManager Class
Manages radio stream sources and playback.
- Handles stream URL management
- Validates stream sources
- Manages stream metadata
- Provides stream switching logic

##### Methods:
- `load_streams()`: Loads stream configurations
- `add_stream(url, name)`: Adds new stream source
- `remove_stream(url)`: Removes stream from list
- `get_next_stream()`: Returns next stream in rotation
- `validate_stream(url)`: Checks stream validity

#### ConfigManager Class
Manages application configuration and settings.
- Handles config file operations
- Manages network settings
- Controls audio configuration
- Provides config validation

##### Methods:
- `load_config()`: Loads configuration from file
- `save_config()`: Persists current configuration
- `update_network_config()`: Updates network settings
- `update_audio_config()`: Updates audio settings
- `get_saved_networks()`: Returns saved network list

## Logging System

### Log Configuration

1. **Application Logs**
   - Location: `/home/radio/internetRadio/logs/`
   - Main log files:
     - `radio.log`: Main application log
     - `wifi.log`: Network-related logs
     - `app.log`: General application events
   - Size limits:
     - Individual files: 1MB max
     - Backup count: 2 files per log
     - Total per logger: 3MB max (1 current + 2 backups)

2. **System Journal**
   - Size limit: 100MB
   - Retention: 7 days
   - Location: `/var/log/journal/`

3. **Log Management**
   ```bash
   # Clean application logs
   sudo rm -f /home/radio/internetRadio/logs/*.gz

   # Clean journal
   sudo journalctl --vacuum-time=7d
   sudo journalctl --vacuum-size=100M

   # Monitor logs
   tail -f /home/radio/internetRadio/logs/radio.log
   journalctl -u internetradio -f
   ```

4. **Development Guidelines**
   - Use appropriate log levels (ERROR, WARNING, INFO, DEBUG)
   - Messages truncated to 200 characters
   - Console output only in development mode
   - Automatic rotation when size limits reached
   - Regular cleanup of old logs

## Testing Lessons Learned

### Common Testing Pitfalls

1. **Patch Order Matters**
   - Patches are applied from bottom to top
   - Method parameters must match patch order in reverse
   ```python
   @patch('subprocess.run')
   @patch('src.network.wifi_manager.ConfigManager')
   def test_method(self, mock_config, mock_run):  # Order matches patches in reverse
   ```

2. **Class-Level Patches**
   - Be aware of patches applied in setUp/class level
   - Account for all patches in test method signatures
   - Document class-level patches in test class docstring

3. **Mock Side Effects**
   - Use side_effect for multiple return values
   - Match mock returns with expected command sequence
   ```python
   mock_run.side_effect = [
       MagicMock(returncode=0, stdout="success output"),
       MagicMock(returncode=0)  # Next call
   ]
   ```

4. **Command Verification**
   - Use assert_has_calls to verify command sequence
   - Match exact command format including all parameters
   - Include capture_output and text parameters
   ```python
   mock_run.assert_has_calls([
       call(['command', 'arg1'], capture_output=True, text=True),
       call(['command', 'arg2'], capture_output=True, text=True)
   ])
   ```

5. **Output Format Parsing**
   - Match exact output format from real commands
   - Consider all possible output variations
   - Handle empty or malformed output gracefully
   ```python
   # Example nmcli output format
   "NetworkName:uuid:wifi:wlan0\n"
   ```

### Best Practices

1. **Test Setup**
   - Document all patches in test method docstring
   - Clear mock call history between tests
   - Reset singleton instances if used

2. **Error Handling**
   - Test both success and failure scenarios
   - Verify error logging
   - Check return values for all paths

3. **Resource Cleanup**
   - Use tearDown for consistent cleanup
   - Close file handlers
   - Reset mocks and patches

4. **Command Testing**
   - Use exact command formats from documentation
   - Include all required parameters
   - Match real-world output formats

5. **Documentation**
   - Document expected mock formats
   - Include example command outputs
   - Note any special setup requirements

### Network Management Updates

#### NetworkController Improvements
- Enhanced error handling for NetworkManager operations
- Added retry mechanism for network operations
- Improved AP mode state management
- Added test environment detection
- Implemented proper cleanup procedures

#### Testing Framework Updates
1. **Test Environment Detection**
```python
# Environment-aware network operations
if not os.environ.get('TESTING'):
    # Production code
else:
    # Test code
```

2. **Dependency Injection**
```python
class NetworkController:
    def __init__(self, config_manager=None, wifi_manager=None, ap_manager=None):
        self.config_manager = config_manager
        self.wifi_manager = wifi_manager
        self.ap_manager = ap_manager
```

3. **Mock Setup Best Practices**
```python
def setUp(self):
    # Create and configure mocks
    self.mock_wifi = MagicMock()
    self.mock_ap = MagicMock()
    self.mock_config = MagicMock()
    
    # Initialize controller with mocks
    self.network_controller = NetworkController(
        config_manager=self.mock_config,
        wifi_manager=self.mock_wifi,
        ap_manager=self.mock_ap
    )
```

#### Network Controller Features
- AP mode status monitoring
- WiFi connection management
- Network state transitions
- Service management (NetworkManager)
- Error recovery and logging
- Resource cleanup

#### Testing Improvements
- Enhanced mock configurations
- Better test isolation
- Proper resource cleanup
- Service management handling
- Environment-aware testing
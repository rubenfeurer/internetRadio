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

## Testing Best Practices

### Lessons Learned
- **Mock Side Effects**: When testing retry mechanisms, use `side_effect` instead of `return_value` for mocks that need to return different values on subsequent calls:
```python
mock_check.side_effect = [False, False, True]  # Returns False twice, then True
```

- **Control Flow in Retry Logic**: 
  - Avoid early returns in retry loops
  - Use explicit retry counters
  - Place retry logic at the end of the loop
  - Ensure all conditions trigger the retry mechanism

- **Test Debugging**:
  - Add debug prints in tests to show actual calls:
```python
print(f"Actual sleep calls: {mock_sleep.mock_calls}")
print(f"Actual check calls: {mock_check.mock_calls}")
```

- **Mock Verification**:
  - Check both call count and call arguments
  - Use `assert_has_calls` for verifying multiple calls in order
  - Consider using `any_order=True` when order doesn't matter

### Common Pitfalls
1. **Incorrect Mock Setup**:
   - Not patching the correct path
   - Forgetting to mock dependencies
   - Using return_value instead of side_effect for multiple returns

2. **Retry Logic Issues**:
   - Returning too early from loops
   - Not incrementing retry counters
   - Missing delay between retries
   - Not handling all failure cases

3. **Test Isolation**:
   - Not cleaning up resources
   - Leaking state between tests
   - Missing tearDown cleanup

### Test Structure Guidelines
1. **Setup Phase**:
```python
def setUp(self):
    # Mock all dependencies first
    self.patches = [
        patch('path.to.dependency'),
    ]
    self.mocks = [patcher.start() for patcher in self.patches]
    
    # Configure mock behaviors
    self.mock_wifi.get_saved_networks.return_value = ["Network1"]
```

2. **Test Cases**:
```python
def test_with_retries(self):
    # Arrange
    mock_check.side_effect = [False, False, True]
    
    # Act
    with patch('time.sleep') as mock_sleep:
        result = self.component.method()
        
    # Assert
    self.assertTrue(result)
    self.assertEqual(mock_check.call_count, expected_count)
```

3. **Cleanup**:
```python
def tearDown(self):
    # Stop all patches
    for patcher in self.patches:
        patcher.stop()
```

### Test Development Process
1. Write test first (TDD)
2. Run test to see it fail
3. Implement minimal code to pass
4. Refactor while keeping tests green
5. Add debug logging if needed
6. Verify edge cases
7. Clean up and document

### Integration Test Considerations
- Mock external services
- Use test configurations
- Reset state between tests
- Handle timeouts
- Log all important steps

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
  - WiFi Network
  - Internet Connection
- Radio Status
  - Service Status
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
The monitor automatically launches in an xterm window and updates every second. The display shows:
- System metrics in real-time
- Network connectivity status
- Radio playback information
- Recent system events

Note: Only one instance can run at a time (singleton pattern implemented).
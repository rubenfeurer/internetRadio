#!/bin/bash

LOG_FILE="/home/radio/internetRadio/scripts/logs/installation.log"
SUCCESS=true

# Function to log messages
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

# Function to log errors
log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] ERROR: $1" | tee -a "$LOG_FILE"
    SUCCESS=false
}

# Clear log
mkdir -p "$(dirname "$LOG_FILE")"
echo "=== Installation Started $(date '+%Y-%m-%d %H:%M:%S') ===" > "$LOG_FILE"

log_message "Starting installation..."

# Update system
log_message "Updating system packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev vlc pigpio

# Setup directories
log_message "Setting up directories..."
RADIO_DIR="/home/radio/internetRadio"
mkdir -p "$RADIO_DIR"
cd "$RADIO_DIR" || log_error "Failed to change to $RADIO_DIR"

# Setup virtual environment
log_message "Setting up virtual environment..."
python3 -m venv .venv || log_error "Failed to create virtual environment"
source .venv/bin/activate || log_error "Failed to activate virtual environment"

# Add missing install_package function
install_package() {
    local package=$1
    log_message "Installing $package..."
    if ! pip install "$package"; then
        log_error "Failed to install $package"
        return 1
    fi
    return 0
}

# Improve PulseAudio setup
setup_audio() {
    log_message "Setting up audio system..."
    
    # Stop all pulseaudio instances
    systemctl --user stop pulseaudio.socket pulseaudio.service || true
    killall -9 pulseaudio || true
    
    # Clean up
    rm -rf /home/radio/.config/pulse/*
    rm -rf /run/user/1000/pulse/*
    
    # Wait for cleanup
    sleep 2
    
    # Start fresh
    systemctl --user start pulseaudio.socket pulseaudio.service
    
    # Wait for startup
    sleep 2
}

# Improve Python package installation
install_python_packages() {
    log_message "Installing Python packages..."
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Update pip
    python3 -m pip install --upgrade pip
    
    # Install packages
    PACKAGES=(
        "flask==2.0.1"
        "flask-cors==3.0.10"
        "gpiozero==2.0"
        "python-vlc==3.0.18"
        "pigpio==1.78"
        "toml==0.10.2"
    )
    
    for package in "${PACKAGES[@]}"; do
        install_package "$package"
    done
    
    deactivate
}

# Install required packages
packages=(
    "gpiozero"
    "python-vlc"
    "pigpio"
    "toml"
    "flask"
    "flask-cors"
)

# Clear pip cache
pip cache purge

for package in "${packages[@]}"; do
    install_package "$package"
done

# Verify installations with detailed error reporting
log_message "Verifying package installations..."
for package in "${packages[@]}"; do
    if ! pip list | grep -q "^$package "; then
        log_error "Package $package is not installed"
        log_message "Attempting to fix $package installation..."
        
        # Try alternative installation methods
        if [[ $package == "flask" ]]; then
            pip install Flask --no-cache-dir || log_error "Alternative Flask installation failed"
        elif [[ $package == "flask-cors" ]]; then
            pip install Flask-Cors --no-cache-dir || log_error "Alternative Flask-Cors installation failed"
        fi
    else
        log_message "Verified installation of $package"
    fi
done

# Verify Flask specifically
if ! python3 -c "import flask" 2>/dev/null; then
    log_error "Flask import failed, attempting system-wide installation"
    sudo apt-get install -y python3-flask || log_error "System Flask installation failed"
fi

# Verify Flask-CORS specifically
if ! python3 -c "import flask_cors" 2>/dev/null; then
    log_error "Flask-CORS import failed, attempting system-wide installation"
    sudo apt-get install -y python3-flask-cors || log_error "System Flask-CORS installation failed"
fi

# Start and verify the service
log_message "Starting internetradio service..."
sudo systemctl start internetradio || log_error "Failed to start internetradio service"

# Wait for service to start
sleep 5

# Check service status
if ! systemctl is-active --quiet internetradio; then
    log_error "internetradio service is not running"
    log_message "Checking service logs..."
    journalctl -u internetradio -n 50 >> "$LOG_FILE"
fi

# Final status and log viewing

# Add script verification and fixes section
log_message "Verifying and fixing script permissions..."

# Install dos2unix if needed
if ! command -v dos2unix &> /dev/null; then
    log_message "Installing dos2unix..."
    sudo apt-get install -y dos2unix || log_error "Failed to install dos2unix"
fi

# Fix script files
SCRIPT_FILES=(
    "scripts/runApp.sh"
    "scripts/update_radio.sh"
    "scripts/check_radio.sh"
    "scripts/uninstall_radio.sh"
)

for script in "${SCRIPT_FILES[@]}"; do
    if [ -f "$script" ]; then
        log_message "Fixing $script..."
        
        # Convert line endings
        sudo dos2unix "$script" || log_error "Failed to convert line endings for $script"
        
        # Ensure correct shebang
        if ! head -n1 "$script" | grep -q "^#!/bin/bash"; then
            sudo sed -i '1i#!/bin/bash' "$script"
            log_message "Added shebang to $script"
        fi
        
        # Set permissions
        sudo chmod +x "$script" || log_error "Failed to make $script executable"
        sudo chown radio:radio "$script" || log_error "Failed to set ownership for $script"
        
        log_message "Verified $script"
    else
        log_error "Script file not found: $script"
    fi
done

# Verify runApp.sh specifically (as it's critical)
if [ -f "scripts/runApp.sh" ]; then
    log_message "Verifying runApp.sh..."
    
    # Check permissions
    if [ ! -x "scripts/runApp.sh" ]; then
        log_message "Fixing runApp.sh permissions..."
        sudo chmod +x "scripts/runApp.sh" || log_error "Failed to make runApp.sh executable"
    fi
    
    # Check ownership
    if [ "$(stat -c '%U:%G' scripts/runApp.sh)" != "radio:radio" ]; then
        log_message "Fixing runApp.sh ownership..."
        sudo chown radio:radio "scripts/runApp.sh" || log_error "Failed to set runApp.sh ownership"
    fi
    
    # Verify content
    if ! grep -q "^#!/bin/bash" "scripts/runApp.sh"; then
        log_error "runApp.sh is missing shebang line"
    fi
else
    log_error "Critical error: runApp.sh not found"
    exit 1
fi

# Create the radio service with verified paths
sudo bash -c "cat > /etc/systemd/system/internetradio.service" <<EOL
[Unit]
Description=Internet Radio Service
After=network.target pigpiod.service pulseaudio.service
Requires=pigpiod.service

[Service]
Type=simple
User=radio
Group=radio
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/radio/.Xauthority
Environment=HOME=/home/radio
Environment=XDG_RUNTIME_DIR=/run/user/1000
WorkingDirectory=/home/radio/internetRadio

# Setup audio and required services
ExecStartPre=/bin/bash -c 'mkdir -p /run/user/1000 && chmod 700 /run/user/1000'
ExecStartPre=/usr/bin/pulseaudio --start
ExecStartPre=/bin/sleep 5

# Start the main application with explicit bash
ExecStart=/bin/bash /home/radio/internetRadio/scripts/runApp.sh

# Restart settings
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Set permissions
log_message "Setting permissions..."
sudo usermod -a -G gpio,dialout,video,audio radio

# Delay before chmod commands
log_message "Waiting for 3 seconds before setting permissions..."
sleep 3

sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem
sudo chown -R radio:radio "$RADIO_DIR"
sudo chmod -R 755 "$RADIO_DIR"

# Verify installations
log_message "Verifying installations..."

# Verify virtual environment
if [ ! -f ".venv/bin/activate" ]; then
    log_error "Virtual environment not properly created"
fi

# Verify Python packages
source .venv/bin/activate
for package in flask flask-cors gpiozero python-vlc pigpio toml; do
    if ! pip list | grep -q "^$package "; then
        log_error "Package $package is not installed"
        pip install --no-cache-dir "$package"
    fi
done

# Verify pigpiod
if ! systemctl is-active --quiet pigpiod; then
    log_error "pigpiod is not running, attempting to start..."
    sudo systemctl start pigpiod
    sleep 2
    if ! systemctl is-active --quiet pigpiod; then
        sudo /usr/bin/pigpiod
    fi
fi

# Final verification
log_message "Running final verification..."
source .venv/bin/activate
python3 -c "import flask; import flask_cors" 2>/dev/null || log_error "Flask verification failed"
if ! pgrep pigpiod > /dev/null; then
    log_error "pigpiod verification failed"
fi

# Setup autostart
log_message "Setting up autostart service..."

# Create systemd service file
sudo bash -c "cat > /etc/systemd/system/internetradio.service" <<EOL
[Unit]
Description=Internet Radio Service
After=network.target pigpiod.service pulseaudio.service
Requires=pigpiod.service

[Service]
Type=simple
User=radio
Group=radio
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/radio/.Xauthority
Environment=HOME=/home/radio
Environment=XDG_RUNTIME_DIR=/run/user/1000
WorkingDirectory=/home/radio/internetRadio

# Setup audio and required services
ExecStartPre=/bin/bash -c 'mkdir -p /run/user/1000 && chmod 700 /run/user/1000'
ExecStartPre=/usr/bin/pulseaudio --start
ExecStartPre=/bin/sleep 5

# Start the main application
ExecStart=/home/radio/internetRadio/scripts/runApp.sh

# Restart settings
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Set up permissions and groups
log_message "Setting up permissions and groups..."

# Add radio user to required groups
sudo usermod -a -G audio,video,gpio,pulse,pulse-access radio

# Set up runtime directory
sudo mkdir -p /run/user/1000
sudo chown radio:radio /run/user/1000
sudo chmod 700 /run/user/1000

# Set application permissions
sudo chown -R radio:radio /home/radio/internetRadio
sudo chmod -R 755 /home/radio/internetRadio

# Enable and start services
log_message "Enabling and starting services..."

# Enable and start pigpiod
sudo systemctl enable pigpiod
if ! sudo systemctl start pigpiod; then
    log_error "Failed to start pigpiod service"
fi

# Enable and start radio service
sudo systemctl daemon-reload
if ! sudo systemctl enable internetradio.service; then
    log_error "Failed to enable internetradio service"
fi
if ! sudo systemctl start internetradio.service; then
    log_error "Failed to start internetradio service"
fi

# Verify service status
if ! systemctl is-active --quiet internetradio.service; then
    log_error "internetradio service is not running"
else
    log_message "internetradio service is running successfully"
fi

# Add service status check
log_message "Checking service status..."
SERVICE_STATUS=$(systemctl status internetradio.service)
log_message "Service status: $SERVICE_STATUS"

# Add daily update service
log_message "Setting up daily update service..."

# Create the update service
sudo bash -c "cat > /etc/systemd/system/radio-update.service" <<EOL
[Unit]
Description=Daily Radio Update Service
After=network.target

[Service]
Type=oneshot
User=radio
Group=radio
WorkingDirectory=/home/radio/internetRadio
Environment=HOME=/home/radio
ExecStart=/home/radio/internetRadio/scripts/update_radio.sh
StandardOutput=append:/home/radio/internetRadio/scripts/logs/update_radio.log
StandardError=append:/home/radio/internetRadio/scripts/logs/update_radio.log

[Install]
WantedBy=multi-user.target
EOL

# Make the update script executable
sudo chmod +x /home/radio/internetRadio/scripts/update_radio.sh

# Set proper ownership
sudo chown radio:radio /home/radio/internetRadio/scripts/update_radio.sh

# Reload systemd
sudo systemctl daemon-reload

# Enable the service
sudo systemctl enable radio-update.service

# Create the timer
sudo bash -c "cat > /etc/systemd/system/radio-update.timer" <<EOL
[Unit]
Description=Daily Radio Update Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=24h
Persistent=true

[Install]
WantedBy=timers.target
EOL

# Enable and start the timer
log_message "Enabling and starting update timer..."
sudo systemctl daemon-reload
if ! sudo systemctl enable radio-update.timer; then
    log_error "Failed to enable update timer"
fi
if ! sudo systemctl start radio-update.timer; then
    log_error "Failed to start update timer"
fi

# Verify timer status
if ! systemctl is-active --quiet radio-update.timer; then
    log_error "Update timer is not running"
else
    log_message "Update timer is running successfully"
fi

# Add timer status check
TIMER_STATUS=$(systemctl status radio-update.timer)
log_message "Timer status: $TIMER_STATUS"

# Final status
    log_message "Installation completed with errors"
    echo
    echo "Would you like to view the installation log? (y/N): "
    read -r view_log
    if [[ $view_log =~ ^[Yy]$ ]]; then
        if command -v less >/dev/null 2>&1; then
            less "$LOG_FILE"
        else
            cat "$LOG_FILE"
        fi
        echo
        echo "The full log is available at: $LOG_FILE"
    else
        echo "You can view the log later with: cat $LOG_FILE"
    fi
    
    echo
    echo "Would you like to run the diagnostic script to check for issues? (y/N): "
    read -r run_diagnostic
    if [[ $run_diagnostic =~ ^[Yy]$ ]]; then
        ./scripts/check_radio.sh
    fi
fi

echo "=== Installation Finished $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE" 

# Install audio and GPIO dependencies
log_message "Installing audio and GPIO dependencies..."
sudo apt-get install -y alsa-utils python3-pigpio python3-rpi.gpio

# Install additional Python packages
source .venv/bin/activate
pip install RPi.GPIO lgpio

# Enable and start pigpiod
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Set up audio
log_message "Setting up audio..."
# Get available audio controls
AUDIO_CONTROLS=$(amixer scontrols)
log_message "Available audio controls: $AUDIO_CONTROLS"

# Function to check GPIO connections
check_hardware() {
    log_message "Checking hardware connections..."
    
    # GPIO Pin definitions
    declare -A PINS=(
        ["ROTARY_CLK"]=11    # GPIO11
        ["ROTARY_DT"]=9      # GPIO9
        ["ROTARY_SW"]=10     # GPIO10
        ["BUTTON_1"]=17      # GPIO17
        ["BUTTON_2"]=27      # GPIO27
        ["BUTTON_3"]=22      # GPIO22
        ["LED"]=4            # GPIO4
    )
    
    # Array to store results
    declare -A RESULTS=()
    
    # Test each pin
    for pin in "${!PINS[@]}"; do
        if python3 - <<END
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pin = ${PINS[$pin]}

# Setup pin
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Read initial state
state = GPIO.input(pin)

# For LED, try to output
if pin == 4:  # LED pin
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(pin, GPIO.LOW)

GPIO.cleanup()
END
        then
            RESULTS[$pin]="✓"
        else
            RESULTS[$pin]="✗"
        fi
    done
    
    # Print results in a nice format
    echo
    echo "Hardware Connection Check Results:"
    echo "================================="
    echo "Rotary Encoder:"
    echo "  CLK (GPIO11): ${RESULTS[ROTARY_CLK]}"
    echo "  DT  (GPIO9):  ${RESULTS[ROTARY_DT]}"
    echo "  SW  (GPIO10): ${RESULTS[ROTARY_SW]}"
    echo
    echo "Buttons:"
    echo "  Button 1 (GPIO17): ${RESULTS[BUTTON_1]}"
    echo "  Button 2 (GPIO27): ${RESULTS[BUTTON_2y
    ]}"
    echo "  Button 3 (GPIO22): ${RESULTS[BUTTON_3]}"
    echo
    echo "LED:"
    echo "  LED with 220Ω resistor (GPIO4): ${RESULTS[LED]}"
    echo
    echo "Note: ✓ = Pin accessible, ✗ = Pin not accessible or in use"
    echo "This is just a basic connectivity test and doesn't guarantee correct wiring."
    echo "Refer to the wiring diagram for correct connections:"
    echo
    echo "Wiring Instructions:"
    echo "-------------------"
    echo "Rotary Encoder:"
    echo "  - GND → Pin 6 (Ground)"
    echo "  - VCC → Pin 1 (3.3V)"
    echo "  - SW  → Pin 19 (GPIO10)"
    echo "  - DT  → Pin 21 (GPIO9)"
    echo "  - CLK → Pin 23 (GPIO11)"
    echo
    echo "Buttons:"
    echo "  - Button 1 → GPIO17 (Pin 11)"
    echo "  - Button 2 → GPIO27 (Pin 13)"
    echo "  - Button 3 → GPIO22 (Pin 15)"
    echo "  - All buttons also connect to Ground"
    echo
    echo "LED:"
    echo "  - LED positive → 220Ω resistor → GPIO4 (Pin 7)"
    echo "  - LED negative → Ground"
    echo
}

# At the end of successful installation
if [ "$SUCCESS" = true ]; then
    log_message "Installation completed successfully"
    log_message "The radio will start automatically on next boot"
    log_message "To check status: sudo systemctl status internetradio"
    log_message "To view logs: journalctl -u internetradio -f"
    
    echo
    echo "Would you like to check the hardware connections? (y/N): "
    read -r check_hw
    if [[ $check_hw =~ ^[Yy]$ ]]; then
        check_hardware
    else
        echo
        echo "You can check hardware connections later by running:"
        echo "sudo ./scripts/check_radio.sh"
    fi
    
    echo
    echo "Installation Summary:"
    echo "-------------------"
    echo "✓ Software installation complete"
    echo "✓ Services configured"
    echo "✓ Permissions set"
    echo "✓ Auto-update configured"
    echo
    echo "Next Steps:"
    echo "1. Verify hardware connections if not done"
    echo "2. Reboot the system"
    echo "3. The radio will start automatically"
    echo
    read -p "Would you like to reboot now? (y/N): " reboot
    if [[ $reboot == [yY] ]]; then
        sudo reboot
    fi
else
    log_message "Installation completed with errors"
fi

# Improve audio setup
setup_audio() {
    log_message "Setting up audio..."
    
    # Stop any running pulseaudio
    pulseaudio --kill || true
    sleep 2
    
    # Clean up old files
    rm -rf /home/radio/.config/pulse
    rm -rf /run/user/1000/pulse
    
    # Create fresh pulse config
    mkdir -p /home/radio/.config/pulse
    
    # Configure pulseaudio
    cat > /home/radio/.config/pulse/client.conf <<EOF
autospawn = no
daemon-binary = /usr/bin/pulseaudio
EOF

    # Set permissions
    chown -R radio:radio /home/radio/.config/pulse
    
    # Update service file to handle audio better
    sudo sed -i 's/ExecStartPre=\/usr\/bin\/pulseaudio --start/ExecStartPre=\/usr\/bin\/pulseaudio --start --exit-idle-time=-1/' /etc/systemd/system/internetradio.service
}

# Improve GPIO setup
setup_gpio() {
    log_message "Setting up GPIO..."
    
    # Stop existing pigpiod
    sudo systemctl stop pigpiod || true
    
    # Clean up any existing files
    sudo rm -f /var/run/pigpio.pid
    
    # Install GPIO packages
    sudo apt-get install -y python3-pigpio python3-rpi.gpio
    
    # Configure pigpiod service
    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod
    
    # Wait for service
    sleep 2
    
    # Verify GPIO
    if ! pigs help >/dev/null 2>&1; then
        log_error "pigpiod verification failed"
        # Try to fix
        sudo killall pigpiod
        sleep 1
        sudo pigpiod
    fi
}

# Main installation flow
main() {
    # ... existing initial setup ...

    setup_audio
    setup_gpio
    install_python_packages

    # Verify all components
    verify_installation() {
        local success=true
        
        # Check Flask
        python3 -c "import flask" || success=false
        
        # Check Audio
        pulseaudio --check || success=false
        
        # Check GPIO
        pigs help >/dev/null 2>&1 || success=false
        
        if [ "$success" = true ]; then
            log_message "All components verified successfully"
        else
            log_error "Some components failed verification"
        fi
        
        return $success
    }

    # Final service restart
    if verify_installation; then
        sudo systemctl restart internetradio
        sleep 5
        if ! systemctl is-active --quiet internetradio; then
            log_error "Service failed to start after verification"
        fi
    fi
}

# Run main installation
main

# Improve package verification
verify_package() {
    local package=$1
    local module_name=$2  # Sometimes different from package name
    
    log_message "Verifying $package..."
    if source .venv/bin/activate && python3 -c "import $module_name" 2>/dev/null; then
        log_message "Verified installation of $package"
        deactivate
        return 0
    else
        log_message "ERROR: Package $package verification failed"
        deactivate
        return 1
    fi
}

verify_installations() {
    log_message "Verifying installations..."
    
    # Map of package names to their import names
    declare -A PACKAGES=(
        ["gpiozero"]="gpiozero"
        ["python-vlc"]="vlc"
        ["pigpio"]="pigpio"
        ["toml"]="toml"
        ["flask"]="flask"
        ["flask-cors"]="flask_cors"
    )
    
    local failed=0
    for package in "${!PACKAGES[@]}"; do
        if ! verify_package "$package" "${PACKAGES[$package]}"; then
            failed=1
        fi
    done
    
    return $failed
}

# Fix broken pipe handling
exec_with_retry() {
    local cmd="$1"
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$cmd" 2>&1 | tee /dev/null; then
            return 0
        fi
        log_message "Attempt $attempt failed, retrying..."
        ((attempt++))
        sleep 1
    done
    
    log_message "Failed after $max_attempts attempts"
    return 1
}
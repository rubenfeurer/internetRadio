#!/bin/bash

LOG_FILE="/home/radio/internetRadio/scripts/logs/installation.log"

# Simple logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" 2>/dev/null || true
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
cd "$RADIO_DIR" || log_message "Failed to change to $RADIO_DIR"

# Setup virtual environment
log_message "Setting up virtual environment..."
python3 -m venv .venv || log_message "Failed to create virtual environment"
source .venv/bin/activate || log_message "Failed to activate virtual environment"

# Add missing install_package function
install_package() {
    local package=$1
    log_message "Installing $package..."
    if ! pip install "$package"; then
        log_message "Failed to install $package"
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
        log_message "Package $package is not installed"
        log_message "Attempting to fix $package installation..."
        
        # Try alternative installation methods
        if [[ $package == "flask" ]]; then
            pip install Flask --no-cache-dir || log_message "Alternative Flask installation failed"
        elif [[ $package == "flask-cors" ]]; then
            pip install Flask-Cors --no-cache-dir || log_message "Alternative Flask-Cors installation failed"
        fi
    else
        log_message "Verified installation of $package"
    fi
done

# Verify Flask specifically
if ! python3 -c "import flask" 2>/dev/null; then
    log_message "Flask import failed, attempting system-wide installation"
    sudo apt-get install -y python3-flask || log_message "System Flask installation failed"
fi

# Verify Flask-CORS specifically
if ! python3 -c "import flask_cors" 2>/dev/null; then
    log_message "Flask-CORS import failed, attempting system-wide installation"
    sudo apt-get install -y python3-flask-cors || log_message "System Flask-CORS installation failed"
fi

# Start and verify the service
log_message "Starting internetradio service..."
sudo systemctl start internetradio || log_message "Failed to start internetradio service"

# Wait for service to start
sleep 5

# Check service status
if ! systemctl is-active --quiet internetradio; then
    log_message "internetradio service is not running"
    log_message "Checking service logs..."
    journalctl -u internetradio -n 50 >> "$LOG_FILE"
fi

# Final status and log viewing

# Add script verification and fixes section
log_message "Verifying and fixing script permissions..."

# Install dos2unix if needed
if ! command -v dos2unix &> /dev/null; then
    log_message "Installing dos2unix..."
    sudo apt-get install -y dos2unix || log_message "Failed to install dos2unix"
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
        sudo dos2unix "$script" || log_message "Failed to convert line endings for $script"
        
        # Ensure correct shebang
        if ! head -n1 "$script" | grep -q "^#!/bin/bash"; then
            sudo sed -i '1i#!/bin/bash' "$script"
            log_message "Added shebang to $script"
        fi
        
        # Set permissions
        sudo chmod +x "$script" || log_message "Failed to make $script executable"
        sudo chown radio:radio "$script" || log_message "Failed to set ownership for $script"
        
        # Remove Windows line endings without needing dos2unix
        sed -i 's/\r$//' "$script"
        
        log_message "Verified $script"
    else
        log_message "Script file not found: $script"
    fi
done

# Verify runApp.sh specifically (as it's critical)
if [ -f "scripts/runApp.sh" ]; then
    log_message "Verifying runApp.sh..."
    
    # Check permissions
    if [ ! -x "scripts/runApp.sh" ]; then
        log_message "Fixing runApp.sh permissions..."
        sudo chmod +x "scripts/runApp.sh" || log_message "Failed to make runApp.sh executable"
    fi
    
    # Check ownership
    if [ "$(stat -c '%U:%G' scripts/runApp.sh)" != "radio:radio" ]; then
        log_message "Fixing runApp.sh ownership..."
        sudo chown radio:radio "scripts/runApp.sh" || log_message "Failed to set runApp.sh ownership"
    fi
    
    # Verify content
    if ! grep -q "^#!/bin/bash" "scripts/runApp.sh"; then
        log_message "runApp.sh is missing shebang line"
    fi
else
    log_message "Critical error: runApp.sh not found"
    exit 1
fi

# Create the radio service with verified paths
sudo bash -c "cat > /etc/systemd/system/internetradio.service" <<EOL
[Unit]
Description=Internet Radio Service
After=network.target pigpiod.service
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

# Setup runtime directory
ExecStartPre=/bin/bash -c 'mkdir -p /run/user/1000 && chmod 700 /run/user/1000'
ExecStartPre=/bin/sleep 2

# Start the main application
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
    log_message "Virtual environment not properly created"
fi

# Verify Python packages
source .venv/bin/activate
for package in flask flask-cors gpiozero python-vlc pigpio toml; do
    if ! pip list | grep -q "^$package "; then
        log_message "Package $package is not installed"
        pip install --no-cache-dir "$package"
    fi
done

# Verify pigpiod
if ! systemctl is-active --quiet pigpiod; then
    log_message "pigpiod is not running, attempting to start..."
    sudo systemctl start pigpiod
    sleep 2
    if ! systemctl is-active --quiet pigpiod; then
        sudo /usr/bin/pigpiod
    fi
fi

# Final verification
log_message "Running final verification..."
source .venv/bin/activate
python3 -c "import flask; import flask_cors" 2>/dev/null || log_message "Flask verification failed"
if ! pgrep pigpiod > /dev/null; then
    log_message "pigpiod verification failed"
fi

# Setup autostart
log_message "Setting up autostart service..."

# Create systemd service file
sudo bash -c "cat > /etc/systemd/system/internetradio.service" <<EOL
[Unit]
Description=Internet Radio Service
After=network.target pigpiod.service
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

# Setup runtime directory
ExecStartPre=/bin/bash -c 'mkdir -p /run/user/1000 && chmod 700 /run/user/1000'
ExecStartPre=/bin/sleep 2

# Start the main application
ExecStart=/bin/bash /home/radio/internetRadio/scripts/runApp.sh

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
    log_message "Failed to start pigpiod service"
fi

# Enable and start radio service
sudo systemctl daemon-reload
if ! sudo systemctl enable internetradio.service; then
    log_message "Failed to enable internetradio service"
fi
if ! sudo systemctl start internetradio.service; then
    log_message "Failed to start internetradio service"
fi

# Verify service status
if ! systemctl is-active --quiet internetradio.service; then
    log_message "internetradio service is not running"
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
    log_message "Failed to enable update timer"
fi
if ! sudo systemctl start radio-update.timer; then
    log_message "Failed to start update timer"
fi

# Verify timer status
if ! systemctl is-active --quiet radio-update.timer; then
    log_message "Update timer is not running"
else
    log_message "Update timer is running successfully"
fi

# Add timer status check
TIMER_STATUS=$(systemctl status radio-update.timer)
log_message "Timer status: $TIMER_STATUS"

# Final status check - only care about service running
check_installation_status() {
    if systemctl is-active --quiet internetradio && \
       systemctl is-active --quiet radio-update.timer; then
        log_message "Installation completed successfully"
        log_message "Service is running at http://$(hostname -I | cut -d' ' -f1):8080"
        log_message "Service status: $(systemctl status internetradio | head -n3)"
        log_message "Timer status: $(systemctl status radio-update.timer | head -n3)"
        return 0
    else
        log_message "Installation completed with errors - service not running"
        return 1
    fi
}

# Main installation function
main() {
    log_message "Starting installation..."
    
    # Check if service is already running
    if systemctl is-active --quiet internetradio; then
        log_message "Service already running - installation successful"
        return 0
    fi
    
    # Only continue with installation if service isn't running
    install_packages
    
    # Final status check
    check_installation_status
}

# Run main installation
main

# Add this function to install_radio.sh, after the other service setups

setup_monitor_service() {
    log_message "Setting up monitor service..."
    
    # Create monitor service
    cat > /etc/systemd/system/radio-monitor.service <<EOL
[Unit]
Description=Internet Radio Monitor
After=internetradio.service
BindsTo=internetradio.service

[Service]
Type=simple
User=radio
Group=radio
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/radio/.Xauthority

ExecStart=/usr/bin/xterm -T "Internet Radio Monitor" -geometry 100x30 -e "/home/radio/internetRadio/scripts/monitor_radio.sh"
ExecStop=/usr/bin/pkill -f "monitor_radio.sh"

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

    # Enable and start monitor service
    systemctl daemon-reload
    systemctl enable radio-monitor.service
    systemctl start radio-monitor.service
}

# Add this line in the main installation section, after internetradio.service setup
setup_monitor_service

# Add before service setup
log_message "Setting up required directories..."
mkdir -p /run/user/1000
chmod 700 /run/user/1000
chown radio:radio /run/user/1000

# Verify PulseAudio setup
log_message "Setting up PulseAudio..."
mkdir -p /home/radio/.config/pulse
chown -R radio:radio /home/radio/.config/pulse

check_prerequisites() {
    log_message "Checking prerequisites..."
    
    # Check Python version (3.7 or higher)
    python3 -c "import sys; assert sys.version_info >= (3,7)" || {
        log_message "ERROR: Python 3.7 or higher is required"
        exit 1
    }
    
    # Check required packages
    REQUIRED_PACKAGES=(
        "python3-venv"
        "python3-pip"
        "vlc"
        "pulseaudio"
        "pigpiod"
        "git"
    )
    
    for package in "${REQUIRED_PACKAGES[@]}"; do
        dpkg -l | grep -q "^ii  $package" || {
            log_message "Installing $package..."
            sudo apt-get install -y "$package"
        }
    done
}

cleanup_system() {
    log_message "Cleaning up system..."
    
    # Stop any existing services
    systemctl stop internetradio || true
    systemctl stop pigpiod || true
    
    # Kill any existing processes
    pkill -f "python.*main.py" || true
    pkill -f "pulseaudio" || true
    
    # Clean up runtime directories
    rm -rf /run/user/1000/pulse
    rm -rf /run/user/1000/radio
    
    # Recreate necessary directories
    mkdir -p /run/user/1000
    chmod 700 /run/user/1000
    chown radio:radio /run/user/1000
}

verify_installation() {
    log_message "Verifying installation..."
    
    # Check service status
    systemctl is-active --quiet internetradio || {
        log_message "ERROR: Radio service not running"
        journalctl -u internetradio -n 50 >> "$LOG_FILE"
        return 1
    }
    
    # Check Python environment
    [ -f "/home/radio/internetRadio/.venv/bin/python" ] || {
        log_message "ERROR: Python virtual environment not found"
        return 1
    }
    
    # Check audio setup
    sudo -u radio pulseaudio --check || {
        log_message "ERROR: PulseAudio not running properly"
        return 1
    }
    
    # Check GPIO access
    [ -w "/dev/gpiomem" ] || {
        log_message "ERROR: GPIO access not configured properly"
        return 1
    }
    
    return 0
}

setup_network() {
    log_message "Setting up network..."
    
    # Ensure wlan0 is up
    ip link set wlan0 up || {
        log_message "ERROR: Could not activate wlan0"
        return 1
    }
    
    # Wait for network interface
    for i in {1..30}; do
        if ip addr show wlan0 | grep -q "state UP"; then
            break
        fi
        sleep 1
    done
    
    # Configure network manager
    cat > /etc/NetworkManager/conf.d/wifi-hotspot.conf <<EOF
[device]
wifi.scan-rand-mac-address=no
EOF
    
    systemctl restart NetworkManager
}

verify_permissions() {
    log_message "Verifying permissions..."
    
    # List of critical directories and files
    PATHS=(
        "/home/radio/internetRadio"
        "/home/radio/internetRadio/scripts"
        "/home/radio/internetRadio/sounds"
        "/run/user/1000"
        "/dev/gpiomem"
    )
    
    for path in "${PATHS[@]}"; do
        if [ -e "$path" ]; then
            # Fix ownership
            chown -R radio:radio "$path" 2>/dev/null || log_message "WARNING: Could not set ownership for $path"
            
            # Fix permissions
            if [ -d "$path" ]; then
                chmod 755 "$path" 2>/dev/null || log_message "WARNING: Could not set permissions for $path"
            elif [ -f "$path" ]; then
                chmod 644 "$path" 2>/dev/null || log_message "WARNING: Could not set permissions for $path"
            fi
        fi
    done
    
    # Make scripts executable
    chmod +x /home/radio/internetRadio/scripts/*.sh 2>/dev/null || log_message "WARNING: Could not make scripts executable"
}

setup_python_env() {
    log_message "Setting up Python environment..."
    
    # Remove existing venv if it exists
    rm -rf /home/radio/internetRadio/.venv
    
    # Create fresh venv
    python3 -m venv /home/radio/internetRadio/.venv
    
    # Activate venv and install requirements
    source /home/radio/internetRadio/.venv/bin/activate
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements with error handling
    if ! pip install -r /home/radio/internetRadio/requirements.txt; then
        log_message "ERROR: Failed to install Python requirements"
        return 1
    fi
    
    # Verify installation
    if ! /home/radio/internetRadio/.venv/bin/python -c "import vlc; import toml; import flask"; then
        log_message "ERROR: Required Python packages not properly installed"
        return 1
    fi
    
    return 0
}
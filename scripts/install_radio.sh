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

# Install Python packages with retry mechanism and error handling
log_message "Installing Python packages..."

# Upgrade pip first
log_message "Upgrading pip..."
python3 -m pip install --upgrade pip || log_error "Failed to upgrade pip"

# Function to install package with retry
install_package() {
    local package=$1
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_message "Installing $package (attempt $attempt of $max_attempts)..."
        
        # Try different installation methods
        if pip install "$package" --no-cache-dir; then
            log_message "Successfully installed $package"
            return 0
        elif pip install "$package" --user; then
            log_message "Successfully installed $package (user installation)"
            return 0
        elif pip install "$package" --ignore-installed; then
            log_message "Successfully installed $package (ignored existing)"
            return 0
        fi

        attempt=$((attempt + 1))
        if [ $attempt -le $max_attempts ]; then
            log_message "Retrying $package installation..."
            sleep 2
        fi
    done

    log_error "Failed to install $package after $max_attempts attempts"
    return 1
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
=======
for package in "${packages[@]}"; do
    log_message "Installing $package..."
    pip install "$package"
done

# Verify installations
for package in "${packages[@]}"; do
    if ! pip list | grep -q "^$package "; then
        log_error "Package $package failed to install"
    fi
done

# Add explicit version check
pip list | grep -E "^(flask|flask-cors|gpiozero|python-vlc|pigpio|toml|werkzeug) "

# Verify Flask installation
if ! pip list | grep -q "^Flask "; then
    log_error "Flask not installed. Trying alternative installation..."
    pip install --no-cache-dir flask
fi

if ! pip list | grep -q "^Flask-Cors "; then
    log_error "Flask-Cors not installed. Trying alternative installation..."
    pip install --no-cache-dir flask-cors
fi

# Setup pigpiod
log_message "Setting up pigpiod..."
sudo systemctl stop pigpiod
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Create systemd service for the application
log_message "Creating systemd service for the application..."
SERVICE_FILE="/etc/systemd/system/internetRadio.service"
if [ ! -f "$SERVICE_FILE" ]; then
    sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Internet Radio Service
After=network.target pigpiod.service

[Service]
Type=simple
User=radio
WorkingDirectory=/home/radio/internetRadio
ExecStart=/home/radio/internetRadio/runApp.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL
    sudo systemctl daemon-reload
    sudo systemctl enable internetRadio.service
    log_message "Service created and enabled"
else
    log_message "Service already exists"
fi

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
ExecStart=/bin/bash /home/radio/internetRadio/scripts/update_radio.sh
StandardOutput=append:/home/radio/internetRadio/scripts/logs/update_radio.log
StandardError=append:/home/radio/internetRadio/scripts/logs/update_radio.log

[Install]
WantedBy=multi-user.target
EOL

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
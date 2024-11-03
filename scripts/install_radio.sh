#!/bin/bash

LOG_FILE="/home/radio/internetRadio/scripts/logs/installation.log"
ERROR_LOG="/home/radio/internetRadio/scripts/logs/installation_errors.log"
SUCCESS=true

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to log errors
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" "$ERROR_LOG"
    SUCCESS=false
}

# Clear logs
echo "" > "$LOG_FILE"
echo "" > "$ERROR_LOG"

log_message "Starting installation..."

# Update system
log_message "Updating system packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev vlc pigpio

# Setup directories
log_message "Setting up directories..."
RADIO_DIR="/home/radio/internetRadio"
mkdir -p "$RADIO_DIR"
cd "$RADIO_DIR" || exit

# Setup virtual environment
log_message "Setting up virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Activate virtual environment
source /home/radio/internetRadio/.venv/bin/activate

# Install Python packages with retry mechanism
log_message "Installing Python packages..."
pip install --upgrade pip

# Install each package individually to better track errors
packages=(
    "gpiozero"
    "python-vlc"  # Note: the import name is 'vlc' but package name is 'python-vlc'
    "pigpio"
    "toml"        # Note: it's 'toml' not 'tomlsource'
    "flask"
    "flask-cors"
)

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

# Create the update timer service
sudo bash -c "cat > /etc/systemd/system/radio-update.service" <<EOL
[Unit]
Description=Daily Radio Update Service
After=network.target

[Service]
Type=oneshot
User=radio
Group=radio
WorkingDirectory=/home/radio/internetRadio
ExecStart=/home/radio/internetRadio/scripts/update_radio.sh

[Install]
WantedBy=multi-user.target
EOL

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
if [ "$SUCCESS" = true ]; then
    log_message "Installation completed successfully"
    log_message "The radio will start automatically on next boot"
    log_message "To check status: sudo systemctl status internetradio"
    log_message "To view logs: journalctl -u internetradio -f"
else
    log_message "Installation completed with errors. Check $ERROR_LOG for details"
fi

# Generate summary
echo -e "\n=== Installation Summary ===" | tee -a "$LOG_FILE"
if [ "$SUCCESS" = true ]; then
    echo "Installation completed successfully!" | tee -a "$LOG_FILE"
else
    echo "Installation completed with errors. Check $ERROR_LOG for details." | tee -a "$LOG_FILE"
    echo -e "\nTroubleshooting Steps:" | tee -a "$ERROR_LOG"
    echo "1. Try running these commands manually:" | tee -a "$ERROR_LOG"
    echo "   source /home/radio/internetRadio/.venv/bin/activate" | tee -a "$ERROR_LOG"
    echo "   pip install flask flask-cors" | tee -a "$ERROR_LOG"
    echo "   sudo systemctl restart pigpiod" | tee -a "$ERROR_LOG"
    echo "2. If still failing, try:" | tee -a "$ERROR_LOG"
    echo "   sudo apt-get update && sudo apt-get upgrade" | tee -a "$ERROR_LOG"
    echo "   sudo reboot" | tee -a "$ERROR_LOG"
fi

echo -e "\nLog files:"
echo "- Full installation log: $LOG_FILE"
echo "- Error log: $ERROR_LOG"

if [ "$SUCCESS" = true ]; then
    echo -e "\nReboot recommended. Reboot now? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
        sudo reboot
    fi
else
    echo -e "\nPlease fix errors before rebooting."
fi
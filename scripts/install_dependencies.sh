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

# Install Python packages with retry mechanism
log_message "Installing Python packages..."
for i in {1..3}; do
    if pip install flask flask-cors gpiozero python-vlc pigpio toml; then
        log_message "Python packages installed successfully"
        break
    else
        log_error "Attempt $i: Failed to install Python packages. Retrying..."
        sleep 2
    fi
done

# Verify Flask installation
if ! pip list | grep -q "^Flask "; then
    log_error "Flask not installed. Trying alternative installation..."
    pip install --no-cache-dir flask flask-cors
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
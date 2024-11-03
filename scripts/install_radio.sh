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

# Install Python packages with retry mechanism
log_message "Installing Python packages..."
pip install --upgrade pip

# Install each package individually to better track errors
packages=(
    "gpiozero"
    "python-vlc"
    "pigpio"
    "toml"
    "flask"
    "flask-cors"
)

for package in "${packages[@]}"; do
    log_message "Installing $package..."
    if ! pip install "$package"; then
        log_error "Failed to install $package"
    fi
done

# Verify installations
for package in "${packages[@]}"; do
    if ! pip list | grep -q "^$package "; then
        log_error "Package $package is not installed"
    else
        log_message "Verified installation of $package"
    fi
done

# ... (rest of installation code) ...

# Final status
if [ "$SUCCESS" = true ]; then
    log_message "Installation completed successfully"
    log_message "The radio will start automatically on next boot"
    log_message "To check status: sudo systemctl status internetradio"
    log_message "To view logs: journalctl -u internetradio -f"
else
    log_message "Installation completed with errors"
fi

echo "=== Installation Finished $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE" 
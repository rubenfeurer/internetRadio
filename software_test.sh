#!/bin/bash

LOG_FILE="/home/internetRadio/radio/radio_diagnostics.log"
RADIO_DIR="/home/internetRadio/radio/internetRadio"
VENV_PATH="$RADIO_DIR/.venv"

#Instructions:
#1. Run this script with sudo
#2. If any errors are reported, fix them and run the script again
#3. Once all errors are resolved, run the runApp.sh script to start the application (sudo ./runApp.sh)  

# Function to log messages with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Clear previous log
echo "" > "$LOG_FILE"
log_message "Starting diagnostic check..."

# Check if running as root (sudo)
if [[ $EUID -ne 0 ]]; then
    log_message "ERROR: Script must be run with sudo privileges"
    exit 1
fi

# Check if radio directory exists
if [ ! -d "$RADIO_DIR" ]; then
    log_message "ERROR: Radio directory not found at $RADIO_DIR"
fi

# Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    log_message "ERROR: Virtual environment not found at $VENV_PATH"
else
    log_message "Virtual environment found"
fi

# Check required system packages
packages=("python3" "vlc" "pigpio")
for package in "${packages[@]}"; do
    if ! dpkg -l | grep -q "^ii  $package"; then
        log_message "ERROR: Required package '$package' is not installed"
    else
        log_message "Package '$package' is installed"
    fi
done

# Check if pigpiod is running
if ! pgrep pigpiod > /dev/null; then
    log_message "ERROR: pigpiod daemon is not running"
else
    log_message "pigpiod daemon is running"
fi

# Check Python dependencies
log_message "Checking Python packages..."
source "$VENV_PATH/bin/activate" 2>/dev/null
if [ $? -ne 0 ]; then
    log_message "ERROR: Failed to activate virtual environment"
else
    required_packages=("flask" "flask-cors" "gpiozero" "python-vlc" "pigpio" "toml")
    for package in "${required_packages[@]}"; do
        if ! pip list | grep -q "^$package "; then
            log_message "ERROR: Required Python package '$package' is not installed"
        else
            log_message "Python package '$package' is installed"
        fi
    done
fi

# Check file permissions
files_to_check=(
    "$RADIO_DIR/main.py"
    "$RADIO_DIR/config.toml"
)

for file in "${files_to_check[@]}"; do
    if [ ! -f "$file" ]; then
        log_message "ERROR: Required file '$file' not found"
    elif [ ! -r "$file" ]; then
        log_message "ERROR: No read permission for '$file'"
    else
        log_message "File '$file' exists and is readable"
    fi
done

# Check if VLC can play audio
if ! sudo -u radio timeout 2 cvlc --play-and-exit /usr/share/sounds/freedesktop/stereo/complete.oga >/dev/null 2>&1; then
    log_message "ERROR: VLC audio playback test failed"
else
    log_message "VLC audio playback test successful"
fi

# Check GPIO access
if ! gpio readall >/dev/null 2>&1; then
    log_message "ERROR: Cannot access GPIO"
else
    log_message "GPIO access successful"
fi

# Check network connectivity
if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    log_message "ERROR: No internet connectivity"
else
    log_message "Internet connectivity confirmed"
fi

log_message "Diagnostic check complete. Check $LOG_FILE for details."
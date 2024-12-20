#!/bin/bash

LOG_FILE="/home/radio/internetRadio/scripts/logs/radio_diagnostics.log"
RADIO_DIR="/home/radio/internetRadio"
VENV_PATH="$RADIO_DIR/.venv"

#Instructions:
#1. Run this script with sudo
#2. If any errors are reported, fix them and run the script again
#3. Once all errors are resolved, run install_radio.sh to set up the system
#4. The application can be manually started with: sudo ./scripts/runApp.sh

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
VENV_PYTHON="/home/radio/internetRadio/.venv/bin/python3"

check_package() {
    local package=$1
    local import_name=$2
    if $VENV_PYTHON -c "import ${import_name}" 2>/dev/null; then
        log_message "Python package '$package' is installed"
        return 0
    else
        log_message "ERROR: Required Python package '$package' is not installed"
        return 1
    fi
}

# Activate virtual environment
source /home/radio/internetRadio/.venv/bin/activate

# Check each package with correct import names
check_package "flask" "flask"
check_package "flask-cors" "flask_cors"
check_package "gpiozero" "gpiozero"
check_package "python-vlc" "vlc"
check_package "pigpio" "pigpio"
check_package "toml" "toml"

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

# Check if there were any errors in the log
if grep -q "ERROR:" "$LOG_FILE"; then
    echo
    echo "Errors were found during diagnostics."
    echo "Would you like to view the diagnostic log? (y/N): "
    read -r view_log
    if [[ $view_log =~ ^[Yy]$ ]]; then
        if command -v less >/dev/null 2>&1; then
            less "$LOG_FILE"
        else
            cat "$LOG_FILE"
        fi
        echo
        echo "The full diagnostic log is available at: $LOG_FILE"
    else
        echo "You can view the log later with: cat $LOG_FILE"
    fi
else
    echo "No errors found during diagnostics."
    echo "Would you like to view the full diagnostic log anyway? (y/N): "
    read -r view_log
    if [[ $view_log =~ ^[Yy]$ ]]; then
        if command -v less >/dev/null 2>&1; then
            less "$LOG_FILE"
        else
            cat "$LOG_FILE"
        fi
    fi
fi

echo
echo "Diagnostic log location: $LOG_FILE"
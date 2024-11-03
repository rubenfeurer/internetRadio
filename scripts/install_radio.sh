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
if [ "$SUCCESS" = true ]; then
    log_message "Installation completed successfully"
    log_message "The radio will start automatically on next boot"
    log_message "To check status: sudo systemctl status internetradio"
    log_message "To view logs: journalctl -u internetradio -f"
else
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
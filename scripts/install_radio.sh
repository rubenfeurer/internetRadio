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

# Improve Python package installation
install_python_packages() {
    log_message "Installing Python packages..."
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip first
    python3 -m pip install --upgrade pip
    
    # Install packages with specific versions and error handling
    PACKAGES=(
        "flask==2.0.1"
        "flask-cors==3.0.10"
        "gpiozero"
        "python-vlc"
        "pigpio"
        "toml"
    )
    
    for package in "${PACKAGES[@]}"; do
        log_message "Installing $package..."
        # Try up to 3 times to install each package
        for i in {1..3}; do
            if pip install "$package"; then
                log_message "Successfully installed $package"
                break
            else
                log_message "Attempt $i failed for $package"
                if [ $i -eq 3 ]; then
                    log_error "Failed to install $package after 3 attempts"
                    # Try system packages as fallback
                    if [[ $package == flask* ]]; then
                        log_message "Trying system package for $package..."
                        sudo apt-get install -y python3-${package%%=*}
                    fi
                fi
                sleep 2
            fi
        done
    done
    
    # Verify installations
    python3 -c "import flask" || log_error "Flask verification failed"
    python3 -c "import flask_cors" || log_error "Flask-CORS verification failed"
    
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

# Add this function to properly set up audio
setup_audio() {
    log_message "Setting up audio system..."
    
    # Kill any existing pulseaudio processes
    log_message "Stopping existing pulseaudio processes..."
    sudo killall pulseaudio || true
    sudo killall -9 pulseaudio || true
    
    # Clean up old files
    log_message "Cleaning up old audio files..."
    sudo rm -rf /home/radio/.config/pulse/*
    sudo rm -rf /run/user/1000/pulse/*
    
    # Create fresh pulse config
    log_message "Creating fresh audio configuration..."
    sudo mkdir -p /home/radio/.config/pulse
    sudo tee /home/radio/.config/pulse/client.conf > /dev/null <<EOL
autospawn = no
daemon-binary = /usr/bin/pulseaudio
EOL
    
    # Set correct ownership
    sudo chown -R radio:radio /home/radio/.config/pulse
    
    # Update service file
    log_message "Updating service configuration..."
    sudo sed -i '/ExecStartPre=\/usr\/bin\/pulseaudio/c\ExecStartPre=\/bin\/bash -c "killall pulseaudio || true; sleep 2; /usr/bin/pulseaudio --start --exit-idle-time=-1"' /etc/systemd/system/internetradio.service
    
    # Reload systemd
    sudo systemctl daemon-reload
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
#!/bin/bash

# Simple logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Install required system packages
install_system_packages() {
    log_message "Updating system packages..."
    apt-get update -qq
    apt-get install -qq -y python3-pip python3-dev vlc pigpio
}

# Install Python packages quietly
install_python_packages() {
    log_message "Installing Python packages..."
    source .venv/bin/activate >/dev/null 2>&1
    pip install --quiet --no-input \
        gpiozero \
        python-vlc \
        pigpio \
        toml \
        flask \
        flask-cors
    deactivate >/dev/null 2>&1
}

# Setup virtual environment
setup_venv() {
    log_message "Setting up virtual environment..."
    python3 -m venv .venv
}

# Setup services
setup_services() {
    log_message "Setting up services..."
    systemctl enable pigpiod >/dev/null 2>&1
    systemctl enable internetradio >/dev/null 2>&1
    systemctl enable radio-update.timer >/dev/null 2>&1
    
    systemctl start pigpiod
    systemctl start internetradio
    systemctl start radio-update.timer
}

# Main installation function
main() {
    log_message "Starting installation..."
    
    install_system_packages
    setup_venv
    install_python_packages
    setup_services
    
    # Check if services are running
    if systemctl is-active --quiet internetradio && \
       systemctl is-active --quiet radio-update.timer; then
        log_message "Installation completed successfully"
        log_message "Service is running at http://$(hostname -I | cut -d' ' -f1):8080"
        return 0
    else
        log_message "Installation failed - service not running"
        return 1
    fi
}

# Run main function
main
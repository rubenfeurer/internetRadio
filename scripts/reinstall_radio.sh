#!/bin/bash

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_services() {
    log_message "Checking services..."
    
    if systemctl is-active --quiet internetradio.service && systemctl is-active --quiet pigpiod.service; then
        echo "✓ Services are running"
        return 0
    else
        echo "✗ Service check failed"
        return 1
    fi
}

check_audio() {
    log_message "Checking audio..."
    
    if [ -f "/etc/asound.conf" ] && aplay -l | grep -q "card 2: Headphones"; then
        echo "✓ Audio configuration is correct"
        return 0
    else
        echo "✗ Audio check failed"
        return 1
    fi
}

check_web() {
    log_message "Checking web interface..."
    IP_ADDRESS=$(hostname -I | cut -d' ' -f1)
    
    if curl -s "http://${IP_ADDRESS}:5000" > /dev/null; then
        echo "✓ Web interface is accessible"
        return 0
    else
        echo "✗ Web interface check failed"
        return 1
    fi
}

get_current_branch() {
    cd /home/radio/internetRadio
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo $BRANCH
}

main() {
    if [ "$EUID" -ne 0 ]; then
        log_message "Please run as root"
        exit 1
    }

    # Store current branch
    CURRENT_BRANCH=$(get_current_branch)
    log_message "Current branch: $CURRENT_BRANCH"
    
    # Store backup of config.toml if it exists
    if [ -f "/home/radio/internetRadio/config.toml" ]; then
        log_message "Backing up config.toml"
        cp /home/radio/internetRadio/config.toml /tmp/config.toml.backup
    fi
    
    # Uninstall
    log_message "Starting uninstallation..."
    if ! bash /home/radio/internetRadio/scripts/uninstall_radio.sh; then
        log_message "Uninstallation failed"
        exit 1
    fi
    
    # Remove old directory
    log_message "Removing old installation..."
    rm -rf /home/radio/internetRadio
    
    # Clone repository
    log_message "Cloning repository..."
    cd /home/radio
    if ! git clone https://github.com/rubenfeurer/internetRadio.git; then
        log_message "Failed to clone repository"
        exit 1
    fi
    
    # Checkout correct branch
    cd /home/radio/internetRadio
    if ! git checkout $CURRENT_BRANCH; then
        log_message "Failed to checkout branch $CURRENT_BRANCH"
        exit 1
    fi
    
    # Restore config if backup exists
    if [ -f "/tmp/config.toml.backup" ]; then
        log_message "Restoring config.toml"
        cp /tmp/config.toml.backup /home/radio/internetRadio/config.toml
        rm /tmp/config.toml.backup
    fi
    
    # Install
    log_message "Starting installation..."
    if ! bash /home/radio/internetRadio/scripts/install_radio.sh; then
        log_message "Installation failed"
        exit 1
    fi
    
    # Wait for services to start
    log_message "Waiting for services to start..."
    sleep 10
    
    # Verify installation
    log_message "Verifying installation..."
    
    FAILED=0
    
    check_services || FAILED=1
    check_audio || FAILED=1
    check_web || FAILED=1
    
    if [ $FAILED -eq 0 ]; then
        log_message "✓ Reinstallation completed successfully"
        IP_ADDRESS=$(hostname -I | cut -d' ' -f1)
        log_message "Radio is accessible at http://${IP_ADDRESS}:5000"
        exit 0
    else
        log_message "✗ Reinstallation verification failed"
        exit 1
    fi
}

main "$@" 
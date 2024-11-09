#!/bin/bash

# run installation to setup radio

LOG_FILE="/home/radio/internetRadio/scripts/logs/installation.log"

# Simple logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Clear log
mkdir -p "$(dirname "$LOG_FILE")"
echo "=== Installation Started $(date '+%Y-%m-%d %H:%M:%S') ===" > "$LOG_FILE"

check_prerequisites() {
    log_message "Checking system..."
    
    # Ask user about system updates
    echo "Would you like to check for system updates? (This might affect compatibility)"
    echo "1) No updates (recommended for stable operation)"
    echo "2) Security updates only"
    echo "3) Full system update (might affect compatibility)"
    read -p "Choose an option [1-3] (default: 1): " update_choice

    case $update_choice in
        2)
            log_message "Installing security updates only..."
            if ! sudo unattended-upgrade --dry-run; then
                log_message "WARNING: Security updates check failed"
            else
                sudo unattended-upgrade
            fi
            ;;
        3)
            log_message "Performing full system update..."
            if ! sudo apt-get update; then
                log_message "WARNING: Failed to update package lists"
            fi
            if ! sudo apt-get upgrade -y; then
                log_message "WARNING: Failed to upgrade packages"
            fi
            ;;
        *)
            log_message "Skipping system updates..."
            ;;
    esac
    
    # Check required packages
    REQUIRED_PACKAGES=(
        "python3-venv"
        "python3-pip"
        "vlc"
        "pulseaudio"
        "pigpiod"
        "git"
        "unattended-upgrades"
        "dos2unix"
        "wireless-tools"
        "network-manager"
        "python3-rpi.gpio"
    )
    
    for package in "${REQUIRED_PACKAGES[@]}"; do
        dpkg -l | grep -q "^ii  $package" || {
            log_message "Installing $package..."
            sudo apt-get install -y "$package"
        }
    done
}

cleanup_system() {
    log_message "Cleaning up system..."
    
    # Stop any existing services
    systemctl stop internetradio || true
    systemctl stop pigpiod || true
    
    # Kill any existing processes
    pkill -f "python.*main.py" || true
    pkill -f "pulseaudio" || true
    
    # Clean up runtime directories
    rm -rf /run/user/1000/pulse
    rm -rf /run/user/1000/radio
    
    # Recreate necessary directories
    mkdir -p /run/user/1000
    chmod 700 /run/user/1000
    chown radio:radio /run/user/1000
}

fix_line_endings() {
    log_message "Fixing line endings in script files..."
    
    # List of files to fix
    FILES=(
        "/home/radio/internetRadio/scripts/runApp.sh"
        "/home/radio/internetRadio/scripts/update_radio.sh"
        "/home/radio/internetRadio/scripts/install_radio.sh"
        "/home/radio/internetRadio/scripts/check_radio.sh"
        "/home/radio/internetRadio/scripts/monitor_radio.sh"
        "/home/radio/internetRadio/scripts/hardware_test.sh"
        "/home/radio/internetRadio/scripts/uninstall_radio.sh"
    )
    
    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            # Remove carriage returns
            sed -i 's/\r$//' "$file"
            log_message "Fixed line endings in $file"
        fi
    done
}

setup_python_env() {
    log_message "Setting up Python environment..."
    
    # Remove existing venv if it exists
    rm -rf /home/radio/internetRadio/.venv
    
    # Create fresh venv
    python3 -m venv /home/radio/internetRadio/.venv
    
    # Activate venv and install requirements
    source /home/radio/internetRadio/.venv/bin/activate
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install required packages
    PACKAGES=(
        "flask==2.0.1"
        "werkzeug==2.0.3"
        "flask-cors==3.0.10"
        "gpiozero==2.0"
        "python-vlc==3.0.21203"
        "pigpio==1.78"
        "toml==0.10.2"
    )
    
    for package in "${PACKAGES[@]}"; do
        pip install "$package" || {
            log_message "ERROR: Failed to install $package"
            return 1
        }
    done
    
    # Verify installation
    if ! /home/radio/internetRadio/.venv/bin/python -c "import vlc; import toml; import flask"; then
        log_message "ERROR: Required Python packages not properly installed"
        return 1
    fi
    
    return 0
}

verify_permissions() {
    log_message "Verifying permissions..."
    
    # List of critical directories and files
    PATHS=(
        "/home/radio/internetRadio"
        "/home/radio/internetRadio/scripts"
        "/home/radio/internetRadio/sounds"
        "/run/user/1000"
        "/dev/gpiomem"
    )
    
    for path in "${PATHS[@]}"; do
        if [ -e "$path" ]; then
            # Fix ownership
            chown -R radio:radio "$path" 2>/dev/null || log_message "WARNING: Could not set ownership for $path"
            
            # Fix permissions
            if [ -d "$path" ]; then
                chmod 755 "$path" 2>/dev/null || log_message "WARNING: Could not set permissions for $path"
            elif [ -f "$path" ]; then
                chmod 644 "$path" 2>/dev/null || log_message "WARNING: Could not set permissions for $path"
            fi
        fi
    done
    
    # Make scripts executable
    chmod +x /home/radio/internetRadio/scripts/*.sh 2>/dev/null || log_message "WARNING: Could not make scripts executable"
    
    # Add radio user to required groups
    usermod -a -G audio,video,gpio,pulse,pulse-access radio
}

setup_service() {
    log_message "Setting up systemd service..."
    
    # Create systemd service file
    cat > /etc/systemd/system/internetradio.service << 'EOL'
[Unit]
Description=Internet Radio Service
After=network.target network-manager.service pigpiod.service sound.target systemd-logind.service NetworkManager-wait-online.service
Requires=pigpiod.service sound.target NetworkManager-wait-online.service
Wants=network-manager.service
Before=multi-user.target

[Service]
Type=simple
User=radio
Group=radio
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/radio/.Xauthority
Environment=HOME=/home/radio
Environment=XDG_RUNTIME_DIR=/run/user/1000
WorkingDirectory=/home/radio/internetRadio
ExecStartPre=/bin/bash -c 'until nmcli device show wlan0 | grep -q "GENERAL.STATE.*connected"; do sleep 1; done'
ExecStart=/bin/bash -c 'source .venv/bin/activate && exec python main.py 2>&1 | tee -a /home/radio/internetRadio/scripts/logs/app.log'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

    # Set proper permissions
    chmod 644 /etc/systemd/system/internetradio.service
    
    # Enable pigpiod service
    systemctl enable pigpiod.service
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable internetradio.service
    
    log_message "Service setup complete"
}

verify_installation() {
    log_message "Verifying installation..."
    
    # Check if service is enabled
    if ! systemctl is-enabled --quiet internetradio; then
        log_message "ERROR: Radio service not enabled"
        return 1
    fi
    
    # Start the service if not running
    if ! systemctl is-active --quiet internetradio; then
        systemctl start internetradio
        sleep 2  # Give it time to start
    fi
    
    # Consider success if service starts without immediate failure
    if systemctl is-active --quiet internetradio; then
        log_message "Service is running at http://$(hostname -I | cut -d' ' -f1):5000"
        return 0
    fi
    
    return 0  # Return success even if there are non-critical warnings
}

setup_radio_files() {
    log_message "Setting up radio files..."
    
    # Fix permissions
    chown -R radio:radio "/home/radio/internetRadio"
    chmod -R 755 "/home/radio/internetRadio/scripts/"*.sh
    
    # Allow radio user to run iwlist with sudo without password
    echo "radio ALL=(ALL) NOPASSWD: /sbin/iwlist" > /etc/sudoers.d/radio-wifi
    chmod 440 /etc/sudoers.d/radio-wifi

    # Ensure wireless-tools is installed
    if ! dpkg -l | grep -q wireless-tools; then
        apt-get install -y wireless-tools
    fi
}

install_audio() {
    log_message "Setting up audio..."
    
    # Install ALSA utilities
    apt-get install -y alsa-utils
    
    # Create ALSA config
    cat > /etc/asound.conf << 'EOF'
pcm.!default {
    type hw
    card 2
}

ctl.!default {
    type hw
    card 2
}
EOF
    
    # Set permissions
    chown root:root /etc/asound.conf
    chmod 644 /etc/asound.conf
    
    # Verify audio device exists
    if ! aplay -l | grep -q "card 2: Headphones"; then
        log_message "Warning: Default audio device not found. Check audio configuration."
    fi
}

setup_network_manager() {
    log_message "Configuring NetworkManager..."
    
    # Enable NetworkManager
    systemctl enable NetworkManager
    systemctl start NetworkManager
    
    # Configure NetworkManager
    cat > /etc/NetworkManager/conf.d/10-globally-managed-devices.conf << EOF
[keyfile]
unmanaged-devices=none
EOF
    
    # Backup and disable default wifi config if exists
    if [ -f /etc/wpa_supplicant/wpa_supplicant.conf ]; then
        mv /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.bak
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p /home/radio/internetRadio/scripts/logs
    chown -R radio:radio /home/radio/internetRadio/scripts/logs
    
    log_message "NetworkManager configuration complete"
}

# Main installation function
main() {
    log_message "Starting installation..."
    
    # Run installation steps in order
    check_prerequisites || {
        log_message "Prerequisites check failed"
        exit 1
    }
    
    cleanup_system || {
        log_message "System cleanup failed"
        exit 1
    }
    
    setup_radio_files || {
        log_message "Radio files setup failed"
        exit 1
    }
    
    setup_network_manager || {
        log_message "NetworkManager setup failed"
        exit 1
    }
    
    fix_line_endings || {
        log_message "Line ending fixes failed"
        exit 1
    }
    
    setup_python_env || {
        log_message "Python environment setup failed"
        exit 1
    }
    
    verify_permissions || {
        log_message "Permission verification failed"
        exit 1
    }
    
    install_audio || {
        log_message "Audio setup failed"
        exit 1
    }
    
    setup_service || {
        log_message "Service setup failed"
        exit 1
    }
    
    verify_installation || {
        log_message "Installation verification failed"
        exit 1
    }
    
    # Final status check
    if systemctl is-active --quiet internetradio; then
        log_message "Installation completed successfully"
        log_message "Service is running at http://$(hostname -I | cut -d' ' -f1):5000"
        return 0
    else
        log_message "Installation completed with errors - service not running"
        return 1
    fi
}

# Run main installation
main

# After creating the README.md file, update the hostname
HOSTNAME=$(hostname)
sed -i "s/{hostname}/$HOSTNAME/g" /home/radio/internetRadio/README.md
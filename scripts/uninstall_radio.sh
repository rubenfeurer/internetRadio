#!/bin/bash

LOG_FILE="/home/radio/internetRadio/scripts/logs/uninstall.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Ask for confirmation
echo "WARNING: This will remove the Internet Radio application and its data."
read -p "Are you sure you want to continue? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    log_message "Uninstallation cancelled by user"
    exit 1
fi

log_message "Starting uninstallation..."

# Stop all services
log_message "Stopping all services..."
SERVICES=(
    "internetradio.service"
    "radio-update.timer"
    "radio-update.service"
    "pigpiod.service"
)

for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service"; then
        log_message "Stopping $service..."
        sudo systemctl stop "$service"
    fi
    if systemctl is-enabled --quiet "$service" 2>/dev/null; then
        log_message "Disabling $service..."
        sudo systemctl disable "$service"
    fi
done

# Remove service files
log_message "Removing service files..."
SERVICE_FILES=(
    "/etc/systemd/system/internetradio.service"
    "/etc/systemd/system/radio-update.service"
    "/etc/systemd/system/radio-update.timer"
)

for file in "${SERVICE_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_message "Removing $file..."
        sudo rm -f "$file"
    fi
done

# Reload systemd
sudo systemctl daemon-reload
log_message "Systemd configuration reloaded"

# Remove Python packages from virtual environment
if [ -d "/home/radio/internetRadio/.venv" ]; then
    log_message "Removing Python virtual environment..."
    if [ -f "/home/radio/internetRadio/.venv/bin/activate" ]; then
        source /home/radio/internetRadio/.venv/bin/activate
        pip freeze | xargs pip uninstall -y 2>/dev/null || true
        deactivate
    fi
    sudo rm -rf "/home/radio/internetRadio/.venv"
fi

# Clean up system packages
read -p "Do you want to remove installed system packages? (y/N): " remove_packages
if [[ $remove_packages == [yY] ]]; then
    log_message "Removing system packages..."
    PACKAGES=(
        "python3-pip"
        "python3-dev"
        "vlc"
        "pigpio"
        "dos2unix"
    )
    
    for package in "${PACKAGES[@]}"; do
        if dpkg -l | grep -q "^ii  $package "; then
            sudo apt-get remove -y "$package"
        fi
    done
    
    sudo apt-get autoremove -y
fi

# Remove application directories and files
log_message "Removing application files..."
DIRS_TO_REMOVE=(
    "/home/radio/internetRadio"
    "/run/user/1000/pulse"
    "/var/log/internetradio"
)

for dir in "${DIRS_TO_REMOVE[@]}"; do
    if [ -d "$dir" ]; then
        log_message "Removing directory: $dir"
        sudo rm -rf "$dir"
    fi
done

# Remove user from groups but keep the user
log_message "Removing radio user from additional groups..."
GROUPS=(
    "audio"
    "video"
    "gpio"
    "pulse"
    "pulse-access"
)

for group in "${GROUPS[@]}"; do
    if groups radio | grep -q "\b$group\b"; then
        sudo gpasswd -d radio "$group"
    fi
done

# Clean up runtime directories
log_message "Cleaning up runtime directories..."
sudo rm -rf /run/user/1000/pulse
sudo rm -rf /run/user/1000/radio

# Final cleanup
log_message "Performing final cleanup..."
sudo systemctl daemon-reload
sudo ldconfig

# Save log before complete removal
FINAL_LOG="$HOME/radio_uninstall.log"
cp "$LOG_FILE" "$FINAL_LOG"

log_message "Uninstallation completed successfully"
echo
echo "Internet Radio has been removed from the system."
echo "The radio user account has been preserved."
echo "Uninstallation log has been saved to: $FINAL_LOG"
echo
echo "Please reboot the system to complete the cleanup."
read -p "Would you like to reboot now? (y/N): " reboot
if [[ $reboot == [yY] ]]; then
    sudo reboot
fi

# Add process cleanup section
log_message "Cleaning up running processes..."
sudo pkill -f pulseaudio || true
sudo pkill -f python || true
sudo pkill -f vlc || true

# Add runtime directory cleanup
log_message "Cleaning runtime directories..."
sudo rm -rf /run/user/1000/* || true

# Stop and remove service
if systemctl is-active --quiet internetradio; then
    systemctl stop internetradio
fi
if systemctl is-enabled --quiet internetradio; then
    systemctl disable internetradio
fi
rm -f /etc/systemd/system/internetradio.service
systemctl daemon-reload

# Add repository handling
log_message "Checking for repository..."
if [ -d "/home/radio/internetRadio/.git" ]; then
    read -p "Repository clone found. Do you want to remove it? (y/N): " remove_repo
    if [[ $remove_repo == [yY] ]]; then
        log_message "Removing repository..."
        sudo rm -rf /home/radio/internetRadio
    else
        log_message "Keeping repository but cleaning build artifacts..."
        # Clean but keep repo
        if [ -d "/home/radio/internetRadio/.venv" ]; then
            sudo rm -rf /home/radio/internetRadio/.venv
        fi
        sudo rm -f /home/radio/internetRadio/logs/*
    fi
fi

# Add ALSA configuration cleanup
cleanup_audio() {
    log_message "Cleaning up audio configuration..."
    rm -f /etc/asound.conf
}

main() {
    # ... existing checks ...

    # Stop and disable services
    cleanup_services

    # Remove audio config
    cleanup_audio

    # Remove Python packages and venv
    cleanup_python_env

    # Remove logs
    cleanup_logs

    log_message "Uninstallation completed successfully"
}
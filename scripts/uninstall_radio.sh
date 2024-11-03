#!/bin/bash

LOG_FILE="/home/radio/internetRadio/scripts/logs/uninstall.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Ask for confirmation
echo "WARNING: This will completely remove the Internet Radio application and all its data."
read -p "Are you sure you want to continue? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    log_message "Uninstallation cancelled by user"
    exit 1
fi

log_message "Starting uninstallation..."

# Stop and disable services
log_message "Stopping and removing services..."
sudo systemctl stop internetradio.service
sudo systemctl disable internetradio.service
sudo systemctl stop radio-update.timer
sudo systemctl disable radio-update.timer
sudo systemctl stop radio-update.service
sudo systemctl disable radio-update.service

# Remove service files
log_message "Removing service files..."
sudo rm -f /etc/systemd/system/internetradio.service
sudo rm -f /etc/systemd/system/radio-update.service
sudo rm -f /etc/systemd/system/radio-update.timer
sudo systemctl daemon-reload

# Stop and disable pigpiod if not needed by other applications
read -p "Do you want to remove pigpiod service? (y/N): " remove_pigpio
if [[ $remove_pigpio == [yY] ]]; then
    log_message "Stopping and disabling pigpiod..."
    sudo systemctl stop pigpiod
    sudo systemctl disable pigpiod
fi

# Remove Python packages from virtual environment
if [ -d "/home/radio/internetRadio/.venv" ]; then
    log_message "Removing Python virtual environment..."
    source /home/radio/internetRadio/.venv/bin/activate
    pip freeze | xargs pip uninstall -y
    deactivate
fi

# Remove application directory
log_message "Removing application directory..."
sudo rm -rf /home/radio/internetRadio

# Remove radio user from groups
log_message "Removing radio user from additional groups..."
sudo gpasswd -d radio audio || true
sudo gpasswd -d radio video || true
sudo gpasswd -d radio gpio || true
sudo gpasswd -d radio pulse || true
sudo gpasswd -d radio pulse-access || true

# Option to remove radio user
read -p "Do you want to remove the radio user? (y/N): " remove_user
if [[ $remove_user == [yY] ]]; then
    log_message "Removing radio user..."
    sudo pkill -u radio  # Kill all processes owned by radio
    sudo userdel -r radio  # -r flag removes home directory
fi

# Remove system packages if not needed by other applications
read -p "Do you want to remove installed system packages (python3-pip, vlc, etc.)? (y/N): " remove_packages
if [[ $remove_packages == [yY] ]]; then
    log_message "Removing system packages..."
    sudo apt-get remove -y python3-pip python3-dev vlc pigpio
    sudo apt-get autoremove -y
fi

# Clean up runtime directory
log_message "Cleaning up runtime directory..."
sudo rm -rf /run/user/1000

# Remove logs
log_message "Removing log files..."
sudo rm -rf /var/log/internetradio*

# Final cleanup
log_message "Performing final cleanup..."
sudo systemctl daemon-reload
sudo ldconfig

log_message "Uninstallation completed successfully"
echo "Internet Radio has been completely removed from the system."
echo "Log file is available at: $LOG_FILE"
echo "Please reboot the system to complete the cleanup."
read -p "Would you like to reboot now? (y/N): " reboot
if [[ $reboot == [yY] ]]; then
    sudo reboot
fi 
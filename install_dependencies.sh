#!/bin/bash

LOG_FILE="/home/radio/installation.log"
ERROR_LOG="/home/radio/installation_errors.log"
SUCCESS=true

# Function to log messages with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to log errors with timestamps
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" "$ERROR_LOG"
    SUCCESS=false
}

# Clear previous logs
echo "" > "$LOG_FILE"
echo "" > "$ERROR_LOG"

log_message "Starting installation..."

# Function to check command success
check_command() {
    if [ $? -ne 0 ]; then
        log_error "$1 failed"
        return 1
    else
        log_message "$1 successful"
        return 0
    fi
}

echo "Updating package lists..."
sudo apt-get update
check_command "System update" || log_error "Try running 'sudo apt-get update' manually"

echo "Installing system dependencies..."
sudo apt-get install -y python3-pip python3-dev vlc pigpio
check_command "System dependencies installation" || log_error "Try running 'sudo apt-get install -y python3-pip python3-dev vlc pigpio' manually"

echo "Setting up user groups and permissions..."
# Add radio user to required groups
sudo usermod -a -G gpio,dialout,video,audio radio
check_command "User group setup" || log_error "Try running 'sudo usermod -a -G gpio,dialout,video,audio radio' manually"

# Fix GPIO permissions
sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem
check_command "GPIO permissions setup" || log_error "GPIO permission setup failed. Try rebooting and running the script again"

echo "Creating Python virtual environment..."
cd /home/radio/internetRadio || log_error "Directory /home/radio/internetRadio not found"
python3 -m venv .venv
source .venv/bin/activate
check_command "Virtual environment setup" || log_error "Try running 'python3 -m venv .venv' manually"

echo "Installing Python packages..."
pip3 install flask flask-cors gpiozero python-vlc pigpio toml
check_command "Python packages installation" || log_error "Try running pip install commands manually after activating virtual environment"

echo "Setting up pigpiod service..."
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
check_command "pigpiod service setup" || log_error "Try running 'sudo systemctl start pigpiod' manually"

# Add pigpiod to rc.local if not already there
if ! grep -q "pigpiod" /etc/rc.local; then
    sudo sed -i '/^exit 0/i /usr/bin/pigpiod' /etc/rc.local
    check_command "Adding pigpiod to rc.local" || log_error "Failed to add pigpiod to rc.local"
fi

echo "Setting file permissions..."
sudo chown -R radio:radio /home/radio/internetRadio
sudo chmod -R 755 /home/radio/internetRadio
check_command "File permissions setup" || log_error "Permission setup failed"

# Verify installations
log_message "Verifying installations..."

# Check Python packages
source .venv/bin/activate
for package in flask flask-cors gpiozero python-vlc pigpio toml; do
    if ! pip list | grep -q "^$package "; then
        log_error "Package $package is not installed"
    fi
done

# Check pigpiod
if ! systemctl is-active --quiet pigpiod; then
    log_error "pigpiod is not running"
fi

# Generate installation summary
echo -e "\n=== Installation Summary ===" | tee -a "$LOG_FILE"
if [ "$SUCCESS" = true ]; then
    echo "Installation completed successfully!" | tee -a "$LOG_FILE"
else
    echo "Installation completed with errors. Please check $ERROR_LOG for details." | tee -a "$LOG_FILE"
    echo -e "\nTroubleshooting Guide:" | tee -a "$ERROR_LOG"
    echo "1. Check error messages above for specific issues" | tee -a "$ERROR_LOG"
    echo "2. Ensure you have internet connectivity" | tee -a "$ERROR_LOG"
    echo "3. Verify you have sufficient disk space: df -h" | tee -a "$ERROR_LOG"
    echo "4. Check if virtual environment is activated: source /home/radio/internetRadio/.venv/bin/activate" | tee -a "$ERROR_LOG"
    echo "5. Verify user permissions: groups radio" | tee -a "$ERROR_LOG"
    echo "6. Check system logs: sudo journalctl -xe" | tee -a "$ERROR_LOG"
    echo "7. For GPIO issues, try rebooting the system" | tee -a "$ERROR_LOG"
fi

echo -e "\nLog files:"
echo "- Full installation log: $LOG_FILE"
echo "- Error log: $ERROR_LOG"

if [ "$SUCCESS" = true ]; then
    echo -e "\nWould you like to reboot now? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
        sudo reboot
    fi
else
    echo -e "\nPlease fix the errors listed in $ERROR_LOG before rebooting."
fi 
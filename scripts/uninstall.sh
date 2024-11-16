#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Starting uninstallation..."

# Stop and disable the service
systemctl stop radio
systemctl disable radio

# Remove service file
rm -f /etc/systemd/system/radio.service

# Clean up Python packages (optional)
echo "Do you want to remove installed Python packages? (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
    pip3 uninstall -y flask python-vlc requests tomli
fi

# Clean up system packages (optional)
echo "Do you want to remove system packages (vlc, alsa-utils)? (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
    apt-get remove -y vlc alsa-utils
    apt-get autoremove -y
fi

# Clean up configuration and logs (optional)
echo "Do you want to remove configuration and log files? (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
    rm -rf /home/radio/internetRadio/logs/*
    rm -rf /home/radio/internetRadio/config/*
fi

# Reload systemd daemon
systemctl daemon-reload

echo "Uninstallation complete!" 
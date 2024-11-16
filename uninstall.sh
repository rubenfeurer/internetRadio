#!/bin/bash

# Make script executable
chmod +x uninstall.sh

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Stop and disable the service
systemctl stop radio
systemctl disable radio

# Remove service file
rm /etc/systemd/system/radio.service

# Reload systemd daemon
systemctl daemon-reload

echo "Uninstallation complete!" 
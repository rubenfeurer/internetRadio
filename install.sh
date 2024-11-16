#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Add radio user to audio group
usermod -a -G audio radio

# Stop the service if it's running
systemctl stop radio 2>/dev/null || true

# Copy service file
cp radio.service /etc/systemd/system/

# Reload systemd daemon
systemctl daemon-reload

# Enable and start the service
systemctl enable radio
systemctl start radio

echo "Installation complete! Service is running."
echo "Check status with: systemctl status radio"
echo "View logs with: journalctl -u radio -f" 
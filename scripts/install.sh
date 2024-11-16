#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Starting installation..."

# Update package list
apt-get update

# Install required system packages
echo "Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    vlc \
    alsa-utils \
    git

# Install Python dependencies
echo "Installing Python packages..."
pip3 install \
    flask \
    python-vlc \
    requests \
    tomli

# Add radio user to required groups
usermod -a -G audio,video radio

# Create required directories
echo "Setting up directories..."
mkdir -p /home/radio/internetRadio/logs
mkdir -p /home/radio/internetRadio/config

# Set proper permissions
chown -R radio:radio /home/radio/internetRadio

# Stop the service if it's running
systemctl stop radio 2>/dev/null || true

# Copy service file
cp systemd/radio.service /etc/systemd/system/

# Create initial config files if they don't exist
if [ ! -f "/home/radio/internetRadio/config/radio_state.json" ]; then
    echo '{"selected_stations": [], "current_stream": null}' > /home/radio/internetRadio/config/radio_state.json
    chown radio:radio /home/radio/internetRadio/config/radio_state.json
fi

# Set proper permissions for log directory
chown -R radio:radio /home/radio/internetRadio/logs
chmod 755 /home/radio/internetRadio/logs

# Reload systemd daemon
systemctl daemon-reload

# Enable and start the service
systemctl enable radio
systemctl start radio

echo "Installation complete! Service is running."
echo "Check status with: systemctl status radio"
echo "View logs with: journalctl -u radio -f"
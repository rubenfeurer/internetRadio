#!/bin/bash

# Set up error handling
set -e

# Create logs directory if it doesn't exist
mkdir -p /home/radio/internetRadio/logs

echo "Setting up audio..."
# Try to restore ALSA settings first
sudo alsactl restore || echo "Warning: Could not restore ALSA settings"
sleep 1  # Give audio system time to initialize

# Try to unmute and set volume
sudo amixer sset 'Master' unmute || echo "Warning: Could not unmute Master"
sudo amixer sset 'Master' 100% || echo "Warning: Could not set Master volume"

# Verify audio setup
if ! amixer sget 'Master' >/dev/null 2>&1; then
    echo "Warning: Audio system not responding, trying force-reload..."
    sudo alsa force-reload
    sleep 2
fi

echo "Checking Python environment..."
which python3
python3 --version

echo "Starting Python application..."
cd /home/radio/internetRadio

# Use exec to replace shell with Python process
exec python3 main.py >> /home/radio/internetRadio/logs/app.log 2>&1

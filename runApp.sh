#!/bin/bash

# Set up error handling
set -e

# Kill any existing Python processes
echo "Cleaning up existing processes..."
pkill -f "python3 main.py" || true
sleep 1

# Create logs directory if it doesn't exist
mkdir -p /home/radio/internetRadio/logs

echo "Setting up audio..."
# Try to restore ALSA settings first
sudo alsactl restore 2>/dev/null || echo "Warning: Could not restore ALSA settings"
sleep 1

# Try to unmute and set volume (redirect ALSA errors)
sudo amixer -q sset 'Master' unmute 2>/dev/null || true
sudo amixer -q sset 'Master' 100% 2>/dev/null || true

echo "Checking Python environment..."
which python3
python3 --version

echo "Starting Python application..."
cd /home/radio/internetRadio

# Wait for NetworkManager to be fully started
timeout=30
while [ $timeout -gt 0 ]; do
    if systemctl is-active --quiet NetworkManager; then
        break
    fi
    sleep 1
    ((timeout--))
done

if [ $timeout -eq 0 ]; then
    echo "Error: NetworkManager failed to start"
    exit 1
fi

# Start the application with error filtering and proper output handling
exec python3 main.py 2> >(grep -v \
    -e "snd_use_case_mgr_open" \
    -e "Could not unmute Master" \
    -e "Unable to find simple control" \
    -e "Could not set Master volume" \
    -e "Warning: Could not" \
    -e "amixer: Unable to find" \
    -e "failed to import hw:" \
    -e "alsa-lib" \
    >&2) >> /home/radio/internetRadio/logs/app.log &

# Store the PID
echo $! > /home/radio/internetRadio/app.pid

# Wait for the application to start
sleep 2

# Check if process is running
if ps -p $(cat /home/radio/internetRadio/app.pid) > /dev/null; then
    echo "Application started successfully"
    tail -f /home/radio/internetRadio/logs/app.log
else
    echo "Failed to start application"
    exit 1
fi

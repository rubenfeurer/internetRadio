#!/bin/bash

# Set display for GUI applications
export DISPLAY=:0
export XAUTHORITY=/home/radio/.Xauthority
export HOME=/home/radio

# Create logs directory
mkdir -p /home/radio/internetRadio/scripts/logs

# Function to check if X server is ready
wait_for_x() {
    for i in {1..30}; do
        if xset q &>/dev/null; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# Wait for X server
wait_for_x

# Start the application
cd /home/radio/internetRadio
. /home/radio/internetRadio/.venv/bin/activate
sudo pigpiod
lxterminal -e python /home/radio/internetRadio/main.py
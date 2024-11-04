#!/bin/bash

# Set up logging
exec 1> >(logger -s -t $(basename $0)) 2>&1

# Set display for GUI applications
export DISPLAY=:0
export XAUTHORITY=/home/radio/.Xauthority
export HOME=/home/radio

# Set up audio environment
export XDG_RUNTIME_DIR=/run/user/$(id -u radio)
export PULSE_RUNTIME_PATH=$XDG_RUNTIME_DIR/pulse

# Create logs directory if it doesn't exist
mkdir -p /home/radio/internetRadio/scripts/logs

# Set audio volume
amixer -D pulse sset Master 100% unmute || true

# Start the application
cd /home/radio/internetRadio
source /home/radio/internetRadio/.venv/bin/activate

# Ensure pigpiod is running
/usr/bin/sudo /usr/bin/pigpiod || true

# Start the Python application
/home/radio/internetRadio/.venv/bin/python /home/radio/internetRadio/main.py

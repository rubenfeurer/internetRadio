#!/bin/bash

# Set up logging
exec 1> >(logger -s -t $(basename $0)) 2>&1

# Set display for GUI applications
export DISPLAY=:0
export XAUTHORITY=/home/radio/.Xauthority
export HOME=/home/radio

# Set up audio environment
export XDG_RUNTIME_DIR=/run/user/$(id -u radio)
mkdir -p $XDG_RUNTIME_DIR
chmod 700 $XDG_RUNTIME_DIR
chown radio:radio $XDG_RUNTIME_DIR

# Create logs directory if it doesn't exist
mkdir -p /home/radio/internetRadio/scripts/logs

# Set audio
export PULSE_SERVER=unix:/run/user/$(id -u radio)/pulse/native
/usr/bin/amixer -D pulse sset Master 100% unmute || true

# Start the application
cd /home/radio/internetRadio
source /home/radio/internetRadio/.venv/bin/activate
/usr/bin/sudo /usr/bin/pigpiod

# Start the Python application
/home/radio/internetRadio/.venv/bin/python /home/radio/internetRadio/main.py

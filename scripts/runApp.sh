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

# Create logs directory
mkdir -p /home/radio/internetRadio/scripts/logs

# Kill any existing PulseAudio processes and start fresh
pulseaudio -k || true
sleep 2
pulseaudio --start

# Set audio
/usr/bin/amixer -c 0 sset 'Headphone' 100% unmute || true
/usr/bin/amixer -c 0 sset 'Speaker' 100% unmute || true

# Start the application
cd /home/radio/internetRadio
source /home/radio/internetRadio/.venv/bin/activate
/usr/bin/sudo /usr/bin/pigpiod

# Start the Python application
/home/radio/internetRadio/.venv/bin/python /home/radio/internetRadio/main.py
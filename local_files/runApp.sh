#!/bin/bash

# Set display for GUI applications
export DISPLAY=:0
export XAUTHORITY=/home/radio/.Xauthority
export HOME=/home/radio

# Set up audio environment
export XDG_RUNTIME_DIR=/run/user/$(id -u radio)
amixer sset 'Master' 100% unmute
amixer sset 'PCM' 100% unmute

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

# Start pulseaudio if not running
pulseaudio --start

# Start the application
cd /home/radio/internetRadio
. /home/radio/internetRadio/.venv/bin/activate
sudo pigpiod
lxterminal -e python /home/radio/internetRadio/main.py 
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

# Change to application directory
cd /home/radio/internetRadio

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Wait for pigpiod to be ready
echo "Waiting for pigpiod..."
max_attempts=10
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if pgrep pigpiod > /dev/null; then
        echo "pigpiod is running"
        sleep 2  # Give it a moment to fully initialize
        break
    fi
    echo "Waiting for pigpiod (attempt $((attempt + 1))/$max_attempts)..."
    attempt=$((attempt + 1))
    sleep 1
done

# Start the Python application with error handling
echo "Starting Python application..."
python main.py 2>&1 | tee -a /home/radio/internetRadio/scripts/logs/app.log
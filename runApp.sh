#!/bin/bash

# Set up error handling
set -e

# Create logs directory if it doesn't exist
mkdir -p /home/radio/internetRadio/logs

echo "Setting up audio..."
amixer sset 'Master' 100% || echo "Warning: Could not set audio volume"

echo "Checking Python environment..."
which python3
python3 --version

echo "Waiting for pigpiod..."
# Start pigpiod if not running
if ! pgrep pigpiod > /dev/null; then
    echo "Starting pigpiod..."
    sudo pigpiod
    sleep 2  # Give it time to start
fi

# Check if pigpiod is running
ATTEMPTS=0
MAX_ATTEMPTS=10
while ! pgrep pigpiod > /dev/null && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    echo "Waiting for pigpiod (attempt $((ATTEMPTS+1))/$MAX_ATTEMPTS)..."
    sleep 1
    ATTEMPTS=$((ATTEMPTS+1))
done

if ! pgrep pigpiod > /dev/null; then
    echo "Error: pigpiod failed to start"
    exit 1
fi

echo "pigpiod is running"

echo "Starting Python application..."
cd /home/radio/internetRadio
python3 main.py 2>&1 | tee -a /home/radio/internetRadio/logs/app.log

#!/bin/bash

# Add debug output
set -x

# Wait for system to fully boot
sleep 5

# Start pigpiod daemon if not running
if ! pgrep pigpiod > /dev/null; then
    sudo pigpiod
fi

# Change to the correct directory
cd /home/radio/internetRadio

# Activate virtual environment
source .venv/bin/activate

# Run the main application with proper Python path
python main.py 2>&1 | tee /home/radio/internetRadio/scripts/logs/app.log

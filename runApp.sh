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

echo "Starting Python application..."
cd /home/radio/internetRadio

# Use exec to replace shell with Python process
exec python3 main.py >> /home/radio/internetRadio/logs/app.log 2>&1

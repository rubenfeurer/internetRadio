#!/bin/bash

cd /home/radio/internetRadio

# Fetch updates from the remote repository
FETCH_OUTPUT=$(git fetch origin develop 2>&1)

# Resets branch to match remote branch
RESET_OUTPUT=$(git reset --hard origin/develop 2>&1)

# Log both fetch and pull outputs with timestamps
echo "$(date '+%Y-%m-%d %H:%M:%S'): Fetch Output: $FETCH_OUTPUT" >> /home/radio/internetRadio/scripts/logs/update_repo.log
echo "$(date '+%Y-%m-%d %H:%M:%S'): Pull Output: $RESET_OUTPUT" >> /home/radio/internetRadio/scripts/logs/update_repo.log

sleep 3

chmod +x main.py
chmod +x stream_manager.py
chmod +x app.py
chmod +x sounds.py
chmod +x update_repo.sh
chmod +x scripts/install_dependencies.sh
chmod +x scripts/runApp.sh
chmod +x scripts/check_radio.sh
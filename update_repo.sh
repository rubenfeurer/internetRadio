#!/bin/bash

# cd /home/radio/internetRadio
# git pull origin main

# git fetch origin
# git reset --hard origin/main  # Replace 'main' with your branch name

# GIT_OUTPUT=$(git pull origin develop 2>&1)
# echo "$(date '+%Y-%m-%d %H:%M:%S'): $GIT_OUTPUT" >> /home/radio/internetRadio/update_repo.log

cd /home/radio/internetRadio

# Fetch updates from the remote repository
FETCH_OUTPUT=$(git fetch origin develop 2>&1)

# Resets branch to match remote branch
RESET_OUTPUT=$(git reset --hard origin/develop 2>&1)

# Log both fetch and pull outputs with timestamps
echo "$(date '+%Y-%m-%d %H:%M:%S'): Fetch Output: $FETCH_OUTPUT" >> /home/radio/internetRadio/update_repo.log
echo "$(date '+%Y-%m-%d %H:%M:%S'): Pull Output: $RESET_OUTPUT" >> /home/radio/internetRadio/update_repo.log

sleep 5

chmod +x main.py
chmod +x stream_manager.py
chmod +x app.py
chmod +x sounds.py
chmod +x update_repo.sh
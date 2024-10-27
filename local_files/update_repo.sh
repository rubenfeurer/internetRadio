#!/bin/bash

# cd /home/radio/internetRadio
# git pull origin main

# git fetch origin
# git reset --hard origin/main  # Replace 'main' with your branch name

cd /home/radio/internetRadio

GIT_OUTPUT=$(git pull 2>&1)
echo "$(date '+%Y-%m-%d %H:%M:%S'): $GIT_OUTPUT" >> /home/radio/internetRadio/update_repo.log

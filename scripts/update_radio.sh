#!/bin/bash

# Set up logging
LOG_FILE="/home/radio/internetRadio/scripts/logs/update_radio.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

cd /home/radio/internetRadio

# Fix ownership before fetch
sudo chown -R radio:radio .
sudo chmod -R 755 .

# Fetch updates from the remote repository
log_message "Fetching updates..."
FETCH_OUTPUT=$(git fetch origin develop 2>&1)
log_message "Fetch Output: $FETCH_OUTPUT"

# Reset branch to match remote
log_message "Resetting to origin/develop..."
RESET_OUTPUT=$(git reset --hard origin/develop 2>&1)
log_message "Reset Output: $RESET_OUTPUT"

# Fix permissions after reset
log_message "Updating file permissions..."

# Main directory files
sudo chown -R radio:radio /home/radio/internetRadio
sudo chmod 755 /home/radio/internetRadio

# Define file permissions
declare -A FILE_PERMISSIONS=(
    ["main.py"]=755
    ["stream_manager.py"]=755
    ["app.py"]=755
    ["sounds.py"]=755
    ["config.toml"]=644
    ["scripts/update_radio.sh"]=755
    ["scripts/install_radio.sh"]=755
    ["scripts/runApp.sh"]=755
    ["scripts/check_radio.sh"]=755
)

# Define directory permissions
declare -A DIR_PERMISSIONS=(
    ["scripts"]=755
    ["scripts/logs"]=755
    ["templates"]=755
    ["templates/static"]=755
    ["templates/static/css"]=755
    [".venv"]=755
    ["sounds"]=755
)

# Apply directory permissions
for dir in "${!DIR_PERMISSIONS[@]}"; do
    if [ -d "$dir" ]; then
        sudo chmod "${DIR_PERMISSIONS[$dir]}" "$dir"
        log_message "Set permissions ${DIR_PERMISSIONS[$dir]} for directory: $dir"
    else
        log_message "Warning: Directory not found: $dir"
    fi
done

# Apply file permissions
for file in "${!FILE_PERMISSIONS[@]}"; do
    if [ -f "$file" ]; then
        sudo chmod "${FILE_PERMISSIONS[$file]}" "$file"
        log_message "Set permissions ${FILE_PERMISSIONS[$file]} for file: $file"
    else
        log_message "Warning: File not found: $file"
    fi
done

# Set ownership for all files and directories
sudo chown -R radio:radio /home/radio/internetRadio
log_message "Set ownership radio:radio for all files and directories"

# Ensure logs directory exists and has correct permissions
sudo mkdir -p scripts
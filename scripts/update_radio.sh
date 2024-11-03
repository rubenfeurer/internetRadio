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

# Make Python files executable
FILES_TO_MAKE_EXECUTABLE=(
    "main.py"
    "stream_manager.py"
    "app.py"
    "sounds.py"
    "scripts/update_radio.sh"
    "scripts/install_radio.sh"
    "scripts/runApp.sh"
    "scripts/check_radio.sh"
)

for file in "${FILES_TO_MAKE_EXECUTABLE[@]}"; do
    if [ -f "$file" ]; then
        sudo chmod +x "$file"
        log_message "Made executable: $file"
    else
        log_message "Warning: File not found: $file"
    fi
done

# Set proper permissions for directories
sudo find . -type d -exec chmod 755 {} \;
sudo find . -type f -exec chmod 644 {} \;

# Re-apply executable permissions after the blanket file permission set
for file in "${FILES_TO_MAKE_EXECUTABLE[@]}"; do
    if [ -f "$file" ]; then
        sudo chmod +x "$file"
    fi
done

# Ensure logs directory exists and has correct permissions
sudo mkdir -p scripts/logs
sudo chown -R radio:radio scripts/logs
sudo chmod 755 scripts/logs

log_message "Permission update completed"
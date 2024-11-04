#!/bin/bash

# Set up logging with immediate console output
LOG_FILE="/home/radio/internetRadio/scripts/logs/update_radio.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1"
    echo "[$timestamp] $1" >> "$LOG_FILE"
}

# Add initial message
echo "Starting radio update..."
log_message "Starting update process..."

# Function for both manual and service updates
perform_update() {
    cd /home/radio/internetRadio || {
        log_message "❌ ERROR: Failed to change to /home/radio/internetRadio"
        return 1
    }
    log_message "📂 Changed to directory: $(pwd)"

    # Fetch updates with verbose output
    echo "📡 Fetching updates..."
    if ! git fetch origin develop; then
        log_message "❌ ERROR: Git fetch failed"
        return 1
    fi
    log_message "✓ Fetch completed"

    # Reset branch with verbose output
    echo "🔄 Resetting to latest version..."
    if ! git reset --hard origin/develop; then
        log_message "❌ ERROR: Git reset failed"
        return 1
    fi
    log_message "✓ Reset completed"

    # Fix permissions
    echo "🔒 Updating permissions..."
    fix_permissions

    echo -e "\n✅ Update completed successfully!"
    return 0
}

# Run update
if perform_update; then
    log_message "Update completed successfully!"
else
    echo -e "\n❌ Update failed! Check the log for details: $LOG_FILE"
    exit 1
fi
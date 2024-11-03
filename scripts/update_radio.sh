#!/bin/bash

# Set up logging
LOG_FILE="/home/radio/internetRadio/scripts/logs/update_radio.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Function to fix permissions after update
fix_permissions() {
    log_message "Fixing script permissions..."
    
    # Make all scripts executable
    SCRIPTS=(
        "scripts/runApp.sh"
        "scripts/update_radio.sh"
        "scripts/check_radio.sh"
        "scripts/uninstall_radio.sh"
        "scripts/install_radio.sh"
    )
    
    for script in "${SCRIPTS[@]}"; do
        if [ -f "$script" ]; then
            log_message "Making $script executable..."
            sudo chmod +x "$script"
            sudo chown radio:radio "$script"
        fi
    done
}

# Function for both manual and service updates
perform_update() {
    cd /home/radio/internetRadio || {
        log_message "ERROR: Failed to change to /home/radio/internetRadio"
        return 1
    }

    # Fix ownership before fetch
    sudo chown -R radio:radio .
    sudo chmod -R 755 .

    # Fetch updates
    log_message "Fetching updates..."
    if ! FETCH_OUTPUT=$(git fetch origin develop 2>&1); then
        log_message "ERROR: Git fetch failed: $FETCH_OUTPUT"
        return 1
    fi
    log_message "Fetch Output: $FETCH_OUTPUT"

    # Reset branch
    log_message "Resetting to origin/develop..."
    if ! RESET_OUTPUT=$(git reset --hard origin/develop 2>&1); then
        log_message "ERROR: Git reset failed: $RESET_OUTPUT"
        return 1
    fi
    log_message "Reset Output: $RESET_OUTPUT"

    # Fix permissions after update
    fix_permissions

    return 0
}

# Check if running interactively
if [ -t 1 ]; then
    # Interactive mode
    echo "Starting radio update..."
    echo "This may take a few moments..."
    echo

    if perform_update; then
        echo -e "\n✓ Update completed successfully!"
        echo "All scripts are now executable"
    else
        echo -e "\n❌ Update failed!"
        echo "Check the log for details: $LOG_FILE"
        exit 1
    fi
else
    # Service mode
    perform_update
fi
#!/bin/bash

# Set up logging
LOG_FILE="/home/radio/internetRadio/scripts/logs/update_radio.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

# Function to handle manual update with feedback
manual_update() {
    echo "Starting radio update..."
    echo "This may take a few moments..."
    echo

    cd /home/radio/internetRadio

    # Fix ownership before fetch
    sudo chown -R radio:radio .
    sudo chmod -R 755 .

    # Fetch updates from the remote repository
    echo -n "Updating"
    log_message "Fetching updates..."
    FETCH_OUTPUT=$(git fetch origin develop 2>&1)
    log_message "Fetch Output: $FETCH_OUTPUT"

    # Reset branch to match remote
    log_message "Resetting to origin/develop..."
    RESET_OUTPUT=$(git reset --hard origin/develop 2>&1)
    log_message "Reset Output: $RESET_OUTPUT"

    # Update permissions
    log_message "Updating file permissions..."
    
    # ... (existing permission update code) ...

    # Check for errors in the log
    if grep -q "ERROR:" "$LOG_FILE"; then
        echo -e "\n\n⚠️ Update completed with warnings"
        echo -e "\nWould you like to view the log? (y/N): "
        read -r view_log
        if [[ $view_log =~ ^[Yy]$ ]]; then
            echo -e "\nRecent log entries:"
            tail -n 20 "$LOG_FILE"
        fi
    else
        echo -e "\n\n✅ Update completed successfully!"
    fi

    echo -e "\nUpdate log location: $LOG_FILE"
}

# Function for service update (without interactive elements)
service_update() {
    cd /home/radio/internetRadio

    # ... (existing update code) ...

    log_message "Update completed"
}

# Check if script is being run manually or by the service
if [ -t 1 ]; then
    # Terminal attached - running manually
    manual_update
else
    # No terminal - running as service
    service_update
fi
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
    
    # List of scripts to fix
    SCRIPTS=(
        "runApp.sh"
        "update_radio.sh"
        "check_radio.sh"
        "uninstall_radio.sh"
        "install_radio.sh"
        "detect_audio.sh"
    )
    
    # Fix each script explicitly
    for script in "${SCRIPTS[@]}"; do
        SCRIPT_PATH="/home/radio/internetRadio/scripts/$script"
        if [ -f "$SCRIPT_PATH" ]; then
            log_message "Setting permissions for $script"
            sudo chmod 755 "$SCRIPT_PATH"
            sudo chown radio:radio "$SCRIPT_PATH"
        else
            log_message "WARNING: $script not found"
        fi
    done

    # Fix detect_audio.sh in system location
    if [ -f "/usr/local/bin/detect_audio.sh" ]; then
        log_message "Setting permissions for system detect_audio.sh"
        sudo chmod 755 "/usr/local/bin/detect_audio.sh"
        sudo chown radio:radio "/usr/local/bin/detect_audio.sh"
    fi
    
    # Fix audio-related directories and files
    log_message "Fixing audio-related permissions..."
    
    # PulseAudio directory
    sudo mkdir -p /home/radio/.config/pulse
    sudo chown -R radio:radio /home/radio/.config/pulse
    sudo chmod -R 755 /home/radio/.config/pulse
    
    # Runtime directory
    sudo mkdir -p /run/user/1000
    sudo chown radio:radio /run/user/1000
    sudo chmod 700 /run/user/1000
    
    # Main application directory
    sudo chown -R radio:radio /home/radio/internetRadio
    sudo chmod -R 755 /home/radio/internetRadio
    
    # Verify all permissions
    log_message "Final permission check:"
    ls -la /home/radio/internetRadio/scripts/*.sh
    ls -la /home/radio/internetRadio/audio-related
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

    # Fix permissions explicitly after update
    fix_permissions
    
    # Verify one last time
    if [ ! -x "/home/radio/internetRadio/scripts/install_radio.sh" ]; then
        log_message "CRITICAL: install_radio.sh is still not executable"
        sudo chmod +x /home/radio/internetRadio/scripts/install_radio.sh
    fi

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
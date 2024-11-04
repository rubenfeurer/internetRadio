#!/bin/bash

# Set up logging with immediate console output
LOG_FILE="/home/radio/internetRadio/scripts/logs/update_radio.log"
mkdir -p "$(dirname "$LOG_FILE")"

log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] $1"
    echo "[$timestamp] $1" >> "$LOG_FILE"
}

# Function to fix permissions
fix_permissions() {
    log_message "🔒 Fixing script permissions..."
    
    # List of scripts to fix
    SCRIPTS=(
        "runApp.sh"
        "update_radio.sh"
        "check_radio.sh"
        "uninstall_radio.sh"
        "install_radio.sh"
        "detect_audio.sh"
        "monitor_radio.sh"
        "hardware_test.sh"
    )
    
    # Fix each script explicitly
    for script in "${SCRIPTS[@]}"; do
        SCRIPT_PATH="/home/radio/internetRadio/scripts/$script"
        if [ -f "$SCRIPT_PATH" ]; then
            log_message "   Setting permissions for $script"
            chmod 755 "$SCRIPT_PATH"
            chown radio:radio "$SCRIPT_PATH"
        fi
    done

    # Fix audio-related permissions
    log_message "🔊 Fixing audio-related permissions..."
    chmod -R 755 /home/radio/internetRadio/sounds
    chown -R radio:radio /home/radio/internetRadio/sounds
}

# Function for both manual and service updates
perform_update() {
    cd /home/radio/internetRadio || {
        log_message "❌ ERROR: Failed to change to /home/radio/internetRadio"
        return 1
    }
    log_message "📂 Changed to directory: $(pwd)"

    # Fetch updates
    log_message "📡 Fetching updates..."
    if ! git fetch origin develop; then
        log_message "❌ ERROR: Git fetch failed"
        return 1
    fi
    log_message "✓ Fetch successful"

    # Reset to latest version
    log_message "🔄 Resetting to latest version..."
    if ! git reset --hard origin/develop; then
        log_message "❌ ERROR: Git reset failed"
        return 1
    fi
    log_message "✓ Reset successful"

    # Fix permissions
    fix_permissions

    log_message "✅ Update completed successfully!"
    return 0
}

# Main execution
echo -e "\n📻 Starting radio update..."
if perform_update; then
    echo -e "\n✅ Update completed successfully!"
else
    echo -e "\n❌ Update failed! Check the log for details: $LOG_FILE"
    exit 1
fi
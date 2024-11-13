#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo_step() {
    echo -e "${GREEN}==>${NC} $1"
}

PROJECT_DIR="/home/radio/internetRadio"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

echo_step "Cleaning up logs..."

# Backup existing logs
echo_step "Backing up logs..."
mkdir -p "$PROJECT_DIR/logs/backup"
cp "$PROJECT_DIR/logs"/*.log "$PROJECT_DIR/logs/backup/"

# Clear current logs
echo_step "Clearing current logs..."
truncate -s 0 "$PROJECT_DIR/logs/app.log"
truncate -s 0 "$PROJECT_DIR/logs/radio.log"
truncate -s 0 "$PROJECT_DIR/logs/wifi.log"

# Set up log rotation
echo_step "Setting up log rotation..."
cat > /etc/logrotate.d/internetradio << EOL
/home/radio/internetRadio/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 radio radio
    size 100M
}
EOL

# Fix permissions
echo_step "Fixing permissions..."
chown -R radio:radio "$PROJECT_DIR/logs"
chmod 755 "$PROJECT_DIR/logs"
chmod 644 "$PROJECT_DIR/logs"/*.log

echo_step "Done."
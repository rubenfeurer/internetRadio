#!/bin/bash

# Set up error handling
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_step() {
    echo -e "${GREEN}==>${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

echo_step "Stopping service..."
systemctl stop internetradio || echo_warning "Service was not running"

echo_step "Disabling service..."
systemctl disable internetradio || echo_warning "Service was not enabled"

echo_step "Removing service file..."
rm -f /etc/systemd/system/internetradio.service
systemctl daemon-reload

echo_step "Service removed successfully"
echo_warning "Note: Project files and user 'radio' were not removed for safety."
echo "To completely remove everything, run:"
echo "sudo rm -rf /home/radio/internetRadio"
echo "sudo userdel -r radio" 
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

# Check if running as correct user
if [ "$(whoami)" != "radio" ]; then
    echo -e "${RED}Please run as radio user${NC}"
    exit 1
fi

PROJECT_DIR="/home/radio/internetRadio"

# Backup current configuration
echo_step "Backing up configuration..."
if [ -d "$PROJECT_DIR/config" ]; then
    cp -r "$PROJECT_DIR/config" "$PROJECT_DIR/config.bak"
fi
if [ -d "$PROJECT_DIR/streams" ]; then
    cp -r "$PROJECT_DIR/streams" "$PROJECT_DIR/streams.bak"
fi

echo_step "Updating from repository..."
cd "$PROJECT_DIR"
git pull

echo_step "Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Restore configuration if needed
if [ -d "$PROJECT_DIR/config.bak" ]; then
    cp -r "$PROJECT_DIR/config.bak"/* "$PROJECT_DIR/config/"
    rm -rf "$PROJECT_DIR/config.bak"
fi
if [ -d "$PROJECT_DIR/streams.bak" ]; then
    cp -r "$PROJECT_DIR/streams.bak"/* "$PROJECT_DIR/streams/"
    rm -rf "$PROJECT_DIR/streams.bak"
fi

echo_step "Restarting service..."
sudo systemctl restart internetradio

if systemctl is-active --quiet internetradio; then
    echo -e "${GREEN}Service updated and running successfully${NC}"
else
    echo -e "${RED}Service failed to start after update${NC}"
    echo "Check logs with: journalctl -u internetradio"
    exit 1
fi 
#!/bin/bash

# Set up logging
exec 1> >(logger -s -t $(basename $0)) 2>&1

# Configuration
REPO_URL="https://github.com/rubenfeurer/internetRadio.git"
RADIO_DIR="/home/radio/internetRadio"
BRANCH="#92-apmode"

# Ensure we're in the correct directory
cd $RADIO_DIR || exit 1

# Backup current config
cp config.toml config.toml.bak

# Pull latest changes
git fetch origin $BRANCH
git reset --hard FETCH_HEAD

# Restore config
mv config.toml.bak config.toml

# Fix permissions after update
chown -R radio:radio $RADIO_DIR
chmod -R 755 $RADIO_DIR/scripts/*.sh

# Remove any duplicate logs directory if it exists
rm -rf "$RADIO_DIR/scripts/logs"

# Restart service
systemctl restart internetradio

echo "✓ Update completed successfully!"

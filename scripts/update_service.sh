#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo_step() {
    echo -e "${GREEN}==>${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

echo_step "Updating service configuration..."

# Update service file with increased timeout and proper environment
cat > /etc/systemd/system/internetradio.service << EOL
[Unit]
Description=Internet Radio Service
After=network.target sound.target
Wants=sound.target

[Service]
Type=simple
User=radio
WorkingDirectory=/home/radio/internetRadio
Environment=XDG_RUNTIME_DIR=/run/user/1000
ExecStartPre=/bin/mkdir -p /run/user/1000
ExecStartPre=/bin/chown radio:radio /run/user/1000
ExecStartPre=/bin/chmod 700 /run/user/1000
ExecStart=/home/radio/internetRadio/runApp.sh
Restart=always
RestartSec=5
TimeoutStopSec=20
KillMode=mixed

StandardOutput=append:/home/radio/internetRadio/logs/radio.log
StandardError=append:/home/radio/internetRadio/logs/radio.log

[Install]
WantedBy=multi-user.target
EOL

echo_step "Reloading systemd..."
systemctl daemon-reload

echo_step "Restarting service..."
systemctl restart internetradio

echo_step "Service status:"
systemctl status internetradio --no-pager 
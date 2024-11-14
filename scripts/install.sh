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

echo_error() {
    echo -e "${RED}Error:${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo_error "Please run as root"
    exit 1
fi

# Check Raspberry Pi model
if ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo_error "This script must be run on a Raspberry Pi"
    exit 1
fi

echo_step "Installing system dependencies..."
apt-get update
apt-get install -y python3-pip python3-venv alsa-utils hostapd dnsmasq vlc xterm

# Verify radio user exists
if ! id "radio" &>/dev/null; then
    echo_step "Creating radio user..."
    useradd -m -s /bin/bash radio
    usermod -a -G audio,gpio,video radio
fi

PROJECT_DIR="/home/radio/internetRadio"

echo_step "Setting up Python virtual environment..."
su - radio -c "cd $PROJECT_DIR && python3 -m venv venv"
su - radio -c "cd $PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt"

echo_step "Setting up service..."
cat > /etc/systemd/system/internetradio.service << EOL
[Unit]
Description=Internet Radio Service
After=network.target sound.target
Wants=sound.target

[Service]
Type=simple
User=radio
Group=radio
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/radio/.Xauthority
Environment=HOME=/home/radio
Environment=XDG_RUNTIME_DIR=/run/user/1000
WorkingDirectory=/home/radio/internetRadio

# Setup runtime directory
ExecStartPre=/bin/mkdir -p /run/user/1000
ExecStartPre=/bin/chown radio:radio /run/user/1000
ExecStartPre=/bin/chmod 700 /run/user/1000
ExecStart=/home/radio/internetRadio/runApp.sh

# Add restart controls
Restart=always
RestartSec=5
TimeoutStopSec=20
KillMode=mixed

# Add logging
StandardOutput=append:/home/radio/internetRadio/logs/radio.log
StandardError=append:/home/radio/internetRadio/logs/radio.log

[Install]
WantedBy=multi-user.target
EOL

echo_step "Setting up directories and permissions..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/config"
mkdir -p "$PROJECT_DIR/streams"
mkdir -p "$PROJECT_DIR/sounds"
touch "$PROJECT_DIR/logs/radio.log"
touch "$PROJECT_DIR/logs/app.log"
chown -R radio:radio "$PROJECT_DIR"
chmod 755 "$PROJECT_DIR"
chmod +x "$PROJECT_DIR/scripts/runApp.sh"

echo_step "Configuring DNS settings..."
rm -f /etc/resolv.conf
echo "nameserver 8.8.8.8" | tee /etc/resolv.conf
echo "nameserver 8.8.4.4" | tee -a /etc/resolv.conf
chmod 644 /etc/resolv.conf
chattr +i /etc/resolv.conf

# Configure systemd-networkd to not override DNS
mkdir -p /etc/systemd/network/
cat > /etc/systemd/network/25-wireless.network << EOL
[Match]
Name=wlan0

[Network]
DHCP=yes
DNSDefaultRoute=no

[DHCP]
UseDNS=no
EOL

echo_step "Setting up log rotation..."

# Create logrotate configuration
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
    postrotate
        systemctl reload internetradio >/dev/null 2>&1 || true
    endscript
}
EOL

# Create log directory if it doesn't exist
mkdir -p /home/radio/internetRadio/logs

# Set correct permissions
chown -R radio:radio /home/radio/internetRadio/logs
chmod 755 /home/radio/internetRadio/logs
chmod 644 /home/radio/internetRadio/logs/*.log 2>/dev/null || true

# Force initial log rotation if needed
if [ -f /home/radio/internetRadio/logs/app.log ] && [ $(stat -f%z /home/radio/internetRadio/logs/app.log 2>/dev/null || stat -c%s /home/radio/internetRadio/logs/app.log) -gt 104857600 ]; then
    echo_step "Rotating large log files..."
    logrotate -f /etc/logrotate.d/internetradio
fi

echo_step "Configuring ALSA..."
cat > /etc/asound.conf << EOL
defaults.pcm.card 2
defaults.pcm.device 0
defaults.ctl.card 2
EOL

echo_step "Testing audio configuration..."
su - radio -c "amixer -c 2 sset 'PCM' unmute"
su - radio -c "amixer -c 2 sset 'PCM' 100%"

echo_step "Enabling and starting services..."
systemctl daemon-reload
systemctl restart systemd-networkd
systemctl restart wpa_supplicant
systemctl enable internetradio
systemctl restart internetradio

echo_step "Setting up system monitor service..."
cat > /etc/systemd/system/radiomonitor.service << EOL
[Unit]
Description=Internet Radio System Monitor
After=internetradio.service
Wants=internetradio.service

[Service]
Type=simple
User=radio
Group=radio
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/radio/.Xauthority
WorkingDirectory=/home/radio/internetRadio
ExecStart=/usr/bin/xterm -T "System Monitor" -geometry 80x24+0+0 -e /usr/bin/python3 -c "from src.utils.system_monitor import SystemMonitor; SystemMonitor().run()"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

systemctl enable radiomonitor
systemctl restart radiomonitor

echo_step "Checking service status..."
systemctl status internetradio --no-pager

if systemctl is-active --quiet internetradio; then
    echo -e "${GREEN}Service is running successfully${NC}"
else
    echo_error "Service failed to start. Check logs with: journalctl -u internetradio"
fi
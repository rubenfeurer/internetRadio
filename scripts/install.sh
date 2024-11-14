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
apt-get install -y python3-pip python3-venv alsa-utils hostapd dnsmasq vlc xterm network-manager

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
cp services/internetradio.service /etc/systemd/system/
chmod 644 /etc/systemd/system/internetradio.service

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
echo "nameserver 1.1.1.1" | tee -a /etc/resolv.conf
chmod 644 /etc/resolv.conf
chattr +i /etc/resolv.conf

# Add DNS test after configuration
echo_step "Testing DNS configuration..."
if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}DNS configuration successful${NC}"
else
    echo_warning "DNS configuration might have issues. Check network connectivity."
fi

# Configure systemd-networkd to not override DNS
mkdir -p /etc/systemd/network/
cp services/network.conf /etc/systemd/network/25-wireless.network
chmod 644 /etc/systemd/network/25-wireless.network

echo_step "Setting up log rotation..."
cp services/logrotate.conf /etc/logrotate.d/internetradio
chmod 644 /etc/logrotate.d/internetradio

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
cp services/radiomonitor.service /etc/systemd/system/
chmod 644 /etc/systemd/system/radiomonitor.service

echo_step "Checking service status..."
systemctl status internetradio --no-pager

if systemctl is-active --quiet internetradio; then
    echo -e "${GREEN}Service is running successfully${NC}"
else
    echo_error "Service failed to start. Check logs with: journalctl -u internetradio"
fi

echo_step "Setting up git hooks..."
HOOK_DIR="$PROJECT_DIR/.git/hooks"
mkdir -p "$HOOK_DIR"
cp scripts/git-hooks/pre-commit "$HOOK_DIR/pre-commit"
chmod +x "$HOOK_DIR/pre-commit"

# Ensure NetworkManager is running and enabled
echo_step "Configuring NetworkManager..."
systemctl enable NetworkManager
systemctl start NetworkManager

# Add radio user to netdev group for NetworkManager access
usermod -a -G netdev radio

# Create default config file if not exists
if [ ! -f "$PROJECT_DIR/config/config.toml" ]; then
    echo_step "Creating default config..."
    cat > "$PROJECT_DIR/config/config.toml" << EOL
[network]
saved_networks = []
ap_ssid = "InternetRadio"
ap_password = "password123"

[audio]
volume = 50
default_stream = ""
EOL
    chown radio:radio "$PROJECT_DIR/config/config.toml"
    chmod 644 "$PROJECT_DIR/config/config.toml"
fi

# Test audio device availability
if ! su - radio -c "aplay -l | grep -q 'card 2'"; then
    echo_warning "Audio card 2 not found. Check audio device configuration."
fi

# Add after DNS configuration
echo_step "Setting up log directories..."
LOG_DIRS=(
    "$PROJECT_DIR/logs/radio"
    "$PROJECT_DIR/logs/network"
    "$PROJECT_DIR/logs/system"
)

for dir in "${LOG_DIRS[@]}"; do
    mkdir -p "$dir"
    chown radio:radio "$dir"
    chmod 755 "$dir"
done

# Add after audio configuration
echo_step "Testing audio playback..."
if [ -f "$PROJECT_DIR/sounds/test.wav" ]; then
    su - radio -c "aplay -D plughw:2,0 $PROJECT_DIR/sounds/test.wav"
else
    echo_warning "Test sound file not found. Skipping audio test."
fi

# Add after NetworkManager installation
echo_step "Configuring NetworkManager..."
cat > /etc/NetworkManager/NetworkManager.conf << EOL
[main]
plugins=ifupdown,keyfile
dns=default
rc-manager=resolvconf

[ifupdown]
managed=true

[device]
wifi.scan-rand-mac-address=no

[connection]
wifi.powersave=0
EOL

# Set proper permissions
chmod 644 /etc/NetworkManager/NetworkManager.conf
chown root:root /etc/NetworkManager/NetworkManager.conf

# Ensure NetworkManager state directory exists with proper permissions
mkdir -p /var/lib/NetworkManager
chmod 755 /var/lib/NetworkManager
chown root:root /var/lib/NetworkManager

# Disable conflicting services
systemctl stop wpa_supplicant
systemctl disable wpa_supplicant
systemctl mask wpa_supplicant

# Enable and restart NetworkManager
systemctl enable NetworkManager
systemctl restart NetworkManager

# Add radio user to required groups
usermod -a -G netdev,network radio

# Wait for NetworkManager to be fully started
sleep 5

# Test NetworkManager status
if ! systemctl is-active --quiet NetworkManager; then
    echo_error "NetworkManager failed to start"
    exit 1
fi
#!/bin/bash

# Set up error handling
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_step() {
    echo -e "${GREEN}==>${NC} $1"
}

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

PROJECT_DIR="/home/radio/internetRadio"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo_error "Please run as root"
    exit 1
fi

# 1. Verify sound files and permissions
echo_step "Verifying sound files..."
SOUND_FILES=(
    "boot.wav"
    "click.wav"
    "error.wav"
    "noWifi.wav"
    "shutdown.wav"
    "wifi.wav"
)

for sound in "${SOUND_FILES[@]}"; do
    if [ -f "$PROJECT_DIR/sounds/$sound" ]; then
        if file "$PROJECT_DIR/sounds/$sound" | grep -q "WAVE audio"; then
            echo_info "$sound is valid"
        else
            echo_error "$sound is not a valid WAV file"
        fi
    else
        echo_error "Missing sound file: $sound"
    fi
done

# 2. Fix permissions
echo_step "Fixing permissions..."
chown -R radio:radio "$PROJECT_DIR"
chmod 755 "$PROJECT_DIR/sounds"
chmod 644 "$PROJECT_DIR/sounds"/*.wav
chmod 755 "$PROJECT_DIR/logs"
chmod 644 "$PROJECT_DIR/logs"/*.log

# 3. Fix log rotation
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
}
EOL

# 4. Clean up old logs
echo_step "Cleaning up old logs..."
find "$PROJECT_DIR/logs" -name "*.log" -size +100M -exec truncate -s 100M {} \;

# 5. Fix audio settings
echo_step "Configuring audio..."
amixer sset 'Master' 100%
alsactl store

# 6. Ensure services are running
echo_step "Checking services..."
systemctl restart pigpiod
systemctl restart internetradio

# 7. Clean up failed WiFi connections
echo_step "Cleaning up failed WiFi connections..."
nmcli connection show | grep -E "Salt_2GHz|visitor-" | awk '{print $1}' | while read -r conn; do
    nmcli connection delete "$conn" 2>/dev/null || true
    echo_info "Removed failed connection: $conn"
done

# 8. Fix thread cleanup timeout
echo_step "Updating service configuration..."
sed -i 's/TimeoutStopSec=10/TimeoutStopSec=20/' /etc/systemd/system/internetradio.service
systemctl daemon-reload

echo_step "All fixes applied. Running health check..."
"$PROJECT_DIR/scripts/health_check.sh"

echo -e "\nRecommended next steps:"
echo "1. Monitor logs for new errors: tail -f $PROJECT_DIR/logs/app.log"
echo "2. Test audio playback: aplay $PROJECT_DIR/sounds/boot.wav"
echo "3. Verify WiFi connectivity" 
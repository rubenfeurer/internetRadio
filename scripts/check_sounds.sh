#!/bin/bash

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
SOUNDS_DIR="$PROJECT_DIR/sounds"

echo_step "Checking sound files..."

# List all sound files and their details
echo_info "Sound files details:"
ls -l "$SOUNDS_DIR"

# Check each sound file
for sound in "$SOUNDS_DIR"/*.wav; do
    filename=$(basename "$sound")
    echo -e "\nChecking $filename:"
    
    # Check permissions
    perms=$(stat -c "%a" "$sound")
    owner=$(stat -c "%U:%G" "$sound")
    echo "Permissions: $perms"
    echo "Owner: $owner"
    
    # Check if it's a valid WAV file
    if file "$sound" | grep -q "WAVE audio"; then
        echo_info "Valid WAV file"
        # Show audio file details
        soxi "$sound" 2>/dev/null || echo_error "Could not read audio metadata"
    else
        echo_error "Not a valid WAV file"
    fi
    
    # Try to play the file
    echo "Testing playback..."
    if aplay "$sound" 2>/dev/null; then
        echo_info "Playback successful"
    else
        echo_error "Playback failed"
    fi
done

# Check audio system
echo -e "\nChecking audio system..."
echo "ALSA devices:"
aplay -l

echo -e "\nCurrent audio settings:"
amixer sget 'Master'

echo -e "\nChecking file access..."
sudo -u radio test -r "$SOUNDS_DIR/boot.wav" && echo_info "radio user can read boot.wav" || echo_error "radio user cannot read boot.wav"

# Suggest fixes if needed
echo -e "\nRecommended fixes:"
echo "1. Fix permissions: sudo chown -R radio:radio $SOUNDS_DIR && sudo chmod 644 $SOUNDS_DIR/*.wav"
echo "2. Test sound: sudo -u radio aplay $SOUNDS_DIR/boot.wav"
echo "3. Restart service: sudo systemctl restart internetradio" 
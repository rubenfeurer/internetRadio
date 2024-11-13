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
TEMP_DIR="/tmp/sound_fix"

# Create temporary directory
mkdir -p "$TEMP_DIR"

echo_step "Fixing WAV files..."

for sound in "$SOUNDS_DIR"/*.wav; do
    filename=$(basename "$sound")
    echo_info "Processing $filename..."
    
    # Create a new WAV file with correct headers
    if ffmpeg -i "$sound" -c:a pcm_s16le -ar 44100 "$TEMP_DIR/$filename" 2>/dev/null; then
        # Backup original
        cp "$sound" "$sound.bak"
        # Replace with fixed version
        cp "$TEMP_DIR/$filename" "$sound"
        echo_info "Fixed $filename"
    else
        echo_error "Failed to fix $filename"
    fi
done

# Clean up
rm -rf "$TEMP_DIR"

echo_step "Setting permissions..."
chown -R radio:radio "$SOUNDS_DIR"
chmod 644 "$SOUNDS_DIR"/*.wav

echo_step "Testing fixed files..."
for sound in "$SOUNDS_DIR"/*.wav; do
    filename=$(basename "$sound")
    if file "$sound" | grep -q "WAVE audio"; then
        echo_info "$filename is now a valid WAV file"
    else
        echo_error "$filename is still invalid"
    fi
done

echo_step "Restarting service..."
systemctl restart internetradio

echo_step "Done. Please check the logs for any remaining sound-related errors." 
#!/bin/bash

# Function to check if headphones are plugged in
check_headphones() {
    # Check headphone status using raspi-gpio
    if raspi-gpio get | grep -q "GPIO4: level=1"; then
        echo "Headphones"
        return 0
    fi
    return 1
}

# Function to check if HDMI is connected and audio capable
check_hdmi() {
    if tvservice -s | grep -q "HDMI"; then
        # Check if HDMI supports audio
        if vcgencmd get_property hdmi_audio | grep -q "=1"; then
            echo "HDMI"
            return 0
        fi
    fi
    return 1
}

# Detect primary audio output
if check_headphones; then
    echo "Headphones"
elif check_hdmi; then
    echo "HDMI"
else
    echo "Headphones" # Default fallback
fi 
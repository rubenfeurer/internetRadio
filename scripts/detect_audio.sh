#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if headphones are plugged in
check_headphones() {
    if command_exists "raspi-gpio"; then
        if raspi-gpio get | grep -q "GPIO4: level=1"; then
            echo "Headphones"
            return 0
        fi
    else
        echo "WARNING: raspi-gpio not found" >&2
    fi
    return 1
}

# Function to check if HDMI is connected and audio capable
check_hdmi() {
    if command_exists "tvservice" && command_exists "vcgencmd"; then
        if tvservice -s | grep -q "HDMI"; then
            if vcgencmd get_property hdmi_audio | grep -q "=1"; then
                echo "HDMI"
                return 0
            fi
        fi
    else
        echo "WARNING: tvservice or vcgencmd not found" >&2
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
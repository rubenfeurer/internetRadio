#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'    # No Color
BOLD='\033[1m'

# Function to get WiFi signal strength
get_wifi_strength() {
    local signal=$(iwconfig wlan0 2>/dev/null | grep "Signal level" | awk '{print $4}' | cut -d"=" -f2)
    local quality=$(iwconfig wlan0 2>/dev/null | grep "Link Quality" | awk '{print $2}' | cut -d"=" -f2)
    echo "$quality ($signal dBm)"
}

# Function to check internet connection
check_internet() {
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        local speed=$(speedtest-cli --simple 2>/dev/null | grep -oP "Download: \K[0-9.]+")
        echo -e "${GREEN}Connected${NC} (Download: ${speed:-N/A} Mbit/s)"
    else
        echo -e "${RED}Disconnected${NC}"
    fi
}

# Function to get network info
show_network_info() {
    echo -e "${BLUE}Network Information:${NC}"
    echo "-------------------"
    echo -e "WiFi Network:    $(iwconfig wlan0 2>/dev/null | grep ESSID | awk -F'"' '{print $2}')"
    echo -e "Signal Strength: $(get_wifi_strength)"
    echo -e "IP Address:      $(hostname -I | awk '{print $1}')"
    echo -e "Internet:        $(check_internet)"
    echo
}

# Main display
clear
echo -e "${BOLD}Internet Radio Monitor${NC}"
echo "===================="
echo

# Show network status
show_network_info

# Show service status
echo -e "${BLUE}Service Status:${NC}"
echo "---------------"
systemctl status internetradio | head -n 4
echo

# Show audio status
echo -e "${BLUE}Audio Status:${NC}"
echo "-------------"
amixer get Master | grep -E 'Mono|Playback' | tail -n 2
echo

# Show current station
echo -e "${BLUE}Current Station:${NC}"
echo "----------------"
if pgrep -f "python.*main.py" > /dev/null; then
    current_station=$(ps aux | grep "python.*main.py" | grep -v grep)
    echo -e "${GREEN}Radio is running${NC}"
else
    echo -e "${RED}Radio is not running${NC}"
fi
echo

# Monitor logs
echo -e "${BLUE}Live Logs:${NC}"
echo "----------"
echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
echo

# Follow logs with highlighting
journalctl -u internetradio -f -n 50 | while read line; do
    # Network related
    if [[ $line == *"Network"* ]] || [[ $line == *"WiFi"* ]] || [[ $line == *"Connection"* ]]; then
        echo -e "${BLUE}$line${NC}"
    # Errors
    elif [[ $line == *"ERROR"* ]] || [[ $line == *"Failed"* ]]; then
        echo -e "${RED}$line${NC}"
    # Playing status
    elif [[ $line == *"Playing"* ]] || [[ $line == *"Station"* ]]; then
        echo -e "${GREEN}$line${NC}"
    # Volume changes
    elif [[ $line == *"Volume"* ]]; then
        echo -e "${YELLOW}$line${NC}"
    # Everything else
    else
        echo "$line"
    fi
done 
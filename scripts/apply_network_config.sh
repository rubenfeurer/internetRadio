#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Generate config
python3 -c "from src.network.wifi_manager import WiFiManager; WiFiManager().generate_network_config()"

if [ $? -ne 0 ]; then
    echo "Failed to generate config"
    exit 1
fi

# Backup existing config
if [ -f /etc/NetworkManager/NetworkManager.conf ]; then
    cp /etc/NetworkManager/NetworkManager.conf /etc/NetworkManager/NetworkManager.conf.backup
fi

# Apply new config
cp networkmanager.conf /etc/NetworkManager/NetworkManager.conf
chmod 644 /etc/NetworkManager/NetworkManager.conf

# Restart NetworkManager
systemctl restart NetworkManager

# Enable WiFi
nmcli radio wifi on
rfkill unblock wifi

echo "Network configuration applied successfully" 
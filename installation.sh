# DNS Configuration
echo "Configuring DNS settings..."
sudo rm -f /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf
sudo chmod 644 /etc/resolv.conf
sudo chattr +i /etc/resolv.conf

# Configure systemd-networkd to not override DNS
sudo mkdir -p /etc/systemd/network/
cat > /etc/systemd/network/25-wireless.network << EOL
[Match]
Name=wlan0

[Network]
DHCP=yes
DNSDefaultRoute=no

[DHCP]
UseDNS=no
EOL

# Restart networking services
sudo systemctl restart systemd-networkd
sudo systemctl restart wpa_supplicant 
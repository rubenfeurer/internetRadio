import subprocess
import logging
import time
from typing import List, Dict, Optional, Any
import os
from src.utils.config_manager import ConfigManager
import socket

class WiFiManager:
    def __init__(self):
        self.logger = logging.getLogger('network')
        # Load from config
        config = ConfigManager()
        network_config = config.get_network_config()
        
        # Get AP settings from config with fallbacks
        ap_ssid = network_config.get('ap_ssid', '${HOSTNAME}')
        if ap_ssid == '${HOSTNAME}':
            ap_ssid = socket.gethostname()
        
        self.ap_ssid = ap_ssid
        self.ap_password = network_config.get('ap_password', 'Radio@1234')
        self.ap_channel = network_config.get('ap_channel', 6)
        
    def get_saved_networks(self) -> List[Dict[str, Any]]:
        """Get list of saved WiFi networks with details"""
        try:
            # Get from both NetworkManager and our config
            nm_networks = self._get_nm_saved_networks()
            
            # Get from our config
            config = ConfigManager()
            network_config = config.get_network_config()
            saved_networks = network_config.get('saved_networks', [])
            
            # Merge and validate
            result = []
            for network in saved_networks:
                if network['ssid'] in nm_networks:
                    result.append(network)
                else:
                    # Network exists in our config but not in NetworkManager
                    self.logger.warning(f"Network {network['ssid']} found in config but not in NetworkManager")
                    
            return result
                
        except Exception as e:
            self.logger.error(f"Error getting saved networks: {str(e)}")
            return []
    
    def _get_nm_saved_networks(self) -> List[str]:
        """Get list of networks saved in NetworkManager"""
        try:
            result = subprocess.run(
                ["sudo", "nmcli", "connection", "show"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                networks = []
                for line in result.stdout.split('\n')[1:]:
                    if line.strip() and "wifi" in line:
                        networks.append(line.split()[0])
                return networks
            return []
                
        except Exception as e:
            self.logger.error(f"Error getting NetworkManager networks: {str(e)}")
            return []
    
    def scan_networks(self) -> List[Dict[str, str]]:
        """Scan for available WiFi networks"""
        try:
            self.logger.info("Scanning for networks...")
            result = subprocess.run(
                ["sudo", "iwlist", "wlan0", "scan"],
                capture_output=True,
                text=True
            )
            
            networks = []
            current_network = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if 'ESSID:' in line:
                    ssid = line.split('ESSID:"')[1].split('"')[0]
                    if ssid:  # Only add non-empty SSID
                        current_network['ssid'] = ssid
                        networks.append(current_network)
                        current_network = {}
                elif 'Quality=' in line:
                    quality = line.split('Quality=')[1].split(' ')[0]
                    current_network['quality'] = quality
                    
            self.logger.info(f"Found networks: {networks}")
            return networks
            
        except Exception as e:
            self.logger.error(f"Error scanning networks: {str(e)}")
            return []
    
    def connect_to_network(self, ssid: str, password: Optional[str] = None) -> bool:
        """Connect to a WiFi network"""
        try:
            self.logger.info(f"Attempting to connect to {ssid}")
            
            if password:
                cmd = [
                    "sudo", "nmcli", "device", "wifi", "connect", ssid,
                    "password", password
                ]
            else:
                cmd = ["sudo", "nmcli", "device", "wifi", "connect", ssid]
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully connected to {ssid}")
                return True
            else:
                self.logger.error(f"Failed to connect to {ssid}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to network: {str(e)}")
            return False
    
    def initialize(self) -> bool:
        """Initialize WiFi hardware"""
        try:
            self.logger.info("Initializing WiFi Manager")
            # Execute commands and check their return codes
            commands = [
                ["sudo", "rfkill", "unblock", "wifi"],
                ["sudo", "ifconfig", "wlan0", "up"]
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"Command failed: {' '.join(cmd)}")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WiFi: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to a WiFi network"""
        try:
            result = subprocess.run(
                ["iwconfig", "wlan0"],
                capture_output=True,
                text=True
            )
            
            # More precise check for connection status
            if "ESSID:" not in result.stdout:
                return False
                
            if "Not-Associated" in result.stdout:
                return False
                
            if "ESSID:off/any" in result.stdout:
                return False
                
            essid = result.stdout.split('ESSID:"')[1].split('"')[0]
            return bool(essid.strip())
            
        except Exception as e:
            self.logger.error(f"Error checking connection status: {e}")
            return False

    def get_current_network(self) -> Optional[str]:
        """Get current connected network SSID"""
        try:
            result = subprocess.run(
                ["iwconfig", "wlan0"],
                capture_output=True,
                text=True
            )
            if "ESSID:" in result.stdout:
                essid = result.stdout.split('ESSID:"')[1].split('"')[0]
                return essid if essid else None
            return None
        except Exception as e:
            self.logger.error(f"Error getting current network: {e}")
            return None

    def disconnect(self) -> bool:
        """Disconnect from current network"""
        try:
            result = subprocess.run(
                ["sudo", "nmcli", "device", "disconnect", "wlan0"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
            return False

    def cleanup(self) -> None:
        """Cleanup WiFi resources"""
        try:
            self.logger.info("Cleaning up WiFi resources...")
            # Stop wpa_supplicant if running
            subprocess.run(["sudo", "systemctl", "stop", "wpa_supplicant"], 
                         check=False)
            # Reset interface if needed
            subprocess.run(["sudo", "ifconfig", "wlan0", "down"], 
                         check=False)
            self.logger.info("WiFi cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during WiFi cleanup: {str(e)}")

    def configure_dns(self) -> bool:
        """Configure DNS servers with direct resolv.conf management"""
        try:
            self.logger.info("Configuring DNS servers...")
            dns_config = "nameserver 8.8.8.8\nnameserver 8.8.4.4\n"
            
            # Check if resolv.conf exists and is a symlink
            if os.path.islink('/etc/resolv.conf'):
                self.logger.info("Removing resolv.conf symlink...")
                result = subprocess.run(
                    ['sudo', 'rm', '/etc/resolv.conf'],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.logger.error(f"Failed to remove symlink: {result.stderr}")
                    return False
            
            # Write new resolv.conf
            result = subprocess.run(
                ['sudo', 'bash', '-c', f'echo "{dns_config}" > /etc/resolv.conf'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.logger.error(f"Failed to write DNS config: {result.stderr}")
                return False
            
            # Set proper permissions
            result = subprocess.run(
                ['sudo', 'chmod', '644', '/etc/resolv.conf'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.logger.error(f"Failed to set permissions: {result.stderr}")
                return False
            
            self.logger.info("DNS servers configured successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error configuring DNS: {e}")
            return False

    def check_dns_resolution(self) -> bool:
        """Check if DNS resolution is working"""
        try:
            self.logger.info("Checking DNS resolution...")
            import socket
            socket.gethostbyname('google.com')
            self.logger.info("DNS resolution working")
            return True
        except socket.gaierror as e:
            self.logger.error(f"DNS resolution failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking DNS: {e}")
            return False
        except socket.gaierror as e:
            self.logger.error(f"DNS resolution failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking DNS: {e}")
            return False

    def save_network(self, ssid: str, password: Optional[str] = None) -> bool:
        """Save network to both NetworkManager and our config"""
        try:
            # Save to NetworkManager
            if password:
                cmd = ["sudo", "nmcli", "connection", "add",
                      "type", "wifi",
                      "con-name", ssid,
                      "ifname", "wlan0",
                      "ssid", ssid,
                      "wifi-sec.key-mgmt", "wpa-psk",
                      "wifi-sec.psk", password]
            else:
                cmd = ["sudo", "nmcli", "connection", "add",
                      "type", "wifi",
                      "con-name", ssid,
                      "ifname", "wlan0",
                      "ssid", ssid]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to save network {ssid}: {result.stderr}")
                return False
            
            # Save to our config
            config = ConfigManager()
            network_config = config.get_network_config()
            saved_networks = network_config.get('saved_networks', [])
            
            if ssid not in saved_networks:
                saved_networks.append({
                    'ssid': ssid,
                    'password': password,
                    'last_connected': time.strftime('%Y-%m-%d %H:%M:%S')
                })
                network_config['saved_networks'] = saved_networks
                config.update_network_config(network_config)
            
            self.logger.info(f"Successfully saved network {ssid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving network: {str(e)}")
            return False

    def remove_network(self, ssid: str) -> bool:
        """Remove network from both NetworkManager and our config"""
        try:
            # Remove from NetworkManager
            cmd = ["sudo", "nmcli", "connection", "delete", ssid]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to remove network {ssid}: {result.stderr}")
                return False
            
            # Remove from our config
            config = ConfigManager()
            network_config = config.get_network_config()
            saved_networks = network_config.get('saved_networks', [])
            saved_networks = [n for n in saved_networks if n['ssid'] != ssid]
            network_config['saved_networks'] = saved_networks
            config.update_network_config(network_config)
            
            self.logger.info(f"Successfully removed network {ssid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing network: {str(e)}")
            return False

    def maintain_networks(self) -> None:
        """Clean up saved networks based on connection history"""
        try:
            config = ConfigManager()
            network_config = config.get_network_config()
            saved_networks = network_config.get('saved_networks', [])
            current_time = time.time()
            
            networks_to_remove = []
            for network in saved_networks:
                last_connected = time.strptime(network['last_connected'], '%Y-%m-%d %H:%M:%S')
                days_since_connection = (current_time - time.mktime(last_connected)) / (24 * 3600)
                
                # Remove if not connected for 30 days
                if days_since_connection > 30:
                    networks_to_remove.append(network['ssid'])
                    
            # Remove old networks
            for ssid in networks_to_remove:
                self.remove_network(ssid)
                
        except Exception as e:
            self.logger.error(f"Error maintaining networks: {str(e)}")

    def check_internet_connection(self) -> bool:
        """Check internet connectivity with multiple fallback hosts"""
        test_hosts = [
            ("8.8.8.8", 53),    # Google DNS
            ("1.1.1.1", 53),    # Cloudflare DNS
            ("208.67.222.222", 53)  # OpenDNS
        ]
        
        for host, port in test_hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    self.logger.info(f"Internet connection verified via {host}")
                    return True
                    
            except Exception as e:
                self.logger.error(f"Error checking connection to {host}: {e}")
                continue
                
        self.logger.error("Failed to connect to any test hosts")
        return False

    def enable_client_mode(self) -> bool:
        """Enable client mode and disable AP mode"""
        try:
            # First, stop AP mode if it's running
            subprocess.run(["sudo", "systemctl", "stop", "hostapd"], check=False)
            subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"], check=False)
            
            # Enable NetworkManager control
            subprocess.run(["sudo", "nmcli", "radio", "wifi", "on"], check=True)
            subprocess.run(["sudo", "rfkill", "unblock", "wifi"], check=False)
            
            self.logger.info("Client mode enabled")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to enable client mode: {str(e)}")
            return False
            
    def enable_ap_mode(self) -> bool:
        """Enable AP mode and disable client mode"""
        try:
            # First, disconnect from any networks
            self.disconnect()
            
            # Stop NetworkManager control of wlan0 and disable WiFi
            subprocess.run(["sudo", "nmcli", "radio", "wifi", "off"], check=True)
            subprocess.run(["sudo", "nmcli", "device", "set", "wlan0", "managed", "no"], check=True)
            
            # Start AP services
            subprocess.run(["sudo", "systemctl", "start", "hostapd"], check=True)
            subprocess.run(["sudo", "systemctl", "start", "dnsmasq"], check=True)
            
            self.logger.info("AP mode enabled")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to enable AP mode: {str(e)}")
            return False

    def is_client_mode(self) -> bool:
        """Check if WiFi is in client mode"""
        try:
            cmd = ["nmcli", "device", "status"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error("Failed to check client mode status")
                return False
                
            # Check if wlan0 is present AND in managed state AND not unmanaged
            lines = result.stdout.split('\n')
            for line in lines:
                if 'wlan0' in line:
                    return 'managed' in line.lower() and 'unmanaged' not in line.lower()
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking client mode: {str(e)}")
            return False
            
    def is_ap_mode(self) -> bool:
        """Check if WiFi is in AP mode"""
        try:
            # Check if hostapd is running
            cmd = ["systemctl", "is-active", "hostapd"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Error checking AP mode: {str(e)}")
            return False
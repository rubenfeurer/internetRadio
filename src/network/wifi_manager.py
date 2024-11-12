import subprocess
import logging
import time
from typing import List, Dict, Optional

class WiFiManager:
    def __init__(self):
        self.logger = logging.getLogger('network')
        self.ap_ssid = "InternetRadio"
        self.ap_password = "raspberry"
        
    def get_saved_networks(self) -> List[str]:
        """Get list of saved WiFi networks"""
        try:
            self.logger.info("Checking for saved networks...")
            result = subprocess.run(
                ["sudo", "nmcli", "connection", "show"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                networks = []
                for line in result.stdout.split('\n')[1:]:  # Skip header
                    if line.strip() and "wifi" in line:
                        networks.append(line.split()[0])
                self.logger.info(f"Found saved networks: {networks}")
                return networks
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting saved networks: {str(e)}")
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
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize WiFi: {e}")
            return False
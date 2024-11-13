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
            self.logger.info("Cleaning up WiFi Manager resources...")
            # Add any necessary cleanup code here
        except Exception as e:
            self.logger.error(f"Error during WiFi Manager cleanup: {e}")
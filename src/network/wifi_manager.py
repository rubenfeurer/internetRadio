import subprocess
import logging
import time
from typing import List, Dict, Optional, Any
import os
from src.utils.config_manager import ConfigManager
import socket
import shutil

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
    
    def scan_networks(self) -> List[Dict[str, Any]]:
        """Scan for available WiFi networks"""
        try:
            result = subprocess.run(
                ['nmcli', '-f', 'IN-USE,SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list', '--rescan', 'yes'],
                capture_output=True,
                text=True,
                check=True
            )
            
            networks = []
            lines = result.stdout.strip().split('\n')
            
            # Skip header line
            for line in lines[1:]:
                if not line.strip():
                    continue
                    
                # Parse fixed-width format
                try:
                    in_use = line[0:8].strip()
                    ssid = line[8:24].strip()
                    signal = line[24:32].strip()
                    security = line[32:].strip()
                    
                    networks.append({
                        'ssid': ssid,
                        'signal': int(signal),  # Convert to integer
                        'security': '' if security == '--' else security,
                        'in_use': '*' in in_use
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse line '{line}': {e}")
                    continue
                    
            self.logger.debug(f"Mock output:\n{result.stdout}")
            self.logger.debug(f"Parsed networks: {networks}")
            return networks
            
        except Exception as e:
            self.logger.error(f"Error scanning networks: {e}")
            return []
    
    def connect_to_network(self, ssid: str, password: str) -> bool:
        """Connect to a WiFi network using nmcli"""
        try:
            # First disconnect from current network
            disconnect_result = subprocess.run(
                ['nmcli', 'device', 'disconnect', 'wlan0'],
                capture_output=True,
                text=True
            )
            
            if disconnect_result.returncode != 0:
                self.logger.error(f"Failed to disconnect: {disconnect_result.stderr}")
                return False
            
            # Connect to new network
            connect_result = subprocess.run(
                ['nmcli', 'device', 'wifi', 'connect', ssid,
                 'password', password, 'ifname', 'wlan0'],
                capture_output=True,
                text=True
            )
            
            if connect_result.returncode != 0:
                self.logger.error(f"Failed to connect: {connect_result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to network: {e}")
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
                ['nmcli', 'device', 'status'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to check connection status: {result.stderr}")
                return False
            
            # Parse output looking for wifi device that's connected
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'wifi' in line.lower() and 'connected' in line.lower():
                    # Make sure it's not "disconnected"
                    if 'disconnected' not in line.lower():
                        return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking connection status: {e}")
            return False

    def get_current_network(self) -> Optional[str]:
        """Get the name of the currently connected network"""
        try:
            result = subprocess.run(
                ['nmcli', 'device', 'status'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get current network: {result.stderr}")
                return None
            
            # Parse output looking for connected wifi device
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'wifi' in line.lower() and 'connected' in line.lower():
                    # Make sure it's not "disconnected"
                    if 'disconnected' not in line.lower():
                        # Get the last field which is the network name
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            network = parts[3]
                            return None if network == '--' else network
                    
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
        """Configure DNS servers using nmcli"""
        try:
            self.logger.info("Configuring DNS servers...")
            
            # Get active connection name
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'NAME,UUID,TYPE,DEVICE', 'connection', 'show', '--active'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error("Failed to get active connection")
                return False
            
            # Parse active wifi connection name
            active_connection = None
            for line in result.stdout.strip().split('\n'):
                parts = line.split(':')
                if len(parts) >= 3 and 'wifi' in parts[2].lower():
                    active_connection = parts[0]  # NAME is the first field
                    break
                
            if not active_connection:
                self.logger.error("No active WiFi connection found")
                return False
            
            # Set DNS servers
            dns_result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'modify', active_connection,
                 'ipv4.dns', '8.8.8.8,8.8.4.4'],
                capture_output=True,
                text=True
            )
            
            if dns_result.returncode != 0:
                self.logger.error(f"Failed to set DNS servers: {dns_result.stderr}")
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

    def save_network(self, ssid: str, password: str) -> bool:
        """Save network credentials to configuration"""
        try:
            # Get current network config
            config = ConfigManager()
            network_config = config.get_network_config()
            
            # Initialize saved_networks if not exists
            if 'saved_networks' not in network_config:
                network_config['saved_networks'] = []
            
            # Check if network already exists
            for network in network_config['saved_networks']:
                if network['ssid'] == ssid:
                    network['password'] = password  # Update password
                    break
            else:
                # Add new network
                network_config['saved_networks'].append({
                    'ssid': ssid,
                    'password': password
                })
            
            # Save updated config and return result
            return config.save_network_config(network_config)
            
        except Exception as e:
            self.logger.error(f"Error saving network: {e}")
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
            # Check if any wifi connection is active
            result = subprocess.run(
                ['nmcli', 'device', 'status'],
                capture_output=True,
                text=True
            )
            
            # Look for "wifi      connected" in the output
            return 'wifi      connected' in result.stdout
            
        except Exception as e:
            self.logger.error(f"Error checking client mode: {e}")
            return False

    def is_ap_mode(self) -> bool:
        """Check if WiFi is in AP mode"""
        try:
            # Check if hostapd is active
            result = subprocess.run(
                ['systemctl', 'is-active', 'hostapd'],
                capture_output=True,
                text=True
            )
            # AP mode is active only if hostapd service is active
            return result.stdout.strip() == "active"
            
        except Exception as e:
            self.logger.error(f"Error checking AP mode: {e}")
            return False

    def apply_network_config(self) -> bool:
        """Apply NetworkManager configuration"""
        try:
            # Paths
            config_path = "src/utils/network_configs/networkmanager.conf"
            system_path = "/etc/NetworkManager/NetworkManager.conf"
            backup_path = "/etc/NetworkManager/NetworkManager.conf.backup"
            
            # Check if config exists
            if not os.path.exists(config_path):
                self.logger.error(f"Config file not found: {config_path}")
                return False
            
            # Create backup
            if os.path.exists(system_path):
                shutil.copy2(system_path, backup_path)
                self.logger.info(f"Backup created: {backup_path}")
            
            # Copy new config
            shutil.copy2(config_path, system_path)
            os.chmod(system_path, 0o644)
            self.logger.info("Network config updated")
            
            # Restart NetworkManager
            subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=True)
            self.logger.info("NetworkManager restarted")
            
            # Enable WiFi
            subprocess.run(["sudo", "nmcli", "radio", "wifi", "on"], check=True)
            subprocess.run(["sudo", "rfkill", "unblock", "wifi"], check=True)
            self.logger.info("WiFi enabled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying network config: {e}")
            return False

    def generate_network_config(self) -> bool:
        """Generate NetworkManager configuration file"""
        try:
            config_content = """[main]
plugins=ifupdown,keyfile

[ifupdown]
managed=true

[device]
wifi.scan-rand-mac-address=no"""

            # Use correct path
            config_dir = "src/utils/network_configs"
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "networkmanager.conf")
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            self.logger.info(f"Network config generated: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating network config: {e}")
            return False

    def connect_wifi(self, ssid: str, password: str) -> bool:
        """Connect to WiFi with proper service management"""
        try:
            # Stop services that might interfere
            subprocess.run(['sudo', 'systemctl', 'stop', 'internetradio'], check=True)
            subprocess.run(['sudo', 'systemctl', 'stop', 'radiomonitor'], check=True)
            subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], check=True)
            
            # Clean restart NetworkManager
            subprocess.run(['sudo', 'systemctl', 'restart', 'NetworkManager'], check=True)
            time.sleep(5)  # Wait for NetworkManager to be ready
            
            # Remove existing connection if any
            subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], check=False)
            
            # Add connection with specific parameters
            cmd = [
                'sudo', 'nmcli', 'connection', 'add',
                'type', 'wifi',
                'con-name', ssid,
                'ifname', 'wlan0',
                'ssid', ssid,
                'wifi-sec.key-mgmt', 'wpa-psk',
                'wifi-sec.psk', password,
                '802-11-wireless.band', 'a',
                'ipv4.method', 'auto',
                'connection.autoconnect', 'yes'
            ]
            subprocess.run(cmd, check=True)
            
            # Connect
            subprocess.run(['sudo', 'nmcli', 'connection', 'up', ssid], check=True)
            
            # Verify connection
            time.sleep(5)
            result = subprocess.run(['nmcli', 'device', 'status'], 
                                  capture_output=True, text=True)
            
            if 'wifi      connected' in result.stdout:
                # Restart services
                subprocess.run(['sudo', 'systemctl', 'start', 'internetradio'], check=True)
                subprocess.run(['sudo', 'systemctl', 'start', 'radiomonitor'], check=True)
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error connecting to WiFi: {e}")
            return False

    def connect_to_saved_network(self, ssid: str) -> bool:
        """Connect to a saved network by SSID with retry mechanism"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # Get network config
                config = ConfigManager()
                network_config = config.get_network_config()
                
                # Find network in saved networks
                network = next(
                    (n for n in network_config.get('saved_networks', []) if n['ssid'] == ssid),
                    None
                )
                if not network:
                    self.logger.error(f"Network {ssid} not found in saved networks")
                    return False
                
                # Stop services that might interfere
                subprocess.run(['sudo', 'systemctl', 'stop', 'internetradio'], check=False)
                subprocess.run(['sudo', 'systemctl', 'stop', 'radiomonitor'], check=False)
                subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], check=False)
                
                # Restart NetworkManager
                if subprocess.run(['sudo', 'systemctl', 'restart', 'NetworkManager']).returncode != 0:
                    self.logger.error("Failed to restart NetworkManager")
                    retry_count += 1
                    continue
                
                # Delete existing connection if exists
                subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid])
                
                # Connect to network
                connect_result = subprocess.run([
                    'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
                    'password', network['password']
                ])
                
                # Verify connection
                status_result = subprocess.run(
                    ['nmcli', 'device', 'status'],
                    capture_output=True,
                    text=True
                )
                
                if connect_result.returncode == 0 and 'wifi      connected' in status_result.stdout:
                    self.logger.info(f"Successfully connected to {ssid}")
                    return True
                
                self.logger.warning(f"Connection attempt {retry_count + 1} failed")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error connecting to network: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(5)
        
        return False

    def get_signal_strength(self) -> int:
        """Get current WiFi signal strength using nmcli"""
        try:
            result = subprocess.run(
                ['nmcli', '-f', 'IN-USE,SSID,SIGNAL', 'device', 'wifi', 'list'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return 0
            
            # Find the line with '*' (current connection)
            for line in result.stdout.split('\n'):
                if '*' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            # Signal strength is the last field
                            return int(parts[-1])
                        except ValueError:
                            return 0
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error getting signal strength: {e}")
            return 0

    def disable_power_management(self) -> bool:
        """Disable WiFi power management via NetworkManager"""
        try:
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'modify', 'type', 'wifi', 
                 'wifi.powersave', '2'],  # 2 = disabled
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error disabling power management: {e}")
            return False
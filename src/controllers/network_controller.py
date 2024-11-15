from src.utils.logger import Logger
import subprocess
import time
import threading
from typing import Optional, Dict, List, Tuple

class NetworkController:
    def __init__(self, config_manager=None):
        """Initialize NetworkController"""
        # Initialize logger
        self.logger = Logger('network', log_dir='/home/radio/internetRadio/logs')
        
        self.config_manager = config_manager
        self.current_network = None
        self.ap_mode = False
        self.scan_thread = None
        self.should_scan = False
        
        try:
            # Initialize network state
            self._init_network_state()
            self.logger.info("NetworkController initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing NetworkController: {e}")
            raise

    def _init_network_state(self) -> None:
        """Initialize network state"""
        try:
            # Check if NetworkManager is running
            result = subprocess.run(['systemctl', 'is-active', 'NetworkManager'], 
                                 capture_output=True, text=True)
            if result.stdout.strip() != 'active':
                self.logger.warning("NetworkManager is not running")
                
            # Get current connection state
            self._update_connection_state()
        except Exception as e:
            self.logger.error(f"Error initializing network state: {e}")
            raise

    def _update_connection_state(self) -> None:
        """Update current connection state"""
        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'NAME,TYPE,STATE', 'connection', 'show', '--active'],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                connections = result.stdout.strip().split('\n')
                for conn in connections:
                    if conn:
                        name, type_, state = conn.split(':')
                        if type_ == 'wifi' and state == 'activated':
                            self.current_network = name
                            return
                
            self.current_network = None
        except Exception as e:
            self.logger.error(f"Error updating connection state: {e}")
            self.current_network = None

    def scan_networks(self) -> List[Dict[str, str]]:
        """Scan for available WiFi networks"""
        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list'],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                networks = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        ssid, signal, security = line.split(':')
                        if ssid:  # Skip empty SSIDs
                            networks.append({
                                'ssid': ssid,
                                'signal': signal,
                                'security': security
                            })
                return networks
            return []
        except Exception as e:
            self.logger.error(f"Error scanning networks: {e}")
            return []

    def connect_to_network(self, ssid: str, password: Optional[str] = None) -> bool:
        """Connect to a WiFi network"""
        try:
            if self.ap_mode:
                self.stop_ap_mode()
            
            cmd = ['nmcli', 'device', 'wifi', 'connect', ssid]
            if password:
                cmd.extend(['password', password])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.current_network = ssid
                self.logger.info(f"Connected to network: {ssid}")
                return True
            else:
                self.logger.error(f"Failed to connect to network: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error connecting to network: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from current network"""
        try:
            if self.current_network:
                result = subprocess.run(['nmcli', 'connection', 'down', self.current_network],
                                     capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.current_network = None
                    self.logger.info("Disconnected from network")
                    return True
                else:
                    self.logger.error(f"Failed to disconnect: {result.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
            return False

    def start_ap_mode(self) -> bool:
        """Start Access Point mode"""
        try:
            if self.current_network:
                self.disconnect()
            
            if not self.config_manager:
                self.logger.error("No config manager available")
                return False
            
            ssid = self.config_manager.network.ap_ssid
            password = self.config_manager.network.ap_password
            
            cmd = [
                'nmcli', 'device', 'wifi', 'hotspot',
                'ssid', ssid,
                'password', password
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.ap_mode = True
                self.logger.info(f"Started AP mode with SSID: {ssid}")
                return True
            else:
                self.logger.error(f"Failed to start AP mode: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error starting AP mode: {e}")
            return False

    def stop_ap_mode(self) -> bool:
        """Stop Access Point mode"""
        try:
            if self.ap_mode:
                result = subprocess.run(['nmcli', 'connection', 'down', 'Hotspot'],
                                     capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.ap_mode = False
                    self.logger.info("Stopped AP mode")
                    return True
                else:
                    self.logger.error(f"Failed to stop AP mode: {result.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Error stopping AP mode: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.ap_mode:
                self.stop_ap_mode()
            if self.current_network:
                self.disconnect()
            self.logger.info("NetworkController cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
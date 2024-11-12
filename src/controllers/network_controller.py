import logging
from typing import Optional, Dict, List
from ..network.wifi_manager import WiFiManager
from ..network.ap_manager import APManager
from ..utils.logger import Logger

class NetworkController:
    """Controls network functionality (WiFi client and AP mode)"""
    
    def __init__(self):
        self.logger = Logger(__name__)
        self.logger.debug("Initializing NetworkController")
        self.wifi_manager = WiFiManager()
        self.ap_manager = APManager()
        self.is_ap_mode = False
        self.logger.debug("NetworkController initialization complete")
    
    def initialize(self) -> bool:
        """Initialize network components"""
        try:
            self.logger.debug("Starting NetworkController initialization")
            if not self.wifi_manager.initialize():
                self.logger.error("Failed to initialize WiFi manager")
                return False
            
            if not self.ap_manager.initialize():
                self.logger.error("Failed to initialize AP manager")
                return False
            
            self.logger.debug("NetworkController initialization successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing NetworkController: {e}")
            return False
    
    def scan_networks(self) -> List[Dict[str, str]]:
        """Scan for available WiFi networks"""
        try:
            return self.wifi_manager.scan_networks()
        except Exception as e:
            self.logger.error(f"Error scanning networks: {e}")
            return []
    
    def connect_wifi(self, ssid: str, password: str) -> bool:
        """Connect to a WiFi network"""
        try:
            self.logger.debug(f"Attempting to connect to WiFi: {ssid}")
            if self.is_ap_mode:
                self.stop_ap_mode()
            
            result = self.wifi_manager.connect_to_network(ssid, password)
            self.logger.debug(f"WiFi connection result: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error connecting to WiFi: {e}")
            return False
    
    def start_ap_mode(self, ssid: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Start Access Point mode"""
        try:
            if self.ap_manager.start(ssid, password):
                self.is_ap_mode = True
                self.logger.info("AP mode started")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error starting AP mode: {e}")
            return False
    
    def stop_ap_mode(self) -> bool:
        """Stop Access Point mode"""
        try:
            if self.ap_manager.stop():
                self.is_ap_mode = False
                self.logger.info("AP mode stopped")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error stopping AP mode: {e}")
            return False
    
    def get_current_ip(self) -> Optional[str]:
        """Get current IP address"""
        try:
            if self.is_ap_mode:
                return self.ap_manager.get_ip()
            return self.wifi_manager.get_ip()
        except Exception as e:
            self.logger.error(f"Error getting IP address: {e}")
            return None
    
    def get_connection_status(self) -> Dict[str, any]:
        """Get current network connection status"""
        try:
            return {
                'is_ap_mode': self.is_ap_mode,
                'ip_address': self.get_current_ip(),
                'wifi_connected': self.wifi_manager.is_connected() if not self.is_ap_mode else False,
                'current_ssid': self.wifi_manager.get_current_ssid() if not self.is_ap_mode else None
            }
        except Exception as e:
            self.logger.error(f"Error getting connection status: {e}")
            return {
                'is_ap_mode': False,
                'ip_address': None,
                'wifi_connected': False,
                'current_ssid': None
            }
    
    def cleanup(self) -> None:
        """Clean up network resources"""
        try:
            if self.is_ap_mode:
                self.stop_ap_mode()
            self.wifi_manager.cleanup()
            self.ap_manager.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
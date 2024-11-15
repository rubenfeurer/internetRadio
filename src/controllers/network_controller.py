from src.utils.logger import Logger
from src.network.wifi_manager import WiFiManager
from src.network.ap_manager import APManager
from src.audio.audio_manager import AudioManager
import subprocess
import time
import threading
import os
import logging

class NetworkController:
    def __init__(self, config_manager=None, wifi_manager=None, ap_manager=None):
        self.logger = logging.getLogger('src.controllers.network_controller')
        self.config_manager = config_manager
        self.wifi_manager = wifi_manager
        self.ap_manager = ap_manager
        self.initialized = False
        self.is_ap_mode = False
        
    def initialize(self) -> bool:
        """Initialize network controller"""
        try:
            if self.wifi_manager:
                if not self.wifi_manager.initialize():
                    return False
                    
            if self.ap_manager:
                if not self.ap_manager.initialize():
                    return False
                    
            self.initialized = True
            self.logger.info("NetworkController initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing NetworkController: {e}")
            return False
            
    def cleanup(self) -> None:
        """Cleanup network resources"""
        try:
            if self.wifi_manager:
                self.wifi_manager.cleanup()
                
            if self.ap_manager:
                self.ap_manager.stop()
                self.ap_manager.cleanup()
                
            if not os.environ.get('TESTING'):
                try:
                    subprocess.run(["sudo", "systemctl", "start", "NetworkManager"], 
                                 check=True, capture_output=True)
                except Exception as e:
                    self.logger.warning(f"Error starting NetworkManager during cleanup: {e}")
                    
            self.initialized = False
            self.logger.info("NetworkController cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            
    def start_ap_mode(self, ssid: str = "InternetRadio", password: str = "raspberry") -> bool:
        """Start AP mode with given or default credentials"""
        try:
            if not self.initialized or not self.ap_manager:
                return False
                
            if not ssid or ssid == '${HOSTNAME}':
                ssid = "InternetRadio"
                
            self.logger.info(f"Starting AP mode with SSID: {ssid}")
            if not self.ap_manager.start(ssid, password):
                return False
                
            self.is_ap_mode = True
            return True
        except Exception as e:
            self.logger.error(f"Error starting AP mode: {e}")
            return False
            
    def connect_wifi(self, ssid: str, password: str) -> bool:
        """Connect to WiFi network"""
        try:
            if not self.initialized or not self.wifi_manager:
                return False
            return self.wifi_manager.connect_to_network(ssid, password)
        except Exception as e:
            self.logger.error(f"Error connecting to WiFi: {e}")
            return False
            
    def is_ap_mode_active(self) -> bool:
        """Check if AP mode is active"""
        return self.is_ap_mode and self.ap_manager and self.ap_manager.is_active()
        
    def check_and_setup_network(self) -> bool:
        """Check and setup network connection"""
        try:
            if not self.initialized:
                self.logger.error("NetworkController not initialized")
                return False
                
            if not self.config_manager:
                self.logger.info("No config manager available, starting AP mode with default configuration")
                return self.start_ap_mode()
                
            try:
                saved_networks = self.config_manager.get_saved_networks()
                if saved_networks:
                    for ssid, password in saved_networks.items():
                        if self.connect_wifi(ssid, password):
                            self.logger.info(f"Connected to saved network: {ssid}")
                            return True
                            
                # If we get here, no saved networks worked
                ap_config = self.config_manager.get_ap_config()
                if ap_config and 'ssid' in ap_config and 'password' in ap_config:
                    return self.start_ap_mode(ap_config['ssid'], ap_config['password'])
                    
            except Exception as e:
                self.logger.warning(f"Error connecting to saved networks: {e}")
                
            # Fallback to default AP mode
            return self.start_ap_mode()
        except Exception as e:
            self.logger.error(f"Error in network setup: {e}")
            return False
            
    def monitor(self) -> None:
        """Monitor network status"""
        try:
            if self.is_ap_mode:
                if not self.ap_manager or not self.ap_manager.is_active():
                    self.logger.warning("AP mode stopped unexpectedly")
                    if not self.start_ap_mode():
                        self.logger.error("Failed to restart AP mode")
            else:
                if not self.wifi_manager or not self.wifi_manager.is_connected():
                    self.logger.warning("WiFi connection lost")
                    if not self.check_and_setup_network():
                        if not self.start_ap_mode():
                            self.logger.error("Failed to start AP mode as fallback")
        except Exception as e:
            self.logger.error(f"Error monitoring network: {e}")

    @property
    def ap_mode_active(self) -> bool:
        """Property to check if AP mode is active"""
        return self.is_ap_mode_active()


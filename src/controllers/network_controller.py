from src.utils.logger import Logger
from src.network.wifi_manager import WiFiManager
from src.network.ap_manager import APManager
from src.audio.audio_manager import AudioManager
import subprocess
import time
import threading
import os

class NetworkController:
    def __init__(self, config_manager=None, log_dir=None):
        """Initialize NetworkController"""
        self.logger = Logger(__name__, log_dir=log_dir)
        self.logger.debug("Creating NetworkController")
        self.initialized = False
        self.config_manager = config_manager
        self.is_ap_mode = False
        self.wifi_manager = WiFiManager()
        self.ap_manager = APManager()
        self.audio_manager = AudioManager()
        self.last_connection_state = False

    def initialize(self) -> bool:
        """Initialize network controller"""
        try:
            self.logger.debug("Initializing NetworkController")
            if self.initialized:
                return True
            
            # Initialize managers
            self.wifi_manager.initialize()
            self.ap_manager.initialize()
            
            self.initialized = True
            self.logger.info("NetworkController initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize NetworkController: {e}")
            return False

    def connect_wifi(self, ssid: str, password: str) -> bool:
        """Connect to WiFi network"""
        try:
            self.logger.debug(f"Attempting to connect to network: {ssid}")
            return self.wifi_manager.connect_to_network(ssid, password)
        except Exception as e:
            self.logger.error(f"Failed to connect to WiFi: {e}")
            return False

    def start_ap_mode(self, ssid: str, password: str) -> bool:
        """Start Access Point mode"""
        try:
            self.logger.debug(f"Starting AP mode with SSID: {ssid}")
            if self.ap_manager.start(ssid, password):
                self.is_ap_mode = True
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to start AP mode: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.is_ap_mode:
                self.ap_manager.stop()
            self.wifi_manager.cleanup()
            self.ap_manager.cleanup()
            self.logger.info("NetworkController cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


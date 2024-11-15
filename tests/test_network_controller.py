import unittest
from unittest.mock import patch, MagicMock, call
import logging
import subprocess
import time
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestNetworkController(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Create patches with correct paths - patch where they are used, not where they are defined
        self.patches = [
            patch('src.controllers.network_controller.WiFiManager'),
            patch('src.controllers.network_controller.APManager'),
            patch('src.controllers.network_controller.Logger'),
            patch('src.controllers.network_controller.AudioManager')
        ]
        
        self.logger.debug("Starting patches")
        # Start all patches
        self.mocks = [patcher.start() for patcher in self.patches]
        
        # Get individual mocks
        self.mock_wifi_class = self.mocks[0]
        self.mock_ap_class = self.mocks[1]
        self.mock_logger_class = self.mocks[2]
        self.mock_audio_class = self.mocks[3]
        
        # Create instance mocks
        self.mock_wifi = MagicMock()
        self.mock_ap = MagicMock()
        self.mock_logger = MagicMock()
        self.mock_audio = MagicMock()
        
        # Configure class mocks
        self.mock_wifi_class.return_value = self.mock_wifi
        self.mock_ap_class.return_value = self.mock_ap
        self.mock_logger_class.return_value = self.mock_logger
        self.mock_audio_class.return_value = self.mock_audio
        
        # Import after patching
        from src.controllers.network_controller import NetworkController
        self.network_controller = NetworkController()

    def tearDown(self):
        for patcher in self.patches:
            patcher.stop()

    def test_initialize(self):
        """Test initialization of NetworkController"""
        # Configure mocks
        self.mock_wifi.initialize.return_value = True
        self.mock_ap.initialize.return_value = True
        
        # Call the method
        result = self.network_controller.initialize()
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(self.network_controller.initialized)
        self.mock_wifi.initialize.assert_called_once()
        self.mock_ap.initialize.assert_called_once()

    def test_cleanup(self):
        """Test cleanup method"""
        # Setup
        self.network_controller.is_ap_mode = True
        
        # Call the method
        self.network_controller.cleanup()
        
        # Verify
        self.mock_wifi.cleanup.assert_called_once()
        self.mock_ap.cleanup.assert_called_once()
        self.mock_ap.stop.assert_called_once()

    def test_connect_wifi(self):
        """Test WiFi connection"""
        # Setup
        ssid = "test_network"
        password = "test_password"
        self.mock_wifi.connect_to_network.return_value = True
        
        # Call the method
        result = self.network_controller.connect_wifi(ssid, password)
        
        # Verify
        self.assertTrue(result)
        self.mock_wifi.connect_to_network.assert_called_once_with(ssid, password)

    def test_start_ap_mode(self):
        """Test starting AP mode"""
        # Setup
        ssid = "test_ap"
        password = "test_password"
        self.mock_ap.start.return_value = True
        
        # Call the method
        result = self.network_controller.start_ap_mode(ssid, password)
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(self.network_controller.is_ap_mode)
        self.mock_ap.start.assert_called_once_with(ssid, password)

if __name__ == '__main__':
    unittest.main()
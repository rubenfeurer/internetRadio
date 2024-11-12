import unittest
from unittest.mock import patch, MagicMock
import logging

class TestNetworkController(unittest.TestCase):
    def setUp(self):
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Create patches with correct class names
        self.patches = [
            patch('src.controllers.network_controller.WiFiManager'),  # Changed path to match import in NetworkController
            patch('src.controllers.network_controller.APManager'),
            patch('src.controllers.network_controller.Logger')
        ]
        
        self.logger.debug("Starting patches")
        # Start all patches
        self.mocks = [patcher.start() for patcher in self.patches]
        
        # Get individual mocks
        self.mock_wifi_class = self.mocks[0]
        self.mock_ap_class = self.mocks[1]
        self.mock_logger_class = self.mocks[2]
        
        # Create instance mocks
        self.mock_wifi = MagicMock()
        self.mock_ap = MagicMock()
        self.mock_logger = MagicMock()
        
        self.logger.debug("Configuring mocks")
        # Configure class mocks
        self.mock_wifi_class.return_value = self.mock_wifi
        self.mock_ap_class.return_value = self.mock_ap
        self.mock_logger_class.return_value = self.mock_logger
        
        # Configure success returns
        self.mock_wifi.initialize.return_value = True
        self.mock_ap.initialize.return_value = True
        
        self.logger.debug("Importing NetworkController")
        # Import and create NetworkController
        from src.controllers.network_controller import NetworkController
        self.network = NetworkController()
        self.logger.debug("Setup complete")
    
    def tearDown(self):
        self.logger.debug("Stopping patches")
        for patcher in self.patches:
            patcher.stop()
    
    def test_initialize_success(self):
        self.logger.debug("Testing initialize")
        result = self.network.initialize()
        self.logger.debug(f"Initialize result: {result}")
        self.assertTrue(result)
        self.mock_wifi.initialize.assert_called_once()
        self.mock_ap.initialize.assert_called_once()
    
    def test_wifi_connection(self):
        self.logger.debug("Testing WiFi connection")
        # Setup
        test_ssid = "TestNetwork"
        test_password = "TestPassword"
        self.mock_wifi.connect_to_network.return_value = True
        
        # Test connection
        result = self.network.connect_wifi(test_ssid, test_password)
        self.logger.debug(f"WiFi connection result: {result}")
        
        # Verify
        self.assertTrue(result)
        self.mock_wifi.connect_to_network.assert_called_once_with(test_ssid, test_password)
    
    def test_ap_mode(self):
        # Setup
        test_ssid = "TestAP"
        test_password = "APPassword"
        self.mock_ap.start.return_value = True
        self.mock_ap.stop.return_value = True
        
        # Test AP start
        result = self.network.start_ap_mode(test_ssid, test_password)
        self.assertTrue(result)
        self.assertTrue(self.network.is_ap_mode)
        self.mock_ap.start.assert_called_once_with(test_ssid, test_password)
        
        # Test AP stop
        result = self.network.stop_ap_mode()
        self.assertTrue(result)
        self.assertFalse(self.network.is_ap_mode)
        self.mock_ap.stop.assert_called_once()
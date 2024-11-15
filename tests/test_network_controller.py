import unittest
from unittest.mock import patch, MagicMock, call
import logging
import subprocess
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import NetworkController
from src.controllers.network_controller import NetworkController

class TestNetworkController(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        os.environ['TESTING'] = 'true'
        
        # Create logger mock
        self.logger_mock = MagicMock()
        self.logger_mock.info = MagicMock()
        self.logger_mock.error = MagicMock()
        self.logger_mock.warning = MagicMock()
        
        # Patch the logger
        patcher = patch('logging.getLogger')
        mock_logger = patcher.start()
        mock_logger.return_value = self.logger_mock
        self.addCleanup(patcher.stop)
        
        # Create mock WiFi manager
        self.mock_wifi = MagicMock()
        self.mock_wifi.initialize.return_value = True
        self.mock_wifi.connect_to_network.return_value = True
        self.mock_wifi.is_connected.return_value = True
        self.mock_wifi.cleanup = MagicMock()
        
        # Create mock AP manager
        self.mock_ap = MagicMock()
        self.mock_ap.initialize.return_value = True
        self.mock_ap.start.return_value = True
        self.mock_ap.stop.return_value = True
        self.mock_ap.is_active.return_value = True
        self.mock_ap.is_running.return_value = True
        self.mock_ap.cleanup = MagicMock()
        
        # Create mock config manager
        self.mock_config = MagicMock()
        self.mock_config.get_saved_networks.return_value = {}
        self.mock_config.get_ap_config.return_value = {
            'ssid': 'InternetRadio',
            'password': 'raspberry'
        }
        
        # Create NetworkController instance with mocked dependencies
        self.network_controller = NetworkController(
            config_manager=self.mock_config,
            wifi_manager=self.mock_wifi,
            ap_manager=self.mock_ap
        )
        self.network_controller.initialized = True

    def tearDown(self):
        """Clean up after tests"""
        if 'TESTING' in os.environ:
            del os.environ['TESTING']
        
        # Clean up mocks
        self.mock_wifi.reset_mock()
        self.mock_ap.reset_mock()
        self.mock_config.reset_mock()
        self.logger_mock.reset_mock()

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

    def test_check_and_setup_network_with_saved_networks(self):
        """Test network setup with saved networks"""
        # Setup
        self.mock_wifi.connect_to_network.return_value = True
        self.mock_config.get_saved_networks.return_value = {
            'test_ssid': 'test_password'
        }
        
        # Call the method
        result = self.network_controller.check_and_setup_network()
        
        # Verify
        self.assertTrue(result)
        self.mock_wifi.connect_to_network.assert_called_once_with('test_ssid', 'test_password')
        self.mock_ap.start.assert_not_called()
        self.assertFalse(self.network_controller.is_ap_mode)

    def test_check_and_setup_network_fallback_to_ap(self):
        """Test network setup falling back to AP mode"""
        # Setup mocks
        self.mock_wifi.connect_to_network.return_value = False
        self.mock_config.get_saved_networks.return_value = {}
        self.mock_config.get_ap_config.return_value = {
            'ssid': 'custom_ap',
            'password': 'custom_password'
        }
        
        # Test
        result = self.network_controller.check_and_setup_network()
        
        # Verify
        self.assertTrue(result)
        self.mock_ap.start.assert_called_once_with('custom_ap', 'custom_password')

    def test_check_and_setup_network_no_config(self):
        """Test network setup with no config manager"""
        # Setup
        self.network_controller = NetworkController(
            config_manager=None,
            wifi_manager=self.mock_wifi,
            ap_manager=self.mock_ap
        )
        self.network_controller.initialize()
        self.mock_ap.start.return_value = True
        
        # Call the method
        result = self.network_controller.check_and_setup_network()
        
        # Verify
        self.assertTrue(result)
        self.mock_wifi.connect_to_network.assert_not_called()
        self.mock_ap.start.assert_called_once_with('InternetRadio', 'raspberry')
        self.assertTrue(self.network_controller.is_ap_mode)

    def test_check_and_setup_network_initialization_failure(self):
        """Test network setup with initialization failure"""
        # Setup
        self.network_controller.initialized = False
        
        # Call the method
        result = self.network_controller.check_and_setup_network()
        
        # Verify
        self.assertFalse(result)
        self.mock_wifi.connect_to_network.assert_not_called()
        self.mock_ap.start.assert_not_called()

    def test_ap_mode_status(self):
        """Test both method and property for AP mode status"""
        # Initially not in AP mode
        self.assertFalse(self.network_controller.ap_mode_active)
        self.assertFalse(self.network_controller.is_ap_mode_active())
        
        # Set AP mode
        self.network_controller.is_ap_mode = True
        self.mock_ap.is_active.return_value = True
        
        # Should now be in AP mode
        self.assertTrue(self.network_controller.ap_mode_active)
        self.assertTrue(self.network_controller.is_ap_mode_active())

    def test_start_ap_mode_with_defaults(self):
        """Test starting AP mode with default credentials"""
        # Setup
        self.mock_ap.start.return_value = True
        
        # Call method
        result = self.network_controller.start_ap_mode()
        
        # Verify
        self.assertTrue(result)
        self.mock_ap.start.assert_called_once_with("InternetRadio", "raspberry")
        self.assertTrue(self.network_controller.is_ap_mode)

    def test_start_ap_mode_with_custom_credentials(self):
        """Test starting AP mode with custom credentials"""
        # Setup
        self.mock_ap.start.return_value = True
        
        # Call method
        result = self.network_controller.start_ap_mode("CustomSSID", "CustomPass")
        
        # Verify
        self.assertTrue(result)
        self.mock_ap.start.assert_called_once_with("CustomSSID", "CustomPass")
        self.assertTrue(self.network_controller.is_ap_mode)

    def test_start_ap_mode_no_arguments(self):
        """Test starting AP mode without providing arguments"""
        # Setup
        self.mock_ap.start.return_value = True
        
        # Call method without arguments
        result = self.network_controller.start_ap_mode()
        
        # Verify
        self.assertTrue(result)
        self.mock_ap.start.assert_called_once_with("InternetRadio", "raspberry")
        self.assertTrue(self.network_controller.is_ap_mode)

    def test_monitor_ap_mode(self):
        """Test monitoring AP mode"""
        # Setup
        self.network_controller.is_ap_mode = True
        self.mock_ap.is_active.return_value = False
        
        # Test
        self.network_controller.monitor()
        
        # Verify
        self.mock_ap.is_active.assert_called_once()
        self.mock_ap.start.assert_called_once()

    def test_monitor_wifi_mode(self):
        """Test monitoring WiFi mode"""
        # Setup
        self.network_controller.is_ap_mode = False
        self.mock_wifi.is_connected.return_value = False
        self.mock_wifi.connect_to_network.return_value = True
        self.mock_config.get_saved_networks.return_value = {"test_ssid": "test_pass"}
        
        # Call monitor
        self.network_controller.monitor()
        
        # Verify
        self.mock_wifi.is_connected.assert_called_once()
        self.mock_wifi.connect_to_network.assert_called_once_with("test_ssid", "test_pass")

    def test_monitor_ap_mode_restart(self):
        """Test monitoring AP mode with restart"""
        # Setup
        self.network_controller.is_ap_mode = True
        self.mock_ap.is_active.return_value = False
        
        # Test
        self.network_controller.monitor()
        
        # Verify
        self.mock_ap.is_active.assert_called_once()
        self.mock_ap.start.assert_called_once_with("InternetRadio", "raspberry")
        
        # Verify AP mode is still set
        self.assertTrue(self.network_controller.is_ap_mode)

    def test_monitor_ap_mode_with_defaults(self):
        """Test monitoring AP mode with default parameters"""
        # Setup
        self.network_controller.is_ap_mode = True
        self.mock_ap.is_active.return_value = False
        
        # Test
        self.network_controller.monitor()
        
        # Verify
        self.mock_ap.is_active.assert_called_once()
        self.mock_ap.start.assert_called_once_with("InternetRadio", "raspberry")
        
        # Verify AP mode is still set
        self.assertTrue(self.network_controller.is_ap_mode)

    def test_monitor_wifi_mode_with_fallback(self):
        """Test monitoring WiFi mode with fallback to AP mode"""
        # Setup
        self.network_controller.is_ap_mode = False
        self.mock_wifi.is_connected.return_value = False
        self.mock_wifi.connect_to_network.return_value = False
        self.mock_ap.start.return_value = True
        
        # Call monitor
        self.network_controller.monitor()
        
        # Verify
        self.mock_wifi.is_connected.assert_called_once()
        self.mock_ap.start.assert_called_once_with("InternetRadio", "raspberry")
        self.assertTrue(self.network_controller.is_ap_mode)

if __name__ == '__main__':
    unittest.main()
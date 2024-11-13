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
        self.mock_logger_class.get_logger.return_value = self.mock_logger
        
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
    
    def test_network_setup(self):
        # Setup
        self.mock_wifi.get_saved_networks.return_value = ["Network1", "Network2"]
        self.mock_wifi.connect_to_network.return_value = True
        
        # Test
        result = self.network.check_and_setup_network()
        
        # Verify
        self.assertTrue(result)
        self.mock_wifi.get_saved_networks.assert_called_once()
        self.mock_wifi.connect_to_network.assert_called_once_with("Network1", None)
    
    def test_network_setup_fallback(self):
        # Setup
        self.mock_wifi.get_saved_networks.return_value = []
        self.mock_ap.start.return_value = True
        
        # Test
        result = self.network.check_and_setup_network()
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(self.network.is_ap_mode)
        self.mock_ap.start.assert_called_once()
    
    def test_get_connection_status(self):
        """Test getting connection status"""
        # Setup
        self.mock_wifi.is_connected.return_value = True
        self.mock_wifi.get_current_ssid.return_value = "TestNetwork"
        self.mock_wifi.get_ip.return_value = "192.168.1.100"
        
        # Test normal WiFi mode
        status = self.network.get_connection_status()
        self.assertEqual(status['is_ap_mode'], False)
        self.assertEqual(status['ip_address'], "192.168.1.100")
        self.assertEqual(status['wifi_connected'], True)
        self.assertEqual(status['current_ssid'], "TestNetwork")
        
        # Test AP mode
        self.network.is_ap_mode = True
        self.mock_ap.get_ip.return_value = "192.168.4.1"
        status = self.network.get_connection_status()
        self.assertEqual(status['is_ap_mode'], True)
        self.assertEqual(status['ip_address'], "192.168.4.1")
        self.assertEqual(status['wifi_connected'], False)
        self.assertIsNone(status['current_ssid'])
    
    def test_cleanup(self):
        """Test network cleanup"""
        # Setup
        self.network.is_ap_mode = True
        self.mock_ap.stop.return_value = True
        
        # Test
        self.network.cleanup()
        
        # Verify
        self.mock_ap.stop.assert_called_once()
        self.mock_wifi.cleanup.assert_called_once()
        self.mock_ap.cleanup.assert_called_once()
    
    def test_monitor_network(self):
        """Test network monitoring"""
        # Setup
        self.network.is_ap_mode = True
        self.mock_ap.is_active.return_value = False
        
        # Test
        self.network.monitor_network()
        
        # Verify
        self.mock_ap.is_active.assert_called_once()
        self.mock_ap.start.assert_called_once()
    
    @patch('subprocess.run')
    def test_log_network_status(self, mock_run):
        """Test network status logging"""
        # Setup
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Test output"
        )
        
        # Create a mock logger instance
        mock_logger_instance = MagicMock()
        self.mock_logger_class.get_logger.return_value = mock_logger_instance
        
        # Create a new NetworkController instance to use the mock logger
        from src.controllers.network_controller import NetworkController
        network = NetworkController()
        
        # Test
        network.log_network_status()
        
        # Verify
        self.assertEqual(mock_run.call_count, 6)  # Six different commands
        mock_logger_instance.info.assert_called()  # Check the instance's info method
    
    def test_check_and_setup_network_with_dns(self):
        """Test network setup with DNS configuration"""
        # Setup
        self.mock_wifi.get_saved_networks.return_value = ["Network1"]
        self.mock_wifi.connect_to_network.return_value = True
        self.mock_wifi.configure_dns.return_value = True
        self.mock_wifi.check_dns_resolution.return_value = True
        
        # Test
        result = self.network.check_and_setup_network()
        
        # Verify
        self.assertTrue(result)
        self.mock_wifi.get_saved_networks.assert_called_once()
        self.mock_wifi.connect_to_network.assert_called_once_with("Network1", None)
        self.mock_wifi.configure_dns.assert_called_once()
        self.mock_wifi.check_dns_resolution.assert_called_once()
import unittest
from unittest.mock import patch, MagicMock, call
import logging
import subprocess
import time

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
        self.network_controller = NetworkController()
        self.logger.debug("Setup complete")
    
    def tearDown(self):
        self.logger.debug("Stopping patches")
        for patcher in self.patches:
            patcher.stop()
    
    def test_initialize_success(self):
        self.logger.debug("Testing initialize")
        result = self.network_controller.initialize()
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
        result = self.network_controller.connect_wifi(test_ssid, test_password)
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
        result = self.network_controller.start_ap_mode(test_ssid, test_password)
        self.assertTrue(result)
        self.assertTrue(self.network_controller.is_ap_mode)
        self.mock_ap.start.assert_called_once_with(test_ssid, test_password)
        
        # Test AP stop
        result = self.network_controller.stop_ap_mode()
        self.assertTrue(result)
        self.assertFalse(self.network_controller.is_ap_mode)
        self.mock_ap.stop.assert_called_once()
    
    def test_network_setup(self):
        """Test network setup with single network"""
        # Setup
        test_network = {'ssid': 'Network1', 'password': None}
        self.mock_wifi.get_saved_networks.return_value = [test_network]
        self.mock_wifi.connect_to_network.return_value = True
        self.mock_wifi.configure_dns.return_value = True
        self.mock_wifi.check_dns_resolution.return_value = True
        
        # Mock check_internet_connection
        with patch.object(self.network_controller, 'check_internet_connection', return_value=True):
            # Mock time.sleep to avoid delays
            with patch('time.sleep'):
                # Test
                result = self.network_controller.check_and_setup_network()
                
                # Verify
                self.assertTrue(result)
                self.mock_wifi.get_saved_networks.assert_called_once()
                self.mock_wifi.connect_to_network.assert_called_once_with(test_network['ssid'], test_network['password'])
                self.mock_wifi.configure_dns.assert_called_once()
                self.mock_wifi.check_dns_resolution.assert_called_once()
    
    def test_network_setup_fallback(self):
        # Setup
        self.mock_wifi.get_saved_networks.return_value = []
        self.mock_ap.start.return_value = True
        
        # Test
        result = self.network_controller.check_and_setup_network()
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(self.network_controller.is_ap_mode)
        self.mock_ap.start.assert_called_once()
    
    def test_get_connection_status(self):
        """Test getting connection status"""
        # Setup
        self.mock_wifi.get_connection_info.return_value = {
            'ssid': 'TestNetwork',
            'ip': '192.168.1.100',
            'signal': 70
        }
        
        # Test normal WiFi mode
        status = self.network_controller.get_connection_status()
        self.assertEqual(status['is_ap_mode'], False)
        self.assertEqual(status['ip'], '192.168.1.100')
        self.assertEqual(status['ssid'], 'TestNetwork')
        self.assertEqual(status['signal'], 70)
    
    def test_cleanup(self):
        """Test network cleanup"""
        # Setup
        self.network_controller.is_ap_mode = True
        self.mock_ap.stop.return_value = True
        
        # Test
        self.network_controller.cleanup()
        
        # Verify
        self.mock_ap.stop.assert_called_once()
        self.mock_wifi.cleanup.assert_called_once()
        self.mock_ap.cleanup.assert_called_once()
    
    def test_monitor_network(self):
        """Test network monitoring"""
        # Setup mock config manager
        mock_config = MagicMock()
        mock_config.get_ap_credentials.return_value = ("TestAP", "TestPass")
        self.network_controller.config_manager = mock_config
        
        # Set AP mode
        self.network_controller.is_ap_mode = True
        self.mock_ap.is_active.return_value = False
        
        # Test
        self.network_controller.monitor_network()
        
        # Verify
        self.mock_ap.is_active.assert_called_once()
        self.mock_ap.start.assert_called_once_with("TestAP", "TestPass")
    
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
    
    @patch('time.sleep')  # Prevent actual delays
    @patch('subprocess.run')  # Mock subprocess calls
    def test_check_and_setup_network_with_dns(self, mock_subprocess_run, mock_sleep):
        """Test network setup with DNS configuration"""
        # Mock WiFiManager methods
        self.mock_wifi.get_saved_networks.return_value = [{
            'ssid': 'Network1'
        }]
        self.mock_wifi.connect_to_network.return_value = True
        self.mock_wifi.configure_dns.return_value = True
        self.mock_wifi.check_dns_resolution.return_value = True
        
        # Mock successful ping for internet check
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        
        # Execute
        result = self.network_controller.check_and_setup_network()
        
        # Verify result
        self.assertTrue(result)
        
        # Verify method calls
        self.mock_wifi.get_saved_networks.assert_called_once()
        self.mock_wifi.connect_to_network.assert_called_once_with('Network1', None)
        self.mock_wifi.configure_dns.assert_called_once()
        self.mock_wifi.check_dns_resolution.assert_called_once()
        
        # Verify no sleep was called (since everything succeeded first try)
        mock_sleep.assert_not_called()
        
        # Verify ping was called for internet check
        mock_subprocess_run.assert_called_with(
            ['ping', '-c', '1', '-W', '2', '8.8.8.8'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    
    @patch('subprocess.run')
    def test_check_internet_connection(self, mock_run):
        """Test internet connection check with fallback hosts"""
        # Test successful connection to first host
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.network_controller.check_internet_connection())
        mock_run.assert_called_once()
        
        # Test fallback to second host
        mock_run.reset_mock()
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, 'ping'),  # First host fails
            MagicMock(returncode=0)  # Second host succeeds
        ]
        self.assertTrue(self.network_controller.check_internet_connection())
        self.assertEqual(mock_run.call_count, 2)
        
        # Test all hosts fail
        mock_run.reset_mock()
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ping')
        self.assertFalse(self.network_controller.check_internet_connection())
        self.assertEqual(mock_run.call_count, 3)  # Should try all three hosts
    
    def test_internet_connection_sound_notifications(self):
        """Test sound notifications for internet connection status"""
        # Setup
        mock_audio_manager = MagicMock()
        self.network_controller.audio_manager = mock_audio_manager
        
        # Test successful connection
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            self.network_controller.check_internet_connection()
            mock_audio_manager.play_sound.assert_called_once_with('wifi.wav')
        
        # Test failed connection
        mock_audio_manager.reset_mock()
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'ping')
            self.network_controller.check_internet_connection()
            mock_audio_manager.play_sound.assert_called_once_with('noWifi.wav')
    
    def test_check_and_setup_network_with_internet_check(self):
        """Test network setup with internet connectivity verification"""
        # Setup
        self.mock_wifi.get_saved_networks.return_value = ["Network1"]
        self.mock_wifi.connect_to_network.return_value = True
        self.mock_wifi.configure_dns.return_value = True
        self.mock_wifi.check_dns_resolution.return_value = True
        
        # Test case 1: WiFi connects and internet is available
        with patch.object(self.network_controller, 'check_internet_connection') as mock_check:
            mock_check.return_value = True
            result = self.network_controller.check_and_setup_network()
            
            # Verify the result
            self.assertTrue(result)
            mock_check.assert_called_once()
            self.mock_ap.start.assert_not_called()
    
    def test_check_and_setup_network_with_retries(self):
        """Test network setup with retry mechanism"""
        # Setup
        self.mock_wifi.get_saved_networks.return_value = ["Network1"]
        self.mock_wifi.connect_to_network.return_value = True  # Always succeed connection
        self.mock_wifi.configure_dns.return_value = True
        self.mock_wifi.check_dns_resolution.return_value = True
        
        # Mock check_internet_connection to fail twice then succeed
        with patch.object(self.network_controller, 'check_internet_connection') as mock_check:
            mock_check.side_effect = [False, False, True]
            
            # Mock time.sleep to avoid actual delays in test
            with patch('time.sleep') as mock_sleep:
                result = self.network_controller.check_and_setup_network()
                
                # Print actual calls for debugging
                print(f"Actual sleep calls: {mock_sleep.mock_calls}")
                print(f"Actual check calls: {mock_check.mock_calls}")
                
                # Verify the result
                self.assertTrue(result)
                self.assertEqual(mock_check.call_count, 3)  # Should be called three times
                
                # Verify sleep was called with correct delays
                self.assertEqual(mock_sleep.call_count, 2)  # Should be called twice
                mock_sleep.assert_has_calls([
                    call(5),  # First retry
                    call(5)   # Second retry
                ], any_order=True)  # Order doesn't matter as long as both delays are 5
    
    def test_monitor_network_ap_mode_restart(self):
        """Test network monitoring when AP mode needs restart"""
        # Setup
        self.network_controller.is_ap_mode = True
        self.mock_ap.is_active.return_value = False
        
        # Configure config manager mock
        mock_config = MagicMock()
        mock_config.get_ap_credentials.return_value = ("TestAP", "TestPass")
        self.network_controller.config_manager = mock_config
        
        # Test
        self.network_controller.monitor_network()
        
        # Verify
        self.mock_ap.is_active.assert_called_once()
        self.mock_ap.start.assert_called_once_with("TestAP", "TestPass")
    
    def test_check_network_manager(self):
        """Test checking NetworkManager status"""
        # Mock subprocess.run
        with patch('subprocess.run') as mock_run:
            # Test when NetworkManager is active
            mock_run.return_value.stdout = 'active\n'
            self.assertTrue(self.network_controller._check_network_manager())
            
            # Test when NetworkManager is inactive
            mock_run.return_value.stdout = 'inactive\n'
            self.assertFalse(self.network_controller._check_network_manager())
            
            # Test when command fails
            mock_run.side_effect = Exception("Command failed")
            self.assertFalse(self.network_controller._check_network_manager())
    
    def test_monitor_network_without_network_manager(self):
        """Test monitor_network behavior when NetworkManager is not running"""
        with patch.object(self.network_controller, '_check_network_manager', return_value=False):
            self.network_controller.monitor_network()
            # Verify it logs the error
            self.mock_logger.error.assert_called_with("NetworkManager is not running")
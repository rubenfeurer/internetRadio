import unittest
from unittest.mock import patch, MagicMock
from src.network.wifi_manager import WiFiManager
import socket
import os

class TestWiFiManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create logger mock with proper call tracking
        self.logger_mock = MagicMock()
        self.logger_mock.info = MagicMock()
        self.logger_mock.error = MagicMock()
        
        # Patch the logger
        patcher = patch('logging.getLogger')
        mock_logger = patcher.start()
        mock_logger.return_value = self.logger_mock
        self.addCleanup(patcher.stop)
        
        # Create WiFiManager instance
        self.wifi_manager = WiFiManager()
    
    @patch('subprocess.run')
    def test_get_saved_networks(self, mock_run):
        # Mock the nmcli command output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""NAME                UUID                                  TYPE      DEVICE 
TestNetwork1         f7148ade-534a-480d-92f5-5d402816dc17  wifi      wlan0  
TestNetwork2         f815578d-bd33-47c1-b3a8-6998815b2bd1  wifi      --     
Wired connection 1   d5ce7973-f25b-33c5-bc00-50dc57c4800d  ethernet  --     """
        )
        
        networks = self.wifi_manager.get_saved_networks()
        self.assertEqual(networks, ['TestNetwork1', 'TestNetwork2'])
    
    @patch('subprocess.run')
    def test_scan_networks(self, mock_run):
        # Mock the iwlist scan output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""Cell 01 - Address: 00:11:22:33:44:55
                    Quality=70/70  Signal level=-30 dBm  
                    ESSID:"TestNetwork1"
                  Cell 02 - Address: 11:22:33:44:55:66
                    Quality=50/70  Signal level=-60 dBm  
                    ESSID:"TestNetwork2"
                """
        )
        
        networks = self.wifi_manager.scan_networks()
        self.assertEqual(len(networks), 2)
        self.assertEqual(networks[0]['ssid'], 'TestNetwork1')
        self.assertEqual(networks[1]['ssid'], 'TestNetwork2')
    
    @patch('subprocess.run')
    def test_connect_to_network_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(
            self.wifi_manager.connect_to_network("TestNetwork", "password123")
        )
    
    @patch('subprocess.run')
    def test_connect_to_network_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Connection failed"
        )
        self.assertFalse(
            self.wifi_manager.connect_to_network("TestNetwork", "password123")
        )
    
    @patch('subprocess.run')
    def test_is_connected(self, mock_run):
        # Test connected state
        mock_run.return_value = MagicMock(
            stdout='wlan0     IEEE 802.11  ESSID:"TestNetwork"  Mode:Managed'
        )
        self.assertTrue(self.wifi_manager.is_connected())
        
        # Test disconnected state
        mock_run.return_value = MagicMock(
            stdout='wlan0     IEEE 802.11  ESSID:off/any  Mode:Managed'
        )
        self.assertFalse(self.wifi_manager.is_connected())
    
    @patch('subprocess.run')
    def test_get_current_network(self, mock_run):
        # Test with connected network
        mock_run.return_value = MagicMock(
            stdout='wlan0     IEEE 802.11  ESSID:"TestNetwork"  Mode:Managed'
        )
        self.assertEqual(self.wifi_manager.get_current_network(), 'TestNetwork')
        
        # Test with no network
        mock_run.return_value = MagicMock(
            stdout='wlan0     IEEE 802.11  ESSID:off/any  Mode:Managed'
        )
        self.assertIsNone(self.wifi_manager.get_current_network())
    
    @patch('subprocess.run')
    def test_disconnect(self, mock_run):
        # Test successful disconnect
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.wifi_manager.disconnect())
        
        # Test failed disconnect
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(self.wifi_manager.disconnect())
    
    @patch('subprocess.run')
    def test_initialize(self, mock_run):
        # Test successful initialization
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.wifi_manager.initialize())
        
        # Test failed initialization
        mock_run.side_effect = Exception("Failed to initialize")
        self.assertFalse(self.wifi_manager.initialize())
    
    @patch('subprocess.run')
    @patch('os.path.islink')
    def test_configure_dns(self, mock_islink, mock_run):
        """Test DNS configuration"""
        # Setup
        mock_islink.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        # Test
        self.assertTrue(self.wifi_manager.configure_dns())
        
        # Verify
        self.assertEqual(mock_run.call_count, 3)  # rm, echo, chmod
        mock_run.assert_any_call(['sudo', 'rm', '/etc/resolv.conf'], 
                                capture_output=True, text=True)
        mock_run.assert_any_call(
            ['sudo', 'bash', '-c', 'echo "nameserver 8.8.8.8\nnameserver 8.8.4.4\n" > /etc/resolv.conf'],
            capture_output=True, text=True)
        mock_run.assert_any_call(['sudo', 'chmod', '644', '/etc/resolv.conf'], 
                                capture_output=True, text=True)
    
    @patch('socket.gethostbyname')
    def test_check_dns_resolution(self, mock_gethostbyname):
        """Test DNS resolution check"""
        # Test successful DNS resolution
        mock_gethostbyname.return_value = '142.250.180.78'
        self.assertTrue(self.wifi_manager.check_dns_resolution())
        
        # Test failed DNS resolution
        mock_gethostbyname.side_effect = socket.gaierror
        self.assertFalse(self.wifi_manager.check_dns_resolution())
    
    @patch('subprocess.run')
    def test_cleanup(self, mock_run):
        """Test WiFi cleanup"""
        # Configure mock
        mock_run.return_value = MagicMock(returncode=0)
        
        # Execute cleanup
        self.wifi_manager.cleanup()
        
        # Verify
        calls = mock_run.call_args_list
        self.assertTrue(any('wpa_supplicant' in str(call) for call in calls))
        self.assertTrue(any('wlan0' in str(call) for call in calls))
        self.logger_mock.info.assert_any_call("Cleaning up WiFi resources...")

if __name__ == '__main__':
    unittest.main() 
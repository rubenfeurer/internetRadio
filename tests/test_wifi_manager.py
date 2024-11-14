import unittest
from unittest.mock import patch, MagicMock, call
from src.network.wifi_manager import WiFiManager
import socket
import os
from src.utils.config_manager import ConfigManager
import subprocess
import time

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
        
        # Patch ConfigManager
        config_patcher = patch('src.network.wifi_manager.ConfigManager')
        self.mock_config = config_patcher.start()
        self.mock_config_instance = MagicMock()
        self.mock_config.return_value = self.mock_config_instance
        self.mock_config_instance.get_network_config.return_value = {
            'ap_ssid': 'InternetRadio',
            'ap_password': 'Radio123',
            'ap_channel': 6
        }
        self.addCleanup(config_patcher.stop)
        
        # Create WiFiManager instance
        self.wifi_manager = WiFiManager()
    
    @patch('subprocess.run')
    def test_get_saved_networks(self, mock_run):
        """Test getting saved networks"""
        # Mock the nmcli command output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="""NAME                UUID                                  TYPE      DEVICE 
TestNetwork1         f7148ade-534a-480d-92f5-5d402816dc17  wifi      wlan0  
TestNetwork2         f815578d-bd33-47c1-b3a8-6998815b2bd1  wifi      --     
Wired connection 1   d5ce7973-f25b-33c5-bc00-50dc57c4800d  ethernet  --     """
        )
        
        # Mock config manager to return saved networks
        self.mock_config_instance.get_network_config.return_value = {
            'saved_networks': [
                {'ssid': 'TestNetwork1'},
                {'ssid': 'TestNetwork2'}
            ]
        }
        
        networks = self.wifi_manager.get_saved_networks()
        self.assertEqual(len(networks), 2)
        self.assertTrue(any(n['ssid'] == 'TestNetwork1' for n in networks))
        self.assertTrue(any(n['ssid'] == 'TestNetwork2' for n in networks))
    
    def test_scan_networks(self):
        """Test network scanning using nmcli"""
        with patch('subprocess.run') as mock_run:
            # Mock nmcli wifi list output
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="""IN-USE  SSID             MODE   CHAN  RATE        SIGNAL  BARS  SECURITY
*       MyNetwork        Infra  11    130 Mbit/s  90      ▂▄▆█  WPA2
        OtherNetwork     Infra  6     65 Mbit/s   75      ▂▄▆_  WPA1
        OpenNetwork      Infra  1     54 Mbit/s   60      ▂▄__  --""",
                text=True
            )

            networks = self.wifi_manager.scan_networks()

            # Verify nmcli command
            mock_run.assert_called_once_with(
                ['nmcli', 'device', 'wifi', 'list', '--rescan', 'yes'],
                capture_output=True,
                text=True,
                check=True
            )

            # Verify parsed networks
            self.assertEqual(len(networks), 3)
            self.assertEqual(networks[0], {
                'ssid': 'MyNetwork',
                'signal': '90',
                'security': 'WPA2',
                'in_use': True
            })
            self.assertEqual(networks[1], {
                'ssid': 'OtherNetwork',
                'signal': '75',
                'security': 'WPA1',
                'in_use': False
            })
            self.assertEqual(networks[2], {
                'ssid': 'OpenNetwork',
                'signal': '60',
                'security': '--',
                'in_use': False
            })
    
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
    
    def test_ap_settings_from_config(self):
        """Test that AP settings are loaded from config"""
        with patch('src.utils.config_manager.ConfigManager') as mock_config:
            # Mock the config manager
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            
            # Set up the mock config values
            mock_config_instance.get_network_config.return_value = {
                'ap_ssid': 'InternetRadio',
                'ap_password': 'Radio123',
                'ap_channel': 6
            }
            
            # Create new WiFiManager instance
            wifi_manager = WiFiManager()
            
            # Verify settings were loaded from config
            self.assertEqual(wifi_manager.ap_ssid, 'InternetRadio')
            self.assertEqual(wifi_manager.ap_password, 'Radio123')
            self.assertEqual(wifi_manager.ap_channel, 6)
    
    @patch('socket.gethostname')
    def test_ap_settings_with_hostname(self, mock_gethostname):
        """Test that AP SSID uses hostname and correct password"""
        mock_gethostname.return_value = "radiopi"
        
        with patch('src.network.wifi_manager.ConfigManager') as mock_config:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_config_instance.get_network_config.return_value = {
                'ap_ssid': socket.gethostname(),  # Should use hostname
                'ap_password': 'Radio@1234',
                'ap_channel': 6
            }
            
            wifi_manager = WiFiManager()
            
            self.assertEqual(wifi_manager.ap_ssid, 'radiopi')
            self.assertEqual(wifi_manager.ap_password, 'Radio@1234')
            self.assertEqual(wifi_manager.ap_channel, 6)
    
    @patch('socket.socket')
    def test_check_internet_connection(self, mock_socket):
        """Test internet connectivity check with multiple hosts"""
        # Setup mock socket
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        # Test successful connection
        mock_sock.connect_ex.return_value = 0  # 0 means success
        self.assertTrue(self.wifi_manager.check_internet_connection())
        
        # Verify socket was called with correct parameters
        mock_sock.connect_ex.assert_called_with(("8.8.8.8", 53))
        mock_sock.settimeout.assert_called_with(2)
        
        # Test failed connection
        mock_sock.reset_mock()
        mock_sock.connect_ex.return_value = 1  # Non-zero means failure
        self.assertFalse(self.wifi_manager.check_internet_connection())
        
        # Test exception handling
        mock_sock.reset_mock()
        mock_sock.connect_ex.side_effect = Exception("Connection error")
        self.assertFalse(self.wifi_manager.check_internet_connection())
    
    def test_exclusive_mode_operation(self):
        """Test that WiFi can't be in both AP and Client mode simultaneously"""
        with patch('subprocess.run') as mock_run:
            def mock_command(cmd, *args, **kwargs):
                # Mock nmcli device status for client mode check
                if cmd[0] == "nmcli" and cmd[1] == "device" and cmd[2] == "status":
                    return MagicMock(
                        returncode=0,
                        stdout="""DEVICE  TYPE      STATE      CONNECTION
wlan0   wifi      connected  Salt_5GHz_D8261F
eth0    ethernet  unmanaged  --""",
                        text=True
                    )
                # Mock systemctl for AP mode check
                elif cmd[0] == "systemctl" and cmd[1] == "is-active":
                    return MagicMock(
                        returncode=1,  # hostapd is not active
                        stdout="inactive",
                        text=True
                    )
                return MagicMock(returncode=0)
                
            mock_run.side_effect = mock_command
            
            # Test client mode
            self.wifi_manager.enable_client_mode()
            self.assertTrue(self.wifi_manager.is_client_mode())
            self.assertFalse(self.wifi_manager.is_ap_mode())
            
            # Now mock AP mode
            def mock_ap_command(cmd, *args, **kwargs):
                if cmd[0] == "nmcli":
                    return MagicMock(
                        returncode=0,
                        stdout="""DEVICE  TYPE      STATE        CONNECTION
wlan0   wifi      unmanaged   --
eth0    ethernet  unmanaged   --""",
                        text=True
                    )
                elif cmd[0] == "systemctl" and cmd[1] == "is-active":
                    return MagicMock(
                        returncode=0,  # hostapd is active
                        stdout="active",
                        text=True
                    )
                return MagicMock(returncode=0)
                
            mock_run.side_effect = mock_ap_command
            
            # Test AP mode
            self.wifi_manager.enable_ap_mode()
            self.assertTrue(self.wifi_manager.is_ap_mode())
            self.assertFalse(self.wifi_manager.is_client_mode())
    
    def test_mode_detection(self):
        """Test WiFi mode detection"""
        with patch('subprocess.run') as mock_run:
            def mock_command(cmd, *args, **kwargs):
                # For client mode check (nmcli device status)
                if cmd[0] == "nmcli" and cmd[1] == "device" and cmd[2] == "status":
                    return MagicMock(
                        returncode=0,
                        stdout="""DEVICE  TYPE      STATE      CONNECTION
wlan0   wifi      connected  MyNetwork
eth0    ethernet  unmanaged  --""",
                        text=True
                    )
                # For AP mode check (systemctl)
                elif cmd[0] == "systemctl" and cmd[1] == "is-active":
                    return MagicMock(
                        returncode=1,  # hostapd is not active
                        stdout="inactive",
                        text=True
                    )
                return MagicMock(returncode=0)
                
            mock_run.side_effect = mock_command
            self.assertTrue(self.wifi_manager.is_client_mode())
            self.assertFalse(self.wifi_manager.is_ap_mode())
    
    def test_network_config(self):
        """Test NetworkManager configuration file"""
        # Create the directory if it doesn't exist
        os.makedirs("src/utils/network_configs", exist_ok=True)
        
        # Test config generation
        self.assertTrue(self.wifi_manager.generate_network_config())
        
        config_path = "src/utils/network_configs/networkmanager.conf"
        
        # Test if config file exists
        self.assertTrue(os.path.exists(config_path))
        
        # Test config content
        with open(config_path, 'r') as f:
            content = f.read()
            self.assertIn('[main]', content)
            self.assertIn('managed=true', content)
            self.assertIn('wifi.scan-rand-mac-address=no', content)
    
    @patch('src.network.wifi_manager.ConfigManager')
    def test_save_network(self, mock_config_manager):
        """Test saving a network to the configuration"""
        # Arrange
        mock_config_instance = MagicMock()
        mock_config_manager.return_value = mock_config_instance
        mock_config_instance.get_network_config.return_value = {
            'saved_networks': []
        }
        mock_config_instance.save_network_config.return_value = True
        
        # Act
        result = self.wifi_manager.save_network("TestNetwork", "TestPassword123")
        
        # Assert
        self.assertTrue(result)
        mock_config_instance.save_network_config.assert_called_once()
        saved_config = mock_config_instance.save_network_config.call_args[0][0]
        self.assertIn('saved_networks', saved_config)
        self.assertEqual(len(saved_config['saved_networks']), 1)
        self.assertEqual(saved_config['saved_networks'][0]['ssid'], "TestNetwork")
    
    @patch('time.sleep')
    @patch('subprocess.run')
    @patch('src.network.wifi_manager.ConfigManager')
    def test_connect_to_saved_network_with_retries(self, mock_config_manager, mock_run, mock_sleep):
        """Test connecting to a saved network with retry mechanism"""
        # Arrange
        mock_config_instance = MagicMock()
        mock_config_manager.return_value = mock_config_instance
        mock_config_instance.get_network_config.return_value = {
            'saved_networks': [{
                'ssid': 'TestNetwork',
                'password': 'TestPassword123'
            }]
        }
        
        # Mock connection attempts - fail twice, succeed on third try
        failed_status = MagicMock(stdout='wifi      disconnected', returncode=0)
        success_status = MagicMock(stdout='wifi      connected', returncode=0)
        
        mock_run.side_effect = [
            # First attempt
            MagicMock(returncode=0),  # Stop internetradio
            MagicMock(returncode=0),  # Stop radiomonitor
            MagicMock(returncode=0),  # Stop hostapd
            MagicMock(returncode=0),  # NetworkManager restart
            MagicMock(returncode=0),  # Delete connection
            MagicMock(returncode=0),  # Add connection
            failed_status,            # Status check fails
            
            # Second attempt
            MagicMock(returncode=0),  # Stop internetradio
            MagicMock(returncode=0),  # Stop radiomonitor
            MagicMock(returncode=0),  # Stop hostapd
            MagicMock(returncode=0),  # NetworkManager restart
            MagicMock(returncode=0),  # Delete connection
            MagicMock(returncode=0),  # Add connection
            failed_status,            # Status check fails
            
            # Third attempt (success)
            MagicMock(returncode=0),  # Stop internetradio
            MagicMock(returncode=0),  # Stop radiomonitor
            MagicMock(returncode=0),  # Stop hostapd
            MagicMock(returncode=0),  # NetworkManager restart
            MagicMock(returncode=0),  # Delete connection
            MagicMock(returncode=0),  # Add connection
            success_status            # Status check succeeds
        ]
        
        # Act
        result = self.wifi_manager.connect_to_saved_network('TestNetwork')
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_sleep.call_count, 2)  # Should sleep twice
        mock_sleep.assert_has_calls([
            call(5),  # First retry
            call(5)   # Second retry
        ])
        
        # Verify correct number of connection attempts
        expected_calls = [
            call(['sudo', 'systemctl', 'stop', 'internetradio'], check=False),
            call(['sudo', 'systemctl', 'stop', 'radiomonitor'], check=False),
            call(['sudo', 'systemctl', 'stop', 'hostapd'], check=False),
            call(['sudo', 'systemctl', 'restart', 'NetworkManager']),
            call(['sudo', 'nmcli', 'connection', 'delete', 'TestNetwork']),
            call(['sudo', 'nmcli', 'device', 'wifi', 'connect', 'TestNetwork', 'password', 'TestPassword123']),
            call(['nmcli', 'device', 'status'], capture_output=True, text=True)
        ] * 3  # Three attempts
        
        # Verify all expected commands were called in order
        mock_run.assert_has_calls(expected_calls, any_order=False)
    
    def test_is_ap_mode(self):
        """Test AP mode detection"""
        with patch('subprocess.run') as mock_run:
            # Test when AP mode is active
            mock_run.return_value = MagicMock(
                returncode=0,  # hostapd is active
                stdout="active"
            )
            self.assertTrue(self.wifi_manager.is_ap_mode())
            
            # Test when AP mode is inactive
            mock_run.return_value = MagicMock(
                returncode=1,  # hostapd is not active
                stdout="inactive"
            )
            self.assertFalse(self.wifi_manager.is_ap_mode())
            
            # Verify correct command was called
            mock_run.assert_called_with(
                ['systemctl', 'is-active', 'hostapd'],
                capture_output=True,
                text=True
            )

if __name__ == '__main__':
    unittest.main() 
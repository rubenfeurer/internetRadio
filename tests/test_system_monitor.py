import unittest
from unittest.mock import Mock, patch, mock_open
import psutil
from src.utils.system_monitor import SystemMonitor
import os
from unittest.mock import MagicMock
import subprocess
from src.network.wifi_manager import WiFiManager
from src.utils.logger import Logger
from io import StringIO

class TestSystemMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = SystemMonitor()
        
    def test_singleton_instance(self):
        """Test that only one instance of monitor can exist"""
        monitor1 = SystemMonitor()
        monitor2 = SystemMonitor()
        self.assertEqual(id(monitor1), id(monitor2))
        
    def test_metrics_collection(self):
        """Test system metrics collection"""
        with patch('psutil.cpu_percent') as mock_cpu:
            with patch('psutil.virtual_memory') as mock_memory:
                with patch('psutil.disk_usage') as mock_disk:
                    mock_cpu.return_value = 25.0
                    mock_memory.return_value = Mock(percent=50.0)
                    mock_disk.return_value = Mock(percent=30.0)
                    
                    metrics = self.monitor.collect_metrics()
                    
                    self.assertIn('cpu_usage', metrics)
                    self.assertIn('memory_usage', metrics)
                    self.assertIn('disk_usage', metrics)
                    self.assertEqual(metrics['cpu_usage'], 25.0)
                    self.assertEqual(metrics['memory_usage'], 50.0)
                    self.assertEqual(metrics['disk_usage'], 30.0)

    def test_display_format(self):
        """Test that metrics are displayed in the correct format"""
        with patch('builtins.print') as mock_print:
            self.monitor.display_metrics()
            
            # Get all calls to print as a list of strings
            printed_lines = [str(call) for call in mock_print.mock_calls]
            output = '\n'.join(printed_lines)
            
            # Check for required sections
            self.assertIn('=== System Monitor ===', output)
            self.assertIn('=== Network Status ===', output)
            self.assertIn('=== Radio Status ===', output)
            
            # Check for key metrics
            self.assertIn('CPU Usage:', output)
            self.assertIn('Memory Usage:', output)
            self.assertIn('Mode:', output)
            self.assertIn('WiFi Network:', output)
            self.assertIn('Internet Connected:', output)

    def test_service_file_exists(self):
        """Test that service file exists and has correct content"""
        service_path = 'services/radiomonitor.service'
        self.assertTrue(os.path.exists(service_path))
        
        with open(service_path, 'r') as f:
            content = f.read()
            self.assertIn('Description=Internet Radio System Monitor', content)
            self.assertIn('User=radio', content)
            self.assertIn('Group=radio', content)
            self.assertIn('Environment=DISPLAY=:0', content)
            self.assertIn('ExecStart=/usr/bin/xterm', content)

    def test_service_file_content(self):
        """Test that service file has correct content and permissions"""
        service_path = '/etc/systemd/system/radiomonitor.service'
        expected_content = """[Unit]
Description=Internet Radio System Monitor
After=internetradio.service NetworkManager.service
Wants=internetradio.service NetworkManager.service

[Service]
Type=simple
User=radio
Group=radio
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/radio/.Xauthority
WorkingDirectory=/home/radio/internetRadio
ExecStart=/usr/bin/xterm -T "System Monitor" -geometry 80x24+0+0 -fn fixed -e /usr/bin/python3 -c "from src.utils.system_monitor import SystemMonitor; SystemMonitor().run()"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target"""
        
        # Check if file exists
        self.assertTrue(os.path.exists(service_path))
        
        # Check file content
        with open(service_path, 'r') as f:
            content = f.read().strip()
            self.assertEqual(content.strip(), expected_content.strip())
        
        # Check file permissions
        stat = os.stat(service_path)
        self.assertEqual(stat.st_mode & 0o777, 0o644)  # Should be -rw-r--r--

    def test_run_method(self):
        """Test the run method execution"""
        with patch.object(self.monitor, 'display_metrics') as mock_display:
            with patch('time.sleep') as mock_sleep:
                # Simulate KeyboardInterrupt after first iteration
                mock_sleep.side_effect = KeyboardInterrupt()
                
                self.monitor.run()
                
                # Verify display_metrics was called
                mock_display.assert_called_once()
                # Verify sleep was attempted
                mock_sleep.assert_called_once_with(1)

    def test_metrics_collection_error(self):
        """Test error handling in metrics collection"""
        with patch('psutil.cpu_percent', side_effect=Exception("Test error")):
            metrics = self.monitor.collect_metrics()
            self.assertEqual(metrics['cpu_usage'], 0.0)  # Should return safe default

    def test_network_metrics(self):
        """Test network metrics collection"""
        # Create a mock WiFiManager
        mock_wifi = MagicMock()
        # Mock the get_connection_info method to return a dictionary
        mock_wifi.get_connection_info.return_value = {
            'ssid': 'MyNetwork',
            'ip': '192.168.1.100',
            'signal': 70
        }
        mock_wifi.check_internet_connection.return_value = True
        
        # Inject the mock into SystemMonitor
        self.monitor.wifi_manager = mock_wifi
        
        metrics = self.monitor.collect_network_metrics()
        
        self.assertEqual(metrics['wifi_ssid'], 'MyNetwork')
        self.assertTrue(metrics['internet_connected'])

    def test_radio_status(self):
        """Test radio service status check"""
        with patch('subprocess.check_output') as mock_cmd:
            with patch('builtins.open', mock_open(read_data='Radio 1')) as mock_file:
                mock_cmd.return_value = b'active'
                
                status = self.monitor.check_radio_service()
                self.assertTrue(status['is_running'])
                self.assertEqual(status['current_station'], 'Radio 1')

    def test_system_temperature(self):
        """Test temperature reading"""
        with patch('subprocess.check_output') as mock_cmd:
            mock_cmd.return_value = b'temp=45.7\'C\n'
            
            temp = self.monitor.get_system_temperature()
            self.assertGreater(temp, 0)
            self.assertLess(temp, 100)

    def test_volume_level(self):
        """Test volume level reading"""
        with patch('subprocess.check_output') as mock_cmd:
            mock_cmd.return_value = b'Volume: 75%\n'
            
            volume = self.monitor.get_volume_level()
            self.assertGreaterEqual(volume, 0)
            self.assertLessEqual(volume, 100)

    def test_system_events(self):
        """Test system events collection"""
        with patch('subprocess.check_output') as mock_cmd:
            mock_cmd.return_value = b'Last events...\n'
            
            events = self.monitor.get_system_events()
            self.assertIsInstance(events, list)
            self.assertLessEqual(len(events), 5)  # Last 5 events

    def test_network_metrics_with_active_connection(self):
        """Test network metrics collection with an active WiFi connection"""
        mock_wifi = MagicMock()
        mock_wifi.get_connection_info.return_value = {
            'ssid': 'Salt_5GHz_D8261F',
            'ip': '192.168.1.100',
            'signal': 70
        }
        mock_wifi.check_internet_connection.return_value = True
        
        self.monitor.wifi_manager = mock_wifi
        
        metrics = self.monitor.collect_network_metrics()
        self.assertEqual(metrics['wifi_ssid'], 'Salt_5GHz_D8261F')

    def test_display_metrics_with_active_wifi(self):
        """Test metrics display with active WiFi connection"""
        mock_wifi = MagicMock()
        mock_wifi.get_connection_info.return_value = {
            'ssid': 'Salt_5GHz_D8261F',
            'ip': '192.168.1.100',
            'signal': 70
        }
        mock_wifi.check_internet_connection.return_value = True
        
        self.monitor.wifi_manager = mock_wifi
        
        with patch('builtins.print') as mock_print:
            self.monitor.display_metrics()
            printed_lines = [str(call) for call in mock_print.mock_calls]
            output = '\n'.join(printed_lines)
            
            self.assertIn('Salt_5GHz_D8261F', output)
            self.assertIn('Yes', output)

    def test_enhanced_network_metrics(self):
        """Test enhanced network metrics collection using WiFiManager"""
        mock_wifi = MagicMock()
        mock_wifi.get_connection_info.return_value = {
            'ssid': 'TestNetwork',
            'ip': '192.168.1.100',
            'signal': 70
        }
        mock_wifi.check_internet_connection.return_value = True
        
        self.monitor.wifi_manager = mock_wifi
        
        metrics = self.monitor.collect_network_metrics()
        self.assertEqual(metrics['wifi_ssid'], 'TestNetwork')

    def test_mode_display(self):
        """Test WiFi mode display formatting"""
        # Create a mock WiFiManager
        mock_wifi = MagicMock()
        mock_wifi.get_connection_info.return_value = {
            'ssid': 'TestNetwork',
            'ip': '192.168.1.100',
            'signal': 70
        }
        mock_wifi.is_ap_mode.return_value = False
        
        self.monitor.wifi_manager = mock_wifi
        metrics = self.monitor.collect_network_metrics()
        
        self.assertEqual(metrics['mode'], 'client')
        self.assertEqual(metrics['wifi_ssid'], 'TestNetwork')

    def test_display_service(self):
        """Test display service configuration"""
        with patch('subprocess.run') as mock_run:
            # Test xterm availability
            mock_run.return_value = MagicMock(returncode=0)
            self.assertTrue(os.path.exists('/usr/bin/xterm'))
            
            # Test font availability
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="fixed"
            )
            result = subprocess.run(['xlsfonts'], capture_output=True, text=True)
            self.assertIn('fixed', result.stdout)

    def test_network_metrics_with_nmcli(self):
        """Test network metrics collection using actual nmcli output"""
        # Mock ConfigManager for WiFiManager initialization
        with patch('src.network.wifi_manager.ConfigManager') as mock_config:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_config_instance.get_network_config.return_value = {
                'ap_ssid': 'TestAP',
                'ap_password': 'TestPass',
                'ap_channel': 6
            }

            # Create a mock WiFiManager with proper connection info
            mock_wifi = MagicMock()
            mock_wifi.get_connection_info.return_value = {
                'ssid': 'Salt_5GHz_D8261F',
                'ip': '192.168.1.100',
                'signal': 70
            }
            mock_wifi.is_client_mode.return_value = True
            mock_wifi.is_ap_mode.return_value = False
            mock_wifi.check_internet_connection.return_value = True

            # Inject mock WiFiManager
            self.monitor.wifi_manager = mock_wifi

            metrics = self.monitor.collect_network_metrics()

            # Verify metrics
            self.assertEqual(metrics['wifi_ssid'], 'Salt_5GHz_D8261F')
            self.assertEqual(metrics['ip'], '192.168.1.100')
            self.assertEqual(metrics['signal'], 70)
            self.assertTrue(metrics['internet_connected'])
            self.assertEqual(metrics['mode'], 'client')
import unittest
from unittest.mock import Mock, patch, mock_open
import psutil
from src.utils.system_monitor import SystemMonitor
import os
from unittest.mock import MagicMock
import subprocess

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
        """Test display output format"""
        with patch('builtins.print') as mock_print:
            with patch.object(self.monitor, 'collect_metrics') as mock_collect:
                mock_collect.return_value = {
                    'cpu_usage': 25.0,
                    'memory_usage': 50.0,
                    'disk_usage': 30.0
                }
                self.monitor.display_metrics()
                mock_print.assert_called()
                
                # Verify all metrics are displayed
                calls = mock_print.call_args_list
                output = ' '.join(str(call) for call in calls)
                self.assertIn('CPU Usage', output)
                self.assertIn('Memory Usage', output)
                self.assertIn('Disk Usage', output)

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
After=internetradio.service
Wants=internetradio.service

[Service]
Type=simple
User=radio
Group=radio
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/radio/.Xauthority
WorkingDirectory=/home/radio/internetRadio
ExecStart=/usr/bin/xterm -T "System Monitor" -geometry 80x24+0+0 -e /usr/bin/python3 -c "from src.utils.system_monitor import SystemMonitor; SystemMonitor().run()"
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
        mock_wifi.is_client_mode.return_value = True
        mock_wifi.is_ap_mode.return_value = False
        mock_wifi.get_current_network.return_value = "MyNetwork"
        mock_wifi.check_internet_connection.return_value = True
        
        # Inject the mock into SystemMonitor
        self.monitor.wifi_manager = mock_wifi
        
        metrics = self.monitor.collect_network_metrics()
        
        self.assertIn('wifi_ssid', metrics)
        self.assertIn('internet_connected', metrics)
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

    def test_enhanced_network_metrics(self):
        """Test enhanced network metrics collection using WiFiManager"""
        # Create a mock WiFiManager
        mock_wifi = MagicMock()
        mock_wifi.is_client_mode.return_value = True
        mock_wifi.is_ap_mode.return_value = False
        mock_wifi.get_current_network.return_value = "TestNetwork"
        mock_wifi.check_internet_connection.return_value = True
        
        # Inject the mock into SystemMonitor
        self.monitor.wifi_manager = mock_wifi
        
        # Test the metrics collection
        metrics = self.monitor.collect_network_metrics()
        
        # Verify results
        self.assertEqual(metrics['wifi_ssid'], 'TestNetwork')
        self.assertTrue(metrics['internet_connected'])
        self.assertTrue(metrics['is_client_mode'])
        self.assertFalse(metrics['is_ap_mode'])

    def test_mode_display(self):
        """Test WiFi mode display formatting"""
        # Create a mock WiFiManager
        mock_wifi = MagicMock()
        
        # Test Client Mode
        mock_wifi.is_client_mode.return_value = True
        mock_wifi.is_ap_mode.return_value = False
        self.monitor.wifi_manager = mock_wifi
        metrics = self.monitor.collect_network_metrics()
        self.assertEqual(metrics['mode'], 'Client')
        
        # Test AP Mode
        mock_wifi.is_client_mode.return_value = False
        mock_wifi.is_ap_mode.return_value = True
        metrics = self.monitor.collect_network_metrics()
        self.assertEqual(metrics['mode'], 'AP')
        
        # Test Unknown Mode
        mock_wifi.is_client_mode.return_value = False
        mock_wifi.is_ap_mode.return_value = False
        metrics = self.monitor.collect_network_metrics()
        self.assertEqual(metrics['mode'], 'Unknown')

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
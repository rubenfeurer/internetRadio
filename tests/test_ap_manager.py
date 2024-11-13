import unittest
from unittest.mock import patch, MagicMock
from src.network.ap_manager import APManager

class TestAPManager(unittest.TestCase):
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
        
        # Create AP Manager instance
        self.ap_manager = APManager()
    
    @patch('subprocess.run')
    def test_setup_ap_mode_success(self, mock_run):
        # Mock all subprocess calls to succeed
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="active\n"
        )
        
        self.assertTrue(self.ap_manager.setup_ap_mode())
    
    @patch('subprocess.run')
    def test_setup_ap_mode_failure(self, mock_run):
        # Mock service start failure
        def mock_command(*args, **kwargs):
            if 'is-active' in args[0]:
                return MagicMock(returncode=0, stdout="inactive\n")
            return MagicMock(returncode=0)
        
        mock_run.side_effect = mock_command
        self.assertFalse(self.ap_manager.setup_ap_mode())
    
    @patch('subprocess.run')
    def test_is_ap_mode_active_true(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="active\n"
        )
        self.assertTrue(self.ap_manager.is_ap_mode_active())
    
    @patch('subprocess.run')
    def test_is_ap_mode_active_false(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="inactive\n"
        )
        self.assertFalse(self.ap_manager.is_ap_mode_active())
    
    @patch('subprocess.run')
    def test_configure_interface_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(self.ap_manager._configure_interface())
    
    @patch('subprocess.run')
    def test_configure_interface_failure(self, mock_run):
        mock_run.side_effect = Exception("Network error")
        self.assertFalse(self.ap_manager._configure_interface())
    
    @patch('subprocess.run')
    def test_stop_network_services(self, mock_run):
        """Test stopping network services"""
        mock_run.return_value = MagicMock(returncode=0)
        self.ap_manager._stop_network_services()
        
        # Verify both services were stopped
        calls = mock_run.call_args_list
        self.assertEqual(len(calls), 2)  # Two services should be stopped
        self.assertIn("NetworkManager", str(calls[0]))
        self.assertIn("wpa_supplicant", str(calls[1]))
    
    @patch('subprocess.run')
    def test_configure_and_start_services(self, mock_run):
        """Test service configuration and startup"""
        # Mock successful service starts
        def mock_command(*args, **kwargs):
            if 'is-active' in args[0]:
                return MagicMock(returncode=0, stdout="active\n")
            return MagicMock(returncode=0)
        
        mock_run.side_effect = mock_command
        self.assertTrue(self.ap_manager._configure_and_start_services())
        
        # Verify service starts were called
        calls = mock_run.call_args_list
        service_starts = [call for call in calls if "start" in str(call)]
        self.assertEqual(len(service_starts), 2)  # Both services should be started
    
    @patch('subprocess.run')
    def test_service_verification(self, mock_run):
        """Test service status verification"""
        # Test when both services are active
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="active\n"
        )
        self.assertTrue(self.ap_manager.is_ap_mode_active())
        
        # Test when one service is inactive
        def mock_status(*args, **kwargs):
            if "hostapd" in args[0]:
                return MagicMock(returncode=0, stdout="active\n")
            return MagicMock(returncode=0, stdout="inactive\n")
        
        mock_run.side_effect = mock_status
        self.assertFalse(self.ap_manager.is_ap_mode_active())
    
    @patch('subprocess.run')
    def test_initialize_success(self, mock_run):
        """Test successful initialization of AP Manager"""
        # Mock successful command checks
        mock_run.return_value = MagicMock(returncode=0)
        
        result = self.ap_manager.initialize()
        self.assertTrue(result)
        # Verify logging
        self.logger_mock.info.assert_any_call("Initializing AP Manager...")
    
    @patch('subprocess.run')
    def test_initialize_failure(self, mock_run):
        """Test initialization failure of AP Manager"""
        # Mock command failure
        mock_run.side_effect = Exception("Test error")
        
        result = self.ap_manager.initialize()
        self.assertFalse(result)
        # Verify error logging
        self.logger_mock.error.assert_any_call("Error initializing AP Manager: Test error")
    
    @patch('subprocess.run')
    def test_initialize_checks_dependencies(self, mock_run):
        """Test that initialize checks for required dependencies"""
        # Mock successful command checks
        mock_run.return_value = MagicMock(returncode=0)
        
        result = self.ap_manager.initialize()
        
        # Verify hostapd and dnsmasq checks
        calls = mock_run.call_args_list
        self.assertTrue(any('hostapd' in str(call) for call in calls))
        self.assertTrue(any('dnsmasq' in str(call) for call in calls))
        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_initialize_missing_dependencies(self, mock_run):
        """Test initialization with missing dependencies"""
        # Mock command not found
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        result = self.ap_manager.initialize()
        self.assertFalse(result)
        # Verify error logging
        self.logger_mock.error.assert_any_call("Required dependency missing: Command not found")

if __name__ == '__main__':
    unittest.main() 
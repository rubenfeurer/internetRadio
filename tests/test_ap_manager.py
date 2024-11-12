import unittest
from unittest.mock import patch, MagicMock
from src.network.ap_manager import APManager

class TestAPManager(unittest.TestCase):
    def setUp(self):
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

if __name__ == '__main__':
    unittest.main() 
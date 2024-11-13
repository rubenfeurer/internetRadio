import unittest
from unittest.mock import patch, Mock, MagicMock
import signal
import sys
from pathlib import Path

class TestMain(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Clear module cache first
        if 'main' in sys.modules:
            del sys.modules['main']
            
        # Create mocks
        self.network_mock = Mock()
        self.network_mock.initialize.return_value = True
        self.network_mock.cleanup = Mock()
        self.network_mock.check_and_setup_network.return_value = True
        self.network_mock.is_ap_mode_active.return_value = True
        self.network_mock.monitor = Mock()
        
        self.radio_controller_mock = Mock()
        self.radio_controller_mock.initialize.return_value = True
        self.radio_controller_mock.cleanup = Mock()
        self.radio_controller_mock.monitor = Mock()
        self.radio_controller_mock.set_led_state = Mock()
        
        # Create InternetRadio instance mock
        self.radio_instance = Mock()
        self.radio_instance.network_controller = self.network_mock
        self.radio_instance.radio_controller = self.radio_controller_mock
        self.radio_instance.cleanup = Mock()
        
        # Create logger mock
        self.logger_mock = Mock()
        
        # Set up patches
        self.patches = [
            patch('main.logger', self.logger_mock),
            patch('main.InternetRadio', return_value=self.radio_instance),
            patch('builtins.print'),  # Suppress print statements
            patch('main.signal.signal'),  # Don't register signal handlers
            # Make sleep raise KeyboardInterrupt after first call
            patch('main.time.sleep', side_effect=[None, KeyboardInterrupt])
        ]
        
        # Start all patches
        for p in self.patches:
            p.start()
            
        self.addCleanup(patch.stopall)
    
    def test_failed_wifi_connection(self):
        """Test failed WiFi connection scenario"""
        self.network_mock.check_and_setup_network.return_value = False
        
        import main
        try:
            main.main()
        except KeyboardInterrupt:
            pass
        
        self.network_mock.check_and_setup_network.assert_called_once()
        self.logger_mock.info.assert_any_call("Could not connect to any networks, maintaining AP mode...")
        self.radio_controller_mock.set_led_state.assert_called_with(blink=True, on_time=0.5, off_time=0.5)
        self.network_mock.cleanup.assert_called_once()
    
    def test_network_initialization_failure(self):
        """Test network initialization failure scenario"""
        self.network_mock.initialize.return_value = False
        
        import main
        result = main.main()
        
        self.network_mock.initialize.assert_called_once()
        self.network_mock.cleanup.assert_called_once()
        self.logger_mock.error.assert_any_call("Failed to initialize network controller")
        self.assertEqual(result, 1)
    
    def test_radio_initialization_failure(self):
        """Test radio initialization failure scenario"""
        self.radio_controller_mock.initialize.return_value = False
        
        import main
        result = main.main()
        
        self.radio_controller_mock.initialize.assert_called_once()
        self.network_mock.cleanup.assert_called_once()
        self.logger_mock.error.assert_any_call("Failed to initialize radio controller")
        self.assertEqual(result, 1)
    
    def test_successful_wifi_connection(self):
        """Test successful WiFi connection scenario"""
        self.network_mock.check_and_setup_network.return_value = True
        
        import main
        try:
            main.main()
        except KeyboardInterrupt:
            pass
        
        self.network_mock.check_and_setup_network.assert_called_once()
        self.logger_mock.info.assert_any_call("Connected to WiFi network")
        self.radio_controller_mock.set_led_state.assert_called_with(blink=True, on_time=3, off_time=3)
        
        # Verify monitoring was called
        self.radio_controller_mock.monitor.assert_called()
        self.network_mock.monitor.assert_called()
        
        # Verify cleanup was called
        self.network_mock.cleanup.assert_called_once()

if __name__ == '__main__':
    unittest.main() 
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
            
        # Create mocks for managers
        self.config_manager_mock = Mock()
        self.stream_manager_mock = Mock()
        self.audio_manager_mock = Mock()
        self.gpio_manager_mock = Mock()
        
        # Create mocks for controllers
        self.network_mock = Mock()
        self.network_mock.initialize.return_value = True
        self.network_mock.cleanup = Mock()
        self.network_mock.check_and_setup_network.return_value = True
        self.network_mock.is_ap_mode_active.return_value = True
        self.network_mock.monitor = Mock()
        
        # Create RadioController mock with proper gpio_manager attribute
        self.radio_controller_mock = Mock()
        self.radio_controller_mock.initialize.return_value = True
        self.radio_controller_mock.cleanup = Mock()
        self.radio_controller_mock.monitor = Mock()
        self.radio_controller_mock.set_led_state = Mock()
        self.radio_controller_mock.gpio_manager = self.gpio_manager_mock  # Set the gpio_manager
        
        # Create InternetRadio instance mock with all components
        self.radio_instance = Mock()
        self.radio_instance.config_manager = self.config_manager_mock
        self.radio_instance.stream_manager = self.stream_manager_mock
        self.radio_instance.audio_manager = self.audio_manager_mock
        self.radio_instance.gpio_manager = self.gpio_manager_mock
        self.radio_instance.network_controller = self.network_mock
        self.radio_instance.radio_controller = self.radio_controller_mock
        self.radio_instance.cleanup = Mock()
        
        # Create logger mock
        self.logger_mock = Mock()
        
        # Set up patches
        self.patches = [
            patch('main.logger', self.logger_mock),
            patch('main.InternetRadio', return_value=self.radio_instance),
            patch('main.ConfigManager', return_value=self.config_manager_mock),
            patch('main.StreamManager', return_value=self.stream_manager_mock),
            patch('main.AudioManager', return_value=self.audio_manager_mock),
            patch('main.GPIOManager', return_value=self.gpio_manager_mock),
            patch('main.RadioController', return_value=self.radio_controller_mock),
            patch('main.NetworkController', return_value=self.network_mock),
            patch('builtins.print'),  # Suppress print statements
            patch('main.signal.signal'),  # Don't register signal handlers
            patch('main.time.sleep', side_effect=[None, KeyboardInterrupt]),
            patch('sys.exit', Mock())  # Prevent actual exit
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
        self.network_mock.cleanup.assert_called()
    
    def test_network_initialization_failure(self):
        """Test network initialization failure scenario"""
        self.network_mock.initialize.return_value = False
        
        import main
        result = main.main()
        
        self.network_mock.initialize.assert_called_once()
        self.network_mock.cleanup.assert_called()
        self.logger_mock.error.assert_any_call("Failed to initialize network controller")
        self.assertEqual(result, 1)
    
    def test_radio_initialization_failure(self):
        """Test radio initialization failure scenario"""
        self.radio_controller_mock.initialize.return_value = False
        
        import main
        result = main.main()
        
        self.radio_controller_mock.initialize.assert_called_once()
        self.network_mock.cleanup.assert_called()
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
        self.network_mock.cleanup.assert_called()
    
    def test_signal_handler(self):
        """Test signal handler cleanup"""
        import main
        
        # Create a new mock for sys.exit
        exit_mock = Mock()
        with patch('sys.exit', exit_mock):
            # Set up global variables that signal handler uses
            main.radio = self.radio_instance
            main.network = self.network_mock
            main.web = None  # Web controller not initialized in our tests
            
            # Call signal handler with SIGTERM
            main.signal_handler(signal.SIGTERM, None)
            
            # Verify:
            # 1. Logger recorded the signal
            self.logger_mock.info.assert_any_call("Received signal 15 to terminate")
            
            # 2. Cleanup was called
            self.network_mock.cleanup.assert_called()
            self.radio_instance.cleanup.assert_called()
            
            # 3. System exit was called
            exit_mock.assert_called_once_with(0)
    
    def test_internet_radio_initialization(self):
        """Test InternetRadio initialization"""
        import main
        
        # Create mocks for managers that should be passed
        mock_gpio = self.gpio_manager_mock  # Use the existing mock from setUp
        
        # Update patches to include the correct initialization parameters
        with patch('main.GPIOManager', return_value=mock_gpio):
            radio = main.InternetRadio()
            
            # Verify all components are initialized
            self.assertIsNotNone(radio.config_manager)
            self.assertIsNotNone(radio.stream_manager)
            self.assertIsNotNone(radio.audio_manager)
            self.assertIsNotNone(radio.gpio_manager)
            self.assertIsNotNone(radio.network_controller)
            self.assertIsNotNone(radio.radio_controller)
            
            # Verify RadioController was initialized with correct gpio_manager
            # Use assertIs to check if it's the same instance
            self.assertIs(radio.radio_controller.gpio_manager, mock_gpio)

if __name__ == '__main__':
    unittest.main()

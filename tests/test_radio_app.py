import unittest
from unittest.mock import Mock, patch, MagicMock
from src.app import RadioApp

class TestRadioApp(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create mocks with all required methods
        self.radio_mock = Mock()
        self.radio_mock.initialize = Mock(return_value=True)
        self.radio_mock.cleanup = Mock()
        self.radio_mock.next_station = Mock()
        self.radio_mock.reset_to_first_station = Mock()
        self.radio_mock.volume_up = Mock()
        self.radio_mock.volume_down = Mock()
        
        self.button_mock = Mock()
        self.button_mock.initialize = Mock(return_value=True)
        self.button_mock.cleanup = Mock()
        self.button_mock.when_pressed = Mock()
        self.button_mock.when_held = Mock()
        
        self.encoder_mock = Mock()
        self.encoder_mock.initialize = Mock(return_value=True)
        self.encoder_mock.cleanup = Mock()
        self.encoder_mock.when_rotated = Mock()
        
        self.logger_mock = Mock()
        
        # Create logger patcher
        self.logger_patcher = patch('src.app.Logger')
        mock_logger_class = self.logger_patcher.start()
        mock_logger_class.get_logger.return_value = self.logger_mock
        
        # Create app instance with mocked dependencies
        self.app = RadioApp(
            radio_controller=self.radio_mock,
            button_controller=self.button_mock,
            encoder_controller=self.encoder_mock
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.logger_patcher.stop()
    
    def test_initialization(self):
        """Test app initialization"""
        result = self.app.initialize()
        
        self.assertTrue(result)
        self.radio_mock.initialize.assert_called_once()
        self.button_mock.initialize.assert_called_once()
        self.encoder_mock.initialize.assert_called_once()
    
    def test_button_event_binding(self):
        """Test button event handlers are properly bound"""
        self.app.initialize()
        
        # Verify button handlers are set
        self.button_mock.when_pressed.assert_called_once()
        self.button_mock.when_held.assert_called_once()
        
        # Test press handler
        press_handler = self.button_mock.when_pressed.call_args[0][0]
        press_handler()
        self.radio_mock.next_station.assert_called_once()
        
        # Test hold handler
        hold_handler = self.button_mock.when_held.call_args[0][0]
        hold_handler()
        self.radio_mock.reset_to_first_station.assert_called_once()
    
    def test_encoder_event_binding(self):
        """Test encoder event handler is properly bound"""
        self.app.initialize()
        
        # Verify encoder handler is set
        self.encoder_mock.when_rotated.assert_called_once()
        
        # Test rotation handler
        rotation_handler = self.encoder_mock.when_rotated.call_args[0][0]
        
        # Test volume up
        rotation_handler(1)
        self.radio_mock.volume_up.assert_called_once()
        
        # Reset mock for volume down test
        self.radio_mock.volume_up.reset_mock()
        
        # Test volume down
        rotation_handler(-1)
        self.radio_mock.volume_down.assert_called_once()
    
    def test_cleanup(self):
        """Test app cleanup"""
        self.app.cleanup()
        self.radio_mock.cleanup.assert_called_once()
        self.button_mock.cleanup.assert_called_once()
        self.encoder_mock.cleanup.assert_called_once()
    
    def test_error_handling(self):
        """Test error handling during initialization"""
        # Make radio controller initialization fail
        self.radio_mock.initialize.return_value = False
        
        result = self.app.initialize()
        
        self.assertFalse(result)
        self.logger_mock.error.assert_called_once()
        
        # Verify cleanup was called
        self.radio_mock.cleanup.assert_called_once()
        self.button_mock.cleanup.assert_called_once()
        self.encoder_mock.cleanup.assert_called_once()

if __name__ == '__main__':
    unittest.main() 
import unittest
from unittest.mock import Mock, patch, PropertyMock
from gpiozero import Button
from src.hardware.button_controller import ButtonController

class TestButtonController(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create the logger mock
        self.logger_mock = Mock()
        self.logger_patcher = patch('logging.getLogger', return_value=self.logger_mock)
        self.logger_patcher.start()
        
        # Create button mock
        self.button_patcher = patch('src.hardware.button_controller.Button')
        self.mock_button_class = self.button_patcher.start()
        self.button_mock = Mock(spec=Button)
        
        # Set up property mocks for button events
        self.when_pressed_mock = PropertyMock()
        self.when_released_mock = PropertyMock()
        self.when_held_mock = PropertyMock()
        
        type(self.button_mock).when_pressed = self.when_pressed_mock
        type(self.button_mock).when_released = self.when_released_mock
        type(self.button_mock).when_held = self.when_held_mock
        
        self.mock_button_class.return_value = self.button_mock
        
        # Create controller
        self.button_controller = ButtonController(pin=17)
    
    def tearDown(self):
        """Clean up after tests"""
        self.logger_patcher.stop()
        self.button_patcher.stop()
    
    def test_initialization(self):
        """Test button initialization"""
        self.assertIsNotNone(self.button_controller)
        self.assertEqual(self.button_controller.pin, 17)
        self.mock_button_class.assert_called_once_with(17, hold_time=2.0, pull_up=True)
        self.logger_mock.info.assert_called_once()
    
    def test_when_pressed(self):
        """Test button press callback"""
        test_callback = Mock()
        self.button_controller.when_pressed(test_callback)
        
        self.when_pressed_mock.assert_called_once()
        
        # Get and call the wrapped callback
        wrapped_callback = self.when_pressed_mock.call_args[0][0]
        wrapped_callback()
        
        test_callback.assert_called_once()
        self.logger_mock.debug.assert_called()
    
    def test_when_released(self):
        """Test button release callback"""
        test_callback = Mock()
        self.button_controller.when_released(test_callback)
        
        self.when_released_mock.assert_called_once()
        
        wrapped_callback = self.when_released_mock.call_args[0][0]
        wrapped_callback()
        
        test_callback.assert_called_once()
        self.logger_mock.debug.assert_called()
    
    def test_when_held(self):
        """Test button held callback"""
        test_callback = Mock()
        self.button_controller.when_held(test_callback)
        
        self.when_held_mock.assert_called_once()
        
        wrapped_callback = self.when_held_mock.call_args[0][0]
        wrapped_callback()
        
        test_callback.assert_called_once()
        self.logger_mock.debug.assert_called()
    
    def test_callback_error_handling(self):
        """Test error handling in button callbacks"""
        def failing_callback():
            raise ValueError("Test error")
        
        self.logger_mock.reset_mock()
        
        self.button_controller.when_pressed(failing_callback)
        wrapped_callback = self.when_pressed_mock.call_args[0][0]
        wrapped_callback()
        
        self.logger_mock.error.assert_called_once_with("Error in button callback: Test error")
    
    def test_cleanup(self):
        """Test button cleanup"""
        self.button_controller.cleanup()
        self.button_mock.close.assert_called_once()
        self.logger_mock.info.assert_called_with("Button resources cleaned up")
    
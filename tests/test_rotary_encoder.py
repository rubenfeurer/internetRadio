import unittest
from unittest.mock import Mock, patch, PropertyMock
from gpiozero import RotaryEncoder
from src.hardware.rotary_encoder import RotaryEncoderController

class TestRotaryEncoderController(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create the logger mock first
        self.logger_mock = Mock()
        self.logger_patcher = patch('logging.getLogger', return_value=self.logger_mock)
        self.logger_patcher.start()
        
        # Then create encoder mock
        self.encoder_patcher = patch('src.hardware.rotary_encoder.RotaryEncoder')
        self.mock_encoder_class = self.encoder_patcher.start()
        self.encoder_mock = Mock(spec=RotaryEncoder)
        self.when_rotated_mock = PropertyMock()
        type(self.encoder_mock).when_rotated = self.when_rotated_mock
        self.mock_encoder_class.return_value = self.encoder_mock
        
        # Create controller
        self.encoder_controller = RotaryEncoderController(clk_pin=22, dt_pin=23)
    
    def tearDown(self):
        """Clean up after tests"""
        self.logger_patcher.stop()
        self.encoder_patcher.stop()
    
    def test_initialization(self):
        """Test encoder initialization"""
        self.assertIsNotNone(self.encoder_controller)
        self.assertEqual(self.encoder_controller.clk_pin, 22)
        self.assertEqual(self.encoder_controller.dt_pin, 23)
        self.mock_encoder_class.assert_called_once_with(22, 23)
        self.logger_mock.info.assert_called_once()
    
    def test_when_rotated_callback(self):
        """Test rotary encoder rotation callback"""
        test_callback = Mock()
        self.encoder_controller.when_rotated(test_callback)
        
        # Verify the callback was set
        self.when_rotated_mock.assert_called_once()
        
        # Get the wrapped callback that was set
        wrapped_callback = self.when_rotated_mock.call_args[0][0]
        
        # Test the wrapped callback
        wrapped_callback(1)  # Simulate clockwise rotation
        test_callback.assert_called_once_with(1)
        self.logger_mock.debug.assert_called_once()
    
    def test_cleanup(self):
        """Test encoder cleanup"""
        self.encoder_controller.cleanup()
        self.encoder_mock.close.assert_called_once()
        self.logger_mock.info.assert_called_with("Rotary encoder resources cleaned up")
    
    def test_get_steps(self):
        """Test getting steps count"""
        self.encoder_mock.steps = 5
        self.assertEqual(self.encoder_controller.get_steps(), 5)
    
    def test_reset_steps(self):
        """Test resetting steps count"""
        self.encoder_controller.reset_steps()
        self.assertEqual(self.encoder_mock.steps, 0)
        self.logger_mock.debug.assert_called_with("Steps reset to 0")
    
    def test_callback_error_handling(self):
        """Test error handling in rotation callback"""
        def failing_callback(direction):
            raise ValueError("Test error")
        
        # Reset the logger mock to ensure clean state
        self.logger_mock.reset_mock()
        
        # Set up the failing callback
        self.encoder_controller.when_rotated(failing_callback)
        
        # Get and call the wrapped callback
        wrapped_callback = self.when_rotated_mock.call_args[0][0]
        wrapped_callback(1)
        
        # Verify error was logged with specific message
        self.logger_mock.error.assert_called_once_with("Error in rotation callback: Test error")
    
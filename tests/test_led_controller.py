import unittest
from unittest.mock import Mock, patch
from gpiozero import LED
from gpiozero.exc import GPIOPinInUse
from src.hardware.led_controller import LEDController

class TestLEDController(unittest.TestCase):
    @patch('src.hardware.led_controller.LED')
    def setUp(self, mock_led_class):
        """Set up test fixtures"""
        # Create a mock LED instance
        self.led_mock = Mock(spec=LED)
        # Configure the mock LED class to return our mock instance
        mock_led_class.return_value = self.led_mock
        # Store the mock class for assertions
        self.mock_led_class = mock_led_class
        # Create LED controller
        self.led_controller = LEDController(pin=17)
    
    def test_initialization(self):
        """Test LED controller initialization"""
        self.assertIsNotNone(self.led_controller)
        self.assertEqual(self.led_controller.pin, 17)
        self.mock_led_class.assert_called_once_with(17)
    
    def test_turn_on(self):
        """Test turning LED on"""
        self.led_controller.turn_on()
        self.led_mock.on.assert_called_once()
    
    def test_turn_off(self):
        """Test turning LED off"""
        self.led_controller.turn_off()
        self.led_mock.off.assert_called_once()
    
    def test_blink(self):
        """Test LED blink"""
        self.led_controller.blink(on_time=0.5, off_time=0.5)
        self.led_mock.blink.assert_called_once_with(on_time=0.5, off_time=0.5)
    
    def test_cleanup(self):
        """Test LED cleanup"""
        self.led_controller.cleanup()
        self.led_mock.close.assert_called_once()
    
    @patch('src.hardware.led_controller.LED')
    def test_initialization_error(self, mock_led_class):
        """Test LED initialization with GPIO pin in use"""
        mock_led_class.side_effect = GPIOPinInUse("Pin already in use")
        with self.assertRaises(GPIOPinInUse):
            LEDController(pin=17)
import unittest
from unittest.mock import patch, MagicMock
from src.hardware.gpio_manager import GPIOManager

class TestGPIOManager(unittest.TestCase):
    @patch('src.hardware.gpio_manager.LED')
    def setUp(self, mock_led_class):
        # Setup mocks
        self.mock_led = MagicMock()
        
        # Configure mock returns
        mock_led_class.return_value = self.mock_led
        
        # Create GPIO manager
        self.gpio = GPIOManager()
        
        # Initialize to create LED instance
        self.gpio.initialize()
        
    def test_led_control(self):
        """Test LED control methods"""
        # Test LED on
        self.gpio.led_on()
        self.mock_led.on.assert_called_once()
        
        # Test LED off
        self.gpio.led_off()
        self.mock_led.off.assert_called_once()
        
        # Test LED blink
        on_time = 1.0
        off_time = 0.5
        self.gpio.led_blink(on_time=on_time, off_time=off_time)
        self.mock_led.blink.assert_called_once_with(on_time=on_time, off_time=off_time) 
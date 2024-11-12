import unittest
from unittest.mock import patch, MagicMock, PropertyMock, call
import logging

class TestGPIOManager(unittest.TestCase):
    def setUp(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        
        # Create patches
        self.patches = {
            'pigpio': patch('src.hardware.gpio_manager.pigpio.pi'),
            'LED': patch('src.hardware.gpio_manager.LED'),
            'RotaryEncoder': patch('src.hardware.gpio_manager.RotaryEncoder'),
            'Button': patch('src.hardware.gpio_manager.Button'),
            'Factory': patch('src.hardware.gpio_manager.PiGPIOFactory'),
            'Device': patch('src.hardware.gpio_manager.Device')
        }
        
        # Start patches
        self.mocks = {name: patcher.start() for name, patcher in self.patches.items()}
        
        # Configure pigpio mock
        self.mock_pi = MagicMock()
        self.mock_pi.connected = True
        self.mocks['pigpio'].return_value = self.mock_pi
        
        # Configure mock instances
        self.mock_led = MagicMock()
        self.mock_encoder = MagicMock()
        self.mock_button = MagicMock()
        
        self.mocks['LED'].return_value = self.mock_led
        self.mocks['RotaryEncoder'].return_value = self.mock_encoder
        self.mocks['Button'].return_value = self.mock_button
        
        # Import and create GPIOManager
        from src.hardware.gpio_manager import GPIOManager
        self.gpio_manager = GPIOManager()
    
    def tearDown(self):
        # Stop all patches
        for patcher in self.patches.values():
            patcher.stop()
    
    def test_initialize_success(self):
        # Test initialization
        result = self.gpio_manager.initialize()
        
        # Verify result
        self.assertTrue(result)
        
        # Verify component initialization
        self.mocks['LED'].assert_called_once_with(self.gpio_manager.LED_PIN)
        self.mocks['RotaryEncoder'].assert_called_once_with(
            self.gpio_manager.ENCODER_A_PIN,
            self.gpio_manager.ENCODER_B_PIN,
            max_steps=20
        )
        self.mocks['Button'].assert_called_once_with(
            self.gpio_manager.BUTTON_PIN,
            pull_up=True
        )
    
    def test_initialize_failure_pigpio(self):
        # Set pigpio to fail connection
        self.mock_pi.connected = False
        
        # Test initialization
        result = self.gpio_manager.initialize()
        self.assertFalse(result)
    
    def test_led_control(self):
        # Initialize GPIO
        self.gpio_manager.initialize()
        
        # Test LED on
        self.gpio_manager.set_led_state(True)
        self.mock_led.on.assert_called_once()
        self.mock_led.reset_mock()
        
        # Test LED off
        self.gpio_manager.set_led_state(False)
        self.mock_led.off.assert_called_once()
    
    def test_led_blink(self):
        # Initialize GPIO
        self.gpio_manager.initialize()
        
        # Test LED blink
        self.gpio_manager.start_led_blink(0.5, 0.5)
        self.mock_led.blink.assert_called_once_with(
            on_time=0.5,
            off_time=0.5
        )
    
    def test_cleanup(self):
        # Initialize GPIO
        self.gpio_manager.initialize()
        
        # Test cleanup
        self.gpio_manager.cleanup()
        
        # Verify cleanup calls
        self.mock_led.close.assert_called_once()
        self.mock_encoder.close.assert_called_once()
        self.mock_button.close.assert_called_once()
        self.mock_pi.stop.assert_called_once()

if __name__ == '__main__':
    unittest.main() 
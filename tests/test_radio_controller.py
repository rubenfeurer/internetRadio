import unittest
from unittest.mock import patch, MagicMock, call
import logging

class TestRadioController(unittest.TestCase):
    @patch('src.controllers.radio_controller.AudioManager')
    @patch('src.controllers.radio_controller.GPIOManager')
    @patch('src.controllers.radio_controller.Logger')
    def setUp(self, mock_logger_class, mock_gpio_class, mock_audio_class):
        logging.basicConfig(level=logging.DEBUG)
        
        # Create instance mocks
        self.mock_audio = MagicMock()
        self.mock_gpio = MagicMock()
        self.mock_logger = MagicMock()
        
        # Configure class mocks
        mock_audio_class.return_value = self.mock_audio
        mock_gpio_class.return_value = self.mock_gpio
        mock_logger_class.return_value = self.mock_logger
        
        # Configure success returns
        self.mock_gpio.initialize.return_value = True
        self.mock_audio.initialize.return_value = True
        self.mock_audio.play_url.return_value = True
        
        # Import and create RadioController
        from src.controllers.radio_controller import RadioController
        self.radio = RadioController()
        
        # Store classes for test methods
        self.mock_audio_class = mock_audio_class
        self.mock_gpio_class = mock_gpio_class
        self.mock_logger_class = mock_logger_class
    
    def test_initialize_success(self):
        result = self.radio.initialize()
        self.assertTrue(result)
        self.mock_gpio.initialize.assert_called_once()
        self.mock_audio.initialize.assert_called_once()
    
    def test_playback_control(self):
        # Initialize
        self.radio.initialize()
        test_url = "http://example.com/stream"
        
        # Start playback
        result = self.radio.start_playback(test_url)
        
        # Debug info
        print(f"AudioManager instance: {self.mock_audio}")
        print(f"play_url method: {self.mock_audio.play_url}")
        print(f"play_url calls: {self.mock_audio.play_url.mock_calls}")
        print(f"Result: {result}")
        
        # Verify
        self.assertTrue(result)
        self.assertTrue(self.radio.is_playing)
        self.mock_audio.play_url.assert_called_once_with(test_url)
        self.mock_gpio.start_led_blink.assert_called_once()
        
        # Stop playback
        self.radio.stop_playback()
        self.assertFalse(self.radio.is_playing)
        self.mock_audio.stop.assert_called_once()
        self.mock_gpio.set_led_state.assert_called_with(False)
    
    def test_volume_control(self):
        # Initialize
        self.radio.initialize()
        initial_volume = self.radio.current_volume
        print(f"Initial volume: {initial_volume}")
        
        # Test volume up
        self.radio.volume_up()
        expected_volume_up = initial_volume + 5
        print(f"Volume after up: {self.radio.current_volume}")
        print(f"AudioManager instance: {self.mock_audio}")
        print(f"set_volume method: {self.mock_audio.set_volume}")
        print(f"set_volume calls: {self.mock_audio.set_volume.mock_calls}")
        
        self.assertEqual(self.radio.current_volume, expected_volume_up)
        self.mock_audio.set_volume.assert_called_with(expected_volume_up)
        
        # Reset mock
        self.mock_audio.set_volume.reset_mock()
        
        # Test volume down
        self.radio.volume_down()
        expected_volume_down = initial_volume
        self.assertEqual(self.radio.current_volume, expected_volume_down)
        self.mock_audio.set_volume.assert_called_with(expected_volume_down)

if __name__ == '__main__':
    unittest.main()
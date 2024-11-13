import os
import time
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src import ROOT_DIR, CONFIG_DIR, LOGS_DIR
from src.controllers.radio_controller import RadioController
from src.controllers.network_controller import NetworkController
from src.web.web_controller import WebController
from src.utils.logger import Logger
from src.utils.config_manager import ConfigManager
from src.utils.stream_manager import StreamManager
from src.audio.audio_manager import AudioManager
from src.hardware.gpio_manager import GPIOManager
from src.network.wifi_manager import WiFiManager
from src.network.ap_manager import APManager

class TestSystemIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.logs_dir = os.path.join(self.test_dir, 'logs')
        os.makedirs(self.config_dir)
        os.makedirs(self.logs_dir)

        # Initialize logger
        Logger.setup_logging(self.logs_dir)
        self.logger = Logger.get_logger(__name__)

        # Initialize managers
        self.config_manager = ConfigManager(config_dir=self.config_dir)
        self.stream_manager = StreamManager(config_dir=self.config_dir)

        yield

        # Cleanup
        import shutil
        shutil.rmtree(self.test_dir)

    def test_system_startup(self):
        """Test system startup sequence"""
        with patch('src.hardware.gpio_manager.pigpio') as mock_pigpio, \
             patch('src.hardware.gpio_manager.LED') as mock_led, \
             patch('src.hardware.gpio_manager.RotaryEncoder') as mock_encoder, \
             patch('src.hardware.gpio_manager.Button') as mock_button, \
             patch('src.hardware.gpio_manager.PiGPIOFactory') as mock_factory:
            
            # Set up mock with proper initialization expectations
            mock_pi = Mock()
            mock_pi.connected = True
            mock_pigpio.pi.return_value = mock_pi
            
            # Initialize components
            gpio = GPIOManager()
            audio = AudioManager()
            
            # Force GPIO initialization
            gpio.initialize()
            
            # Test initialization
            assert audio.initialize()
            
            # Verify GPIO setup was called
            assert mock_pigpio.pi.called
            mock_led.assert_called_once_with(gpio.LED_PIN)
            mock_encoder.assert_called_once_with(
                gpio.ENCODER_A_PIN,
                gpio.ENCODER_B_PIN,
                max_steps=20
            )
            mock_button.assert_called_once_with(gpio.BUTTON_PIN, pull_up=True)

    def test_network_fallback(self):
        """Test network fallback to AP mode"""
        with patch('src.network.wifi_manager.WiFiManager') as mock_wifi, \
             patch('src.network.ap_manager.APManager') as mock_ap:
            
            # Create mocked instances
            wifi_manager = mock_wifi.return_value
            ap_manager = mock_ap.return_value
            
            # Set up WiFiManager mock behavior
            wifi_manager.initialize.return_value = True
            wifi_manager.connect_to_network.return_value = False  # WiFi fails
            wifi_manager.get_saved_networks.return_value = ['network1', 'network2']
            wifi_manager.is_connected.return_value = False
            
            # Set up APManager mock behavior
            ap_manager.initialize.return_value = True
            ap_manager.start.return_value = True  # AP mode succeeds
            ap_manager.is_ap_mode_active.return_value = True
            
            # Create NetworkController with mocked dependencies
            network = NetworkController(wifi_manager, ap_manager, self.config_manager)
            
            # Initialize controller
            assert network.initialize()
            
            # Test network fallback
            result = network.check_and_setup_network()
            
            # Verify behavior
            assert result  # Should be True because AP mode succeeded
            wifi_manager.connect_to_network.assert_called()  # Should try to connect
            assert network.is_ap_mode  # Should be in AP mode
            ap_manager.start.assert_called_once_with("DefaultAP", "password")  # Should start AP mode

    def test_audio_stream_playback(self):
        """Test audio stream playback"""
        with patch('src.audio.audio_manager.vlc.Instance') as mock_vlc:
            # Create test stream
            test_stream = {
                'name': 'Test Radio',
                'url': 'http://test.com/stream',
                'country': 'Test Country',
                'location': 'Test Location'
            }
            self.stream_manager.add_stream(test_stream)
            
            # Create controller with dependencies
            audio = AudioManager()
            gpio = GPIOManager()
            radio = RadioController(audio, gpio, self.stream_manager)
            
            # Initialize the controller
            assert radio.initialize()
            
            # Test playback
            assert radio.start_playback(test_stream['url'])
            assert mock_vlc.called
            
            # Verify playback state
            assert radio.is_playing
            
            # Test stop playback
            radio.stop_playback()
            assert not radio.is_playing

    def test_web_interface(self):
        """Test web interface initialization"""
        with patch('src.web.web_controller.Thread') as mock_thread, \
             patch('src.web.web_controller.Flask') as mock_flask:
            
            # Create mocked controllers
            radio = Mock(spec=RadioController)
            network = Mock(spec=NetworkController)
            
            # Configure thread mock
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            # Create web controller
            web = WebController(radio, network)
            
            # Test initialization and start
            web.start()
            
            # Verify behavior
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
            assert web.thread is not None
            assert len(mock_flask().route.call_args_list) > 0  # Routes were registered

    def test_system_shutdown(self):
        """Test system shutdown sequence"""
        with patch('src.hardware.gpio_manager.pigpio') as mock_pigpio:
            # Set up mock
            mock_pi = Mock()
            mock_pigpio.pi.return_value = mock_pi
            
            # Initialize components
            gpio = GPIOManager()
            audio = AudioManager()
            
            # Initialize GPIO
            gpio.initialize()
            
            # Create and initialize radio controller
            radio = RadioController()
            radio.audio_manager = audio
            radio.gpio_manager = gpio
            radio.initialize()
            
            # Test cleanup
            radio.cleanup()
            
            # Verify cleanup
            mock_pi.stop.assert_called_once()

    @pytest.mark.slow
    def test_system_monitoring(self):
        """Test system monitoring"""
        with patch('src.network.wifi_manager.WiFiManager') as mock_wifi, \
             patch('src.network.ap_manager.APManager') as mock_ap:
            
            # Create mocked instances
            wifi_manager = mock_wifi.return_value
            ap_manager = mock_ap.return_value
            
            # Set up connection simulation
            wifi_manager.is_connected.side_effect = [True, True, False, True]
            
            # Create controller with dependencies
            network = NetworkController(wifi_manager, ap_manager, self.config_manager)
            
            # Test monitoring
            for _ in range(4):
                network.monitor()
                time.sleep(0.1)
            
            assert wifi_manager.is_connected.call_count == 4
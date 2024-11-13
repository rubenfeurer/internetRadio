import os
import time
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

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
        # Create temporary directories
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.logs_dir = os.path.join(self.test_dir, 'logs')
        os.makedirs(self.config_dir)
        os.makedirs(self.logs_dir)

        # Initialize logger
        Logger.reset()
        Logger.setup_logging(self.logs_dir)
        self.logger = Logger.get_logger('test')

        # Initialize managers with test configuration
        self.config_manager = ConfigManager(config_dir=self.config_dir)
        self.stream_manager = StreamManager(config_dir=self.config_dir)
        
        yield

        # Cleanup
        import shutil
        shutil.rmtree(self.test_dir)

    def test_system_startup(self):
        """Test system startup sequence"""
        with patch('src.hardware.gpio_manager.pigpio') as mock_pigpio:
            # Initialize components
            gpio = GPIOManager()
            audio = AudioManager()
            wifi = WiFiManager()
            ap = APManager()

            # Test initialization
            assert gpio.initialize()
            assert audio.initialize()
            
            # Verify GPIO setup
            assert mock_pigpio.pi.called
            assert len(mock_pigpio.pi().set_mode.call_args_list) > 0

    def test_network_fallback(self):
        """Test network fallback to AP mode"""
        with patch('src.network.wifi_manager.WiFiManager.connect_to_network') as mock_connect:
            mock_connect.return_value = False
            
            wifi = WiFiManager()
            ap = APManager()
            network = NetworkController(wifi, ap, self.config_manager)

            # Test network fallback
            assert not network.check_and_setup_network()
            assert network.is_ap_mode_active()

    def test_audio_stream_playback(self):
        """Test audio stream playback"""
        with patch('src.audio.audio_manager.vlc.Instance') as mock_vlc:
            audio = AudioManager()
            gpio = GPIOManager()
            radio = RadioController(audio, gpio, self.stream_manager)

            # Add test stream
            test_stream = {
                'name': 'Test Radio',
                'url': 'http://test.com/stream',
                'country': 'Test Country',
                'location': 'Test City'
            }
            self.stream_manager.add_stream(test_stream)

            # Test playback
            assert radio.play_stream('Test Radio')
            assert mock_vlc.called

    def test_web_interface(self):
        """Test web interface initialization"""
        with patch('src.web.web_controller.Flask') as mock_flask:
            # Initialize controllers
            audio = AudioManager()
            gpio = GPIOManager()
            wifi = WiFiManager()
            ap = APManager()
            
            radio = RadioController(audio, gpio, self.stream_manager)
            network = NetworkController(wifi, ap, self.config_manager)
            web = WebController(radio, network)

            # Test web interface
            web.start()
            assert mock_flask.called
            assert len(mock_flask().route.call_args_list) > 0

    def test_system_shutdown(self):
        """Test system shutdown sequence"""
        with patch('src.hardware.gpio_manager.pigpio') as mock_pigpio:
            # Initialize components
            gpio = GPIOManager()
            audio = AudioManager()
            wifi = WiFiManager()
            ap = APManager()
            
            radio = RadioController(audio, gpio, self.stream_manager)
            network = NetworkController(wifi, ap, self.config_manager)
            web = WebController(radio, network)

            # Test cleanup
            radio.cleanup()
            network.cleanup()
            web.stop()

            assert mock_pigpio.pi().stop.called

    @pytest.mark.slow
    def test_system_monitoring(self):
        """Test system monitoring"""
        with patch('src.network.wifi_manager.WiFiManager.is_connected') as mock_wifi:
            mock_wifi.side_effect = [True, True, False, True]  # Simulate connection changes
            
            wifi = WiFiManager()
            ap = APManager()
            network = NetworkController(wifi, ap, self.config_manager)

            # Test monitoring over time
            for _ in range(4):
                network.monitor()
                time.sleep(1)

            assert mock_wifi.call_count == 4 
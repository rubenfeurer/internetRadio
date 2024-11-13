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
        with patch('src.hardware.gpio_manager.pigpio') as mock_pigpio:
            # Set up mock
            mock_pi = Mock()
            mock_pigpio.pi.return_value = mock_pi
            mock_pi.set_mode = Mock()
            
            # Initialize components
            gpio = GPIOManager()
            audio = AudioManager()
            
            # Force GPIO initialization
            gpio.initialize()
            
            # Test initialization
            assert audio.initialize()
            
            # Verify GPIO setup was called
            assert mock_pigpio.pi.called
            assert mock_pi.set_mode.called

    def test_network_fallback(self):
        """Test network fallback to AP mode"""
        with patch('src.network.wifi_manager.WiFiManager') as mock_wifi, \
             patch('src.network.ap_manager.APManager') as mock_ap:
            
            # Create mocked instances
            wifi_manager = mock_wifi.return_value
            ap_manager = mock_ap.return_value
            
            # Set up return values
            wifi_manager.connect_to_network.return_value = False
            ap_manager.setup_ap_mode.return_value = True
            
            # Create NetworkController with mocked dependencies
            network = NetworkController(wifi_manager, ap_manager, self.config_manager)
            
            # Test network fallback
            network.check_and_setup_network()
            assert network.is_ap_mode_active()
            assert ap_manager.setup_ap_mode.called

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
            
            # Test playback
            assert radio.start_stream('Test Radio')
            assert mock_vlc.called

    def test_web_interface(self):
        """Test web interface initialization"""
        with patch('src.web.web_controller.Flask') as mock_flask:
            # Create mocked controllers
            radio = Mock(spec=RadioController)
            network = Mock(spec=NetworkController)
            
            # Create web controller
            web = WebController(radio, network)
            
            # Test initialization
            web.start()
            assert mock_flask.called
            assert len(mock_flask().route.call_args_list) > 0

    def test_system_shutdown(self):
        """Test system shutdown sequence"""
        with patch('src.hardware.gpio_manager.pigpio') as mock_pigpio:
            gpio = GPIOManager()
            audio = AudioManager()
            
            radio = RadioController()
            radio.audio_manager = audio
            radio.gpio_manager = gpio
            
            # Test cleanup
            radio.cleanup()
            assert mock_pigpio.pi().stop.called

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
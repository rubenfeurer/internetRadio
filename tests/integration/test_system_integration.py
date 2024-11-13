import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.controllers.radio_controller import RadioController
from src.controllers.network_controller import NetworkController
from src.web.web_controller import WebController
import os

class TestSystemIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.patches = []
        self.mocks = {}
        
        # Setup all required mocks
        components = {
            'LED': 'src.hardware.gpio_manager.LED',
            'Button': 'src.hardware.gpio_manager.Button',
            'RotaryEncoder': 'src.hardware.gpio_manager.RotaryEncoder',
            'vlc.Instance': 'vlc.Instance',
            'WiFiManager': 'src.network.wifi_manager.WiFiManager',
            'APManager': 'src.network.ap_manager.APManager'
        }
        
        for name, path in components.items():
            patcher = patch(path)
            self.patches.append(patcher)
            self.mocks[name] = patcher.start()
            
        # Create Flask test client
        self.app = Flask(__name__)
        self.app.testing = True
        self.client = self.app.test_client()
    
    def test_system_startup(self):
        """Test system startup sequence"""
        with self.app.test_request_context():
            # Create controllers
            radio = RadioController()
            network = NetworkController()
            web = WebController(radio, network)
            
            # Test initialization
            self.assertTrue(radio.initialize())
            self.assertTrue(network.initialize())
            
            # Verify LED setup
            self.mocks['LED'].assert_called()
            
            # Verify encoder setup
            self.mocks['RotaryEncoder'].assert_called()
            
            # Verify button setup
            self.mocks['Button'].assert_called()
            
            # Verify audio environment variables
            self.assertEqual(os.environ.get('ALSA_IGNORE_UCM'), '1')
            self.assertEqual(os.environ.get('AUDIODEV'), 'hw:2,0')
            
            # Verify VLC initialization
            self.mocks['vlc.Instance'].assert_called_with('--no-xlib --aout=alsa')
            
            # Cleanup
            radio.cleanup()
            network.cleanup()
    
    def test_system_shutdown(self):
        """Test system shutdown sequence"""
        with self.app.test_request_context():
            # Create controllers
            radio = RadioController()
            network = NetworkController()
            web = WebController(radio, network)
            
            # Initialize
            radio.initialize()
            network.initialize()
            
            # Test cleanup
            radio.cleanup()
            network.cleanup()
            
            # Verify cleanup calls
            self.mocks['LED'].return_value.close.assert_called()
            self.mocks['Button'].return_value.close.assert_called()
            self.mocks['RotaryEncoder'].return_value.close.assert_called()
            
            # Verify VLC cleanup
            vlc_instance = self.mocks['vlc.Instance'].return_value
            if hasattr(vlc_instance, 'release'):
                vlc_instance.release.assert_called()
    
    def test_audio_system_integration(self):
        """Test audio system integration"""
        with self.app.test_request_context():
            radio = RadioController()
            self.assertTrue(radio.initialize())
            
            # Test volume control
            radio.set_volume(75)
            self.assertEqual(radio.audio_manager.current_volume, 75)
            
            # Mock file existence check
            with patch('os.path.isfile', return_value=True):
                # Test sound playback
                radio.audio_manager.play_sound('test.wav')
                vlc_player = self.mocks['vlc.Instance'].return_value.media_player_new.return_value
                vlc_player.play.assert_called()
            
            radio.cleanup()
    
    def tearDown(self):
        """Clean up after tests"""
        for patcher in self.patches:
            patcher.stop()
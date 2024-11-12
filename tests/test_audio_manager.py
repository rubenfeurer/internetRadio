import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import logging

class TestAudioManager(unittest.TestCase):
    def setUp(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        
        # Create patches
        self.patches = {
            'Instance': patch('src.audio.audio_manager.vlc.Instance'),
            'MediaPlayer': patch('src.audio.audio_manager.vlc.MediaPlayer')
        }
        
        # Start patches
        self.mocks = {name: patcher.start() for name, patcher in self.patches.items()}
        
        # Configure mock instances
        self.mock_instance = MagicMock()
        self.mock_player = MagicMock()
        self.mock_media = MagicMock()
        
        self.mocks['Instance'].return_value = self.mock_instance
        self.mock_instance.media_player_new.return_value = self.mock_player
        self.mock_instance.media_new.return_value = self.mock_media
        
        # Import and create AudioManager
        from src.audio.audio_manager import AudioManager
        self.audio_manager = AudioManager()
    
    def tearDown(self):
        # Stop all patches
        for patcher in self.patches.values():
            patcher.stop()
    
    def test_initialize_success(self):
        # Test initialization
        result = self.audio_manager.initialize()
        
        # Verify result and calls
        self.assertTrue(result)
        self.mocks['Instance'].assert_called_once_with('--no-xlib')
        self.mock_instance.media_player_new.assert_called_once()
        self.mock_player.audio_set_volume.assert_called_once_with(50)
    
    def test_play_url_success(self):
        # Initialize first
        self.audio_manager.initialize()
        
        # Test URL playback
        url = "http://example.com/stream"
        result = self.audio_manager.play_url(url)
        
        # Verify result and calls
        self.assertTrue(result)
        self.mock_instance.media_new.assert_called_once_with(url)
        self.mock_player.set_media.assert_called_once_with(self.mock_media)
        self.mock_player.play.assert_called_once()
    
    def test_stop_playback(self):
        # Initialize first
        self.audio_manager.initialize()
        
        # Test stop
        self.audio_manager.stop()
        
        # Verify calls
        self.mock_player.stop.assert_called_once()
    
    def test_set_volume(self):
        # Initialize first
        self.audio_manager.initialize()
        
        # Test volume setting
        self.audio_manager.set_volume(75)
        
        # Verify calls and value
        self.mock_player.audio_set_volume.assert_called_with(75)
        self.assertEqual(self.audio_manager.current_volume, 75)
    
    def test_cleanup(self):
        # Initialize first
        self.audio_manager.initialize()
        
        # Test cleanup
        self.audio_manager.cleanup()
        
        # Verify calls
        self.mock_player.stop.assert_called_once()
        self.mock_player.release.assert_called_once()
        self.mock_instance.release.assert_called_once()

if __name__ == '__main__':
    unittest.main() 
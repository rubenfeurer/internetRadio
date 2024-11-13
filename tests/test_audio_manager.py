import unittest
from unittest.mock import Mock, patch
import os
from src.audio.audio_manager import AudioManager

class TestAudioManager(unittest.TestCase):
    def setUp(self):
        self.audio_manager = AudioManager()
        # Mock VLC instance and player
        self.audio_manager.instance = Mock()
        self.audio_manager.player = Mock()
        # Set up test sounds directory
        self.test_sounds_dir = os.path.join(os.path.dirname(__file__), 'test_sounds')
        os.makedirs(self.test_sounds_dir, exist_ok=True)
        self.audio_manager.sounds_dir = self.test_sounds_dir

    def tearDown(self):
        self.audio_manager.cleanup()
        # Clean up test files if needed
        if os.path.exists(self.test_sounds_dir):
            for file in os.listdir(self.test_sounds_dir):
                os.remove(os.path.join(self.test_sounds_dir, file))
            os.rmdir(self.test_sounds_dir)

    def test_initialize(self):
        with patch('vlc.Instance') as mock_vlc:
            mock_instance = Mock()
            mock_instance.media_player_new.return_value = Mock()
            mock_vlc.return_value = mock_instance
            
            result = self.audio_manager.initialize()
            
            self.assertTrue(result)
            mock_vlc.assert_called_once_with('--no-xlib')
            mock_instance.media_player_new.assert_called_once()

    def test_initialize_failure(self):
        with patch('vlc.Instance', side_effect=Exception("VLC Error")):
            result = self.audio_manager.initialize()
            self.assertFalse(result)

    def test_play_sound_file_not_found(self):
        result = self.audio_manager.play_sound('nonexistent.wav')
        self.assertFalse(result)

    def test_play_sound_success(self):
        # Create a test sound file
        test_sound = os.path.join(self.test_sounds_dir, 'test.wav')
        with open(test_sound, 'wb') as f:
            f.write(b'RIFF' + b'\x00' * 100)  # Minimal WAV header
        
        # Mock the media creation and playback
        mock_media = Mock()
        self.audio_manager.instance.media_new_path.return_value = mock_media
        self.audio_manager.player.play.return_value = 0
        
        result = self.audio_manager.play_sound('test.wav')
        
        self.assertTrue(result)
        self.audio_manager.instance.media_new_path.assert_called_once()
        self.audio_manager.player.set_media.assert_called_once_with(mock_media)
        self.audio_manager.player.play.assert_called_once()

    def test_play_sound_media_creation_failure(self):
        # Create a test sound file
        test_sound = os.path.join(self.test_sounds_dir, 'test.wav')
        with open(test_sound, 'wb') as f:
            f.write(b'RIFF' + b'\x00' * 100)
            
        self.audio_manager.instance.media_new_path.return_value = None
        result = self.audio_manager.play_sound('test.wav')
        self.assertFalse(result)

    def test_play_sound_playback_failure(self):
        # Create a test sound file
        test_sound = os.path.join(self.test_sounds_dir, 'test.wav')
        with open(test_sound, 'wb') as f:
            f.write(b'RIFF' + b'\x00' * 100)
            
        mock_media = Mock()
        self.audio_manager.instance.media_new_path.return_value = mock_media
        self.audio_manager.player.play.return_value = -1
        
        result = self.audio_manager.play_sound('test.wav')
        self.assertFalse(result)

    def test_set_volume(self):
        self.audio_manager.set_volume(75)
        self.audio_manager.player.audio_set_volume.assert_called_once_with(75)
        self.assertEqual(self.audio_manager.current_volume, 75)

    def test_set_volume_limits(self):
        # Test upper limit
        self.audio_manager.set_volume(150)
        self.audio_manager.player.audio_set_volume.assert_called_with(100)
        
        # Test lower limit
        self.audio_manager.set_volume(-50)
        self.audio_manager.player.audio_set_volume.assert_called_with(0)

    def test_cleanup(self):
        self.audio_manager.cleanup()
        self.audio_manager.player.stop.assert_called_once()
        self.audio_manager.player.release.assert_called_once()
        self.audio_manager.instance.release.assert_called_once()

    def test_cleanup_with_exception(self):
        self.audio_manager.player.stop.side_effect = Exception("Cleanup Error")
        self.audio_manager.cleanup()  # Should not raise exception

    def test_play_url(self):
        url = "http://example.com/stream"
        mock_media = Mock()
        self.audio_manager.instance.media_new.return_value = mock_media
        
        result = self.audio_manager.play_url(url)
        
        self.assertTrue(result)
        self.audio_manager.instance.media_new.assert_called_once_with(url)
        self.audio_manager.player.set_media.assert_called_once_with(mock_media)
        self.audio_manager.player.play.assert_called_once()

    def test_stop(self):
        self.audio_manager.stop()
        self.audio_manager.player.stop.assert_called_once() 
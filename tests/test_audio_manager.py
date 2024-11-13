import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from src.audio.audio_manager import AudioManager

class TestAudioManager(unittest.TestCase):
    def setUp(self):
        self.audio_manager = AudioManager()
        # Mock VLC instance and player
        self.audio_manager.instance = Mock()
        self.audio_manager.player = Mock()
        # Mock the logger properly
        self.audio_manager.logger = Mock()
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
            mock_vlc.assert_called_once_with('--no-xlib --aout=alsa')
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

    @patch('subprocess.run')
    def test_initialize_bcm2835_audio(self, mock_run):
        """Test bcm2835 Headphones audio initialization"""
        # Setup
        mock_run.return_value = MagicMock(returncode=0)
        with patch('vlc.Instance') as mock_vlc, \
             patch('ctypes.CDLL') as mock_cdll, \
             patch('ctypes.util.find_library', return_value='libasound.so.2'):
            
            mock_instance = Mock()
            mock_instance.media_player_new.return_value = Mock()
            mock_vlc.return_value = mock_instance
            
            mock_asound = MagicMock()
            mock_cdll.return_value = mock_asound
            
            # Test
            result = self.audio_manager.initialize()
            
            # Verify
            self.assertTrue(result)
            mock_vlc.assert_called_once_with('--no-xlib --aout=alsa')
            mock_instance.media_player_new.assert_called_once()
            
            # Verify environment variables
            self.assertEqual(os.environ.get('ALSA_IGNORE_UCM'), '1')
            self.assertEqual(os.environ.get('AUDIODEV'), 'hw:2,0')

    def test_alsa_error_handling(self):
        """Test ALSA error handler filtering"""
        with patch('ctypes.CDLL') as mock_cdll, \
             patch('ctypes.util.find_library', return_value='libasound.so.2'), \
             patch('vlc.Instance') as mock_vlc:  # Add VLC mock
            
            # Setup VLC mock
            mock_instance = Mock()
            mock_instance.media_player_new.return_value = Mock()
            mock_vlc.return_value = mock_instance
            
            # Setup mock logger
            self.audio_manager.logger = MagicMock()
            
            mock_asound = MagicMock()
            mock_cdll.return_value = mock_asound
            
            # Initialize audio manager
            result = self.audio_manager.initialize()
            self.assertTrue(result)
            
            # Verify error handler was set
            mock_asound.snd_lib_error_set_handler.assert_called_once()
            
            # Get the error handler function
            handler = mock_asound.snd_lib_error_set_handler.call_args[0][0]
            
            # Test ignored patterns
            ignored_messages = [
                b"snd_use_case_mgr_open test error",
                b"function error evaluating strings",
                b"Parse arguments error test",
                b"Evaluate error test",
                b"returned error test",
                b"error evaluating test",
                b"function error test"
            ]
            
            # Test each ignored pattern
            for msg in ignored_messages:
                handler(b"file", 1, b"some_func", -1, msg)
                self.audio_manager.logger.error.assert_not_called()
                self.audio_manager.logger.error.reset_mock()
            
            # Test non-ignored message
            handler(b"file", 1, b"some_func", -1, b"some other error")
            self.audio_manager.logger.error.assert_called_once_with("ALSA: some other error")

    def test_alsa_error_suppression(self):
        """Test that specific ALSA errors are properly suppressed"""
        with patch('ctypes.CDLL') as mock_cdll, \
             patch('ctypes.util.find_library', return_value='libasound.so.2'):
            
            mock_asound = MagicMock()
            mock_cdll.return_value = mock_asound
            
            # Initialize audio manager
            self.audio_manager.initialize()
            
            # Get the error handler function
            handler = mock_asound.snd_lib_error_set_handler.call_args[0][0]
            
            # Test specific error message
            test_message = b"snd_use_case_mgr_open error: failed to import hw:0 use case configuration -2"
            handler(b"file", 1, b"some_func", -1, test_message)
            
            # Verify this specific error was suppressed
            self.audio_manager.logger.error.assert_not_called()

    def test_specific_alsa_hw_errors(self):
        """Test that specific hardware configuration errors are suppressed"""
        with patch('ctypes.CDLL') as mock_cdll, \
             patch('ctypes.util.find_library', return_value='libasound.so.2'), \
             patch('vlc.Instance') as mock_vlc:  # Add VLC mock
            
            # Setup VLC mock
            mock_instance = Mock()
            mock_instance.media_player_new.return_value = Mock()
            mock_vlc.return_value = mock_instance
            
            mock_asound = MagicMock()
            mock_cdll.return_value = mock_asound
            
            # Initialize audio manager with mocked logger
            self.audio_manager.logger = Mock()
            self.audio_manager.initialize()
            
            # Get the error handler function
            handler = mock_asound.snd_lib_error_set_handler.call_args[0][0]
            
            # Test all hardware configurations
            for hw_num in [0, 1, 2]:
                test_message = f"error: failed to import hw:{hw_num} use case configuration -2".encode()
                handler(b"file", 1, b"some_func", -1, test_message)
                self.audio_manager.logger.error.assert_not_called()
                self.audio_manager.logger.error.reset_mock()

    def test_alsa_master_control_errors(self):
        """Test that master control related errors are suppressed"""
        with patch('ctypes.CDLL') as mock_cdll, \
             patch('ctypes.util.find_library', return_value='libasound.so.2'):
            
            mock_asound = MagicMock()
            mock_cdll.return_value = mock_asound
            
            # Initialize audio manager with mocked logger
            self.audio_manager.logger = Mock()
            self.audio_manager.initialize()
            
            # Get the error handler function
            handler = mock_asound.snd_lib_error_set_handler.call_args[0][0]
            
            # Test master control error messages
            test_messages = [
                b"Could not unmute Master",
                b"Unable to find simple control 'Master',0",
                b"Could not set Master volume",
                b"main.c:1541:(snd_use_case_mgr_open) error: failed to import hw:2"
            ]
            
            for msg in test_messages:
                handler(b"file", 1, b"some_func", -1, msg)
                self.audio_manager.logger.error.assert_not_called()
                self.audio_manager.logger.error.reset_mock()

    def test_alsa_exact_error_patterns(self):
        """Test that specific ALSA error messages are exactly matched and suppressed"""
        with patch('ctypes.CDLL') as mock_cdll, \
             patch('ctypes.util.find_library', return_value='libasound.so.2'):
            
            mock_asound = MagicMock()
            mock_cdll.return_value = mock_asound
            
            # Initialize audio manager with mocked logger
            self.audio_manager.logger = Mock()
            self.audio_manager.initialize()
            
            # Get the error handler function
            handler = mock_asound.snd_lib_error_set_handler.call_args[0][0]
            
            # Test exact error messages
            test_messages = [
                b"alsa-lib main.c:1541:(snd_use_case_mgr_open) error: failed to import hw:0 use case configuration -2",
                b"alsa-lib main.c:1541:(snd_use_case_mgr_open) error: failed to import hw:1 use case configuration -2",
                b"alsa-lib main.c:1541:(snd_use_case_mgr_open) error: failed to import hw:2 use case configuration -2"
            ]
            
            for msg in test_messages:
                handler(b"file", 1, b"some_func", -1, msg)
                self.audio_manager.logger.error.assert_not_called()
                self.audio_manager.logger.error.reset_mock()

    def test_alsa_warning_messages(self):
        """Test that warning messages are properly suppressed"""
        with patch('ctypes.CDLL') as mock_cdll, \
             patch('ctypes.util.find_library', return_value='libasound.so.2'):
            
            mock_asound = MagicMock()
            mock_cdll.return_value = mock_asound
            
            # Initialize audio manager with mocked logger
            self.audio_manager.logger = Mock()
            self.audio_manager.initialize()
            
            # Get the error handler function
            handler = mock_asound.snd_lib_error_set_handler.call_args[0][0]
            
            # Test warning messages
            test_messages = [
                b"Warning: Could not unmute Master",
                b"amixer: Unable to find simple control 'Master',0",
                b"Warning: Could not set Master volume"
            ]
            
            for msg in test_messages:
                handler(b"file", 1, b"some_func", -1, msg)
                self.audio_manager.logger.error.assert_not_called()
                self.audio_manager.logger.error.reset_mock()
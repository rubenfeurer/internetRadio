import logging
import vlc
import os
from typing import Optional
import ctypes
import ctypes.util

class AudioManager:
    def __init__(self, default_volume: int = 50, volume_step: int = 5):
        self.logger = logging.getLogger('audio')
        self.instance: Optional[vlc.Instance] = None
        self.player: Optional[vlc.MediaPlayer] = None
        self.current_volume: int = default_volume
        self.volume_step: int = volume_step
        self.sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sounds')
    
    def initialize(self) -> bool:
        """Initialize audio system"""
        try:
            self.logger.info("Initializing audio system...")
            
            # Set environment variables for BCM2835 audio
            os.environ['ALSA_IGNORE_UCM'] = '1'
            os.environ['AUDIODEV'] = 'hw:2,0'
            
            # Set ALSA error handling
            def py_error_handler(filename, line, function, err, fmt):
                if isinstance(fmt, bytes):
                    fmt_str = fmt.decode('utf-8', errors='ignore')
                else:
                    fmt_str = str(fmt)
                
                if '%' in fmt_str:
                    return
                
                # Common ALSA patterns to ignore
                ignore_patterns = [
                    "snd_use_case_mgr_open",
                    "failed to import hw:",
                    "Could not unmute",
                    "Unable to find simple control",
                    "Could not set",
                    "Warning: Could not",
                    "amixer: Unable to find",
                    "alsa-lib",
                    "function error evaluating strings",
                    "Parse arguments error",
                    "Evaluate error",
                    "returned error",
                    "error evaluating",
                    "function error"
                ]
                
                if any(pattern in fmt_str for pattern in ignore_patterns):
                    if self.logger.isEnabledFor(logging.DEBUG):
                        self.logger.debug(f"Suppressed ALSA message: {fmt_str}")
                    return
                
                self.logger.error(f"ALSA: {fmt_str}")
            
            # Set up ALSA error handler
            ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int,
                                                ctypes.c_char_p, ctypes.c_int,
                                                ctypes.c_char_p)
            
            c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
            try:
                asound = ctypes.CDLL(ctypes.util.find_library('asound'))
                asound.snd_lib_error_set_handler(c_error_handler)
                self.logger.info("ALSA error handler initialized")
            except Exception as e:
                self.logger.debug(f"Non-critical: Could not set ALSA error handler: {e}")
            
            # Initialize VLC with ALSA output
            self.instance = vlc.Instance('--no-xlib --aout=alsa')
            self.player = self.instance.media_player_new()
            self.set_volume(self.current_volume)
            self.logger.info("AudioManager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing audio system: {str(e)}")
            return False
    
    def play_url(self, url: str) -> bool:
        """Play audio from URL"""
        try:
            if not self.instance or not self.player:
                self.logger.error("AudioManager not initialized")
                return False
            
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing URL: {str(e)}")
            return False
    
    def play_sound(self, sound_file: str) -> bool:
        """Play a local sound file"""
        try:
            if not self.instance or not self.player:
                self.logger.error("AudioManager not initialized")
                return False
            
            sound_path = os.path.join(self.sounds_dir, sound_file)
            if not os.path.isfile(sound_path):
                self.logger.error(f"Sound file not found: {sound_path}")
                return False
            
            media = self.instance.media_new_path(sound_path)
            if not media:
                self.logger.error(f"Failed to create media for {sound_path}")
                return False
            
            self.player.set_media(media)
            return self.player.play() != -1
            
        except Exception as e:
            self.logger.error(f"Error playing sound: {str(e)}")
            return False
    
    def stop(self) -> None:
        """Stop playback"""
        try:
            if self.player:
                self.player.stop()
        except Exception as e:
            self.logger.error(f"Error stopping playback: {str(e)}")
    
    def set_volume(self, volume: int) -> None:
        """Set volume level (0-100)"""
        try:
            if self.player:
                self.current_volume = max(0, min(100, volume))
                self.player.audio_set_volume(self.current_volume)
        except Exception as e:
            self.logger.error(f"Error setting volume: {str(e)}")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.player:
                self.player.stop()
                self.player.release()
            if self.instance:
                self.instance.release()
            self.logger.info("AudioManager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}") 
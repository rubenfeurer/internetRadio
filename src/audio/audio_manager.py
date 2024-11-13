import logging
import vlc
import os
from typing import Optional

class AudioManager:
    def __init__(self, default_volume: int = 50, volume_step: int = 5):
        self.logger = logging.getLogger('audio')
        self.instance: Optional[vlc.Instance] = None
        self.player: Optional[vlc.MediaPlayer] = None
        self.current_volume: int = default_volume  # Use the passed default volume
        self.volume_step: int = volume_step  # Store volume step
        self.sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sounds')
    
    def initialize(self) -> bool:
        """Initialize VLC instance and media player"""
        try:
            self.logger.info("Initializing AudioManager...")
            self.instance = vlc.Instance('--no-xlib')
            self.player = self.instance.media_player_new()
            self.set_volume(self.current_volume)
            self.logger.info("AudioManager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error("Error initializing AudioManager: %s", str(e))
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
            self.logger.error("Error playing URL: %s", str(e))
            return False
    
    def stop(self) -> None:
        """Stop playback"""
        try:
            if not self.player:
                self.logger.error("Player not initialized")
                return
                
            self.player.stop()
            
        except Exception as e:
            self.logger.error("Error stopping playback: %s", str(e))
    
    def set_volume(self, volume: int) -> None:
        """Set volume level (0-100)"""
        try:
            if not self.player:
                self.logger.error("Player not initialized")
                return
                
            # Ensure volume is within valid range
            volume = max(0, min(100, volume))
            self.player.audio_set_volume(volume)
            self.current_volume = volume
            
        except Exception as e:
            self.logger.error("Error setting volume: %s", str(e))
    
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
            self.logger.error("Error during cleanup: %s", str(e))
    
    def play_sound(self, sound_file: str) -> bool:
        """Play a local sound file"""
        try:
            if not self.instance or not self.player:
                self.logger.error("AudioManager not initialized")
                return False
            
            # Construct full path
            sound_path = os.path.join(self.sounds_dir, sound_file)
            
            # Check if file exists
            if not os.path.isfile(sound_path):
                self.logger.error(f"Sound file not found: {sound_path}")
                return False
                
            # Create media from file
            media = self.instance.media_new_path(sound_path)
            if not media:
                self.logger.error(f"Failed to create media for {sound_path}")
                return False
                
            self.player.set_media(media)
            result = self.player.play()
            
            if result == -1:
                self.logger.error(f"Failed to play sound: {sound_path}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing sound: {str(e)}")
            return False 
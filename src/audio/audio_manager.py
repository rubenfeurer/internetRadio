import logging
import vlc
from typing import Optional

class AudioManager:
    def __init__(self):
        self.logger = logging.getLogger('audio')
        self.instance: Optional[vlc.Instance] = None
        self.player: Optional[vlc.MediaPlayer] = None
        self.current_volume: int = 50  # Default volume (0-100)
    
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
import logging
from typing import Optional, Dict
from ..hardware.gpio_manager import GPIOManager
from ..audio.audio_manager import AudioManager
from ..utils.logger import Logger

class RadioController:
    def __init__(self):
        self.logger = Logger(__name__)
        self.logger.debug("Creating RadioController")
        self.gpio_manager = GPIOManager()
        self.audio_manager = AudioManager()
        self.is_playing = False
        self.current_volume = 50
        self.logger.debug(f"AudioManager instance: {self.audio_manager}")
    
    def initialize(self) -> bool:
        """Initialize hardware components"""
        try:
            if not self.gpio_manager.initialize():
                return False
            if not self.audio_manager.initialize():
                self.gpio_manager.cleanup()
                return False
                
            self._setup_gpio_callbacks()
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing RadioController: {e}")
            return False
    
    def _setup_gpio_callbacks(self) -> None:
        """Setup GPIO button and encoder callbacks"""
        self.gpio_manager.button.when_pressed = self.toggle_playback
        self.gpio_manager.encoder.when_rotated_clockwise = self.volume_up
        self.gpio_manager.encoder.when_rotated_counter_clockwise = self.volume_down
    
    def toggle_playback(self) -> None:
        """Toggle radio playback"""
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()
    
    def start_playback(self, url: Optional[str] = None) -> bool:
        """Start playing stream"""
        try:
            if url is None:
                self.logger.error("No URL provided for playback")
                return False
                
            self.logger.debug(f"Attempting to play URL: {url}")
            self.logger.debug(f"Using AudioManager instance: {self.audio_manager}")
            
            success = self.audio_manager.play_url(url)
            self.logger.debug(f"play_url result: {success}")
            
            if success:
                self.is_playing = True
                self.gpio_manager.start_led_blink(0.5, 0.5)
                self.logger.info(f"Started playback: {url}")
                return True
            else:
                self.logger.error("Failed to start playback")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in start_playback: {e}")
            return False
    
    def stop_playback(self) -> None:
        """Stop current playback"""
        self.audio_manager.stop()
        self.is_playing = False
        self.gpio_manager.set_led_state(False)
    
    def volume_up(self) -> None:
        """Increase volume by 5%"""
        try:
            self.logger.debug(f"Current volume before increase: {self.current_volume}")
            self.current_volume = min(100, self.current_volume + 5)
            self.logger.debug(f"Setting volume to: {self.current_volume}")
            self.logger.debug(f"Using AudioManager instance: {self.audio_manager}")
            self.audio_manager.set_volume(self.current_volume)
            self.logger.debug("Volume set successfully")
        except Exception as e:
            self.logger.error(f"Error in volume_up: {e}")
    
    def volume_down(self) -> None:
        """Decrease volume by 5%"""
        try:
            self.current_volume = max(0, self.current_volume - 5)
            self.audio_manager.set_volume(self.current_volume)
            self.logger.debug(f"Volume down: {self.current_volume}")
        except Exception as e:
            self.logger.error(f"Error in volume_down: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self.stop_playback()
            self.gpio_manager.cleanup()
            self.audio_manager.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_playback_status(self) -> Dict:
        """Get current playback status"""
        try:
            return {
                'is_running': self.is_playing,
                'current_stream': self.current_stream if self.is_playing else None
            }
        except Exception as e:
            self.logger.error(f"Error getting playback status: {e}")
            return {
                'is_running': False,
                'current_stream': None,
                'error': str(e)
            }
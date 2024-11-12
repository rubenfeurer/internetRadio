from typing import Dict, List, Optional
from ..hardware.gpio_manager import GPIOManager
from ..audio.audio_manager import AudioManager
from ..utils.logger import Logger
import json
import os

class RadioController:
    def __init__(self):
        self.logger = Logger(__name__)
        self.gpio_manager = GPIOManager()
        self.audio_manager = AudioManager()
        self.is_playing = False
        self.current_stream = None
        self.current_volume = 50  # Default volume
        self.config_path = os.path.join(os.path.dirname(__file__), '../../config/streams.json')
        self.default_streams = self.load_streams()

    def initialize(self) -> bool:
        """Initialize radio components"""
        try:
            if not self.gpio_manager.initialize():
                self.logger.error("Failed to initialize GPIO")
                return False
                
            if not self.audio_manager.initialize():
                self.logger.error("Failed to initialize audio")
                return False
                
            # Set initial volume
            self.audio_manager.set_volume(self.current_volume)
            
            # Set up GPIO callbacks
            self.setup_gpio_handlers()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing radio: {e}")
            return False

    def setup_gpio_handlers(self) -> None:
        """Set up GPIO button and encoder handlers"""
        try:
            self.gpio_manager.set_button_callback(self.handle_button_press)
            self.gpio_manager.set_encoder_callback(self.handle_volume_change)
        except Exception as e:
            self.logger.error(f"Error setting up GPIO handlers: {e}")

    def handle_button_press(self) -> None:
        """Handle physical button press"""
        try:
            if self.is_playing:
                self.stop_playback()
            else:
                self.start_playback(self.default_streams[0]['url'])
        except Exception as e:
            self.logger.error(f"Error handling button press: {e}")

    def handle_volume_change(self, value: int) -> None:
        """Handle volume encoder rotation"""
        try:
            new_volume = max(0, min(100, self.current_volume + value))
            self.set_volume(new_volume)
        except Exception as e:
            self.logger.error(f"Error handling volume change: {e}")

    def start_playback(self, url: str) -> bool:
        """Start playing a stream"""
        try:
            if self.audio_manager.play_url(url):
                self.is_playing = True
                self.current_stream = url
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error starting playback: {e}")
            return False

    def stop_playback(self) -> bool:
        """Stop current playback"""
        try:
            if self.audio_manager.stop():
                self.is_playing = False
                self.current_stream = None
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error stopping playback: {e}")
            return False

    def set_volume(self, volume: int) -> None:
        """Set audio volume"""
        try:
            self.current_volume = max(0, min(100, volume))
            self.audio_manager.set_volume(self.current_volume)
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")

    def set_led_state(self, blink: bool = False, on_time: float = 1, off_time: float = 1) -> None:
        """Set LED state"""
        try:
            if blink:
                self.gpio_manager.set_led_blink(on_time, off_time)
            else:
                self.gpio_manager.set_led(True)
        except Exception as e:
            self.logger.error(f"Error setting LED state: {e}")

    def load_streams(self) -> List[Dict]:
        """Load stream configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"Error loading streams: {e}")
            return []

    def get_default_streams(self) -> List[Dict]:
        """Get list of default streams"""
        return self.default_streams

    def get_spare_links(self) -> List[Dict]:
        """Get list of spare stream links"""
        try:
            # Load all available streams from configuration
            all_streams = self.load_streams()
            # Filter out default streams
            default_urls = [s['url'] for s in self.default_streams]
            return [s for s in all_streams if s['url'] not in default_urls]
        except Exception as e:
            self.logger.error(f"Error getting spare links: {e}")
            return []

    def update_stream(self, channel: str, url: str) -> bool:
        """Update stream configuration"""
        try:
            streams = self.load_streams()
            for stream in streams:
                if stream['url'] == url:
                    # Update default streams
                    if channel == 'link1':
                        self.default_streams[0] = stream
                    elif channel == 'link2':
                        self.default_streams[1] = stream
                    elif channel == 'link3':
                        self.default_streams[2] = stream
                    
                    # Save updated configuration
                    with open(self.config_path, 'w') as f:
                        json.dump(streams, f, indent=4)
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating stream: {e}")
            return False

    def monitor(self) -> None:
        """Monitor radio state"""
        try:
            # Check if stream is still playing
            if self.is_playing and not self.audio_manager.is_playing():
                self.is_playing = False
                self.current_stream = None
        except Exception as e:
            self.logger.error(f"Error monitoring radio state: {e}")
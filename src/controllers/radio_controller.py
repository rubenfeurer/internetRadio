from typing import Dict, List, Optional
from src.utils.logger import Logger
from src.utils.stream_manager import StreamManager
from src.audio.audio_manager import AudioManager
from src.hardware.gpio_manager import GPIOManager
import json
import os

class RadioController:
    def __init__(self, audio_manager=None, gpio_manager=None, stream_manager=None):
        self.logger = Logger.get_logger(__name__)
        self.logger.debug("Initializing RadioController")
        self.audio_manager = audio_manager or AudioManager()
        self.gpio_manager = gpio_manager or GPIOManager()
        self.stream_manager = stream_manager or StreamManager()
        self.current_volume = 50  # Default volume
        self.initialized = False
        self.is_playing = False

    def initialize(self) -> bool:
        """Initialize the controller and its dependencies"""
        try:
            if self.audio_manager:
                self.audio_manager.initialize()
            if self.gpio_manager:
                self.gpio_manager.initialize()
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Error initializing RadioController: {e}")
            return False

    def start_playback(self, url: str) -> bool:
        """Start playing a stream"""
        try:
            if not self.initialized:
                self.logger.error("RadioController not initialized")
                return False
            if not self.audio_manager:
                self.logger.error("No audio manager available")
                return False
            success = self.audio_manager.play_url(url)
            if success:
                self.is_playing = True
                self.gpio_manager.start_led_blink()
            return success
        except Exception as e:
            self.logger.error(f"Error starting playback: {e}")
            return False

    def stop_playback(self) -> None:
        """Stop current playback"""
        if self.audio_manager:
            self.audio_manager.stop()
        if self.gpio_manager:
            self.gpio_manager.set_led_state(False)
        self.is_playing = False

    def volume_up(self) -> None:
        """Increase volume"""
        if not self.initialized or not self.audio_manager:
            self.logger.error("RadioController not initialized or no audio manager")
            return
        self.current_volume = min(100, self.current_volume + 5)
        if self.audio_manager:
            self.audio_manager.set_volume(self.current_volume)

    def volume_down(self) -> None:
        """Decrease volume"""
        if not self.initialized or not self.audio_manager:
            self.logger.error("RadioController not initialized or no audio manager")
            return
        self.current_volume = max(0, self.current_volume - 5)
        if self.audio_manager:
            self.audio_manager.set_volume(self.current_volume)

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.audio_manager:
            self.audio_manager.cleanup()
        if self.gpio_manager:
            self.gpio_manager.cleanup()
        self.initialized = False
        self.is_playing = False

    def set_led_state(self, blink: bool = False, on_time: float = 1.0, off_time: float = 1.0) -> None:
        """Set LED state for status indication
        
        Args:
            blink (bool): Whether LED should blink
            on_time (float): Time in seconds LED should stay on during blink
            off_time (float): Time in seconds LED should stay off during blink
        """
        try:
            if not self.gpio_manager:
                self.logger.error("GPIO manager not initialized")
                return
            
            if blink:
                self.gpio_manager.led_blink(on_time=on_time, off_time=off_time)
            else:
                self.gpio_manager.led_on()
            
        except Exception as e:
            self.logger.error(f"Error setting LED state: {e}")
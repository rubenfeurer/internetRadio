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
        self.audio_manager = audio_manager or AudioManager()
        self.gpio_manager = gpio_manager or GPIOManager()
        self.stream_manager = stream_manager or StreamManager()
        self.current_volume = 50  # Default volume
        self.logger.debug("Initializing RadioController")

    def initialize(self) -> bool:
        """Initialize radio controller"""
        try:
            self.audio_manager.initialize()
            self.gpio_manager.initialize()
            self.audio_manager.set_volume(self.current_volume)
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize radio: {e}")
            return False

    def start_stream(self, stream_name: str) -> bool:
        """Start playing a stream"""
        stream = self.stream_manager.get_stream(stream_name)
        if stream and 'url' in stream:
            return self.audio_manager.play_url(stream['url'])
        return False
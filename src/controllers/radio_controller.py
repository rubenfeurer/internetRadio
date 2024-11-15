from typing import Dict, List, Optional
from src.utils.logger import Logger
from src.utils.stream_manager import StreamManager
from src.audio.audio_manager import AudioManager
from src.hardware.gpio_manager import GPIOManager
import json
import os
import logging

class RadioController:
    def __init__(self):
        self.logger = logging.getLogger('radio')
        self.stream_manager = None
        self.initialized = False
        
        try:
            if not os.environ.get('TESTING'):
                self.stream_manager = StreamManager()
            self.initialized = True
            self.logger.info("RadioController initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing RadioController: {e}")
            
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.stream_manager:
                self.stream_manager.cleanup()
            self.initialized = False
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
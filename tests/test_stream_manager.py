import os
import tempfile
from pathlib import Path
import toml
import pytest
from src.utils.stream_manager import StreamManager
from src.models.radio_stream import RadioStream
from src.utils.logger import Logger

class TestStreamManager:
    def setUp(self):
        # Create a temporary directory for test config
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.log_dir = os.path.join(self.temp_dir, 'logs')

        # Set logger to test mode
        Logger.reset()
        Logger.set_test_mode(self.log_dir)

        # Create test streams
        self.test_streams = {
            'links': [
                {
                    'name': 'Test Radio 1',
                    'url': 'http://test1.com/stream',
                    'country': 'Test Country',
                    'location': 'Test City'
                },
                {
                    'name': 'Test Radio 2',
                    'url': 'http://test2.com/stream',
                    'country': 'Test Country',
                    'location': 'Another City'
                }
            ]
        }

        # Write test streams to file
        with open(os.path.join(self.config_dir, 'streams.toml'), 'w') as f:
            toml.dump(self.test_streams, f)

        self.stream_manager = StreamManager(config_dir=str(self.temp_dir))
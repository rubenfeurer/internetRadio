import os
import toml
from dataclasses import asdict
from typing import List, Optional, Dict, Any
from src.models.radio_stream import RadioStream
from src.utils.logger import Logger

class StreamManager:
    def __init__(self, config_dir: str = None):
        """Initialize StreamManager"""
        self.logger = Logger.get_logger(__name__)
        self.config_dir = config_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.streams_file = os.path.join(self.config_dir, 'streams.toml')
        self.streams: List[RadioStream] = []
        self._load_streams()

    def _convert_dict_to_stream(self, data: Dict[str, Any]) -> RadioStream:
        """Convert dictionary to RadioStream object"""
        return RadioStream(
            name=data.get('name', ''),
            url=data.get('url', ''),
            country=data.get('country', ''),
            location=data.get('location', ''),
            description=data.get('description'),
            genre=data.get('genre'),
            language=data.get('language'),
            bitrate=data.get('bitrate')
        )

    def _load_streams(self) -> None:
        """Load streams from TOML file"""
        try:
            if os.path.exists(self.streams_file):
                with open(self.streams_file, 'r') as f:
                    data = toml.load(f)
                    self.streams = [self._convert_dict_to_stream(stream) 
                                  for stream in data.get('links', [])]
            else:
                self.streams = []
        except Exception as e:
            self.logger.error(f"Error loading streams: {str(e)}")
            self.streams = []

    def get_all_streams(self) -> List[RadioStream]:
        """Get all available streams"""
        return self.streams

    def get_stream_by_name(self, name: str) -> Optional[RadioStream]:
        """Get stream by name"""
        return next((s for s in self.streams if s.name == name), None)

    def get_streams_by_country(self, country: str) -> List[RadioStream]:
        """Get streams by country"""
        return [s for s in self.streams if s.country == country]

    def get_streams_by_location(self, location: str) -> List[RadioStream]:
        """Get streams by location"""
        return [s for s in self.streams if s.location == location]

    def add_stream(self, stream: RadioStream) -> bool:
        """Add new stream"""
        try:
            if not isinstance(stream, RadioStream):
                raise ValueError("Invalid stream object")
            self.streams.append(stream)
            return self.save_streams()
        except Exception as e:
            self.logger.error(f"Error adding stream: {str(e)}")
            return False

    def remove_stream(self, name: str) -> bool:
        """Remove stream by name"""
        try:
            original_length = len(self.streams)
            self.streams = [s for s in self.streams if s.name != name]
            if len(self.streams) < original_length:
                return self.save_streams()
            return False
        except Exception as e:
            self.logger.error(f"Error removing stream: {str(e)}")
            return False

    def save_streams(self) -> bool:
        """Save streams to TOML file"""
        try:
            with open(self.streams_file, 'w') as f:
                toml.dump({'links': [asdict(s) for s in self.streams]}, f)
            return True
        except Exception as e:
            self.logger.error(f"Error saving streams: {str(e)}")
            return False

    def load_streams(self) -> bool:
        """Load streams from file"""
        try:
            if not self.streams_file.exists():
                self.logger.warning(f"Streams file not found: {self.streams_file}")
                return False

            with open(self.streams_file) as f:
                data = toml.load(f)
                
            if not isinstance(data, dict) or 'links' not in data:
                self.logger.error("Invalid streams file format")
                return False
                
            self.streams = [
                RadioStream(
                    name=stream.get('name', ''),
                    url=stream.get('url', ''),
                    country=stream.get('country', ''),
                    location=stream.get('location', '')
                )
                for stream in data.get('links', [])
            ]
            
            self.logger.info(f"Successfully loaded {len(self.streams)} streams")
            return True
        except Exception as e:
            self.logger.error(f"Error loading streams: {e}")
            return False 
import toml
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from ..utils.logger import Logger
import os

@dataclass
class RadioStream:
    name: str
    url: str
    country: str
    location: str

class StreamManager:
    def __init__(self, config_dir: str = None):
        self.logger = Logger(__name__)
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent / 'config'
        self.streams_file = self.config_dir / 'streams.toml'
        self.streams: List[RadioStream] = []
        self._load_streams()

    def _load_streams(self) -> None:
        """Load streams from TOML file"""
        try:
            with open(self.streams_file) as f:
                data = toml.load(f)
                self.streams = [
                    RadioStream(**stream) for stream in data.get('links', [])
                ]
            self.logger.info(f"Loaded {len(self.streams)} streams")
        except Exception as e:
            self.logger.error(f"Error loading streams: {e}")
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
            if not self.get_stream_by_name(stream.name):
                self.streams.append(stream)
                return self._save_streams()
            return False
        except Exception as e:
            self.logger.error(f"Error adding stream: {e}")
            return False

    def remove_stream(self, name: str) -> bool:
        """Remove stream by name"""
        try:
            initial_length = len(self.streams)
            self.streams = [s for s in self.streams if s.name != name]
            if len(self.streams) < initial_length:
                return self._save_streams()
            return False
        except Exception as e:
            self.logger.error(f"Error removing stream: {e}")
            return False

    def _save_streams(self) -> bool:
        """Save streams to TOML file"""
        try:
            data = {
                'links': [
                    {
                        'name': s.name,
                        'url': s.url,
                        'country': s.country,
                        'location': s.location
                    } for s in self.streams
                ]
            }
            with open(self.streams_file, 'w') as f:
                toml.dump(data, f)
            return True
        except Exception as e:
            self.logger.error(f"Error saving streams: {e}")
            return False

    def save_streams(self) -> bool:
        """Save streams to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.streams_file), exist_ok=True)
            
            # Prepare data structure
            data = {
                'links': [
                    {
                        'name': stream.name,
                        'url': stream.url,
                        'country': getattr(stream, 'country', ''),
                        'location': getattr(stream, 'location', '')
                    }
                    for stream in self.streams
                ]
            }
            
            self.logger.debug(f"Saving streams to {self.streams_file}: {data}")
            
            # Save to file
            with open(self.streams_file, 'w') as f:
                toml.dump(data, f)
            
            # Verify save was successful
            if not os.path.exists(self.streams_file):
                self.logger.error("Failed to create streams file")
                return False
            
            self.logger.info(f"Successfully saved {len(self.streams)} streams")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save streams: {e}")
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
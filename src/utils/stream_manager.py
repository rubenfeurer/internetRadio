import os
import toml
from dataclasses import asdict
from typing import List, Optional, Dict, Any
from src.models.radio_stream import RadioStream
from src.utils.logger import Logger
import vlc
import time
import threading

class StreamManager:
    def __init__(self, config_dir: str = None):
        """Initialize StreamManager"""
        # Initialize logger first
        self.logger = Logger('stream', log_dir='/home/radio/internetRadio/logs')
        
        # Set up configuration
        self.config_dir = config_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.streams_file = os.path.join(self.config_dir, 'streams.toml')
        self.streams: List[RadioStream] = []
        
        try:
            # Initialize VLC instance
            self.instance = vlc.Instance('--no-xlib')
            self.player = self.instance.media_player_new()
            self.media = None
            self.current_url = None
            self.is_playing = False
            self.volume = 50  # Default volume
            
            # Initialize thread for monitoring playback
            self.monitor_thread = None
            self.should_monitor = False
            
            # Load streams
            self._load_streams()
            
            self.logger.info("StreamManager initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing StreamManager: {e}")
            raise

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

    def play(self, url: str) -> bool:
        """Start playing a stream from the given URL"""
        try:
            if url != self.current_url:
                self.stop()
                self.media = self.instance.media_new(url)
                self.player.set_media(self.media)
                self.current_url = url
            
            result = self.player.play()
            if result == 0:
                self.is_playing = True
                self.start_monitoring()
                self.logger.info(f"Started playing stream: {url}")
                return True
            else:
                self.logger.error(f"Failed to start playback: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in play: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the current stream"""
        try:
            self.should_monitor = False
            if self.monitor_thread:
                self.monitor_thread.join()
            
            self.player.stop()
            self.is_playing = False
            self.current_url = None
            self.logger.info("Stopped playback")
            
        except Exception as e:
            self.logger.error(f"Error in stop: {e}")
    
    def set_volume(self, volume: int) -> None:
        """Set the volume level (0-100)"""
        try:
            volume = max(0, min(100, volume))
            self.player.audio_set_volume(volume)
            self.volume = volume
            self.logger.info(f"Volume set to {volume}")
            
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
    
    def get_volume(self) -> int:
        """Get the current volume level"""
        return self.volume
    
    def start_monitoring(self) -> None:
        """Start monitoring playback status"""
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self.should_monitor = True
            self.monitor_thread = threading.Thread(target=self._monitor_playback)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
    
    def _monitor_playback(self) -> None:
        """Monitor playback status and handle errors"""
        while self.should_monitor:
            try:
                state = self.player.get_state()
                if state == vlc.State.Playing:
                    self.logger.info("Playing")
                elif state == vlc.State.Paused:
                    self.logger.info("Paused")
                elif state == vlc.State.Stopped:
                    self.logger.info("Stopped")
                elif state == vlc.State.Error:
                    self.logger.error("Error")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in _monitor_playback: {e}")
                break 
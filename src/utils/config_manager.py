import toml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .logger import Logger
import os

@dataclass
class AudioConfig:
    default_volume: int = 50
    volume_step: int = 5
    sounds_enabled: bool = True

@dataclass
class NetworkConfig:
    saved_networks: list = None
    ap_ssid: str = "InternetRadio"
    ap_password: str = "radio123"
    connection_timeout: int = 30

@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/radio.log"

class ConfigManager:
    def __init__(self, config_dir: str = None):
        self.logger = Logger(__name__)
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent / 'config'
        self.radio_file = self.config_dir / 'radio.toml'
        
        # Initialize with defaults
        self.audio = AudioConfig()
        self.network = NetworkConfig()
        self.logging = LoggingConfig()
        
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from TOML file"""
        try:
            config_data = {}
            
            # Load default config first
            default_config_path = self.config_dir / 'default.toml'
            if default_config_path.exists():
                with open(default_config_path) as f:
                    config_data = toml.load(f)
                    self.logger.debug(f"Loaded default config: {config_data}")

            # Override with user config if exists
            if self.radio_file.exists():
                with open(self.radio_file) as f:
                    user_data = toml.load(f)
                    self.logger.debug(f"Loaded user config: {user_data}")
                    self._merge_config_data(config_data, user_data)
                    self.logger.debug(f"Merged config: {config_data}")
            
            # Update instance attributes
            self._update_from_dict(config_data)
            self.logger.debug(f"Final config state: audio.default_volume={self.audio.default_volume}")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise

    def _merge_config_data(self, base: dict, override: dict) -> None:
        """Deep merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config_data(base[key], value)
            else:
                base[key] = value

    def _save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            config_data = {
                'audio': {
                    'default_volume': self.audio.default_volume,
                    'volume_step': self.audio.volume_step,
                    'sounds_enabled': self.audio.sounds_enabled
                },
                'network': {
                    'saved_networks': self.network.saved_networks,
                    'ap_ssid': self.network.ap_ssid,
                    'ap_password': self.network.ap_password,
                    'connection_timeout': self.network.connection_timeout
                },
                'logging': {
                    'level': self.logging.level
                }
            }
            
            self.logger.debug(f"Saving config: {config_data}")
            os.makedirs(os.path.dirname(self.radio_file), exist_ok=True)
            with open(self.radio_file, 'w') as f:
                toml.dump(config_data, f)
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def update_audio_config(self, **kwargs) -> bool:
        """Update audio configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.audio, key):
                    setattr(self.audio, key, value)
            return self._save_config()
        except Exception as e:
            self.logger.error(f"Error updating audio config: {e}")
            return False

    def update_network_config(self, **kwargs) -> bool:
        """Update network configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.network, key):
                    setattr(self.network, key, value)
            return self._save_config()
        except Exception as e:
            self.logger.error(f"Error updating network config: {e}")
            return False

    def add_saved_network(self, network: Dict[str, Any]) -> bool:
        """Add a network to saved networks"""
        try:
            if self.network.saved_networks is None:
                self.network.saved_networks = []
            if network not in self.network.saved_networks:
                self.network.saved_networks.append(network)
                return self._save_config()
            return False
        except Exception as e:
            self.logger.error(f"Error adding saved network: {e}")
            return False

    def remove_saved_network(self, ssid: str) -> bool:
        """Remove a saved network by SSID"""
        try:
            if not hasattr(self.network, 'saved_networks'):
                self.network.saved_networks = []
                return False
            
            networks = self.network.saved_networks
            initial_count = len(networks)
            
            self.logger.debug(f"Current networks: {networks}")
            self.logger.debug(f"Removing network: {ssid}")
            
            # Filter out the network to remove
            self.network.saved_networks = [
                network for network in networks 
                if network.get('ssid') != ssid
            ]
            
            # If network was found and removed
            if len(self.network.saved_networks) < initial_count:
                if self._save_config():
                    self.logger.info(f"Successfully removed network: {ssid}")
                    return True
                
            self.logger.warning(f"Network not found or could not be removed: {ssid}")
            return False
        except Exception as e:
            self.logger.error(f"Error removing network: {e}")
            return False

    def _update_from_dict(self, config_data: dict) -> None:
        """Update configuration from dictionary"""
        try:
            # Initialize audio config
            if not hasattr(self, 'audio'):
                self.audio = type('AudioConfig', (), {})()
            
            audio_config = config_data.get('audio', {})
            self.audio.default_volume = audio_config.get('default_volume', 50)
            self.audio.volume_step = audio_config.get('volume_step', 5)
            self.audio.sounds_enabled = audio_config.get('sounds_enabled', True)

            # Initialize network config
            if not hasattr(self, 'network'):
                self.network = type('NetworkConfig', (), {})()
            
            network_config = config_data.get('network', {})
            self.network.saved_networks = network_config.get('saved_networks', [])
            self.network.ap_ssid = network_config.get('ap_ssid', 'InternetRadio')
            self.network.ap_password = network_config.get('ap_password', 'radio123')
            self.network.connection_timeout = network_config.get('connection_timeout', 30)

            # Initialize logging config
            if not hasattr(self, 'logging'):
                self.logging = type('LoggingConfig', (), {})()
            
            logging_config = config_data.get('logging', {})
            self.logging.level = logging_config.get('level', 'INFO')
            
            # Apply logging level using the correct method
            if hasattr(self, 'logger'):
                self.logger.set_level(self.logging.level)

            self.logger.debug(f"Updated config: audio={vars(self.audio)}, network={vars(self.network)}, logging={vars(self.logging)}")
        except Exception as e:
            self.logger.error(f"Error updating from dict: {e}")
            raise
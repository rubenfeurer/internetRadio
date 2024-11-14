import toml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .logger import Logger
import os
import logging

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
        """Initialize ConfigManager"""
        self.logger = Logger.get_logger(__name__)
        self.config_dir = config_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from TOML file"""
        try:
            config_data = {}
            
            # Try both config.toml and radio.toml
            config_files = ['config.toml', 'radio.toml']
            
            for filename in config_files:
                config_path = os.path.join(self.config_dir, filename)
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config_data = toml.load(f)
                        self.logger.debug(f"Loaded config from {config_path}: {config_data}")
                    break
            
            # Initialize audio config with defaults
            self.audio = AudioConfig()
            
            # Update from loaded config
            if 'audio' in config_data:
                audio_config = config_data['audio']
                self.audio.default_volume = audio_config.get('default_volume', self.audio.default_volume)
                self.audio.volume_step = audio_config.get('volume_step', self.audio.volume_step)
                self.audio.sounds_enabled = audio_config.get('sounds_enabled', self.audio.sounds_enabled)
            
            # Initialize network config with defaults
            self.network = NetworkConfig()
            
            # Update from loaded config
            if 'network' in config_data:
                network_config = config_data['network']
                self.network.saved_networks = network_config.get('saved_networks', [])
                self.network.ap_ssid = network_config.get('ap_ssid', self.network.ap_ssid)
                self.network.ap_password = network_config.get('ap_password', self.network.ap_password)
            
            # Initialize logging config with defaults
            self.logging = LoggingConfig()
            
            # Update from loaded config
            if 'logging' in config_data:
                logging_config = config_data['logging']
                self.logging.level = logging_config.get('level', self.logging.level)
            
            # Apply logging level
            logging.getLogger().setLevel(self.logging.level)
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")

    def _merge_config_data(self, base: dict, override: dict) -> None:
        """Deep merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config_data(base[key], value)
            else:
                base[key] = value

    def save_config(self) -> bool:
        """Save configuration to file"""
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
            
            config_path = os.path.join(self.config_dir, 'radio.toml')
            with open(config_path, 'w') as f:
                toml.dump(config_data, f)
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            return False

    def update_audio_config(self, **kwargs) -> bool:
        """Update audio configuration"""
        try:
            self.logger.debug(f"Updating audio config with: {kwargs}")
            
            if not hasattr(self, 'audio'):
                self.logger.error("Audio configuration not initialized")
                return False
            
            # Update each provided value
            for key, value in kwargs.items():
                if hasattr(self.audio, key):
                    self.logger.debug(f"Setting {key} to {value}")
                    setattr(self.audio, key, value)
                else:
                    self.logger.warning(f"Unknown audio config key: {key}")
            
            # Save the updated configuration
            return self._save_config()
            
        except Exception as e:
            self.logger.error(f"Error updating audio config: {str(e)}")
            return False

    def update_network_config(self, **kwargs) -> bool:
        """Update network configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.network, key):
                    setattr(self.network, key, value)
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error updating network config: {str(e)}")
            return False

    def add_saved_network(self, network: Dict[str, Any]) -> bool:
        """Add a network to saved networks"""
        try:
            self.logger.debug(f"Adding network: {network}")
            
            if not hasattr(self, 'network'):
                self.logger.error("Network configuration not initialized")
                return False
            
            if self.network.saved_networks is None:
                self.network.saved_networks = []
            
            # Check if network already exists
            if network not in self.network.saved_networks:
                self.network.saved_networks.append(network)
                self.logger.debug(f"Network added, saving config")
                return self._save_config()
            
            self.logger.debug("Network already exists")
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding saved network: {e}")
            return False

    def remove_saved_network(self, ssid: str) -> bool:
        """Remove saved network by SSID"""
        try:
            self.logger.debug(f"Starting remove_saved_network for SSID: {ssid}")
            
            if not hasattr(self, 'network'):
                self.logger.error("No network attribute")
                return False
            
            if not hasattr(self.network, 'saved_networks'):
                self.logger.error("No saved_networks attribute")
                return False
            
            networks = self.network.saved_networks
            initial_length = len(networks)
            self.logger.debug(f"Initial networks: {networks}")
            
            # Remove network
            new_networks = [n for n in networks if n.get('ssid') != ssid]
            self.logger.debug(f"Networks after filtering: {new_networks}")
            
            if len(new_networks) < initial_length:
                self.network.saved_networks = new_networks
                try:
                    self._save_config()
                    self.logger.info(f"Successfully removed network {ssid} and saved config")
                    return True
                except Exception as save_error:
                    self.logger.error(f"Error saving config: {save_error}")
                    return False
            
            self.logger.warning(f"Network {ssid} not found in saved networks")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in remove_saved_network: {str(e)}")
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
    
            # Apply logging level
            if hasattr(self, 'logger'):
                logging.getLogger().setLevel(self.logging.level)

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error updating config: {str(e)}")
            else:
                print(f"Error updating config: {str(e)}")

    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration section"""
        try:
            # Add debug logging
            self.logger.debug(f"Current working directory: {os.getcwd()}")
            self.logger.debug(f"Config dir: {self.config_dir}")
            self.logger.debug(f"Config file exists: {os.path.exists(os.path.join(self.config_dir, 'config.toml'))}")
            
            if hasattr(self, 'network'):
                return {
                    'saved_networks': self.network.saved_networks,
                    'ap_ssid': self.network.ap_ssid,
                    'ap_password': self.network.ap_password
                }
            return {}
        except Exception as e:
            self.logger.error(f"Error getting network config: {str(e)}")
            return {}

    def _save_config(self) -> bool:
        """Save configuration to TOML file"""
        try:
            self.logger.debug("Starting _save_config")
            config_data = {}
            
            # Add audio config if it exists
            if hasattr(self, 'audio'):
                config_data['audio'] = {
                    'default_volume': self.audio.default_volume,
                    'volume_step': self.audio.volume_step,
                    'sounds_enabled': self.audio.sounds_enabled
                }
            
            # Add network config if it exists
            if hasattr(self, 'network'):
                config_data['network'] = {
                    'saved_networks': self.network.saved_networks,
                    'ap_ssid': self.network.ap_ssid,
                    'ap_password': self.network.ap_password
                }
            
            config_path = os.path.join(self.config_dir, 'config.toml')
            self.logger.debug(f"Saving to: {config_path}")
            self.logger.debug(f"Config data: {config_data}")
            
            with open(config_path, 'w') as f:
                toml.dump(config_data, f)
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            return False

    def get_ap_credentials(self) -> tuple[str, str]:
        """Get AP mode credentials from config
        
        Returns:
            tuple[str, str]: SSID and password for AP mode
        """
        return (
            self.network.ap_ssid,
            self.network.ap_password
        )

DEFAULT_CONFIG = {
    'network': {
        'ap_settings': {
            'ssid': 'InternetRadio',
            'password': 'raspberry',
            'channel': 6
        },
        'saved_networks': []  # Add this to track saved networks
    }
}
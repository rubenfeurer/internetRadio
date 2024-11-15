import toml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
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
    ap_ssid: str = "InternetRadio"
    ap_password: str = "raspberry"
    wifi_networks: Dict[str, str] = field(default_factory=dict)
    connection_timeout: int = 60
    saved_networks: Dict[str, str] = field(default_factory=dict)

@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/radio.log"

class ConfigManager:
    def __init__(self, config_dir=None):
        # Set config directory
        self.config_dir = config_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
        
        # Initialize logger with proper directory
        log_dir = os.path.join(os.path.dirname(self.config_dir), 'logs')
        self.logger = Logger('config', log_dir=log_dir)
        
        # Set default configurations
        self.audio = AudioConfig()
        self.network = NetworkConfig()
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            config_path = os.path.join(self.config_dir, 'config.toml')
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = toml.load(f)
                
                # Load network configuration
                if 'network' in config:
                    # Handle AP settings
                    self.network.ap_ssid = config['network'].get('ap_ssid', self.network.ap_ssid)
                    if self.network.ap_ssid == '${HOSTNAME}':
                        self.network.ap_ssid = "InternetRadio"
                    self.network.ap_password = config['network'].get('ap_password', self.network.ap_password)
                    
                    # Handle saved networks
                    saved_networks = config['network'].get('saved_networks', {})
                    if isinstance(saved_networks, list):
                        # Convert list format to dictionary
                        networks_dict = {}
                        for network in saved_networks:
                            if isinstance(network, dict) and 'ssid' in network and 'password' in network:
                                networks_dict[network['ssid']] = network['password']
                        self.network.saved_networks = networks_dict
                    else:
                        self.network.saved_networks = saved_networks
                        
                    self.network.connection_timeout = config['network'].get('connection_timeout', 60)
            else:
                self.logger.warning(f"Config file not found at {config_path}, using defaults")
                
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            # Use defaults if loading fails
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            config_data = {}
            
            # Add network config if it exists
            if hasattr(self, 'network'):
                config_data['network'] = {
                    'ap_ssid': self.network.ap_ssid,
                    'ap_password': self.network.ap_password,
                    'saved_networks': self.network.saved_networks,
                    'connection_timeout': self.network.connection_timeout
                }
            
            config_path = os.path.join(self.config_dir, 'config.toml')
            with open(config_path, 'w') as f:
                toml.dump(config_data, f)
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            return False
    
    def add_saved_network(self, ssid: str, password: str) -> bool:
        """Add a network to saved networks"""
        try:
            self.network.saved_networks[ssid] = password
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error in add_saved_network: {e}")
            return False
    
    def remove_saved_network(self, ssid: str) -> bool:
        """Remove a network from saved networks"""
        try:
            self.logger.info(f"Networks before removal: {self.network.saved_networks}")
            if ssid in self.network.saved_networks:
                del self.network.saved_networks[ssid]
                return self.save_config()
            return False
        except Exception as e:
            self.logger.error(f"Error in remove_saved_network: {e}")
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
            self.network.ap_ssid = network_config.get('ap_ssid', 'RadioAP')
            self.network.ap_password = network_config.get('ap_password', 'Radio@1234')
            self.network.wifi_networks = network_config.get('wifi_networks', {})
            self.network.connection_timeout = network_config.get('connection_timeout', 60)
            self.network.saved_networks = network_config.get('saved_networks', {})
    
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
                    'ap_ssid': self.network.ap_ssid,
                    'ap_password': self.network.ap_password,
                    'wifi_networks': self.network.wifi_networks,
                    'connection_timeout': self.network.connection_timeout,
                    'saved_networks': self.network.saved_networks
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
                    'ap_ssid': self.network.ap_ssid,
                    'ap_password': self.network.ap_password,
                    'wifi_networks': self.network.wifi_networks,
                    'connection_timeout': self.network.connection_timeout,
                    'saved_networks': self.network.saved_networks
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

    def get_saved_networks(self) -> Dict[str, str]:
        """Get saved networks from config
        
        Returns:
            Dict[str, str]: Dictionary of saved networks (SSID: password)
        """
        return self.network.saved_networks

    def get_ap_config(self) -> Dict[str, str]:
        """Get AP configuration
        
        Returns:
            Dict[str, str]: AP configuration with 'ssid' and 'password'
        """
        return {
            'ssid': self.network.ap_ssid if hasattr(self, 'network') else "InternetRadio",
            'password': self.network.ap_password if hasattr(self, 'network') else "raspberry"
        }

DEFAULT_CONFIG = {
    'network': {
        'ap_ssid': 'InternetRadio',
        'ap_password': 'raspberry',
        'saved_networks': {}
    }
}
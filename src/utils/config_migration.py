import toml
from pathlib import Path
from typing import Dict, Any
from .logger import Logger

class ConfigMigration:
    def __init__(self, config_dir: Path):
        self.logger = Logger(__name__)
        self.config_dir = config_dir
        self.current_version = 2  # Increment this when config format changes

    def migrate(self) -> bool:
        """Migrate configuration files to latest version"""
        try:
            # Check current config version
            version = self._get_config_version()
            
            if version < self.current_version:
                self.logger.info(f"Migrating config from version {version} to {self.current_version}")
                
                # Apply migrations sequentially
                if version < 1:
                    self._migrate_to_v1()
                if version < 2:
                    self._migrate_to_v2()
                
                # Update version
                self._update_version()
                return True
                
            return False  # No migration needed
            
        except Exception as e:
            self.logger.error(f"Error during migration: {e}")
            return False

    def _get_config_version(self) -> int:
        """Get current config version"""
        try:
            radio_file = self.config_dir / 'radio.toml'
            if radio_file.exists():
                with open(radio_file) as f:
                    data = toml.load(f)
                    return data.get('version', 0)
            return 0
        except Exception:
            return 0

    def _update_version(self) -> None:
        """Update config version"""
        radio_file = self.config_dir / 'radio.toml'
        if radio_file.exists():
            with open(radio_file) as f:
                data = toml.load(f)
            
            data['version'] = self.current_version
            
            with open(radio_file, 'w') as f:
                toml.dump(data, f)

    def _migrate_to_v1(self) -> None:
        """Migrate from initial version to v1"""
        # Example: Split radio.toml into radio.toml and streams.toml
        old_file = self.config_dir / 'radio.toml'
        if old_file.exists():
            with open(old_file) as f:
                data = toml.load(f)
            
            # Extract streams
            if 'links' in data:
                streams_data = {'links': data.pop('links')}
                with open(self.config_dir / 'streams.toml', 'w') as f:
                    toml.dump(streams_data, f)
            
            # Save remaining config
            with open(old_file, 'w') as f:
                toml.dump(data, f)

    def _migrate_to_v2(self) -> None:
        """Migrate from v1 to v2"""
        # Example: Update network configuration format
        radio_file = self.config_dir / 'radio.toml'
        if radio_file.exists():
            with open(radio_file) as f:
                data = toml.load(f)
            
            if 'network' in data:
                # Convert old network format to new format
                old_network = data['network']
                data['network'] = {
                    'saved_networks': old_network.get('saved_networks', []),
                    'ap_ssid': old_network.get('ap_ssid', 'InternetRadio'),
                    'ap_password': old_network.get('ap_password', 'radio123'),
                    'connection_timeout': old_network.get('timeout', 30)
                }
            
            with open(radio_file, 'w') as f:
                toml.dump(data, f) 
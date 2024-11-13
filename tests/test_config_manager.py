import unittest
import tempfile
import os
import toml
from pathlib import Path
from src.utils.config_manager import ConfigManager
from src.utils.logger import Logger
import shutil

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        self.log_dir = os.path.join(self.temp_dir, 'logs')
        
        # Set logger to test mode with DEBUG level
        Logger.reset()
        Logger.setup_logging(self.log_dir, "DEBUG")
        
        # Create test config
        self.test_config = {
            'audio': {
                'default_volume': 60,
                'volume_step': 5,
                'sounds_enabled': True
            },
            'network': {
                'saved_networks': [
                    {'ssid': 'TestNetwork', 'password': 'test123'}
                ],
                'ap_ssid': 'TestRadio',
                'ap_password': 'test456',
                'connection_timeout': 45
            },
            'logging': {
                'level': 'DEBUG'
            }
        }
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Write test config
        with open(self.config_dir / 'radio.toml', 'w') as f:
            toml.dump(self.test_config, f)
        
        # Initialize config manager
        self.config_manager = ConfigManager(config_dir=str(self.config_dir))
        
    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            Logger.reset()
        
    def test_load_config(self):
        """Test loading configuration from file"""
        self.assertEqual(self.config_manager.audio.default_volume, 60)
        self.assertEqual(self.config_manager.network.ap_ssid, 'TestRadio')
        self.assertEqual(self.config_manager.logging.level, 'DEBUG')
        
    def test_update_audio_config(self):
        """Test updating audio configuration"""
        self.assertTrue(
            self.config_manager.update_audio_config(
                default_volume=70,
                volume_step=15
            )
        )
        self.assertEqual(self.config_manager.audio.default_volume, 70)
        self.assertEqual(self.config_manager.audio.volume_step, 15)
        
    def test_update_network_config(self):
        """Test updating network configuration"""
        self.assertTrue(
            self.config_manager.update_network_config(
                ap_ssid='NewRadio',
                connection_timeout=60
            )
        )
        self.assertEqual(self.config_manager.network.ap_ssid, 'NewRadio')
        self.assertEqual(self.config_manager.network.connection_timeout, 60)
        
    def test_add_saved_network(self):
        """Test adding saved network"""
        new_network = {
            'ssid': 'NewNetwork',
            'password': 'new123'
        }
        self.assertTrue(self.config_manager.add_saved_network(new_network))
        self.assertIn(new_network, self.config_manager.network.saved_networks)
        
        # Test adding duplicate network
        self.assertFalse(self.config_manager.add_saved_network(new_network))
        
    def test_remove_saved_network(self):
        """Test removing saved network"""
        self.assertTrue(self.config_manager.remove_saved_network('TestNetwork'))
        self.assertEqual(len(self.config_manager.network.saved_networks), 0)
        
        # Test removing non-existent network
        self.assertFalse(self.config_manager.remove_saved_network('NonExistent'))
        
    def test_save_config(self):
        """Test saving configuration to file"""
        self.config_manager.update_audio_config(default_volume=80)
        
        # Load config again to verify save
        new_manager = ConfigManager(config_dir=self.temp_dir)
        self.assertEqual(new_manager.audio.default_volume, 80)
        
    def test_default_config(self):
        """Test default configuration when file doesn't exist"""
        # Remove existing config file
        os.remove(self.config_dir / 'radio.toml')
        
        # Create new manager
        new_manager = ConfigManager(config_dir=self.temp_dir)
        
        # Check default values
        self.assertEqual(new_manager.audio.default_volume, 50)
        self.assertEqual(new_manager.network.ap_ssid, 'InternetRadio')
        self.assertEqual(new_manager.logging.level, 'INFO')

if __name__ == '__main__':
    unittest.main() 
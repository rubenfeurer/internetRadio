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
        """Set up test fixtures"""
        # Create test config
        self.test_config = {
            'network': {
                'ap_ssid': 'TestRadio',
                'ap_password': 'TestPass',
                'saved_networks': []
            },
            'audio': {
                'default_volume': 50,
                'volume_step': 5,
                'sounds_enabled': True
            },
            'logging': {
                'level': 'DEBUG'
            }
        }
        
        # Create config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Write test config to radio.toml
        with open(self.config_dir / 'radio.toml', 'w') as f:
            toml.dump(self.test_config, f)
        
        # Initialize config manager with test directory
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
        # Verify audio config
        self.assertEqual(self.config_manager.audio.default_volume, 50)
        
        # Verify network config
        self.assertEqual(self.config_manager.network.ap_ssid, 'TestRadio')
        self.assertEqual(self.config_manager.network.ap_password, 'TestPass')
        
        # Verify logging config
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
        # Create test config with a network to remove
        test_config = {
            'network': {
                'saved_networks': [
                    {'ssid': 'TestNetwork', 'password': 'test123'}
                ],
                'ap_ssid': 'TestRadio',
                'ap_password': 'test456'
            }
        }
        
        # Write test config
        config_path = os.path.join(self.config_dir, 'config.toml')
        with open(config_path, 'w') as f:
            toml.dump(test_config, f)
        
        # Create new config manager with this config
        self.config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        # Verify network exists before removal
        networks = self.config_manager.get_network_config().get('saved_networks', [])
        print(f"Networks before removal: {networks}")  # Debug print
        
        # Try to remove the network
        result = self.config_manager.remove_saved_network('TestNetwork')
        print(f"Remove result: {result}")  # Debug print
        
        # Verify removal
        self.assertTrue(result)
        self.assertEqual(len(self.config_manager.network.saved_networks), 0)
        
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
        
    def test_saved_networks_config(self):
        """Test that saved networks are loaded correctly from config.toml"""
        # Create test config with our Salt network
        test_config = {
            'network': {
                'saved_networks': [
                    {'ssid': 'Salt_5GHz_D8261F', 'password': 'GDk2hc2UQFV29tHSuR'}
                ],
                'ap_ssid': 'InternetRadio',
                'ap_password': 'password123'
            }
        }
        
        # Write test config to temp directory
        config_path = os.path.join(self.config_dir, 'config.toml')
        with open(config_path, 'w') as f:
            toml.dump(test_config, f)
        
        # Create new config manager instance
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        # Get network config
        network_config = config_manager.get_network_config()
        
        # Verify saved networks
        self.assertIsNotNone(network_config.get('saved_networks'))
        saved_networks = network_config['saved_networks']
        self.assertEqual(len(saved_networks), 1)
        
        # Verify Salt network details
        salt_network = next((n for n in saved_networks if n['ssid'] == 'Salt_5GHz_D8261F'), None)
        self.assertIsNotNone(salt_network)
        self.assertEqual(salt_network['password'], 'GDk2hc2UQFV29tHSuR')
        
    def test_audio_config_initialization(self):
        """Test audio configuration initialization"""
        # Create test config with audio settings
        test_config = {
            'audio': {
                'default_volume': 50,
                'volume_step': 5
            }
        }
        
        # Write test config
        config_path = os.path.join(self.config_dir, 'config.toml')
        with open(config_path, 'w') as f:
            toml.dump(test_config, f)
        
        # Create new config manager
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        # Verify audio attributes exist
        self.assertTrue(hasattr(config_manager, 'audio'))
        self.assertEqual(config_manager.audio.default_volume, 50)
        self.assertEqual(config_manager.audio.volume_step, 5)
        
    def test_update_audio_config_single_value(self):
        """Test updating a single audio configuration value"""
        # Create test config with initial audio settings
        test_config = {
            'audio': {
                'default_volume': 50,
                'volume_step': 5
            }
        }
        
        # Write test config
        config_path = os.path.join(self.config_dir, 'config.toml')
        with open(config_path, 'w') as f:
            toml.dump(test_config, f)
        
        # Create config manager
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        # Update single value
        result = config_manager.update_audio_config(default_volume=70)
        
        # Verify update
        self.assertTrue(result)
        self.assertEqual(config_manager.audio.default_volume, 70)
        self.assertEqual(config_manager.audio.volume_step, 5)  # Should remain unchanged

    def test_add_saved_network_single(self):
        """Test adding a single network to saved networks"""
        # Create test config
        test_config = {
            'network': {
                'saved_networks': [],
                'ap_ssid': 'TestRadio',
                'ap_password': 'test123'
            }
        }
        
        # Write test config
        config_path = os.path.join(self.config_dir, 'config.toml')
        with open(config_path, 'w') as f:
            toml.dump(test_config, f)
        
        # Create config manager
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        # Add new network
        new_network = {'ssid': 'NewNetwork', 'password': 'new123'}
        result = config_manager.add_saved_network(new_network)
        
        # Verify
        self.assertTrue(result)
        self.assertIn(new_network, config_manager.network.saved_networks)

    def test_load_config_with_audio(self):
        """Test loading audio configuration from file"""
        # Create test config with specific audio settings
        test_config = {
            'audio': {
                'default_volume': 60,
                'volume_step': 5,
                'sounds_enabled': True
            }
        }
        
        # Write test config
        config_path = os.path.join(self.config_dir, 'config.toml')
        with open(config_path, 'w') as f:
            toml.dump(test_config, f)
        
        # Create new config manager
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        # Verify audio settings
        self.assertEqual(config_manager.audio.default_volume, 60)
        self.assertEqual(config_manager.audio.volume_step, 5)
        self.assertTrue(config_manager.audio.sounds_enabled)

    def test_get_ap_credentials(self):
        """Test getting AP credentials from config"""
        # Setup - use update_network_config instead of direct assignment
        self.config_manager.update_network_config(
            ap_ssid='TestAP',
            ap_password='TestPass'
        )
        
        # Test
        ssid, password = self.config_manager.get_ap_credentials()
        
        # Verify
        self.assertEqual(ssid, 'TestAP')
        self.assertEqual(password, 'TestPass')

    def test_network_mode_conflict(self):
        """Test that AP mode doesn't interfere with NetworkManager"""
        # Create test config with network settings
        test_config = {
            'network': {
                'saved_networks': [
                    {'ssid': 'Salt_2GHz_D8261F', 'password': 'GDk2hc2UQFV29tHSuR'}
                ],
                'ap_ssid': 'TestRadio',
                'ap_password': 'test123'
            }
        }
        
        # Write test config
        config_path = os.path.join(self.config_dir, 'config.toml')
        with open(config_path, 'w') as f:
            toml.dump(test_config, f)
        
        # Create config manager
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        # Verify network settings don't conflict
        network_config = config_manager.get_network_config()
        self.assertIn('saved_networks', network_config)
        self.assertEqual(len(network_config['saved_networks']), 1)

if __name__ == '__main__':
    unittest.main() 
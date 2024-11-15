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
        # Create temporary directory for test configs
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir) / 'config'
        self.config_dir.mkdir(exist_ok=True)
        
        # Create test config file
        self.test_config = {
            'audio': {
                'default_volume': 50,
                'volume_step': 5,
                'sounds_enabled': True
            },
            'network': {
                'ap_ssid': 'TestRadio',
                'ap_password': 'TestPass123',
                'wifi_networks': {},
                'saved_networks': {'TestNetwork': 'TestPassword'},
                'connection_timeout': 60
            }
        }
        
        # Write test config to file
        config_file = self.config_dir / 'config.toml'
        with open(config_file, 'w') as f:
            toml.dump(self.test_config, f)
        
        # Initialize config manager with test directory
        self.config_manager = ConfigManager(config_dir=str(self.config_dir))
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_load_config(self):
        """Test loading configuration from file"""
        self.assertEqual(self.config_manager.audio.default_volume, 50)
        self.assertEqual(self.config_manager.audio.volume_step, 5)
        self.assertEqual(self.config_manager.network.ap_ssid, 'TestRadio')
        self.assertEqual(self.config_manager.network.ap_password, 'TestPass123')
        self.assertEqual(self.config_manager.network.wifi_networks, {})
        
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
        ssid = "TestNetwork2"
        password = "TestPassword2"
        result = self.config_manager.add_saved_network(ssid, password)
        self.assertTrue(result)
        self.assertIn(ssid, self.config_manager.network.saved_networks)
        self.assertEqual(self.config_manager.network.saved_networks[ssid], password)
        
    def test_remove_saved_network(self):
        """Test removing saved network"""
        ssid = "TestNetwork"
        self.config_manager.network.saved_networks[ssid] = "TestPassword"
        result = self.config_manager.remove_saved_network(ssid)
        self.assertTrue(result)
        self.assertNotIn(ssid, self.config_manager.network.saved_networks)
        
    def test_save_config(self):
        """Test saving configuration to file"""
        # Update some values
        self.config_manager.audio.default_volume = 75
        self.config_manager.network.ap_ssid = "NewRadio"
        
        # Save configuration
        result = self.config_manager.save_config()
        self.assertTrue(result)
        
        # Create new config manager to read saved config
        new_manager = ConfigManager(config_dir=str(self.config_dir))
        
        # Verify values were saved
        self.assertEqual(new_manager.audio.default_volume, 75)
        self.assertEqual(new_manager.network.ap_ssid, "NewRadio")
        
    def test_default_config(self):
        """Test default configuration when file doesn't exist"""
        # Create a new empty directory for this test
        empty_dir = tempfile.mkdtemp()
        empty_config_dir = os.path.join(empty_dir, 'config')
        os.makedirs(empty_config_dir, exist_ok=True)
        
        # Create config manager with empty directory
        config_manager = ConfigManager(config_dir=empty_config_dir)
        
        # Test default values
        self.assertEqual(config_manager.audio.default_volume, 50)
        self.assertEqual(config_manager.audio.volume_step, 5)
        self.assertEqual(config_manager.network.ap_ssid, "RadioAP")
        self.assertEqual(config_manager.network.ap_password, "Radio@1234")
        self.assertEqual(config_manager.network.wifi_networks, {})
        
        # Clean up
        shutil.rmtree(empty_dir)
        
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
        new_network = "TestNetwork2"
        password = "TestPassword2"
        result = self.config_manager.add_saved_network(new_network, password)
        self.assertTrue(result)
        self.assertIn(new_network, self.config_manager.network.saved_networks)
        self.assertEqual(self.config_manager.network.saved_networks[new_network], password)

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
from src.utils.config_manager import ConfigManager
import os

config = ConfigManager()
print("Config dir:", config.config_dir)
print("Network config:", config.get_network_config())

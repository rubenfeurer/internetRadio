from src.utils.logger import Logger
from src.utils.config_manager import ConfigManager
from src.network.wifi_manager import WiFiManager
from src.network.ap_manager import APManager
import subprocess

class NetworkController:
    def __init__(self, wifi_manager=None, ap_manager=None, config_manager=None):
        self.logger = Logger.get_logger(__name__)
        self.wifi_manager = wifi_manager or WiFiManager()
        self.ap_manager = ap_manager or APManager()
        self.config_manager = config_manager or ConfigManager()
        self.is_ap_mode = False
        self.logger.debug("Initializing NetworkController")

    def initialize(self) -> bool:
        """Initialize network controller"""
        try:
            self.wifi_manager.initialize()
            self.ap_manager.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize network: {e}")
            return False

    def cleanup(self) -> None:
        """Cleanup network resources"""
        if self.is_ap_mode:
            self.ap_manager.stop()
        self.wifi_manager.cleanup()
        self.ap_manager.cleanup()

    def start_ap_mode(self, ssid: str, password: str) -> bool:
        """Start access point mode"""
        if self.ap_manager.start(ssid, password):
            self.is_ap_mode = True
            return True
        return False

    def get_connection_status(self) -> dict:
        """Get current connection status"""
        status = {
            'is_ap_mode': self.is_ap_mode,
            'mode': 'AP' if self.is_ap_mode else 'WiFi',
            'wifi_connected': self.wifi_manager.is_connected(),
            'ip_address': self.wifi_manager.get_ip()
        }
        
        if not self.is_ap_mode:
            status.update({
                'current_ssid': self.wifi_manager.get_current_ssid()
            })
        return status

    def monitor_network(self) -> None:
        """Monitor network status"""
        if self.is_ap_mode:
            if not self.ap_manager.is_active():
                self.ap_manager.start("DefaultAP", "password")
        else:
            self.wifi_manager.is_connected()

    def log_network_status(self) -> None:
        """Log current network status"""
        status = self.get_connection_status()
        self.logger.info(f"Network Status: {status}")
        
        commands = [
            "iwconfig",
            "ifconfig",
            "route -n",
            "systemctl status hostapd",
            "systemctl status dnsmasq",
            "ps aux | grep wpa_supplicant"
        ]
        
        for cmd in commands:
            try:
                output = subprocess.run(cmd.split(), capture_output=True, text=True)
                self.logger.info(f"{cmd} output: {output.stdout}")
            except Exception as e:
                self.logger.error(f"Error running command {cmd}: {e}")

    def check_and_setup_network(self) -> bool:
        """Check and setup network connection"""
        saved_networks = self.wifi_manager.get_saved_networks()
        if saved_networks:
            for network in saved_networks:
                if self.wifi_manager.connect_to_network(network):
                    return True
        return self.start_ap_mode("DefaultAP", "password")

    def connect_wifi(self, ssid: str, password: str = None) -> bool:
        """Connect to WiFi network"""
        return self.wifi_manager.connect_to_network(ssid)

    def stop_ap_mode(self) -> bool:
        """Stop access point mode"""
        if self.ap_manager.stop():
            self.is_ap_mode = False
            return True
        return False

    def is_ap_mode_active(self) -> bool:
        """Check if AP mode is active"""
        return self.is_ap_mode

    def monitor(self) -> None:
        """Monitor network status"""
        self.wifi_manager.is_connected()
        if not self.wifi_manager.is_connected() and not self.is_ap_mode:
            self.check_and_setup_network()
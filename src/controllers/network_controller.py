from src.utils.logger import Logger
from src.utils.config_manager import ConfigManager
from src.network.wifi_manager import WiFiManager
from src.network.ap_manager import APManager
from src.audio.audio_manager import AudioManager
import subprocess
import time
from typing import Optional

class NetworkController:
    def __init__(self, wifi_manager=None, ap_manager=None, config_manager=None, audio_manager=None):
        self.logger = Logger.get_logger(__name__)
        self.wifi_manager = wifi_manager or WiFiManager()
        self.ap_manager = ap_manager or APManager()
        self.config_manager = config_manager or ConfigManager()
        self.audio_manager = audio_manager or AudioManager()
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

    def get_connection_status(self) -> dict:
        """Get current connection status"""
        status = {
            'is_ap_mode': self.is_ap_mode,
            'mode': 'AP' if self.is_ap_mode else 'WiFi',
            'wifi_connected': False,
            'current_ssid': None,
            'ip_address': None
        }
        
        if self.is_ap_mode:
            status['ip_address'] = self.ap_manager.get_ip()
        else:
            status['wifi_connected'] = self.wifi_manager.is_connected()
            status['ip_address'] = self.wifi_manager.get_ip()
            status['current_ssid'] = self.wifi_manager.get_current_ssid()
        
        return status

    def connect_wifi(self, ssid: str, password: Optional[str] = None) -> bool:
        """Connect to WiFi network"""
        return self.wifi_manager.connect_to_network(ssid, password)

    def check_and_setup_network(self) -> bool:
        """Check and setup network connection with retry mechanism"""
        retry_count = 0
        max_retries = 10
        delay = 5
        
        while True:
            if retry_count >= max_retries:
                self.logger.error("Max retries reached")
                return False
            
            saved_networks = self.wifi_manager.get_saved_networks()
            if not saved_networks:
                self.logger.warning("No saved networks found, starting AP mode")
                # Start AP mode as fallback
                if self.start_ap_mode("DefaultAP", "password"):
                    return True
                return False
            
            # Extract SSID from network object
            network = saved_networks[0]
            ssid = network['ssid'] if isinstance(network, dict) else network
            
            # Try network setup
            if (self.wifi_manager.connect_to_network(ssid, None) and 
                self.wifi_manager.configure_dns() and 
                self.wifi_manager.check_dns_resolution()):
                
                self.logger.info("Network setup complete with DNS")
                
                # Check internet connection
                if self.check_internet_connection():
                    self.logger.info("Internet connection verified")
                    return True
                    
                self.logger.warning("Internet check failed, will retry")
            else:
                self.logger.warning("Network setup failed, will retry")
            
            delay = 60 if retry_count >= 5 else 5
            self.logger.warning(f"Retrying in {delay} seconds (attempt {retry_count + 1}/{max_retries})")
            time.sleep(delay)
            retry_count += 1

    def start_ap_mode(self, ssid: str, password: str) -> bool:
        """Start access point mode"""
        if self.ap_manager.start(ssid, password):
            self.is_ap_mode = True
            return True
        return False

    def stop_ap_mode(self) -> bool:
        """Stop access point mode"""
        if self.ap_manager.stop():
            self.is_ap_mode = False
            return True
        return False

    def monitor_network(self) -> None:
        """Monitor network status"""
        if self.is_ap_mode:
            if not self.ap_manager.is_active():
                ap_ssid, ap_password = self.config_manager.get_ap_credentials()
                self.ap_manager.start(ap_ssid, ap_password)
        else:
            self.wifi_manager.is_connected()

    def log_network_status(self) -> None:
        """Log current network status"""
        try:
            # Get and log network status
            status = self.get_connection_status()
            self.logger.info(f"Network Status: {status}")
            
            # Define commands to run
            commands = [
                "iwconfig",
                "ifconfig",
                "route -n",
                "systemctl status hostapd",
                "systemctl status dnsmasq",
                "ps aux | grep wpa_supplicant"
            ]
            
            # Run each command and log output
            for cmd in commands:
                try:
                    output = subprocess.run(cmd.split(), capture_output=True, text=True)
                    if output.returncode == 0:
                        self.logger.info(f"{cmd} output: {output.stdout}")
                    else:
                        self.logger.info(f"{cmd} failed with return code {output.returncode}")
                except Exception as e:
                    self.logger.error(f"Error running command {cmd}: {e}")
        except Exception as e:
            self.logger.error(f"Error in log_network_status: {e}")

    def cleanup(self) -> None:
        """Cleanup network resources"""
        if self.is_ap_mode:
            self.ap_manager.stop()
        self.wifi_manager.cleanup()
        self.ap_manager.cleanup()

    def is_ap_mode_active(self) -> bool:
        """Check if AP mode is active"""
        return self.is_ap_mode

    def monitor(self) -> None:
        """Monitor network status"""
        if not self.wifi_manager.is_connected() and not self.is_ap_mode:
            self.check_and_setup_network()

    def check_internet_connection(self) -> bool:
        """Check internet connectivity with multiple fallback hosts"""
        test_hosts = [
            "8.8.8.8",      # Google DNS
            "1.1.1.1",      # Cloudflare DNS
            "208.67.222.222" # OpenDNS
        ]
        
        for host in test_hosts:
            try:
                subprocess.run(
                    ["ping", "-c", "1", "-W", "2", host],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                if self.audio_manager:
                    self.audio_manager.play_sound('wifi.wav')
                return True
            except subprocess.CalledProcessError:
                continue
        
        if self.audio_manager:
            self.audio_manager.play_sound('noWifi.wav')
        
        self.logger.error("Failed to connect to any test hosts")
        return False
import os
import psutil
import time
import subprocess
import socket
from src.utils.logger import Logger
from src.network.wifi_manager import WiFiManager

class SystemMonitor:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.logger = Logger.get_logger(__name__)
        self.wifi_manager = WiFiManager()
        
    def collect_metrics(self) -> dict:
        """Collect basic system metrics"""
        try:
            return {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'disk_usage': 0.0
            }
        
    def collect_network_metrics(self) -> dict:
        """Collect enhanced network-related metrics"""
        try:
            self.logger.debug("Checking WiFi modes...")
            is_client = self.wifi_manager.is_client_mode()
            self.logger.debug(f"Client mode: {is_client}")
            is_ap = self.wifi_manager.is_ap_mode()
            self.logger.debug(f"AP mode: {is_ap}")
            
            # Determine mode with logging
            if is_client:
                mode = 'Client'
                ssid = self.wifi_manager.get_current_network()
                self.logger.debug(f"Client mode detected, SSID: {ssid}")
            elif is_ap:
                mode = 'AP'
                ssid = "AP Mode"
                self.logger.debug("AP mode detected")
            else:
                mode = 'Unknown'
                ssid = "Not connected"
                self.logger.debug("No mode detected, setting to Unknown")
                
            internet = self.wifi_manager.check_internet_connection()
            self.logger.debug(f"Internet connected: {internet}")
            
            metrics = {
                'wifi_ssid': ssid or "Not connected",
                'internet_connected': internet,
                'is_client_mode': is_client,
                'is_ap_mode': is_ap,
                'mode': mode
            }
            self.logger.debug(f"Network metrics: {metrics}")
            return metrics
        except Exception as e:
            self.logger.error(f"Network metrics error: {e}")
            return {
                'wifi_ssid': "Error",
                'internet_connected': False,
                'is_client_mode': False,
                'is_ap_mode': False,
                'mode': 'Error'
            }

    def check_radio_service(self) -> dict:
        """Check radio service status"""
        try:
            status = subprocess.check_output(['systemctl', 'is-active', 'internetradio']).decode().strip()
            is_running = status == 'active'
            
            # Get current station from radio service
            station = "Unknown"
            try:
                with open('/tmp/current_station', 'r') as f:
                    station = f.read().strip()
            except FileNotFoundError:
                self.logger.warning("Current station file not found")
            
            return {
                'is_running': is_running,
                'current_station': station
            }
        except Exception as e:
            self.logger.error(f"Radio service check error: {e}")
            return {
                'is_running': False,
                'current_station': 'Unknown'
            }

    def get_system_temperature(self) -> float:
        """Get CPU temperature"""
        try:
            temp = subprocess.check_output(['vcgencmd', 'measure_temp']).decode()
            return float(temp.replace('temp=', '').replace('\'C\n', ''))
        except Exception as e:
            self.logger.error(f"Temperature reading error: {e}")
            return 0.0

    def get_volume_level(self) -> int:
        """Get current volume level"""
        try:
            vol = subprocess.check_output(['amixer', 'get', 'Master']).decode()
            return int(vol.split('[')[1].split('%')[0])
        except Exception as e:
            self.logger.error(f"Volume reading error: {e}")
            return 0

    def get_system_events(self) -> list:
        """Get last system events"""
        try:
            events = subprocess.check_output(['journalctl', '-n', '5', '--no-pager']).decode()
            return events.split('\n')[-5:]
        except Exception as e:
            self.logger.error(f"Events reading error: {e}")
            return []

    def display_metrics(self):
        """Display metrics in console"""
        metrics = self.collect_metrics()
        network = self.collect_network_metrics()
        radio = self.check_radio_service()
        temp = self.get_system_temperature()
        volume = self.get_volume_level()
        events = self.get_system_events()

        print("\033[2J\033[H")  # Clear screen
        print("=== System Monitor ===")
        print(f"CPU Usage: {metrics['cpu_usage']}%")
        print(f"Memory Usage: {metrics['memory_usage']}%")
        print(f"Disk Usage: {metrics['disk_usage']}%")
        print(f"Temperature: {temp}°C")
        print("\n=== Network Status ===")
        print(f"WiFi Network: {network['wifi_ssid']}")
        print(f"Mode: {'Client' if network['is_client_mode'] else 'AP' if network['is_ap_mode'] else 'Unknown'}")
        print(f"Internet Connected: {'Yes' if network['internet_connected'] else 'No'}")
        print("\n=== Radio Status ===")
        print(f"Service Running: {'Yes' if radio['is_running'] else 'No'}")
        print(f"Current Station: {radio['current_station']}")
        print(f"Volume Level: {volume}%")
        print("\n=== Last Events ===")
        for event in events:
            print(event)
        print("===================")
        
    def run(self):
        """Main monitoring loop"""
        try:
            while True:
                self.display_metrics()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Monitor stopped by user")
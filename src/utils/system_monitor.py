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
        self.logger.info("SystemMonitor initialized")
        
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
        """Alias for collect_network_info for backward compatibility"""
        return self.collect_network_info()
        
    def collect_network_info(self) -> dict:
        """Collect network information with proper mode detection"""
        try:
            wifi_info = self.wifi_manager.get_connection_info()
            
            # Determine mode based on NetworkManager status
            mode = "unknown"
            if wifi_info.get('ssid'):
                mode = "client"
            elif self.wifi_manager.is_ap_mode():
                mode = "ap"
            
            return {
                'mode': mode,
                'wifi_ssid': wifi_info.get('ssid', ''),
                'ip': wifi_info.get('ip', ''),
                'signal': wifi_info.get('signal', 0),
                'internet_connected': self.wifi_manager.check_internet_connection()
            }
        except Exception as e:
            self.logger.error(f"Network info collection error: {e}")
            return {
                'mode': 'unknown',
                'wifi_ssid': '',
                'ip': '',
                'signal': 0,
                'internet_connected': False
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
        """Display metrics in console with color indicators"""
        try:
            metrics = self.collect_metrics()
            network = self.collect_network_info()
            radio = self.check_radio_service()
            temp = self.get_system_temperature()
            volume = self.get_volume_level()
            events = self.get_system_events()

            # ANSI color codes
            RED = '\033[91m'
            GREEN = '\033[92m'
            YELLOW = '\033[93m'
            NC = '\033[0m'  # No Color

            print("\033[2J\033[H")  # Clear screen
            print("=== System Monitor ===")
            
            # CPU with color based on usage
            cpu_color = GREEN if metrics['cpu_usage'] < 70 else YELLOW if metrics['cpu_usage'] < 90 else RED
            print(f"CPU Usage: {cpu_color}{metrics['cpu_usage']}%{NC}")
            
            # Memory with color
            mem_color = GREEN if metrics['memory_usage'] < 70 else YELLOW if metrics['memory_usage'] < 90 else RED
            print(f"Memory Usage: {mem_color}{metrics['memory_usage']}%{NC}")
            
            # Temperature with color
            temp_color = GREEN if temp < 60 else YELLOW if temp < 70 else RED
            print(f"Temperature: {temp_color}{temp}°C{NC}")
            
            print("\n=== Network Status ===")
            # Network mode and status
            mode_str = network['mode'] if network['mode'] != 'unknown' else f"{RED}unknown{NC}"
            print(f"Mode: {mode_str}")
            
            # WiFi connection
            wifi_color = GREEN if network['wifi_ssid'] else RED
            print(f"WiFi Network: {wifi_color}{network['wifi_ssid'] or 'Not Connected'}{NC}")
            
            # Internet connection
            internet_color = GREEN if network['internet_connected'] else RED
            print(f"Internet Connected: {internet_color}{'Yes' if network['internet_connected'] else 'No'}{NC}")
            
            print("\n=== Radio Status ===")
            # Service status
            service_color = GREEN if radio['is_running'] else RED
            print(f"Service Running: {service_color}{'Yes' if radio['is_running'] else 'No'}{NC}")
            
            # Current station
            station_color = GREEN if radio['current_station'] else YELLOW
            print(f"Current Station: {station_color}{radio['current_station'] or 'Unknown'}{NC}")
            
            # Volume level
            volume_color = GREEN if volume > 0 else YELLOW
            print(f"Volume Level: {volume_color}{volume}%{NC}")
            
            print("\n=== Last Events ===")
            for event in events:
                if "error" in event.lower() or "fail" in event.lower():
                    print(f"{RED}{event}{NC}")
                elif "warning" in event.lower():
                    print(f"{YELLOW}{event}{NC}")
                else:
                    print(event)
            
            print("===================")
        except Exception as e:
            self.logger.error(f"Error displaying metrics: {e}")
            print(f"{RED}Error displaying metrics: {e}{NC}")

    def run(self):
        """Main monitoring loop"""
        try:
            while True:
                self.display_metrics()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Monitor stopped by user")

if __name__ == '__main__':
    monitor = SystemMonitor()
    monitor.run()
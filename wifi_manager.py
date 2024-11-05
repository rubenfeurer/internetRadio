import subprocess
import time
from flask import jsonify, render_template

class WiFiManager:
    def __init__(self, app=None):
        """Initialize the WiFi manager.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the manager with a Flask application instance."""
        self.app = app
        self.register_routes()

    def register_routes(self):
        """Register the WiFi-related routes with Flask."""
        self.app.add_url_rule(
            '/wifi-scan',
            'wifi_manager.wifi_scan',
            self.handle_wifi_scan
        )
        self.app.add_url_rule(
            '/wifi-setup',
            'wifi_manager.wifi_setup',
            self.handle_wifi_setup
        )

    def scan_wifi(self):
        """Scan for available Wi-Fi networks using iwlist with multiple attempts."""
        try:
            print("Starting WiFi scan with multiple attempts...")
            all_networks = set()
            
            for attempt in range(3):
                print(f"Scan attempt {attempt + 1}/3")
                
                cmd = ['sudo', '/sbin/iwlist', 'wlan0', 'scan']
                print(f"Running command: {' '.join(cmd)}")
                result = subprocess.check_output(
                    cmd,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                for line in result.splitlines():
                    line = line.strip()
                    if "ESSID:" in line:
                        ssid = line.split('ESSID:"')[1].strip('"')
                        if ssid and not ssid.startswith('\x00'):
                            all_networks.add(ssid)
                            print(f"Found network: {ssid}")
                
                if attempt < 2:
                    time.sleep(1)
            
            networks = sorted(list(all_networks))
            print(f"Final network list: {networks}")
            return networks
            
        except Exception as e:
            print(f"Error scanning WiFi: {str(e)}")
            return []

    def handle_wifi_scan(self):
        """Handle the /wifi-scan route."""
        try:
            networks = self.scan_wifi()
            return jsonify({
                'status': 'complete',
                'networks': networks
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500

    def handle_wifi_setup(self):
        """Handle the /wifi-setup route."""
        try:
            print("Starting WiFi setup route")
            return render_template('wifi_settings.html', ssids=[])
        except Exception as e:
            print(f"Error in wifi setup: {str(e)}")
            return jsonify({'error': str(e)}), 500 
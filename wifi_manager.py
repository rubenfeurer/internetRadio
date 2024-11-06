import subprocess
import time
from flask import Blueprint, jsonify, render_template, request

class WiFiManager:
    def __init__(self, app=None):
        """Initialize the WiFi manager."""
        self.app = app
        self.blueprint = Blueprint('wifi', __name__)
        self.register_routes()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the manager with a Flask application instance."""
        self.app = app
        app.register_blueprint(self.blueprint)

    def register_routes(self):
        """Register the WiFi-related routes with Flask."""
        @self.blueprint.route('/wifi-scan')
        def wifi_scan():
            return self.handle_wifi_scan()
            
        @self.blueprint.route('/wifi-settings', methods=['GET', 'POST'])
        def wifi_settings():
            return self.handle_wifi_settings()
            
        @self.blueprint.route('/ping')
        def ping():
            return self.handle_ping()
            
        @self.blueprint.route('/get-ip')
        def get_ip():
            return jsonify({'ip': self.get_ip_address()})

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

    def connect_to_wifi(self, ssid, password):
        """Attempt to connect to a WiFi network using nmcli."""
        try:
            print(f"Attempting to connect to {ssid}")
            
            # Check current connection
            current = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            current_ssid = current.stdout.strip()
            print(f"Currently connected to: {current_ssid}")
            
            # First, forget the current connection if it exists
            subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], 
                          capture_output=True, check=False)  # Ignore errors if connection doesn't exist
            
            # Connect to the new network
            print(f"Connecting to {ssid}...")
            result = subprocess.run([
                'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
                'password', password, 'ifname', 'wlan0'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error output: {result.stderr}")
                return False, f"Failed to connect: {result.stderr}"
            
            # Wait for connection
            time.sleep(5)
            
            # Verify new connection
            new_connection = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            new_ssid = new_connection.stdout.strip()
            
            if new_ssid == ssid:
                return True, f"Successfully connected to {ssid}"
            else:
                return False, f"Failed to connect to {ssid}. Connected to {new_ssid} instead."
                
        except Exception as e:
            print(f"Error in connect_to_wifi: {str(e)}")
            return False, f"Error connecting to WiFi: {str(e)}"

    def restart_networking(self):
        """Restart networking services in a more robust way."""
        try:
            # Stop services
            subprocess.run(['sudo', 'systemctl', 'stop', 'wpa_supplicant'], check=True)
            subprocess.run(['sudo', 'systemctl', 'stop', 'networking'], check=True)
            time.sleep(2)
            
            # Bring interface down
            subprocess.run(['sudo', 'ifconfig', 'wlan0', 'down'], check=True)
            time.sleep(1)
            
            # Bring interface up
            subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'], check=True)
            time.sleep(1)
            
            # Start services
            subprocess.run(['sudo', 'systemctl', 'start', 'wpa_supplicant'], check=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'networking'], check=True)
            
            return True
        except Exception as e:
            print(f"Error restarting networking: {str(e)}")
            return False

    def handle_wifi_settings(self):
        """Handle the /wifi-settings route."""
        try:
            print(f"WiFi settings route called with method: {request.method}")
            
            if request.method == 'POST':
                ssid = request.form.get('ssid')
                password = request.form.get('password')
                print(f"Received connection request for network: {ssid}")
                print(f"Password length: {len(password)} characters")
                
                success, message = self.connect_to_wifi(ssid, password)
                
                if success:
                    return jsonify({
                        'status': 'success',
                        'message': message,
                        'redirect': '/'
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': message
                    }), 400
            else:
                networks = self.scan_wifi()
                return render_template('wifi_settings.html', networks=networks)
                
        except Exception as e:
            print(f"Error in wifi settings: {str(e)}")
            return jsonify({'error': str(e)}), 500 

    def handle_ping(self):
        """Simple endpoint to check if server is responsive."""
        return jsonify({'status': 'ok'})
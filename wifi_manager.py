import subprocess
import time
from flask import Blueprint, jsonify, render_template, request
import os
import logging
from datetime import datetime

class WiFiManager:
    def __init__(self, app=None):
        """Initialize the WiFi manager."""
        self.app = app
        self.blueprint = Blueprint('wifi', __name__)
        self.register_routes()
        self.ap_mode = False
        self.ap_ssid = "InternetRadio"
        self.ap_password = "radiopassword"
        self.initial_connection_made = False
        
        # Setup logging
        self.setup_logging()
        
        if app is not None:
            self.init_app(app)

    def setup_logging(self):
        """Setup logging configuration."""
        log_file = '/home/radio/internetRadio/logs/wifi.log'
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_saved_networks(self):
        """Get list of saved network connections."""
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'NAME', 'connection', 'show'],
                capture_output=True, text=True, check=True
            )
            networks = [net for net in result.stdout.split('\n') if net]
            logging.info(f"Found saved networks: {networks}")
            return networks
        except Exception as e:
            logging.error(f"Error getting saved networks: {e}")
            return []

    def try_connect_saved_networks(self):
        """Try to connect to saved networks only at startup."""
        if self.initial_connection_made:
            logging.info("Initial connection already made, skipping network scan")
            return True
            
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            networks = self.get_saved_networks()
            logging.info(f"Attempting to connect to saved networks (attempt {attempt + 1}/{max_attempts})")
            
            for network in networks:
                if network != self.ap_ssid:  # Skip our own AP
                    if self.connect_to_network(network):
                        if self.check_internet():
                            logging.info(f"Successfully connected to {network} with internet access")
                            self.initial_connection_made = True
                            return True
            attempt += 1
            time.sleep(5)
        
        # Only enable AP mode if we haven't made an initial connection
        if not self.initial_connection_made:
            logging.info("No saved networks available or couldn't connect, enabling AP mode")
            return self.enable_ap_mode()
        return False

    def connect_to_network(self, ssid):
        """Connect to a specific network."""
        try:
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'up', ssid],
                capture_output=True, text=True, check=True
            )
            logging.info(f"Initial connection to {ssid} successful")
            time.sleep(5)  # Wait for connection to stabilize
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to connect to {ssid}: {e}")
            return False

    def check_internet(self):
        """Check if we have internet connectivity."""
        try:
            subprocess.run(
                ['ping', '-c', '1', '8.8.8.8'],
                capture_output=True, check=True, timeout=5
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def enable_ap_mode(self):
        """Enable AP mode using NetworkManager."""
        if self.ap_mode:
            return True
            
        try:
            # Delete existing AP connection if it exists
            subprocess.run(['sudo', 'nmcli', 'connection', 'delete', self.ap_ssid], 
                         capture_output=True, check=False)
            
            # Create new AP connection
            subprocess.run([
                'sudo', 'nmcli', 'connection', 'add',
                'type', 'wifi',
                'ifname', 'wlan0',
                'con-name', self.ap_ssid,
                'autoconnect', 'yes',
                'ssid', self.ap_ssid,
                'mode', 'ap',
                'ipv4.method', 'shared'
            ], check=True)
            
            # Set password
            subprocess.run([
                'sudo', 'nmcli', 'connection', 'modify', self.ap_ssid,
                'wifi-sec.key-mgmt', 'wpa-psk',
                'wifi-sec.psk', self.ap_password
            ], check=True)
            
            # Activate the connection
            subprocess.run(['sudo', 'nmcli', 'connection', 'up', self.ap_ssid], check=True)
            
            self.ap_mode = True
            logging.info("AP mode enabled successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error enabling AP mode: {e}")
            return False

    def scan_wifi(self):
        """Scan for available Wi-Fi networks, handling both client and AP modes."""
        try:
            print("Starting WiFi scan...")
            all_networks = set()
            
            if self.ap_mode:
                # In AP mode, we need to do a special scan without disrupting the AP
                try:
                    # Create a temporary interface for scanning
                    subprocess.run(['sudo', 'iw', 'phy', 'phy0', 'interface', 'add', 'scan0', 'type', 'station'],
                                 check=True, capture_output=True)
                    time.sleep(1)
                    
                    # Bring the interface up
                    subprocess.run(['sudo', 'ip', 'link', 'set', 'scan0', 'up'],
                                 check=True, capture_output=True)
                    time.sleep(1)
                    
                    # Scan using the temporary interface
                    for attempt in range(3):
                        try:
                            result = subprocess.run(['sudo', 'iw', 'dev', 'scan0', 'scan'],
                                                  capture_output=True, text=True, check=True)
                            
                            for line in result.stdout.splitlines():
                                if "SSID:" in line:
                                    ssid = line.split('SSID:')[1].strip()
                                    if ssid and not ssid.startswith('\x00') and ssid != self.ap_ssid:
                                        all_networks.add(ssid)
                        
                            if all_networks:
                                break
                                    
                            time.sleep(1)
                        except subprocess.CalledProcessError:
                            time.sleep(1)
                            continue
                    
                finally:
                    # Clean up: remove temporary interface
                    try:
                        subprocess.run(['sudo', 'iw', 'dev', 'scan0', 'del'],
                                     check=False, capture_output=True)
                    except:
                        pass
                        
            else:
                # Normal scanning mode when not in AP mode
                for attempt in range(3):
                    result = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'],
                                          capture_output=True, text=True, check=True)
                    
                    for line in result.stdout.splitlines():
                        if "ESSID:" in line:
                            ssid = line.split('ESSID:"')[1].strip('"')
                            if ssid and not ssid.startswith('\x00'):
                                all_networks.add(ssid)
                    
                    if all_networks:
                        break
                            
                    time.sleep(1)
            
            networks = sorted(list(all_networks))
            logging.info(f"Found networks: {networks}")
            return networks
            
        except Exception as e:
            logging.error(f"Error scanning WiFi: {str(e)}")
            return []

    def handle_wifi_scan(self):
        """Handle the /wifi-scan route."""
        try:
            networks = self.scan_wifi()
            return jsonify({
                'status': 'complete',
                'networks': networks,
                'ap_mode': self.ap_mode  # Let the frontend know if we're in AP mode
            })
        except Exception as e:
            logging.error(f"Error in wifi scan handler: {str(e)}")
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

    def handle_wifi_status(self):
        """Handle the /wifi/status route."""
        try:
            if self.ap_mode:
                return jsonify({
                    'connected': False,
                    'ap_mode': True,
                    'ssid': self.ap_ssid
                })
            
            current = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            current_ssid = current.stdout.strip()
            
            return jsonify({
                'connected': bool(current_ssid),
                'ap_mode': False,
                'ssid': current_ssid
            })
        except Exception as e:
            logging.error(f"Error getting WiFi status: {e}")
            return jsonify({
                'connected': False,
                'ap_mode': self.ap_mode,
                'error': str(e)
            })

    def handle_reboot(self):
        """Handle the reboot request."""
        try:
            logging.info("Reboot requested via web interface")
            subprocess.run(['sudo', 'reboot'], check=True)
            return jsonify({'status': 'success'})
        except Exception as e:
            logging.error(f"Error rebooting: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    def register_routes(self):
        """Register the WiFi routes."""
        @self.blueprint.route('/wifi-settings', methods=['GET', 'POST'])
        def wifi_settings():
            return self.handle_wifi_settings()
            
        @self.blueprint.route('/wifi-scan')
        def wifi_scan():
            return self.handle_wifi_scan()
            
        @self.blueprint.route('/status')
        def wifi_status():
            return self.handle_wifi_status()
            
        @self.blueprint.route('/ping')
        def ping():
            return self.handle_ping()
            
        @self.blueprint.route('/reboot', methods=['POST'])
        def reboot():
            return self.handle_reboot()

    def init_app(self, app):
        """Initialize the application."""
        self.app = app
        app.register_blueprint(self.blueprint)
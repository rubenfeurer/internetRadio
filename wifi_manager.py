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
        
        # Try to connect to saved networks at startup
        logging.info("Initializing WiFi Manager...")
        self.try_connect_saved_networks()
        
        if app is not None:
            self.init_app(app)

    def setup_logging(self):
        """Setup logging configuration."""
        log_file = '/home/radio/internetRadio/scripts/logs/wifi.log'
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_saved_networks(self):
        """Get list of valid saved network connections."""
        try:
            logging.info("Getting saved networks...")
            
            # First get the actual SSID from preconfigured connection
            active_conn = subprocess.run(
                ['sudo', 'nmcli', '-s', 'connection', 'show', 'preconfigured'],
                capture_output=True, text=True, check=True
            )
            
            # Extract the SSID from active connection
            active_ssid = None
            for line in active_conn.stdout.splitlines():
                if '802-11-wireless.ssid' in line:
                    active_ssid = line.split(':')[1].strip()
                    logging.info(f"Found active SSID: {active_ssid}")
                    break
            
            # Get all saved connections
            result = subprocess.run(
                ['sudo', 'nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'],
                capture_output=True, text=True, check=True
            )
            
            networks = []
            if active_ssid:
                networks.append(active_ssid)
                
            for line in result.stdout.split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) == 2:
                        name, conn_type = parts
                        # Include wifi connections that aren't preconfigured or AP
                        if (conn_type == 'wifi' and 
                            name != self.ap_ssid and 
                            name != 'preconfigured' and 
                            name != '--' and
                            name != active_ssid):
                            networks.append(name)
                            logging.info(f"Found saved wifi network: {name}")
            
            logging.info(f"Final list of saved networks: {networks}")
            return networks
        except Exception as e:
            logging.error(f"Error getting saved networks: {e}")
            return []

    def try_connect_saved_networks(self):
        """Try to connect to saved networks and fall back to AP mode if needed."""
        logging.info("Starting try_connect_saved_networks...")
        
        # First check if we're already connected
        try:
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'GENERAL.STATE', 'device', 'show', 'wlan0'],
                capture_output=True, text=True, check=True
            )
            if 'connected' in result.stdout:
                ssid = subprocess.run(
                    ['iwgetid', '-r'],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
                logging.info(f"Already connected to network: {ssid}")
                self.initial_connection_made = True
                return True
        except Exception as e:
            logging.error(f"Error checking current connection: {e}")
        
        # Get list of saved networks
        networks = self.get_saved_networks()
        logging.info(f"Found saved networks: {networks}")
        
        # Try each saved network
        for network in networks:
            if network != self.ap_ssid:  # Skip our own AP
                logging.info(f"Attempting to connect to: {network}")
                if self.connect_to_network(network):
                    logging.info(f"Connected to {network}, checking internet...")
                    if self.check_internet():
                        logging.info(f"Internet connection confirmed on {network}")
                        self.initial_connection_made = True
                        return True
                    else:
                        logging.info(f"No internet on {network}")
                else:
                    logging.info(f"Failed to connect to {network}")
        
        # If we get here, we couldn't connect to any network
        logging.info("Could not connect to any saved networks, enabling AP mode")
        return self.enable_ap_mode()

    def connect_to_network(self, ssid):
        """Connect to a specific network."""
        try:
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'up', ssid],
                capture_output=True, text=True, check=True
            )
            logging.info(f"Initial connection to {ssid} successful")
            time.sleep(2)  # Changed from 5 to 2 seconds to wait for connection to stabilize
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to connect to {ssid}: {e}")
            return False

    def check_internet(self):
        """Check if we have internet connectivity."""
        try:
            subprocess.run(
                ['ping', '-c', '1', '-W', '5', '8.8.8.8'],
                capture_output=True, check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def enable_ap_mode(self):
        """Enable AP mode using NetworkManager."""
        if self.ap_mode:
            return True
            
        try:
            logging.info("Starting Wi-Fi hotspot...")
            
            # Delete any existing hotspot connections
            subprocess.run(
                ['sudo', 'nmcli', 'connection', 'delete', 'Hotspot'],
                capture_output=True, text=True
            )
            subprocess.run(
                ['sudo', 'nmcli', 'connection', 'delete', self.ap_ssid],
                capture_output=True, text=True
            )
            
            # Create new hotspot
            result = subprocess.run([
                'sudo', 'nmcli', 'device', 'wifi', 'hotspot',
                'ifname', 'wlan0',
                'ssid', self.ap_ssid,
                'password', self.ap_password
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info("Hotspot started successfully")
                self.ap_mode = True
                return True
            else:
                logging.error(f"Failed to start hotspot: {result.stderr}")
                return False
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
        
        # Store reference to self for closure
        manager = self
        
        @self.blueprint.route('/ping')
        def ping():
            return jsonify({'status': 'ok'})
        
        @self.blueprint.route('/wifi-scan')
        def wifi_scan():
            logging.info("WiFi scan route called")
            try:
                networks = manager.scan_wifi()
                logging.info(f"Scan complete. Found networks: {networks}")
                return jsonify({
                    'status': 'success',
                    'networks': networks
                })
            except Exception as e:
                logging.error(f"Error in wifi_scan route: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
            
        @self.blueprint.route('/status')
        def status():
            logging.info("Status route called")
            try:
                return manager.handle_wifi_status()
            except Exception as e:
                logging.error(f"Error in status route: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
            
        @self.blueprint.route('/wifi-settings', methods=['GET', 'POST'])
        def wifi_settings():
            logging.info(f"WiFi settings route called with method: {request.method}")
            try:
                return manager.handle_wifi_settings()
            except Exception as e:
                logging.error(f"Error in wifi_settings route: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
            
        @self.blueprint.route('/reboot', methods=['POST'])
        def reboot():
            logging.info("Reboot route called")
            try:
                return manager.handle_reboot()
            except Exception as e:
                logging.error(f"Error in reboot route: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500

    def init_app(self, app):
        """Initialize the application."""
        self.app = app
        app.register_blueprint(self.blueprint)

    def start_ap_test_mode(self):
        """Start AP test mode with connection removal"""
        try:
            # Create backup directory with timestamp
            backup_dir = f"/home/radio/internetRadio/connection_backup_{int(time.time())}"
            os.makedirs(backup_dir)
            
            # Backup current connections
            subprocess.run(f"sudo cp -r /etc/NetworkManager/system-connections/* {backup_dir}/", shell=True)
            
            # Store test mode info
            with open('/home/radio/internetRadio/ap_test_mode', 'w') as f:
                end_time = time.time() + 300  # 5 minutes
                f.write(f"{end_time}\n{backup_dir}")
                
            # Remove all connections
            subprocess.run("sudo rm /etc/NetworkManager/system-connections/*", shell=True)
            
            logging.info(f"Starting AP test mode. Connections backed up to {backup_dir}")
            
            # Reboot to trigger AP mode
            subprocess.run("sudo reboot", shell=True)
            
        except Exception as e:
            logging.error(f"Error starting AP test mode: {e}")
            return False
        return True

    def check_and_handle_test_mode(self):
        """Check if we're in test mode and handle accordingly"""
        try:
            if os.path.exists('/home/radio/internetRadio/ap_test_mode'):
                with open('/home/radio/internetRadio/ap_test_mode', 'r') as f:
                    lines = f.readlines()
                    end_time = float(lines[0].strip())
                    backup_dir = lines[1].strip()
                    
                if time.time() > end_time:
                    # Test mode expired, restore connections
                    logging.info("AP test mode expired, restoring connections")
                    subprocess.run(f"sudo cp -r {backup_dir}/* /etc/NetworkManager/system-connections/", shell=True)
                    os.remove('/home/radio/internetRadio/ap_test_mode')
                    subprocess.run("sudo reboot", shell=True)
                    return False
                return True
        except Exception as e:
            logging.error(f"Error checking test mode: {e}")
            return False
        return False
from flask import Blueprint, jsonify, request
import subprocess
import logging
import time
import os

class WiFiManager:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
        
        # Register routes with Flask
        wifi_bp = Blueprint('wifi', __name__)
        
        @wifi_bp.route('/api/wifi/status', methods=['GET'])
        def get_wifi_status():
            is_connected = self.check_connection()
            ip_address = self.get_ip_address() if is_connected else None
            return jsonify({
                'connected': is_connected,
                'ip_address': ip_address
            })
            
        @wifi_bp.route('/api/wifi/networks', methods=['GET'])
        def get_networks():
            networks = self.scan_networks()
            return jsonify(networks)
            
        @wifi_bp.route('/api/wifi/connect', methods=['POST'])
        def connect_wifi():
            data = request.get_json()
            ssid = data.get('ssid')
            password = data.get('password')
            
            if not ssid or not password:
                return jsonify({'error': 'SSID and password required'}), 400
                
            success = self.connect_to_network(ssid, password)
            return jsonify({'success': success})
            
        # Register the blueprint with the app
        app.register_blueprint(wifi_bp)

    def check_connection(self):
        """Check if connected to WiFi"""
        try:
            result = subprocess.run(['iwgetid'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error checking WiFi connection: {e}")
            return False

    def get_ip_address(self, interface='wlan0'):
        """Get current IP address"""
        try:
            result = subprocess.check_output(['ip', 'addr', 'show', interface]).decode()
            for line in result.splitlines():
                if 'inet ' in line:
                    return line.strip().split()[1].split('/')[0]
        except Exception as e:
            self.logger.error(f"Error getting IP address: {e}")
            return None

    def scan_networks(self):
        """Scan for available WiFi networks"""
        try:
            result = subprocess.check_output(['sudo', 'iwlist', 'wlan0', 'scan']).decode()
            networks = []
            current_network = {}
            
            for line in result.splitlines():
                line = line.strip()
                if 'ESSID:' in line:
                    ssid = line.split('ESSID:')[1].strip('"')
                    if ssid:  # Only add non-empty SSIDs
                        current_network['ssid'] = ssid
                        networks.append(current_network)
                        current_network = {}
                elif 'Quality=' in line:
                    quality = line.split('Quality=')[1].split(' ')[0]
                    current_network['quality'] = quality
                    
            return networks
        except Exception as e:
            self.logger.error(f"Error scanning networks: {e}")
            return []

    def connect_to_network(self, ssid, password):
        """Connect to a WiFi network"""
        try:
            # Create the connection file
            connection_file = f"""
[connection]
id={ssid}
type=wifi

[wifi]
mode=infrastructure
ssid={ssid}

[wifi-security]
key-mgmt=wpa-psk
psk={password}

[ipv4]
method=auto

[ipv6]
method=auto
"""
            # Save the connection file
            file_path = f"/etc/NetworkManager/system-connections/{ssid}.nmconnection"
            with open(file_path, 'w') as f:
                f.write(connection_file)
                
            # Set proper permissions
            os.chmod(file_path, 0o600)
            
            # Reload NetworkManager and connect
            subprocess.run(['sudo', 'systemctl', 'reload', 'NetworkManager'])
            subprocess.run(['sudo', 'nmcli', 'connection', 'up', ssid])
            
            # Wait for connection
            time.sleep(5)
            return self.check_connection()
            
        except Exception as e:
            self.logger.error(f"Error connecting to network: {e}")
            return False

    def start_hotspot(self):
        """Start WiFi hotspot"""
        try:
            subprocess.run([
                'sudo', 'nmcli', 'device', 'wifi', 'hotspot',
                'ssid', 'Radio', 'password', 'Radio@1234',
                'ifname', 'wlan0'
            ], check=True)
            
            ip_address = self.get_ip_address('wlan0')
            if ip_address:
                self.logger.info(f"Hotspot started. IP: {ip_address}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error starting hotspot: {e}")
            return False
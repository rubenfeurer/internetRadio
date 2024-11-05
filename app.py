from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import subprocess
import re
import toml
from stream_manager import StreamManager
import json

def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__, static_folder='templates/static')
    app.secret_key = 'your_secret_key_here'

    player = StreamManager(50)

    @app.route('/')
    def index():
        """Render the index page with configuration links."""
        config = toml.load('config.toml')
        links = config.get('links', [])
        link1 = config.get('link1')
        link2 = config.get('link2')
        link3 = config.get('link3')

        link_to_channel_mapping = {link['url']: link['name'] for link in links}
    
        channel1_name = link_to_channel_mapping.get(link1, "Unknown Channel")
        channel2_name = link_to_channel_mapping.get(link2, "Unknown Channel")
        channel3_name = link_to_channel_mapping.get(link3, "Unknown Channel")

        return render_template('index.html', link1=channel1_name, link2=channel2_name, link3=channel3_name)

    @app.route('/wifi-setup')
    def wifi_settings():
        """Render the Wi-Fi setup page with a list of available SSIDs."""
        ssids = scan_wifi()
        return render_template('wifi_settings.html', ssids=ssids)

    @app.route('/wifi-setup', methods=['POST'])
    def wifi_setup():
        ssid = request.form.get('ssid')
        password = request.form.get('password')
        if ssid and password:
            # Try to connect to the Wi-Fi network
            connect_to_wifi(ssid, password)
            return redirect(url_for('index'))
        return redirect(url_for('wifi_settings'))
    
    @app.route('/stream-select', methods=['GET'])
    def select_link():
        channel = request.args.get('channel')  # Get channel (link1, link2, etc.) from the query params
        # Load the config file
        config_data = toml.load('config.toml')

        # Extract active links
        active_links = {
            'link1': config_data['link1'],
            'link2': config_data['link2'],
            'link3': config_data['link3']
        }

        # Extract spare links
        spare_links = config_data['links']

        return render_template('stream_select.html', channel=channel, active_links=active_links, spare_links=spare_links)

    @app.route('/update-stream', methods=['POST'])
    def update_link():
        channel = request.form['channel']  # e.g., link1, link2, link3
        selected_link = request.form['selected_link']  # The new URL selected by the user

        # Load the config file
        config_data = toml.load('config.toml')

        # Update the selected link
        config_data[channel] = selected_link

        # Write the changes back to config.toml
        with open('config.toml', 'w') as configfile:
            toml.dump(config_data, configfile)

        print(f"Channel: {channel}, Selected Link: {selected_link}")
        return jsonify({'success': True})  # Redirect back to the main page

    @app.route('/play-stream', methods=['POST'])
    def play_stream():
        url_stream = request.form['url']  # Get the channel from the request
        player.play_stream_radio(url_stream)  # Call the play_stream method
        return jsonify({'success': True})  # Return a success response

    def connect_to_wifi(ssid, password):
        connection_command = ["nmcli", "--colors", "no", "device", "wifi", "connect", ssid, "ifname", "wlan0"]
        if len(password) > 0:
          connection_command.append("password")
          connection_command.append(password)
        result = subprocess.run(connection_command, capture_output=True)
        if result.stderr:
            return "Error: failed to connect to wifi network: <i>%s</i>" % result.stderr.decode()
        elif result.stdout:
            return "Success: <i>%s</i>" % result.stdout.decode()
        return "Error: failed to connect."

    def scan_wifi():
        """Scan for available Wi-Fi networks using nmcli."""
        try:
            # Force a rescan on both bands
            result = subprocess.check_output(
                ["nmcli", "device", "wifi", "rescan"],
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Get all networks, including 5GHz
            result = subprocess.check_output(
                ["nmcli", "-f", "SSID,FREQ", "device", "wifi", "list"],
                text=True
            )
            
            # Process and print debug info
            networks = []
            for line in result.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 1:
                        ssid = parts[0]
                        freq = parts[1] if len(parts) > 1 else "unknown"
                        networks.append(ssid)
                        print(f"Found network: {ssid} on {freq}")  # Debug info
            
            return list(dict.fromkeys(networks))  # Remove duplicates while preserving order
            
        except subprocess.CalledProcessError as e:
            print(f"Error scanning WiFi: {str(e)}")
            return []

    @app.route('/get_wifi_ssid')
    def get_wifi_ssid():
        try:
            # Check the Wi-Fi connection by using iwgetid
            result = subprocess.run(['iwgetid', '-r'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ssid = result.stdout.decode().strip()
            if ssid:
                return jsonify({'ssid': ssid})
            else:
                return jsonify({'error': 'No Wi-Fi connected'})
        except Exception as e:
            return jsonify({'error': str(e)})
    
    @app.route('/check_internet_connection')
    def check_internet_connection():
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return jsonify({'connected': True})
            else:
                return jsonify({'connected': False})
        except Exception as e:
            return jsonify({'connected': False, 'error': str(e)})

    @app.route('/wifi-debug')
    def wifi_debug():
        try:
            # Get current connection info
            iw_info = subprocess.check_output(["iwconfig", "wlan0"], text=True)
            nm_status = subprocess.check_output(["nmcli", "device", "status"], text=True)
            
            # Parse current connection
            current = {}
            for line in iw_info.splitlines():
                if "ESSID" in line:
                    current["ESSID"] = line.split('ESSID:')[1].strip('"')
                if "Frequency" in line:
                    current["Frequency"] = line.split('Frequency:')[1].split()[0]
                if "Signal level" in line:
                    current["Signal"] = line.split('Signal level=')[1].split()[0]

            # Parse network devices
            devices = []
            for line in nm_status.splitlines()[1:]:  # Skip header
                if line:
                    parts = line.split()
                    devices.append({
                        "device": parts[0],
                        "type": parts[1],
                        "state": parts[2]
                    })

            # Return the template with our parsed data
            return render_template('wifi_debug.html', 
                                current=current,
                                devices=devices,
                                networks=[])  # We'll add network scanning later

        except Exception as e:
            return f"Error: {str(e)}"

    def check_radio_status():
        try:
            result = subprocess.run(['systemctl', 'is-active', 'radio'], 
                                  capture_output=True, 
                                  text=True)
            if result.stdout.strip() == 'active':
                return True, "Radio service is running"
            else:
                return False, f"Radio service is not active: {result.stdout.strip()}"
        except Exception as e:
            return False, f"Error checking radio status: {str(e)}"

    return app

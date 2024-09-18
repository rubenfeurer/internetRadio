from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import subprocess
import re
import toml

def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here'

    @app.route('/')
    def index():
        """Render the index page with configuration links."""
        config = toml.load('config.toml')
        return render_template('index.html', link1=config.get('link1', ''), link2=config.get('link2', ''), link3=config.get('link3', ''))

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
        """Scan for available Wi-Fi networks and return a list of SSIDs."""
        try:
            result = subprocess.check_output(["sudo", "iwlist", "wlan0", "scan"], stderr=subprocess.STDOUT, text=True)
            ssids = re.findall(r'ESSID:"(.*?)"', result)
            return ssids
        except subprocess.CalledProcessError as e:
            print(f"Error scanning Wi-Fi: {e.output}")
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

    return app

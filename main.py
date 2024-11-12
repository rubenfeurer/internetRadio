#!/usr/bin/env -S python

import subprocess
import threading
import time
import os
import logging
import signal
import sys
import pygame
import vlc
from flask import Flask, request, jsonify, render_template, url_for
from gpiozero import Button, RotaryEncoder, LED, Device
from gpiozero.pins.pigpio import PiGPIOFactory
import pigpio
import re
import toml
import tempfile

# Set up logging with more detailed configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/radio/internetRadio/logs/app.log'),
        logging.FileHandler('/home/radio/internetRadio/logs/network_debug.log'),  # Separate file for network logs
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add a specific logger for network operations
network_logger = logging.getLogger('network')
network_logger.setLevel(logging.DEBUG)
network_handler = logging.FileHandler('/home/radio/internetRadio/logs/network_debug.log')
network_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
network_logger.addHandler(network_handler)

def log_network_status():
    try:
        # Log WiFi interface status
        wifi_status = subprocess.run(["iwconfig", "wlan0"], capture_output=True, text=True)
        network_logger.info(f"WiFi Status:\n{wifi_status.stdout}")

        # Log IP configuration
        ip_status = subprocess.run(["ip", "addr", "show", "wlan0"], capture_output=True, text=True)
        network_logger.info(f"IP Configuration:\n{ip_status.stdout}")

        # Log routing table
        route_status = subprocess.run(["ip", "route"], capture_output=True, text=True)
        network_logger.info(f"Routing Table:\n{route_status.stdout}")

        # Log NetworkManager status
        nm_status = subprocess.run(["systemctl", "status", "NetworkManager"], capture_output=True, text=True)
        network_logger.info(f"NetworkManager Status:\n{nm_status.stdout}")

        # Log hostapd status if in AP mode
        hostapd_status = subprocess.run(["systemctl", "status", "hostapd"], capture_output=True, text=True)
        network_logger.info(f"Hostapd Status:\n{hostapd_status.stdout}")

        # Log dnsmasq status if in AP mode
        dnsmasq_status = subprocess.run(["systemctl", "status", "dnsmasq"], capture_output=True, text=True)
        network_logger.info(f"Dnsmasq Status:\n{dnsmasq_status.stdout}")

    except Exception as e:
        network_logger.error(f"Error logging network status: {str(e)}")

# Initialize pigpio
print("Initializing pigpio...")
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpiod")
    exit()
print("Connected to pigpiod successfully")

# Set up PiGPIO as the pin factory
Device.pin_factory = PiGPIOFactory()

# Constants
SOUND_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
LED_PIN = 25  # LED on GPIO25
ENCODER_SW = 10  # Encoder button on GPIO10
ENCODER_DT = 9  # Encoder DT on GPIO9
ENCODER_CLK = 11  # Encoder CLK on GPIO11
BUTTON_PINS = {
    'link1': 17,  # Button 1 on GPIO17
    'link2': 16,  # Button 2 on GPIO16
    'link3': 26   # Button 3 on GPIO26
}

class StreamManager:
    def __init__(self, initial_volume=50):
        logger.info("Initializing StreamManager...")
        self.instance = vlc.Instance('--no-xlib',
                                   '--aout=alsa',
                                   '--alsa-audio-device=hw:2,0')
        self.player = self.instance.media_player_new()
        self.volume = initial_volume
        self.current_stream = None
        self.is_playing = False
        self.streams = {}  # Dictionary to store stream URLs for each button
        
        # Initialize streams from config.toml
        try:
            with open('config.toml', 'r', encoding='utf-8') as f:
                config = toml.load(f)
                stations = config.get('links', [])
                # Set first three stations as default streams
                for i, station in enumerate(stations[:3]):
                    self.streams[f'link{i+1}'] = station['url']
        except Exception as e:
            logger.error(f"Error loading initial streams: {e}")
        
        self.player.audio_set_volume(self.volume)
        logger.info("StreamManager initialized with streams: %s", self.streams)

    def play_stream(self, stream_key):
        try:
            logger.info(f"Playing stream_key: {stream_key}")
            logger.info(f"Available streams: {self.streams}")
            
            if stream_key in self.streams:
                if self.current_stream == stream_key and self.is_playing:
                    logger.info("Stopping current stream")
                    self.stop_stream()
                    return True
                
                self.current_stream = stream_key
                stream_url = self.streams[stream_key]
                logger.info(f"Creating media for URL: {stream_url}")
                media = self.instance.media_new(stream_url)
                self.player.set_media(media)
                success = self.player.play() == 0
                self.is_playing = success
                logger.info(f"Stream play result: {success}")
                return success
            return False
        except Exception as e:
            logger.error(f"Error playing stream: {e}")
            return False

    def stop_stream(self):
        try:
            logger.info("Stopping stream")
            self.player.stop()
            self.is_playing = False
            return True
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return False

    def set_volume(self, volume):
        try:
            self.volume = max(0, min(100, volume))
            self.player.audio_set_volume(self.volume)
            logger.info(f"Volume set to {self.volume}")
        except Exception as e:
            logger.error(f"Error setting volume: {e}")

    def get_volume(self):
        return self.volume

class SoundManager:
    def __init__(self, sounds_dir):
        logger.info("Initializing SoundManager...")
        self.sounds_dir = sounds_dir
        pygame.mixer.init()
        logger.info("SoundManager initialized")

    def play_sound(self, sound_file):
        try:
            sound_path = os.path.join(self.sounds_dir, sound_file)
            if os.path.exists(sound_path):
                sound = pygame.mixer.Sound(sound_path)
                sound.play()
                logger.info(f"Playing sound: {sound_file}")
            else:
                logger.error(f"Sound file not found: {sound_path}")
        except Exception as e:
            logger.error(f"Error playing sound: {e}")

class WiFiManager:
    def __init__(self):
        logger.info("Initializing WiFiManager...")
        self.networks = []
        self.update_networks()
        logger.info("WiFiManager initialized")

    def update_networks(self):
        try:
            result = subprocess.run(
                ["sudo", "iwlist", "wlan0", "scan"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                networks = []
                for line in result.stdout.split('\n'):
                    if 'ESSID:' in line:
                        essid = line.split('ESSID:"')[1].split('"')[0]
                        if essid:  # Only add non-empty ESSIDs
                            networks.append(essid)
                self.networks = list(set(networks))  # Remove duplicates
                logger.info(f"Found networks: {self.networks}")
            else:
                logger.error("Failed to scan networks")
                
        except Exception as e:
            logger.error(f"Error updating networks: {e}")

    def get_networks(self):
        return self.networks

    def connect_to_network(self, ssid, password):
        try:
            # Create a temporary file for the connection
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                connection_content = f"""[connection]
id={ssid}
uuid=$(uuidgen)
type=wifi

[wifi]
mode=infrastructure
ssid={ssid}

[wifi-security]
auth-alg=open
key-mgmt=wpa-psk
psk={password}

[ipv4]
method=auto

[ipv6]
addr-gen-mode=stable-privacy
method=auto"""
                temp_file.write(connection_content)
                temp_file_path = temp_file.name

            # Import the connection
            result = subprocess.run(
                ["sudo", "nmcli", "connection", "import", "type", "wifi", "file", temp_file_path],
                capture_output=True,
                text=True
            )

            # Clean up the temporary file
            os.unlink(temp_file_path)

            if result.returncode == 0:
                logger.info(f"Successfully imported connection for {ssid}")
                
                # Try to connect to the network
                connect_result = subprocess.run(
                    ["sudo", "nmcli", "connection", "up", ssid],
                    capture_output=True,
                    text=True
                )
                
                if connect_result.returncode == 0:
                    logger.info(f"Successfully connected to {ssid}")
                    return True, "Connected successfully"
                else:
                    logger.error(f"Failed to connect to {ssid}: {connect_result.stderr}")
                    return False, f"Failed to connect: {connect_result.stderr}"
            else:
                logger.error(f"Failed to import connection: {result.stderr}")
                return False, f"Failed to import connection: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error connecting to network: {e}")
            return False, f"Error: {str(e)}"

class RadioController:
    def __init__(self):
        logger.info("Initializing RadioController...")
        self.app = self.create_app()
        self.stream_manager = None
        self.sound_manager = None
        self.wifi_manager = None
        self.led = None
        self.encoder = None
        self.buttons = {}
        logger.info("RadioController initialized")

    def initialize(self):
        try:
            # Initialize LED
            self.led = LED(LED_PIN)
            
            # Initialize rotary encoder
            self.encoder = RotaryEncoder(ENCODER_DT, ENCODER_CLK)
            self.encoder.when_rotated_clockwise = self.volume_up
            self.encoder.when_rotated_counter_clockwise = self.volume_down
            
            # Initialize buttons
            for name, pin in BUTTON_PINS.items():
                button = Button(pin)
                button.when_pressed = lambda n=name: self.handle_button_press(n)
                self.buttons[name] = button
            
            # Initialize managers
            self.stream_manager = StreamManager()
            self.sound_manager = SoundManager(SOUND_FOLDER)
            self.wifi_manager = WiFiManager()
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            return False

    def create_app(self):
        app = Flask(__name__)

        @app.route('/wifi_settings')
        def wifi_settings():
            available_networks = get_available_networks()
            saved_networks = get_saved_networks()
            return render_template('wifi_settings.html', 
                                 available_networks=available_networks,
                                 saved_networks=saved_networks)

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/api/networks', methods=['GET'])
        def get_networks():
            try:
                self.wifi_manager.update_networks()
                networks = self.wifi_manager.get_networks()
                return jsonify({"networks": networks})
            except Exception as e:
                logger.error(f"Error getting networks: {e}")
                return jsonify({"error": str(e)}), 500

        @app.route('/api/connect', methods=['POST'])
        def connect_network():
            try:
                data = request.get_json()
                ssid = data.get('ssid')
                password = data.get('password')
                
                if not ssid or not password:
                    return jsonify({"error": "SSID and password required"}), 400
                
                success, message = self.wifi_manager.connect_to_network(ssid, password)
                
                if success:
                    return jsonify({"message": message})
                else:
                    return jsonify({"error": message}), 500
                    
            except Exception as e:
                logger.error(f"Error connecting to network: {e}")
                return jsonify({"error": str(e)}), 500

        @app.route('/api/volume', methods=['GET', 'POST'])
        def handle_volume():
            if request.method == 'GET':
                try:
                    volume = self.stream_manager.get_volume()
                    return jsonify({"volume": volume})
                except Exception as e:
                    logger.error(f"Error getting volume: {e}")
                    return jsonify({"error": str(e)}), 500
            else:
                try:
                    data = request.get_json()
                    volume = data.get('volume')
                    
                    if volume is None:
                        return jsonify({"error": "Volume value required"}), 400
                        
                    self.stream_manager.set_volume(volume)
                    return jsonify({"message": "Volume updated successfully"})
                    
                except Exception as e:
                    logger.error(f"Error setting volume: {e}")
                    return jsonify({"error": str(e)}), 500

        @app.route('/api/stream/<stream_key>', methods=['POST'])
        def handle_stream(stream_key):
            try:
                success = self.stream_manager.play_stream(stream_key)
                
                if success:
                    return jsonify({"message": f"Stream {stream_key} handled successfully"})
                else:
                    return jsonify({"error": f"Failed to handle stream {stream_key}"}), 500
                    
            except Exception as e:
                logger.error(f"Error handling stream: {e}")
                return jsonify({"error": str(e)}), 500

        @app.route('/api/stop', methods=['POST'])
        def stop_stream():
            try:
                success = self.stream_manager.stop_stream()
                
                if success:
                    return jsonify({"message": "Stream stopped successfully"})
                else:
                    return jsonify({"error": "Failed to stop stream"}), 500
                    
            except Exception as e:
                logger.error(f"Error stopping stream: {e}")
                return jsonify({"error": str(e)}), 500

        return app

    def handle_button_press(self, button_name):
        try:
            logger.info(f"Button pressed: {button_name}")
            self.sound_manager.play_sound("click.wav")
            self.stream_manager.play_stream(button_name)
        except Exception as e:
            logger.error(f"Error handling button press: {e}")

    def volume_up(self):
        try:
            current_volume = self.stream_manager.get_volume()
            new_volume = min(100, current_volume + 5)
            self.stream_manager.set_volume(new_volume)
            self.sound_manager.play_sound("click.wav")
        except Exception as e:
            logger.error(f"Error increasing volume: {e}")

    def volume_down(self):
        try:
            current_volume = self.stream_manager.get_volume()
            new_volume = max(0, current_volume - 5)
            self.stream_manager.set_volume(new_volume)
            self.sound_manager.play_sound("click.wav")
        except Exception as e:
            logger.error(f"Error decreasing volume: {e}")

def signal_handler(signum, frame):
    logger.info("Received signal to terminate")
    sys.exit(0)

def is_in_ap_mode():
    try:
        # Check if hostapd is running
        hostapd_status = subprocess.run(
            ["sudo", "systemctl", "is-active", "hostapd"],
            capture_output=True,
            text=True
        )
        return hostapd_status.stdout.strip() == "active"
    except Exception as e:
        logger.error(f"Error checking AP mode: {str(e)}")
        return False

def get_saved_networks():
    try:
        logger.info("Checking for saved networks...")
        result = subprocess.run(
            ["sudo", "nmcli", "connection", "show"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            networks = []
            logger.info(f"Raw nmcli output: {result.stdout}")  # Debug line
            
            for line in result.stdout.split('\n')[1:]:  # Skip header line
                if line.strip():
                    # Split line and get connection name and type
                    parts = line.split()
                    if len(parts) >= 3 and parts[2] == "wifi":  # Check if it's a WiFi connection
                        networks.append(parts[0])
            
            logger.info(f"Found saved WiFi networks: {networks}")
            return networks
        
        logger.error(f"nmcli command failed with return code: {result.returncode}")
        logger.error(f"Error output: {result.stderr}")
        return []
        
    except Exception as e:
        logger.error(f"Error getting saved networks: {str(e)}")
        return []

def get_available_networks():
    try:
        result = subprocess.run(
            ["sudo", "iwlist", "wlan0", "scan"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            networks = []
            for line in result.stdout.split('\n'):
                if 'ESSID:' in line:
                    essid = line.split('ESSID:"')[1].split('"')[0]
                    if essid:  # Only add non-empty ESSIDs
                        networks.append(essid)
            return list(set(networks))  # Remove duplicates
        return []
        
    except Exception as e:
        logger.error(f"Error getting networks: {str(e)}")
        return []

def setup_ap_mode():
    try:
        # Create hostapd configuration
        hostapd_conf = """interface=wlan0
driver=nl80211
ssid=InternetRadio
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=raspberry
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP"""

        # Write hostapd configuration
        with open('/etc/hostapd/hostapd.conf', 'w') as f:
            f.write(hostapd_conf)

        # Create dnsmasq configuration
        dnsmasq_conf = """interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=wlan
address=/gw.wlan/192.168.4.1"""

        # Write dnsmasq configuration
        with open('/etc/dnsmasq.conf', 'w') as f:
            f.write(dnsmasq_conf)

        # Update hostapd default configuration
        with open('/etc/default/hostapd', 'w') as f:
            f.write('DAEMON_CONF="/etc/hostapd/hostapd.conf"')

        return True

    except Exception as e:
        logger.error(f"Error setting up AP mode: {str(e)}")
        return False



def switch_to_ap_mode():
    try:
        logger.info("Starting AP mode setup...")
        
        # Stop potentially interfering services
        logger.info("Stopping NetworkManager...")
        subprocess.run(["sudo", "systemctl", "stop", "NetworkManager"])
        time.sleep(2)
        
        logger.info("Stopping wpa_supplicant...")
        subprocess.run(["sudo", "systemctl", "stop", "wpa_supplicant"])
        time.sleep(2)
        
        # Ensure wireless interface is up and not blocked
        logger.info("Unblocking WiFi and bringing up interface...")
        subprocess.run(["sudo", "rfkill", "unblock", "wifi"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        time.sleep(1)
        
        # Configure network interface
        logger.info("Configuring network interface...")
        subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
        time.sleep(1)
        subprocess.run(["sudo", "ifconfig", "wlan0", "192.168.4.1", "netmask", "255.255.255.0"])
        time.sleep(1)
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        time.sleep(1)
        
        # Start services in correct order with proper delays
        logger.info("Starting dnsmasq...")
        subprocess.run(["sudo", "systemctl", "start", "dnsmasq"])
        time.sleep(3)
        
        logger.info("Starting hostapd...")
        subprocess.run(["sudo", "systemctl", "start", "hostapd"])
        time.sleep(3)
        
        # Verify services are running
        logger.info("Verifying services...")
        dnsmasq_status = subprocess.run(["sudo", "systemctl", "is-active", "dnsmasq"], 
                                      capture_output=True, text=True)
        hostapd_status = subprocess.run(["sudo", "systemctl", "is-active", "hostapd"], 
                                      capture_output=True, text=True)
        
        logger.info(f"dnsmasq status: {dnsmasq_status.stdout.strip()}")
        logger.info(f"hostapd status: {hostapd_status.stdout.strip()}")
        
        if dnsmasq_status.stdout.strip() != "active" or hostapd_status.stdout.strip() != "active":
            logger.error("Failed to start AP mode services")
            return False
        
        logger.info("AP mode activated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error switching to AP mode: {str(e)}")
        return False

def check_and_setup_network():
    try:
        network_logger.info("=== Starting network setup check ===")
        log_network_status()  # Log initial state
        
        saved_networks = get_saved_networks()
        network_logger.info(f"Found saved networks: {saved_networks}")
        
        if not saved_networks:
            network_logger.info("No saved networks found, switching to AP mode")
            ap_result = switch_to_ap_mode()
            network_logger.info(f"AP mode setup result: {ap_result}")
            log_network_status()  # Log state after AP mode setup
            return ap_result
            
        # Try to connect to saved networks
        max_retries = 3
        for network in saved_networks:
            network_logger.info(f"Attempting to connect to {network}")
            
            for attempt in range(max_retries):
                network_logger.info(f"Connection attempt {attempt + 1} of {max_retries} for {network}")
                
                result = subprocess.run(
                    ["sudo", "nmcli", "connection", "up", network],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    network_logger.info(f"Successfully connected to {network}")
                    log_network_status()  # Log successful connection state
                    return True
                
                network_logger.warning(f"Failed to connect to {network} on attempt {attempt + 1}")
                network_logger.warning(f"Error output: {result.stderr}")
                time.sleep(2)
            
            network_logger.warning(f"All connection attempts failed for {network}")
        
        network_logger.info("Could not connect to any saved networks, switching to AP mode")
        ap_result = switch_to_ap_mode()
        network_logger.info(f"AP mode setup result: {ap_result}")
        log_network_status()  # Log final state
        return ap_result
        
    except Exception as e:
        network_logger.error(f"Error in network setup: {str(e)}")
        return False

def main():
    try:
        # Set up signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Create and initialize radio controller
        global radio
        radio = RadioController()
        if not radio.initialize():
            logger.error("Failed to initialize radio")
            return 1

        # Try to connect to saved networks first
        wifi_connected = check_and_setup_network()
        
        if wifi_connected:
            radio.led.blink(on_time=3, off_time=3)
        else:
            logger.info("Could not connect to any networks, maintaining AP mode...")
            radio.led.blink(on_time=0.5, off_time=0.5)

        # Start Flask in a separate thread
        flask_thread = threading.Thread(
            target=lambda: radio.app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        )
        flask_thread.daemon = True
        flask_thread.start()

        # Keep the main thread running and monitor AP mode if active
        while True:
            if not wifi_connected:
                # Verify AP mode is still active
                if not is_in_ap_mode():
                    logger.warning("AP mode stopped unexpectedly, restarting...")
                    switch_to_ap_mode()
            time.sleep(5)

    except Exception as e:
        logger.error(f"Main error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
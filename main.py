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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/home/radio/internetRadio/logs/app.log'
)
logger = logging.getLogger(__name__)

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
    def __init__(self, app):
        self.app = app
        self.interface = "wlan0"

    def start_hotspot(self):
        try:
            logger.info("Starting WiFi hotspot...")
            # Add hotspot setup code here if needed
            pass
        except Exception as e:
            logger.error(f"Error starting hotspot: {e}")

    def get_current_wifi_status(self):
        try:
            result = subprocess.run(['iwgetid', '-r'], 
                                  capture_output=True, 
                                  text=True)
            current_ssid = result.stdout.strip() if result.returncode == 0 else None
            
            result = subprocess.run(['iwconfig', self.interface], 
                                  capture_output=True, 
                                  text=True)
            signal_match = re.search(r'Signal level=(-\d+)', result.stdout)
            signal_strength = signal_match.group(1) if signal_match else 'unknown'
            
            return {
                'connected': bool(current_ssid),
                'ssid': current_ssid if current_ssid else None,
                'signal_strength': signal_strength
            }
        except Exception as e:
            logger.error(f"Error getting WiFi status: {e}")
            return {'connected': False, 'ssid': None, 'signal_strength': 'unknown'}

class RadioController:
    def __init__(self):
        self.stream_manager = None
        self.sound_manager = None
        self.wifi_manager = None
        self.buttons = {}
        self.encoder = None
        self.led = None
        self.app = None

    def initialize(self):
        try:
            print("\n=== INITIALIZATION START ===")
            
            # Initialize StreamManager
            self.stream_manager = StreamManager(50)
            
            # Initialize sound manager
            self.sound_manager = SoundManager(SOUND_FOLDER)
            self.sound_manager.play_sound("boot.wav")
            
            # Initialize LED
            self.led = LED(LED_PIN)
            self.setup_buttons()
            self.setup_encoder()
            
            # Create Flask app
            self.app = create_app(self.stream_manager)
            
            return True
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False

    def setup_buttons(self):
        try:
            self.buttons = {
                'link1': Button(BUTTON_PINS['link1'], pull_up=True, bounce_time=0.2),
                'link2': Button(BUTTON_PINS['link2'], pull_up=True, bounce_time=0.2),
                'link3': Button(BUTTON_PINS['link3'], pull_up=True, bounce_time=0.2),
                'encoder': Button(ENCODER_SW, pull_up=True, bounce_time=0.2, hold_time=2)
            }
            
            # Set up callbacks
            self.buttons['link1'].when_pressed = lambda: self.button_handler('link1')
            self.buttons['link2'].when_pressed = lambda: self.button_handler('link2')
            self.buttons['link3'].when_pressed = lambda: self.button_handler('link3')
            self.buttons['encoder'].when_pressed = lambda: logger.info("Encoder Pressed")
            self.buttons['encoder'].when_held = restart_pi
            
        except Exception as e:
            logger.error(f"Button setup error: {e}")

    def setup_encoder(self):
        try:
            self.encoder = RotaryEncoder(
                ENCODER_DT,
                ENCODER_CLK,
                bounce_time=0.1,
                max_steps=1,
                wrap=False
            )
            self.encoder.when_rotated_clockwise = self.volume_up
            self.encoder.when_rotated_counter_clockwise = self.volume_down
        except Exception as e:
            logger.error(f"Encoder setup error: {e}")

    def button_handler(self, stream_key):
        try:
            logger.info(f"Button pressed for stream: {stream_key}")
            if self.stream_manager:
                self.sound_manager.play_sound("click.wav")
                self.stream_manager.play_stream(stream_key)
        except Exception as e:
            logger.error(f"Button handler error: {e}")
            self.sound_manager.play_sound("error.wav")

    def volume_up(self):
        if self.stream_manager:
            current_volume = self.stream_manager.get_volume()
            new_volume = min(100, current_volume + 5)
            self.stream_manager.set_volume(new_volume)
            logger.info(f"Volume up: {new_volume}")

    def volume_down(self):
        if self.stream_manager:
            current_volume = self.stream_manager.get_volume()
            new_volume = max(0, current_volume - 5)
            self.stream_manager.set_volume(new_volume)
            logger.info(f"Volume down: {new_volume}")

    def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Starting cleanup...")
            if self.stream_manager:
                self.stream_manager.stop_stream()
            if self.led:
                self.led.off()
            if self.sound_manager:
                self.sound_manager.play_sound("shutdown.wav")
                time.sleep(1)  # Give time for shutdown sound to play
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Move this function outside create_app
def is_in_ap_mode():
    """Check if device is in Access Point mode"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'hostapd'], 
                              capture_output=True, text=True)
        logger.info(f"hostapd service {result.stdout.strip()}")
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking AP mode: {e}")
        return False

def create_app(stream_manager):
    app = Flask(__name__, 
                static_folder='static',
                static_url_path='/static')
    
    @app.route('/')
    def index():
        try:
            # Load radio stations from config.toml
            with open('config.toml', 'r', encoding='utf-8') as f:
                config = toml.load(f)
                stations = config.get('links', [])
            
            # Get default streams (first three entries)
            default_streams = stations[:3]
            
            return render_template('index.html', default_streams=default_streams)
        except Exception as e:
            logger.error(f"Error in index: {e}")
            return str(e), 500

    @app.route('/wifi_settings', methods=['GET', 'POST'])
    def wifi_settings():
        if request.method == 'POST':
            try:
                # If we're in AP mode, disable it before connecting
                if is_in_ap_mode():
                    if not disable_ap_mode():
                        return jsonify({
                            'status': 'error',
                            'message': 'Failed to disable AP mode'
                        })
                    time.sleep(2)  # Give services time to restart
                
                ssid = request.form.get('ssid')
                password = request.form.get('password')
                
                if not ssid or not password:
                    return jsonify({
                        'status': 'error',
                        'message': 'SSID and password are required'
                    })

                logger.info(f"Attempting to connect to network: {ssid}")
                
                # Delete existing connection with same SSID if exists
                subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid], 
                             capture_output=True)
                
                # Add new connection
                logger.info(f"Adding new connection for {ssid}")
                add_result = subprocess.run([
                    'sudo', 'nmcli', 'connection', 'add',
                    'type', 'wifi',
                    'con-name', ssid,
                    'ifname', 'wlan0',
                    'ssid', ssid,
                    'wifi-sec.key-mgmt', 'wpa-psk',
                    'wifi-sec.psk', password
                ], capture_output=True, text=True)
                
                if add_result.returncode != 0:
                    raise Exception(f"Failed to add connection: {add_result.stderr}")
                
                # Try to activate new connection
                logger.info(f"Activating connection to {ssid}")
                activate_result = subprocess.run([
                    'sudo', 'nmcli', 'connection', 'up', ssid
                ], capture_output=True, text=True)
                
                # Check connection status
                max_attempts = 3
                for attempt in range(max_attempts):
                    logger.info(f"Connection verification attempt {attempt + 1}/{max_attempts}")
                    time.sleep(5)
                    
                    check_result = subprocess.run([
                        'nmcli', '-t', '-f', 'NAME', 'connection', 'show', '--active'
                    ], capture_output=True, text=True)
                    
                    new_ssid = check_result.stdout.strip()
                    logger.info(f"Current SSID: {new_ssid}")
                    
                    if ssid in new_ssid:
                        logger.info(f"Successfully connected to {ssid}")
                        return jsonify({
                            'status': 'success',
                            'message': 'Connected successfully'
                        })
                
                # Connection failed, restore previous connection
                logger.error(f"Failed to connect to {ssid}, restoring previous connection")
                if current_ssid:
                    logger.info(f"Reconnecting to {current_ssid}")
                    subprocess.run([
                        'sudo', 'nmcli', 'connection', 'up', current_ssid
                    ])
                
                # Clean up failed connection
                subprocess.run([
                    'sudo', 'nmcli', 'connection', 'delete', ssid
                ])
                
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to connect. Please check your password.'
                })
                
            except Exception as network_error:
                logger.error(f"Network error: {network_error}")
                # Try to restore previous connection
                if current_ssid:
                    subprocess.run([
                        'sudo', 'nmcli', 'connection', 'up', current_ssid
                    ])
                raise
                
            except Exception as e:
                logger.error(f"Error in wifi_settings: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                })
            
        return render_template('wifi_settings.html')

    @app.route('/wifi-scan')
    def wifi_scan():
        try:
            # Get current connection
            iwgetid_result = subprocess.run(['iwgetid', '-r'], 
                                          capture_output=True, text=True)
            current_network = iwgetid_result.stdout.strip() if iwgetid_result.stdout else None
            
            # Get available and saved networks
            available_networks = get_wifi_networks()
            saved_networks = get_saved_networks()
            
            response_data = {
                'status': 'complete',
                'networks': available_networks,
                'saved_networks': saved_networks,
                'current_network': current_network,
                'ap_mode': is_in_ap_mode()
            }
            
            logger.info(f"Sending response: {response_data}")
            return jsonify(response_data)
        except Exception as e:
            logger.error(f"Error in wifi_scan: {e}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            })

    # Add WiFi status route
    @app.route('/get_wifi_ssid')
    def get_wifi_ssid():
        try:
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            ssid = result.stdout.strip() if result.returncode == 0 else None
            return jsonify({'ssid': ssid})
        except Exception as e:
            logger.error(f"Error getting SSID: {e}")
            return jsonify({'error': str(e)})

    # Add internet check route
    @app.route('/check_internet_connection')
    def check_internet_connection():
        try:
            subprocess.check_output(['ping', '-c', '1', '8.8.8.8'])
            return jsonify({'connected': True})
        except Exception as e:
            logger.error(f"Error checking internet: {e}")
            return jsonify({'connected': False})

    @app.route('/play-stream', methods=['POST'])
    def play_stream():
        try:
            url = request.form.get('url')
            logger.info(f"Attempting to play URL: {url}")
            logger.info(f"Available streams: {stream_manager.streams}")
            
            if not url:
                return jsonify({'success': False, 'error': 'URL required'}), 400
                
            # Find which channel this URL belongs to
            channel = None
            for key, stream_url in stream_manager.streams.items():
                if stream_url == url:
                    channel = key
                    break
                    
            if channel:
                success = stream_manager.play_stream(channel)
            else:
                # If no channel found, play directly with URL
                media = stream_manager.instance.media_new(url)
                stream_manager.player.set_media(media)
                success = stream_manager.player.play() == 0
                
            return jsonify({'success': success})
        except Exception as e:
            logger.error(f"Error playing stream: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/stop-stream', methods=['POST'])
    def stop_stream():
        try:
            success = stream_manager.stop_stream()
            return jsonify({'success': success})
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/stream-status')
    def stream_status():
        try:
            is_running = stream_manager.is_playing and stream_manager.player.is_playing()
            current_stream = stream_manager.current_stream if is_running else None
            
            logger.info(f"Stream status: playing={is_running}, stream={current_stream}")
            
            return jsonify({
                'is_running': bool(is_running),
                'current_stream': current_stream
            })
        except Exception as e:
            logger.error(f"Error checking stream status: {e}")
            return jsonify({
                'is_running': False,
                'current_stream': None
            })

    @app.route('/api/stream/volume', methods=['POST'])
    def set_volume():
        try:
            data = request.get_json()
            volume = data.get('volume')
            if volume is None:
                return jsonify({'error': 'volume required'}), 400
            stream_manager.set_volume(volume)
            return jsonify({'success': True, 'volume': volume})
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/stream-select')
    def stream_select():
        try:
            channel = request.args.get('channel')
            if not channel:
                return "Channel parameter is required", 400

            # Load radio stations from config.toml
            with open('config.toml', 'r', encoding='utf-8') as f:
                config = toml.load(f)
                stations = config.get('links', [])
            
            # Get default streams (first three entries)
            default_streams = stations[:3]
            # Get remaining stations for selection
            spare_links = stations[3:]
            
            return render_template('stream_select.html', 
                                 spare_links=spare_links,
                                 channel=channel,
                                 default_streams=default_streams)
        except Exception as e:
            logger.error(f"Error in stream_select: {e}")
            return str(e), 500

    @app.route('/update-stream', methods=['POST'])
    def update_stream():
        try:
            channel = request.form.get('channel')
            selected_link = request.form.get('selected_link')
            
            logger.info(f"Updating stream for channel {channel} with URL {selected_link}")
            logger.info(f"Current streams before update: {stream_manager.streams}")
            
            if not channel or not selected_link:
                return jsonify({'success': False, 'error': 'Missing parameters'}), 400
                
            # Load current config
            with open('config.toml', 'r', encoding='utf-8') as f:
                config = toml.load(f)
                stations = config.get('links', [])
            
            # Find the selected station
            selected_station = None
            for station in stations:
                if station['url'] == selected_link:
                    selected_station = station
                    break
                
            if selected_station:
                # Move selected station to the appropriate position (0, 1, or 2)
                channel_index = int(channel[-1]) - 1  # Convert link1 to 0, link2 to 1, etc.
                if 0 <= channel_index < 3:
                    # Remove station from current position if it exists
                    stations.remove(selected_station)
                    # Insert at new position
                    stations.insert(channel_index, selected_station)
                    
                    # Save updated config
                    with open('config.toml', 'w', encoding='utf-8') as f:
                        toml.dump({'links': stations}, f)
                    
                    # Update the stream manager with the new URL
                    stream_manager.streams[channel] = selected_station['url']
                    logger.info(f"Updated streams in manager: {stream_manager.streams}")
                    
                    # Reload the stream if it was currently playing
                    if stream_manager.current_stream == channel:
                        logger.info(f"Reloading current stream for channel {channel}")
                        stream_manager.play_stream(channel)
                    
                    return jsonify({'success': True})
            
            return jsonify({'success': False, 'error': 'Station not found'})
        except Exception as e:
            logger.error(f"Error updating stream: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/wifi/reboot', methods=['POST'])
    def reboot_device():
        try:
            logger.info("Initiating device reboot...")
            response = jsonify({'status': 'success', 'message': 'Rebooting device'})
            
            def delayed_reboot():
                time.sleep(2)
                subprocess.run(['sudo', 'shutdown', '-r', 'now'])
                
            threading.Thread(target=delayed_reboot).start()
            return response
            
        except Exception as e:
            logger.error(f"Error during reboot: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/ping')
    def ping():
        return jsonify({'status': 'ok'})

    @app.route('/connect', methods=['POST'])
    def connect_to_network():
        try:
            ssid = request.form.get('ssid')
            password = request.form.get('password')
            
            if not ssid:
                return jsonify({'status': 'error', 'message': 'SSID is required'}), 400
                
            logger.info(f"Attempting to connect to network: {ssid}")
            
            # If it's the Salt 5GHz network, use the preconfigured connection
            if ssid == 'Salt_5GHz_D8261F':
                result = subprocess.run(
                    ['sudo', 'nmcli', 'connection', 'up', 'preconfigured'],
                    capture_output=True,
                    text=True
                )
            else:
                # For other networks, connect directly
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid] + 
                    (['password', password] if password else []),
                    capture_output=True,
                    text=True
                )

            if result.returncode == 0:
                logger.info(f"Successfully connected to {ssid}")
                return jsonify({'status': 'success'})
            else:
                error_msg = result.stderr.strip() or "Connection failed"
                logger.error(f"Failed to connect to {ssid}: {error_msg}")
                return jsonify({
                    'status': 'error',
                    'message': error_msg
                }), 400
                
        except Exception as e:
            logger.error(f"Error in connect_to_network: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/forget_network', methods=['POST'])
    def forget_network_route():
        try:
            data = request.get_json()
            if not data or 'ssid' not in data:
                return jsonify({'status': 'error', 'message': 'SSID is required'}), 400
                
            ssid = data['ssid']
            logger.info(f"Attempting to forget network: {ssid}")
            
            # First check if we're currently connected to this network
            current_connection = subprocess.run(
                ['nmcli', '-t', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show', '--active'],
                capture_output=True,
                text=True
            )
            
            is_current = any(ssid in line and 'wifi' in line for line in current_connection.stdout.split('\n'))
            
            # If it's the current connection, disconnect first
            if is_current:
                logger.info(f"Disconnecting from current network: {ssid}")
                subprocess.run(['sudo', 'nmcli', 'device', 'disconnect', 'wlan0'],
                             capture_output=True)
                time.sleep(1)
            
            # Delete the connection
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'delete', ssid],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully forgot network: {ssid}")
                return jsonify({'status': 'success'})
            else:
                error_msg = result.stderr.strip() or "Unknown error occurred"
                logger.error(f"Failed to forget network {ssid}: {error_msg}")
                return jsonify({'status': 'error', 'message': error_msg}), 400
                
        except Exception as e:
            logger.error(f"Error in forget_network route: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return app

def restart_pi():
    """Restart the Raspberry Pi"""
    try:
        logger.info("Restarting Raspberry Pi...")
        subprocess.run(['sudo', 'reboot'])
    except Exception as e:
        logger.error(f"Error restarting Pi: {e}")

def check_wifi():
    """Check if WiFi is connected"""
    try:
        result = subprocess.run(['iwgetid'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking WiFi: {e}")
        return False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if 'radio' in globals():
        radio.cleanup()
    sys.exit(0)

def get_wifi_networks():
    """Get list of available WiFi networks"""
    try:
        # Get list of available networks using nmcli
        result = subprocess.run(
            ['sudo', 'nmcli', '-t', '-f', 'SSID', 'device', 'wifi', 'list', '--rescan', 'yes'],
            capture_output=True, text=True
        )
        
        # Split output into lines and remove empty strings
        networks = [line for line in result.stdout.strip().split('\n') if line]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_networks = []
        for network in networks:
            if network not in seen and network:  # Skip empty SSIDs
                seen.add(network)
                unique_networks.append(network)
        
        logger.info(f"Found networks: {unique_networks}")
        return unique_networks
        
    except Exception as e:
        logger.error(f"Error getting networks: {e}")
        return []

def get_saved_networks():
    try:
        # Get all saved connections including preconfigured
        result = subprocess.run(
            ['sudo', 'nmcli', '--fields', 'NAME,TYPE', 'connection', 'show'],
            capture_output=True,
            text=True
        )
        
        saved_networks = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if 'wifi' in line.lower():  # Only get WiFi connections
                    name = line.split()[0]  # Get the network name
                    if name != 'Hotspot':  # Exclude the AP mode hotspot
                        # Replace 'preconfigured' with actual SSID if it's the preconfigured network
                        if name == 'preconfigured':
                            saved_networks.append('Salt_5GHz_D8261F')
                        else:
                            saved_networks.append(name)
        
        logger.info(f"Found saved networks: {saved_networks}")
        return saved_networks
        
    except Exception as e:
        logger.error(f"Error getting saved networks: {str(e)}")
        return []

def get_network_status():
    try:
        # Get current connection
        current = subprocess.run(
            ['nmcli', '-t', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show', '--active'],
            capture_output=True,
            text=True
        )
        
        # Get saved networks
        saved_networks = get_saved_networks()
        
        # Get all available networks
        available = get_available_networks()
        
        current_network = None
        if current.returncode == 0:
            for line in current.stdout.strip().split('\n'):
                if 'wifi' in line and 'wlan0' in line:
                    conn_name = line.split(':')[0]
                    if conn_name == 'preconfigured':
                        current_network = 'Salt_5GHz_D8261F'
                    else:
                        current_network = conn_name
        
        # Mark networks as saved and/or current
        for network in available:
            network['saved'] = network['ssid'] in saved_networks
            network['current'] = network['ssid'] == current_network
        
        logger.info(f"Network status: {available}")
        return available
        
    except Exception as e:
        logger.error(f"Error getting network status: {str(e)}")
        return []

def setup_ap_mode():
    try:
        # Get hostname to use as SSID
        hostname = subprocess.check_output(['hostname']).decode('utf-8').strip()
        
        # Create hostapd config
        hostapd_config = f"""
interface=wlan0
driver=nl80211
ssid={hostname}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=Radio@1234
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        
        with open('/etc/hostapd/hostapd.conf', 'w') as f:
            f.write(hostapd_config)
            
        # Update default configuration
        with open('/etc/default/hostapd', 'w') as f:
            f.write('DAEMON_CONF="/etc/hostapd/hostapd.conf"')
            
        logger.info("AP mode configuration updated")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up AP mode: {str(e)}")
        return False

def get_available_networks():
    try:
        # Get hostname to exclude from network list
        hostname = subprocess.check_output(['hostname']).decode('utf-8').strip()
        
        # Get all networks
        result = subprocess.run(
            ['sudo', 'nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'device', 'wifi', 'list'],
            capture_output=True,
            text=True
        )
        
        networks = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    ssid, signal, security = line.split(':')
                    # Skip empty SSIDs and our own AP
                    if ssid and ssid != hostname:
                        networks.append({
                            'ssid': ssid,
                            'signal': signal,
                            'security': security
                        })
        
        return networks
        
    except Exception as e:
        logger.error(f"Error getting networks: {str(e)}")
        return []

def check_and_setup_network():
    try:
        # Check for saved networks
        saved_networks = get_saved_networks()
        
        if not saved_networks:
            logger.info("No saved networks found, switching to AP mode")
            return switch_to_ap_mode()
            
        # Try to connect to saved networks
        for network in saved_networks:
            logger.info(f"Attempting to connect to {network}")
            
            result = subprocess.run(
                ["sudo", "nmcli", "connection", "up", network],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully connected to {network}")
                return True
            
            logger.warning(f"Failed to connect to {network}")
        
        # If no connections successful, switch to AP mode
        logger.info("Could not connect to any saved networks, switching to AP mode")
        return switch_to_ap_mode()
        
    except Exception as e:
        logger.error(f"Error in network setup: {str(e)}")
        return False

def switch_to_ap_mode():
    try:
        logger.info("Starting AP mode setup...")
        
        # Stop potentially interfering services
        subprocess.run(['sudo', 'systemctl', 'stop', 'NetworkManager'])
        subprocess.run(['sudo', 'systemctl', 'stop', 'wpa_supplicant'])
        
        # Ensure wireless interface is up and not blocked
        subprocess.run(['sudo', 'rfkill', 'unblock', 'wifi'])
        subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'])
        
        # Setup AP configuration
        if not setup_ap_mode():
            logger.error("Failed to setup AP mode configuration")
            return False
            
        # Configure network interface before starting services
        subprocess.run(['sudo', 'ifconfig', 'wlan0', 'down'])
        subprocess.run(['sudo', 'ifconfig', 'wlan0', '192.168.4.1', 'netmask', '255.255.255.0'])
        subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'])
        
        # Start services in correct order
        subprocess.run(['sudo', 'systemctl', 'restart', 'dnsmasq'])
        time.sleep(2)  # Give dnsmasq time to start
        subprocess.run(['sudo', 'systemctl', 'restart', 'hostapd'])
        
        logger.info("AP mode activated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error switching to AP mode: {str(e)}")
        return False

def connect_to_network(ssid, password=None):
    try:
        logger.info(f"Attempting to connect to network: {ssid}")
        
        # First, bring down any active WiFi connection
        subprocess.run(['sudo', 'nmcli', 'device', 'disconnect', 'wlan0'],
                      capture_output=True)
        time.sleep(1)
        
        # If it's the Salt 5GHz network, use the preconfigured connection
        if ssid == 'Salt_5GHz_D8261F':
            logger.info("Using preconfigured connection")
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'up', 'preconfigured'],
                capture_output=True,
                text=True
            )
        else:
            # For other networks, use the connection by name
            result = subprocess.run(
                ['sudo', 'nmcli', 'connection', 'up', ssid],
                capture_output=True,
                text=True
            )

        if result.returncode == 0:
            logger.info(f"Successfully connected to {ssid}")
            return {'status': 'success'}
        else:
            error_msg = result.stderr.strip() or "Connection failed"
            logger.error(f"Failed to connect to {ssid}: {error_msg}")
            return {'status': 'error', 'message': error_msg}
            
    except Exception as e:
        logger.error(f"Error in connect_to_network: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def should_enable_ap_mode():
    try:
        # Check if we're already in AP mode
        if is_in_ap_mode():
            return False
            
        # Check for any active WiFi connection
        wifi_status = subprocess.run(['iwgetid'], capture_output=True, text=True)
        if wifi_status.returncode == 0 and wifi_status.stdout.strip():
            return False
            
        # Check saved networks
        saved_networks = get_saved_networks()
        if not saved_networks:
            logger.info("No saved networks found")
            return True
            
        # Try scanning for saved networks
        available = get_available_networks()
        available_ssids = [net['ssid'] for net in available]
        
        for saved in saved_networks:
            if saved in available_ssids:
                return False
                
        logger.info("No saved networks in range")
        return True
        
    except Exception as e:
        logger.error(f"Error checking AP mode status: {str(e)}")
        return True  # Default to AP mode on error

def disable_ap_mode():
    try:
        logger.info("Disabling AP mode...")
        
        # Stop AP services
        subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'])
        subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'])
        
        # Reset interface
        subprocess.run(['sudo', 'ifconfig', 'wlan0', 'down'])
        subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'])
        
        # Restart network services
        subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'])
        subprocess.run(['sudo', 'systemctl', 'restart', 'NetworkManager'])
        
        logger.info("AP mode disabled")
        return True
        
    except Exception as e:
        logger.error(f"Error disabling AP mode: {str(e)}")
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

        # Check WiFi
        if not check_wifi():
            logger.info("Starting Wi-Fi hotspot...")
            radio.wifi_manager = WiFiManager(radio.app)
            radio.wifi_manager.start_hotspot()
            radio.led.blink(on_time=0.5, off_time=0.5)
        else:
            radio.led.blink(on_time=3, off_time=3)

        # Start Flask in a separate thread
        flask_thread = threading.Thread(
            target=lambda: radio.app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        )
        flask_thread.daemon = True
        flask_thread.start()

        # Keep the main thread running
        while True:
            time.sleep(1)

    except Exception as e:
        logger.error(f"Main error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

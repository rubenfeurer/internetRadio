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
        # Add VLC parameters for better buffering
        self.instance = vlc.Instance('--no-xlib',
                                   '--aout=alsa',
                                   '--alsa-audio-device=hw:2,0',
                                   '--file-caching=5000',
                                   '--network-caching=5000',
                                   '--live-caching=5000',
                                   '--sout-mux-caching=5000',
                                   '--clock-jitter=0',
                                   '--sout-rtp-proto=udp')
        self.player = self.instance.media_player_new()
        self.volume = initial_volume
        self.current_key = None
        self.streams = {
            'link1': "http://stream.srg-ssr.ch/m/rsj/mp3_128",
            'link2': "http://stream.srg-ssr.ch/m/rsj/mp3_128",
            'link3': "http://stream.srg-ssr.ch/m/rsj/mp3_128"
        }
        self.player.audio_set_volume(self.volume)
        logger.info("StreamManager initialized")

    def play_stream(self, stream_key):
        try:
            logger.info(f"Playing stream: {stream_key}")
            if stream_key in self.streams:
                if self.current_key == stream_key and self.player.is_playing():
                    logger.info("Stopping current stream")
                    self.stop_stream()
                    return True
                
                self.current_key = stream_key
                stream_url = self.streams[stream_key]
                media = self.instance.media_new(stream_url)
                # Add media options for better buffering
                media.add_option('network-caching=1500')
                media.add_option('file-caching=1500')
                media.add_option('live-caching=1500')
                self.player.set_media(media)
                self.player.play()
                return True
            return False
        except Exception as e:
            logger.error(f"Error playing stream: {e}")
            return False

    def stop_stream(self):
        try:
            logger.info("Stopping stream")
            self.player.stop()
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

def create_app(stream_manager):
    app = Flask(__name__, 
                static_folder='static',
                static_url_path='/static')
    
    @app.route('/')
    def index():
        try:
            return render_template('index.html', 
                                 link1=stream_manager.streams['link1'],
                                 link2=stream_manager.streams['link2'],
                                 link3=stream_manager.streams['link3'])
        except Exception as e:
            logger.error(f"Error in index route: {e}")
            return str(e), 500

    @app.route('/wifi-settings', methods=['GET', 'POST'])
    def wifi_settings():
        try:
            if request.method == 'POST':
                ssid = request.form.get('ssid')
                password = request.form.get('password')
                # Add your WiFi connection logic here
                return jsonify({'status': 'success'})
            return render_template('wifi_settings.html')
        except Exception as e:
            logger.error(f"Error in wifi_settings: {e}")
            return str(e), 500

    @app.route('/wifi-scan')
    def wifi_scan():
        try:
            # Get list of available networks
            result = subprocess.run(['iwlist', 'wlan0', 'scan'], capture_output=True, text=True)
            networks = []
            for line in result.stdout.split('\n'):
                if 'ESSID:' in line:
                    ssid = line.split('ESSID:')[1].strip('"')
                    if ssid and ssid != 'InternetRadio':  # Don't show our own AP
                        networks.append(ssid)
            return jsonify({'status': 'complete', 'networks': networks})
        except Exception as e:
            logger.error(f"Error scanning networks: {e}")
            return jsonify({'status': 'error', 'error': str(e)})

    # Add WiFi status route
    @app.route('/get_wifi_ssid')
    def get_wifi_ssid():
        try:
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            ssid = result.stdout.strip() if result.returncode == 0 else None
            return jsonify({'ssid': ssid})
        except Exception as e:
            return jsonify({'error': str(e)})

    # Add internet check route
    @app.route('/check_internet_connection')
    def check_internet_connection():
        try:
            subprocess.check_output(['ping', '-c', '1', '8.8.8.8'])
            return jsonify({'connected': True})
        except:
            return jsonify({'connected': False})

    @app.route('/api/stream/play', methods=['POST'])
    def play_stream():
        try:
            data = request.get_json()
            stream_key = data.get('stream_key')
            if not stream_key:
                return jsonify({'error': 'stream_key required'}), 400
            success = stream_manager.play_stream(stream_key)
            return jsonify({'success': success})
        except Exception as e:
            logger.error(f"Error playing stream: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/stream/stop', methods=['POST'])
    def stop_stream():
        try:
            success = stream_manager.stop_stream()
            return jsonify({'success': success})
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return jsonify({'error': str(e)}), 500

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
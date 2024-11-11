#!/usr/bin/env -S python

import subprocess
import threading
import time
import os
import logging

from gpiozero import Button, RotaryEncoder, LED
from signal import pause

from stream_manager import StreamManager
from app import create_app
from sounds import SoundManager
from wifi_manager import WiFiManager

from flask import Flask, Blueprint, request, jsonify

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/home/radio/internetRadio/logs/app.log'
)
logger = logging.getLogger(__name__)

# Add these constants at the top of the file, after imports
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

def check_wifi():
    """Check if WiFi is connected"""
    try:
        result = subprocess.run(['iwgetid'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking WiFi: {e}")
        return False

def create_app():
    app = Flask(__name__)
    
    # Initialize StreamManager only once (it's now a singleton)
    stream_manager = StreamManager(50)
    
    # Initialize other components
    wifi_manager = WiFiManager(app)
    
    # Register stream endpoints
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

    @app.route('/api/stream/status', methods=['GET'])
    def get_stream_status():
        try:
            return jsonify({
                'is_playing': stream_manager.player.is_playing(),
                'current_stream': stream_manager.current_key,
                'volume': stream_manager.volume
            })
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({'error': str(e)}), 500

    return app, stream_manager

def main():
    try:
        # Create the application
        app, stream_manager = create_app()
        
        # Initialize sound manager and play boot sound
        sound_manager = SoundManager(SOUND_FOLDER)
        sound_manager.play_sound("boot.wav")

        # Initialize LED with correct pin
        led = LED(LED_PIN)
        led.on()

        # Initialize encoder button with correct pin
        buttonEn = Button(ENCODER_SW, pull_up=True, bounce_time=0.2, hold_time=2)
        buttonEn.when_pressed = lambda: logger.info("Encoder Pressed")
        buttonEn.when_held = lambda: restart_pi()

        # Check WiFi and start hotspot if needed
        if not check_wifi():
            logger.info("Starting Wi-Fi hotspot...")
            wifi_manager.start_hotspot()
            led.blink(on_time=0.5, off_time=0.5)  # Fast blink in AP mode
        else:
            led.blink(on_time=3, off_time=3)  # Slow blink when connected

        # Set up radio buttons with correct pins
        button1 = Button(BUTTON_PINS['link1'], pull_up=True, bounce_time=0.2)
        button2 = Button(BUTTON_PINS['link2'], pull_up=True, bounce_time=0.2)
        button3 = Button(BUTTON_PINS['link3'], pull_up=True, bounce_time=0.2)

        button1.when_pressed = lambda: button_handler('link1')
        button2.when_pressed = lambda: button_handler('link2')
        button3.when_pressed = lambda: button_handler('link3')

        # Set up rotary encoder with correct pins
        encoder = RotaryEncoder(
            ENCODER_DT,   # Data pin (GPIO9)
            ENCODER_CLK,  # Clock pin (GPIO11)
            bounce_time=0.1,
            max_steps=1,
            wrap=False,
            threshold_steps=(0,100)
        )
        encoder.when_rotated_clockwise = lambda rotation: volume_up(rotation)
        encoder.when_rotated_counter_clockwise = lambda rotation: volume_down(rotation)

        # Start Flask app
        app.run(host='0.0.0.0', port=5000, debug=False)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

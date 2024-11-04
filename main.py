#!/usr/bin/env -S python

import subprocess
import threading
import time
import os

from gpiozero import Button, RotaryEncoder, LED
from signal import pause

from stream_manager import StreamManager
from app import create_app
from sounds import SoundManager

print("Starting Internet Radio...")

volume = 50
sound_folder = "/home/radio/internetRadio/sounds"
stream_manager = None
sound_manager = None

def run_flask_app():
    print("Starting Flask app...")
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=False)

print("Initializing components...")

# Initialize sound manager
sound_manager = SoundManager(sound_folder)
print(f"Sound manager initialized with folder: {sound_folder}")

# Initialize LED
LED_PIN = 24
led = LED(LED_PIN)
led.on()
print("LED initialized")

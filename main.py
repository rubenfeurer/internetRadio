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
from wifi_manager import WiFiManager

from flask import Flask

app = Flask(__name__)

# Initialize managers
wifi_manager = WiFiManager(app)

volume = 50
sound_folder = "/home/radio/internetRadio/sounds"
stream_manager = None
sound_manager = None

def run_flask_app():
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)

def button_handler(stream_key):
    # print(f"Button pressed for {stream_key}")
    if stream_manager.current_key == stream_key:
        stream_manager.stop_stream()
    else:
        stream_manager.play_stream(stream_key)

def restart_pi():
    print("Reboot Pi")
    sound_manager.play_sound("boot.wav")  # Add this line
    time.sleep(2)  # Add a small delay to ensure the sound plays
    os.system("sudo reboot")

def volume_up(encoder):
    global volume, stream_manager
    if stream_manager:
        volume = min(100, volume + 5)  # Increase by 5, max 100
        print(f"Volume Up: {volume}")
        stream_manager.set_volume(volume)

def volume_down(encoder):
    global volume, stream_manager
    if stream_manager:
        volume = max(0, volume - 5)  # Decrease by 5, min 0
        print(f"Volume Down: {volume}")
        stream_manager.set_volume(volume)

def check_wifi():
    try:
        # Check if connected to a Wi-Fi network (router)
        result = subprocess.run(['iwgetid'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:  # Return code 0 means connected to a Wi-Fi network
            network_name = result.stdout.decode().strip()
            print(f"Connected to network: {network_name}")
            return True
        else:
            print("Not connected to any Wi-Fi network.")
            return False
    except Exception as e:
        print(f"Error checking Wi-Fi: {e}")
        return False

def get_ip_address(interface='wlan0'):
    try:
        result = subprocess.check_output(['ip', 'addr', 'show', interface]).decode()
        for line in result.splitlines():
            if 'inet ' in line:
                ip_address = line.strip().split()[1].split('/')[0]
                return ip_address
    except (subprocess.CalledProcessError, IndexError):
        return None

def start_hotspot():
    try:
        print("Starting Wi-Fi hotspot...")
        subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'hotspot', 'ssid', 'Radio', 'password', 'Radio@1234', 'ifname', 'wlan0'], check=True)
        ip_address = get_ip_address('wlan0')
        if ip_address:
            print(f"Hotspot started successfully. Visit http://{ip_address}:5000 to configure Wi-Fi settings.")
        else:
            print("Hotspot started, but IP address could not be determined.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting hotspot: {e}") 

def fade_volume_down():
    # Fade out from current volume to 0%
    for vol in range(100, -1, -10):
        subprocess.run(['amixer', 'set', 'PCM', f'{vol}%'], capture_output=True)
        time.sleep(0.05)

def fade_volume_up():
    # Fade in from 0% to 100%
    subprocess.run(['amixer', 'set', 'PCM', '0%'], capture_output=True)
    time.sleep(0.1)  # Small delay before starting playback
    for vol in range(0, 101, 10):
        subprocess.run(['amixer', 'set', 'PCM', f'{vol}%'], capture_output=True)
        time.sleep(0.05)

# Use before shutdown/reboot
def safe_shutdown():
    fade_volume_down()
    time.sleep(0.2)  # Small delay before actual shutdown
    subprocess.run(['sudo', 'shutdown', '-h', 'now'])

# Use before reboot
def safe_reboot():
    fade_volume_down()
    time.sleep(0.2)  # Small delay before actual reboot
    subprocess.run(['sudo', 'reboot'])

def shutdown_sequence():
    # Set volume to 0 before shutdown
    subprocess.run(['amixer', 'set', 'PCM', '0%'], capture_output=True)
    time.sleep(0.2)  # Wait for audio to settle
    subprocess.run(['sudo', 'shutdown', '-h', 'now'])

def startup_sequence():
    # Start with volume at 0
    subprocess.run(['amixer', 'set', 'PCM', '0%'], capture_output=True)
    time.sleep(0.2)  # Wait for system to settle
    # Then gradually increase
    for vol in range(0, 101, 10):
        subprocess.run(['amixer', 'set', 'PCM', f'{vol}%'], capture_output=True)
        time.sleep(0.05)

@app.route('/wifi-scan')
def wifi_scan():
    return wifi_manager.handle_wifi_scan()

@app.route('/wifi-setup')
def wifi_setup():
    return wifi_manager.handle_wifi_setup()

if __name__ == "__main__":
    sound_manager = SoundManager(sound_folder)
    sound_manager.play_sound("boot.wav")

    LED_PIN = 24
    ENCODER_BUTTON = 10  # Pin 19 (GPIO10)

    led = LED(LED_PIN)
    led.on()
    
    buttonEn = Button(ENCODER_BUTTON, pull_up=True, bounce_time=0.2, hold_time=2)
    buttonEn.when_pressed = lambda: print("Encoder Pressed")
    buttonEn.when_held = lambda: restart_pi()
    
    if not check_wifi():
        print("Starting Wi-Fi hotspot...")
        start_hotspot()  

    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    while not check_wifi():
        led.blink(on_time=1, off_time=1)
        print("Waiting for Wi-Fi connection...")
        time.sleep(5) 

    led.blink(on_time=3, off_time=3)
    sound_manager.play_sound("wifi.wav")
    stream_manager = StreamManager(volume)
    print (volume)

    BUTTON1_PIN = 17  # Pin 11 (GPIO17) with GND on Pin 9
    BUTTON2_PIN = 16  # Pin 36 (GPIO16) with GND on Pin 34
    BUTTON3_PIN = 26  # Pin 37 (GPIO26) with GND on Pin 39

    button1 = Button(BUTTON1_PIN, pull_up=True, bounce_time=0.2)
    button2 = Button(BUTTON2_PIN, pull_up=True, bounce_time=0.2)
    button3 = Button(BUTTON3_PIN, pull_up=True, bounce_time=0.2)

    button1.when_pressed = lambda: button_handler('link1')
    button2.when_pressed = lambda: button_handler('link2')
    button3.when_pressed = lambda: button_handler('link3')

    DT_PIN = 9    # Changed from 5 to 9 (GPIO9)
    CLK_PIN = 11  # Changed from 6 to 11 (GPIO11)

    encoder = RotaryEncoder(
        DT_PIN, 
        CLK_PIN, 
        bounce_time=0.1, 
        max_steps=1, 
        wrap=False, 
        threshold_steps=(0,100)
    )
    encoder.when_rotated_clockwise = lambda rotation: volume_up(rotation)
    encoder.when_rotated_counter_clockwise = lambda rotation: volume_down(rotation)
    
    played = False

    while True:
        wifi_status = check_wifi()
        if not wifi_status and not played:
            print("WiFi connection lost")
            sound_manager.play_sound("noWifi.wav")
            led.blink(on_time=0.5, off_time=0.5)
            played = True
        elif wifi_status and played:
            sound_manager.play_sound("wifi.wav")
            led.blink(on_time=3, off_time=3)
            played = False
        
        time.sleep(30)

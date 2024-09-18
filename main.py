import subprocess
import threading
import time

from gpiozero import Button, RotaryEncoder
from signal import pause

from stream_manager import StreamManager
from app import create_app

volume = 50
stream_manager = None

def run_flask_app():
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=False)

def button_handler(stream_key):
    # print(f"Button pressed for {stream_key}")
    if stream_manager.current_key == stream_key:
        stream_manager.stop_stream()
    else:
        stream_manager.play_stream(stream_key)

def volume_up(encoder):
    global volume
    volume = volume + 1
    volume = max(0, min(volume, 100))
    stream_manager.set_volume(volume)

def volume_down(encoder):
    global volume
    volume = volume - 1
    volume = max(0, min(volume, 100))
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

def start_hotspot():
    try:
        # Set up the hotspot using nmcli
        print("Starting Wi-Fi hotspot...")
        subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'hotspot', 'ssid', 'radioDevice', 'password', 'Radio@1234', 'ifname', 'wlan0'], check=True)
        print("Hotspot started successfully. Visit http://192.168.50.1:8080 to configure Wi-Fi settings.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting hotspot: {e}")

def initialize_radio_features():
    global stream_manager
    stream_manager = StreamManager(volume)
    print(volume)

    BUTTON1_PIN = 17
    BUTTON2_PIN = 27
    BUTTON3_PIN = 22

    button1 = Button(BUTTON1_PIN, pull_up=True, bounce_time=0.2)
    button2 = Button(BUTTON2_PIN, pull_up=True, bounce_time=0.2)
    button3 = Button(BUTTON3_PIN, pull_up=True, bounce_time=0.2)

    button1.when_pressed = lambda: button_handler('link1')
    button2.when_pressed = lambda: button_handler('link2')
    button3.when_pressed = lambda: button_handler('link3')

    DT_PIN = 5
    CLK_PIN = 6

    encoder = RotaryEncoder(DT_PIN, CLK_PIN, bounce_time=0.1, max_steps=1, wrap=False, threshold_steps=(0, 100))
    encoder.when_rotated_clockwise = lambda rotation: volume_down(rotation)
    encoder.when_rotated_counter_clockwise = lambda rotation: volume_up(rotation)

if __name__ == "__main__":
    if not check_wifi():
        print("Starting Wi-Fi hotspot...")
        start_hotspot()  

    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    while not check_wifi():
        print("Waiting for Wi-Fi connection...")
        time.sleep(5) 

    stream_manager = StreamManager(volume)
    print (volume)

    BUTTON1_PIN = 17  # GPIO pin for Button 1
    BUTTON2_PIN = 27  # GPIO pin for Button 2
    BUTTON3_PIN = 22  # GPIO pin for Button 3

    button1 = Button(BUTTON1_PIN, pull_up=True, bounce_time=0.2)
    button2 = Button(BUTTON2_PIN, pull_up=True, bounce_time=0.2)
    button3 = Button(BUTTON3_PIN, pull_up=True, bounce_time=0.2)

    button1.when_pressed = lambda: button_handler('link1')
    button2.when_pressed = lambda: button_handler('link2')
    button3.when_pressed = lambda: button_handler('link3')

    DT_PIN = 5  # GPIO pin for DT
    CLK_PIN = 6  # GPIO pin for CLK

    encoder = RotaryEncoder(DT_PIN, CLK_PIN, bounce_time=0.1, max_steps=1, wrap=False, threshold_steps=(0,100))
    encoder.when_rotated_clockwise = lambda rotation: volume_down(rotation)
    encoder.when_rotated_counter_clockwise = lambda rotation: volume_up(rotation)


    pause()

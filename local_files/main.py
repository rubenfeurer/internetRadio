import subprocess
import threading
import time
import os

from gpiozero import Button, RotaryEncoder, LED
from signal import pause

from stream_manager import StreamManager
from app import create_app
from sounds import SoundManager

volume = 50
sound_folder = "/home/pi/pi_radio/sounds"
stream_manager = None
sound_manager = None

def run_flask_app():
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=False)

def button_handler(stream_key):
    # print(f"Button pressed for {stream_key}")
    if stream_manager.current_key == stream_key:
        stream_manager.stop_stream()
    else:
        stream_manager.play_stream(stream_key)

def restart_pi():
    print("Reboot Pi")
    os.system("sudo reboot")

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

if __name__ == "__main__":
    sound_manager = SoundManager(sound_folder)
    sound_manager.play_sound("boot.wav")

    LED_PIN = 24
    led = LED(LED_PIN)
    led.on()
    
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

    BUTTON1_PIN = 17  # GPIO pin for Button 1
    BUTTON2_PIN = 27  # GPIO pin for Button 2
    BUTTON3_PIN = 22  # GPIO pin for Button 3
    ENCODER_BUTTON = 23 # GPIO pin for Encoder Button

    button1 = Button(BUTTON1_PIN, pull_up=True, bounce_time=0.2)
    button2 = Button(BUTTON2_PIN, pull_up=True, bounce_time=0.2)
    button3 = Button(BUTTON3_PIN, pull_up=True, bounce_time=0.2)
    buttonEn = Button(ENCODER_BUTTON, pull_up=True, bounce_time=0.2, hold_time=2)

    button1.when_pressed = lambda: button_handler('link1')
    button2.when_pressed = lambda: button_handler('link2')
    button3.when_pressed = lambda: button_handler('link3')
    buttonEn.when_pressed = lambda: print("Encoder Pressed")
    buttonEn.when_held = lambda: restart_pi()

    DT_PIN = 5  # GPIO pin for DT
    CLK_PIN = 6  # GPIO pin for CLK

    encoder = RotaryEncoder(DT_PIN, CLK_PIN, bounce_time=0.1, max_steps=1, wrap=False, threshold_steps=(0,100))
    encoder.when_rotated_clockwise = lambda rotation: volume_down(rotation)
    encoder.when_rotated_counter_clockwise = lambda rotation: volume_up(rotation)
    
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
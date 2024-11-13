#!/usr/bin/env python3

import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio.audio_manager import AudioManager

def test_sounds():
    audio = AudioManager()
    if not audio.initialize():
        print("Failed to initialize AudioManager")
        return
    
    sound_files = ['boot.wav', 'click.wav', 'error.wav', 'noWifi.wav', 'shutdown.wav', 'wifi.wav']
    
    for sound in sound_files:
        print(f"\nTesting {sound}...")
        if audio.play_sound(sound):
            print(f"Playing {sound}")
            time.sleep(2)  # Wait for sound to play
        else:
            print(f"Failed to play {sound}")
    
    audio.cleanup()

if __name__ == "__main__":
    test_sounds() 
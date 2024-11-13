#!/usr/bin/env python3

import os
import sys
import time
import vlc

def play_sound(sound_file: str) -> None:
    """Play a sound file with error handling"""
    try:
        # Create a new instance for each sound
        instance = vlc.Instance('--no-xlib --quiet')
        player = instance.media_player_new()
        media = instance.media_new(sound_file)
        player.set_media(media)
        
        # Play and wait
        player.play()
        time.sleep(1)  # Wait for audio to start
        
        # Wait for playback to complete
        while player.is_playing():
            time.sleep(0.1)
            
        # Clean up
        player.stop()
        media.release()
        player.release()
        instance.release()
        
    except Exception as e:
        print(f"Error playing {sound_file}: {e}")
        sys.exit(1)

def main():
    """Test all sound files"""
    sound_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sounds')
    
    for sound_file in ['boot.wav', 'click.wav', 'error.wav', 'noWifi.wav', 'shutdown.wav', 'wifi.wav']:
        full_path = os.path.join(sound_dir, sound_file)
        if os.path.exists(full_path):
            print(f"\nTesting {sound_file}...")
            print(f"Playing {sound_file}")
            play_sound(full_path)
            time.sleep(0.5)  # Brief pause between sounds
        else:
            print(f"Warning: {sound_file} not found")

if __name__ == '__main__':
    main() 
import os
import vlc
import subprocess
import time

class SoundManager:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.player = vlc.MediaPlayer()

    def play_sound(self, sound_file, fade=False):
        """Play a sound file from the folder."""
        sound_path = os.path.join(self.folder_path, sound_file)
        if fade:
            # Start at 0 volume and fade in
            subprocess.run(['amixer', 'set', 'PCM', '0%'])
            subprocess.run(['aplay', sound_path])
            # Gradually increase volume
            for vol in range(0, 100, 10):
                subprocess.run(['amixer', 'set', 'PCM', f'{vol}%'])
                time.sleep(0.05)
        else:
            subprocess.run(['aplay', sound_path])

    def stop_sound(self):
        """Stop the currently playing sound."""
        self.player.stop()


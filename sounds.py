import os
import vlc

class SoundManager:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.player = vlc.MediaPlayer()

    def play_sound(self, sound_file):
        """Play a sound file from the folder."""
        sound_path = os.path.join(self.folder_path, sound_file)
        if os.path.isfile(sound_path):
            print(f"Playing sound: {sound_path}")
            media = vlc.Media(sound_path)
            self.player.set_media(media)
            self.player.play()
        else:
            print(f"Sound file not found: {sound_path}")

    def stop_sound(self):
        """Stop the currently playing sound."""
        self.player.stop()


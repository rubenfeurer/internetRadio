import vlc
import toml
import time
import threading

class StreamManager:
    def __init__(self, volume):
        self.current_stream = None
        self.config = toml.load('config.toml')
        self.current_key = None  # Track the current playing stream key
        self.volume = volume

        # Create an instance of the VLC player
        self.player = vlc.MediaPlayer()

    def play_stream(self, stream_key):
        """Play the radio stream associated with the given key."""
        stream_url = self.config.get(stream_key, '')
        if stream_url:
            print(f"Starting stream: {stream_url}")
            # Set the media to the player
            media = vlc.Media(stream_url)
            self.player.set_media(media)
            self.player.play()
            self.player.audio_set_volume(self.volume)
            self.current_key = stream_key

    def stop_stream(self):
        """Stop the currently playing stream."""
        if self.current_key:
            print(f"Stopping stream.")
            self.player.stop()
            self.current_key = None

    def set_volume(self, volume):
        """Set the volume of the player."""
        if self.current_key:
            # Ensure the volume is within VLC's acceptable range (0-100)
            volume = max(0, min(volume, 100))
            self.volume = volume
            print(f"Setting volume to: {self.volume}")
            self.player.audio_set_volume(self.volume)

    def play_stream_radio(self, stream_url):
        """Preview the radio stream """
        if stream_url:
            print(f"Starting stream: {stream_url}")
            # Set the media to the player
            media = vlc.Media(stream_url)
            self.player.set_media(media)
            self.player.play()
            self.player.audio_set_volume(self.volume)
            threading.Thread(target=self.stop_stream_after_delay, args=(15,)).start()

    def stop_stream_after_delay(self, delay):
        """Stop the stream after a specified delay."""
        time.sleep(delay)  # Wait for the specified delay
        self.player.stop()  # Stop the player
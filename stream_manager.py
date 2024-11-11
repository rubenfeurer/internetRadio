import vlc
import toml
import time
import threading
import os

class StreamManager:
    _instance = None
    
    def __new__(cls, volume=50):
        if cls._instance is None:
            print("Creating new StreamManager instance...")
            cls._instance = super(StreamManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, volume=50):
        if self._initialized:
            return
            
        try:
            print("Initializing StreamManager...")
            self.current_stream = None
            self.config_path = '/home/radio/internetRadio/config.toml'
            self.config = toml.load(self.config_path)
            self.current_key = None
            self.last_played_url = None
            self.volume = volume

            print("Creating VLC instance...")
            instance = vlc.Instance('--aout=alsa', '--alsa-audio-device=plughw:2,0')
            print("VLC instance created")
            
            print("Creating media player...")
            self.player = instance.media_player_new()
            print("Media player created")
            
            self._initialized = True
            print("StreamManager initialized successfully")
            
        except Exception as e:
            print(f"Error initializing StreamManager: {e}")

    def play_stream(self, stream_key):
        """Play the radio stream associated with the given key."""
        try:
            print(f"Loading config from: {self.config_path}")
            self.config = toml.load(self.config_path)
            
            print(f"Attempting to play stream_key: {stream_key}")
            
            # Handle different config formats
            if stream_key in self.config:
                stream_url = self.config[stream_key]
            else:
                # Try to find in links array
                for link in self.config.get('links', []):
                    if link.get('name') == stream_key:
                        stream_url = link.get('url')
                        break
                else:
                    print(f"Error: No URL found for key {stream_key}")
                    return False
            
            print(f"Starting stream: {stream_url}")
            
            # Stop any currently playing stream
            if self.player.is_playing():
                print("Stopping current stream")
                self.player.stop()
                
            # Create and set new media
            print("Creating new media")
            media = vlc.Media(stream_url)
            
            # Add error handling for media
            media.parse()
            if media.get_parsed_status() == vlc.MediaParsedStatus.failed:
                print(f"Failed to parse media for stream: {stream_key}")
                return False
            
            print("Setting media to player")
            self.player.set_media(media)
            
            print("Starting playback")
            result = self.player.play()
            
            if result == 0:  # VLC returns 0 on success
                print("Setting volume")
                self.player.audio_set_volume(self.volume)
                self.current_key = stream_key
                print(f"Stream started successfully: {stream_key}")
                return True
            else:
                print(f"Failed to start stream: {stream_key}")
                return False
            
        except Exception as e:
            print(f"Error in play_stream: {e}")
            return False

    def stop_stream(self):
        """Stop the current stream."""
        try:
            if self.player.is_playing():
                print("Stopping stream")
                self.player.stop()
                self.current_key = None
                return True
            return False
        except Exception as e:
            print(f"Error stopping stream: {e}")
            return False

    def set_volume(self, volume):
        """Set the volume of the player."""
        if self.current_key:
            # Ensure the volume is within VLC's acceptable range (0-100)
            volume = max(0, min(volume, 100))
            self.volume = volume
            print(f"Setting volume to: {self.volume}")
            self.player.audio_set_volume(self.volume)

    def play_stream_radio(self, stream_url):
        """Preview the radio stream."""
        if stream_url:
            if self.last_played_url == stream_url:
                self.player.stop() 
                self.last_played_url = None  
            else:
                if self.player.is_playing():
                    self.player.stop()  

                print(f"Starting new stream: {stream_url}")
                media = vlc.Media(stream_url)
                self.player.set_media(media)
                self.player.play()  
                self.player.audio_set_volume(self.volume)
                self.last_played_url = stream_url  

                threading.Thread(target=self.stop_stream_after_delay, args=(30,)).start()

    def stop_stream_after_delay(self, delay):
        """Stop the stream after a specified delay."""
        time.sleep(delay)  
        self.player.stop()  
        self.last_played_url = None  
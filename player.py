import vlc
import time

class RadioPlayer:
    _instance = None
    
    def __new__(cls):
        # Singleton pattern to ensure only one player instance exists
        if cls._instance is None:
            cls._instance = super(RadioPlayer, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        self.instance = vlc.Instance('--no-xlib')  # headless mode for Raspberry Pi
        self.player = self.instance.media_player_new()
        self.current_media = None
        self.current_url = None
        
    def play(self, stream_url):
        try:
            # Stop current stream if any
            if self.is_playing():
                self.stop()
            
            # Create and play new media
            self.current_url = stream_url
            media = self.instance.media_new(stream_url)
            self.player.set_media(media)
            self.current_media = media
            self.player.play()
            
            # Wait a moment to ensure playback starts
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"Error playing stream: {e}")
            return False
    
    def stop(self):
        try:
            self.player.stop()
            self.current_media = None
            self.current_url = None
            return True
        except Exception as e:
            print(f"Error stopping stream: {e}")
            return False
    
    def is_playing(self):
        return bool(self.player.is_playing())
    
    def get_current_stream(self):
        return self.current_url
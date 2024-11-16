import vlc
import time
import threading
import os
import signal
import logging
import requests
import subprocess
import math
import toml

logger = logging.getLogger(__name__)

class RadioPlayer:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RadioPlayer, cls).__new__(cls)
            cls._instance.current_status = {
                "state": "stopped",
                "current_station": None,
                "volume": 50
            }
            cls._instance.current_media = None
            cls._instance.current_url = None
            cls._instance.initialize()
        return cls._instance
    
    def _init_alsa_volume(self):
        """Initialize ALSA volume settings"""
        try:
            logger.info("Initializing ALSA volume settings")
            
            # Set initial ALSA volume to maximum
            cmd = ['amixer', '-c', '2', 'set', 'PCM', '400']  # 400 is max value for this device
            logger.info(f"Executing ALSA command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True)
            
            if result.returncode != 0:
                logger.error(f"ALSA command failed: {result.stderr}")
            else:
                logger.info(f"ALSA volume initialized: {result.stdout}")
                
        except Exception as e:
            logger.error(f"Error initializing ALSA volume: {e}")
    
    def initialize(self):
        try:
            # Load config
            with open('config.toml', 'r') as f:
                config = toml.load(f)
                default_volume = config.get('default_volume', 80)  # fallback to 80 if not set
            
            # VLC configuration
            vlc_args = [
                '--no-xlib',
                '--aout=alsa',
                '--alsa-audio-device=plughw:2,0',
                '--verbose=2'
            ]
            
            self.instance = vlc.Instance(' '.join(vlc_args))
            self.player = self.instance.media_player_new()
            
            # Initialize ALSA volume first
            self._init_alsa_volume()
            
            # Then set initial VLC volume from config
            self.set_volume(default_volume)
            
            logger.info(f"Player initialized with ALSA output and volume {default_volume}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing player: {e}")
            return False
    
    def _signal_handler(self, signum, frame):
        self.cleanup()
    
    def cleanup(self):
        try:
            if hasattr(self, 'player') and self.player:
                self.player.stop()
                del self.player
            if hasattr(self, 'instance') and self.instance:
                del self.instance
        except:
            pass
        finally:
            # Force kill any remaining VLC processes
            os.system("pkill vlc")
    
    def play(self, stream_url):
        try:
            logger.info(f"Attempting to play stream: {stream_url}")
            
            # Stop current stream if any
            if self.is_playing():
                logger.info("Stopping current stream")
                self.stop()
                time.sleep(1)
            
            # Create media
            media = self.instance.media_new(stream_url)
            if not media:
                raise Exception("Failed to create media")
            
            logger.info("Setting media to player")
            self.player.set_media(media)
            self.current_media = media
            
            # Ensure volume is set before playing
            current_vol = self.player.audio_get_volume()
            logger.info(f"Current volume before play: {current_vol}")
            if current_vol == 0:
                logger.info("Volume is 0, resetting to previous value")
                self.set_volume(self.current_status["volume"])
            
            logger.info("Starting playback")
            play_result = self.player.play()
            logger.info(f"Play result: {play_result}")
            
            # Update status
            self.current_status.update({
                "state": "playing",
                "current_station": stream_url
            })
            
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Error playing stream: {e}", exc_info=True)
            self.current_status["state"] = "error"
            return False
    
    def stop(self):
        try:
            logger.info("Stopping playback")
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
    
    def get_status(self):
        try:
            return {
                "state": self.current_status["state"],
                "current_station": self.current_status["current_station"],
                "volume": self.current_status["volume"]
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "state": "error",
                "error": str(e)
            }
    
    def set_volume(self, volume):
        """Set volume level (0-100) for both VLC and ALSA"""
        try:
            logger.info(f"Setting volume to {volume}")
            
            # Set VLC volume
            self.player.audio_set_volume(volume)
            
            # Convert percentage to ALSA value
            if volume >= 90:  # High volume range
                alsa_value = 400  # Maximum value
            elif volume >= 70:  # Medium-high range
                alsa_value = 0   # 0 dB
            elif volume >= 50:  # Medium range
                alsa_value = -1000  # -10 dB
            else:  # Low range
                # Linear scaling for lower volumes
                alsa_value = int(-10239 + (volume * 100))
            
            # Set ALSA volume using the converted value
            cmd = ['amixer', '-c', '2', 'set', 'PCM', f'{alsa_value}']
            logger.info(f"Executing ALSA command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True)
            
            if result.returncode != 0:
                logger.error(f"ALSA volume command failed: {result.stderr}")
            else:
                logger.info(f"ALSA volume set successfully: {result.stdout}")
            
            self.current_status["volume"] = volume
            return True
                
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    def get_volume(self):
        try:
            return self.player.audio_get_volume()
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return 0
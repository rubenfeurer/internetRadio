#!/usr/bin/env -S python

import signal
import sys
import time
import logging
from pathlib import Path
from src.controllers.radio_controller import RadioController
from src.controllers.network_controller import NetworkController
from src.web.web_controller import WebController
from src.utils.logger import Logger
from src.utils.config_manager import ConfigManager
from src.utils.stream_manager import StreamManager
from src.utils.logger import Logger
from src.audio.audio_manager import AudioManager
from src.hardware.gpio_manager import GPIOManager
from src.network.wifi_manager import WiFiManager
from src.network.ap_manager import APManager
from src.controllers.network_controller import NetworkController
from src.controllers.radio_controller import RadioController
from src.web.web_controller import WebController
from src.utils.config_migration import ConfigMigration
import os

# At the top of the file, after imports
def setup_logging():
    """Initialize logging configuration"""
    try:
        print("Setting up logging...")  # Debug print
        log_dir = os.path.join('/home/radio/internetRadio/logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Use the new Logger implementation
        logger = Logger('main', log_dir=log_dir)
        print(f"Logger created: {logger}")  # Debug print
        return logger
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        import traceback
        print(traceback.format_exc())
        return None

# Global logger instance
logger = setup_logging()
print(f"Global logger initialized: {logger}")  # Debug print

def cleanup(radio=None, network=None, web=None):
    """Clean up resources"""
    try:
        if logger:
            logger.info("Cleaning up resources...")
        if web:
            web.stop()
        if radio:
            radio.cleanup()
        if network:
            network.cleanup()
    except Exception as e:
        if logger:
            logger.error(f"Error during cleanup: {e}")
    finally:
        # Clean up logger resources
        Logger.cleanup()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum} to terminate")
    cleanup(radio, network, web)
    sys.exit(0)

class InternetRadio:
    def __init__(self):
        """Initialize InternetRadio"""
        try:
            # Initialize logger
            self.logger = Logger('radio', log_dir='/home/radio/internetRadio/logs')
            
            # Initialize configuration
            self.config_manager = ConfigManager()
            
            # Initialize managers
            self.stream_manager = StreamManager()
            self.audio_manager = AudioManager()
            self.gpio_manager = GPIOManager()
            
            # Initialize controllers
            self.radio_controller = RadioController(
                config_manager=self.config_manager,
                gpio_manager=self.gpio_manager
            )
            
            self.network_controller = NetworkController(
                config_manager=self.config_manager
            )
            
            # Initialize state
            self.current_stream = None
            self.volume = self.config_manager.audio.default_volume
            
            self.logger.info("InternetRadio initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing InternetRadio: {e}")
            raise

    def play_stream(self, stream_name: str) -> bool:
        """Play a stream by name"""
        try:
            stream = self.stream_manager.get_stream_by_name(stream_name)
            if stream:
                if self.stream_manager.play(stream.url):
                    self.current_stream = stream
                    self.logger.info(f"Playing stream: {stream_name}")
                    return True
            self.logger.error(f"Stream not found: {stream_name}")
            return False
        except Exception as e:
            self.logger.error(f"Error playing stream: {e}")
            return False

    def stop_stream(self) -> None:
        """Stop the current stream"""
        try:
            self.stream_manager.stop()
            self.current_stream = None
            self.logger.info("Stream stopped")
        except Exception as e:
            self.logger.error(f"Error stopping stream: {e}")

    def set_volume(self, volume: int) -> None:
        """Set the volume"""
        try:
            self.stream_manager.set_volume(volume)
            self.volume = volume
            self.logger.info(f"Volume set to {volume}")
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")

    def get_volume(self) -> int:
        """Get the current volume"""
        return self.volume

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self.stream_manager.stop()
            self.network_controller.cleanup()
            self.logger.info("InternetRadio cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

def main():
    global radio, network, web
    radio = None
    network = None
    web = None
    
    try:
        print("Starting main function...")  # Debug print
        if logger is None:
            print("Logger not initialized properly")
            return 1
        
        print("Initializing InternetRadio...")  # Debug print
        radio = InternetRadio()
        print("InternetRadio initialized")  # Debug print
        
        network = radio.network_controller
        print("Network controller assigned")  # Debug print
        
        print("Initializing controllers...")  # Debug print
        if not radio.radio_controller.initialize():
            print("Failed to initialize radio controller")  # Debug print
            logger.error("Failed to initialize radio controller")
            return 1
            
        if not network.initialize():
            print("Failed to initialize network controller")  # Debug print
            logger.error("Failed to initialize network controller")
            return 1

        print("Controllers initialized")  # Debug print
        
        # Try to connect to saved networks
        wifi_connected = network.check_and_setup_network()
        print(f"WiFi connected: {wifi_connected}")  # Debug print
        
        if wifi_connected:
            logger.info("Connected to WiFi network")
            radio.radio_controller.set_led_state(blink=True, on_time=3, off_time=3)
        else:
            logger.info("Could not connect to any networks, maintaining AP mode...")
            radio.radio_controller.set_led_state(blink=True, on_time=0.5, off_time=0.5)

        print("Entering main loop...")  # Debug print
        # Main loop
        while True:
            try:
                if not wifi_connected and not network.is_ap_mode_active():
                    logger.warning("AP mode stopped unexpectedly, restarting...")
                    network.start_ap_mode()
                radio.radio_controller.monitor()  # Handle radio state monitoring
                network.monitor()  # Handle network monitoring
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                print(f"Error in main loop: {e}")  # Debug print

    except Exception as e:
        print(f"Critical error in main: {e}")  # Debug print
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str)  # Debug print
        if logger:
            logger.error(f"Critical error in main: {e}")
            logger.error(traceback_str)
        return 1
    finally:
        cleanup(radio, network, web)

    return 0

if __name__ == "__main__":
    exit(main())
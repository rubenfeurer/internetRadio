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

# At the top of the file, after imports
def setup_logging():
    """Initialize logging configuration"""
    try:
        print("Setting up logging...")  # Debug print
        Logger.setup_logging(
            app_log_path='/home/radio/internetRadio/logs/app.log',
            network_log_path='/home/radio/internetRadio/logs/network_debug.log'
        )
        logger = Logger('main')
        print(f"Logger created: {logger}")  # Debug print
        return logger
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        import traceback
        print(traceback.format_exc())  # Print full traceback
        return None

# Global logger instance
logger = setup_logging()
print(f"Global logger initialized: {logger}")  # Debug print

def cleanup(radio=None, network=None, web=None):
    """Clean up resources"""
    try:
        logger.info("Cleaning up resources...")
        if web:
            web.stop()
        if radio:
            radio.cleanup()
        if network:
            network.cleanup()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum} to terminate")
    cleanup(radio, network, web)
    sys.exit(0)

class InternetRadio:
    def __init__(self):
        self.logger = logger
        
        try:
            # Initialize configuration migration
            config_dir = Path(__file__).parent / 'config'
            migration = ConfigMigration(config_dir)
            migration.migrate()
        except Exception as e:
            self.logger.warning(f"Config migration failed: {e}, using default config")

        # Initialize managers
        self.config_manager = ConfigManager()
        self.stream_manager = StreamManager()

        # Initialize hardware components with config
        self.audio = AudioManager(
            default_volume=self.config_manager.audio.default_volume,
            volume_step=self.config_manager.audio.volume_step
        )
        self.gpio = GPIOManager()

        # Initialize network components
        self.wifi = WiFiManager()
        self.ap = APManager(
            ssid=self.config_manager.network.ap_ssid,
            password=self.config_manager.network.ap_password
        )

        # Initialize controllers
        self.network_controller = NetworkController(
            wifi_manager=self.wifi,
            ap_manager=self.ap,
            config_manager=self.config_manager
        )
        self.radio_controller = RadioController(
            audio_manager=self.audio,
            gpio_manager=self.gpio,
            stream_manager=self.stream_manager
        )
        self.web_controller = WebController(
            radio_controller=self.radio_controller,
            network_controller=self.network_controller
        )

    def start(self):
        try:
            self.logger.info("Starting Internet Radio...")
            
            # Initialize components
            self.gpio.initialize()
            self.audio.initialize()
            self.network_controller.initialize()
            
            # Start web interface
            self.web_controller.start()
            
        except Exception as e:
            self.logger.error(f"Error starting application: {e}")
            self.cleanup()

    def cleanup(self):
        try:
            self.logger.info("Cleaning up...")
            self.gpio.cleanup()
            self.audio.cleanup()
            self.network_controller.cleanup()
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
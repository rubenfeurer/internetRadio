#!/usr/bin/env -S python

import signal
import sys
import logging
from src.controllers.radio_controller import RadioController
from src.controllers.network_controller import NetworkController
from src.web.web_controller import WebController
from src.utils.logger import Logger

# Set up logging
logger = Logger.setup_logging(
    app_log_path='/home/radio/internetRadio/logs/app.log',
    network_log_path='/home/radio/internetRadio/logs/network_debug.log'
)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received signal to terminate")
    sys.exit(0)

def main():
    try:
        # Set up signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Initialize controllers
        radio = RadioController()
        network = NetworkController()
        
        if not radio.initialize() or not network.initialize():
            logger.error("Failed to initialize controllers")
            return 1

        # Try to connect to saved networks
        wifi_connected = network.check_and_setup_network()
        
        if wifi_connected:
            radio.set_led_state(blink=True, on_time=3, off_time=3)
        else:
            logger.info("Could not connect to any networks, maintaining AP mode...")
            radio.set_led_state(blink=True, on_time=0.5, off_time=0.5)

        # Initialize and start web interface
        web = WebController(radio, network)
        web.start()

        # Main loop
        while True:
            if not wifi_connected and not network.is_ap_mode_active():
                logger.warning("AP mode stopped unexpectedly, restarting...")
                network.start_ap_mode()
            radio.monitor()  # Handle radio state monitoring
            network.monitor()  # Handle network monitoring
            time.sleep(5)

    except Exception as e:
        logger.error(f"Main error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
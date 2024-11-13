from typing import Optional
from src.utils.logger import Logger
from src.controllers.radio_controller import RadioController
from src.hardware.button_controller import ButtonController
from src.hardware.rotary_encoder import RotaryEncoderController

class RadioApp:
    """Main application class for the Internet Radio"""
    
    def __init__(self, 
                 radio_controller: Optional[RadioController] = None,
                 button_controller: Optional[ButtonController] = None,
                 encoder_controller: Optional[RotaryEncoderController] = None):
        """Initialize the radio application
        
        Args:
            radio_controller: Optional custom radio controller
            button_controller: Optional custom button controller
            encoder_controller: Optional custom rotary encoder controller
        """
        self.logger = Logger.get_logger(__name__)
        self.radio = radio_controller or RadioController()
        self.button = button_controller or ButtonController(pin=17)
        self.encoder = encoder_controller or RotaryEncoderController(clk_pin=22, dt_pin=23)
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize all components and bind event handlers
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Initialize components
            if not self.radio.initialize():
                self.logger.error("Failed to initialize radio controller")
                self.cleanup()
                return False
                
            if not self.button.initialize():
                self.logger.error("Failed to initialize button controller")
                self.cleanup()
                return False
                
            if not self.encoder.initialize():
                self.logger.error("Failed to initialize encoder controller")
                self.cleanup()
                return False

            # Bind button events
            self.button.when_pressed(self.handle_button_press)
            self.button.when_held(self.handle_button_hold)
            
            # Bind encoder events
            self.encoder.when_rotated(self.handle_rotation)
            
            self.initialized = True
            self.logger.info("Radio application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize radio application: {str(e)}")
            self.cleanup()
            return False
    
    def handle_button_press(self):
        """Handle button press event"""
        try:
            self.radio.next_station()
        except Exception as e:
            self.logger.error(f"Error handling button press: {str(e)}")
    
    def handle_button_hold(self):
        """Handle button hold event"""
        try:
            self.radio.reset_to_first_station()
        except Exception as e:
            self.logger.error(f"Error handling button hold: {str(e)}")
    
    def handle_rotation(self, direction: int):
        """Handle encoder rotation event"""
        try:
            if direction > 0:
                self.radio.volume_up()
            else:
                self.radio.volume_down()
        except Exception as e:
            self.logger.error(f"Error handling rotation: {str(e)}")
    
    def cleanup(self) -> None:
        """Clean up all resources"""
        try:
            if self.radio:
                self.radio.cleanup()
            if self.button:
                self.button.cleanup()
            if self.encoder:
                self.encoder.cleanup()
            self.initialized = False
            self.logger.info("Radio application cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def run(self) -> None:
        """Run the main application loop"""
        if not self.initialized:
            self.logger.error("Cannot run: Application not initialized")
            return
        
        try:
            self.logger.info("Starting radio application")
            while True:
                self.radio.monitor()
                
        except KeyboardInterrupt:
            self.logger.info("Radio application stopped by user")
        except Exception as e:
            self.logger.error(f"Error in main loop: {str(e)}")
        finally:
            self.cleanup() 
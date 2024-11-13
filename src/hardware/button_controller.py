import logging
from gpiozero import Button
from typing import Callable

class ButtonController:
    """Controller for managing button input"""
    
    def __init__(self, pin: int = 17, hold_time: float = 2.0):
        """Initialize button controller
        
        Args:
            pin (int): GPIO pin number for button (default: 17)
            hold_time (float): Time in seconds for hold detection (default: 2.0)
        """
        self.logger = logging.getLogger('hardware')
        self.pin = pin
        
        try:
            self.button = Button(pin, hold_time=hold_time, pull_up=True)
            self.logger.info(f"Button initialized on GPIO{pin}")
        except Exception as e:
            self.logger.error(f"Failed to initialize button: {str(e)}")
            raise
    
    def when_pressed(self, callback: Callable[[], None]) -> None:
        """Set callback for button press events
        
        Args:
            callback (Callable[[], None]): Function to call when button is pressed
        """
        try:
            def wrapped_callback():
                try:
                    callback()
                    self.logger.debug("Button press callback executed")
                except Exception as e:
                    self.logger.error(f"Error in button callback: {str(e)}")
            
            self.button.when_pressed = wrapped_callback
            self.logger.debug("Button press callback set")
        except Exception as e:
            self.logger.error(f"Failed to set button press callback: {str(e)}")
            raise
    
    def when_released(self, callback: Callable[[], None]) -> None:
        """Set callback for button release events
        
        Args:
            callback (Callable[[], None]): Function to call when button is released
        """
        try:
            def wrapped_callback():
                try:
                    callback()
                    self.logger.debug("Button release callback executed")
                except Exception as e:
                    self.logger.error(f"Error in button callback: {str(e)}")
            
            self.button.when_released = wrapped_callback
            self.logger.debug("Button release callback set")
        except Exception as e:
            self.logger.error(f"Failed to set button release callback: {str(e)}")
            raise
    
    def when_held(self, callback: Callable[[], None]) -> None:
        """Set callback for button held events
        
        Args:
            callback (Callable[[], None]): Function to call when button is held
        """
        try:
            def wrapped_callback():
                try:
                    callback()
                    self.logger.debug("Button held callback executed")
                except Exception as e:
                    self.logger.error(f"Error in button callback: {str(e)}")
            
            self.button.when_held = wrapped_callback
            self.logger.debug("Button held callback set")
        except Exception as e:
            self.logger.error(f"Failed to set button held callback: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up button resources"""
        try:
            self.button.close()
            self.logger.info("Button resources cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to clean up button resources: {str(e)}")
            raise 
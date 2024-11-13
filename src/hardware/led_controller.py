import logging
from gpiozero import LED
from gpiozero.exc import GPIOPinInUse

class LEDController:
    """Controller for managing LED status indicator"""
    
    def __init__(self, pin: int = 17):
        """Initialize LED controller
        
        Args:
            pin (int): GPIO pin number for LED (default: 17)
        """
        self.logger = logging.getLogger('hardware')
        self.pin = pin
        try:
            self.led = LED(pin)
            self.logger.info(f"LED initialized on GPIO{pin}")
        except GPIOPinInUse as e:
            self.logger.error(f"Failed to initialize LED on GPIO{pin}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize LED on GPIO{pin}: {str(e)}")
            raise
    
    def turn_on(self) -> None:
        """Turn LED on"""
        try:
            self.led.on()
            self.logger.debug("LED turned on")
        except Exception as e:
            self.logger.error(f"Failed to turn LED on: {str(e)}")
            raise
    
    def turn_off(self) -> None:
        """Turn LED off"""
        try:
            self.led.off()
            self.logger.debug("LED turned off")
        except Exception as e:
            self.logger.error(f"Failed to turn LED off: {str(e)}")
            raise
    
    def blink(self, on_time: float = 1, off_time: float = 1) -> None:
        """Make LED blink
        
        Args:
            on_time (float): Time in seconds for LED to stay on
            off_time (float): Time in seconds for LED to stay off
        """
        try:
            self.led.blink(on_time=on_time, off_time=off_time)
            self.logger.debug(f"LED blinking (on: {on_time}s, off: {off_time}s)")
        except Exception as e:
            self.logger.error(f"Failed to make LED blink: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up LED resources"""
        try:
            self.led.close()
            self.logger.info("LED resources cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to clean up LED resources: {str(e)}")
            raise

import logging
from gpiozero import RotaryEncoder
from typing import Callable

class RotaryEncoderController:
    """Controller for managing rotary encoder input"""
    
    def __init__(self, clk_pin: int = 22, dt_pin: int = 23):
        """Initialize rotary encoder controller
        
        Args:
            clk_pin (int): GPIO pin number for CLK (default: 22)
            dt_pin (int): GPIO pin number for DT (default: 23)
        """
        self.logger = logging.getLogger('hardware')
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        
        try:
            self.encoder = RotaryEncoder(clk_pin, dt_pin)
            self.logger.info(f"Rotary encoder initialized on GPIO{clk_pin}/GPIO{dt_pin}")
        except Exception as e:
            self.logger.error(f"Failed to initialize rotary encoder: {str(e)}")
            raise
    
    def when_rotated(self, callback: Callable[[int], None]) -> None:
        """Set callback for rotation events
        
        Args:
            callback (Callable[[int], None]): Function to call when rotation occurs.
                                            Takes direction (-1 or 1) as argument.
        """
        try:
            def wrapped_callback(direction: int) -> None:
                try:
                    callback(direction)
                except Exception as e:
                    self.logger.error(f"Error in rotation callback: {str(e)}")
            
            # Set the wrapped callback as a property
            self.encoder.when_rotated = wrapped_callback
            self.logger.debug("Rotation callback set")
        except Exception as e:
            self.logger.error(f"Failed to set rotation callback: {str(e)}")
            raise
    
    def get_steps(self) -> int:
        """Get current step count
        
        Returns:
            int: Current step count
        """
        try:
            return self.encoder.steps
        except Exception as e:
            self.logger.error(f"Failed to get steps: {str(e)}")
            raise
    
    def reset_steps(self) -> None:
        """Reset step counter to zero"""
        try:
            self.encoder.steps = 0
            self.logger.debug("Steps reset to 0")
        except Exception as e:
            self.logger.error(f"Failed to reset steps: {str(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up encoder resources"""
        try:
            self.encoder.close()
            self.logger.info("Rotary encoder resources cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to clean up rotary encoder resources: {str(e)}")
            raise 
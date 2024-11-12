import logging
from typing import Optional
from gpiozero import Button, RotaryEncoder, LED, Device
from gpiozero.pins.pigpio import PiGPIOFactory
import pigpio

class GPIOManager:
    def __init__(self):
        self.logger = logging.getLogger('hardware')
        self.pi = None
        self.factory = None
        self.led = None
        self.encoder = None
        self.button = None
        
        # GPIO Pin definitions
        self.LED_PIN = 17
        self.ENCODER_A_PIN = 22
        self.ENCODER_B_PIN = 23
        self.BUTTON_PIN = 27
    
    def initialize(self) -> bool:
        """Initialize GPIO connections and setup devices"""
        try:
            self.logger.info("Initializing GPIO...")
            
            # Initialize pigpio
            self.pi = pigpio.pi()
            if not self.pi.connected:
                self.logger.error("Failed to connect to pigpiod")
                return False
            
            # Create pin factory
            self.factory = PiGPIOFactory()
            Device.pin_factory = self.factory
            
            # Initialize devices
            self.led = LED(self.LED_PIN)
            self.encoder = RotaryEncoder(
                self.ENCODER_A_PIN,
                self.ENCODER_B_PIN,
                max_steps=20
            )
            self.button = Button(self.BUTTON_PIN, pull_up=True)
            
            self.logger.info("GPIO initialization successful")
            return True
            
        except Exception as e:
            self.logger.error("Error initializing GPIO: %s", str(e))
            return False
    
    def cleanup(self) -> None:
        """Clean up GPIO resources"""
        try:
            if self.led:
                self.led.close()
            if self.encoder:
                self.encoder.close()
            if self.button:
                self.button.close()
            if self.pi:
                self.pi.stop()
            
            self.logger.info("GPIO cleanup completed")
            
        except Exception as e:
            self.logger.error("Error during GPIO cleanup: %s", str(e))
    
    def set_led_state(self, state: bool) -> None:
        """Set LED state (on/off)"""
        try:
            if not self.led:
                self.logger.error("LED not initialized")
                return
                
            if state:
                self.led.on()
            else:
                self.led.off()
                
        except Exception as e:
            self.logger.error("Error setting LED state: %s", str(e))
    
    def start_led_blink(self, on_time: float = 1, off_time: float = 1) -> None:
        """Start LED blinking pattern"""
        try:
            if not self.led:
                self.logger.error("LED not initialized")
                return
                
            self.led.blink(on_time=on_time, off_time=off_time)
                
        except Exception as e:
            self.logger.error("Error starting LED blink: %s", str(e))
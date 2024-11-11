from gpiozero import Button, RotaryEncoder
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Only Button 3 and Encoder pins
BUTTON3_PIN = 26      # Pin 37 (GPIO26)
ENCODER_SW = 10       # Pin 19 (GPIO10) - Button Press
ENCODER_DT = 9        # Pin 21 (GPIO9)  - Data Channel
ENCODER_CLK = 11      # Pin 23 (GPIO11) - Clock Channel

# Global volume variable
volume = 50

print("\n=== Testing Button 3 and Rotary Encoder ===")
print("Press Ctrl+C to exit\n")

try:
    # Initialize Button 3
    print("Initializing Button 3...")
    button3 = Button(BUTTON3_PIN, pull_up=True, bounce_time=0.2)
    
    def button3_pressed():
        print("Button 3 pressed!")
        logger.info("Button 3 pressed!")
    
    button3.when_pressed = button3_pressed
    print("Button 3 initialized successfully")

    # Initialize Encoder
    print("\nInitializing Rotary Encoder...")
    
    def volume_change():
        global volume
        volume = max(0, min(100, volume + (5 if encoder.value > 0 else -5)))
        print(f"Volume: {volume}")
        logger.info(f"Volume: {volume}")
    
    def encoder_button_press():
        print("Encoder button pressed!")
        logger.info("Encoder button pressed!")
    
    encoder = RotaryEncoder(
        ENCODER_DT, 
        ENCODER_CLK,
        bounce_time=0.1,
        max_steps=1,
        wrap=False
    )
    encoder_button = Button(ENCODER_SW, pull_up=True, bounce_time=0.2)
    
    encoder.when_rotated = volume_change
    encoder_button.when_pressed = encoder_button_press
    
    print("Rotary Encoder initialized successfully")
    
    print("\nTest instructions:")
    print("1. Press Button 3")
    print("2. Turn encoder clockwise and counterclockwise")
    print("3. Press encoder button")
    print("\nWaiting for input...\n")
    
    while True:
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\nTest completed - Ctrl+C pressed")
except Exception as e:
    print(f"\nError during test: {e}")
    logger.error(f"Error during test: {e}")
finally:
    print("Test ended") 
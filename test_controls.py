from gpiozero import Button, RotaryEncoder
import time
import logging

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Print to console
        logging.FileHandler('/home/radio/internetRadio/logs/test.log')  # Save to file
    ]
)
logger = logging.getLogger(__name__)

# Print immediate feedback
print("Starting control test script...")
logger.info("Test script initialized")

# Button Pins
BUTTON_PINS = {
    'button1': 17,  # Pin 11 (GPIO17)
    'button2': 16,  # Pin 36 (GPIO16)
    'button3': 26   # Pin 37 (GPIO26)
}

# Rotary Encoder Pins
ENCODER_SW = 10    # Pin 19 (GPIO10)
ENCODER_DT = 9     # Pin 21 (GPIO9)
ENCODER_CLK = 11   # Pin 23 (GPIO11)

def test_buttons():
    print("Initializing buttons...")
    logger.info("Testing buttons...")
    
    def button_callback(button_num):
        print(f"Button {button_num} pressed!")
        logger.info(f"Button {button_num} pressed!")
    
    # Initialize buttons
    buttons = {}
    for name, pin in BUTTON_PINS.items():
        print(f"Setting up {name} on pin {pin}")
        try:
            buttons[name] = Button(pin, pull_up=True, bounce_time=0.2)
            buttons[name].when_pressed = lambda b=name: button_callback(b)
        except Exception as e:
            print(f"Failed to set up {name}: {e}")
            logger.error(f"Failed to set up {name}: {e}")
    
    return buttons

def test_encoder():
    logger.info("Testing encoder...")
    
    value = 50  # Starting value
    
    def volume_change():
        nonlocal value
        value = max(0, min(100, value + (5 if encoder.value > 0 else -5)))
        logger.info(f"Volume: {value}")
    
    encoder = RotaryEncoder(ENCODER_DT, ENCODER_CLK, ENCODER_SW)
    encoder.when_rotated = volume_change
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("Testing completed.")
    
    encoder.when_rotated = None
    encoder.close()
    
    logger.info("Encoder test completed.")
    
    return encoder 
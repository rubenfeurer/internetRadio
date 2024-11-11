from gpiozero import Button
import time
import logging

# Set up logging
print("Starting simple GPIO test...")

# Test just one button first
try:
    print("Initializing button on GPIO 17...")
    button1 = Button(17, pull_up=True)
    
    def button_press():
        print("Button pressed!")
    
    button1.when_pressed = button_press
    
    print("Button initialized. Press the button or Ctrl+C to exit...")
    
    # Keep the script running
    while True:
        time.sleep(0.1)
        
except Exception as e:
    print(f"Error: {e}")
finally:
    print("Test ended") 
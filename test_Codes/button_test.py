from gpiozero import Button
from signal import pause

BUTTON1_PIN = 17  # Example GPIO pin for Button 1
BUTTON2_PIN = 27  # Example GPIO pin for Button 2
BUTTON3_PIN = 22  # Example GPIO pin for Button 3

button1 = Button(BUTTON1_PIN, pull_up=True, bounce_time=0.2)
button2 = Button(BUTTON2_PIN, pull_up=True, bounce_time=0.2)
button3 = Button(BUTTON3_PIN, pull_up=True, bounce_time=0.2)

button1.when_pressed = lambda: print("Button 1 pressed")
button2.when_pressed = lambda: print("Button 2 pressed")
button3.when_pressed = lambda: print("Button 3 pressed")

print("Testing button presses...")

pause()

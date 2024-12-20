#!/bin/bash

# GPIO Pin definitions
ROTARY_CLK=11  # GPIO11
ROTARY_DT=9    # GPIO9
ROTARY_SW=10   # GPIO10
BUTTON_1=17    # GPIO17
BUTTON_2=16    # GPIO16
BUTTON_3=26    # GPIO26
LED=4          # GPIO4

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'    # No Color
BOLD='\033[1m'

# Logging function
log() {
    echo -e "${BOLD}$1${NC}"
}

# Test individual GPIO pin
test_pin() {
    local pin=$1
    local name=$2
    local test_passed=false
    
    while [ "$test_passed" = false ]; do
        # Create Python script for testing
        cat > /tmp/test_pin.py <<EOF
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup($pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    start_time = time.time()
    while time.time() - start_time < 10:
        if GPIO.input($pin) == 0:  # Button pressed
            print("SUCCESS")
            GPIO.cleanup()
            exit(0)
        time.sleep(0.1)
    print("TIMEOUT")
    GPIO.cleanup()
except Exception as e:
    print(f"ERROR: {str(e)}")
    GPIO.cleanup()
EOF

        echo -e "\nTesting ${BOLD}$name (GPIO$pin)${NC}"
        echo "Please press/turn the $name within 10 seconds..."
        
        result=$(python3 /tmp/test_pin.py)
        
        if [ "$result" = "SUCCESS" ]; then
            echo -e "${GREEN}✓ $name is working${NC}"
            test_passed=true
            return 0
        else
            if [ "$result" = "TIMEOUT" ]; then
                echo -e "${RED}✗ No input detected from $name${NC}"
            else
                echo -e "${RED}✗ Error testing $name: $result${NC}"
            fi
            
            # Ask if user wants to retry this specific test
            echo
            read -p "Would you like to test $name again? (Y/n): " retry
            if [[ $retry =~ ^[Nn]$ ]]; then
                return 1
            fi
            echo -e "\nRetrying $name test..."
        fi
    done
}

# Test LED with retry
test_led() {
    local test_passed=false
    
    while [ "$test_passed" = false ]; do
        # Create Python script for LED test
        cat > /tmp/test_led.py <<EOF
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup($LED, GPIO.OUT)

try:
    for _ in range(3):
        GPIO.output($LED, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output($LED, GPIO.LOW)
        time.sleep(0.5)
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {str(e)}")
finally:
    GPIO.cleanup()
EOF

        echo -e "\nTesting ${BOLD}LED (GPIO$LED)${NC}"
        echo "The LED should blink 3 times..."
        
        result=$(python3 /tmp/test_led.py)
        
        if [ "$result" = "SUCCESS" ]; then
            echo -e "${GREEN}✓ LED test completed${NC}"
            test_passed=true
            return 0
        else
            echo -e "${RED}✗ Error testing LED: $result${NC}"
            
            # Ask if user wants to retry LED test
            echo
            read -p "Would you like to test the LED again? (Y/n): " retry
            if [[ $retry =~ ^[Nn]$ ]]; then
                return 1
            fi
            echo -e "\nRetrying LED test..."
        fi
    done
}

# Main test function
main() {
    clear
    log "Internet Radio Hardware Test"
    log "=========================="
    echo
    log "This script will help you test if all hardware components are correctly wired."
    log "Follow the instructions for each component."
    echo
    
    # Print wiring diagram
    log "Wiring Diagram:"
    echo "-------------"
    echo "Rotary Encoder:"
    echo "  - GND → Pin 6 (Ground)"
    echo "  - VCC → Pin 1 (3.3V)"
    echo "  - SW  → Pin 19 (GPIO10)"
    echo "  - DT  → Pin 21 (GPIO9)"
    echo "  - CLK → Pin 23 (GPIO11)"
    echo
    echo "Buttons:"
    echo "  - Button 1 → Pin 11 (GPIO17) + Ground"
    echo "  - Button 2 → Pin 36 (GPIO16) + Ground"
    echo "  - Button 3 → Pin 37 (GPIO26) + Ground"
    echo
    echo "LED:"
    echo "  - LED positive → 220Ω resistor → GPIO4 (Pin 7)"
    echo "  - LED negative → Ground"
    echo
    
    read -p "Press Enter to start the tests..."
    
    # Test each component
    test_pin $ROTARY_CLK "Rotary Encoder CLK"
    test_pin $ROTARY_DT "Rotary Encoder DT"
    test_pin $ROTARY_SW "Rotary Encoder Button"
    test_pin $BUTTON_1 "Button 1"
    test_pin $BUTTON_2 "Button 2"
    test_pin $BUTTON_3 "Button 3"
    test_led
    
    # Cleanup
    rm -f /tmp/test_pin.py /tmp/test_led.py
    
    echo
    log "Test Summary"
    log "==========="
    echo "If all tests passed (✓), your hardware is correctly wired."
    echo "If any test failed (✗), please check the wiring for that component."
}

# Run main function
main

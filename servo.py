from gpiozero import Servo
from time import sleep

# GPIO 12 is Pin 32
# MG90S typically likes pulse widths between 0.5ms and 2.5ms
my_factory = None # Default factory is usually fine on Pi 5
servo = Servo(12, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

try:
    print("Starting servo test on GPIO 12...")
    while True:
        servo.min()
        print("Min")
        sleep(1)
        
        servo.mid()
        print("Mid")
        sleep(1)
        
        servo.max()
        print("Max")
        sleep(1)
        
except KeyboardInterrupt:
    servo.detach() # Turns off the signal so it doesn't buzz
    print("\nProgram stopped")
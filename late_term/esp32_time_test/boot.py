from machine import Pin

DOWNROAD_PIN = 33
downroad_pin = Pin(DOWNROAD_PIN, Pin.IN, Pin.PULL_UP)
if(not downroad_pin.value()):
    execfile("prog/do.py")
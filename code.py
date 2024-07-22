import time
import board
import neopixel
import time
import board
from utils import *
import pwmio
from adafruit_motor import servo
import asyncio

# Define the number of NeoPixels
num_pixels = 1
pixel = neopixel.NeoPixel(board.NEOPIXEL, num_pixels)

# Set the brightness
pixel.brightness = 0.3



def light_test():
    print("Light test")
    led_strip_pin = pwmio.PWMOut(board.GP8, frequency=100)

    for _ in range(3):
        pwm_fade_in_out(led_strip_pin, fade_time=0.5)
    led_strip_pin.duty_cycle = 0
    print("Light test done")



def leg_test():
    print("Leg test")
    leg1_joint1 = Joint(board.GP15)
    leg1_joint1.move(30)
    time.sleep(0.5)
    leg1_joint1.move(180)
    time.sleep(0.5)
    leg1_joint1.move(90)
    print("Leg test done")

def rainbow():
    print("Rainbow")
    while True:
        
        # Main loop to cycle through the rainbow colors with smooth transitions
        for i in range(len(rainbow_colors)):
            start_color = rainbow_colors[i]
            end_color = rainbow_colors[(i + 1) % len(rainbow_colors)]
            for j in range(100):  # 100 steps for smooth transition
                factor = j / 100.0
                color = interpolate_color(start_color, end_color, factor)
                pixel.fill(color)
                time.sleep(0.01)  # Adjust speed of the gradient

async def main():
    print("Starting tests")
    leg_test()
    light_test()

    rainbow()

asyncio.run(main())

import time
import board
import neopixel
import time
import board
from utils import pwm_fade_in_out, Joint
import pwmio
from adafruit_motor import servo

# Define the number of NeoPixels
num_pixels = 1
pixel = neopixel.NeoPixel(board.NEOPIXEL, num_pixels)

# Set the brightness
pixel.brightness = 0.3

# Define the rainbow colors
rainbow_colors = [
    (255, 0, 0),    # Red
    (255, 127, 0),  # Orange
    (255, 255, 0),  # Yellow
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (75, 0, 130),   # Indigo    (148, 0, 211)   # Violet
]

# Function to interpolate between two colors
def interpolate_color(color1, color2, factor):
    return (
        int(color1[0] + (color2[0] - color1[0]) * factor),
        int(color1[1] + (color2[1] - color1[1]) * factor),
        int(color1[2] + (color2[2] - color1[2]) * factor)
    )
led_strip_pin = pwmio.PWMOut(board.GP8, frequency=100)



#Perform 3 fade in and fade out cycles
for _ in range(3):
    pwm_fade_in_out(led_strip_pin, fade_time=0.2)
led_strip_pin.duty_cycle = 0

# Legs test
leg1_joint1 = Joint(board.GP15)

leg1_joint1.move(30)
time.sleep(0.5)
leg1_joint1.move(180)
time.sleep(0.5)
leg1_joint1.move(90)

# Cycle
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

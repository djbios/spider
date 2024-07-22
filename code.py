import time
import board
import neopixel
import time
import board
from utils import pwm_fade_in_out
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
    pwm_fade_in_out(led_strip_pin, fade_time=0.1)
led_strip_pin.duty_cycle = 0

# Legs

# create a PWMOut object on Pin A2.
pwm = pwmio.PWMOut(board.GP15, duty_cycle=2 ** 15, frequency=50)

# Create a servo object, my_servo.
my_servo = servo.Servo(pwm)


for angle in range(30, 180, 5):  # 0 - 180 degrees, 5 degrees at a time.
    my_servo.angle = angle
    time.sleep(0.05)
for angle in range(180, 30, -5): # 180 - 0 degrees, 5 degrees at a time.
    my_servo.angle = angle
    time.sleep(0.05)

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
            time.sleep(0.05)  # Adjust speed of the gradient

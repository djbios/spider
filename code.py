import time
import neopixel
import time
import board
from utils import *
import pwmio
from adafruit_motor import servo
import asyncio
import analogio
import pins
import circuitpython_schedule as schedule
import sys


VOLTAGE_MULTIPLIER = 0.0002985503
BATTERY_MAX_VOLTAGE = 12.6
BATTERY_MIN_VOLTAGE = 9.6

# Define the number of NeoPixels

pixel = neopixel.NeoPixel(pins.NEOPIXEL, 1)

# Set the brightness
pixel.brightness = 0.3

leg1 = Leg(
    hip=Joint(pins.LEG1_HIP), 
    knee=Joint(pins.LEG1_KNEE), 
    ankle=Joint(pins.LEG1_ANKLE),
)
leg2 = Leg(
    hip=Joint(pins.LEG2_HIP),
    knee=Joint(pins.LEG2_KNEE),
    ankle=Joint(pins.LEG2_ANKLE),
)
leg3 = Leg(
    hip=Joint(pins.LEG3_HIP),
    knee=Joint(pins.LEG3_KNEE),
    ankle=Joint(pins.LEG3_ANKLE),
)
leg4 = Leg(
    hip=Joint(pins.LEG4_HIP),
    knee=Joint(pins.LEG4_KNEE),
    ankle=Joint(pins.LEG4_ANKLE),
)

led_strip_pwm = pwmio.PWMOut(pins.LED_STRIP)

battery_adc = analogio.AnalogIn(pins.BATTERY_ADC)

# Tests
def get_battery_voltage() -> float:
    # Convert the analog reading to voltage
    return battery_adc.value * VOLTAGE_MULTIPLIER

def get_battery_percentage() -> int:
    voltage = get_battery_voltage()
    perc = int((voltage - BATTERY_MIN_VOLTAGE) / (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE) * 100)
    return max(0, min(100, perc))

def light_test():
    print("Light test")

    for _ in range(3):
        pwm_fade_in_out(led_strip_pwm, fade_time=0.5)
    led_strip_pwm.duty_cycle = 0
    print("Light test done")



def leg_test():
    print("Leg test")
    for leg in [leg1, leg2, leg3, leg4]:
        for joint in [leg.hip, leg.knee, leg.ankle]:
            for angle in [80, 100, 90]:
                joint.move(angle, speed=0.2)
                time.sleep(0.5)
            
    print("Leg test done")

def print_battery():
    voltage = get_battery_voltage()
    percentage = get_battery_percentage()

    bar_length = 50  # Length of the progress bar
    filled_length = int(bar_length * percentage // 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write(f"\rBattery voltage: {voltage:.2f}V |{bar}| {percentage}%")

# Scheduled tasks
schedule.every(30).seconds.do(print_battery)

async def main():
    print("Starting tests")
    print_battery()
    light_test()
    leg_test()

    while True:
        # Scheduler
        schedule.run_pending()

        # Rainbow
        for i in range(len(rainbow_colors)):
            start_color = rainbow_colors[i]
            end_color = rainbow_colors[(i + 1) % len(rainbow_colors)]
            for j in range(100):  # 100 steps for smooth transition
                factor = j / 100.0
                color = interpolate_color(start_color, end_color, factor)
                pixel.fill(color)
                time.sleep(0.01)  # Adjust speed of the gradient


asyncio.run(main())

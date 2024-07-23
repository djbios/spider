import time
import board
import neopixel
import time
import board
from utils import *
import pwmio
from adafruit_motor import servo
import asyncio
import analogio
import pins

VOLTAGE_MULTIPLIER = 0.0002985503
BATTERY_MAX_VOLTAGE = 12.6
BATTERY_MIN_VOLTAGE = 9.6

# Define the number of NeoPixels

pixel = neopixel.NeoPixel(pins.NEOPIXEL, 1)

# Set the brightness
pixel.brightness = 0.3

# Pins config
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
    return int((voltage - BATTERY_MIN_VOLTAGE) / (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE) * 100)

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
            joint.move(80)
            time.sleep(0.2)
            joint.move(100)
            time.sleep(0.2)
            joint.move(90)
            time.sleep(0.2)
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
    print(f"Battery voltage: {get_battery_voltage():.2f}V")
    print(f"Battery percentage: {get_battery_percentage()}%")
    light_test()
    leg_test()
    rainbow()

asyncio.run(main())

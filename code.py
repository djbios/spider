import time
from utils import Battery, Leg, Joint, pwm_fade_in_out
import pwmio
import asyncio
import pins
from routines import RoutinesRegistry, BaseRoutine
import circuitpython_schedule as schedule

# Discovery
from serial import *  # noqa

# Hardware setup
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

battery = Battery(pins.BATTERY_ADC)

# Tests


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
                joint.move(angle, speed=0.8)
                time.sleep(0.5)

    print("Leg test done")


# Routines
@RoutinesRegistry.register()
class SchedulerRoutine(BaseRoutine):
    def __init__(self) -> None:
        schedule.every(5).seconds.do(battery.print_battery)
        print("SchedulerRoutine initialized")
        super().__init__()

    async def run(self):
        schedule.run_pending()


# Main
async def main():
    print("Starting tests")

    light_test()
    leg_test()

    RoutinesRegistry.initialise()

    while True:
        await RoutinesRegistry.run()

asyncio.run(main())

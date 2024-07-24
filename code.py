import time
import asyncio
from routines import RoutinesRegistry, BaseRoutine
import circuitpython_schedule as schedule
from hardware import walker, light, battery

# Discovery
from serial import *  # noqa


# Tests

def light_test():
    print("Light test")

    for _ in range(3):
        light.fade_in(fade_time=0.5)
        light.fade_out(fade_time=0.5)
        light.turn_off()
    print("Light test done")


def leg_test():
    print("Leg test")
    for leg in walker.legs:
        for joint in [leg.hip, leg.knee, leg.ankle]:
            for angle in [80, 100, 90]:
                joint.move(angle, speed=1)
                time.sleep(0.2)

    print("Leg test done")


# Routines
@RoutinesRegistry.register()
class SchedulerRoutine(BaseRoutine):
    def __init__(self) -> None:
        schedule.every(60).seconds.do(battery.print_battery)
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

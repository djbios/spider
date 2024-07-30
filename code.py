import asyncio
from routines import RoutinesRegistry, BaseRoutine
import circuitpython_schedule as schedule
from hardware import light, battery, walker
from adafruit_pca9685 import PCA9685

# Discovery
from serial import * # noqa
from tests import leg_test, light_test  # noqa


# Tests


# Routines
@RoutinesRegistry.register()
class SchedulerRoutine(BaseRoutine):
    def __init__(self) -> None:
        schedule.every(30).seconds.do(battery.print_battery)
        print("SchedulerRoutine initialized")
        super().__init__()

    async def tick(self):
        schedule.run_pending()


async def initial_actions():
    battery.print_battery()
    light_test()
    await leg_test()
    await walker.wiggle(10)
    await walker.to_zero()


# Main
async def main():
    await RoutinesRegistry.initialise()
    await asyncio.gather(
        asyncio.create_task(initial_actions()),
        RoutinesRegistry.routines_coroutine,
    )


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Interrupted")
    #walker.deactivate()

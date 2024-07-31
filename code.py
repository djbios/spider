import asyncio
from hardware import battery, accelerometer, walker, storage
from routines import RoutinesRegistry
import time
from tests import light_test, leg_test

# # Discovery
# from serial import * # noqa
from api import *  # noqa


async def initial_actions():
    battery.print_battery()
    accelerometer.print_xyz()
    light_test()
    storage["last_boot"] = time.time()
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
    walker.deactivate()

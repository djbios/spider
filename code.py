import asyncio
from hardware import battery, accelerometer, walker
from flash_storage import storage
from routines import RoutinesRegistry
import time

# # Discovery
# from serial import * # noqa
from api import *  # noqa


async def initial_actions():
    battery.log_battery()
    accelerometer.log_xyz()
    storage["last_boot"] = time.time()
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
except Exception as e:
    print(e)
    walker.deactivate()
    raise e

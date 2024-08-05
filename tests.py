import time
from logging_ import log

def light_test():
    from hardware import light
    log("Light test")

    for _ in range(3):
        light.fade_in(fade_time=0.5)
        light.fade_out(fade_time=0.5)
        light.turn_off()
    log("Light test done")


async def leg_test():
    from hardware import walker
    log("Leg test")
    for leg in walker.legs:
        for joint in [leg.hip, leg.knee, leg.ankle]:
            for angle in [70, 110, 90]:
                await joint.move(angle)
                time.sleep(0.1)

    log("Leg test done")
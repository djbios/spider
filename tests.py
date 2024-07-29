from hardware import light, walker
import time

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
                joint.move(angle)
                time.sleep(0.2)

    print("Leg test done")
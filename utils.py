import time
from pwmio import PWMOut
from adafruit_motor import servo

def pwm_fade_in_out(pwm_pin, fade_time=0.5, steps=100):
    step_delay = fade_time / steps
    for i in range(steps):
        # Increase the duty cycle for fade in
        pwm_pin.duty_cycle = int((i / steps) * 65535)
        time.sleep(step_delay)
    for i in range(steps, 0, -1):
        # Decrease the duty cycle for fade out
        pwm_pin.duty_cycle = int((i / steps) * 65535)
        time.sleep(step_delay)


class Joint:
    def __init__(self, pin):
        self.pwm = PWMOut(pin, duty_cycle=2 ** 15, frequency=50)
        self.servo = servo.Servo(self.pwm)

    def move(self, angle: float):
        self.servo.angle = angle
        time.sleep(0.05)

class Leg:
    def __init__(self, joint1: Joint, joint2: Joint, joint3: Joint):
        self.joint1 = joint1
        self.joint2 = joint2
        self.joint3 = joint3
    
    def move(self, angle1: float, angle2: float, angle3: float):
        self.joint1.move(angle1)
        self.joint2.move(angle2)
        self.joint3.move(angle3)
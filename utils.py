import time
from pwmio import PWMOut

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


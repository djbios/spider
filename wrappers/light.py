import time
from logging import log


class Light:
    PWM_MAX = 65535

    def __init__(self, pwm):
        self.pwm = pwm
        log("Light initialized")

    def turn_on(self):
        self.pwm.duty_cycle = self.PWM_MAX  # TODO refactor to use a constant

    def turn_off(self):
        self.pwm.duty_cycle = 0

    def fade_in(self, fade_time=0.5):
        step_delay = fade_time / 100
        for i in range(100):
            self.pwm.duty_cycle = int((i / 100) * self.PWM_MAX)
            time.sleep(step_delay)

    def fade_out(self, fade_time=0.5):
        step_delay = fade_time / 100
        for i in range(100, 0, -1):
            self.pwm.duty_cycle = int((i / 100) * self.PWM_MAX)
            time.sleep(step_delay)

    def set_brightness(self, brightness: int):
        """
        :param brightness: Brightness in percentage 0-100
        """
        self.pwm.duty_cycle = int((brightness / 100) * self.PWM_MAX)

    def get_brightness(self):
        return int((self.pwm.duty_cycle / self.PWM_MAX) * 100)
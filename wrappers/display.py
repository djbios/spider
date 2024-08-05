from logging_ import log, get_unsent_loglines
import adafruit_ssd1306
from routines import BaseRoutine, RoutinesRegistry
from collections import deque
import asyncio

class Display(adafruit_ssd1306.SSD1306_I2C):
    MAX_LINES = 3
    MAX_LINE_LENGTH = 21

    MODE_NONE = "None"
    MODE_LOGS = "Logs"
    MODE_STATS = "Stats"

    def __init__(self, width, height, i2c):
        super().__init__(width, height, i2c)
        self.writelines(["", "Initializing..."])
        log("Display initialized")
        self.animation = None
        self.mode = self.MODE_NONE

    def set_animation(self, animation):
        self.animation = animation

    def writelines(self, lines, cut=True):
        # Attention! Slow method
        if cut:
            lines = lines[: self.MAX_LINES]
            for l in lines:
                if len(l) > self.MAX_LINE_LENGTH:
                    l = l[: self.MAX_LINE_LENGTH]
        else:
            assert len(lines) <= 8, "Too many lines"
            assert all(len(line) <= 21 for line in lines), "Line too long"

        self.fill(0)
        for i, line in enumerate(lines):
            self.text(line, 0, i * 10, 1)
        if lines:
            self.show()

    def write_text(self, text):
        lines = text.split("\n")
        self.writelines(lines)

    def set_mode(self, mode):
        self.mode = mode


def register_display_routine(display, battery, wifi, accelerometer):
    @RoutinesRegistry.register()
    class DisplayRoutine(BaseRoutine):
        def __init__(self) -> None:
            self.display = display
            self.logs_deque = deque([], display.MAX_LINES)
            super().__init__()

        async def tick(self):
            if self.display.mode == Display.MODE_LOGS:
                new_lines = get_unsent_loglines("display", count=4)
                if new_lines:
                    self.logs_deque.extend(new_lines)
                    self.display.writelines(list(self.logs_deque))
            elif self.display.mode == Display.MODE_STATS:
                lines = [
                    f"Bat: {battery.get_battery_percentage()}% {battery.get_battery_voltage()}V",
                    f"IP: {wifi.radio.ipv4_address}",
                    f"Accel: {accelerometer.xyz}",
                    f"Angles: {accelerometer.angles}",
                ]
                self.display.writelines(lines)
                await asyncio.sleep(2)

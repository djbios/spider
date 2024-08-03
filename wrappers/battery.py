import analogio
from logging import log

VOLTAGE_MULTIPLIER = 0.0002985503
BATTERY_MAX_VOLTAGE = 12.6
BATTERY_MIN_VOLTAGE = 9.6

class Battery:
    def __init__(self, battery_pin):
        self.adc = analogio.AnalogIn(battery_pin)
        log("Battery initialized")

    def log_battery(self):
        voltage = self.get_battery_voltage()
        percentage = self.get_battery_percentage()

        bar_length = 50  # Length of the progress bar
        filled_length = int(bar_length * percentage // 100)
        bar = "█" * filled_length + "-" * (bar_length - filled_length)

        log(f"\rBattery voltage: {voltage:.2f}V |{bar}| {percentage}%")

    def get_battery_voltage(self) -> float:
        # Convert the analog reading to voltage
        return self.adc.value * VOLTAGE_MULTIPLIER

    def get_battery_percentage(self) -> int:
        voltage = self.get_battery_voltage()
        perc = int(
            (voltage - BATTERY_MIN_VOLTAGE)
            / (BATTERY_MAX_VOLTAGE - BATTERY_MIN_VOLTAGE)
            * 100
        )
        return max(0, min(100, perc))

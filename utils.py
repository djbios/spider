import time
from pwmio import PWMOut
from adafruit_motor import servo
import analogio


VOLTAGE_MULTIPLIER = 0.0002985503
BATTERY_MAX_VOLTAGE = 12.6
BATTERY_MIN_VOLTAGE = 9.6


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


# Define the rainbow colors
rainbow_colors = [
    (255, 0, 0),  # Red
    (255, 127, 0),  # Orange
    (255, 255, 0),  # Yellow
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (75, 0, 130),  # Indigo    (148, 0, 211)   # Violet
]


# Function to interpolate between two colors
def interpolate_color(color1, color2, factor):
    return (
        int(color1[0] + (color2[0] - color1[0]) * factor),
        int(color1[1] + (color2[1] - color1[1]) * factor),
        int(color1[2] + (color2[2] - color1[2]) * factor),
    )

class Battery:
    def __init__(self, battery_pin):
        self.adc = analogio.AnalogIn(battery_pin)
        print("Battery initialized")

    def print_battery(self):
        voltage = self.get_battery_voltage()
        percentage = self.get_battery_percentage()

        bar_length = 50  # Length of the progress bar
        filled_length = int(bar_length * percentage // 100)
        bar = "█" * filled_length + "-" * (bar_length - filled_length)

        print(f"\rBattery voltage: {voltage:.2f}V |{bar}| {percentage}%")


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


class Joint:
    def __init__(self, pin):
        self.pwm = PWMOut(pin, duty_cycle=0, frequency=50)
        self.servo = servo.Servo(self.pwm)
        print(f"Joint initialized with pin {pin}")

    def move(self, angle: float, speed: float = 1.0):
        if self.servo.angle is None:
            self.servo.angle = angle
            return

        if speed == 1:
            self.servo.angle = angle
            return

        current_angle = self.servo.angle
        steps = int(100 * speed)
        step_size = (angle - current_angle) / steps
        for _ in range(steps):
            current_angle += step_size
            self.servo.angle = current_angle
            time.sleep(0.01)
        self.servo.angle = angle


class Leg:
    def __init__(self, hip: Joint, knee: Joint, ankle: Joint):
        self.hip = hip
        self.knee = knee
        self.ankle = ankle
        print("Leg initialized")

    def move(self, hip: float, knee: float, ankle: float, speed: float = 1):
        # TODO make it smoother (interpolate)
        self.hip.move(hip, speed)
        self.knee.move(knee, speed)
        self.ankle.move(ankle, speed)


# Rainbow TODO refactor as a routine
# for i in range(len(rainbow_colors)):
#     start_color = rainbow_colors[i]
#     end_color = rainbow_colors[(i + 1) % len(rainbow_colors)]
#     for j in range(100):  # 100 steps for smooth transition
#         factor = j / 100.0
#         color = interpolate_color(start_color, end_color, factor)
#         pixel.fill(color)
#         time.sleep(0.01)  # Adjust speed of the gradient

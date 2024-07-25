import random
import time
from pwmio import PWMOut
from adafruit_motor import servo
import analogio
from routines import RoutinesRegistry, BaseRoutine
import math
import asyncio

VOLTAGE_MULTIPLIER = 0.0002985503
BATTERY_MAX_VOLTAGE = 12.6
BATTERY_MIN_VOLTAGE = 9.6


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


@RoutinesRegistry.register()
class JointRoutine(BaseRoutine):
    joints = []

    async def tick(self):
        for joint in self.joints:
            joint.tick()


class SmoothServo:
    def __init__(self, pin, min_angle=0, max_angle=180, default_angle=90):
        """
        :param pin: PWM pin
        :param min_angle: Minimum angle, physical limit
        :param max_angle: Maximum angle, physical limit
        :param default_angle: Default angle, starting position
        """
        self.pwm = PWMOut(pin, duty_cycle=0, frequency=50)
        self.servo = servo.Servo(self.pwm)
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.current_angle = default_angle
        self.target_angle = default_angle
        self.speed = 0  # Initial speed
        self.max_speed = 1
        self.acceleration = 1
        self.tick_flag = False
        self.last_update_time = time.monotonic()
        self.servo.angle = self.current_angle

    def set_speed(self, max_speed):
        """
        :param max_speed: Maximum speed of the servo in degrees per second"""
        self.max_speed = max_speed

    def set_acceleration(self, acceleration):
        """
        :param acceleration: Acceleration of the servo in degrees per second squared
        """
        self.acceleration = acceleration

    def set_target(self, target_angle):
        """
        :param target_angle: Target angle for the servo in degrees
        """
        self.target_angle = max(self.min_angle, min(self.max_angle, target_angle))

    def tick(self):
        """
        Should be called in a loop to update the servo position
        """
        current_time = time.monotonic()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time

        err = self.target_angle - self.current_angle
        if abs(err) > 0.1:
            deceleration_distance = (self.speed * self.speed) / (2 * self.acceleration)
            if deceleration_distance >= abs(err):
                self.speed -= self.acceleration * delta_time * self._sign(self.speed)
            else:
                self.speed += self.acceleration * delta_time * self._sign(err)

            self.speed = max(-self.max_speed, min(self.max_speed, self.speed))
            self.current_angle += self.speed * delta_time
            self.servo.angle = self.current_angle
        else:
            self.stop()

    def _sign(self, value):
        if value > 0:
            return 1
        elif value < 0:
            return -1
        else:
            return 0

    def start(self):
        self.tick_flag = True
        self.last_update_time = time.monotonic()

    def stop(self):
        self.tick_flag = False


class Joint(SmoothServo):
    def __init__(self, pin):
        super().__init__(pin)
        JointRoutine.joints.append(self)
        print("Joint initialized")


    async def move_and_wait(self, angle):
        print(f"Moving to {angle}")
        self.set_target(angle)
        self.start()
        while self.tick_flag:
            await asyncio.sleep(0.01)


class Leg:
    def __init__(self, hip: Joint, knee: Joint, ankle: Joint):
        self.hip = hip
        self.knee = knee
        self.ankle = ankle
        print("Leg initialized")

    def move(
        self,
        hip: float,
        knee: float,
        ankle: float,
        max_speed: float = 1.0,
        max_acceleration: float = 0.1,
    ):
        # TODO make it smoother (interpolate)
        self.hip.move(hip, max_speed, max_acceleration)
        self.knee.move(knee, max_speed, max_acceleration)
        self.ankle.move(ankle, max_speed, max_acceleration)


class Walker:
    def __init__(self, leg1, leg2, leg3, leg4):
        self.leg1 = leg1
        self.leg2 = leg2
        self.leg3 = leg3
        self.leg4 = leg4
        self.legs = [leg1, leg2, leg3, leg4]
        print("Walker initialized")

    # def wiggle(
    #     self, movements=100, max_speed: float = 1.0, max_acceleration: float = 0.1
    # ):
    #     print("Wiggle")

    #     for _ in range(movements):
    #         joint_name = random.choice(["hip", "knee", "ankle"])
    #         angle = random.randint(70, 110)
    #         for leg in self.legs:
    #             getattr(leg, joint_name).move(angle, max_speed, max_acceleration)
    #         time.sleep(0.1)
    #     self.to_zero()
    #     print("Wiggle done")

    # def to_zero(self):
    #     print("To zero")
    #     for leg in self.legs:
    #         leg.move(90, 90, 90)
    #     print("To zero done")


class Light:
    def __init__(self, pwm):
        self.pwm = pwm
        print("Light initialized")

    def turn_on(self):
        self.pwm.duty_cycle = 65535
        print("Light on")

    def turn_off(self):
        self.pwm.duty_cycle = 0
        print("Light off")

    def fade_in(self, fade_time=0.5):
        step_delay = fade_time / 100
        for i in range(100):
            self.pwm.duty_cycle = int((i / 100) * 65535)
            time.sleep(step_delay)

    def fade_out(self, fade_time=0.5):
        step_delay = fade_time / 100
        for i in range(100, 0, -1):
            self.pwm.duty_cycle = int((i / 100) * 65535)
            time.sleep(step_delay)


# Rainbow TODO refactor as a routine
# for i in range(len(rainbow_colors)):
#     start_color = rainbow_colors[i]
#     end_color = rainbow_colors[(i + 1) % len(rainbow_colors)]
#     for j in range(100):  # 100 steps for smooth transition
#         factor = j / 100.0
#         color = interpolate_color(start_color, end_color, factor)
#         pixel.fill(color)
#         time.sleep(0.01)  # Adjust speed of the gradient

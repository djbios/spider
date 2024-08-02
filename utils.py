import random
import time
from adafruit_motor import servo
import analogio
from routines import RoutinesRegistry, BaseRoutine
import asyncio
from adafruit_pca9685 import PWMChannel
import adafruit_adxl34x
import math
from flash_storage import storage
from logging import log
import adafruit_ssd1306

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


@RoutinesRegistry.register()
class JointRoutine(BaseRoutine):
    joints = []

    async def tick(self):
        for joint in self.joints:
            joint.tick()


class SmoothServo:
    def __init__(self, pwm: PWMChannel, min_angle=0, max_angle=180, default_angle=90):
        """
        :param pin: PWM pin
        :param min_angle: Minimum angle, physical limit
        :param max_angle: Maximum angle, physical limit
        :param default_angle: Default angle, starting position
        """
        self.pwm = pwm
        self._servo = servo.Servo(self.pwm)
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.current_angle = default_angle
        self.target_angle = default_angle
        self.speed = 0  # Initial speed
        self.max_speed = 1
        self.acceleration = 1
        self.last_update_time = time.monotonic()
        self.mid_angle = 90
        self.current_movement = None
        self.set_servo_angle(self.current_angle)

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

            step = self.speed * delta_time
            next_angle = self.current_angle + step

            # Check that we not overshoot the target
            movement_from, movement_to = self.current_movement
            if movement_from < movement_to:
                if next_angle > movement_to:
                    next_angle = movement_to
            else:
                if next_angle < movement_to:
                    next_angle = movement_to

            assert (
                self.min_angle <= next_angle <= self.max_angle
            ), f"Angle out of bounds: {next_angle}, {step}, {err}, {self.target_angle}, {self.current_angle}"

            self.current_angle = next_angle
            self.set_servo_angle(next_angle)
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
        self.current_movement = (self.current_angle, self.target_angle)
        self.last_update_time = time.monotonic()

    def stop(self):
        self.current_movement = None

    def deactivate(self):
        self.stop()
        self._servo._pwm.duty_cycle = 0

    def hard_move(self, angle):
        self.set_servo_angle(angle)

    def set_servo_angle(self, angle):
        calibrated_angle = angle + self.mid_angle - 90
        self._servo.angle = calibrated_angle

    def apply_calibration(self, mid_angle):
        self.mid_angle = mid_angle
        self.set_servo_angle(self.current_angle)


class Joint(SmoothServo):
    def __init__(self, channel: PWMChannel, speed, acceleration):
        super().__init__(channel)
        JointRoutine.joints.append(self)
        self.set_speed(speed)
        self.set_acceleration(acceleration)
        log("Joint initialized")

    async def move(self, angle):
        self.set_target(angle)
        self.start()
        while self.current_movement:
            await asyncio.sleep(0.01)


class Leg:
    def __init__(self, hip: Joint, knee: Joint, ankle: Joint):
        self.hip = hip
        self.knee = knee
        self.ankle = ankle
        log("Leg initialized")

    async def move(
        self,
        hip: float,
        knee: float,
        ankle: float,
    ):
        tasks = []
        tasks.append(self.hip.move(hip))
        tasks.append(self.knee.move(knee))
        tasks.append(self.ankle.move(ankle))

        await asyncio.gather(*tasks)


class Walker:
    def __init__(self, leg1: Leg, leg2: Leg, leg3: Leg, leg4: Leg):
        self.leg1 = leg1
        self.leg2 = leg2
        self.leg3 = leg3
        self.leg4 = leg4
        self.legs = [leg1, leg2, leg3, leg4]
        log("Walker initialized")

    async def wiggle(self, movements=10):
        log("Wiggle")

        for _ in range(movements):
            tasks = []
            for leg in self.legs:
                tasks.append(
                    leg.move(
                        random.randint(80, 100),
                        random.randint(80, 100),
                        random.randint(80, 100),
                    )
                )

            await asyncio.gather(*tasks)

    def deactivate(self):
        for leg in self.legs:
            for joint in [leg.hip, leg.knee, leg.ankle]:
                joint.deactivate()

        self.to_zero()
        log("Wiggle done")

    async def to_zero(self):
        log("To zero")
        for leg in self.legs:
            await leg.move(90, 90, 90)
        log("To zero done")

    def apply_calibration(self, values: dict[str, dict[str, int]]):
        for i, leg in enumerate(self.legs, start=1):
            for joint_name in ["hip", "knee", "ankle"]:
                joint = getattr(leg, joint_name)
                joint.apply_calibration(values[f"leg{i}"][joint_name])
        log("Calibration applied")

    def find_hard_limits(walker):
        import json

        hard_limits_config = {}
        for i, leg in enumerate(walker.legs):
            for joint_name in ["hip", "knee", "ankle"]:
                log(f"Finding hard limits for leg {i} {joint_name}")
                joint = getattr(leg, joint_name)

                log(f"Find max for leg {i} {joint_name}")
                current_angle = 90
                while True:
                    try:
                        current_angle = current_angle + 1
                        joint.hard_move(current_angle)
                        time.sleep(0.1)
                    except (KeyboardInterrupt, ValueError):
                        break
                hard_limits_config[f"leg_{i}_{joint_name}_max"] = current_angle

                log(f"Find min for leg {i} {joint_name}")
                current_angle = 90

                while True:
                    try:
                        current_angle = current_angle - 1
                        joint.hard_move(current_angle)
                        time.sleep(0.1)
                    except (KeyboardInterrupt, ValueError):
                        break
                hard_limits_config[f"leg_{i}_{joint_name}_min"] = current_angle
                joint.hard_move(90)

        log(json.dumps(hard_limits_config))

    def apply_hard_limits(self, hard_limits_dict: dict[str, int]):
        for i, leg in enumerate(self.legs):
            for joint_name in ["hip", "knee", "ankle"]:
                joint = getattr(leg, joint_name)
                joint.min_angle = hard_limits_dict[f"leg_{i}_{joint_name}_min"]
                joint.max_angle = hard_limits_dict[f"leg_{i}_{joint_name}_max"]
        log("Hard limits set")

    async def set_servos(
            self,
            leg1_hip: int,
            leg1_knee: int,
            leg1_ankle: int,
            leg2_hip: int,
            leg2_knee: int,
            leg2_ankle: int,
            leg3_hip: int,
            leg3_knee: int,
            leg3_ankle: int,
            leg4_hip: int,
            leg4_knee: int,
            leg4_ankle: int,
            hard=False, # TODO
    ):
        if hard:
            method = "hard_move"
        else:
            method = "move"

        await run_callable_async_or_not(getattr(self.leg1.hip, method), angle=leg1_hip)
        await run_callable_async_or_not(getattr(self.leg1.knee, method), angle=leg1_knee)
        await run_callable_async_or_not(getattr(self.leg1.ankle, method), angle=leg1_ankle)

        await run_callable_async_or_not(getattr(self.leg2.hip, method), angle=leg2_hip)
        await run_callable_async_or_not(getattr(self.leg2.knee, method), angle=leg2_knee)
        await run_callable_async_or_not(getattr(self.leg2.ankle, method), angle=leg2_ankle)

        await run_callable_async_or_not(getattr(self.leg3.hip, method), angle=leg3_hip)
        await run_callable_async_or_not(getattr(self.leg3.knee, method), angle=leg3_knee)
        await run_callable_async_or_not(getattr(self.leg3.ankle, method), angle=leg3_ankle)

        await run_callable_async_or_not(getattr(self.leg4.hip, method), angle=leg4_hip)
        await run_callable_async_or_not(getattr(self.leg4.knee, method), angle=leg4_knee)
        await run_callable_async_or_not(getattr(self.leg4.ankle, method), angle=leg4_ankle)
        

    def save_position(self, name: str):
        storage['saved_positions'] = storage.get('saved_positions', {})
        storage['saved_positions'][name] = {
            'leg1_hip': self.leg1.hip.current_angle,
            'leg1_knee': self.leg1.knee.current_angle,
            'leg1_ankle': self.leg1.ankle.current_angle,
            'leg2_hip': self.leg2.hip.current_angle,
            'leg2_knee': self.leg2.knee.current_angle,
            'leg2_ankle': self.leg2.ankle.current_angle,
            'leg3_hip': self.leg3.hip.current_angle,
            'leg3_knee': self.leg3.knee.current_angle,
            'leg3_ankle': self.leg3.ankle.current_angle,
            'leg4_hip': self.leg4.hip.current_angle,
            'leg4_knee': self.leg4.knee.current_angle,
            'leg4_ankle': self.leg4.ankle.current_angle,
        }
    
    async def load_position(self, name: str, hard=False):
        saved_positions = storage.get('saved_positions', {})
        position = saved_positions.get(name)
        if position:
            await self.set_servos(**position, hard=hard)
            log(f"Position {name} loaded")
        else:
            log(f"Position {name} not found")

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


class Accelerometr(adafruit_adxl34x.ADXL345):
    def __init__(self, i2c):
        super().__init__(i2c)
        self.zero_x = 0
        self.zero_y = 0
        self.zero_z = 0
        self.load_calibration()
        log("Accelerometer initialized")

    @property
    def xyz(self) -> tuple[float, float, float]:
        x, y, z = self.acceleration
        x -= self.zero_x
        y -= self.zero_y
        z -= self.zero_z
        return x, y, z

    def log_xyz(self):
        x, y, z = self.xyz
        log(f"x: {x}, y: {y}, z: {z}")

    def log_xyz_cycle(self, period=0.5):
        while True:
            self.log_xyz()
            time.sleep(period)

    @property
    def angles(self):
        x, y, z = self.xyz
        pitch = -1 * math.atan2(x, math.sqrt(y**2 + z**2)) * 180 / math.pi
        roll = math.atan2(y, z) * 180 / math.pi
        return pitch, roll

    def log_angles(self):
        pitch, roll = self.angles
        log(f"Pitch: {pitch}, Roll: {roll}")

    def log_angles_cycle(self, period=0.5):
        while True:
            self.log_angles()
            time.sleep(period)

    def calibrate_zero(self):
        log("Calibrating zero...")
        initial_x, initial_y, initial_z = self.acceleration
        self.zero_x = initial_x
        self.zero_y = initial_y
        self.zero_z = (
            initial_z - 9.81
        )  # Assuming the z-axis reads gravitational acceleration
        self.store_calibration()
        log("Calibration complete.")
        log(f"Offsets - X: {self.zero_x}, Y: {self.zero_y}, Z: {self.zero_z}")
        log(f"Values after calibration: {self.xyz}")

    def store_calibration(self):
        storage["accelerometer"] = {
            "zero_x": self.zero_x,
            "zero_y": self.zero_y,
            "zero_z": self.zero_z,
        }
        log("Calibration stored.")

    def load_calibration(self):
        calibration = storage.get("accelerometer")
        if calibration:
            self.zero_x = calibration["zero_x"]
            self.zero_y = calibration["zero_y"]
            self.zero_z = calibration["zero_z"]
            log("Calibration loaded.")


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


async def run_callable_async_or_not(callable, *args, **kwargs):
    """Run a callable that may be async or not."""
    try:
        await callable(*args, **kwargs)
    except AttributeError as e:  # The only way I found to identify its not async
        if "__await__" in str(e):
            try:
                callable(*args, **kwargs)
            except Exception as e:
                log(f"❌ Command failed: {e}")
        else:
            log(f"❌ Command failed: {e}")

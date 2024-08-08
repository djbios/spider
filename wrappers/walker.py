from collections import namedtuple
import random
import time
from adafruit_motor import servo
from routines import RoutinesRegistry, BaseRoutine
import asyncio
from adafruit_pca9685 import PWMChannel
from flash_storage import storage
from logging_ import log

from utils import run_callable_async_or_not
import math


class SmoothServo:
    def __init__(self, pwm: PWMChannel, min_angle=0, max_angle=180, default_angle=90):
        """
        :param pin: PWM pin
        :param min_angle: Minimum angle, physical limit
        :param max_angle: Maximum angle, physical limit
        :param default_angle: Default angle, starting position
        """
        self.pwm = pwm
        self._servo = servo.Servo(
            self.pwm, actuation_range=200
        )  # 200 just to disable their range check, we do it ourselves
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.current_angle = default_angle
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
        self.current_movement = (self.current_angle, target_angle)
        self.last_update_time = time.monotonic()

    def tick(self):
        """
        Should be called in a loop to update the servo position
        """
        if not self.current_movement:
            return
        current_time = time.monotonic()
        movement_from, movement_to = self.current_movement
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time

        err = movement_to - self.current_angle
        if abs(err) > 0.1:
            this_dir = self.speed**2 / self.acceleration / 2.0 >= abs(err)  # Time to decelerate
            self.speed += self.acceleration * delta_time * (-1 if this_dir else 1) * (1 if err > 0 else -1)
            self.speed = max(-self.max_speed, min(self.speed, self.max_speed))

            step = self.speed * delta_time

            # Crazy stupid workaround but I have no idea
            if movement_from < movement_to:
                if step < 0:
                    step = -step
            else:
                if step > 0:
                    step = -step

            next_angle = self.current_angle + step
            # Check that we not overshoot the target
            if movement_from < movement_to:
                if next_angle > movement_to:
                    next_angle = movement_to
            else:
                if next_angle < movement_to:
                    next_angle = movement_to

            assert self.min_angle <= next_angle <= self.max_angle, "\n".join(
                [
                    "Angle out of bounds. ",
                    f"Current angle: {self.current_angle},",
                    f"Step: {step},",
                    f"Next angle: {next_angle},",
                    f"Speed: {self.speed},",
                    f"Acceleration: {self.acceleration},",
                    f"Delta time: {delta_time},",
                    f"Movement: {self.current_movement}",
                    f"Max angle: {self.max_angle}",
                    f"Min angle: {self.min_angle}",
                ]
            )

            self.current_angle = next_angle
            self.set_servo_angle(next_angle)
        else:
            self.current_movement = None

    def deactivate(self):
        self.current_movement = None
        self._servo._pwm.duty_cycle = 0

    def hard_move(self, angle):
        self.set_servo_angle(angle)
        self.current_angle = angle

    def set_servo_angle(self, angle):
        if angle < self.min_angle:
            print(f"Target angle {angle} is less than min angle {self.min_angle}")
            return
        if angle > self.max_angle:
            print(f"Target angle {angle} is more than max angle {self.max_angle}")
            return
        calibrated_angle = angle + self.mid_angle - 90
        self._servo.angle = calibrated_angle

    def apply_calibration(self, mid_angle):
        self.mid_angle = mid_angle
        self.set_servo_angle(self.current_angle)


@RoutinesRegistry.register()
class JointRoutine(BaseRoutine):
    joints = []

    async def tick(self):
        for joint in self.joints:
            joint.tick()


class Joint(SmoothServo):
    def __init__(self, channel: PWMChannel, speed, acceleration):
        super().__init__(channel)
        JointRoutine.joints.append(self)
        self.set_speed(speed)
        self.set_acceleration(acceleration)
        log("Joint initialized")

    async def move(self, angle):
        if angle < self.min_angle:
            print(f"Target angle {angle} is less than min angle {self.min_angle}")
            return
        if angle > self.max_angle:
            print(f"Target angle {angle} is more than max angle {self.max_angle}")
            return
        if angle == self.current_angle:
            return

        while self.current_movement:
            await asyncio.sleep(0.01)  # Wait for the previous movement to finish

        print(f"Move to {angle}")
        self.set_target(angle)
        while self.current_movement:
            await asyncio.sleep(0.01)


KEEP = object()
# Constants for the robot's physical dimensions
length_a = 55
length_b = 77.5
length_c = 27.5
length_side = 71
z_absolute = -28

# Constants for movement
z_default = -50
z_up = -30
z_boot = z_absolute
x_default = 62
x_offset = 0
y_start = 0
y_step = 40
y_default = x_default

# Movement speeds
spot_turn_speed = 4
leg_move_speed = 8
body_move_speed = 3
stand_seat_speed = 1


class Leg:
    def __init__(self, hip: Joint, knee: Joint, ankle: Joint, id):
        self.hip = hip
        self.knee = knee
        self.ankle = ankle
        self.id = id
        self.x = 0
        self.y = 0
        self.z = 0

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

    def set_site(self, x, y, z):
        print(f"Set site: {x=}, {y=}, {z=}")
        alpha, beta, gamma = self.get_servo_angles_for_linear_coords(x, y, z)
        print(f"Angles: {alpha=}, {beta=}, {gamma=}")
        self.hip.hard_move(gamma)
        self.knee.hard_move(beta)
        self.ankle.hard_move(alpha)
        self.x = x
        self.y = y
        self.z = z

    def get_servo_angles_for_linear_coords(self, x, y, z):
        alpha, beta, gamma = self.cartesian_to_polar(x, y, z)
        return self.polar_to_servo(beta, alpha, gamma)

    def cartesian_to_polar(self, x, y, z):
        w = (x >= 0 and 1 or -1) * math.sqrt(x**2 + y**2)
        v = w - length_c
        alpha = math.atan2(z, v) + math.acos(
            (length_a**2 - length_b**2 + v**2 + z**2) / (2 * length_a * math.sqrt(v**2 + z**2))
        )
        beta = math.acos((length_a**2 + length_b**2 - v**2 - z**2) / (2 * length_a * length_b))
        gamma = math.atan2(y, x) if w >= 0 else math.atan2(-y, -x)

        alpha = alpha / math.pi * 180
        beta = beta / math.pi * 180
        gamma = gamma / math.pi * 180

        return alpha, beta, gamma

    def polar_to_servo(self, alpha, beta, gamma):
        if self.id == 1:
            alpha = 90 - alpha
            beta = beta
            gamma += 90
        elif self.id == 2:
            alpha += 90
            beta = 180 - beta
            gamma = 90 - gamma
        elif self.id == 3:
            alpha += 90
            beta = 180 - beta
            gamma = 90 - gamma
        elif self.id == 4:
            alpha = 90 - alpha
            beta = beta
            gamma += 90
        return alpha, beta, gamma

    def linear_test(self):
        """Test the linear movement of the leg
        Move the leg in a linear path in the x, y, and z directions
        """
        self.set_site(self.x + 10, self.y, self.z)
        time.sleep(1)
        self.set_site(self.x - 20, self.y, self.z)
        time.sleep(1)
        self.set_site(self.x + 10, self.y, self.z)

        self.set_site(self.x, self.y + 10, self.z)
        time.sleep(1)
        self.set_site(self.x, self.y - 20, self.z)
        time.sleep(1)
        self.set_site(self.x, self.y + 10, self.z)

        self.set_site(self.x, self.y, self.z + 10)
        time.sleep(1)
        self.set_site(self.x, self.y, self.z - 20)
        time.sleep(1)
        self.set_site(self.x, self.y, self.z + 10)

    # async def move_linear(self, dx: float, dy: float, dz: float):
    #     leg_config = self.leg_config
    #     initial_x = self.x
    #     initial_y = self.y
    #     initial_z = self.z

    #     hip_angle, knee_angle, ankle_angle = linear_move_to_angles(
    #         leg_config, initial_x, initial_y, initial_z, dx, dy, dz
    #     )

    #     self.x = dx
    #     self.y = dy
    #     self.z = dz
    #     self.move(hip_angle, knee_angle, ankle_angle)


# LegConfig = namedtuple("LegConfig", ["hip_sign", "knee_sign", "ankle_sign", "is_left"])


# def linear_move_to_angles(
#     leg_config: LegConfig,
#     initial_x: float,
#     initial_y: float,
#     initial_z: float,
#     initial_hip_angle: int,
#     initial_knee_angle: int,
#     initial_ankle_angle: int,
#     x_abs: float,
#     y_abs: float,
#     z_abs: float,
#     lc: float,
#     lf: float,
#     lt: float,
# ) -> tuple[int, int, int]:
#     from math import acos, cos, sin, pi, sqrt, degrees

#     # Diffs of angles relative to the zero position
#     hip_angle0 = (initial_hip_angle - 90) * leg_config.hip_sign
#     knee_angle0 = (initial_knee_angle - 90) * leg_config.knee_sign
#     ankle_angle0 = (initial_ankle_angle - 90) * leg_config.ankle_sign
#     print(f"{hip_angle0=}, {knee_angle0=}, {ankle_angle0=}")

#     dx = (x_abs - initial_x) * (1 if leg_config.is_left else -1)
#     dy = y_abs - initial_y
#     dz = z_abs - initial_z
#     print(f"{dx=}, {dy=}, {dz=}")

#     # Coords of calcaneus in new coordinate system (with zero in hip joint)
#     x0 = (
#         lc + lf * cos(knee_angle0) + lt * sin(knee_angle0 + ankle_angle0)
#     ) * sin(hip_angle0)
#     y0 = (
#         lc + lf * cos(knee_angle0) + lt * sin(knee_angle0 + ankle_angle0)
#     ) * cos(hip_angle0)
#     z0 = lf * sin(knee_angle0) + lt * cos(knee_angle0 + ankle_angle0)

#     print(f"x0: {x0}, y0: {y0}, z0: {z0}")

#     # Calculate hip rotation
#     # Coords of calcaneus in new coordinate system (with zero in hip joint)
#     xn = x0 + dx
#     yn = y0 + dy
#     zn = z0 + dz

#     print(f"xn: {xn}, yn: {yn}, zn: {zn}")
#     if dx == 0 and dy == 0:
#         d_alfa_coxa = 0
#     else:
#         d_alfa_coxa = acos(
#             (x0 * xn + y0 * yn) / (sqrt(x0**2 + y0**2) * sqrt(xn**2 + yn**2))
#         )

#     d_alfa_coxa_degrees = degrees(d_alfa_coxa) * leg_config.hip_sign

#     print(f"d_alfa_coxa: {d_alfa_coxa_degrees}")

#     # Calculate knee and ankle rotation
#     x1 = x0
#     y1 = y0
#     z1 = z0
#     print(f"x1: {x1}, y1: {y1}, z1: {z1}")

#     xn1 = xn * cos(d_alfa_coxa) - yn * sin(d_alfa_coxa)
#     yn1 = xn * sin(d_alfa_coxa) + yn * cos(d_alfa_coxa)
#     zn1 = zn
#     print(f"xn1: {xn1}, yn1: {yn1}, zn1: {zn1}")

#     d_alfa = acos(
#         (y1 * yn1 + z1 * zn1) / (sqrt(y1**2 + z1**2) * sqrt(yn1**2 + zn1**2))
#     )
#     # d_range = sqrt(yn1**2 + zn1**2) - sqrt(y1**2 + z1**2)
#     d_range = yn1 - y1

#     print(f"{d_alfa=}, {d_range=}")


# print(f"{d_knee1_degrees=}, {d_ankle1_degrees=}")
# print(f"{d_knee2_degrees=}, {d_ankle2_degrees=}")

# alfa_coxa = math.acos(
#     (dx * initial_x + dy * initial_y)
#     / (math.sqrt(initial_x**2 + initial_y**2) * math.sqrt(dx**2 + dy**2))
# )
# hip = initial_hip_angle + alfa_coxa

# return hip, ..., ...


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

    def apply_calibration(self, values: dict[str, int]):
        for i, leg in enumerate(self.legs, start=1):
            for joint_name in ["hip", "knee", "ankle"]:
                joint = getattr(leg, joint_name)
                value = values[f"leg{i}_{joint_name}"]
                joint.apply_calibration(value)
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

    async def set_servos_angles(
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
        hard=False,  # TODO
    ):
        if hard:
            method = "hard_move"
        else:
            method = "move"
        # OMG this ugly
        coroutines = [
            run_callable_async_or_not(getattr(self.leg1.hip, method), angle=leg1_hip),
            run_callable_async_or_not(getattr(self.leg1.knee, method), angle=leg1_knee),
            run_callable_async_or_not(getattr(self.leg1.ankle, method), angle=leg1_ankle),
            run_callable_async_or_not(getattr(self.leg2.hip, method), angle=leg2_hip),
            run_callable_async_or_not(getattr(self.leg2.knee, method), angle=leg2_knee),
            run_callable_async_or_not(getattr(self.leg2.ankle, method), angle=leg2_ankle),
            run_callable_async_or_not(getattr(self.leg3.hip, method), angle=leg3_hip),
            run_callable_async_or_not(getattr(self.leg3.knee, method), angle=leg3_knee),
            run_callable_async_or_not(getattr(self.leg3.ankle, method), angle=leg3_ankle),
            run_callable_async_or_not(getattr(self.leg4.hip, method), angle=leg4_hip),
            run_callable_async_or_not(getattr(self.leg4.knee, method), angle=leg4_knee),
            run_callable_async_or_not(getattr(self.leg4.ankle, method), angle=leg4_ankle),
        ]
        await asyncio.gather(*[asyncio.create_task(c) for c in coroutines])

    def get_servos_angles(self) -> dict[str, int]:
        return {
            "leg1_hip": self.leg1.hip.current_angle,
            "leg1_knee": self.leg1.knee.current_angle,
            "leg1_ankle": self.leg1.ankle.current_angle,
            "leg2_hip": self.leg2.hip.current_angle,
            "leg2_knee": self.leg2.knee.current_angle,
            "leg2_ankle": self.leg2.ankle.current_angle,
            "leg3_hip": self.leg3.hip.current_angle,
            "leg3_knee": self.leg3.knee.current_angle,
            "leg3_ankle": self.leg3.ankle.current_angle,
            "leg4_hip": self.leg4.hip.current_angle,
            "leg4_knee": self.leg4.knee.current_angle,
            "leg4_ankle": self.leg4.ankle.current_angle,
        }

    def save_position(self, name: str):
        storage["saved_positions"] = storage.get("saved_positions", {})
        storage["saved_positions"][name] = self.get_servos_angles()

    async def load_position(self, name: str, hard=False):
        saved_positions = storage.get("saved_positions", {})
        position = saved_positions.get(name)
        if position:
            await self.set_servos_angles(**position, hard=hard)
            log(f"Position {name} loaded")
        else:
            log(f"Position {name} not found")

    def get_saved_positions(self):
        return storage.get("saved_positions", {})

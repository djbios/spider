import random
import time
from adafruit_motor import servo
from routines import RoutinesRegistry, BaseRoutine
import asyncio
from adafruit_pca9685 import PWMChannel
from flash_storage import storage
from logging import log

from utils import run_callable_async_or_not




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
        self.target_angle = target_angle

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

        err = self.target_angle - self.current_angle
        if abs(err) > 0.1:
            this_dir = self.speed**2 / self.acceleration / 2.0 >= abs(
                err
            )  # Time to decelerate
            self.speed += (
                self.acceleration
                * delta_time
                * (-1 if this_dir else 1)
                * (1 if err > 0 else -1)
            )
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
            run_callable_async_or_not(
                getattr(self.leg1.ankle, method), angle=leg1_ankle
            ),
            run_callable_async_or_not(getattr(self.leg2.hip, method), angle=leg2_hip),
            run_callable_async_or_not(getattr(self.leg2.knee, method), angle=leg2_knee),
            run_callable_async_or_not(
                getattr(self.leg2.ankle, method), angle=leg2_ankle
            ),
            run_callable_async_or_not(getattr(self.leg3.hip, method), angle=leg3_hip),
            run_callable_async_or_not(getattr(self.leg3.knee, method), angle=leg3_knee),
            run_callable_async_or_not(
                getattr(self.leg3.ankle, method), angle=leg3_ankle
            ),
            run_callable_async_or_not(getattr(self.leg4.hip, method), angle=leg4_hip),
            run_callable_async_or_not(getattr(self.leg4.knee, method), angle=leg4_knee),
            run_callable_async_or_not(
                getattr(self.leg4.ankle, method), angle=leg4_ankle
            ),
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
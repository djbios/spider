import time
import adafruit_adxl34x
import math
from flash_storage import storage
from logging import log


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

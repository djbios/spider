import pins
from utils import Battery, Joint, Leg, Light, Walker, Accelerometr, Storage
import pwmio
import busio
from adafruit_pca9685 import PCA9685


DEFAULT_SPEED = 1000
DEFAULT_ACCELERATION = 1000

WALKER_CALIBRATION_ANGLES = {
    "leg1": {
        "hip": 105,
        "knee": 95,
        "ankle": 85,
    },
    "leg2": {
        "hip": 95,
        "knee": 105,
        "ankle": 85,
    },
    "leg3": {
        "hip": 100,
        "knee": 90,
        "ankle": 90,
    },
    "leg4": {
        "hip": 102,
        "knee": 90,
        "ankle": 105,
    },
}

WALKER_CALIBRATED_HARD_LIMITS = {
    "leg_3_knee_min": 0,
    "leg_0_knee_max": 176,
    "leg_1_ankle_min": 13,
    "leg_2_ankle_min": 0,
    "leg_2_ankle_max": 179,
    "leg_1_hip_max": 176,
    "leg_3_hip_min": 49,
    "leg_3_hip_max": 169,
    "leg_2_knee_max": 181,
    "leg_3_ankle_max": 166,
    "leg_1_hip_min": 39,
    "leg_0_knee_min": 15,
    "leg_3_knee_max": 141,
    "leg_1_knee_min": 0,
    "leg_0_ankle_max": 177,
    "leg_3_ankle_min": 0,
    "leg_2_hip_min": -11,
    "leg_0_ankle_min": 4,
    "leg_0_hip_min": 0,
    "leg_1_knee_max": 142,
    "leg_0_hip_max": 129,
    "leg_2_hip_max": 139,
    "leg_2_knee_min": 45,
    "leg_1_ankle_max": 186,
}


i2c = busio.I2C(pins.I2C_SCL, pins.I2C_SDA)
pca = PCA9685(i2c)
pca.frequency = 50
pca.reference_clock_speed = 2.82337e07

leg1_ankle_ch = pca.channels[9]
leg1_knee_ch = pca.channels[10]
leg1_hip_ch = pca.channels[11]

leg2_ankle_ch = pca.channels[3]
leg2_knee_ch = pca.channels[2]
leg2_hip_ch = pca.channels[1]

leg3_ankle_ch = pca.channels[5]
leg3_knee_ch = pca.channels[6]
leg3_hip_ch = pca.channels[7]

leg4_ankle_ch = pca.channels[13]
leg4_knee_ch = pca.channels[14]
leg4_hip_ch = pca.channels[15]

walker = Walker(
    leg1=Leg(
        hip=Joint(leg1_hip_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        knee=Joint(leg1_knee_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        ankle=Joint(leg1_ankle_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
    ),
    leg2=Leg(
        hip=Joint(leg2_hip_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        knee=Joint(leg2_knee_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        ankle=Joint(leg2_ankle_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
    ),
    leg3=Leg(
        hip=Joint(leg3_hip_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        knee=Joint(leg3_knee_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        ankle=Joint(leg3_ankle_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
    ),
    leg4=Leg(
        hip=Joint(leg4_hip_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        knee=Joint(leg4_knee_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        ankle=Joint(leg4_ankle_ch, DEFAULT_SPEED, DEFAULT_ACCELERATION),
    ),
)
walker.apply_calibration(WALKER_CALIBRATION_ANGLES)
walker.apply_hard_limits(WALKER_CALIBRATED_HARD_LIMITS)

light = Light(pwmio.PWMOut(pins.LED_STRIP))

battery = Battery(pins.BATTERY_ADC)

accelerometer = Accelerometr(i2c)

storage = Storage()

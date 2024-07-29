import pins
from utils import Battery, Joint, Leg, Light, Walker
import pwmio

DEFAULT_SPEED = 1000
DEFAULT_ACCELERATION = 1000

walker = Walker(
    leg1=Leg(
        hip=Joint(pins.LEG1_HIP, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        knee=Joint(pins.LEG1_KNEE, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        ankle=Joint(pins.LEG1_ANKLE, DEFAULT_SPEED, DEFAULT_ACCELERATION),
    ),
    leg2=Leg(
        hip=Joint(pins.LEG2_HIP, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        knee=Joint(pins.LEG2_KNEE, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        ankle=Joint(pins.LEG2_ANKLE, DEFAULT_SPEED, DEFAULT_ACCELERATION),
    ),
    leg3=Leg(
        hip=Joint(pins.LEG3_HIP, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        knee=Joint(pins.LEG3_KNEE, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        ankle=Joint(pins.LEG3_ANKLE, DEFAULT_SPEED, DEFAULT_ACCELERATION),
    ),
    leg4=Leg(
        hip=Joint(pins.LEG4_HIP, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        knee=Joint(pins.LEG4_KNEE, DEFAULT_SPEED, DEFAULT_ACCELERATION),
        ankle=Joint(pins.LEG4_ANKLE, DEFAULT_SPEED, DEFAULT_ACCELERATION),
    ),
)
light = Light(pwmio.PWMOut(pins.LED_STRIP))

battery = Battery(pins.BATTERY_ADC)

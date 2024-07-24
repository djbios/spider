import pins
from utils import Battery, Joint, Leg, Light, Walker
import pwmio

walker = Walker(
    leg1=Leg(
        hip=Joint(pins.LEG1_HIP),
        knee=Joint(pins.LEG1_KNEE),
        ankle=Joint(pins.LEG1_ANKLE),
    ),
    leg2=Leg(
        hip=Joint(pins.LEG2_HIP),
        knee=Joint(pins.LEG2_KNEE),
        ankle=Joint(pins.LEG2_ANKLE),
    ),
    leg3=Leg(
        hip=Joint(pins.LEG3_HIP),
        knee=Joint(pins.LEG3_KNEE),
        ankle=Joint(pins.LEG3_ANKLE),
    ),
    leg4=Leg(
        hip=Joint(pins.LEG4_HIP),
        knee=Joint(pins.LEG4_KNEE),
        ankle=Joint(pins.LEG4_ANKLE),
    ),
)
light = Light(pwmio.PWMOut(pins.LED_STRIP))

battery = Battery(pins.BATTERY_ADC)

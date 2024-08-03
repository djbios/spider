import pins
from wrappers.battery import Battery
from wrappers.walker import Walker, Leg, Joint
from wrappers.light import Light
from wrappers.display import Display, register_display_routine
from wrappers.accelerometer import Accelerometr

import pwmio
import busio
from adafruit_pca9685 import PCA9685
import os

import adafruit_connection_manager
import wifi

import adafruit_requests
from routines import RoutinesRegistry, BaseRoutine
import circuitpython_schedule as schedule
from logging import log, get_unsent_loglines
from collections import deque
import asyncio
from adafruit_httpserver import (
    Server,
    Request,
    FileResponse,
)
from logging import log

DEFAULT_SPEED = 1000
DEFAULT_ACCELERATION = 500

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

# I2C
i2c = busio.I2C(pins.I2C_SCL, pins.I2C_SDA)

# PCA 9685 servo controller
pca = PCA9685(i2c)
pca.frequency = 50
pca.reference_clock_speed = 2.82337e07

# Walker
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

# Light
light = Light(pwmio.PWMOut(pins.LED_STRIP))

# Battery
battery = Battery(pins.BATTERY_ADC)

# Accelerometer
accelerometer = Accelerometr(i2c)


# Wifi
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)
rssi = wifi.radio.ap_info.rssi

try:
    # Connect to the Wi-Fi network
    wifi.radio.connect(ssid, password)
except OSError as e:
    log(f"❌ OSError: {e}")
log(f"✅ Wifi! IP: {wifi.radio.ipv4_address}")

# Http server
server = Server(pool, "/static", debug=True)


@server.route("/")
def base(request: Request):
    """
    Serve the default index.html file.
    """
    return FileResponse(request, "index.html")


@RoutinesRegistry.register()
class HttpServerRoutine(BaseRoutine):
    def __init__(self) -> None:
        server.start(str(wifi.radio.ipv4_address))
        log("HttpServerRoutine initialized")
        super().__init__()

    async def tick(self):
        try:
            server.poll()
        except OSError as error:
            log(error)


# Scheduler
@RoutinesRegistry.register()
class SchedulerRoutine(BaseRoutine):
    def __init__(self) -> None:
        schedule.every(30).seconds.do(battery.log_battery)
        log("SchedulerRoutine initialized")
        super().__init__()

    async def tick(self):
        schedule.run_pending()


# Display
display = Display(128, 32, i2c)
register_display_routine(display, battery, wifi, accelerometer)

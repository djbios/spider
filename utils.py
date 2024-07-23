import time
from pwmio import PWMOut
from adafruit_motor import servo

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
    (255, 0, 0),    # Red
    (255, 127, 0),  # Orange
    (255, 255, 0),  # Yellow
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (75, 0, 130),   # Indigo    (148, 0, 211)   # Violet
]

# Function to interpolate between two colors
def interpolate_color(color1, color2, factor):
    return (
        int(color1[0] + (color2[0] - color1[0]) * factor),
        int(color1[1] + (color2[1] - color1[1]) * factor),
        int(color1[2] + (color2[2] - color1[2]) * factor)
    )


class Joint:
    def __init__(self, pin):
        self.pwm = PWMOut(pin, duty_cycle=0, frequency=50)
        self.servo = servo.Servo(self.pwm)

    def move(self, angle: float, speed: float = 1.0):
        if self.servo.angle is None:
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
    
    def move(self, hip: float, knee: float, ankle: float, speed: float = 1):
        # TODO make it smoother (interpolate)
        self.hip.move(hip, speed)
        self.knee.move(knee, speed)
        self.ankle.move(ankle, speed)
    
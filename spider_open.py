import math
import time

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

# Math constants
KEEP = 255
pi = 3.1415926

# Calculated constants for turning
temp_a = math.sqrt((2 * x_default + length_side) ** 2 + y_step ** 2)
temp_b = 2 * (y_start + y_step) + length_side
temp_c = math.sqrt((2 * x_default + length_side) ** 2 + (2 * y_start + y_step + length_side) ** 2)
temp_alpha = math.acos((temp_a ** 2 + temp_b ** 2 - temp_c ** 2) / (2 * temp_a * temp_b))

turn_x1 = (temp_a - length_side) / 2
turn_y1 = y_start + y_step / 2
turn_x0 = turn_x1 - temp_b * math.cos(temp_alpha)
turn_y0 = temp_b * math.sin(temp_alpha) - turn_y1 - length_side

class Leg:
    def __init__(self, id, pin1, pin2, pin3):
        self.id = id
        self.servo = [Servo() for _ in range(3)]
        self.servo_pins = [pin1, pin2, pin3]
        self.site_now = [0, 0, 0]
        self.site_expect = [0, 0, 0]
        self.temp_speed = [0, 0, 0]
        self.attach_servos()

    def attach_servos(self):
        for i in range(3):
            self.servo[i].attach(self.servo_pins[i])
            time.sleep(0.1)

    def detach_servos(self):
        for i in range(3):
            self.servo[i].detach()
            time.sleep(0.1)

    def set_site(self, x, y, z):
        length_x = length_y = length_z = 0

        if x != KEEP:
            length_x = x - self.site_now[0]
        if y != KEEP:
            length_y = y - self.site_now[1]
        if z != KEEP:
            length_z = z - self.site_now[2]

        length = math.sqrt(length_x ** 2 + length_y ** 2 + length_z ** 2)

        self.temp_speed[0] = length_x / length * move_speed * speed_multiple
        self.temp_speed[1] = length_y / length * move_speed * speed_multiple
        self.temp_speed[2] = length_z / length * move_speed * speed_multiple

        if x != KEEP:
            self.site_expect[0] = x
        if y != KEEP:
            self.site_expect[1] = y
        if z != KEEP:
            self.site_expect[2] = z

    def update_position(self):
        for j in range(3):
            if abs(self.site_now[j] - self.site_expect[j]) < (abs(self.temp_speed[j]) + E_DELTA):
                self.site_now[j] = self.site_expect[j]
            else:
                self.site_now[j] += self.temp_speed[j]

        alpha, beta, gamma = self.cartesian_to_polar(self.site_now[0], self.site_now[1], self.site_now[2])
        self.polar_to_servo(alpha, beta, gamma)

    def cartesian_to_polar(self, x, y, z):
        w = (x >= 0 and 1 or -1) * math.sqrt(x ** 2 + y ** 2)
        v = w - length_c
        alpha = math.atan2(z, v) + math.acos((length_a ** 2 - length_b ** 2 + v ** 2 + z ** 2) / (2 * length_a * math.sqrt(v ** 2 + z ** 2)))
        beta = math.acos((length_a ** 2 + length_b ** 2 - v ** 2 - z ** 2) / (2 * length_a * length_b))
        gamma = math.atan2(y, x) if w >= 0 else math.atan2(-y, -x)

        alpha = alpha / pi * 180
        beta = beta / pi * 180
        gamma = gamma / pi * 180

        return alpha, beta, gamma

    def polar_to_servo(self, alpha, beta, gamma):
        if self.id == 0:
            alpha = 90 - alpha
            beta = beta
            gamma += 90
        elif self.id == 1:
            alpha += 90
            beta = 180 - beta
            gamma = 90 - gamma
        elif self.id == 2:
            alpha += 90
            beta = 180 - beta
            gamma = 90 - gamma
        elif self.id == 3:
            alpha = 90 - alpha
            beta = beta
            gamma += 90

        self.servo[0].write(alpha)
        self.servo[1].write(beta)
        self.servo[2].write(gamma)

    def wait_reach(self):
        while True:
            if self.site_now[0] == self.site_expect[0]:
                if self.site_now[1] == self.site_expect[1]:
                    if self.site_now[2] == self.site_expect[2]:
                        break

class Robot:
    def __init__(self):
        self.legs = [
            Leg(0, 2, 3, 4),
            Leg(1, 5, 6, 7),
            Leg(2, 8, 9, 10),
            Leg(3, 11, 12, 13)
        ]

    def setup(self):
        print("Robot starts initialization")
        self.set_initial_positions()
        print("Servo service started")
        print("Servos initialized")
        print("Robot initialization Complete")

    def set_initial_positions(self):
        self.legs[0].set_site(x_default - x_offset, y_start + y_step, z_boot)
        self.legs[1].set_site(x_default - x_offset, y_start + y_step, z_boot)
        self.legs[2].set_site(x_default + x_offset, y_start, z_boot)
        self.legs[3].set_site(x_default + x_offset, y_start, z_boot)
        for leg in self.legs:
            leg.site_now = leg.site_expect[:]

    def loop(self):
        print("Stand")
        self.stand()
        time.sleep(2)
        print("Step forward")
        self.step_forward(5)
        time.sleep(2)
        print("Step back")
        self.step_back(5)
        time.sleep(2)
        print("Turn left")
        self.turn_left(5)
        time.sleep(2)
        print("Turn right")
        self.turn_right(5)
        time.sleep(2)
        print("Hand wave")
        self.hand_wave(3)
        time.sleep(2)
        print("Hand shake")
        self.hand_shake(3)
        time.sleep(2)
        print("Body dance")
        self.body_dance(10)
        time.sleep(2)
        print("Sit")
        self.sit()
        time.sleep(5)

    def sit(self):
        global move_speed
        move_speed = stand_seat_speed
        for leg in self.legs:
            leg.set_site(KEEP, KEEP, z_boot)
        self.wait_all_reach()

    def stand(self):
        global move_speed
        move_speed = stand_seat_speed
        for leg in self.legs:
            leg.set_site(KEEP, KEEP, z_default)
        self.wait_all_reach()

    def turn_left(self, step):
        global move_speed
        move_speed = spot_turn_speed
        while step > 0:
            step -= 1
            if self.legs[3].site_now[1] == y_start:
                # Leg 3&1 move
                self.legs[3].set_site(x_default + x_offset, y_start, z_up)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x1 - x_offset, turn_y1, z_default)
                self.legs[1].set_site(turn_x0 - x_offset, turn_y0, z_default)
                self.legs[2].set_site(turn_x1 + x_offset, turn_y1, z_default)
                self.legs[3].set_site(turn_x0 + x_offset, turn_y0, z_up)
                self.wait_all_reach()

                self.legs[3].set_site(turn_x0 + x_offset, turn_y0, z_default)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x1 + x_offset, turn_y1, z_default)
                self.legs[1].set_site(turn_x0 + x_offset, turn_y0, z_default)
                self.legs[2].set_site(turn_x1 - x_offset, turn_y1, z_default)
                self.legs[3].set_site(turn_x0 - x_offset, turn_y0, z_default)
                self.wait_all_reach()

                self.legs[1].set_site(turn_x0 + x_offset, turn_y0, z_up)
                self.wait_all_reach()

                self.legs[0].set_site(x_default + x_offset, y_start, z_default)
                self.legs[1].set_site(x_default + x_offset, y_start, z_up)
                self.legs[2].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.legs[3].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.wait_all_reach()

                self.legs[1].set_site(x_default + x_offset, y_start, z_default)
                self.wait_all_reach()
            else:
                # Leg 0&2 move
                self.legs[0].set_site(x_default + x_offset, y_start, z_up)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x0 + x_offset, turn_y0, z_up)
                self.legs[1].set_site(turn_x1 + x_offset, turn_y1, z_default)
                self.legs[2].set_site(turn_x0 - x_offset, turn_y0, z_default)
                self.legs[3].set_site(turn_x1 - x_offset, turn_y1, z_default)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x0 + x_offset, turn_y0, z_default)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x0 - x_offset, turn_y0, z_default)
                self.legs[1].set_site(turn_x1 - x_offset, turn_y1, z_default)
                self.legs[2].set_site(turn_x0 + x_offset, turn_y0, z_default)
                self.legs[3].set_site(turn_x1 + x_offset, turn_y1, z_default)
                self.wait_all_reach()

                self.legs[2].set_site(turn_x0 + x_offset, turn_y0, z_up)
                self.wait_all_reach()

                self.legs[0].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.legs[1].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.legs[2].set_site(x_default + x_offset, y_start, z_up)
                self.legs[3].set_site(x_default + x_offset, y_start, z_default)
                self.wait_all_reach()

                self.legs[2].set_site(x_default + x_offset, y_start, z_default)
                self.wait_all_reach()

    def turn_right(self, step):
        global move_speed
        move_speed = spot_turn_speed
        while step > 0:
            step -= 1
            if self.legs[2].site_now[1] == y_start:
                # Leg 2&0 move
                self.legs[2].set_site(x_default + x_offset, y_start, z_up)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x0 - x_offset, turn_y0, z_default)
                self.legs[1].set_site(turn_x1 - x_offset, turn_y1, z_default)
                self.legs[2].set_site(turn_x0 + x_offset, turn_y0, z_up)
                self.legs[3].set_site(turn_x1 + x_offset, turn_y1, z_default)
                self.wait_all_reach()

                self.legs[2].set_site(turn_x0 + x_offset, turn_y0, z_default)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x0 + x_offset, turn_y0, z_default)
                self.legs[1].set_site(turn_x1 + x_offset, turn_y1, z_default)
                self.legs[2].set_site(turn_x0 - x_offset, turn_y0, z_default)
                self.legs[3].set_site(turn_x1 - x_offset, turn_y1, z_default)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x0 + x_offset, turn_y0, z_up)
                self.wait_all_reach()

                self.legs[0].set_site(x_default + x_offset, y_start, z_up)
                self.legs[1].set_site(x_default + x_offset, y_start, z_default)
                self.legs[2].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.legs[3].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.wait_all_reach()

                self.legs[0].set_site(x_default + x_offset, y_start, z_default)
                self.wait_all_reach()
            else:
                # Leg 1&3 move
                self.legs[1].set_site(x_default + x_offset, y_start, z_up)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x1 + x_offset, turn_y1, z_default)
                self.legs[1].set_site(turn_x0 + x_offset, turn_y0, z_up)
                self.legs[2].set_site(turn_x1 - x_offset, turn_y1, z_default)
                self.legs[3].set_site(turn_x0 - x_offset, turn_y0, z_default)
                self.wait_all_reach()

                self.legs[1].set_site(turn_x0 + x_offset, turn_y0, z_default)
                self.wait_all_reach()

                self.legs[0].set_site(turn_x1 - x_offset, turn_y1, z_default)
                self.legs[1].set_site(turn_x0 - x_offset, turn_y0, z_default)
                self.legs[2].set_site(turn_x1 + x_offset, turn_y1, z_default)
                self.legs[3].set_site(turn_x0 + x_offset, turn_y0, z_default)
                self.wait_all_reach()

                self.legs[3].set_site(turn_x0 + x_offset, turn_y0, z_up)
                self.wait_all_reach()

                self.legs[0].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.legs[1].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.legs[2].set_site(x_default + x_offset, y_start, z_default)
                self.legs[3].set_site(x_default + x_offset, y_start, z_up)
                self.wait_all_reach()

                self.legs[3].set_site(x_default + x_offset, y_start, z_default)
                self.wait_all_reach()

    def step_forward(self, step):
        global move_speed
        move_speed = leg_move_speed
        while step > 0:
            step -= 1
            if self.legs[2].site_now[1] == y_start:
                # Leg 2&1 move
                self.legs[2].set_site(x_default + x_offset, y_start, z_up)
                self.wait_all_reach()
                self.legs[2].set_site(x_default + x_offset, y_start + 2 * y_step, z_up)
                self.wait_all_reach()
                self.legs[2].set_site(x_default + x_offset, y_start + 2 * y_step, z_default)
                self.wait_all_reach()

                move_speed = body_move_speed

                self.legs[0].set_site(x_default + x_offset, y_start, z_default)
                self.legs[1].set_site(x_default + x_offset, y_start + 2 * y_step, z_default)
                self.legs[2].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.legs[3].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.wait_all_reach()

                move_speed = leg_move_speed

                self.legs[1].set_site(x_default + x_offset, y_start + 2 * y_step, z_up)
                self.wait_all_reach()
                self.legs[1].set_site(x_default + x_offset, y_start, z_up)
                self.wait_all_reach()
                self.legs[1].set_site(x_default + x_offset, y_start, z_default)
                self.wait_all_reach()
            else:
                # Leg 0&3 move
                self.legs[0].set_site(x_default + x_offset, y_start, z_up)
                self.wait_all_reach()
                self.legs[0].set_site(x_default + x_offset, y_start + 2 * y_step, z_up)
                self.wait_all_reach()
                self.legs[0].set_site(x_default + x_offset, y_start + 2 * y_step, z_default)
                self.wait_all_reach()

                move_speed = body_move_speed

                self.legs[0].set_site(x_default - x_offset, y_start + y_step, z_default)
                self.legs[1

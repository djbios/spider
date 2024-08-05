from logging_ import log
import math

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


def inverse_kinematics(x, y, z, L_c, L_f, L_t):
    """
    Рассчитывает углы суставов робота-паука для заданной позиции (x, y, z).

    Параметры:
    x, y, z : float
        Координаты цели.
    L_c : float
        Длина сегмента бедра (coxal).
    L_f : float
        Длина сегмента колена (femur).
    L_t : float
        Длина сегмента лодыжки (tibia).

    Возвращает:
    (theta_c, theta_f, theta_t) : tuple of float
        Углы суставов в градусах.
    """
    # Угол Coxal (бедро)
    theta_c = math.atan2(y, x)

    # Расстояние до проекции точки на плоскость OXY
    r = math.sqrt(x**2 + y**2)

    # Проверка достижимости точки
    d = math.sqrt(r**2 + z**2)
    if d > (L_f + L_t):
        raise ValueError("Точка вне досягаемости.")

    # Угол в колене (Femur)
    cos_theta_f = (L_f**2 + d**2 - L_t**2) / (2 * L_f * d)
    theta_f = math.acos(cos_theta_f) - math.atan2(z, r)

    # Угол в лодыжке (Tibia)
    cos_theta_t = (L_f**2 + L_t**2 - d**2) / (2 * L_f * L_t)
    theta_t = math.acos(cos_theta_t)

    # Преобразование углов в градусы
    theta_c_deg = math.degrees(theta_c)
    theta_f_deg = math.degrees(theta_f)
    theta_t_deg = math.degrees(theta_t)

    # Добавляем 90 градусов, чтобы отразить начальные положения
    theta_c_deg += 90
    theta_f_deg += 90
    theta_t_deg += 90

    return theta_c_deg, theta_f_deg, theta_t_deg


# From https://www.instructables.com/vPython-Spider-Robot-simulator/
coxa_len = 27.5
femur_len = 70
tibia_len = 80


def axis_to_angle(x, y, z):
    from math import sqrt, pow, atan2, acos, degrees

    if x >= 0:
        w = sqrt(pow(x, 2) + pow(y, 2))
    else:
        w = -1 * (sqrt(pow(x, 2) + pow(y, 2)))

    v = w - coxa_len
    alpha_tmp = (
        (pow(femur_len, 2) - pow(tibia_len, 2) + pow(v, 2) + pow(z, 2))
        / 2
        / femur_len
        / sqrt(pow(v, 2) + pow(z, 2))
    )
    if alpha_tmp > 1 or alpha_tmp < -1:
        # print "x=%f y=%f v=%f w=%f" % (x, y, v, w)
        # print "alpha=%f" % alpha_tmp
        if alpha_tmp > 1:
            alpha_tmp = 1
        else:
            alpha_tmp = -1
    alpha = atan2(z, v) + acos(alpha_tmp)

    beta_tmp = (
        (pow(femur_len, 2) + pow(tibia_len, 2) - pow(v, 2) - pow(z, 2))
        / 2
        / femur_len
        / tibia_len
    )
    if beta_tmp > 1 or beta_tmp < -1:
        if beta_tmp > 1:
            beta_tmp = 1
        else:
            beta_tmp = -1
    beta = acos(beta_tmp)

    if w >= 0:
        gamma = atan2(y, x)
    else:
        gamma = atan2(-y, -x)
    return (alpha, beta, gamma)

# From https://chatgpt.com/c/fdaafd14-df10-4927-9a90-fbeaa5aef1ad

import math

def cartesian_to_polar(x, y, z):
    """
    Converts Cartesian coordinates to polar coordinates for the spider robot's leg.

    :param x: X-coordinate
    :param y: Y-coordinate
    :param z: Z-coordinate
    :return: (alpha, beta, gamma) angles in degrees
    """
    length_a = 55
    length_b = 77.5
    length_c = 27.5
    pi = math.pi

    # Calculate w-z degree
    w = math.copysign(1, x) * math.sqrt(x**2 + y**2)
    v = w - length_c

    alpha = math.atan2(z, v) + math.acos((length_a**2 - length_b**2 + v**2 + z**2) / (2 * length_a * math.sqrt(v**2 + z**2)))
    beta = math.acos((length_a**2 + length_b**2 - v**2 - z**2) / (2 * length_a * length_b))
    gamma = math.atan2(y, x) if w >= 0 else math.atan2(-y, -x)

    # Convert radians to degrees
    alpha = math.degrees(alpha)
    beta = math.degrees(beta)
    gamma = math.degrees(gamma)

    return alpha, beta, gamma

def linear_move_to_angles(leg_config, initial_x, initial_y, initial_z, dx, dy, dz):
    """
    Calculates the joint angles for a leg to move to a new position in Cartesian space.

    :param leg_config: Configuration of the leg (not used in this implementation)
    :param initial_x: Initial x position
    :param initial_y: Initial y position
    :param initial_z: Initial z position
    :param dx: Desired x movement
    :param dy: Desired y movement
    :param dz: Desired z movement
    :return: (hip_angle, knee_angle, ankle_angle) angles in degrees
    """
    x = initial_x + dx
    y = initial_y + dy
    z = initial_z + dz

    return cartesian_to_polar(x, y, z)


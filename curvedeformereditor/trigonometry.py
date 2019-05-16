import math
from PySide2 import QtCore
from curvedeformereditor.arrayutils import split_value, get_break_indices


def compute_ray_limit(angle, point1, point2):
    limit_x = abs(point1.x() - point2.x())
    limit_y = abs(point1.y() - point2.y())
    angle = ((angle / (math.pi / 2) - 0.5) * 2)
    limit_x *= 1 - abs(angle) if angle >= 0 else 1
    limit_y *= 1 - abs(angle) if angle <= 0 else 1
    limit_xy = (abs(angle) / 4) + .75
    return (limit_x + limit_y) * limit_xy


def point_on_circle(angle, ray, center):
    x = ray * math.cos(float(angle))
    y = ray * math.sin(float(angle))
    return QtCore.QPointF(center.x() + x, center.y() + y)


def compute_angle(point1, point2):
    point3 = QtCore.QPointF(point2.x(), point1.y())
    return math.radians(compute_absolute_angle_c(point3, point2, point1))


def compute_absolute_angle_c(a, b, c):
    quarter = get_quarter(a, b, c)
    try:
        angle_c = compute_angle_c(a, b, c)
    except ZeroDivisionError:
        return 360 - (90 * quarter)

    if quarter == 0:
        return round(180.0 + angle_c, 1)
    elif quarter == 1:
        return round(270.0 + (90 - angle_c), 1)
    elif quarter == 2:
        return round(angle_c, 1)
    else:
        return math.fabs(round(90.0 + (90 - angle_c), 1))


def compute_angle_c(a, b, c):
    return math.degrees(math.atan(distance(a, b) / distance(a, c)))


def get_quarter(a, b, c):
    quarter = None
    if b.y() <= a.y() and b.x() < c.x():
        quarter = 0
    elif b.y() < a.y() and b.x() >= c.x():
        quarter = 1
    elif b.y() >= a.y() and b.x() > c.x():
        quarter = 2
    elif b.y() >= a.y() and b.x() <= c.x():
        quarter = 3
    return quarter


def distance(a, b):
    """ compute distance between two points """
    x = (b.x() - a.x())**2
    y = (b.y() - a.y())**2
    return math.sqrt(abs(x + y))


def move_point_from_resized_rect(point, old_size, new_size):
    """
    This function move a point with a reference size and a new size.
    """
    x = (point.x() / old_size.width()) * new_size.width()
    y = (point.y() / old_size.height()) * new_size.height()
    point.setX(x)
    point.setY(y)

import math
from PySide2 import QtCore, QtGui
from curvedeformereditor.drawing import (
    clamp_point_in_rect, create_beziercurve_path)
from curvedeformereditor.trigonometry import (
    distance, compute_angle, point_on_circle, move_point_from_resized_rect)
from curvedeformereditor.arrayutils import split_value, clamp, get_break_indices


class ControlPoint():
    def __init__(self, center, tangentin=None, tangentout=None):
        self.center = QtCore.QPointF(center)
        self.tangentin = QtCore.QPointF(tangentin or center)
        self.tangentout = QtCore.QPointF(tangentout or center)
        self.isboundary = False
        self.autotangent = True
        self.selected = False
        self.linear = False

    def move(self, point, rect=None):
        if self.isboundary is True:
            point.setX(self.center.x())
        if rect is not None:
            clamp_point_in_rect(point, rect)

        delta = self.center - point
        self.center -= delta
        self.tangentin -= delta
        self.tangentout -= delta

    def move_tangent(self, point1, point2=None):
        if point1.x() < self.center.x():
            parent = self.tangentin
            child = self.tangentout
        else:
            parent = self.tangentout
            child = self.tangentin

        parent.setX(point1.x())
        parent.setY(point1.y())
        mirror = point2 or compute_mirror_tangent(self.center, parent, child)
        child.setX(mirror.x())
        child.setY(mirror.y())

    def resize(self, old_size, new_size):
        move_point_from_resized_rect(self.center, old_size, new_size)
        move_point_from_resized_rect(self.tangentin, old_size, new_size)
        move_point_from_resized_rect(self.tangentout, old_size, new_size)

    def __lt__(self, controlpoint):
        return self.center.x() < controlpoint.center.x()


def insert_controlpoint_in_curve(point, controlpoints):
    controlpoints = sorted(controlpoints)
    for controlpoint in controlpoints[1:]:
        if controlpoint.center.x() > point.x():
            break
    controlpoint = ControlPoint(point, QtCore.QPoint(), QtCore.QPoint())
    return controlpoint


def pick_controlpoint_center(controlpoints, point, tolerance=8):
    for controlpoint in controlpoints:
        if distance(controlpoint.center, point) < tolerance:
            return controlpoint
    return None


def pick_controlpoint_tangent(controlpoints, point, tolerance=8):
    for controlpoint in controlpoints:
        condition = (
            distance(controlpoint.tangentin, point) < tolerance or
            distance(controlpoint.tangentout, point) < tolerance)
        if condition:
            return controlpoint
    return None


def compute_mirror_tangent(center, tangent, child=None):
    angle = compute_angle(center, tangent) - math.pi
    ray = distance(center, child or tangent)
    return point_on_circle(angle, ray, center)


def auto_tangent_beziercurve(
        controlpoints, skip=None, auto_tangent_function=None):
    """
    This apply the good autotangent function on every controlpoint on a bezier
    curve.
    """
    auto_tangent_function = auto_tangent_function or auto_tangent_smoothed
    controlpoints = sorted(controlpoints)
    for i, controlpoint in enumerate(controlpoints):
        if controlpoint is skip:
            continue
        if controlpoint.autotangent is False:
            continue
        if i == 0:
            auto_tangent_boundary_controlpoint(
                controlpoint, controlpoints[i + 1])
            continue
        if i == len(controlpoints) - 1:
            auto_tangent_boundary_controlpoint(
                controlpoint, controlpoints[i - 1])
            continue
        before = controlpoints[i - 1]
        after = controlpoints[i + 1]
        auto_tangent_function(controlpoint, before, after)


def auto_tangent_boundary_controlpoint(controlpoint, target):
    """ 
    This function compute the auto tangent for the first or the last point of
    an bezier curve
    """
    angle = compute_angle(controlpoint.center, target.center)
    ray = distance(controlpoint.center, target.center) * .3
    tangent = point_on_circle(angle, ray, controlpoint.center)
    controlpoint.move_tangent(tangent)


def auto_tangent_smoothed(controlpoint, before, after):
    """
    This function create an auto smoothed tangent on a given controlpoint.
    To compute the tangent angle, it use the controle point before and after
    the given one on a bezier curve.
    To define a smoothed angle, it calculate the average angle between the
    before out tangent --> control point center and the 
    control point center --> after in tangent.
    """
    angle1 = compute_angle(before.tangentout, controlpoint.center)
    angle2 = compute_angle(controlpoint.center, after.tangentin)
    # clamp the angle to avoid tangent swap
    if abs(angle1 - angle2) > math.pi:
        if angle1 > angle2:
            angle1 -= 2 * math.pi
        else:
            angle2 -= 2 * math.pi

    width = after.center.x() - before.center.x()
    # offset the value to avoid ZeroDivisionError
    if width == 0:
        width += 1e-5
    width_before = controlpoint.center.x() - before.center.x()
    factor = width_before / width
    angle = (angle1 * (1 - factor)) + (angle2 * factor)

    ray_in = distance(before.center, controlpoint.center) * 0.3
    ray_out = distance(controlpoint.center, after.center) * 0.3

    tangent1 = point_on_circle(angle, ray_out, controlpoint.center)
    tangent2 = point_on_circle(angle + math.pi, ray_in, controlpoint.center)
    controlpoint.move_tangent(tangent1, tangent2)


def auto_tangent_flatten(controlpoint, before, after):
    condition = (
        controlpoint.center.y() >= before.center.y() and
        controlpoint.center.y() >= after.center.y() or
        controlpoint.center.y() <= before.center.y() and
        controlpoint.center.y() <= after.center.y())
    if condition:
        angle = 0
    else:
        angle1 = compute_angle(before.tangentout, controlpoint.center)
        angle2 = compute_angle(controlpoint.center, after.tangentin)
        if abs(angle1) > abs(angle2):
            angle = angle1
        else:
            angle = angle2

    ray_in = distance(before.center, controlpoint.center) * 0.3
    horizontal = abs(before.center.x() - controlpoint.center.x())
    ray_in = clamp(ray_in, 0, horizontal)
    ray_out = distance(controlpoint.center, after.center) * 0.3
    horizontal = abs(controlpoint.center.x() - after.center.x())
    ray_out = clamp(ray_out, 0, horizontal)

    tangent1 = point_on_circle(angle, ray_out, controlpoint.center)
    tangent2 = point_on_circle(angle + math.pi, ray_in, controlpoint.center)
    controlpoint.move_tangent(tangent1, tangent2)


def vertical_path(rect, x):
    """
    This function create a super tiny vertical rectangle on the x coordinate.
    This is use to find a Y coordinate with X coordinate given on a bezier
    curve.
    """
    point1 = QtCore.QPointF(x, rect.top() - 1e10)
    point2 = QtCore.QPointF(x, rect.bottom() + 1e10)
    point3 = QtCore.QPointF(x + 1e-5, rect.bottom() + 1e10)
    point4 = QtCore.QPointF(x + 1e-5, rect.top() - 1e10)
    path = QtGui.QPainterPath(point1)
    path.lineTo(point2)
    path.lineTo(point3)
    path.lineTo(point4)
    return path


def compute_bezier_curve_values(controlpoints, rect, sample):
    """
    This function compute the values drawn by an horizontal bezier curve as
    QPainterPath. Sample give the number of samples are requested.
    The result is a list of floats. 0.0 is the smallest visible value and
    1.0 is the highest visible value but higher and lower values can be
    returned if the bezier curve is out of rect on sample.
    """
    if sample < 2:
        raise ValueError("At least 2 values can be requested (start and end)")
    # WORKAROUND: if the control points draw a straight line path,
    # for a strange reason, the intersection algorytm fail ...
    # To avoid this issue, if the bezier curve contains only two control point,
    # a third one is created in the middle with a tiny offset to break the line
    if len(controlpoints) == 2:
        x = (controlpoints[0].center.x() + controlpoints[-1].center.x()) / 2
        y = (controlpoints[0].center.y() + controlpoints[-1].center.y()) / 2
        y += 1e-3
        controlpoint = ControlPoint(QtCore.QPointF(x, y))
        controlpoints.insert(1, controlpoint)
    # To find an y coordinate on a horizontal bezier curve from a x coordinate
    # given, we create a vertical really thin rectanglular QPainterPath.
    # Use the QPainterPath.intersected() return a QPainterPath which start
    # exactly on the intersection.
    path = create_beziercurve_path(controlpoints)
    lines = [vertical_path(rect, x) for x in split_value(rect.width(), sample)]
    intersections = [path.intersected(line) for line in lines]
    points = [intersection.pointAtPercent(1) for intersection in intersections]
    values = [1 - (point.y() / rect.height()) for point in points]
    # the first and the last values are not all the time well evaluate with the
    # intersection method, so we compute them separately.
    values[0] = 1 - controlpoints[0].center.y() / rect.height()
    values[-1] = 1 - controlpoints[-1].center.y() / rect.height()
    return values


def create_beziercurve(values, rect, linear=False):
    """ TODO: docstring """
    x_pos = split_value(rect.width(), len(values))
    y_pos = [rect.height() * (1 - value) for value in values]
    breakpoints_indices = get_break_indices(values)
    controlpoints = []
    for i, (x, y) in enumerate(zip(x_pos, y_pos)):
        if i not in breakpoints_indices:
            continue
        controlpoint = ControlPoint(QtCore.QPointF(x, y))
        controlpoint.linear = linear
        controlpoints.append(controlpoint)
    if linear is False:
        auto_tangent_beziercurve(controlpoints)
    # some offset can appear after resizing the widget which cause some
    # issues on the limits control point. This ensure that the first
    # and the last point has the right x value
    controlpoints[0].center.setX(rect.left())
    controlpoints[-1].center.setX(rect.right())
    return controlpoints


def select_controlpoint(selected_controlpoint, controlpoints):
    for controlpoint in controlpoints:
        controlpoint.selected = False
    selected_controlpoint.selected = True


def copy_bezier_curve(controlpoints):
    bezier = []
    for controlpoint in controlpoints:
        bezier.append(ControlPoint(
            center=QtCore.QPointF(controlpoint.center),
            tangentin=QtCore.QPointF(controlpoint.tangentin),
            tangentout=QtCore.QPointF(controlpoint.tangentout)))
    bezier[0].isboundary = True
    bezier[-1].isboundary = True
    return bezier

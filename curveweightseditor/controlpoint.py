
import math
from PyQt5 import QtCore, QtGui
from curveweightseditor.geometry import (
    clamp_in_rect, distance, move_point_from_rect_resized, get_angle,
    point_on_circle)
from curveweightseditor.arrayutils import split_value


class ControlPoint():
    def __init__(self, center, tangentin, tangentout):
        self.center = QtCore.QPointF(center)
        self.tangentin = QtCore.QPointF(tangentin)
        self.tangentout = QtCore.QPointF(tangentout)
        self.isboundary = False
        self.autotangent = True

    def move(self, point, rect=None):
        if self.isboundary is True:
            point.setX(self.center.x())
            clamp_in_rect(point, rect)
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
        mirror = point2 or mirror_tangent(self.center, parent, child)
        child.setX(mirror.x())
        child.setY(mirror.y())

    def resize(self, old_size, new_size):
        move_point_from_rect_resized(self.center, old_size, new_size)
        move_point_from_rect_resized(self.tangentin, old_size, new_size)
        move_point_from_rect_resized(self.tangentout, old_size, new_size)

    def __lt__(self, controlpoint):
        return self.center.x() < controlpoint.center.x()


def create_controlpoint_in_line(position, controlpoints):
    controlpoints = sorted(controlpoints)
    for controlpoint in controlpoints[1:]:
        if controlpoint.center.x() > position.x():
            break
    controlpoint = ControlPoint(position, QtCore.QPoint(), QtCore.QPoint())
    return controlpoint


def pick_a_center(controlpoints, position, tolerance=8):
    for controlpoint in controlpoints:
        if distance(controlpoint.center, position) < tolerance:
            return controlpoint
    return None


def pick_a_tangent(controlpoints, position, tolerance=8):
    for controlpoint in controlpoints:
        condition = (
            distance(controlpoint.tangentin, position) < tolerance or
            distance(controlpoint.tangentout, position) < tolerance)
        if condition:
            return controlpoint
    return None


def mirror_tangent(center, tangent, child=None):
    angle = get_angle(center, tangent) - math.pi
    ray = distance(center, child or tangent)
    return point_on_circle(angle, ray, center)


def auto_tangent_line(controlpoints, skip=None):
    controlpoints = sorted(controlpoints)
    for i, controlpoint in enumerate(controlpoints):
        if controlpoint is skip:
            continue
        if controlpoint.autotangent is False:
            continue
        if i == 0:
            auto_tangent_for_boundary(controlpoint, controlpoints[i + 1])
            continue
        if i == len(controlpoints) - 1:
            auto_tangent_for_boundary(controlpoint, controlpoints[i - 1])
            continue
        before = controlpoints[i - 1]
        after = controlpoints[i + 1]
        auto_tangent(controlpoint, before, after)


def auto_tangent_for_boundary(controlpoint, target):
    angle = get_angle(controlpoint.center, target.center)
    ray = distance(controlpoint.center, target.center) * .3
    tangent = point_on_circle(angle, ray, controlpoint.center)
    controlpoint.move_tangent(tangent)


def auto_tangent(controlpoint, before, after):
    distance1 = distance(before.center, controlpoint.center)
    distance2 = distance(controlpoint.center, after.center)
    ray = (distance1 + distance2) * 0.15
    if ray > distance1 or ray > distance2:
        ray = min([distance1, distance2])

    width = after.center.x() - before.center.x()
    if width == 0:
        width += 1e-5
    width_before = controlpoint.center.x() - before.center.x()
    factor = width_before / width
    target = (before.center * (1 - factor)) + (before.tangentout * factor)
    angle1 = get_angle(target, controlpoint.center)
    target = (after.center * (1 - factor)) + (after.tangentout * factor)
    angle2 = get_angle(controlpoint.center, target)

    # clamp the angle to avoid tangent swapswap
    if abs(angle1 - angle2) > math.pi:
        if angle1 > angle2:
            angle1 -= 2 * math.pi
        else:
            angle2 -= 2 * math.pi

    angle = (angle1 * (1 - factor)) + (angle2 * factor)
    tangent = point_on_circle(angle, ray, controlpoint.center)
    controlpoint.move_tangent(tangent)


def vertical_path(rect, x):
    point1 = QtCore.QPointF(x, rect.top() - 1e10)
    point2 = QtCore.QPointF(x, rect.bottom() + 1e10)
    point3 = QtCore.QPointF(x + 1e-5, rect.bottom() + 1e10)
    point4 = QtCore.QPointF(x + 1e-5, rect.top() - 1e10)
    path = QtGui.QPainterPath(point1)
    path.lineTo(point2)
    path.lineTo(point3)
    path.lineTo(point4)
    return path


def extract_values(path, rect, sample):
    lines = [vertical_path(rect, x) for x in split_value(rect.width(), sample)]
    intersections = [path.intersected(line) for line in lines]
    return [intersection.pointAtPercent(0) for intersection in intersections]

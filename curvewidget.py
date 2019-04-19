import sys

sys.path.append('/nwave/software/PySide2/5.12.0-cp27/linux64/')
sys.path.append('/nwave/software/shiboken2/5.12.0-cp27/linux64/')

import math
from PySide2 import QtGui, QtCore, QtWidgets


DEFAULT_SIZE = 350, 125
MINIMUM_SIZE = 200, 100
DEFAULT_POINTS = [
    {
        'center': (0, 0),
        'in': (-(DEFAULT_SIZE[0] / 3), 0),
        'out':((DEFAULT_SIZE[0] / 3), 0)
    },
    {
        'center': (DEFAULT_SIZE[0], DEFAULT_SIZE[1]),
        'in': (DEFAULT_SIZE[0] - (DEFAULT_SIZE[0] / 3), DEFAULT_SIZE[1]),
        'out': (DEFAULT_SIZE[0] + (DEFAULT_SIZE[0] / 3), DEFAULT_SIZE[1])
    }
]


def get_default_controlpoints():
    controlpoints = []
    for point in DEFAULT_POINTS:
        controlpoints.append(
            ControlPoint(
                center=QtCore.QPointF(*point['center']),
                tangentin=QtCore.QPointF(*point['in']),
                tangentout=QtCore.QPointF(*point['out'])))
    return controlpoints


class ControlPoint(object):
    def __init__(self, center, tangentin, tangentout):
        self.center = QtCore.QPointF(center)
        self.tangentin = QtCore.QPointF(tangentin)
        self.tangentout = QtCore.QPointF(tangentout)

    def move(self, point):
        delta = self.center - point
        self.center -= delta
        self.tangentin -= delta
        self.tangentout -= delta

    def move_tangent(self, point):
        if point.x() < self.center.x():
            parent = self.tangentin
            child = self.tangentout
        else:
            parent = self.tangentout
            child = self.tangentin
        parent.setX(point.x())
        parent.setY(point.y())
        mirror = get_opposite_tangent(self.center, parent)
        child.setX(mirror.x())
        child.setY(mirror.y())

    def resize(self, old_size, new_size):
        move_point_from_rect_resized(self.center, old_size, new_size)
        move_point_from_rect_resized(self.tangentin, old_size, new_size)
        move_point_from_rect_resized(self.tangentout, old_size, new_size)

    def __lt__(self, controlpoint):
        return self.center.x() < controlpoint.center.x()


class InfluenceCurveWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(InfluenceCurveWidget, self).__init__(parent)
        self.setMinimumSize(*MINIMUM_SIZE)
        self.noresize = True
        self.resize(*DEFAULT_SIZE)
        self.setMouseTracking(True)
        self.is_clicked = False
        self.creation_mode = False
        self.controlpoints = get_default_controlpoints()

    def mouseMoveEvent(self, event):
        if self.is_clicked is False:
            return
        if self.center_to_move:
            self.center_to_move.move(event.pos())
            if self.creation_mode is True:
                auto_tangent_in_line(self.center_to_move, self.controlpoints)
            self.repaint()
            return
        if self.tangent_to_move:
            self.tangent_to_move.move_tangent(event.pos())
            self.repaint()

    def mousePressEvent(self, event):
        self.is_clicked = True
        self.center_to_move = pick_a_center(self.controlpoints, event.pos())
        self.tangent_to_move = pick_a_tangent(self.controlpoints, event.pos())
        if not self.center_to_move and not self.tangent_to_move:
            controlpoint = create_controlpoint_in_line(
                event.pos(), self.controlpoints)
            self.controlpoints.append(controlpoint)
            self.controlpoints = sorted(self.controlpoints)
            self.center_to_move = controlpoint
            self.creation_mode = True
        self.repaint()

    def mouseReleaseEvent(self, event):
        if self.center_to_move:
            if not self.rect().contains(self.center_to_move.center.toPoint()):
                self.controlpoints.remove(self.center_to_move)
        self.is_clicked = False
        self.creation_mode = False
        self.center_to_move = None
        self.tangent_to_move = None
        self.repaint()

    def resizeEvent(self, event):
        if self.noresize is True:
            return
        for controlpoint in self.controlpoints:
            controlpoint.resize(event.oldSize(), event.size())
        self.repaint()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        rect = self.rect()

        draw_grid(painter, rect)
        for controlpoint in self.controlpoints:
            draw_controlpoint(painter, controlpoint)
        path = get_line_path(self.controlpoints)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
        painter.setBrush(brush)
        painter.drawPath(path)

    def show(self):
        super(InfluenceCurveWidget, self).show()
        self.noresize = False


def create_controlpoint_in_line(position, controlpoints):
    controlpoints = sorted(controlpoints)
    before = controlpoints[0]
    for controlpoint in controlpoints[1:]:
        after = controlpoint
        if controlpoint.center.x() > position.x():
            break
        before = controlpoint

    controlpoint = ControlPoint(position, QtCore.QPoint(), QtCore.QPoint())
    auto_tangent(controlpoint, before, after)
    return controlpoint


def pick_a_center(controlpoints, position, tolerance=8):
    for controlpoint in controlpoints:
        if distance(controlpoint.center, position) < tolerance:
            return controlpoint


def pick_a_tangent(controlpoints, position, tolerance=8):
    for controlpoint in controlpoints:
        condition = (
            distance(controlpoint.tangentin, position) < tolerance or
            distance(controlpoint.tangentout, position) < tolerance)
        if condition:
            return controlpoint


def get_opposite_tangent(center, tangent):
    angle = get_angle(center, tangent) - math.pi
    ray = distance(center, tangent)
    return point_on_circle(angle, ray, center)


def get_angle(point1, point2):
    point3 = QtCore.QPointF(point2.x(), point1.y())
    return math.radians(get_absolute_angle_c(point3, point2, point1))


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


def point_on_circle(angle, ray, center):
    x = ray * math.cos(float(angle))
    y = ray * math.sin(float(angle))
    return QtCore.QPointF(center.x() + x, center.y() + y)


def get_angle_c(a, b, c):
    return math.degrees(math.atan(distance(a, b) / distance(a, c)))


def get_absolute_angle_c(a, b, c):
    quarter = get_quarter(a, b, c)
    try:
        angle_c = get_angle_c(a, b, c)
    except ZeroDivisionError:
        return 360 - (90 * quarter)

    if quarter == 0:
        return round(180.0 + angle_c, 1)
    elif quarter == 1:
        return round(270.0 + (90 - angle_c), 1)
    elif quarter == 2:
        return round(angle_c, 1)
    elif quarter == 3:
        return math.fabs(round(90.0 + (90 - angle_c), 1))


def distance(a, b):
    """ return distance between two points """
    x = (b.x() - a.x())**2
    y = (b.y() - a.y())**2
    return math.sqrt(abs(x + y))


def create_rect_from_center(center, segment_lenght=8):
    rectangle = QtCore.QRectF(0, 0, segment_lenght, segment_lenght)
    rectangle.moveCenter(center)
    return rectangle


def draw_controlpoint(painter, controlpoint):
    painter.setBrush(QtGui.QColor('red'))
    center_rect = create_rect_from_center(controlpoint.center)
    painter.drawRect(center_rect)

    painter.setBrush(QtGui.QColor(0, 0, 0, 0))
    painter.setPen(QtGui.QColor('red'))

    tin_rect = create_rect_from_center(controlpoint.tangentin)
    painter.drawRect(tin_rect)
    line = QtCore.QLine(controlpoint.tangentin.toPoint(),
                        controlpoint.center.toPoint())
    painter.drawLine(line)

    tout_rect = create_rect_from_center(controlpoint.tangentout)
    painter.drawRect(tout_rect)
    line = QtCore.QLine(controlpoint.center.toPoint(),
                        controlpoint.tangentout.toPoint())
    painter.drawLine(line)


def get_line_path(controlpoints):
    controlpoints = sorted(controlpoints)
    center = controlpoints[0].center
    out = controlpoints[0].tangentout
    path = QtGui.QPainterPath(center)
    for controlpoint in controlpoints:
        path.cubicTo(out, controlpoint.tangentin, controlpoint.center)
        out = controlpoint.tangentout
    return path


def draw_grid(painter, rect):
    pen = QtGui.QPen(QtGui.QColor('#111111'))
    pen.setStyle(QtCore.Qt.SolidLine)
    pen.setWidth(3)
    painter.setPen(pen)
    painter.setBrush(QtGui.QColor('#282828'))
    painter.drawRect(rect)
    pen = QtGui.QPen(QtGui.QColor('#323232'))
    painter.setPen(pen)

    for i in range(50):
        left = i * 20
        painter.drawLine(
            QtCore.QPoint(left, 2),
            QtCore.QPoint(left, rect.height() - 2))

    pen = QtGui.QPen(QtGui.QColor('#434343'))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawLine(
        QtCore.QPoint(100, 3),
        QtCore.QPoint(100, rect.height() - 3))

    pen = QtGui.QPen(QtGui.QColor('#323232'))
    painter.setPen(pen)
    painter.drawLine(
        QtCore.QPoint(3, rect.height() - 15),
        QtCore.QPoint(rect.width() - 3, rect.height() - 15))
    painter.drawLine(
        QtCore.QPoint(3, 15),
        QtCore.QPoint(rect.width() - 3, 15))


def move_point_from_rect_resized(point, old_size, new_size):
    x = (point.x() / old_size.width()) * new_size.width()
    y = (point.y() / old_size.height()) * new_size.height()
    point.setX(x)
    point.setY(y)


def auto_tangent_in_line(controlpoint, controlpoints):
    controlpoints = sorted(controlpoints)
    for i, _ in enumerate(controlpoints):
        if controlpoints[i] is controlpoint:
            auto_tangent(controlpoint, controlpoints[i-1], controlpoints[i+1])
            if i > 1:
                auto_tangent(controlpoints[i-1],
                             controlpoints[i-2], controlpoint)
            if i < len(controlpoints) - 2:
                auto_tangent(controlpoints[i+1],
                             controlpoint, controlpoints[i+2])
            return


def auto_tangent(controlpoint, before, after):
    ray = (
        distance(before.center, controlpoint.center) +
        distance(controlpoint.center, after.center)) / 5
    angle1 = get_angle(before.center, controlpoint.center)
    angle2 = get_angle(controlpoint.center, after.center)
    angle = (angle1 + angle2)
    tangent = point_on_circle(angle, ray, controlpoint.center)
    controlpoint.move_tangent(tangent)


def relative(value, in_min, in_max, out_min, out_max):
    """
    this function resolve simple equation and return the unknown value
    in between two values.
    a, a" = in_min, out_min
    b, b " = out_max, out_max
    c = value
    ? is the unknown processed by function.
    a --------- c --------- b
    a" --------------- ? ---------------- b"
    """
    factor = (value - in_min) / (in_max - in_min)
    width = out_max - out_min
    return out_min + (width * (factor))


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = InfluenceCurveWidget()
    win.show()
    app.exec_()

import math
from PyQt5 import QtGui, QtCore, QtWidgets


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


class ControlPoint(object):
    def __init__(self, center, tangentin, tangentout):
        self.center = QtCore.QPointF(center)
        self.tangentin = QtCore.QPointF(tangentin)
        self.tangentout = QtCore.QPointF(tangentout)

    def move(self, point):
        delta = self.center - point
        self.center += delta
        self.tangentin += delta
        self.tangentout += delta

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

    def __gt__(self, controlpoint):
        return self.center.x() > controlpoint.x()


class InfluenceCurveWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(InfluenceCurveWidget, self).__init__(parent)
        self.setMinimumSize(*MINIMUM_SIZE)
        self.resize(*DEFAULT_SIZE)

        self.setMouseTracking(True)
        self.is_clicked = False
        self.point_to_move = None
        self.point_to_move_is_boundary = None
        self.key_to_move = None
        self.noresize = True
        self.points = [d.copy() for d in DEFAULT_POINTS]

    def mouseMoveEvent(self, _):

        if self.is_clicked is False:
            return
        if not self.point_to_move:
            return
        center = self.point_to_move['center']
        cursor = self.mapFromGlobal(QtGui.QCursor.pos())
        x = center[0]
        y = cursor.y()
        inx = self.point_to_move['in'][0]
        if not self.point_to_move_is_boundary:
            x = cursor.x()
            inx += cursor.x() - center[0]
        else:
            if y < 0:
                y = 0
            if y > self.rect().bottom():
                y = self.rect().bottom()
        iny = self.point_to_move['in'][1] + y - center[1]
        if self.key_to_move == 'center':
            self.point_to_move['center'] = x, y
            self.point_to_move['in'] = inx, iny
            self.point_to_move['out'] = get_opposite_tangent(
                QtCore.QPointF(*self.point_to_move['center']),
                QtCore.QPointF(*self.point_to_move['in']))
            self.repaint()
            return
        relative = 'out' if self.key_to_move == 'in' else 'in'
        self.point_to_move[self.key_to_move] = cursor.x(), y
        self.point_to_move[relative] = get_opposite_tangent(
            QtCore.QPointF(*self.point_to_move['center']),
            QtCore.QPointF(*self.point_to_move[self.key_to_move]))
        self.repaint()

    def mousePressEvent(self, event):
        self.is_clicked = True
        point, key, index = find_point_to_move(self.points, event.pos())
        if point is None:
            position = event.pos()
            point = {
                'center': (position.x(), position.y()),
                'in': (position.x() - 30, position.y()),
                'out': (position.x() + 30, position.y())}
            self.points.append(point)
            key = 'center'
        self.point_to_move = point
        self.key_to_move = key
        is_boundary = index == 0 or index == len(self.points) - 1
        self.point_to_move_is_boundary = is_boundary

    def mouseReleaseEvent(self, event):
        self.is_clicked = False
        if self.point_to_move is None:
            return
        if not self.rect().contains(event.pos()):
            if not self.point_to_move_is_boundary:
                self.points.remove(self.point_to_move)
                'removed'
        self.point_to_move = None
        self.point_to_move_is_boundary = None
        self.repaint()

    def resizeEvent(self, event):
        if self.noresize is True:
            return
        for pointdata in self.points:
            pointdata['center'] = move_point_from_rect_resized(
                pointdata['center'], event.oldSize(), event.size())
            pointdata['in'] = move_point_from_rect_resized(
                pointdata['in'], event.oldSize(), event.size())
            pointdata['out'] = move_point_from_rect_resized(
                pointdata['out'], event.oldSize(), event.size())

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        rect = self.rect()

        draw_grid(painter, rect)
        for point in self.points:
            draw_point(painter, point)
        draw_line(painter, self.points)

    def show(self):
        super(InfluenceCurveWidget, self).show()
        self.noresize = False


def find_point_to_move(pointdatas, position, precision=8):
    pointdatas = sorted(pointdatas, key=lambda x: x['center'][0])
    for index, pointdata in enumerate(pointdatas):
        for key in ("center", "in", "out"):
            if distance(QtCore.QPoint(*pointdata[key]), position) < precision:
                return pointdata, key, index
    return None, None, None


def pick_a_center(controlpoints, position, precision=8):
    for controlpoint in controlpoints:
        if distance(controlpoint.center, position) > precision:
            return controlpoint


def pick_a_tangent(controlpoints, position, precision=8):
    for controlpoint in controlpoints:
        condition = (
            distance(controlpoint.tangentin, position) > precision or
            distance(controlpoint.tangentout, position) > precision)
        if condition:
            return controlpoint


def get_opposite_tangent(center, tangent):
    c = QtCore.QPointF(tangent.x(), center.y())
    angle = math.radians(get_absolute_angle_c(c, tangent, center)) - math.pi
    ray = distance(center, tangent)
    return get_point_on_circle(angle, ray, (center.x(), center.y()))


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


def get_point_on_circle(angle, ray, center):
    x = ray * math.cos(float(angle))
    y = ray * math.sin(float(angle))
    return center[0] + x, center[1] + y


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
    line = QtCore.QLine(controlpoint.tangentin.toPoint(), controlpoint.center.toPoint())
    painter.drawLine(line)

    tout_rect = create_rect_from_center(controlpoint.tangentout)
    painter.drawRect(tout_rect)
    line = QtCore.QLine(controlpoint.center.toPoint(), controlpoint.tangentout.toPoint())
    painter.drawLine(line)


def draw_point(painter, pointdatas):
    painter.setBrush(QtGui.QColor('red'))
    center = QtCore.QPointF(*pointdatas['center'])
    center_rect = create_rect_from_center(center)
    painter.drawRect(center_rect)

    painter.setBrush(QtGui.QColor(0, 0, 0, 0))
    painter.setPen(QtGui.QColor('red'))
    if pointdatas['in']:
        tin = QtCore.QPointF(*pointdatas['in'])
        tin_rect = create_rect_from_center(tin)
        painter.drawRect(tin_rect)
        painter.drawLine(QtCore.QLine(tin.toPoint(), center.toPoint()))

    if pointdatas['out']:
        tout = QtCore.QPointF(*pointdatas['out'])
        tout_rect = create_rect_from_center(tout)
        painter.drawRect(tout_rect)
        painter.drawLine(QtCore.QLine(center.toPoint(), tout.toPoint()))


def draw_line(painter, pointdatas):
    pointdatas = sorted(pointdatas, key=lambda x: x['center'][0])
    path = QtGui.QPainterPath(QtCore.QPointF(*pointdatas[0]['center']))
    out = QtCore.QPointF(*pointdatas[0]['out'])
    for pointdata in pointdatas[1:]:
        in_ = QtCore.QPointF(*pointdata['in'])
        center = QtCore.QPointF(*pointdata['center'])
        path.cubicTo(out, in_, center)
        out = QtCore.QPointF(*pointdata['out'])
    brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
    painter.setBrush(brush)
    painter.drawPath(path)


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
    x = (point[0] / old_size.width()) * new_size.width()
    y = (point[1] / old_size.height()) * new_size.height()
    return x, y


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

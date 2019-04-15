import math
from PyQt5 import QtGui, QtCore, QtWidgets


class InfluenceCurveWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(InfluenceCurveWidget, self).__init__(parent)
        self.points = [
            {
                'center': (150, 150),
                'in': (150, 130),
                'out': (150, 170)
            }]
        self._tangent_points = []

    def mouseMoveEvent(self, _):
        point = self.mapFromGlobal(QtGui.QCursor.pos())
        self.points[0]['in'] = point.x(), point.y()
        self.points[0]['out'] = get_opposite_tangent(
            QtCore.QPointF(*self.points[0]['center']),
            QtCore.QPointF(*self.points[0]['in']))
        self.repaint()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        rect = self.rect()

        draw_grid(painter, rect)
        for point in self.points:
            draw_point(painter, point)


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


def create_rect_from_center(center, segment_lenght=6):
    rectangle = QtCore.QRectF(0, 0, segment_lenght, segment_lenght)
    rectangle.moveCenter(center)
    return rectangle


def draw_point(painter, pointdatas):
    painter.setBrush(QtGui.QColor('red'))
    center = QtCore.QPointF(*pointdatas['center'])
    center_rect = create_rect_from_center(center)
    painter.drawRect(center_rect)

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
            QtCore.QPoint(left, rect.height() -2))

    pen = QtGui.QPen(QtGui.QColor('#434343'))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawLine(
        QtCore.QPoint(100, 3),
        QtCore.QPoint(100, rect.height() -3))

    pen = QtGui.QPen(QtGui.QColor('#323232'))
    painter.setPen(pen)
    painter.drawLine(
        QtCore.QPoint(3, rect.height() -15),
        QtCore.QPoint(rect.width() - 3, rect.height() - 15))
    painter.drawLine(
        QtCore.QPoint(3, 15),
        QtCore.QPoint(rect.width() - 3, 15))



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = InfluenceCurveWidget()
    win.show()
    app.exec_()
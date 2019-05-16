from PySide2 import QtCore, QtGui
from curvedeformereditor.arrayutils import split_value


COLORS = {
    'controlpoint.center': 'white',
    'controlpoint.centerselected': 'yellow',
    'controlpoint.tangentlocked': 'orange',
    'controlpoint.autotangent': 'red',
    'background.color': '#222222',
    'background.border': '#222222',
    'background.griddark': '#111111',
    'background.gridlight': '#353535',
    'bezier.border': '#151515',
    'bezier.body': 'grey',
    'bezier.borderwidth': 3
}


def create_rect_from_point(center, segment_lenght=8):
    rectangle = QtCore.QRectF(0, 0, segment_lenght, segment_lenght)
    rectangle.moveCenter(center)
    return rectangle


def clamp_point_in_rect(point, rect):
    if point.x() < rect.left():
        point.setX(rect.left())
    if point.x() > rect.right():
        point.setX(rect.right())
    if point.y() < rect.top():
        point.setY(rect.top())
    if point.y() > rect.bottom():
        point.setY(rect.bottom())


def create_beziercurve_path(controlpoints, rect=None):
    controlpoints = sorted(controlpoints)
    center = controlpoints[0].center
    out = controlpoints[0].tangentout
    path = QtGui.QPainterPath(center)
    for controlpoint in controlpoints:
        if controlpoint.linear is True:
            path.cubicTo(*[controlpoint.center] * 3)
            out = controlpoint.center
            continue
        path.cubicTo(out, controlpoint.tangentin, controlpoint.center)
        out = controlpoint.tangentout
    if rect is None:
        return path
    path.lineTo(rect.bottomRight())
    path.lineTo(rect.bottomLeft())
    path.lineTo(controlpoints[0].center)
    return path


def grow_rect(rect, value):
    return QtCore.QRect(
        rect.left() - value,
        rect.top() - value,
        rect.width() + (value * 2),
        rect.height() + (value * 2))


def draw_background(painter, rect, colors=None):
    colors = colors or COLORS.copy()
    pen = QtGui.QPen(QtGui.QColor(colors['background.griddark']))
    pen.setStyle(QtCore.Qt.SolidLine)
    pen.setWidth(3)
    painter.setPen(pen)
    painter.setBrush(QtGui.QColor(colors['background.color']))
    painter.drawRect(rect)


def draw_grid(
        painter, rect,
        vertical_small_graduation=25,
        horizontal_small_graduation=4,
        vertical_big_graduation=4,
        horizontal_big_graduation=-1,
        colors=None):
    colors = colors or COLORS.copy()

    pen = QtGui.QPen(QtGui.QColor(colors['background.griddark']))
    pen.setWidth(2)
    painter.setPen(pen)
    lefts = split_value(rect.width(), vertical_small_graduation)
    for left in lefts:
        painter.drawLine(
            QtCore.QPoint(left, 0),
            QtCore.QPoint(left, rect.bottom()))
    tops = split_value(rect.height(), horizontal_small_graduation)
    for top in tops:
        painter.drawLine(
            QtCore.QPoint(0, top),
            QtCore.QPoint(rect.right(), top))

    pen = QtGui.QPen(QtGui.QColor(colors['background.gridlight']))
    pen.setWidth(5)
    painter.setPen(pen)
    lefts = split_value(rect.width(), vertical_big_graduation)
    for left in lefts:
        painter.drawLine(
            QtCore.QPoint(left, 0),
            QtCore.QPoint(left, rect.bottom()))
    tops = split_value(rect.height(), horizontal_big_graduation)
    for top in tops:
        painter.drawLine(
            QtCore.QPoint(0, top),
            QtCore.QPoint(rect.right(), top))


def draw_controlpoint(painter, controlpoint, drawtangent=True, colors=None):
    colors = colors or COLORS.copy()
    selected = 'controlpoint.centerselected'
    colorkey = selected if controlpoint.selected else 'controlpoint.center'
    painter.setBrush(QtGui.QColor(colors[colorkey]))
    painter.setPen(QtGui.QColor(colors[colorkey]))
    center_rect = create_rect_from_point(controlpoint.center)
    painter.drawRect(center_rect)

    if drawtangent is False or controlpoint.linear is True:
        return

    painter.setBrush(QtGui.QColor(0, 0, 0, 0))
    if controlpoint.autotangent is True:
        color = colors['controlpoint.autotangent']
    else:
        color = colors['controlpoint.tangentlocked']
    painter.setPen(QtGui.QColor(color))

    tin_rect = create_rect_from_point(controlpoint.tangentin)
    painter.drawRect(tin_rect)
    line = QtCore.QLine(
        controlpoint.tangentin.toPoint(),
        controlpoint.center.toPoint())
    painter.drawLine(line)

    tout_rect = create_rect_from_point(controlpoint.tangentout)
    painter.drawRect(tout_rect)
    line = QtCore.QLine(
        controlpoint.center.toPoint(),
        controlpoint.tangentout.toPoint())
    painter.drawLine(line)


def draw_bezierpath(painter, path, colors=None):
    colors = colors or COLORS.copy()
    brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
    pen = QtGui.QPen(QtGui.QColor(colors['bezier.border']))
    pen.setWidth(colors['bezier.borderwidth'])
    painter.setBrush(brush)
    painter.setPen(pen)
    painter.drawPath(path)


def draw_bezierbody(painter, path, colors=None):
    colors = colors or COLORS.copy()
    brush = QtGui.QBrush(QtGui.QColor(colors['bezier.body']))
    painter.setBrush(brush)
    painter.setPen(QtGui.QColor(0, 0, 0, 0))
    painter.drawPath(path)

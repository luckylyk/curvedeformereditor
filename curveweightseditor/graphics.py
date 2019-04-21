from PyQt5 import QtGui, QtCore
from curveweightseditor.geometry import create_rect_from_center

COLORS = {
    'controlpoint.center': 'yellow',
    'controlpoint.tangentlocked': 'orange',
    'controlpoint.autotangent': 'red',
    'background.color': '#222222',
    'background.griddark': '#111111',
    'background.gridlight': '#555555',
    'background.gridmedium': '#353535',
    'line': 'red'
}


def draw_grid(painter, rect):
    pen = QtGui.QPen(QtGui.QColor(COLORS['background.griddark']))
    pen.setStyle(QtCore.Qt.SolidLine)
    pen.setWidth(3)
    painter.setPen(pen)
    painter.setBrush(QtGui.QColor(COLORS['background.color']))
    painter.drawRect(rect)
    pen = QtGui.QPen(QtGui.QColor(COLORS['background.griddark']))
    painter.setPen(pen)

    for i in range(50):
        left = i * 20
        painter.drawLine(
            QtCore.QPoint(left, 2),
            QtCore.QPoint(left, rect.height() - 2))

    pen = QtGui.QPen(QtGui.QColor(COLORS['background.gridlight']))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawLine(
        QtCore.QPoint(100, 3),
        QtCore.QPoint(100, rect.height() - 3))

    pen = QtGui.QPen(QtGui.QColor(COLORS['background.gridmedium']))
    painter.setPen(pen)
    painter.drawLine(
        QtCore.QPoint(3, rect.height() - 15),
        QtCore.QPoint(rect.width() - 3, rect.height() - 15))
    painter.drawLine(
        QtCore.QPoint(3, 15),
        QtCore.QPoint(rect.width() - 3, 15))


def draw_controlpoint(painter, controlpoint):
    painter.setBrush(QtGui.QColor(COLORS['controlpoint.center']))
    painter.setPen(QtGui.QColor(COLORS['controlpoint.center']))
    center_rect = create_rect_from_center(controlpoint.center)
    painter.drawRect(center_rect)

    painter.setBrush(QtGui.QColor(0, 0, 0, 0))
    if controlpoint.autotangent is True:
        color = COLORS['controlpoint.autotangent']
    else:
        color = COLORS['controlpoint.tangentlocked']
    painter.setPen(QtGui.QColor(color))

    tin_rect = create_rect_from_center(controlpoint.tangentin)
    painter.drawRect(tin_rect)
    line = QtCore.QLine(
        controlpoint.tangentin.toPoint(),
        controlpoint.center.toPoint())
    painter.drawLine(line)

    tout_rect = create_rect_from_center(controlpoint.tangentout)
    painter.drawRect(tout_rect)
    line = QtCore.QLine(
        controlpoint.center.toPoint(),
        controlpoint.tangentout.toPoint())
    painter.drawLine(line)


def draw_linepath(painter, path):
    brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
    painter.setBrush(brush)
    painter.setPen(QtGui.QColor(COLORS['line']))
    painter.drawPath(path)

# import sys

# sys.path.append('/nwave/software/PySide2/5.12.0-cp27/linux64/')
# sys.path.append('/nwave/software/shiboken2/5.12.0-cp27/linux64/')

from curveweightseditor.controlpoint import (
    ControlPoint, auto_tangent_line, pick_a_center, pick_a_tangent,
    create_controlpoint_in_line, extract_values)
from curveweightseditor.geometry import get_line_path
from curveweightseditor.graphics import (
    draw_grid, draw_controlpoint, draw_linepath)
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


def get_default_controlpoints():
    controlpoints = []
    for point in DEFAULT_POINTS:
        controlpoint = ControlPoint(
            center=QtCore.QPointF(*point['center']),
            tangentin=QtCore.QPointF(*point['in']),
            tangentout=QtCore.QPointF(*point['out']))
        controlpoint.isboundary = True
        controlpoints.append(controlpoint)

    return controlpoints


class CurveWeightEditorWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CurveWeightEditorWidget, self).__init__(parent)
        self.curve_graph_widget = CurveGraphWidget()
        self.apply = QtWidgets.QPushButton('apply')
        self.apply.released.connect(self.tadaaa)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.curve_graph_widget)
        self.layout.addWidget(self.apply)

    def tadaaa(self):
        print(self.curve_graph_widget.values(10))


class CurveGraphWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CurveGraphWidget, self).__init__(parent)
        self.setMinimumSize(*MINIMUM_SIZE)
        self.setFixedSize(*DEFAULT_SIZE)
        self.setMouseTracking(True)
        self.is_clicked = False
        self.center_to_move = None
        self.tangent_to_move = None
        self.controlpoints = get_default_controlpoints()

    def mouseMoveEvent(self, event):
        if self.is_clicked is False:
            return
        if self.center_to_move:
            rect = self.rect() if self.center_to_move.isboundary else None
            self.center_to_move.move(event.pos(), rect)
            auto_tangent_line(self.controlpoints)
            self.repaint()
            return
        if self.tangent_to_move:
            self.tangent_to_move.autotangent = False
            self.tangent_to_move.move_tangent(event.pos())
            auto_tangent_line(self.controlpoints, self.tangent_to_move)
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
            auto_tangent_line(self.controlpoints)
            self.center_to_move = controlpoint
        self.repaint()

    def mouseReleaseEvent(self, _):
        if self.center_to_move:
            if not self.rect().contains(self.center_to_move.center.toPoint()):
                self.controlpoints.remove(self.center_to_move)
        self.is_clicked = False
        self.center_to_move = None
        self.tangent_to_move = None
        self.repaint()

    def resizeEvent(self, event):
        if self.isVisible() is False:
            return
        for controlpoint in self.controlpoints:
            controlpoint.resize(event.oldSize(), event.size())
        self.repaint()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect()

        draw_grid(painter, rect)
        for controlpoint in self.controlpoints:
            draw_controlpoint(painter, controlpoint)
        path = get_line_path(self.controlpoints)
        draw_linepath(painter, path)

    def values(self, sample):
        path = get_line_path(self.controlpoints)
        points = extract_values(path, self.rect(), sample)
        return [1 - (point.y() / self.rect().height()) for point in points]

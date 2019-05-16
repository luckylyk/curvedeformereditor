import math
from PySide2 import QtWidgets, QtCore, QtGui
from curvedeformereditor.drawing import (
    draw_background, draw_bezierpath, draw_controlpoint, draw_grid, COLORS,
    grow_rect, create_beziercurve_path, draw_bezierbody)
from curvedeformereditor.beziercurve import (
    pick_controlpoint_center, auto_tangent_smoothed, auto_tangent_beziercurve,
    pick_controlpoint_tangent, insert_controlpoint_in_curve,
    select_controlpoint, auto_tangent_flatten, create_beziercurve,
    compute_bezier_curve_values)


class BezierEqualizer(QtWidgets.QWidget):
    bezierCurveEdited = QtCore.Signal()
    bezierCurveEditBegin = QtCore.Signal()
    bezierCurveEditEnd = QtCore.Signal()

    Smoothed = 0
    Flatten = 1

    def __init__(self, parent=None):
        super(BezierEqualizer, self).__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(QtCore.QSize(250, 100))

        self.renderhint = QtGui.QPainter.Antialiasing
        self.colors = COLORS.copy()
        self.isclicked = False
        self.gridvisible = True
        self.editabletangents = True
        self.drawbody = False
        self.grid_horizontal_divisions = 5
        self.grid_vertical_divisions = 25
        self.grid_main_disivions_mult = 4
        self.auto_tangent_function = auto_tangent_smoothed
        self.holding = False

        self.picked_center = None
        self.picked_tangent = None
        self.controlpoints = []

    def _fix_boundaries(self):
        if not self.controlpoints:
            return
        #  this ensure the bezier curve is well stick to widget borders
        self.controlpoints[0].center.setX(self.rect().left())
        self.controlpoints[-1].center.setX(self.rect().right())

    def mouseMoveEvent(self, event):
        if self.isclicked is False:
            return

        if self.editabletangents is True and self.picked_tangent is not None:
            self.picked_tangent.autotangent = False
            self.picked_tangent.move_tangent(event.pos())
            auto_tangent_beziercurve(
                controlpoints=self.controlpoints,
                skip=self.picked_tangent,
                auto_tangent_function=self.auto_tangent_function)
            self.repaint()
            self.bezierCurveEdited.emit()
            return

        if not self.picked_center:
            self.repaint()
            self.bezierCurveEdited.emit()
            return
        rect = self.rect()
        point = event.pos()
        cursor = self.mapFromGlobal(QtGui.QCursor.pos())
        self.picked_center.move(point, rect)
        offset = (rect.width() + rect.height()) / 10
        extended_rect = grow_rect(rect, offset)
        if self.picked_center.isboundary is True:
            self._fix_boundaries()
            self.repaint()
            self.bezierCurveEdited.emit()
            return
        if not extended_rect.contains(cursor) and self.holding is False:
            self.controlpoints.remove(self.picked_center)
            self.holding = True
        elif extended_rect.contains(cursor) and self.holding is True:
            self.controlpoints.append(self.picked_center)
            self.controlpoints = sorted(self.controlpoints)
            self.holding = False
        auto_tangent_beziercurve(
            controlpoints=self.controlpoints,
            auto_tangent_function=self.auto_tangent_function)
        self.repaint()
        self.bezierCurveEdited.emit()

    def mousePressEvent(self, event):
        if not self.controlpoints:
            return

        self.isclicked = True
        point = event.pos()
        controlpoints = self.controlpoints
        self.picked_center = pick_controlpoint_center(controlpoints, point)
        self.picked_tangent = pick_controlpoint_tangent(controlpoints, point)

        if not self.picked_center and not self.picked_tangent:
            controlpoint = insert_controlpoint_in_curve(point, controlpoints)
            self.controlpoints.append(controlpoint)
            self.controlpoints = sorted(controlpoints)
            auto_tangent_beziercurve(
                self.controlpoints, self.auto_tangent_function)
            self.picked_center = controlpoint

        if self.picked_center:
            select_controlpoint(self.picked_center, self.controlpoints)

        self.repaint()
        self.bezierCurveEditBegin.emit()

    def mouseReleaseEvent(self, _):
        self.isclicked = False
        self.picked_center = None
        self.picked_tangent = None
        self.holding = False
        self.repaint()
        self.bezierCurveEditEnd.emit()

    def resizeEvent(self, event):
        if self.isVisible() is False or not self.controlpoints:
            return
        for controlpoint in self.controlpoints:
            controlpoint.resize(event.oldSize(), event.size())
        self._fix_boundaries()
        self.repaint()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(self.renderhint)
        rect = self.rect()
        draw_background(painter, rect, self.colors)
        if self.gridvisible is True:
            draw_grid(
                painter, rect,
                vertical_small_graduation=self.grid_vertical_divisions,
                horizontal_small_graduation=self.grid_horizontal_divisions,
                vertical_big_graduation=self.grid_main_disivions_mult,
                horizontal_big_graduation=self.grid_main_disivions_mult,
                colors=None)
        if not self.controlpoints:
            return
        if self.drawbody is True:
            path = create_beziercurve_path(self.controlpoints, self.rect())
            draw_bezierbody(painter, path, self.colors)
        path = create_beziercurve_path(self.controlpoints)
        draw_bezierpath(painter, path, self.colors)
        for controlpoint in self.controlpoints:
            draw_controlpoint(
                painter=painter,
                controlpoint=controlpoint,
                drawtangent=self.editabletangents,
                colors=self.colors)

    def clear(self):
        self.controlpoints = []

    def values(self, sample):
        rect = self.rect()
        return compute_bezier_curve_values(self.controlpoints[:], rect, sample)

    def selectedControlPoint(self):
        for controlpoint in self.controlpoints:
            if controlpoint.selected is True:
                return controlpoint
        return None

    def setValues(self, values):
        if not values:
            self.controlpoints = []
            return
        if len(values) == 1:
            raise ValueError('At least 2 values has to be provided')
        rect = self.rect()
        self.controlpoints = create_beziercurve(values, rect, linear=True)
        self.controlpoints[0].isboundary = True
        self.controlpoints[-1].isboundary = True
        self.repaint()

    def setColor(self, key, colorname):
        if key not in self.colors:
            raise KeyError('{} is not a valid key'.format(key))
        self.colors[key] = colorname

    def updateColors(self, colors):
        for key in colors:
            if key not in self.colors:
                raise KeyError('{} is not a valid key'.format(key))
        self.colors.update(colors)

    def autoTangent(self):
        auto_tangent_beziercurve(
            self.controlpoints, self.auto_tangent_function)
        self.repaint()

    def setRenderHint(self, renderhint):
        self.renderhint = renderhint

    def setGridVisible(self, state):
        self.gridvisible = state

    def setEditableTangents(self, state):
        self.editabletangents = state

    def setBodyVisible(self, state):
        self.drawbody = state

    def setGridHorizontalDivision(self, division):
        self.grid_horizontal_divisions = division

    def setGridVerticalDivision(self, division):
        self.grid_vertical_divisions = division

    def setGridMainDivisionsMult(self, division):
        self.grid_main_disivions_mult = division

    def setAutoTangentMode(self, mode):
        auto_tangent_functions = [
            auto_tangent_smoothed,
            auto_tangent_flatten]
        self.auto_tangent_function = auto_tangent_functions[mode]

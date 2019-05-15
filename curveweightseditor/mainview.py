import os
import maya.OpenMaya as om
from maya import cmds
from PySide2 import QtWidgets, QtCore, QtGui
from curveweightseditor.bezierequalizer import BezierEqualizer
from curveweightseditor.nurbsutils import (
    get_blendshape_weights_per_cv, set_blendshape_weights_per_cv, count_cv)


def icon(filename):
    path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'icons', filename)
    return QtGui.QIcon(path)


class CurveDeformerWeightEditor(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(CurveDeformerWeightEditor, self).__init__(parent, QtCore.Qt.Tool)
        self.controlpoints_per_deformers = {}
        self.callbacks = []
        self.curves = []

        self.linear_selected = QtWidgets.QAction('linear', self)
        self.linear_selected.triggered.connect(self._call_linear_selected)
        self.smooth_selected = QtWidgets.QAction('smooth', self)
        self.smooth_selected.triggered.connect(self._call_smooth_selected)
        self.linear_all = QtWidgets.QAction('linear all', self)
        self.linear_all.triggered.connect(self._call_linear_all)
        self.smooth_all = QtWidgets.QAction('smooth all', self)
        self.smooth_all.triggered.connect(self._call_smooth_all)
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.addAction(self.linear_selected)
        self.toolbar.addAction(self.smooth_selected)
        self.toolbar.addAction(self.linear_all)
        self.toolbar.addAction(self.smooth_all)

        self.bezierequalizer = BezierEqualizer()
        self.bezierequalizer.setGridVisible(False)
        self.bezierequalizer.setEditableTangents(False)
        self.bezierequalizer.setBodyVisible(True)
        self.bezierequalizer.setAutoTangentMode(BezierEqualizer.Flatten)
        self.bezierequalizer.bezierCurveEdited.connect(self.weightschanged)
        self.bezierequalizer.bezierCurveEditBegin.connect(open_undochunk)
        self.bezierequalizer.bezierCurveEditEnd.connect(close_undochunk)

        self.blendshapes = QtWidgets.QComboBox()
        self.blendshapes.currentTextChanged.connect(self._call_update_values)

        self.smooth_in = QtWidgets.QAction(icon('smooth_in.png'), '', self)
        self.smooth_in.triggered.connect(self._call_smooth_in)
        self.smooth_out = QtWidgets.QAction(icon('smooth_out.png'), '', self)
        self.smooth_out.triggered.connect(self._call_smooth_out)
        self.linear_in = QtWidgets.QAction(icon('linear_in.png'), '', self)
        self.linear_in.triggered.connect(self._call_linear_in)
        self.linear_out = QtWidgets.QAction(icon('linear_out.png'), '', self)
        self.linear_out.triggered.connect(self._call_linear_out)
        self.full = QtWidgets.QAction(icon('full.png'), '', self)
        self.full.triggered.connect(self._call_full)
        self.off = QtWidgets.QAction(icon('off.png'), '', self)
        self.off.triggered.connect(self._call_off)
        self.spike = QtWidgets.QAction(icon('positive_spike.png'), '', self)
        self.spike.triggered.connect(self._call_positive_spike)
        self.spike2 = QtWidgets.QAction(icon('negative_spike.png'), '', self)
        self.spike2.triggered.connect(self._call_negative_spike)
        self.presets = QtWidgets.QToolBar()
        self.presets.setIconSize(QtCore.QSize(16, 16))
        self.presets.addWidget(QtWidgets.QLabel('predifined'))
        self.presets.addAction(self.smooth_in)
        self.presets.addAction(self.smooth_out)
        self.presets.addAction(self.linear_in)
        self.presets.addAction(self.linear_out)
        self.presets.addAction(self.full)
        self.presets.addAction(self.off)
        self.presets.addAction(self.spike)
        self.presets.addAction(self.spike2)

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.addWidget(self.toolbar)
        self.hlayout.addWidget(self.blendshapes)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.hlayout)
        self.layout.addWidget(self.bezierequalizer)
        self.layout.addWidget(self.presets)

        self.maya_selection_changed()
        self.register_callback()

    def show(self):
        super(CurveDeformerWeightEditor, self).show()
        self.register_callback()
        self.maya_selection_changed()

    def _call_smooth_all(self):
        for controlpoint in self.bezierequalizer.controlpoints:
            controlpoint.linear = False
        self.bezierequalizer.repaint()
        self.weightschanged()

    def _call_smooth_selected(self):
        for controlpoint in self.bezierequalizer.controlpoints:
            if controlpoint.selected:
                controlpoint.linear = False
        self.bezierequalizer.repaint()
        self.weightschanged()

    def _call_linear_selected(self):
        for controlpoint in self.bezierequalizer.controlpoints:
            if controlpoint.selected:
                controlpoint.linear = True
        self.bezierequalizer.repaint()
        self.weightschanged()

    def _call_linear_all(self):
        for controlpoint in self.bezierequalizer.controlpoints:
            controlpoint.linear = True
        self.bezierequalizer.repaint()
        self.weightschanged()

    def _call_update_values(self, *_):
        blendshape = self.blendshapes.currentText()
        if not blendshape or not self.curves:
            self.bezierequalizer.setValues([])
            return
        # TODO: Doc, eplain this
        curves = self.controlpoints_per_deformers.get(blendshape)
        if curves:
            controlpoints = curves[self.curves[0]]
            if controlpoints:
                self.bezierequalizer.controlpoints = controlpoints
                self.bezierequalizer.repaint()
                return
        values = get_blendshape_weights_per_cv(self.curves[0], blendshape)
        self.bezierequalizer.setValues(values)

    def _call_smooth_in(self):
        self.bezierequalizer.setValues([0.0, 0.0, 1.0, 1.0])
        for controlpoint in self.bezierequalizer.controlpoints:
            controlpoint.linear = False
        self.bezierequalizer.autoTangent()
        self.bezierequalizer.repaint()
        self.weightschanged()

    def _call_smooth_out(self):
        self.bezierequalizer.setValues([1.0, 1.0, 0.0, 0.0])
        for controlpoint in self.bezierequalizer.controlpoints:
            controlpoint.linear = False
        self.bezierequalizer.autoTangent()
        self.bezierequalizer.repaint()
        self.weightschanged()

    def _call_linear_in(self):
        self.bezierequalizer.setValues([0.0, 1.0])
        self.weightschanged()

    def _call_linear_out(self):
        self.bezierequalizer.setValues([1.0, 0.0])
        self.weightschanged()

    def _call_full(self):
        self.bezierequalizer.setValues([1.0, 1.0])
        self.weightschanged()

    def _call_off(self):
        self.bezierequalizer.setValues([0.0, 0.0])
        self.weightschanged()

    def _call_positive_spike(self):
        self.bezierequalizer.setValues([0.0, 1.0, 0.0])
        self.weightschanged()

    def _call_negative_spike(self):
        self.bezierequalizer.setValues([1.0, 0.0, 1.0])
        self.weightschanged()

    def closeEvent(self, event):
        super(CurveDeformerWeightEditor, self).closeEvent(event)
        self.unregister_callback()

    def hide(self):
        super(CurveDeformerWeightEditor, self).hide()
        self.unregister_callback()

    def weightschanged(self):
        blendshape = self.blendshapes.currentText()
        if not blendshape:
            return
        for curve in self.curves:
            sample = count_cv(curve)
            weights = self.bezierequalizer.values(sample)
            set_blendshape_weights_per_cv(curve, blendshape, weights)
        # TODO: Doc, eplain this
        cp = self.bezierequalizer.controlpoints
        if not self.controlpoints_per_deformers.get(blendshape):
            self.controlpoints_per_deformers[blendshape] = {}
        self.controlpoints_per_deformers[blendshape][self.curves[0]] = cp

    def register_callback(self):
        method = self.maya_selection_changed
        cb = om.MEventMessage.addEventCallback('SelectionChanged', method)
        self.callbacks.append(cb)

    def unregister_callback(self):
        for callback in self.callbacks:
            om.MMessage.removeCallback(callback)
        self.callbacks = []

    def maya_selection_changed(self, *_):
        self.blendshapes.clear()
        shapes = cmds.ls(
            selection=True, dag=True, long=True, type='nurbsCurve',
            noIntermediate=True)
        self.curves = [cmds.listRelatives(s, parent=True)[0] for s in shapes]
        if not self.curves:
            self.bezierequalizer.clear()
            self.setEnabled(False)
            return
        self.setEnabled(True)
        blendshapes = cmds.ls(cmds.listHistory(self.curves), type='blendShape')
        self.blendshapes.addItems(blendshapes)
        self._call_update_values()


def open_undochunk():
    cmds.undoInfo(openChunk=True)


def close_undochunk():
    cmds.undoInfo(closeChunk=True)

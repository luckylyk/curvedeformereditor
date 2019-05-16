import os
import maya.OpenMaya as om
from maya import cmds
from PySide2 import QtWidgets, QtCore, QtGui
from curvedeformereditor.bezierequalizer import BezierEqualizer
from curvedeformereditor.nurbsutils import (
    get_deformer_weights_per_cv, set_deformer_weights_per_cv, count_cv)


SUPPORTED_DEFORMERS = 'blendShape', 'cluster'
WINDOW_TITLE = 'Curve Deformer Editor'


def icon(filename):
    path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'icons', filename)
    return QtGui.QIcon(path)


class CurveDeformerEditor(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(CurveDeformerEditor, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle(WINDOW_TITLE)

        self.controlpoints_per_deformers = {}
        self.callbacks = []
        self.reset_memory_callbacks = None
        self.curves = []

        img = icon('linear_selected.png')
        self.linear_selected = QtWidgets.QAction(img, '', self)
        self.linear_selected.setToolTip('linear selected')
        self.linear_selected.triggered.connect(self._call_linear_selected)
        img = icon('smooth_selected.png')
        self.smooth_selected = QtWidgets.QAction(img, '', self)
        self.smooth_selected.setToolTip('smooth selected')
        self.smooth_selected.triggered.connect(self._call_smooth_selected)
        img = icon('linear_all.png')
        self.linear_all = QtWidgets.QAction(img, '', self)
        self.linear_all.setToolTip('linear all')
        self.linear_all.triggered.connect(self._call_linear_all)
        img = icon('smooth_all.png')
        self.smooth_all = QtWidgets.QAction(img, '', self)
        self.smooth_all.setToolTip('smooth all')
        self.smooth_all.triggered.connect(self._call_smooth_all)
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(20, 20))
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

        self.deformers = QtWidgets.QComboBox()
        self.deformers.currentTextChanged.connect(self._call_update_values)

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
        self.hlayout.addWidget(self.deformers)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.hlayout)
        self.layout.addWidget(self.bezierequalizer)
        self.layout.addWidget(self.presets)

        self.maya_selection_changed()
        self.register_callback()

    def show(self):
        super(CurveDeformerEditor, self).show()
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
        deformer = self.deformers.currentText()
        if not deformer or not self.curves:
            self.bezierequalizer.setValues([])
            return
        # TODO: Doc, eplain this
        curves = self.controlpoints_per_deformers.get(deformer)
        if curves:
            controlpoints = curves[self.curves[0]]
            if controlpoints:
                self.bezierequalizer.controlpoints = controlpoints
                self.bezierequalizer.repaint()
                return
        values = get_deformer_weights_per_cv(self.curves[0], deformer)
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
        super(CurveDeformerEditor, self).closeEvent(event)
        self.unregister_callback()

    def hide(self):
        super(CurveDeformerEditor, self).hide()
        self.unregister_callback()

    def weightschanged(self):
        deformer = self.deformers.currentText()
        if not deformer:
            return
        for curve in self.curves:
            sample = count_cv(curve)
            weights = self.bezierequalizer.values(sample)
            set_deformer_weights_per_cv(curve, deformer, weights)
        # TODO: Doc, eplain this
        cp = self.bezierequalizer.controlpoints
        if not self.controlpoints_per_deformers.get(deformer):
            self.controlpoints_per_deformers[deformer] = {}
        self.controlpoints_per_deformers[deformer][self.curves[0]] = cp

    def register_callback(self):
        method = self.maya_selection_changed
        cb = om.MEventMessage.addEventCallback('SelectionChanged', method)
        self.callbacks.append(cb)
        if self.reset_memory_callbacks is not None:
            return
        self.reset_memory_callbacks = []
        events = om.MSceneMessage.kBeforeNew, om.MSceneMessage.kBeforeOpen
        for event in events:
            cb = om.MSceneMessage.addCallback(event, self.reset_memory)
            self.reset_memory_callbacks.append(cb)

    def unregister_callback(self):
        for callback in self.callbacks:
            om.MMessage.removeCallback(callback)
        self.callbacks = []

    def reset_memory(self, *_):
        self.controlpoints_per_deformers = {}

    def maya_selection_changed(self, *_):
        self.deformers.clear()
        shapes = cmds.ls(
            selection=True, dag=True, long=True, type='nurbsCurve',
            noIntermediate=True)
        self.curves = [cmds.listRelatives(s, parent=True)[0] for s in shapes]
        if not self.curves:
            self.bezierequalizer.clear()
            self.setEnabled(False)
            return
        self.setEnabled(True)
        history = cmds.listHistory(self.curves)
        deformers = cmds.ls(history, type=SUPPORTED_DEFORMERS)
        self.deformers.addItems(deformers)
        self._call_update_values()


def open_undochunk():
    cmds.undoInfo(openChunk=True)


def close_undochunk():
    cmds.undoInfo(closeChunk=True)

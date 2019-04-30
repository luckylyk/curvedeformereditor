
from maya import cmds
from PySide2 import QtWidgets, QtCore
from curveweighteditor.bezierequalizer import BezierEqualizer
import maya.OpenMaya as om


class CurveDeformerWeightEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CurveDeformerWeightEditor, self).__init__(parent, QtCore.Qt.Tool)
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
        self.bezierequalizer.setAutotangentMode(BezierEqualizer.Flatten)
        self.bezierequalizer.bezierCurveEdited.connect(self.weightschanged)
        self.bezierequalizer.bezierCurveEditBegin.connect(open_undochunk)
        self.bezierequalizer.bezierCurveEditEnd.connect(close_undochunk)

        self.blendshapes = QtWidgets.QComboBox()
        self.blendshapes.currentTextChanged.connect(self._call_update_values)

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.addWidget(self.toolbar)
        self.hlayout.addWidget(self.blendshapes)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.hlayout)
        self.layout.addWidget(self.bezierequalizer)

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

    def _call_smooth_selected(self):
        for controlpoint in self.bezierequalizer.controlpoints:
            if controlpoint.selected:
                controlpoint.linear = False
        self.bezierequalizer.repaint()

    def _call_linear_selected(self):
        for controlpoint in self.bezierequalizer.controlpoints:
            if controlpoint.selected:
                controlpoint.linear = True
        self.bezierequalizer.repaint()

    def _call_linear_all(self):
        for controlpoint in self.bezierequalizer.controlpoints:
            controlpoint.linear = True
        self.bezierequalizer.repaint()

    def _call_update_values(self, *_):
        blendshape = self.blendshapes.currentText()
        if not blendshape or not self.curves:
            self.bezierequalizer.setValues([])
            return
        values = get_blendshape_weights_per_cv(self.curves[0], blendshape)
        self.bezierequalizer.setValues(values)

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

    def register_callback(self):
        method = self.maya_selection_changed
        cb = om.MEventMessage.addEventCallback('SelectionChanged', method)
        self.callbacks.append(cb)

    def unregister_callback(self):
        for callback in self.callbacks:
            om.MMessage.removeCallback(callback)
        self.callbacks = []

    def maya_selection_changed(self, *_):
        shapes = cmds.ls(
            selection=True, dag=True, long=True, type='nurbsCurve',
            noIntermediate=True)
        self.curves = [cmds.listRelatives(s, parent=True)[0] for s in shapes]
        if not self.curves:
            return
        blendshapes = cmds.ls(cmds.listHistory(self.curves), type='blendShape')
        self.blendshapes.clear()
        self.blendshapes.addItems(blendshapes)
        self._call_update_values()


def open_undochunk():
    cmds.undoInfo(openChunk=True)


def close_undochunk():
    cmds.undoInfo(closeChunk=True)


def get_blendshape_weights_per_cv(curve, blendshape, index=0):
    attr = (
        blendshape + ".inputTarget[{}].inputTargetGroup[0].targetWeights[{}]")
    return [
        cmds.getAttr(attr.format(index, i))
        for i in range(count_cv(curve))]


def set_blendshape_weights_per_cv(curve, blendshape, values, index=0):
    attr = (
        blendshape + ".inputTarget[{}].inputTargetGroup[0].targetWeights[{}]")
    for i, v in enumerate(values):
        cmds.setAttr(attr.format(index, i), v)


def count_cv(curve):
    return cmds.getAttr(curve + '.degree') + cmds.getAttr(curve + '.spans')


if __name__ == "__main__":
    import shiboken2
    import maya.OpenMayaUI as omui
    main_window = omui.MQtUtil.mainWindow()
    parent = shiboken2.wrapInstance(long(main_window), QtWidgets.QWidget)
    wid = CurveDeformerWeightEditor(parent)
    wid.show()

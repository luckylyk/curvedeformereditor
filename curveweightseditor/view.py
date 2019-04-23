
from maya import cmds
from PySide2 import QtWidgets, QtCore
from curveweighteditor.bezierequalizer import BezierEqualizer
import maya.OpenMaya as om


class CurveDeformerWeightEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CurveDeformerWeightEditor, self).__init__(parent)
        self.callbacks = []
        self.curves = []

        self.bezierequalizer = BezierEqualizer()
        self.bezierequalizer.setGridVisible(False)
        self.bezierequalizer.setEditableTangents(False)
        self.bezierequalizer.setBodyVisible(True)
        self.bezierequalizer.bezierCurveEdited.connect(self.weightschanged)
        self.bezierequalizer.bezierCurveEditBegin.connect(self.startedit)
        self.bezierequalizer.bezierCurveEditEnd.connect(self.stopedit)

        self.blendshapes = QtWidgets.QComboBox()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.blendshapes)
        self.layout.addWidget(self.bezierequalizer)

        self.register_callback()

    def show(self):
        super(CurveDeformerWeightEditor, self).show()
        self.register_callback()

    def closeEvent(self, event):
        super(CurveDeformerWeightEditor, self).closeEvent(event)
        self.unregister_callback()

    def hide(self):
        super(CurveDeformerWeightEditor, self).hide()
        self.unregister_callback()

    def startedit(self):
        cmds.undoInfo(openChunk=True)

    def stopedit(self):
        cmds.undoInfo(closeChunk=True)

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
        self._callbacks = []

    def maya_selection_changed(self, *callback_args):
        shapes = cmds.ls(
            selection=True, dag=True, long=True, type='nurbsCurve',
            noIntermediate=True)
        self.curves = [cmds.listRelatives(s, parent=True)[0] for s in shapes]
        if not self.curves:
            return
        blendshapes = cmds.ls(cmds.listHistory(self.curves), type='blendShape')
        self.blendshapes.clear()
        self.blendshapes.addItems(blendshapes)
        self.bezierequalizer.setValues([1, 0])


def get_blendshape_weights_per_cv(curve, blendshape):
    attr = blendshape + ".inputTarget[0].inputTargetGroup[0].targetWeights[{}]"
    return [cmds.getAttr(attr.format(i)) for i in range(count_cv(curve))]


def set_blendshape_weights_per_cv(curve, blendshape, values):
    attr = blendshape + ".inputTarget[0].inputTargetGroup[0].targetWeights[{}]"
    for i, v in enumerate(values):
        cmds.setAttr(attr.format(i), v)


def count_cv(curve):
    return cmds.getAttr(curve + '.degree') + cmds.getAttr(curve + '.spans')


if __name__ == "__main__":
    wid = CurveDeformerWeightEditor()
    wid.show()

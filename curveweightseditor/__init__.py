import shiboken2
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets
from curveweightseditor.mainview import CurveDeformerWeightEditor


_curve_weight_editor = None


def launch():
    global _curve_weight_editor
    if _curve_weight_editor is None:
        main_window = omui.MQtUtil.mainWindow()
        parent = shiboken2.wrapInstance(long(main_window), QtWidgets.QWidget)
        _curve_weight_editor = CurveDeformerWeightEditor(parent)
    _curve_weight_editor.show()

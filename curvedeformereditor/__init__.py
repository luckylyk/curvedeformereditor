import shiboken2
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets
from curvedeformereditor.mainview import CurveDeformerEditor


_curve_deformer_editor = None


def launch():
    global _curve_deformer_editor
    if _curve_deformer_editor is None:
        main_window = omui.MQtUtil.mainWindow()
        parent = shiboken2.wrapInstance(long(main_window), QtWidgets.QWidget)
        _curve_deformer_editor = CurveDeformerEditor(parent)
    _curve_deformer_editor.show()


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

if __name__ == '__main__':

    from PyQt5 import QtWidgets
    from curveweightseditor.curvewidget import CurveWeightEditorWidget
    app = QtWidgets.QApplication([])
    win = CurveWeightEditorWidget()
    win.show()
    app.exec_()

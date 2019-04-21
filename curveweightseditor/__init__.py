
import sys
import os
print(os.path.basename(os.path.basename(__file__)))
sys.path.append(os.path.basename(os.path.basename(__file__)))

if __name__ == '__main__':

    from PyQt5 import QtWidgets
    from curveweightseditor.curvewidget import InfluenceCurveWidget
    app = QtWidgets.QApplication([])
    win = InfluenceCurveWidget()
    win.show()
    app.exec_()

from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QMainWindow,QPushButton
import sys
import ASAXS_Widget


class XAnoS(QMainWindow):
    def __init__(self,parent=None):
        QMainWindow.__init__(self,parent=parent)
        loadUi('UI_Forms/XAnoS.ui',self)
        self.init_signals()

    def init_signals(self):
        self.ASAXSReducerPushButton.clicked.connect(self.launch_ASAXSWidget)


    def launch_ASAXSWidget(self):
        w = ASAXS_Widget.ASAXS_Widget(parent=self)
        w.setWindowTitle('ASAXS Widget')
        w.setGeometry(20, 20, 1000, 800)
        w.show()


if __name__=='__main__':
    app=QApplication(sys.argv)
    w=XAnoS()
    w.show()
    sys.exit(app.exec_())
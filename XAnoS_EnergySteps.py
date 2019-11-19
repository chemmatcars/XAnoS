from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtTest import QTest
import sys
import numpy as np
import copy
import time
from xraydb import XrayDB



class XAnoS_EnergySteps(QWidget):
    """
    """

    def __init__(self, parent=None):
        """
        """
        QWidget.__init__(self, parent)
        loadUi('UI_Forms/XAnoS_EnergySteps.ui', self)
        self.xrdb = XrayDB()
        self.initialize_UI()


    def initialize_UI(self):
        self.elements = self.xrdb.atomic_symbols
        self.elementComboBox.addItems(
            [str(self.xrdb.atomic_number(element)) + ': ' + element for element in self.elements])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = XAnoS_EnergySteps()
    w.setWindowTitle('Energy Steps')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())

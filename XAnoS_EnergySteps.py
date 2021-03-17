from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QFileDialog, QMessageBox
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
    This widget calculates the Energy values at which the f' values are equidistant below the absorption edge of a selected element
    """
    def __init__(self, parent=None):
        """
        """
        QWidget.__init__(self, parent)
        loadUi('UI_Forms/XAnoS_EnergySteps.ui', self)
        self.xrdb = XrayDB()
        self.initialize_UI()
        self.init_signals()

    def initialize_UI(self):
        self.doubleValidator=QDoubleValidator()
        self.elements = self.xrdb.atomic_symbols
        self.elementComboBox.addItems(
            [str(self.xrdb.atomic_number(element)) + ': ' + element for element in self.elements])
        self.element=self.elementComboBox.currentText().split(': ')[1]
        edges = self.xrdb.xray_edges(self.element)
        self.edgeComboBox.addItems([key + ': %.4f' % (edges[key].energy / 1000) for key in edges.keys()])
        self.EOffsetLineEdit.setValidator(self.doubleValidator)
        self.minEnergyLineEdit.setValidator(self.doubleValidator)
        self.maxEnergyLineEdit.setValidator(self.doubleValidator)
        self.edgeChanged(self.edgeComboBox.currentText())
        self.NStepsChanged(20)
        self.energyOffset=float(self.EOffsetLineEdit.text())


    def init_signals(self):
        self.elementComboBox.currentTextChanged.connect(self.elementChanged)
        self.edgeComboBox.currentTextChanged.connect(self.edgeChanged)
        self.EOffsetLineEdit.textChanged.connect(self.energyOffsetChanged)
        self.minEnergyLineEdit.textChanged.connect(self.minEnergyChanged)
        self.maxEnergyLineEdit.textChanged.connect(self.maxEnergyChanged)
        self.NStepsSpinBox.valueChanged.connect(self.NStepsChanged)
        self.calculatePushButton.clicked.connect(self.calculate)
        self.savePushButton.clicked.connect(self.saveFile)

    def elementChanged(self, txt):
        self.element=txt.split(': ')[1]
        self.edgeComboBox.currentTextChanged.disconnect()
        self.edgeComboBox.clear()
        edges = self.xrdb.xray_edges(self.element)
        self.edgeComboBox.addItems([key + ': %.4f' % (edges[key].energy / 1000) for key in edges.keys()])
        self.edgeComboBox.currentTextChanged.connect(self.edgeChanged)
        self.edgeChanged(self.edgeComboBox.currentText())

    def edgeChanged(self,txt):
        self.maxEnergy=float(txt.split(': ')[1])
        self.maxEnergyLineEdit.setText('%.4f'%self.maxEnergy)
        self.minEnergyLineEdit.setText('%.4f'%(np.max(self.maxEnergy-1,0)))

    def energyOffsetChanged(self, txt):
        self.energyOffset=float(txt)

    def NStepsChanged(self, N):
        self.NEnergy=N

    def minEnergyChanged(self,txt):
        self.minEnergy=float(txt)

    def maxEnergyChanged(self,txt):
        self.maxEnergy=float(txt)

    def calculate(self):
        edge_energy=self.maxEnergy*1000
        min_energy=self.minEnergy*1000
        element=self.element
        steps=self.NEnergy
        eoff=self.energyOffset

        self.resultTextEdit.clear()
        evals = np.linspace(edge_energy, min_energy, steps)
        efine = np.linspace(edge_energy, min_energy, 1001)
        f1 = self.xrdb.f1_chantler(element=element, energy=efine, smoothing=0)
        f1vals = np.linspace(f1[0], f1[-1], steps)
        e1vals = np.interp(f1vals, f1, efine)
        self.evaltxt = ''
        etemp = np.linspace(min_energy, edge_energy + (edge_energy - min_energy), 2001)
        f1temp = self.xrdb.f1_chantler(element=element, energy=etemp, smoothing=0)
        self.resultTextEdit.append("%10s\t%10s\t%10s\t%10s\t%10s" % ("Step", "f_value", "Mono_E", "Und_E", "f_1"))
        for i in range(steps):
            # print("%.5f\t%.3f"%(f1vals[i],e1vals[i]/1e3))
            self.evaltxt = self.evaltxt + '%.4f,' % (e1vals[i] / 1e3 + eoff)
            self.resultTextEdit.append("%10d\t%10.7f\t%10.4f\t%10.4f\t%10.7f" % (
            i, f1vals[i], e1vals[i] / 1e3 + eoff, e1vals[i] / 1e3 + 0.17 + eoff,
            self.xrdb.f1_chantler(
                element=element, energy=e1vals[i], smoothing=0)))
        self.plotWidget.add_data(x=etemp/1e3,y=f1temp,fit=True,name='continuous')
        self.plotWidget.add_data(x=e1vals/1e3,y=f1vals,name='discrete')
        self.plotWidget.Plot(['continuous','discrete'])
        txt = 'Energy [' + self.evaltxt[:-1] + '] absolute coupled'
        self.resultTextEdit.append('\n')
        self.resultTextEdit.append(txt)


    def saveFile(self):
        try:
            txt = 'Energy [' + self.evaltxt[:-1] + '] absolute coupled'
        except:
            QMessageBox.warning(self,'Save Error','Please calculate before saving!',QMessageBox.Ok)
            return
        fname=QFileDialog.getSaveFileName(parent=self,caption='Save file as', filter="Text files (*.txt )")[0]
        fh = open(fname, 'w')
        fh.write(txt)
        fh.close()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = XAnoS_EnergySteps()
    w.setWindowTitle('Energy Steps')
    #w.setFixedSize(1024,480)
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())





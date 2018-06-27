'''
###############################################################################
#Module for Intensity optimization at a particular energy                     #
###############################################################################
Typically white beam enters a particular beamline optics where most of the 
times the beam gets monochromatized and then focused. In the undulator beamlines
the white beam is not exactly white as it peaks around the energy we chose by
selecting the selecting the gap between the magnets. There are 4 componets which
needs to be adjusted while changing energy in a beamline. 
1) Monochromator bragg angle: To accept a particular energy. This is a
one time change in the process of changing the energy
2) Undulator energy: We tweak the undulator little bit i.e typically 100-150 eV
above the monochromator energy.
3) 2nd Crystal of the monochromator: Tweek it using a piezo to optimize monB counts
4) 2nd Mirror after the monochromator: Tweak it using a piezo to optimize monD or photodiode counts
'''

from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import pyqtSignal
import sys
import epics



class Energy_Widget(QWidget):
    """
    """
    energyChanging = pyqtSignal(float)
    energyChanged = pyqtSignal(int)


    def __init__(self, parent=None):
        """
        """
        QWidget.__init__(self, parent)
        loadUi('UI_Forms/Energy_Widget.ui', self)
        self.tabWidget.setTabText(0,'Xtal Plot')
        self.tabWidget.setTabText(1,'Mirror Plot')
        self.loadPVs()
        self.init_signals()
        self.undulatorStartPV = epics.PV("ID15:Start.VAL")
        self.undulatorStopPV = epics.PV("ID15:Start.VAL")

    def init_signals(self):
        self.undulatorStartPushButton.clicked.connect(self.startUndulator)
        self.undulatorStopPushButton.clicked.connect(self.stopUndulator)


    def loadPVs(self):
        #        pass
        self.energyRDBKLabel.setPV("15IDA:BraggERdbkAO", prec=4)
        self.lambdaRDBKLabel.setPV("15IDA:BraggLambdaRdbkAO", prec=5)
        self.braggRDBKLabel.setPV("15IDA:BraggThetaRdbkAO", prec=5)
        self.energyLineEdit.setPV("15IDA:BraggEAO.VAL", prec=4)
        self.lambdaLineEdit.setPV("15IDA:BraggLambdaAO.VAL", prec=5)
        self.braggLineEdit.setPV("15IDA:BraggThetaAO.VAL", prec=5)
        self.monoModeComboBox.setPV("15IDA:KohzuModeBO.VAL")
        self.monoStatusLabel.setPV("15IDA:KohzuMoving")
        self.undulatorHarmonicLineEdit.setPV("ID15:HarmonicValue",type=int)
        self.undulatorGapLineEdit.setPV("ID15:GapSet.VAL",prec=3)
        self.undulatorGapLabel.setPV("ID15:Gap.VAL",prec=3)
        self.undulatorEnergyLineEdit.setPV("ID15:EnergySet.VAL",prec=4)
        self.undulatorEnergyLabel.setPV("ID15:Energy.VAL",prec=4)
        self.undulatorStatusLabel.setPV("ID15:Busy.VAL")
        self.mirrorDACLineEdit.setPV("15IDA:DAC1_2.VAL",prec=4)
        self.xtalDACLineEdit.setPV("15IDA:DAC1_4.VAL",prec=4)

    def startUndulator(self):
        self.undulatorStartPV.put(1)

    def stopUndulator(self):
        self.undulatorStopPV.put(1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = Energy_Widget()
    w.setWindowTitle('Energy Widget')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())

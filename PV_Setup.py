from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from pyqtgraph.dockarea import DockArea, Dock
import pyqtgraph as pg
from PVInfo_Widget import PVInfo_Widget
import sys


class PV_Setup(QWidget):
    """
    This Widget sets up and shows all the PV necessary for SAXS/WAXS/GI-SAXS/GI-WAXS/ASAXS data collection
    """
    def __init__(self,parent=None):
        QWidget.__init__(self, parent)
        self.motors={}
        self.scalars={}
        self.detectors={}
        self.devices={}

        self.vbLayout=QVBoxLayout(self)
        self.setupDockArea=DockArea(self)
        self.vbLayout.addWidget(self.setupDockArea)
        
        #Creating the docks
        self.motorDock=Dock("Motors",size=(300,300))
        self.scalarDock=Dock("Scalars",size=(300,300))
        self.detectorDock=Dock("Area Detectors",size=(300,300))
        self.deviceDock=Dock("Devices",size=(300,300))
        
        #Adding the Docks to the DockArea
        self.setupDockArea.addDock(self.detectorDock)
        self.setupDockArea.addDock(self.scalarDock)
        self.setupDockArea.addDock(self.motorDock)
        self.setupDockArea.addDock(self.deviceDock)

        #Moving the Docks w.r.t each other to position them as tabs
        self.setupDockArea.moveDock(self.detectorDock,'above',self.deviceDock)
        self.setupDockArea.moveDock(self.scalarDock,'above',self.detectorDock)
        self.setupDockArea.moveDock(self.motorDock,'above',self.scalarDock)

        #Populating the docks with other widgets
        self.motorPV=PVInfo_Widget(parent=self,pvType='Motor')
        self.motorDock.addWidget(self.motorPV.layout)
        self.scalarPV=PVInfo_Widget(parent=self,pvType='Scalar')
        self.scalarDock.addWidget(self.scalarPV.layout)
        self.detectorPV=PVInfo_Widget(parent=self,pvType='Detector')
        self.detectorDock.addWidget(self.detectorPV.layout)
        self.devicePV=PVInfo_Widget(parent=self,pvType='Device')
        self.deviceDock.addWidget(self.devicePV.layout)



if __name__=='__main__':
    app=QApplication(sys.argv)
    setup=PV_Setup()
    setup.setWindowTitle('Instrument Setup')
    setup.show()
    sys.exit(app.exec_())




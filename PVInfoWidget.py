from PyQt5.QWidgets import QWidget
import pyqtgraph as pg

class PVInfo_Widget(QWidget):
    """
    This widget includes a TableWidget to store PV information and provides a convinient way to add and remove widgets
    """
    def __init__(self,parent=None,pvType='Motor'):
        QWidget.__init__(self,parent)
        self.pvType=pvType
        self.layout=pg.LayoutWidget()
        self.addPVButton=QPushButton('Add '+self.pvType)
        self.addPVButton.clicked.connect(self.addPV)
        self.removePVButton=QPushButton('Remove '+self.pvType)
        self.removePVButton.clicked.connect(self.removePVs)
        self.layout.addWidget(self.addMotorButton,row=0,col=0)
        self.layout.addWidget(self.removeMotorButton,row=0,col=1)
        
        self.PVTable=pg.TableWidget(editable=True,sortable=True)
        self.layout.addWidget(self.PVTable,row=1,col=0,colspan=2)



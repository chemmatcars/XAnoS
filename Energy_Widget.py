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
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
import sys

class Energy_Widget(QWidget):
    """
    """
    energyChanging=pyqtSignal(float)
    energyChanged=pyqtSingal(int)
    
    def __init__(self,parent=None):
        """
        """
        QWidget.__init__(self,parent)
        
        
        
        
if __name__=='__main__':
    app=QApplication(sys.argv)
    #poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w=Energy_Widget()
    w.setWindowTitle('Energy Widget')
    #w.setGeometry(50,50,800,800)
    
    w.show()
    sys.exit(app.exec_())



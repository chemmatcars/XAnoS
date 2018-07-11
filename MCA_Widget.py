from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QFileDialog, QAbstractScrollArea
from PyQt5.QtCore import pyqtSignal, QTimer, QProcess
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtTest import QTest
import sys
import epics
from epics.utils import BYTES2STR
import numpy as np
import copy
import time
import os
from functools import partial
from Data_Dialog import Data_Dialog

class MCA_Widget(QWidget):
    """

    """
    def __init__(self,parent = None):
        QWidget.__init__(self, parent)
        self.mcaDir='/tmp'
        self.init_UI()
        self.init_validation()
        self.init_signals()
        self.overrideEpicsCalib()
        self.mca_x = None
        self.mca_y = None
        self.mca_yerr = None
        self.data = {}
        self.dlg_data = {}
        self.plotColIndex = {}


    def init_UI(self):
        loadUi('./UI_Forms/MCA_Widget.ui',self)
        self.change_MCA()


    def init_signals(self):
        #Signals for MCA scans
        self.addMCAScanPushButton.clicked.connect(lambda x: self.add_mca_scans(fnames=None))
        self.mcaScanListWidget.itemDoubleClicked.connect(self.openDataDialog)
        self.mcaScanListWidget.itemSelectionChanged.connect(self.scanSelectionChanged)

        #Signals for mcaPlotWidget

        #Signals of MCA MEDM setup
        self.medm_P_LineEdit.returnPressed.connect(self.change_MCA)
        self.medm_D_LineEdit.returnPressed.connect(self.change_MCA)
        self.medm_M_LineEdit.returnPressed.connect(self.change_MCA)
        self.launchMEDMPushButton.clicked.connect(self.launch_MEDM)
        self.stopMEDMPushButton.clicked.connect(self.stop_MEDM)
        self.readMCAPushButton.clicked.connect(self.readMCA)
        self.saveMCAPushButton.clicked.connect(lambda x: self.saveMCA(fname=None))

        #Signals from MCA Calibration setup
        self.overrideMCACalibCheckBox.stateChanged.connect(self.overrideEpicsCalib)

        #Signals for Scan Statistics
        self.xminLineEdit.returnPressed.connect(self.xmin_xmax_Changed)
        self.xmaxLineEdit.returnPressed.connect(self.xmin_xmax_Changed)
        self.statsTableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

    def roiRegionChanged(self):
        self.xmin,self.xmax=self.mcaPlotWidget.roi.getRegion()
        self.xminLineEdit.setText('%.4f'%self.xmin)
        self.xmaxLineEdit.setText('%.4f'%self.xmax)


    def overrideEpicsCalib(self):
        if self.overrideMCACalibCheckBox.isChecked():
            self.offsetLineEdit.setEnabled(True)
            self.linearLineEdit.setEnabled(True)
            self.quadraticLineEdit.setEnabled(True)
        else:
            self.offsetLineEdit.setEnabled(False)
            self.linearLineEdit.setEnabled(False)
            self.quadraticLineEdit.setEnabled(False)

    def scanSelectionChanged(self):
        fnames=[item.text() for item in self.mcaScanListWidget.selectedItems()]
        self.mcaPlotWidget.Plot(fnames)
        fullfnames=[os.path.join(self.mcaDir,fname) for fname in fnames]
        self.offsetLineEdit.setText('%.4f'%self.data[fullfnames[0]]['Offset'])
        self.linearLineEdit.setText('%.4f'%self.data[fullfnames[0]]['Linear'])
        self.quadraticLineEdit.setText('%.4f'%self.data[fullfnames[0]]['Quadratic'])
        stats_data=[]
        keys=['Energy','real_time','live_time','sum','sum_err','corr_sum','corr_sum_err']#self.dlg_data[fullfnames[0]]['meta'].keys()
        for fname in fullfnames:
            stats_data.append([self.data[fname][key] for key in keys])
        stats_data=np.array(stats_data)
        self.updateStatisticsTable(stats_data,keys)
        print(stats_data)

    def updateStatisticsTable(self,data,keys):
        self.statsTableWidget.setData(data)
        self.statsTableWidget.setHorizontalHeaderLabels(keys)
        self.statsTableWidget.resizeColumnsToContents()


    #def addStatistics(self,):


    def init_validation(self):
        self.dbleValidator = QDoubleValidator()
        self.intValidator = QIntValidator()
        self.offsetLineEdit.setValidator(self.dbleValidator)
        self.linearLineEdit.setValidator(self.dbleValidator)
        self.quadraticLineEdit.setValidator(self.dbleValidator)
        self.xminLineEdit.setValidator(self.dbleValidator)
        self.xmaxLineEdit.setValidator(self.dbleValidator)

    def openDataDialog(self,item):
        fname=item.text()
        data_dlg=Data_Dialog(data=self.dlg_data[os.path.join(self.mcaDir,fname)],parent=self)
        if data_dlg.exec_():
            self.plotColIndex[fname]=data_dlg.plotColIndex
            self.dlg_data[fname]=copy.copy(data_dlg.data)
            self.data[fname]=copy.copy(data_dlg.externalData)
            self.mcaPlotWidget.add_data(self.data[fname]['x'],self.data[fname]['y'],yerr=self.data[fname]['yerr'],name=fname)
            #self.update_plot()

    def add_mca_scans(self,fnames=None):
        """
        Adds MCA scans to the mcaScanListWidget
        :param fnames: List of mca filenames. If None it will prompt for the files to be imported
        :return:
        """
        if fnames is None:
            self.mcaFnames=QFileDialog.getOpenFileNames(self,'Select MCA files',directory=self.mcaDir)[0]
        else:
            self.mcaFnames=fnames
        if self.mcaFnames !=[]:
            self.mcaDir=os.path.dirname(self.mcaFnames[0])
            self.mcaScanListWidget.addItems([os.path.basename(fname) for fname in self.mcaFnames])
            for fname in self.mcaFnames:
                data_dlg = Data_Dialog(fname=fname, parent=self)
                data_dlg.accept()
                self.dlg_data[fname] = data_dlg.data
                self.plotColIndex[fname] = data_dlg.plotColIndex
                self.data[fname] = data_dlg.externalData
                self.mcaPlotWidget.add_data(self.data[fname]['x'], self.data[fname]['y'], yerr=self.data[fname]['yerr'],
                                            name=os.path.basename(fname))

    def launch_MEDM(self):
        medm=QProcess()
        cmd='medm -x -macro "P=%s,D=%s, M=%s" ./adl/dxpSaturn.adl' % (self.medm_P, self.medm_D, self.medm_M)
        medm.startDetached(cmd)


    def stop_MEDM(self):
        pass

    def readMCA(self):
        self.mca_y=self.mcaPV.value
        self.mca_yerr=np.sqrt(self.mca_y)
        xmca = np.arange(len(self.mca_y))
        if self.overrideMCACalibCheckBox.isChecked():
            self.get_mca_manual_calib()
        else:
            self.get_mca_epics_calib()
        self.energy=epics.caget(BYTES2STR("15IDA:BraggERdbkAO"))
        self.mca_x=self.mca_offset+self.mca_linear*xmca+self.mca_quadratic*xmca**2
        self.mcaPlotWidget.add_data(self.mca_x,self.mca_y,yerr=self.mca_yerr,name='mca1')
        self.xmin=float(self.xminLineEdit.text())
        self.xmax=float(self.xmaxLineEdit.text())
        self.performStats()

    def performStats(self):
        if self.xmin is None:
            imin=0
        else:
            imin = np.where(self.mca_x > self.xmin)[0][0]
        if self.xmax is None:
            imax=len(self.mca_x)-1
        else:
            imax = np.where(self.mca_x < self.xmax)[0][-1]
        if imax<=imin:
            imax=imin+1
        self.data['sum'] = np.sum(self.mca_y[imin:imax+1])
        self.data['sum_err'] = np.sqrt(self.data['sum'])
        self.data['corr_sum'] = self.data['sum']*self.mca_realtime/self.mca_livetime
        self.data['corr_sum_err'] = self.data['sum_err']*self.mca_realtime/self.mca_livetime
        print(self.data['sum'],self.data['sum_err'])

    def xmin_xmax_Changed(self):
        self.xmin = float(self.xminLineEdit.text())
        self.xmax = float(self.xmaxLineEdit.text())
        try:
            self.mcaPlotWidget.roi.setRegion((self.xmin,self.xmax))
        except:
            self.mcaPlotWidget.addROI(values=(self.xmin,self.xmax),orientation='vertical',movable=True)
            self.mcaPlotWidget.roi.sigRegionChanged.connect(self.roiRegionChanged)
        try:
            self.performStats()
        except:
            pass


    def saveMCA(self,fname=None):
        if self.mca_y is None:
            self.readMCA()
        if fname is None:
            fname=QFileDialog.getSaveFileName(self,caption="Provide filename",directory=self.mcaDir)[0]
        data=np.vstack((self.mca_x,self.mca_y,self.mca_yerr)).T
        header='MCA file saved on %s\n'%time.asctime()
        header+='Energy=%.4f\n'%self.energy
        header+='Offset=%.4e\n'%self.mca_offset
        header+='Linear=%.4e\n'%self.mca_linear
        header+='Quadratic=%.4e\n'%self.mca_quadratic
        header+='real_time=%.4f\n'%self.mca_realtime
        header+='live_time=%.4f\n'%self.mca_livetime
        header+='sum=%.4f\n'%self.data['sum']
        header+='sum_err=%.4f\n'%self.data['sum_err']
        header+='corr_sum=%.4f\n'%self.data['corr_sum']
        header+='corr_sum_err=%.4f\n'%self.data['corr_sum_err']
        header+='col_names=["Channel","Counts","Err_Counts"]'
        np.savetxt(fname,data,header=header)
        self.add_mca_scans(fnames=[fname])

    def get_mca_manual_calib(self):
        """
        Get the manual calibration number from the MCA_Widget
        """
        self.mca_offset = float(self.offsetLineEdit.text())
        self.mca_linear = float(self.linearLineEdit.text())
        self.mca_quadratic = float(self.quadraticLineEdit.text())
        self.mca_realtime = epics.caget(BYTES2STR("dxpSaturn:mca1.ERTM"))
        self.mca_livetime = epics.caget(BYTES2STR("dxpSaturn:mca1.ELTM"))


    def get_mca_epics_calib(self):
        """
        Get the epics calibration numbers and reset the manual calibration numbers accordingly
        """
        self.mca_offset = epics.caget(BYTES2STR("dxpSaturn:mca1.CALO"))
        self.mca_linear = epics.caget(BYTES2STR("dxpSaturn:mca1.CALS"))
        self.mca_quadratic = epics.caget(BYTES2STR("dxpSaturn:mca1.CALQ"))
        self.mca_realtime = epics.caget(BYTES2STR("dxpSaturn:mca1.ERTM"))
        self.mca_livetime = epics.caget(BYTES2STR("dxpSaturn:mca1.ELTM"))

        if not self.overrideMCACalibCheckBox.isChecked():
            self.offsetLineEdit.setText('%.5f'%self.mca_offset)
            self.linearLineEdit.setText('%.5f'%self.mca_linear)
            self.quadraticLineEdit.setText('%.5f'%self.mca_quadratic)


    def change_MCA(self):
        """
        Resets the P, D and M values of MCA
        :return:
        """
        self.medm_P = self.medm_P_LineEdit.text()
        self.medm_D = self.medm_D_LineEdit.text()
        self.medm_M = self.medm_M_LineEdit.text()
        self.mcaPV = epics.PV(BYTES2STR(self.medm_P + self.medm_M))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = MCA_Widget()
    w.setWindowTitle('MCA Widget')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())

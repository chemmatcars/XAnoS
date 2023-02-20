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
import pyqtgraph as pg

class MCA_Widget(QWidget):
    """

    """
    mcaUpdating=pyqtSignal(int)

    def __init__(self,parent = None):
        QWidget.__init__(self, parent)
        self.mcaDir='/tmp'
        self.connection=False
        self.init_UI()
        self.init_validation()
        self.init_signals()
        self.overrideEpicsCalib()
        self.mca_x = None
        self.mca_y = None
        self.mca_yerr = None
        self.data = {}
        self.expressions={}
        self.plotColors={}
        self.dlg_data = {}
        self.plotColIndex = {}
        self.mcaFnames=[]
        self.mca_MEDM_running = False
        # self.stopMEDMPushButton.setEnabled(False)



    def init_UI(self):
        loadUi('./UI_Forms/MCA_Widget.ui',self)
        self.change_MCA()

    def closeEvent(self,event):
        if self.mca_MEDM_running:
            self.medm.close()

    def init_pv(self):
        ret=self.realTimeLineEdit.setPV(self.medm_P + 'mca1.PRTM')
        if not ret:
            self.currentStatusLabel.setText('Not Connected')
            self.connection=False
            return
        self.liveTimeLineEdit.setPV(self.medm_P + 'mca1.PLTM')
        self.modeComboBox.setPV(self.medm_P+self.medm_D+'PresetMode')
        self.currentStatusLabel.setPV(self.medm_P+'mca1.ACQG',type='str')
        self.readRealTimeLabel.setPV(self.medm_P+'mca1.ERTM')
        self.readLiveTimeLabel.setPV(self.medm_P+'mca1.ELTM')
        self.connection=True
        # self.stopPushButton.setPV(self.medm_P+'mca1Stop')
        # self.offsetLineEdit.setPV(self.medm_P+'mca1.CALO')
        # self.linearLineEdit.setPV(self.medm_P+'mca1.CALS')
        # self.quadraticLineEdit.setPV(self.medm_P+'mca1.CALQ')



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
        self.countPushButton.clicked.connect(self.startstopCountMCA)
        # self.liveTimeLineEdit.pvChanged.connect(lambda x: self.liveTimeLineEdit.setText())

        #Signals from MCA Calibration setup
        self.overrideMCACalibCheckBox.stateChanged.connect(self.overrideEpicsCalib)

        #Signals for Scan Statistics
        self.xminLineEdit.returnPressed.connect(self.xmin_xmax_Changed)
        self.xmaxLineEdit.returnPressed.connect(self.xmin_xmax_Changed)
        self.statsTableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.calcStatsPushButton.clicked.connect(self.calcStats)

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
        if len(fnames)!=0:
            self.mcaPlotWidget.Plot(fnames)
            self.offsetLineEdit.setText('%.4f'%self.data[fnames[0]]['Counts']['Offset'])
            self.linearLineEdit.setText('%.4f'%self.data[fnames[0]]['Counts']['Linear'])
            self.quadraticLineEdit.setText('%.4f'%self.data[fnames[0]]['Counts']['Quadratic'])
            stats_data=[]
            keys=['Energy','real_time','live_time','sum','sum_err','corr_sum','corr_sum_err']#self.dlg_data[fullfnames[0]]['meta'].keys()
            for fname in fnames:
                stats_data.append([self.data[fname]['Counts'][key] for key in keys])
            stats_data=np.array(stats_data)
            self.updateStatisticsTable(stats_data,keys)

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
        data_dlg=Data_Dialog(data=self.dlg_data[os.path.join(self.mcaDir,fname)],parent=self,plotIndex=self.plotColIndex[fname],colors=self.plotColors[fname])
        if data_dlg.exec_():
            self.mcaPlotWidget.remove_data([fname])
            self.plotColIndex[fname]=data_dlg.plotColIndex
            self.dlg_data[fname]=copy.copy(data_dlg.data)
            self.data[fname]=copy.copy(data_dlg.externalData)
            self.expressions[fname] = data_dlg.expressions
            self.plotColors[fname] = data_dlg.plotColors
            for key in self.data[fname].keys():
                self.mcaPlotWidget.add_data(self.data[fname][key]['x'],self.data[fname][key]['y'],yerr=self.data[
                    fname][key]['yerr'],name=fname,color=self.plotColors[fname][key])
            self.mcaPlotWidget.Plot([fname])



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
            # self.mcaScanListWidget.addItems([os.path.basename(fname) for fname in self.mcaFnames])
            self.mcaScanListWidget.addItems(self.mcaFnames)
            for fname in self.mcaFnames:
                data_dlg = Data_Dialog(fname=fname, parent=self,colors=None)
                data_dlg.accept()
                self.dlg_data[fname] = data_dlg.data
                self.plotColIndex[fname] = data_dlg.plotColIndex
                self.data[fname] = data_dlg.externalData
                self.expressions[fname] = data_dlg.expressions
                self.plotColors[fname] = data_dlg.plotColors
                for key in self.data[fname].keys():
                    self.mcaPlotWidget.add_data(self.data[fname][key]['x'], self.data[fname][key]['y'], \
                                             yerr=self.data[fname][key]['yerr'],
                                             name='%s' % (fname),
                                             color=self.plotColors[fname][key])

    def launch_MEDM(self):
        self.medm=QProcess()
        cmd='medm -x -macro "P=%s,D=%s, M=%s" ./adl/dxpSaturn.adl' % (self.medm_P, self.medm_D, self.medm_M)
        self.medm.start(cmd)
        self.mca_MEDM_running=True
        self.launchMEDMPushButton.setEnabled(False)
        self.stopMEDMPushButton.setEnabled(True)

    def stop_MEDM(self):
        if self.mca_MEDM_running:
            self.medm.close()
        self.mca_MEDM_running=False
        self.stopMEDMPushButton.setEnabled(False)
        self.launchMEDMPushButton.setEnabled(True)

    # def stop_MEDM(self):
    #     self.medm.terminate()

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
        self.performStats(fname=None)
        keys = ['Energy', 'real_time', 'live_time', 'sum', 'sum_err', 'corr_sum',
                'corr_sum_err']  # self.dlg_data[fullfnames[0]]['meta'].keys()
        stats_data=[[self.energy,self.mca_realtime,self.mca_livetime,self.sum,self.sum_err,self.corr_sum,self.corr_sum_err]]
        self.updateStatisticsTable(stats_data,keys)

    def calcStats(self):
        if len(self.mcaFnames)!=0:
            stats_data=[]
            for fname in self.mcaFnames:
                self.mca_x=self.data[fname]['Counts']['x']
                self.mca_y=self.data[fname]['Counts']['y']
                self.mca_realtime=self.data[fname]['Counts']['real_time']
                self.mca_livetime=self.data[fname]['Counts']['live_time']
                self.performStats(fname=fname)
                keys = ['Energy', 'real_time', 'live_time', 'sum', 'sum_err', 'corr_sum',
                        'corr_sum_err']  # self.dlg_data[fullfnames[0]]['meta'].keys()
                stats_data.append([self.data[fname]['Counts'][key] for key in keys])
        else:
            self.performStats(fname=None)
            keys = ['Energy', 'real_time', 'live_time', 'sum', 'sum_err', 'corr_sum',
                    'corr_sum_err']  # self.dlg_data[fullfnames[0]]['meta'].keys()
            stats_data = [[self.energy, self.mca_realtime, self.mca_livetime, self.sum, self.sum_err, self.corr_sum,
                           self.corr_sum_err]]
        self.updateStatisticsTable(stats_data,keys)

    def performStats(self,fname=None):
        #self.xmin_xmax_Changed()
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
        if fname is not None:
            self.data[fname]['Counts']['sum'] = np.sum(self.mca_y[imin:imax+1])
            self.data[fname]['Counts']['sum_err'] = np.sqrt(self.data[fname]['Counts']['sum'])
            self.data[fname]['Counts']['corr_sum'] = self.data[fname]['Counts']['sum']*self.mca_realtime/self.mca_livetime
            self.data[fname]['Counts']['corr_sum_err'] = self.data[fname]['Counts']['sum_err']*self.mca_realtime/self.mca_livetime
        else:
            self.sum = np.sum(self.mca_y[imin:imax+1])
            self.sum_err = np.sqrt(self.sum)
            self.corr_sum = self.sum*self.mca_realtime/self.mca_livetime
            self.corr_sum_err = self.sum_err*self.mca_realtime/self.mca_livetime

    def xmin_xmax_Changed(self):
        self.xmin = float(self.xminLineEdit.text())
        self.xmax = float(self.xmaxLineEdit.text())
        try:
            self.mcaPlotWidget.roi.setRegion((self.xmin,self.xmax))
        except:
            self.mcaPlotWidget.addROI(values=(self.xmin,self.xmax),orientation='vertical',movable=True)
            self.mcaPlotWidget.roi.sigRegionChanged.connect(self.roiRegionChanged)
        try:
            self.calcStats()
        except:
            pass


    def saveMCA(self,fname=None, add_to_table=True):
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
        header+='sum=%.4f\n'%self.sum#self.data['sum']
        header+='sum_err=%.4f\n'%self.sum_err#self.data['sum_err']
        header+='corr_sum=%.4f\n'%self.corr_sum#self.data['corr_sum']
        header+='corr_sum_err=%.4f\n'%self.corr_sum_err#self.data['corr_sum_err']
        header+='col_names=["Channel","Counts","Err_Counts"]'
        np.savetxt(fname,data,header=header)
        if add_to_table:
            self.add_mca_scans(fnames=[fname])

    def get_mca_manual_calib(self):
        """
        Get the manual calibration number from the MCA_Widget
        """
        self.mca_offset = float(self.offsetLineEdit.text())
        self.mca_linear = float(self.linearLineEdit.text())
        self.mca_quadratic = float(self.quadraticLineEdit.text())
        self.mca_realtime = epics.caget(BYTES2STR(self.medm_P+"mca1.ERTM"))
        self.mca_livetime = epics.caget(BYTES2STR(self.medm_P+"mca1.ELTM"))


    def get_mca_epics_calib(self):
        """
        Get the epics calibration numbers and reset the manual calibration numbers accordingly
        """
        self.mca_offset = epics.caget(BYTES2STR(self.medm_P+"mca1.CALO"))
        self.mca_linear = epics.caget(BYTES2STR(self.medm_P+"mca1.CALS"))
        self.mca_quadratic = epics.caget(BYTES2STR(self.medm_P+"mca1.CALQ"))
        self.mca_realtime = epics.caget(BYTES2STR(self.medm_P+"mca1.ERTM"))
        self.mca_livetime = epics.caget(BYTES2STR(self.medm_P+"mca1.ELTM"))

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
        try:
            self.mcaStatusPV.clear_callbacks()
        except:
            self.mcaStatusPV=epics.PV(BYTES2STR(self.medm_P + self.medm_M+'.ACQG'))
        self.monitorIndex=self.mcaStatusPV.add_callback(self.mcaChanging)
        self.mcaUpdating.connect(self.mcaAutoUpdate)
        self.show()
        self.init_pv()

    def mcaChanging(self,**kwargs):
        value=kwargs['value']
        if value==0:
            self.mcaUpdating.emit(value)


    def mcaAutoUpdate(self,value):
        self.readMCA()
        self.countPushButton.setText('Count')

    def startstopCountMCA(self):
        if self.countPushButton.text()=='Count':
            epics.caput(BYTES2STR(self.medm_P+'mca1EraseStart'),1)
            self.countPushButton.setText('Stop')
        else:
            epics.caput(BYTES2STR(self.medm_P + 'mca1Stop'), 1)
            self.countPushButton.setText('Count')









if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = MCA_Widget()
    w.setWindowTitle('MCA Widget')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())

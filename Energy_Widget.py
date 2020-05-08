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
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtTest import QTest
import sys
import epics
from epics.utils import BYTES2STR
import numpy as np
import copy
import time
from threading import Thread



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
        self.init_validation()
        self.xtalMinChanged()
        self.xtalMaxChanged()
        self.mirrorMinChanged()
        self.mirrorMaxChanged()
        self.xtalStepsChanged()
        self.mirrorStepsChanged()
        self.stoppedTracking=False
        self.init_signals()
        self.undulatorStartPV = epics.PV(BYTES2STR("ID15:Start.VAL"))
        self.undulatorStopPV = epics.PV(BYTES2STR("ID15:Start.VAL"))
        self.scaler_15IDC_PV = epics.PV(BYTES2STR("15IDC:scaler1.CNT"))
        self.scaler_15IDD_PV = epics.PV(BYTES2STR("15IDD:vsc:c0.CNT"))
        self.countTime_15IDC_PV=epics.PV(BYTES2STR("15IDC:scaler1.TP"))
        self.countTime_15IDD_PV = epics.PV(BYTES2STR("15IDD:vsc:c0.TP"))
        self.xiaShutter_PV=epics.PV(BYTES2STR("15IDD:2openXIAShutter"))
        self.countTime_15IDC_PV.put(1)
        self.countTime_15IDD_PV.put(1)
        self.getUndulatorOffset()
        self.undulatorChanging=False
        if self.feedbackComboBox.pv.value==1:
            # self.feedback_enabled=True
            # self.feedback_disable=False
            QMessageBox.warning(self,'Feedback Warning','Please switch off the feedback before start energy tracking',QMessageBox.Ok)
        # else:
        #     self.feedback_enabled=False
        #     self.feedback_disabled=True


    def getUndulatorOffset(self):
        self.undulatorOffset = self.undulatorEnergyLineEdit.pv.value - self.energyLineEdit.pv.value
        self.undulatorOffsetLineEdit.setText('%.4f' % self.undulatorOffset)

    def init_validation(self):
        self.dbleValidator=QDoubleValidator()
        self.intValidator=QIntValidator()
        self.xtalMinLineEdit.setValidator(self.dbleValidator)
        self.xtalMaxLineEdit.setValidator(self.dbleValidator)
        self.mirrorMinLineEdit.setValidator(self.dbleValidator)
        self.mirrorMaxLineEdit.setValidator(self.dbleValidator)
        self.xtalStepsLineEdit.setValidator(self.intValidator)
        self.mirrorStepsLineEdit.setValidator(self.intValidator)
        self.undulatorOffsetLineEdit.setValidator(self.dbleValidator)



    def init_signals(self):
        self.undulatorStartPushButton.clicked.connect(self.startUndulator)
        self.undulatorStopPushButton.clicked.connect(self.stopUndulator)
        self.undulatorOffsetLineEdit.returnPressed.connect(self.offsetChanged)
        self.getUndulatorOffsetPushButton.clicked.connect(self.getUndulatorOffset)
        self.startTrackingPushButton.clicked.connect(self.track_undulator)
        self.stopTrackingPushButton.clicked.connect(self.untrack_undulator)
        self.xtalScanPushButton.clicked.connect(self.scan_xtal)
        self.mirrorScanPushButton.clicked.connect(self.scan_mirror)
        self.xtalMinLineEdit.returnPressed.connect(self.xtalMinChanged)
        self.xtalMaxLineEdit.returnPressed.connect(self.xtalMaxChanged)
        self.mirrorMinLineEdit.returnPressed.connect(self.mirrorMinChanged)
        self.mirrorMaxLineEdit.returnPressed.connect(self.mirrorMaxChanged)
        self.xtalStepsLineEdit.returnPressed.connect(self.xtalStepsChanged)
        self.mirrorStepsLineEdit.returnPressed.connect(self.mirrorStepsChanged)




    def loadPVs(self):
        #        pass
        self.feedbackComboBox.setPV("15IDA:pid_mono_1.FBON")
        self.shutterComboBox.setPV("15IDD:2openXIAShutter")
        self.monBCountsLabel.setPV("15IDC:scaler1.S2",type=int)
        self.monPCountsLabel.setPV("15IDC:scaler1.S3",type=int)
        self.monDCountsLabel.setPV("15IDD:vsc:c0.S8",type=int)
        self.pdCountsLabel.setPV("15IDD:vsc:c0.S4",type=int)
        self.energyRDBKLabel.setPV("15IDA:BraggERdbkAO", prec=4)
        self.lambdaRDBKLabel.setPV("15IDA:BraggLambdaRdbkAO", prec=5)
        self.braggRDBKLabel.setPV("15IDA:BraggThetaRdbkAO", prec=5)
        self.energyLineEdit.setPV("15IDA:BraggEAO.VAL", prec=4)
        self.lambdaLineEdit.setPV("15IDA:BraggLambdaAO.VAL", prec=5)
        self.braggLineEdit.setPV("15IDA:BraggThetaAO.VAL", prec=5)
        self.monoModeComboBox.setPV("15IDA:KohzuModeBO.VAL")
        self.monoStatusLabel.setPV("15IDA:KohzuMoving",type=str)
        self.undulatorHarmonicLineEdit.setPV("ID15:HarmonicValue",type=int)
        self.undulatorGapLineEdit.setPV("ID15:GapSet.VAL",prec=3)
        self.undulatorGapLabel.setPV("ID15:Gap.VAL",prec=3,type=float)
        self.undulatorEnergyLineEdit.setPV("ID15:EnergySet.VAL",prec=4)
        self.undulatorEnergyLabel.setPV("ID15:Energy.VAL",prec=4,type=float)
        self.undulatorStatusLabel.setPV("ID15:Busy.VAL",type=str)
        self.mirrorDACLineEdit.setPV("15IDA:DAC1_2.VAL",prec=4)
        self.xtalDACLineEdit.setPV("15IDA:DAC1_4.VAL",prec=4)

    def startUndulator(self):
        self.undulatorStartPV.put(1)

    def stopUndulator(self):
        self.undulatorStopPV.put(1)

    def offsetChanged(self):
        if self.dbleValidator.validate(self.undulatorOffsetLineEdit.text(),0)[0]==self.dbleValidator.Acceptable:
            self.undulatorOffset=float(self.undulatorOffsetLineEdit.text())
        else:
            QMessageBox.warning(self,'Value Error',"Please enter floating point numbers only",QMessageBox.Ok)

    def xtalMinChanged(self):
        if self.dbleValidator.validate(self.xtalMinLineEdit.text(),0)[0]==self.dbleValidator.Acceptable:
            self.xtalMin=float(self.xtalMinLineEdit.text())
        else:
            QMessageBox.warning(self,'Value Error',"Please enter floating point numbers only",QMessageBox.Ok)

    def xtalMaxChanged(self):
        if self.dbleValidator.validate(self.xtalMaxLineEdit.text(),0)[0]==self.dbleValidator.Acceptable:
            self.xtalMax=float(self.xtalMaxLineEdit.text())
        else:
            QMessageBox.warning(self,'Value Error',"Please enter floating point numbers only",QMessageBox.Ok)

    def mirrorMinChanged(self):
        if self.dbleValidator.validate(self.mirrorMinLineEdit.text(), 0)[0] == self.dbleValidator.Acceptable:
            self.mirrorMin = float(self.mirrorMinLineEdit.text())
        else:
            QMessageBox.warning(self, 'Value Error', "Please enter floating point numbers only", QMessageBox.Ok)

    def mirrorMaxChanged(self):
        if self.dbleValidator.validate(self.mirrorMaxLineEdit.text(), 0)[0] == self.dbleValidator.Acceptable:
            self.mirrorMax = float(self.mirrorMaxLineEdit.text())
        else:
            QMessageBox.warning(self, 'Value Error', "Please enter floating point numbers only", QMessageBox.Ok)

    def xtalStepsChanged(self):
        if self.intValidator.validate(self.xtalStepsLineEdit.text(),0)[0]==self.intValidator.Acceptable:
            self.xtalSteps=int(self.xtalStepsLineEdit.text())
        else:
            QMessageBox.warning(self,'Value Error',"Please enter integer value only")

    def mirrorStepsChanged(self):
        if self.intValidator.validate(self.mirrorStepsLineEdit.text(),0)[0]==self.intValidator.Acceptable:
            self.mirrorSteps=int(self.xtalStepsLineEdit.text())
        else:
            QMessageBox.warning(self,'Value Error',"Please enter integer value only")



    def track_undulator(self):
        self.stoppedTracking=False
        self.enable_widgets(enable=False)
        try:
            self.braggLineEdit.pvChanged.disconnect(self.changeUndulatorEnergy)
        except:
            pass
        self.braggLineEdit.pvChanged.connect(self.changeUndulatorEnergy)

    def untrack_undulator(self):
        self.enable_widgets(enable=True)
        self.stoppedTracking=True
        try:
            self.braggLineEdit.pvChanged.disconnect(self.changeUndulatorEnergy)
        except:
            pass

    def changeUndulatorEnergy(self):
        # self.feedback_OFF()
        # print("Feedback Disabled")
        print('Changing Undulator')
        self.undulatorChanging=True
        self.undulatorEnergyLineEdit.pv.put(self.energyLineEdit.pv.value+self.undulatorOffset)
        self.startUndulator()
        while epics.caget(BYTES2STR("15IDA:KohzuMoving"))==1:
            QTest.qWait(10)
        print('Undulator Changed')
        self.wait_for_stablization(detector='MonB')
        #print("Undulator change stablized")
        if self.trackXtalCheckBox.isChecked():
            print("Scanning 2nd Xtal...")
            self.scan_xtal()
        if self.trackMirrorCheckBox.isChecked():
            print("Scanning 2nd Mirror...")
            self.scan_mirror()
        self.undulatorChanging=False
        # self.feeback_ON()
        # print("Feedback Enabled")


    def scan_xtal(self):
        # if self.feedback_enabled:
        #     print("Feedback Disabled")
        #     self.feedback_OFF()
        self.stoppedTracking=False
        self.scan(dac='xtal')
        # print("Feedback Enabled")
        # self.feeback_ON()

    def scan_mirror(self):
        self.stoppedTracking = False
        self.scan(dac='mirror')

    def scan(self,dac='xtal',save=True):
        self.countTime_15IDC_PV.put(1)
        self.countTime_15IDD_PV.put(1)
        if dac=='xtal':
            xold=self.xtalDACLineEdit.pv.value
            xmin=xold+self.xtalMin
            xmax=xold+self.xtalMax
            steps=self.xtalSteps
            yaxis=self.xtalDetectorComboBox.currentText()
            self.xtalPlotTab.setXLabel(dac)
            self.xtalPlotTab.setYLabel(yaxis)
        else:
            xold = self.mirrorDACLineEdit.pv.value
            xmin = xold + self.mirrorMin
            xmax = xold + self.mirrorMax
            steps = self.mirrorSteps
            yaxis = self.mirrorDetectorComboBox.currentText()
            self.mirrorPlotTab.setXLabel(dac)
            self.mirrorPlotTab.setYLabel(yaxis)
        data={}
        data[dac]=np.linspace(xmin,xmax,steps)
        data['MonB'] = np.array([])
        data['MonP'] = np.array([])
        data['MonD'] = np.array([])
        # data['Readback'] = np.array([])
        data['PD'] = np.array([])
        self.auto_count_off()
        if dac == 'xtal':
            self.xtalDACLineEdit.pv.put(data[dac][0], wait=True)
        else:
            self.mirrorDACLineEdit.pv.put(data[dac][0], wait=True)
        #print('val=%.4f I m waiting' % val)
        #t=time.time()
        QTest.qWait(1000)
        #print(time.time()-t)

        for i, val in enumerate(data[dac][1:]):
            if not self.stoppedTracking:
                self.trigger_scalers()
                data['MonB'] = np.append(data['MonB'],self.monBCountsLabel.pv.value)
                data['MonP'] = np.append(data['MonP'],self.monPCountsLabel.pv.value)
                data['MonD'] = np.append(data['MonD'],self.monDCountsLabel.pv.value)
                data['PD']=np.append(data['PD'],self.pdCountsLabel.pv.value)
                # data['Readback'] = np.append(data['Readback'], float(epics.caget(BYTES2STR("15IDA:pid_mono_1.CVAL"))))
                if dac=='xtal':
                    self.tabWidget.setCurrentIndex(0)
                    self.xtalPlotTab.add_data(data[dac][:i+1],data[yaxis],name=dac+'-'+yaxis)
                else:
                    self.tabWidget.setCurrentIndex(1)
                    self.mirrorPlotTab.add_data(data[dac][:i+1],data[yaxis],name=dac+'-'+yaxis)
                if dac == 'xtal':
                    self.xtalDACLineEdit.pv.put(val, wait=True)
                else:
                    self.mirrorDACLineEdit.pv.put(val, wait=True)
                QTest.qWait(100)
            else:
                break
        if not self.stoppedTracking:
            maxval=data[dac][data[yaxis].argmax()]
            # self.readbackvalue=data['Readback'][data[yaxis].argmax()]
            if dac=='xtal':
                # offset of -0.06 is added because we find the
                # peak position obtained from scan is -0.06 from the real peak position
                print('Moving to Maximum %.4f' % (maxval - 0.06))
                self.xtalDACLineEdit.pv.put(maxval-0.06)#Moving DAC to the maximum xtalintensity value
            else:
                print('Moving to Maximum %.4f' % maxval)
                self.mirrorDACLineEdit.pv.put(maxval)  # Moving DAC to the maximum mirror intensity value
        else:
            print('Moving to old value')
            if dac=='xtal':
                self.xtalDACLineEdit.pv.put(xold)#Moving DAC to the known old value
            else:
                self.mirrorDACLineEdit.pv.put(xold)  # Moving DAC to the known old value
        self.auto_count_on()


    def wait_for_stablization(self,detector='MonB'):
        self.auto_count_off()
        self.countTime_15IDC_PV.put(1)
        self.countTime_15IDD_PV.put(1)
        if detector=='MonB':
            self.trigger_scalers()
            for i in range(10):
                QTest.qWait(1000)
                counts=0
                monbCounts=self.monBCountsLabel.pv.value
                while np.abs(counts-monbCounts)>np.sqrt(monbCounts) and not self.stoppedTracking:
                    QTest.qWait(100)
                    print(np.abs(counts-monbCounts),np.sqrt(monbCounts))
                    counts=copy.copy(monbCounts)
                    self.trigger_scalers()
                    monbCounts=self.monBCountsLabel.pv.value
        elif detector=='MonP':
            self.trigger_scalers()
            counts = 0
            monpCounts = self.monPCountsLabel.pv.value
            while np.abs(counts-monpCounts) > np.sqrt(monpCounts) and not self.stoppedTracking:
                QTest.qWait(1000)
                counts = copy.copy(monpCounts)
                self.trigger_scalers()
                monpCounts = self.monPCountsLabel.pv.value
        elif detector=='MonD':
            self.trigger_scalers()
            counts = 0
            mondCounts = self.monDCountsLabel.pv.value
            while np.abs(counts-mondCounts) > np.sqrt(mondCounts) and not self.stoppedTracking:
                QTest.qWait(1000)
                counts = copy.copy(mondCounts)
                self.trigger_scalers()
                mondCounts = self.monDCountsLabel.pv.value
        elif detector=='PD':
            self.trigger_scalers()
            counts = 0
            pdCounts = self.pdCountsLabel.pv.value
            while np.abs(counts-pdCounts) > np.sqrt(pdCounts):
                QTest.qWait(1000)
                counts = copy.copy(pdCounts)
                self.trigger_scalers()
                pdCounts = self.pdCountsLabel.pv.value
        self.auto_count_on()


    # def feeback_ON(self):
    #     epics.caput(BYTES2STR("15IDA:pid_mono_1.INP"),"15IDA:pid_mono_1_incalc.D", wait=True)
    #     sfb=float(epics.caget(BYTES2STR("15IDA:pid_mono_1_incalc.INPC")))
    #     sf=96.0*sfb/self.readbackvalue
    #     print(self.readbackvalue,sfb)
    #     epics.caput(BYTES2STR("15IDA:pid_mono_1_incalc.INPC"), '%.3f'%sf, wait=True)
    #     epics.caput(BYTES2STR("15IDA:pid_mono_1.FBON"), 1, wait=True)
    #     self.feedback_enabled=True
    #     self.feedback_disabled=False
    #
    # def feedback_OFF(self):
    #     epics.caput(BYTES2STR("15IDA:pid_mono_1.FBON"), 0)
    #     self.feedback_disabled=True
    #     self.feedback_enabled=False

    def auto_count_on(self):
        epics.caput(BYTES2STR("15IDC:scaler1.CONT"), 1)  # setting autocount on for 15IDC scaler
        epics.caput(BYTES2STR("15IDD:vsc:c0.CONT"), 1)  # setting autocount on for 15IDD scaler

    def auto_count_off(self):
        epics.caput(BYTES2STR("15IDC:scaler1.CONT"), 0)  # setting autocount off for 15IDC scaler
        epics.caput(BYTES2STR("15IDD:vsc:c0.CONT"), 0)  # setting autocount off for 15IDD scaler

    def trigger_scalers(self):
        self.xiaShutter_PV.put(0)
        QTest.qWait(100)
        self.trigger_15IDC_scaler()
        self.trigger_15IDD_scaler()
        QTest.qWait(10)
        while self.scaler_15IDD_PV.value==1 or self.scaler_15IDC_PV.value==1:
            QTest.qWait(10)
        self.xiaShutter_PV.put(1)


    def trigger_15IDC_scaler(self):
        self.scaler_15IDC_PV.put(1,wait=False)   # Start counting for 1 sec with 15IDC counter

    def trigger_15IDD_scaler(self):
        self.scaler_15IDD_PV.put(1,wait=False)  # Start counting for 1 sec with 15IDD counter


    def enable_widgets(self,enable=True):
        self.feedbackComboBox.setEnabled(enable)
        self.energyLineEdit.setEnabled(enable)
        self.lambdaLineEdit.setEnabled(enable)
        self.braggLineEdit.setEnabled(enable)
        self.undulatorEnergyLineEdit.setEnabled(enable)
        self.undulatorGapLineEdit.setEnabled(enable)
        self.undulatorHarmonicLineEdit.setEnabled(enable)
        self.undulatorStartPushButton.setEnabled(enable)
        self.undulatorStopPushButton.setEnabled(enable)
        self.xtalDACLineEdit.setEnabled(enable)
        self.xtalMinLineEdit.setEnabled(enable)
        self.xtalMaxLineEdit.setEnabled(enable)
        self.xtalStepsLineEdit.setEnabled(enable)
        self.xtalScanPushButton.setEnabled(enable)
        self.mirrorDACLineEdit.setEnabled(enable)
        self.mirrorMinLineEdit.setEnabled(enable)
        self.mirrorMaxLineEdit.setEnabled(enable)
        self.mirrorStepsLineEdit.setEnabled(enable)
        self.mirrorScanPushButton.setEnabled(enable)
        self.startTrackingPushButton.setEnabled(enable)
        self.stopTrackingPushButton.setEnabled(not enable)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = Energy_Widget()
    w.setWindowTitle('Energy Widget')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())

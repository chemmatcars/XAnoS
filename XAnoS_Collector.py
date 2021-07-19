from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QCheckBox, QSpinBox, QComboBox, QListWidget, QDialog, QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPalette, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtTest
import os
import sys
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
from Detector_Widget import Detector_Widget
from epics import caput, caget, camonitor, camonitor_clear
from Setup import Setup
from multiprocessing import Process
import fabio as fb
import time
from numpy import *
from scanner import Scanner
import zmq
from Energy_Widget import Energy_Widget
import traceback
#from Data_Reducer import Data_Reducer


class XAnoS_Collector(QWidget):
    """
    This class is developed to collect SAXS/WAXS data using different Area detectors with different experimental conditions
    """
    undulatorChanged=pyqtSignal(int)
    undulatorGapChanged=pyqtSignal(int)
    undulatorGapChanging=pyqtSignal(float)
    undulatorChanging=pyqtSignal(float)
    energyChanged=pyqtSignal(int)
    energyChanging=pyqtSignal(float)
    jjcvChanging=pyqtSignal(float)
    jjchChanging=pyqtSignal(float)
    jjdvChanging=pyqtSignal(float)
    jjdhChanging=pyqtSignal(float)
    
    def __init__(self,parent=None):
        QWidget.__init__(self,parent)
        self.palette=QPalette()
        self.cwd=os.getcwd()
        self.setup=Setup(os.path.join(self.cwd,'SetupData'))
        self.detectors=self.setup.detectors
        self.motors=self.setup.motors
        self.scalers=self.setup.scalers
        self.BLParams=self.setup.BLParams
        
        self.pdIn=False
        self.beamIn=False
        self.mirrorIn=False
        self.align=True
        self.delay=0.1
        self.detPV='None'
        self.palette.setColor(QPalette.Foreground,Qt.green)
        self.undulatorStatus='<font color="Green">Idle</font>'
        self.monochromatorStatus='<font color="Green">Idle</font>'
        self.pixmapON=QPixmap('./Images/ShutterON.png')
        self.pixmapOFF=QPixmap('./Images/ShutterOFF.png')
        
        self.experimentFolder=None
        
        self.vblayout=QVBoxLayout(self)
        self.mainDock=DockArea(self,parent)
        self.vblayout.addWidget(self.mainDock)
        
        self.beamlineInfoDock=Dock('Beamline Info Dock',size=(1,1))
        self.dataColDock=Dock('Data Collection Dock',size=(1,8))
        #self.dataRedDock=Dock('Data reduction Dock',size=(1,8))
        self.energyDock=Dock('Energy Dock',size=(1,8))
        self.scanDock=Dock('Scan Dock',size=(1,8))
        self.mainDock.addDock(self.beamlineInfoDock)
        self.mainDock.addDock(self.dataColDock)
        self.mainDock.addDock(self.energyDock)
        #self.mainDock.addDock(self.dataRedDock)
        #self.mainDock.moveDock(self.dataColDock,'above',self.dataRedDock)
        self.mainDock.moveDock(self.dataColDock,'above',self.energyDock)
        
        self.create_beamlineInfoDock()
        self.create_dataColDock()
        self.create_energyDock()
        #self.create_dataRedDock()
        self.detectorDialogs={}
        self.detectorWidgets={}
        self.usedDetectors=[]
        self.sampleFolders={}
        self.detectorFolders={}
        self.experimentIsSet=False
        self.darkImage=False
        self.expTime=1.0
        self.sleepTime=0.0
        self.frameCount=1
        #camonitor(self.scalers['15IDD_scaler_start']['PV'],callback=self.changeCountingState)
        camonitor(self.motors['absorber']['PV'],callback=self.monitorAbsorber)
        camonitor(self.motors['shutter']['PV'],callback=self.monitorShutter)
        if self.autoShutterCheckBox.checkState()>0:
            if caget(self.motors['shutter']['PV'])==0:
                ans=QMessageBox.question(self,'Shutter status','The shutter is open. Do you want to close the shutter to proceed further?',QMessageBox.No,QMessageBox.Yes)
                if ans==QMessageBox.Yes:
                    self.shutter_OFF()
        #self.undulatorStatusLabel.setPalette(self.palette)
        #self.monochromatorStatusLabel.setPalette(self.palette)
        
        self.redServerContext = zmq.Context()
        self.redServerSocket = self.redServerContext.socket(zmq.PUB)
        self.redServerSocket.bind("tcp://*:%s" %'2036')

        
        
    def monitorAbsorber(self,**kwargs):
        """
        monitors the changes in abosorber and accordingly updates the absorber spinbox in the gui
        """
        value=kwargs['value']
        self.absSpinBox.setValue(value)
        
    def monitorShutter(self,**kwargs):
        """
        monitors the opening and closing of shutter and accordingly show the shutter status in the DataCollector GUI
        """
        value=kwargs['value']
        if value==0:
            self.shutterStatusLabel.setPixmap(self.pixmapON)
            #self.palette.setColor(QPalette.Foreground,Qt.red)
            #self.shutterStatusLabel.setText('Shutter ON')
        else:
            self.shutterStatusLabel.setPixmap(self.pixmapOFF)
            #self.palette.setColor(QPalette.Foreground,Qt.green)
            #self.shutterStatusLabel.setText('Shutter OFF')
        #self.shutterStatusLabel.setPalette(self.palette)
  
    def create_beamlineInfoDock(self):
        """
        Creates the Beamline information dock
        """
        self.BLDockLayout=pg.LayoutWidget(self)
        #try:
        self.undulatorEnergy=caget(self.BLParams['Undulator_Energy']['PV'])
        self.undulatorGap=caget(self.BLParams['Undulator_Gap']['PV'])
        self.energy=caget(self.BLParams['Energy']['PV']+'RdbkAO')
        self.wavelength= 6.62607e-34*2.9979e8/1.60217e-19/1e3/self.energy*1e10
                
        undulatorEnergyLabel=QLabel('Undulator Energy')
        self.undulatorEnergyLabel=QLabel('%.5f keV'%(self.undulatorEnergy))
        undulatorGapLabel=QLabel('Undulator Gap')
        self.undulatorGapLabel=QLabel('%.5f mm'%(self.undulatorGap))
        energyLabel=QLabel('Energy')
        undulatorStatusLabel=QLabel('Status')
        self.undulatorStatusLabel=QLabel(self.undulatorStatus)
        monochromatorStatusLabel=QLabel('Status')
        self.monochromatorStatusLabel=QLabel(self.monochromatorStatus)
        
        self.energyLabel=QLabel('%.5f keV'%self.energy)
        wavelengthLabel=QLabel('Wavelength')        
        self.wavelengthLabel=QLabel(u'%.5f \u212B'%self.wavelength)
               
        row=0
        col=0
        self.BLDockLayout.addWidget(undulatorEnergyLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.undulatorEnergyLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(undulatorGapLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.undulatorGapLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(undulatorStatusLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.undulatorStatusLabel,row=row,col=col)
        col+=1
                
        row+=1
        col=0
        self.BLDockLayout.addWidget(energyLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.energyLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(wavelengthLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.wavelengthLabel,row=row,col=col)        
        col+=1
        self.BLDockLayout.addWidget(monochromatorStatusLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.monochromatorStatusLabel,row=row,col=col)
                
        row+=1
        col=0
        JJCVLabel=QLabel('Beamsize V')
        JJCHLabel=QLabel('Beamsize H')
        self.beamsizeV=caget(self.BLParams['JJC_VSize']['PV'])
        self.beamsizeH=caget(self.BLParams['JJC_HSize']['PV'])
        self.JJCVLabel=QLabel('%.3f mm'%self.beamsizeV)
        self.JJCHLabel=QLabel('%.3f mm'%self.beamsizeH)
        
        self.BLDockLayout.addWidget(JJCVLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.JJCVLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(JJCHLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.JJCHLabel,row=row,col=col)
        
        row+=1
        col=0
        JJDVLabel=QLabel('Collimator V')
        JJDHLabel=QLabel('Collimator H')
        self.collsizeV=caget(self.BLParams['JJD_VSize']['PV'])
        self.collsizeH=caget(self.BLParams['JJD_HSize']['PV'])
        self.JJDVLabel=QLabel('%.3f mm'%self.collsizeV)
        self.JJDHLabel=QLabel('%.3f mm'%self.collsizeH)
        self.syncBLParamPushButton=QPushButton('Sync BL Info')
        self.syncBLParamPushButton.clicked.connect(self.sync_BLInfo)
        self.BLDockLayout.addWidget(JJDVLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.JJDVLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(JJDHLabel,row=row,col=col)
        col+=1
        self.BLDockLayout.addWidget(self.JJDHLabel,row=row,col=col)
        col+=2
        self.BLDockLayout.addWidget(self.syncBLParamPushButton,row=row,col=col)
        
        self.beamlineInfoDock.addWidget(self.BLDockLayout)
        
        self.sync_BLInfo()
        
        self.energyChanged.connect(self.monochromatorStatusChanged)
        self.undulatorChanged.connect(self.undulatorStatusChanged)
        self.undulatorChanging.connect(self.undulatorEnergyChanged)
        self.undulatorGapChanging.connect(self.undulatorGapChanged)
        self.jjcvChanging.connect(self.JJCV_Changing)
        self.jjchChanging.connect(self.JJCH_Changing)
        self.jjdvChanging.connect(self.JJDV_Changing)
        self.jjdhChanging.connect(self.JJDH_Changing)
        self.energyChanging.connect(self.energyWavelengthChanging)
        
        #except:
        #    QMessageBox.warning(self, 'EPICS error','Please check if 15IDA soft-IOC is running or not.',QMessageBox.Ok)
        #    return

    def create_energyDock(self):
        self.energyWidget=Energy_Widget(parent=self)
        self.energyDock.addWidget(self.energyWidget)
        # self.energyWidget.trackXtalCheckBox.setCheckState(Qt.Checked)

        
    def sync_BLInfo(self):
        """
        Sync all the beamline info
        """
        try:
            camonitor_clear(self.BLParams['Energy']['PV']+'RdbkAO')
            camonitor_clear(self.BLParams['Monochromator_Status']['PV'])
            camonitor_clear(self.BLParams['Undulator_IDStatus']['PV'])
            camonitor_clear(self.BLParams['Undulator_Energy']['PV'])
            camonitor_clear(self.BLParams['Undulator_Gap']['PV'])
            camonitor_clear(self.BLParams['JJC_VSize']['PV'],callback=self.JJCV_changed)
            camonitor_clear(self.BLParams['JJC_HSize']['PV'],callback=self.JJCH_changed)
            camonitor_clear(self.BLParams['JJD_VSize']['PV'],callback=self.JJDV_changed)
            camonitor_clear(self.BLParams['JJD_HSize']['PV'],callback=self.JJDH_changed)
        except:
            pass
        camonitor(self.BLParams['Energy']['PV']+'RdbkAO',callback=self.energyWavelengthChanged)
        camonitor(self.BLParams['Monochromator_Status']['PV'],callback=self.monochromatorStatusCheck)
        camonitor(self.BLParams['Undulator_IDStatus']['PV'],callback=self.undulatorIDStatusCheck)
        camonitor(self.BLParams['Undulator_Energy']['PV'],callback=self.undulatorEnergyStatusCheck)
        camonitor(self.BLParams['Undulator_Gap']['PV'],callback=self.undulatorGapStatusCheck)
        camonitor(self.BLParams['JJC_VSize']['PV'],callback=self.JJCV_changed)
        camonitor(self.BLParams['JJC_HSize']['PV'],callback=self.JJCH_changed)
        camonitor(self.BLParams['JJD_VSize']['PV'],callback=self.JJDV_changed)
        camonitor(self.BLParams['JJD_HSize']['PV'],callback=self.JJDH_changed)        
        
        
    def monochromatorStatusCheck(self,**kwargs):
        """
        Updates the status of the monochromator
        """
        value=kwargs['value']
        self.energyChanged.emit(value)
        
        
    def monochromatorStatusChanged(self,value):
        if value==1:
            #self.palette.setColor(QPalette.Foreground,Qt.red)
            self.monochromatorStatus='<font color="Red">Moving</font>'
        else:
            #self.palette.setColor(QPalette.Foreground,Qt.green)
            self.monochromatorStatus='<font color="Green">Idle</font>'
        self.monochromatorStatusLabel.setText(self.monochromatorStatus)
        #self.monochromatorStatusLabel.setPalette(self.palette)
        pg.QtGui.QApplication.processEvents()
        
        
    def undulatorIDStatusCheck(self,**kwargs):
        """
        Updates the status of the Undulator
        """
        value=kwargs['value']
        self.undulatorChanged.emit(value)
        
    def undulatorStatusChanged(self,value):
        if value==1:
            #self.palette.setColor(QPalette.Foreground,Qt.red)
            self.undulatorStatus='<font color="Red">Moving</font>'
        else:
            #self.palette.setColor(QPalette.Foreground,Qt.green)
            self.undulatorStatus='<font color="Green">Idle</font>'
        self.undulatorStatusLabel.setText(self.undulatorStatus)
        self.undulatorStatusLabel.setPalette(self.palette)

        
    def undulatorEnergyStatusCheck(self,**kwargs):
        """
        Updates the energy of the undulator
        """
        value=kwargs['value']
        self.undulatorChanging.emit(value)
        
    def undulatorEnergyChanged(self,value):
        self.undulatorEnergy=value
        self.undulatorEnergyLabel.setText('%.5f keV'%self.undulatorEnergy)
        #pg.QtGui.QApplication.processEvents()
        
    def undulatorGapStatusCheck(self,**kwargs):
        """
        Updates the Gap of the undulator
        """
        value=kwargs['value']
        self.undulatorGapChanging.emit(value)
        
    def undulatorGapChanged(self,value):
        self.undulatorGap=value
        self.undulatorGapLabel.setText('%.5f mm'%self.undulatorGap)

        
    def JJCV_changed(self, value=None, **kwargs):
        """
        Updates the JJC Vertical slit sizes in the GUI by sensing the changes in the slit sizes
        """
        self.jjcvChanging.emit(value)
        
    def JJCV_Changing(self,value):
        try:
            self.beamsizeV= value # caget(self.BLParams['JJC_VSize']['PV'])
            self.JJCVLabel.setText('%.3f mm'%self.beamsizeV)
            self.experimentLogHandle.write('#Beamsize-Vertical : %.3f mm\n'%self.beamsizeV)
        except:
            pass
        
        
    def JJCH_changed(self, value=None,**kwargs):
        """
        Updates the JJC Horizontal slit sizes in the GUI by sensing the changes in the slit sizes
        """
        self.jjchChanging.emit(value)

    def JJCH_Changing(self,value):       
        try:
            self.beamsizeH=value#caget(self.BLParams['JJC_HSize']['PV'])
            self.JJCHLabel.setText('%.3f mm'%self.beamsizeH)
            self.experimentLogHandle.write('#Beamsize-Horizontal : %.3f mm\n'%self.beamsizeH)
        except:
            pass

        
    def JJDV_changed(self, value=None,**kwargs):
        """
        Updates the JJD Vertical slit sizes in the GUI by sensing the changes in the slit sizes
        """
        self.jjdvChanging.emit(value)
        
    def JJDV_Changing(self,value):
        try:
            self.collsizeV=value#caget(self.BLParams['JJD_VSize']['PV'])
            self.JJDVLabel.setText('%.3f mm'%self.collsizeV)
            self.experimentLogHandle.write('#Collimator-Vertical : %.3f mm\n'%self.collsizeV)
        except:
            pass
        
    def JJDH_changed(self, value=None,**kwargs):
        """
        Updates the JJD Horizontal slit sizes in the GUI by sensing the changes in the slit sizes
        """
        self.jjdhChanging.emit(value)
        
    def JJDH_Changing(self,value):
        try:
            self.collsizeH=value#caget(self.BLParams['JJD_HSize']['PV'])
            self.JJDHLabel.setText('%.3f mm'%self.collsizeH)
            self.experimentLogHandle.write('#Collimator-Horizontal : %.3f mm\n'%self.collsizeH)
        except:
            pass
        
        
        
    def energyWavelengthChanged(self,**kwargs):
        """
        Updates the energy in the GUI by sensing the energy change in EPICS
        """
        value=kwargs['value']
        self.energyChanging.emit(value)
        
        
    def energyWavelengthChanging(self,value):
        self.energy=value    
        self.energyLabel.setText('%.5f keV'%self.energy)
        self.wavelength= 6.62607e-34*2.9979e8/1.60217e-19/1e3/self.energy*1e10
        self.wavelengthLabel.setText(u'%.5f \u212B'%self.wavelength)
        try:
            self.experimentLogHandle.write('#X-ray Energy : %.5f keV\n'%self.energy)
            self.experimentLogHandle.write('#X-ray Wavelength : %.5f Angs\n'%self.wavelength)
        except:
            pass
        #pg.QtGui.QApplication.processEvents()
        
    def change_Energy(self,energy):
        """
        Changes the energy in keV value supplied and optimizes the undulator and other optics
        """
        try:
            #caput('15IDA:pid_mono_1.FBON',0) #Switching intensity feedback off
            caput("15IDA:KohzuModeB0.VAL",1) #Putting the monochromator in Automode (1) from Manual mode (0)
            caput(self.BLParams['Energy']['PV']+'AO.VAL',energy)
            QtTest.QTest.qWait(10)
            while self.monochromatorStatus=='<font color="Red">Moving</font>':
                QtTest.QTest.qWait(10)
            caput(self.BLParams['Undulator_Energy']['PV']+'Set.VAL',energy+0.17)
            caput('15ID:Start.VAL',1)
            QtTest.QTest.qWait(self.sleepTime*1000)
            #caput('15IDA:pid_mono_1.FBON',1) #Switching intensity feedback on
        except:
            QMessageBox.warning(self,'Value error','The energy value should be floating point value.',QMessageBox.Ok)
            
        
    
    def create_dataColDock(self):
        """
        Creates the data collection dock
        """
        self.dataColLayout=pg.LayoutWidget(self)
        row=0
        col=0
        self.newExperimentPushButton=QPushButton('New Experiment')
        self.newExperimentPushButton.clicked.connect(self.newExperiment)
        experimentFolderLabel=QLabel('Experimental Folder')
        
        self.experimentFolderLineEdit=QLineEdit()
        self.openExperimentPushButton=QPushButton('Open Experiment')
        self.openExperimentPushButton.clicked.connect(lambda x: self.openExperiment(expFolder=None))
        self.openScannerPushButton=QPushButton('Open Scanner')
        self.openScannerPushButton.clicked.connect(self.openScanner)
        self.dataColLayout.addWidget(self.newExperimentPushButton,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(experimentFolderLabel,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(self.experimentFolderLineEdit,row=row,col=col,colspan=2)
        col+=2
        self.dataColLayout.addWidget(self.openExperimentPushButton,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(self.openScannerPushButton,row=row,col=col)
        
        row+=1
        col=0
        detAvailableLabel=QLabel('Detectors Available')
        self.detectorComboBox=QComboBox()
        self.detectorComboBox.addItems(list(self.detectors.keys()))
        self.addDetectorPushButton=QPushButton('Add Detector')
        self.addDetectorPushButton.clicked.connect(lambda x: self.addDetector(detname=None))
        self.showDetectorPushButton=QPushButton('Show Detector')
        self.showDetectorPushButton.clicked.connect(self.showDetector)
        detInUseLabel=QLabel('Detectors in use')
        self.removeDetectorPushButton=QPushButton('Remove Detector')
        self.removeDetectorPushButton.clicked.connect(self.removeDetector)
        self.detectorListWidget=QListWidget()
        self.dataColLayout.addWidget(detAvailableLabel,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(self.detectorComboBox,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(detInUseLabel,row=row,col=col)
        row=row+1
        col=1
        self.dataColLayout.addWidget(self.addDetectorPushButton,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(self.detectorListWidget,row=row,col=col,rowspan=3,colspan=4)
        row+=1
        col=1
        self.dataColLayout.addWidget(self.showDetectorPushButton,row=row,col=col)
        row+=1
        col=1
        self.dataColLayout.addWidget(self.removeDetectorPushButton,row=row,col=col)       
        
        
        row=row+1
        sampleNameLabel=QLabel('Sample Name')
        self.sampleNameLineEdit=QLineEdit()
        self.sampleNameLineEdit.returnPressed.connect(self.sampleNameChanged)
        sampleImgCountLabel=QLabel('Next Image Number')
        self.sampleImgCounterLabel=QLabel('1')
        self.dataColLayout.addWidget(sampleNameLabel,row=row,col=0)
        self.dataColLayout.addWidget(self.sampleNameLineEdit,row=row,col=1,colspan=3)
        self.dataColLayout.addWidget(sampleImgCountLabel,row=row,col=4)
        self.dataColLayout.addWidget(self.sampleImgCounterLabel,row=row,col=5)        
        
        
        row=row+1
        self.pdInPositionCheckBox=QCheckBox('PD Position')
        self.pdInPositionCheckBox.setTristate(False)
        self.pdInPositionCheckBox.stateChanged.connect(self.pdInPositionStateChanged)
        self.pdInPositionLineEdit=QLineEdit('-41.5')
        self.beamInPositionCheckBox=QCheckBox('Beam position')
        self.beamInPositionCheckBox.setTristate(False)
        self.beamInPositionCheckBox.stateChanged.connect(self.beamInPositionStateChanged)
        self.beamInPositionLineEdit=QLineEdit('0.0')
        self.mirrorInPositionCheckBox=QCheckBox('Mirror position')
        self.mirrorInPositionCheckBox.setTristate(False)
        self.mirrorInPositionCheckBox.stateChanged.connect(self.mirrorInPositionStateChanged)
        self.mirrorInPositionLineEdit=QLineEdit('-39.0')
        self.enableDisablePDPushButton=QPushButton('Enable')
        self.pdInPositionLineEdit.setDisabled(True)
        self.beamInPositionLineEdit.setDisabled(True)
        self.mirrorInPositionLineEdit.setDisabled(True)
        self.dataColLayout.addWidget(self.pdInPositionCheckBox,row=row,col=0)
        self.dataColLayout.addWidget(self.pdInPositionLineEdit,row=row,col=1)
        self.dataColLayout.addWidget(self.beamInPositionCheckBox,row=row,col=2)
        self.dataColLayout.addWidget(self.beamInPositionLineEdit,row=row,col=3)
        self.dataColLayout.addWidget(self.mirrorInPositionCheckBox,row=row,col=4)
        self.dataColLayout.addWidget(self.mirrorInPositionLineEdit,row=row,col=5)
        
        row=row+1
        self.pdInButton=QPushButton('Pd in')
        self.beamInButton=QPushButton('Beam in')
        self.mirrorInButton=QPushButton('Mirror in')
        self.pdInButton.clicked.connect(self.bringPDIn)
        self.beamInButton.clicked.connect(self.bringBeamIn)
        self.mirrorInButton.clicked.connect(self.bringMirrorIn)
        self.dataColLayout.addWidget(self.pdInButton,row=row,col=0,colspan=2)
        self.dataColLayout.addWidget(self.beamInButton,row=row,col=2,colspan=2)
        self.dataColLayout.addWidget(self.mirrorInButton,row=row,col=4,colspan=2)
        
        row=row+1
        col=0
        expTimeLabel=QLabel('Exposure time (s)')
        self.expTimeLineEdit=QLineEdit('1.0')
        frameCountLabel=QLabel('# of Frames')
        self.frameCountLineEdit=QLineEdit('1')
        sleepTimeLabel=QLabel('Sleep time (s)')
        self.sleepTimeLineEdit=QLineEdit('0.0')
        self.expTimeLineEdit.returnPressed.connect(self.expTimeChanged)
        self.frameCountLineEdit.returnPressed.connect(self.frameCountChanged)
        self.sleepTimeLineEdit.returnPressed.connect(self.sleepTimeChanged)
        self.dataColLayout.addWidget(expTimeLabel,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(self.expTimeLineEdit,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(frameCountLabel,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(self.frameCountLineEdit,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(sleepTimeLabel,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(self.sleepTimeLineEdit,row=row,col=col)
        
        row=row+1
        col=0
        shutterTimeLabel=QLabel('Shutter time')
        self.dataColLayout.addWidget(shutterTimeLabel,row=row,col=col)
        col=col+1
        self.shutterTimeLineEdit=QLineEdit('0.0')
        self.dataColLayout.addWidget(self.shutterTimeLineEdit,row=row,col=col)
        col=col+3
        absLabel=QLabel('Attenuator')
        self.absSpinBox=QSpinBox()
        self.absSpinBox.setRange(0,15)
        self.absSpinBox.setValue(int(caget(self.motors['absorber']['PV'])))
        self.absSpinBox.valueChanged.connect(self.absorberChanged)
        self.absSpinBox.setSingleStep(1)
        self.dataColLayout.addWidget(absLabel,row=row,col=col)
        col=col+1
        self.dataColLayout.addWidget(self.absSpinBox,row=row,col=col) 
        
                
        row=row+1
        instrumentStatusLabel=QLabel('Instrument status')
        self.instrumentStatus=QLabel()
        measurementStatusLabel=QLabel('Measurement Progress')
        self.measurementProgressDialog=QProgressBar()
        self.dataColLayout.addWidget(instrumentStatusLabel,row=row,col=0)
        self.dataColLayout.addWidget(self.instrumentStatus,row=row,col=1,colspan=3)
        self.dataColLayout.addWidget(measurementStatusLabel,row=row,col=4)
        self.dataColLayout.addWidget(self.measurementProgressDialog,row=row,col=5,colspan=1)
        
        
        row=row+1
        self.collectTransmissionCheckBox=QCheckBox('Collect Transmission')
        self.collectTransmissionCheckBox.setTristate(False)        
        self.collectDarkCheckBox=QCheckBox('Collect Dark Images')
        self.collectDarkCheckBox.setTristate(False)
        self.collectDarkCheckBox.setChecked(False)
        self.autoShutterCheckBox=QCheckBox('Auto Shutter')
        self.autoShutterCheckBox.setTristate(False)
        self.autoShutterCheckBox.setChecked(True)
        pumpVolLabel=QLabel('Pump Vol (uL)')
        try:
            self.pumpVolLineEdit=QLineEdit(str(caget('15IDD:PHDUltra:TargetVolume_RBV')))
        except:
            self.pumpVolLineEdit=QLineEdit('Pump not Connected')
        self.pumpVolLineEdit.returnPressed.connect(self.targetVolumeChanged)
        self.autoPumpCheckBox=QCheckBox('Auto Pump')
        self.autoPumpCheckBox.setTristate(False)
        self.autoPumpCheckBox.setChecked(False)
        
        self.dataColLayout.addWidget(self.autoShutterCheckBox,row=row,col=0)
        self.dataColLayout.addWidget(self.collectTransmissionCheckBox,row=row,col=1)
        self.dataColLayout.addWidget(self.collectDarkCheckBox,row=row,col=2)
        self.dataColLayout.addWidget(pumpVolLabel,row=row,col=3)
        self.dataColLayout.addWidget(self.pumpVolLineEdit,row=row,col=4)
        self.dataColLayout.addWidget(self.autoPumpCheckBox,row=row,col=5)
        
        row=row+1
        pdTransLabel=QLabel('PD Transmission:')
        self.PDTransmissionLabel=QLabel()
        self.PDTransmissionButton=QPushButton('Collect PD Transmission')
        self.PDTransmissionButton.clicked.connect(self.collect_transmission)
        bsTransLabel=QLabel('BS Transmission:')
        self.BSTransmissionLabel=QLabel()
        self.dataColLayout.addWidget(pdTransLabel,row=row,col=0)
        self.dataColLayout.addWidget(self.PDTransmissionLabel,row=row,col=1)
        self.dataColLayout.addWidget(self.PDTransmissionButton,row=row,col=2)
        self.dataColLayout.addWidget(bsTransLabel,row=row,col=3)
        self.dataColLayout.addWidget(self.BSTransmissionLabel,row=row,col=4)
        self.shutterStatusLabel=QLabel('Shutter OFF')
        self.dataColLayout.addWidget(self.shutterStatusLabel,row=row,col=5)
        
        
        row=row+1
        positionerLabel=QLabel('Positioner')
        self.positionerComboBox=QComboBox()
        self.positionerComboBox.addItems(list(self.motors.keys()))
        self.addPositionerPushButton=QPushButton('Add Positioner')
        self.removePositionerPushButton=QPushButton('Remove Positioners')
        self.openPositionerFilePushButton=QPushButton('Open Positioner file')
        self.savePositionerFilePushButton=QPushButton('Save Positioner file')
        col=0
        self.dataColLayout.addWidget(positionerLabel,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(self.positionerComboBox,row=row,col=col)
        col+=1
        self.dataColLayout.addWidget(self.addPositionerPushButton,row=row,col=col)
        self.addPositionerPushButton.clicked.connect(self.addPositioner)
        col+=1
        self.dataColLayout.addWidget(self.removePositionerPushButton,row=row,col=col)
        self.removePositionerPushButton.clicked.connect(self.removePositioner)
        col+=1
        self.dataColLayout.addWidget(self.openPositionerFilePushButton,row=row,col=col)
        self.openPositionerFilePushButton.clicked.connect(lambda x: self.openPositionerFile(fname=None))
        col+=1
        self.dataColLayout.addWidget(self.savePositionerFilePushButton,row=row,col=col)
        self.savePositionerFilePushButton.clicked.connect(self.savePositionerFile)
        
        row=row+1
        col=0
        self.positionerTable=QTableWidget()
        self.dataColLayout.addWidget(self.positionerTable,row=row,col=col,colspan=6)
        self.positionerTable.setColumnCount(4)
        self.positionerTable.setHorizontalHeaderLabels(['Positioners','Positoner values','Positioner types','Positioner constraint'])
        self.positionerTable.resizeColumnsToContents()
        row=row+1
        #self.collectDarkButton=QPushButton('Collect Dark')
        #self.collectDarkButton.clicked.connect(self.collect_dark)
        self.autoReduceCheckBox=QCheckBox('Auto Reduce')
        self.autoReduceCheckBox.setTristate(False)
        self.staticCollectButton=QPushButton('Collect Static')
        self.staticCollectButton.clicked.connect(self.static_collect)
        self.loopSpinBox=QSpinBox()
        loopSleepLabel=QLabel('Sleep Time (s)')
        self.loopSleepTimeLineEdit=QLineEdit('0.0')
        self.loopSleepTimeLineEdit.returnPressed.connect(self.loopSleepTimeChanged)
        self.loopSpinBox.setRange(1,1000)
        self.loopSpinBox.setValue(1)
        self.dynamicCollectButton=QPushButton('Collect Dynamic')
        self.dynamicCollectButton.clicked.connect(self.dynamic_collect)
        #self.dataColLayout.addWidget(self.collectDarkButton,row=row,col=0)
        self.dataColLayout.addWidget(self.autoReduceCheckBox,row=row,col=0)
        self.dataColLayout.addWidget(self.staticCollectButton,row=row,col=1)
        self.dataColLayout.addWidget(self.loopSpinBox,row=row,col=2)
        self.dataColLayout.addWidget(loopSleepLabel,row=row,col=3)
        self.dataColLayout.addWidget(self.loopSleepTimeLineEdit,row=row,col=4)
        self.dataColLayout.addWidget(self.dynamicCollectButton,row=row,col=5)        
        
        self.dataColDock.addWidget(self.dataColLayout)
        
    def loopSleepTimeChanged(self):
        try:
            self.loopSleepTime=float(self.loopSleepTimeLineEdit.text())
        except:
            QMessageBox.warning(self,'Value Error', 'Please Enter numbers only')
            self.loopSleeptTime=0.0
            self.loopSleepTimeLineEdit.setText('0.0')
			
        
    def targetVolumeChanged(self):
        try:
            vol=float(self.pumpVolLineEdit.text())
            try:
                caput('15IDD:PHDUltra:TargetVolume',vol)
            except:
                QMessageBox.warning(self,'Pump error','Please check the pump in connected',QMessageBox.Ok)
        except:
            QMessageBox.warning(self,'Value error','Please provide numerical values only',QMessageBox.Ok)
        
        
#    def create_dataRedDock(self):
#        """
#        Create the data reduction Dock for on the fly data reduction from 2D image to azimuthally integrated 1D SAXS data
#        """
#        self.dataReducer=Data_Reducer(poniFile=None)
#        #self.dataReducer.poniFile=None
#        self.dataRedDock.addWidget(self.dataReducer)
#        self.dataReducer.extractedFolder='/tmp'
#        self.dataReducer.extractedFolderLineEdit.setText('/tmp')
        
    def pdInPositionStateChanged(self):
        """
        Enable disable PD motor settings
        """
        if self.pdInPositionCheckBox.isChecked():
            self.pdInPositionLineEdit.setDisabled(False)
        else:
            self.pdInPositionLineEdit.setDisabled(True)
        pg.QtGui.QApplication.processEvents()
            
    def beamInPositionStateChanged(self):
        """
        """
        if self.beamInPositionCheckBox.isChecked():
            self.beamInPositionLineEdit.setDisabled(False)
        else:
            self.beamInPositionLineEdit.setDisabled(True)
        pg.QtGui.QApplication.processEvents()    
            
    def mirrorInPositionStateChanged(self):
        """
        """
        if self.mirrorInPositionCheckBox.isChecked():
            self.mirrorInPositionLineEdit.setDisabled(False)
        else:
            self.mirrorInPositionLineEdit.setDisabled(True)
        pg.QtGui.QApplication.processEvents()
    
    def openPositionerFile(self,fname=None):
        """
        Open saved positioner file for dynamic measurements
        """
        if fname is None:
            fname=str(QFileDialog.getOpenFileName(self,'Select a positioner file',self.cwd,("Positioner Files (*.txt)"))[0])
            self.positionerFile=fname
        if fname!='':
            fh=open(fname,'r')
            lines=fh.readlines()
            fh.close()
            try:
                if len(lines)>0:
                    self.positionerTable.clear()
                    self.positionerTable.setHorizontalHeaderLabels(['Positioners','Positoner values','Positioner types','Positioner constraint'])
                    self.positioner={}                
                    self.positioner_free={}
                    self.positioner_coupled={}
                    for row in range(self.positionerTable.rowCount()):
                        self.positionerTable.removeRow(0)
                    i=0
                    for line in lines:     
                        if line[0]!='#':
                            self.positioner[i]={}
                            row=i
                            self.positionerTable.insertRow(row)
                            txt=line.strip('\n').split()
                            col=0
                            self.positioner[i]['motorName']=txt[0]
                            if txt[0]=='Energy':
                                currVal=caget(self.motors[txt[0]]['PV']+'RdbkAO')
                            elif txt[0]=='Undulator_Energy':
                                currVal=caget(self.motors[txt[0]]['PV'])
                            else:
                                currVal=caget(self.motors[txt[0]]['PV']+'.RBV')
                            self.positionerTable.setItem(row,col,QTableWidgetItem(txt[0]))
                            col+=1
                            self.positioner[i]['valueText']=txt[1]
                            self.positionerTable.setItem(row,col,QTableWidgetItem(txt[1]))
                            values=eval(txt[1])
                            print(values)
                            if type(values)==list:
                                self.positioner[i]['values']=array(values)
                            else:
                                self.positioner[i]['values']=values
                            col+=1
                            self.positioner[i]['valueType']=txt[2]
                            self.positionerTable.setItem(row,col,QTableWidgetItem(txt[2]))
                            if self.positioner[i]['valueType']=='relative':
                                self.positioner[i]['values']=self.positioner[i]['values']+currVal
                            col+=1
                            self.positioner[i]['constraint']=txt[3]
                            self.positionerTable.setItem(row,col,QTableWidgetItem(txt[3]))
                            if txt[3]=='free':
                                self.positioner_free[txt[0]]=self.positioner[i]['values']
                            else:
                                self.positioner_coupled[txt[0]]=self.positioner[i]['values']
                            i+=1
                    self.positionerTable.resizeColumnsToContents()
                    if not self.check_coupledPositioner():
                        QMessageBox.warning(self,'Positioner error','The numper of points of all the coupled positioners should be same. Please check the coupled positioners before starting any dynamic measurement.',QMessageBox.Ok)
                else:
                    QMessageBox.warning(self,'File error','It seems there are there are no lines to read from the file.',QMessageBox.Ok)
            except:
                QMessageBox.warning(self,'File error','The file is not a valid positioner file.\n\n'+traceback.format_exc(),QMessageBox.Ok)
        
    def check_coupledPositioner(self):
        """
        check the number of points on all the coupled positioner and returns True if all the number of points are same and return False if any two of the coupled positioner have different number of points
        """
        if len(list(set([len(self.positioner_coupled[key]) for key in self.positioner_coupled.keys()])))>1:
            return False
        else:
            return True
        
        
    def create_measurementList(self):
        """
        Creates a measurement List by reading the values from the postionerTable the 
        """
        coupled_len=len(self.positioner_coupled[list(self.positioner_coupled.keys())[0]])
        self.measurementList={}
        for keyc in self.positioner_coupled.keys():
            self.measurementList[keyc]=[]
        self.measurementCount=0
        if len(self.positioner_free.keys())!=0:
            for keyf in self.positioner_free.keys():
                self.measurementList[keyf]=[]
                for value in self.positioner_free[keyf]:                    
                    for i in range(coupled_len):
                        self.measurementList[keyf].append(value)
                        for keyc in self.positioner_coupled.keys():
                            self.measurementList[keyc].append(self.positioner_coupled[keyc][i])
                        self.measurementCount+=1
        else:
            for i in range(coupled_len):
                for keyc in self.positioner_coupled.keys():
                    self.measurementList[keyc].append(self.positioner_coupled[keyc][i])
                self.measurementCount+=1
        
        
    def check_motorLimits(self):
        """
        Check the limits of all the motors involved in the dynamic measurments
        """
        check=[]
        for key in self.measurementList.keys():
            if key!='Energy' and key!='Undulator Energy':
                low=caget(self.motors[key]['PV']+'.LLM')
                high=caget(self.motors[key]['PV']+'.HLM')
                valmin,valmax=amin(self.measurementList[key]), amax(self.measurementList[key])
                if valmin>=low and valmin<high:
                    check.append(True)
                else:
                    check.append(False)
                    print('The positioner values of %s are not within  the limits.'%key)
        if all(check):
            return True
        else:
            return False                           
        
        
        
        
    def savePositionerFile(self):
        """
        Saves positioer file values from the positionerTable for future dynamic measurements
        """
        QMessageBox.information(self,"Under development","This is still under development. Check back later. Thank you!",QMessageBox.Ok)
        
    def addPositioner(self):
        """
        Add positioner to the postioner table
        """
        QMessageBox.information(self,"Under development","This is still under development. Check back later. Thank you!",QMessageBox.Ok)
        
        
    def removePositioner(self):
        """
        Removes selected positoners from the positioner table
        """
        QMessageBox.information(self,"Under development","This is still under development. Check back later. Thank you!",QMessageBox.Ok)
        
    

    def addDetector(self,detname=None):
        """
        Adds and opens an Area detector Module and keep it ready for data collection and viewing
        """
        if detname is None:
            detname=str(self.detectorComboBox.currentText())
        if detname not in self.usedDetectors:
            self.detectorWidgets[detname]=Detector_Widget(imgFName='img_'+detname)
            # if self.experimentFolder is not None:
            #     self.detectorWidgets[detname].carsImgFolderChanged(imgFolder=self.experimentFolder)
            #     #self.detectorWidgets[detname].carsImgFolder=self.experimentFolder
            # else:
            #     QMessageBox.warning(self,'File Error','Please add an experiment folder first!',QMessageBox.Ok)
            #     return
            #
            self.detectorWidgets[detname].detectorComboBox.setCurrentIndex(self.detectorWidgets[detname].detectorComboBox.findText(detname))
            if self.experimentFolder is not None:
                self.detectorWidgets[detname].carsImgFolderChanged(imgFolder=self.experimentFolder)
            else:
                QMessageBox.warning(self,'File Error','Please add an experiment folder first!',QMessageBox.Ok)
                return
            self.detectorComboBox.setCurrentIndex(self.detectorComboBox.findText(detname))
            if self.detectorWidgets[detname].connection:
                self.detectorDialogs[detname]=QDialog(self)
                vbLayout=QVBoxLayout(self.detectorDialogs[detname])
                vbLayout.addWidget(self.detectorWidgets[detname])
                self.detectorDialogs[detname].setWindowTitle(detname)
                self.detectorDialogs[detname].setGeometry(810,0,800,1600)
                self.detectorDialogs[detname].show()
                self.detectorListWidget.addItem(self.detectorComboBox.currentText())
                self.usedDetectors.append(detname)
                self.experimentLogHandle.write('##Detector Added on: '+time.asctime()+'\n')
                self.experimentLogHandle.write('#Detectors : '+str(self.usedDetectors)+'\n')
                self.experimentLogHandle.close()
                self.experimentLogHandle=open(self.experimentLogFile,'a')
                self.experimentIsSet=True
                self.expTimeChanged()
            else:
                del self.detectorWidgets[detname]
            if str(self.sampleNameLineEdit.text())!='':
                self.sampleNameChanged()
        else:
            QMessageBox.warning(self,'Detector Error',detname+'  already in use.',QMessageBox.Ok)
            
    def showDetector(self):
        """
        Opens of the Area detector corresponding to the selected detector in the list of detectors
        """
        if self.detectorListWidget.selectedItems()!=[]:
            for item in self.detectorListWidget.selectedItems():
                detname=str(item.text())
                self.detectorDialogs[detname].show()
        else:
            QMessageBox.warning(self,'Detector Error','Please select a detector in the Detector list to show.',QMessageBox.Ok)          
        
    
    def removeDetector(self):
        """
        Removes the detector from the program and closes the corresponding detector module
        """
        for item in self.detectorListWidget.selectedItems():
            detname=str(item.text())
            self.detectorListWidget.takeItem(self.detectorListWidget.row(item))
            self.usedDetectors.remove(detname)
            self.detectorDialogs[detname].done(0)
        
    def newExperiment(self):
        """
        Sets the data collection software for a new experiment in which it opens up a dialog for a new experimental folder
        """
        for row in range(self.detectorListWidget.count()):
            self.detectorListWidget.item(row).setSelected(True)
        self.removeDetector()
        self.experimentFolder=str(QFileDialog.getExistingDirectory(self,caption='Open new experiment folder',directory='/home/epics/CARS5/Data/Data/saxs'))
        self.experimentFolderLineEdit.setText(self.experimentFolder)
        self.experimentLogFile=os.path.join(self.experimentFolder,'experiment.log')
        if os.path.exists(self.experimentLogFile):
            ans=QMessageBox.question(self,'Experiment warning','The experiment folder already exists. Do you want to append data to the folder?',QMessageBox.No, QMessageBox.Yes)
            if ans==QMessageBox.Yes:
                self.openExperiment(expFolder=self.experimentFolder)
            else:
                self.newExperiment()
        else:
            self.experimentLogHandle=open(self.experimentLogFile,'a')
            self.experimentLogHandle.write('##Experiment started on: '+time.asctime()+'\n')
            self.energyWavelengthChanging(self.energy)
            self.JJCH_Changing(self.beamsizeH)
            self.JJCV_Changing(self.beamsizeV)
            self.JJDH_Changing(self.collsizeH)
            self.JJDV_Changing(self.collsizeV)
            self.experimentLogHandle.close()
            self.experimentLogHandle=open(self.experimentLogFile,'a')
        self.experimentIsSet=True
        self.sampleNameLineEdit.clear()
        
    def openExperiment(self,expFolder=None):
        """
        Sets up the data collection software to continue with an old experiment which opens up a dialog to select the experimental folder.
        This also imports all the detector used for the old experiment.
        """
        for row in range(self.detectorListWidget.count()):
            self.detectorListWidget.item(row).setSelected(True)
        self.removeDetector()
        if expFolder is not None:
            self.experimentFolder=expFolder
        else:
            self.experimentFolder=str(QFileDialog.getExistingDirectory(self,caption='Open existing experiment folder',directory='/home/epics/CARS5/Data/chemmat/Data/saxs'))
            self.experimentFolderLineEdit.setText(self.experimentFolder)
        self.experimentLogFile=os.path.join(self.experimentFolder,'experiment.log')
        
        #This is to read the required details from the old file like detector information used in the experiment
        try:
            self.experimentLogHandle=open(self.experimentLogFile,'r')
        except:
            QMessageBox.warning(self,'File Error','It looks like you are doing a new experiment. Please use New Experiment.',QMessageBox.Ok)
            return
        lines=self.experimentLogHandle.readlines()
        self.experimentLogHandle.close()
        self.experimentLogHandle=open(self.experimentLogFile,'w')
        self.experimentLogHandle.write('##Experiment started on: '+time.asctime()+'\n')
        self.energyWavelengthChanging(self.energy)
        self.JJCH_Changing(self.beamsizeH)
        self.JJCV_Changing(self.beamsizeV)
        self.JJDH_Changing(self.collsizeH)
        self.JJDV_Changing(self.collsizeV)
        self.experimentLogHandle=open(self.experimentLogFile,'a')
        for line in lines:
            if '#Detectors :' in line:
                detnames=line.split(':')[1].strip().lstrip('[').rstrip(']').split(',')
                
        try:
            for detname in detnames:
                self.addDetector(detname=detname.lstrip('\'').rstrip('\''))
            self.experimentLogHandle.close()        
            #This is to open the old file to append the log file with new experimental information
            self.experimentLogHandle=open(self.experimentLogFile,'a')
            self.experimentIsSet=True
        except:
            QMessageBox.warning(self,'Detector Error','No detector found in the loaded experimental settings. Add atleast one detector to use.',QMessageBox.Ok)
        self.sampleNameLineEdit.clear()
        
        #except:
        #    QMessageBox.warning(self,'Detector warning','No detectors found in the loaded experiment. Please add a detector to continue with measurement.',QMessageBox.Ok)
    
    def openScanner(self):
        """
        Sets up and opens the scanner for scanning purposes
        """
        if self.experimentIsSet:
            self.mainDock.addDock(self.scanDock,'above',self.dataColDock)
            #self.mainDock.moveDock(self.scanDock,'above',self.dataColDock)
            self.scanFolder=os.path.join(self.experimentFolder,'Scans')
            if not os.path.exists(self.scanFolder):
                os.makedirs(self.scanFolder)
            if not hasattr(self,'scanWidget'):
                self.scanWidget=Scanner(self.scanFolder)
                self.scanDock.addWidget(self.scanWidget)
            else:
                self.scanWidget.changeScanFolder(scanFolder=self.scanFolder)
        else:
            QMessageBox.warning(self,'Experiment warning','Please create or open an experiment first.',QMessageBox.Ok)
        
        
    def absorberChanged(self):
        """
        Changes the absorber number used for the measurments
        """
        caput(self.motors['absorber']['PV'],self.absSpinBox.value())
        
    def expTimeChanged(self):
        """
        Changes the exposure time of the detector
        """
        try:
            self.expTime=float(self.expTimeLineEdit.text())
            for detname in self.usedDetectors:
                self.detectorWidgets[detname].expTimeLineEdit.setText(str(self.expTime))
        except:
            QMessageBox.warning(self,'Value Error','Please input numbers only.\n Setting Exposure time to 1.0 s.',QMessageBox.Ok)
            self.expTime=1.0
            self.expTimeLineEdit.setText(str(self.expTime))
                
    def frameCountChanged(self):
        """
        Changes the number of frames for each data count
        """
        try:
            self.frameCount=int(self.frameCountLineEdit.text())
        except:
            QMessageBox.warning(self,'Value Error','Please input numbers only.\n Setting # of frames to 1.',QMessageBox.Ok)
            self.frameCount=1
            self.frameCountLineEdit.setText(str(self.frameCount))

    def sleepTimeChanged(self):
        """
        Changes the sleep time of the detector
        """
        try:
            self.sleepTime=float(self.sleepTimeLineEdit.text())
        except:
            QMessageBox.warning(self,'Value Error','Please input numbers only.\n Setting sleep time to 0.0 s.',QMessageBox.Ok)
            self.sleepTime=0.0
            self.sleepTimeLineEdit.setText(str(self.sleepTime))

        
        
        
    def sampleNameChanged(self):
        """
        Changes the sample name and create a new folder with the same name as the sample within the experimental folder. If the sample name exists it just updates the image counter to the latest available counter number
        """
        if self.experimentIsSet and self.detectorListWidget.count()>0:
            if str(self.sampleNameLineEdit.text())!='':
                self.sampleName=str(self.sampleNameLineEdit.text())
                self.sampleFolder=os.path.join(self.experimentFolder,self.sampleName)
                if os.path.exists(self.sampleFolder):
                    ans=QMessageBox.question(self,'Sample exists','The Sample name and the corresponding data folder already exists!\n Appending data in the same folder with different file number.',QMessageBox.No,QMessageBox.Yes)
                    if ans==QMessageBox.Yes:
                        self.read_count_record()
                        self.sampleImgCounterLabel.setText(str(self.sampleCounter))
                        self.experimentLogHandle.write('##Sample folder added/accessed %s\n'%self.sampleFolder)
                    else:
                        self.sampleImgCounterLabel.setText('1')
                        self.sampleNameLineEdit.clear()
                else:
                    os.makedirs(self.sampleFolder)
                    self.experimentLogHandle.write('##Sample folder added/accessed %s\n'%self.sampleFolder)
                    self.sampleCounter=1
                    self.sampleImgCounterLabel.setText('1')
                    self.update_counter_record()
                for icount in range(self.detectorListWidget.count()):
                    detname=str(self.detectorListWidget.item(icount).text())
                    self.detectorFolders[detname]=os.path.join(self.sampleFolder,detname.lower())                    
                    if not os.path.exists(self.detectorFolders[detname]):
                        os.makedirs(self.detectorFolders[detname])
            else:
                QMessageBox.warning(self,'Name error', 'Please provide a sample name before starting data collection.',QMessageBox.Ok)
        else:
            self.sampleNameLineEdit.clear()
            QMessageBox.warning(self,'Experimental settings warning','Please start a new experiment and add a detector for SAXS/ASAXS measurement',QMessageBox.Ok)
            
    def update_counter_record(self):
        """
        Updates the .counter_record file
        """
        fh=open(os.path.join(self.sampleFolder,'.count_record'),'w')
        fh.write(str(self.sampleCounter))
        fh.close()
        
    def read_count_record(self):
        """
        Reads .counter_record file if it exists or create a new one 
        """
        try:
            fh=open(os.path.join(self.sampleFolder,'.count_record'),'r')
            self.sampleCounter=int(fh.readline())
        except:
            fh=open(os.path.join(self.sampleFolder,'.count_record'),'w')
            fh.write('1')
            self.sampleCounter=1
        
        
    def collect_transmission(self):
        """
        Collects the transmission data i.e Monitor and Photodiode counts just after the sample
        """
        #self.bringPDIn()
        #self.palette.setColor(QPalette.Foreground,Qt.red)
        #self.instrumentStatus.setPalette(self.palette)
        self.instrumentStatus.setText('<font color="Red">Collecting transmission data! Please wait...</font>')
        caput(self.scalers['15IDD_scaler_count_time']['PV'], self.expTime)
        #caput('pd_state',1)
        #QtTest.QTest.qWait(1000)
        #self.shutter_ON()
        #QtTest.QTest.qWait(1000)
        #caput(self.scalers['15IDD_scaler_start']['PV'],1,wait=False) #Starts counting.
        #while caget(self.scalers['15IDD_scaler_start']['PV'])!=0:
        #    pg.QtGui.QApplication.processEvents()
        #self.shutter_OFF()
        self.direct_diode_counts=caget(self.scalers['monitor_diode']['PV'])
        self.direct_monitor_counts = caget(self.scalers['monitor']['PV'])

        caput('pd_state', 1)
        QtTest.QTest.qWait(1000)
        self.shutter_ON()
        QtTest.QTest.qWait(1000)
        caput(self.scalers['15IDD_scaler_start']['PV'], 1, wait=False)  # Starts counting.
        while caget(self.scalers['15IDD_scaler_start']['PV']) != 0:
            pg.QtGui.QApplication.processEvents()
        self.shutter_OFF()
        caput('pd_state',0)
        QtTest.QTest.qWait(1000)

        self.trans_diode_counts = caget(self.scalers['trans_diode']['PV'])
        self.trans_monitor_counts = caget(self.scalers['monitor']['PV'])
        self.transmission_value=(
                self.trans_diode_counts/self.trans_monitor_counts)#/(
        # self.direct_diode_counts/self.direct_monitor_counts)
        self.PDTransmissionLabel.setText('%.5f'%self.transmission_value)
        #self.palette.setColor(QPalette.Foreground,Qt.green)
        #self.instrumentStatus.setPalette(self.palette)
        self.instrumentStatus.setText('<font color="Green">Done</font>')
        pg.QtGui.QApplication.processEvents()
        
        
        
    def collect_dark(self):
        """
        Collects dark images for the corresponding count_time of the sample
        """
        self.darkImage=True
        self.collect_data()
        self.darkImage=False
        
           
    def collect_data(self):
        """
        Collects data using 2D Detector for the sample
        """
        if str(self.sampleNameLineEdit.text())=='':
            QMessageBox.warning(self,'Sample Name missing', 'Please provide a sample name before doing data collection',QMessageBox.Ok)
        else:
            self.pre_count()
            self.count_em()
            self.post_count()
            
    def static_collect(self):
        """
        Collects SAXS data depending upon the settings also collects dark current and transmission using photodiode near the sample
        """
        if self.autoShutterCheckBox.checkState()>0:
            self.shutter_OFF()
        #try:
        self.frameCount=int(self.frameCountLineEdit.text())
        self.sleepTime=float(self.sleepTimeLineEdit.text())
        if str(self.staticCollectButton.text())!='Abort':
            self.abort=False
            self.staticCollectButton.setText('Abort')
            self.measurementProgressDialog.setMinimum(0)
            self.measurementProgressDialog.setMaximum(self.frameCount)
            self.measurementProgressDialog.setValue(0)
            if self.collectDarkCheckBox.isChecked():
                #caput('15PIL3:cam1:FileNumber', 1)
                #caput('15PIL3:cam1:AutoIncrement', 1)
                self.collect_dark()
            for i in range(self.frameCount):
                if self.abort:
                    break
                self.collect_data()
                if self.autoReduceCheckBox.isChecked():
                    self.redServerSocket.send_string(self.serverFileOut)

                if self.sleepTime>1e-3:
                    #self.palette.setColor(QPalette.Foreground,Qt.red)
                    #self.instrumentStatus.setPalette(self.palette)
                    caput(self.scalers['15IDD_scaler_mode']['PV'], 1, wait=True)
                    self.instrumentStatus.setText('<font color="Red">Sleeping for %s s. Please wait...</font>'%self.sleepTime)
                    QtTest.QTest.qWait(self.sleepTime*1000)
                    caput(self.scalers['15IDD_scaler_mode']['PV'], 0, wait=True)

                self.measurementProgressDialog.setValue(i+1)
            #caput('15PIL3:cam1:FileNumber', 1)
            #caput('15PIL3:cam1:AutoIncrement', 0)
            #self.palette.setColor(QPalette.Foreground,Qt.green)
            #self.instrumentStatus.setPalette(self.palette)
            self.instrumentStatus.setText('<font color="Green">Done</font>')
            self.staticCollectButton.setText('Collect Static')
        else:
            ans=QMessageBox.question(self,'Abort','Do you really like to abort the measurement',QMessageBox.Yes,QMessageBox.No)
            if ans==QMessageBox.Yes:
                self.abort=True
        #except:
        #    QMessageBox.warning(self,'Value Error','Please provide integer frame counts and floating point number
        # sleep time',QMessageBox.Ok)
        caput(self.scalers['15IDD_scaler_mode']['PV'],1,wait=True) #Setting Scalar to Autocount mode
            
    def dynamic_collect(self):
        """
        Collects SAXS with changing PV of either motors or some beamline parameters
        """
        try:
            self.openPositionerFile(fname=self.positionerFile)
        except:
            QMessageBox.warning(self,'Positioner File Error','Either you have not opened a positioner file or '
                                                             'positioner file has some errors.',
                                QMessageBox.Ok)
            return
        if caget('15IDA:KohzuModeBO.VAL')!=1:
            QMessageBox.warning(self,'Monochromator Warning','It seems monochomator is not in Auto mode. Please change the Monochromator to Auto mode before starting data collection', QMessageBox.Ok)
            return
        if caget('15IDA:KohzuUseSetBO.VAL')!=0:
            QMessageBox.warning(self,'Monochromator Warning','It seems monochomator is not in Use mode. Please change the Monochormator to Use mode before starting data collection', QMessageBox.Ok)
            return
        MonoBacklashReversed=False
        self.create_measurementList()
        if self.autoShutterCheckBox.checkState()>0:
            self.shutter_OFF()
        self.NLoops=self.loopSpinBox.value()
        # try:
        self.frameCount=int(self.frameCountLineEdit.text())
        self.sleepTime=float(self.sleepTimeLineEdit.text())
        self.loopSleepTime=float(self.loopSleepTimeLineEdit.text())
        if str(self.dynamicCollectButton.text())!='Abort':
            self.abort=False
            self.create_measurementList()
            for key in self.measurementList.keys():
                print(key, len(self.measurementList[key]))
                print(self.measurementList[key])
            ans=QMessageBox.question(self,'Measurement Information','Total number of measurements to be done: '
                                                                    '%d\n Do you want to continue?'%(
                    self.measurementCount*self.NLoops*self.frameCount),QMessageBox.Yes,QMessageBox.No)
            if ans==QMessageBox.Yes:
                limitsOK=self.check_motorLimits()
                if limitsOK:
                    self.dynamicCollectButton.setText('Abort')
                    self.measurementProgressDialog.setMinimum(0)
                    self.measurementProgressDialog.setMaximum(self.measurementCount*self.NLoops*self.frameCount)
                    self.measurementProgressDialog.setValue(0)
                    firstPosition={}
                    # Recording the intial starting positions of all the motors involved in the Dynamic scan
                    for motorname in self.measurementList.keys():

                        if motorname=='Energy':
                            self.energyWidget.track_undulator()
                            firstPosition[motorname]=caget(self.motors[motorname]['PV']+'RdbkAO')
                            first_det_thresh={}
                            first_det_energy={}
                            thresh_diff={}
                            for detname in self.usedDetectors:
                                first_det_energy[detname]=caget(self.detectors[detname]['PV']+'Energy')
                                first_det_thresh[detname]=caget(self.detectors[detname]['PV']+'ThresholdEnergy')
                                thresh_diff[detname]=firstPosition[motorname]-first_det_thresh[detname]
                        elif motorname=='Undulator_ID15Energy':
                            firstPosition[motorname]=caget(self.motors['Undulator_Energy']['PV'])
                        else:
                            firstPosition[motorname]=caget(self.motors[motorname]['PV']+'.RBV')

                    for loop in range(self.NLoops):
                        if self.abort:
                            break
                        for i in range(self.measurementCount):
                            if self.abort:
                                break
                            for motorname in self.measurementList.keys():
                                if motorname=='Energy':
                                    if caget(self.motors[motorname]['PV']+'RdbkAO')>self.measurementList[motorname][
                                        i] and caget('15IDA:m10.UEIP')==0:
                                        caput('15IDA:m10.BDST',-0.1,wait=True)
                                        MonoBacklashReversed=True
                                    if round(abs(caget(self.motors[motorname]['PV']+'RdbkAO')-self.measurementList[
                                        motorname][i]),4)>1e-4:
                                        self.energyWidget.feedback_OFF()
                                        caput(self.motors[motorname]['PV']+'AO.VAL',self.measurementList[motorname][
                                            i],wait=True)
                                        self.energyWidget.feedback_ON()
                                        for iwait in range(600):
                                            if self.abort:
                                                break
                                            self.instrumentStatus.setText(
                                                '<font color="Red">Waiting for the feedback to stabilize. Please '
                                                'wait for %d sec</font>' % ((60000 - iwait * 100) / 1000))
                                            QtTest.QTest.qWait(100)
                                    if MonoBacklashReversed:
                                        caput('15IDA:m10.BDST',0.1,wait=True)

                                    for detname in self.usedDetectors:
                                        if round(self.measurementList[motorname][i],3) != caget(self.detectors[
                                                                                           detname][
                                                                                           'PV']+'Energy_RBV'):
                                            self.instrumentStatus.setText(
                                                '<font color="Red">Setting the Energy and Threshhold of Pilatus 300K. '
                                                'Please '
                                                'wait...</font>')

                                            caput(self.detectors[detname]['PV']+'Energy',round(self.measurementList[
                                                motorname][i],3),wait=False) #Changing the energy of the detectors
                                            caput(self.detectors[detname]['PV']+'ThresholdEnergy',\
                                                              round(self.measurementList[motorname][
                                                i]-thresh_diff[detname],3),wait=False) #Changing the threshold energy of
                                        # the detectors
                                elif motorname=='Undulator_ID15Energy':
                                    caput(self.motors[motorname]['PV'],self.measurementList[motorname][i],wait=False)
                                else:
                                    caput(self.motors[motorname]['PV']+'.VAL',self.measurementList[motorname][i],wait=False)
                            QtTest.QTest.qWait(100)
                            moving=self.checkMotorsMoving()

                            #Checking the movement of all the motors
                            QtTest.QTest.qWait(10)
                            while moving:
                                if self.abort:
                                    break
                                #self.palette.setColor(QPalette.Foreground,Qt.red)
                                #self.instrumentStatus.setPalette(self.palette)
                                self.instrumentStatus.setText('<font color="Red">Motors are moving for the next position. Please wait...</font>')
                                moving=self.checkMotorsMoving()

                                QtTest.QTest.qWait(10)
                            #Counting starts
                            if self.collectDarkCheckBox.isChecked():
                                #caput('15PIL3:cam1:FileNumber',1)
                                #caput('15PIL3:cam1:AutoIncrement',1)
                                self.collect_dark()
                            for j in range(self.frameCount):
                                if self.abort:
                                    break
                                self.collect_data()
                                if self.autoReduceCheckBox.isChecked():
                                    self.redServerSocket.send_string(self.serverFileOut)
                                if self.sleepTime>1e-3:
                                    caput(self.scalers['15IDD_scaler_mode']['PV'], 1, wait=True)
                                    self.instrumentStatus.setText('Sleeping for %s s. Please wait...'%self.sleepTime)
                                    QtTest.QTest.qWait(self.sleepTime*1000)
                                    caput(self.scalers['15IDD_scaler_mode']['PV'], 0, wait=True)
                                self.measurementProgressDialog.setValue(loop*self.measurementCount*self.frameCount+self.frameCount*i+j+1)
                        if self.loopSleepTime>1e-3:
                            caput(self.scalers['15IDD_scaler_mode']['PV'], 1, wait=True)
                            self.instrumentStatus.setText('Sleeping for %s s. Please wait...'%self.loopSleepTime)
                            QtTest.QTest.qWait(self.loopSleepTime*1000)
                            caput(self.scalers['15IDD_scaler_mode']['PV'], 0, wait=True)
                        #caput('15PIL3:cam1:FileNumber', 1)
                        #caput('15PIL3:cam1:AutoIncrement', 0)

                    #Moving back the motors to the staring position

                    for motorname in self.measurementList.keys():
                        if motorname=='Energy':
                            caput(self.motors[motorname]['PV']+'AO.VAL',firstPosition[motorname],wait=False)
                            for detname in self.usedDetectors:
                                caput(self.detectors[detname]['PV'] + 'Energy', round(first_det_energy[detname], 3),
                                      wait=False) #Changing the energy of the detectors back to the starting point
                                caput(self.detectors[detname]['PV'] + 'ThresholdEnergy', \
                                      round(first_det_thresh[detname], 3),
                                      wait=False)  # Changing the threshold energy of the detectors back to the starting
                                # point


                        elif motorname=='Undulator_ID15Energy':
                            caput(self.motors[motorname]['PV'],firstPosition[motorname],wait=False)
                        else:
                            caput(self.motors[motorname]['PV']+'.VAL',firstPosition[motorname],wait=False)
                    QtTest.QTest.qWait(100)
                    moving=self.checkMotorsMoving()

                    while moving:
                        #self.palette.setColor(QPalette.Foreground,Qt.red)
                        #self.instrumentStatus.setPalette(self.palette)
                        self.instrumentStatus.setText('<font color="Red">Motors are moving back to the starting position. Please wait...</font>')
                        moving=self.checkMotorsMoving()

                        QtTest.QTest.qWait(10)
                    #self.palette.setColor(QPalette.Foreground,Qt.green)
                    #self.instrumentStatus.setPalette(self.palette)
                    self.measurementProgressDialog.setValue(self.measurementCount*self.NLoops*self.frameCount)
                    self.instrumentStatus.setText('<font color="Green">Done</font>')
                    self.dynamicCollectButton.setText('Collect Dynamic')
                    if motorname=='Energy':
                        self.energyWidget.untrack_undulator()
                else:
                    QMessageBox.warning(self,'Limit error', 'The motor positions supplied for measurements are beyond the limits. Please review your positioner values.',QMessageBox.Ok)
        else:
            ans=QMessageBox.question(self,'Abort','Do you really like to abort the measurement',QMessageBox.Yes,QMessageBox.No)
            if ans==QMessageBox.Yes:
                self.abort=True
        # except:
        #     QMessageBox.warning(self,'Positioner File Error','Please load a Positioner file first.',QMessageBox.Ok)
        caput(self.scalers['15IDD_scaler_mode']['PV'],1,wait=True) #Setting Scalar to Autocount mode
                
        
    def checkMotorsMoving(self):
        """
        Returns true if any of the motors in the measurement list is moving and returns False if all the motrs are static
        """
        result=[]
        for motorname in self.measurementList.keys():
            if motorname !='Energy' and motorname !='Undulator_ID15Energy':
                result.append(caget(self.motors[motorname]['PV']+'.DMOV'))
        if self.energyWidget.undulatorChanging:
            result.append(0)
        # if self.monochromatorStatus=='<font color="Red">Moving</font>':
        #     result.append(0)
        # else:
        #     result.append(1)
        # if self.undulatorStatus=='<font color="Red">Moving</font>':
        #     result.append(0)
        # else:
        #     result.append(1)
        return not all(result)
        
        
    def bringPDIn(self):
        """
        Brings the photodiode into the beam for transmission measurements
        """
        self.pdInPosition=float(self.pdInPositionLineEdit.text())
        #if not self.pdIn:
        #self.palette.setColor(QPalette.Foreground,Qt.red)
        #self.instrumentStatus.setPalette(self.palette)
        self.instrumentStatus.setText('<font color="Red">Bringing photodiode in. Please wait...</font>')
        #print('I m here')
        caput(self.motors['cmir']['PV'],self.pdInPosition,wait=False)           
        while caget(self.motors['cmir']['PV']+'.DMOV')==0:
            pg.QtGui.QApplication.processEvents()           
        #self.palette.setColor(QPalette.Foreground,Qt.green)
        self.instrumentStatus.setText('<font color="Green">Done</font>')
        #self.instrumentStatus.setPalette(self.palette)

        
    def bringBeamIn(self):
        """
        Brings the photodiode into the beam for transmission measurements
        """
        self.beamInPosition=float(self.beamInPositionLineEdit.text())
        #self.palette.setColor(QPalette.Foreground,Qt.red)
        #self.instrumentStatus.setPalette(self.palette)
        self.instrumentStatus.setText('<font color="Red">Bringing beam in. Please wait...</font>')
        caput(self.motors['cmir']['PV'],self.beamInPosition,wait=False)
        while caget(self.motors['cmir']['PV']+'.DMOV')==0:
            pg.QtGui.QApplication.processEvents()
        #self.palette.setColor(QPalette.Foreground,Qt.green)
        self.instrumentStatus.setText('<font color="Green">Done</font>')       
        #self.instrumentStatus.setPalette(self.palette)
            
    def bringMirrorIn(self):
        """
        Brings the mirror in to view sample from within the scattering tube.
        """
        self.mirrorInPosition=float(self.mirrorInPositionLineEdit.text())
        #if not self.mirrorIn:
        #self.palette.setColor(QPalette.Foreground,Qt.red)
        #self.instrumentStatus.setPalette(self.palette)
        self.instrumentStatus.setText('<font color="Red">Bringing Mirror in. Please wait...</font>')
        caput(self.motors['cmir']['PV'],self.mirrorInPosition,wait=False)
        while caget(self.motors['cmir']['PV']+'.DMOV')==0:
           pg.QtGui.QApplication.processEvents()            
        #self.palette.setColor(QPalette.Foreground,Qt.green)
        self.instrumentStatus.setText('<font color="Green">Done</font>')       
        #self.instrumentStatus.setPalette(self.palette)

    def pre_count(self):
        """
        Do all the necessary settings before counting like:
            1) Setting up the count_time for all the detectors and scalars
            2) Collecting transmission if collectTransmissionCheckBox is checked
        """
        camonitor(self.scalers['15IDC_scaler_start']['PV'], callback=self.changeCountingState_15IDC)
        camonitor(self.scalers['15IDD_scaler_start']['PV'], callback=self.changeCountingState_15IDD)
        #self.palette.setColor(QPalette.Foreground,Qt.red)
        #self.instrumentStatus.setPalette(self.palette)
        try:
            shutterTime=float(self.shutterTimeLineEdit.text())
        except:
            shutterTime=0.0
            QMessageBox.warning(self,'Value error','Please check the shutter time. It should be a floating point number.',QMessageBox.Ok)
        self.instrumentStatus.setText('<font color="Red">Counting. Please wait...</font>')
        caput(self.scalers['15IDC_scaler_mode']['PV'], 0, wait=True) #Setting the counter to one-shot mode
        caput(self.scalers['15IDD_scaler_mode']['PV'], 0, wait=True) #Setting the counter to one-shot mode
        caput(self.scalers['15IDC_scaler_count_time']['PV'], self.expTime, wait=True)
        caput(self.scalers['15IDD_scaler_count_time']['PV'], self.expTime, wait=True)
        for detname in self.usedDetectors:
            caput(self.detectors[detname]['PV']+'AcquireTime', self.expTime, wait=True)
            caput(self.detectors[detname]['PV'] +'AcquirePeriod', self.expTime + 0.1, wait=True)
            self.detectorWidgets[detname].imageFlag=0
        if self.collectTransmissionCheckBox.isChecked() and not self.darkImage:
            #self.bringPDIn()
            self.collect_transmission()
            #self.bringBeamIn()
        else:
            #self.bringBeamIn()
            self.direct_diode_counts=1.0
            self.direct_monitor_counts=1.0
            self.trans_diode_counts=1.0
            self.trans_monitor_counts=1.0
            self.transmission_value=1.0

            
    def shutter_ON(self):
        """
        Put the shutter ON
        """
        caput(self.motors['shutter']['PV'],0)
        shutterTime = float(self.shutterTimeLineEdit.text())
        QtTest.QTest.qWait(shutterTime * 1000)  # waiting for 0.3 seconds to open the shutter
        
    def shutter_OFF(self):
        """
        Put the shutter OFF
        """
        caput(self.motors['shutter']['PV'],1)
            
        
    def count_em(self):
        """
        Triggers all the detectors and scalers for counting
        """
        if self.autoShutterCheckBox.checkState()>0:
            if not self.darkImage:
                self.shutter_ON()
            else:
                self.shutter_OFF()
        for detname in self.usedDetectors:
            self.detectorWidgets[detname].detStatus=1
            #self.detectorWidgets[detname].detState='Busy'
        #self.palette.setColor(QPalette.Foreground,Qt.red)
        #self.instrumentStatus.setPalette(self.palette)
        if self.darkImage:
            self.instrumentStatus.setText('<font color="Red">Collecting dark images from all the Area Detectors. Please wait...</font>')
        else:
            self.instrumentStatus.setText('<font color="Red">Collecting data from all the Area Detectors. Please wait...</font>')
        #self.counting=Truecamonitor(self.scalers['15IDD_scaler_start']['PV']
        stime=time.time()
        for detname in self.usedDetectors:
            caput(self.detectors[detname]['PV'] + 'Acquire', 1)
        caput(self.scalers['15IDD_scaler_start']['PV'], 1)
        caput(self.scalers['15IDC_scaler_start']['PV'], 1)
        self.counting = True
        QtTest.QTest.qWait(10)
        while self.counting:
            if self.abort:
                break
            timeElapsed = time.time() - stime
            for detname in self.usedDetectors:
                self.detectorWidgets[detname].timeElapsedLabel.setText('%.3f' % timeElapsed)
            pg.QtGui.QApplication.processEvents()
            QtTest.QTest.qWait(10)
        if self.autoShutterCheckBox.checkState()>0:
            self.shutter_OFF()
        QtTest.QTest.qWait(10)
        while any([self.detectorWidgets[detname].imageFlag==0 for detname in self.usedDetectors]):
            if self.abort:
                break
            #while any([self.detectorWidgets[detname].detState!='Idle' for detname in self.usedDetectors]):
            #    if self.abort:
            #        break
            timeElapsed = time.time() - stime
            for detname in self.usedDetectors:
                self.detectorWidgets[detname].timeElapsedLabel.setText('%.3f' % timeElapsed)
            pg.QtGui.QApplication.processEvents()
            QtTest.QTest.qWait(10)
        self.counting=False
        #self.palette.setColor(QPalette.Foreground,Qt.green)
        #self.instrumentStatus.setPalette(self.palette)
        self.instrumentStatus.setText('<font color="Green">Counting Finished</font>')      
        
        
    def changeCountingState_15IDC(self,**kwargs):
        """
        Updates the counting state
        """
        value=kwargs['value']
        if value!=0:
            self.counting=True or self.counting
        else:
            self.counting=False
        #print(self.counting)

    def changeCountingState_15IDD(self,**kwargs):
        """
        Updates the counting state
        """
        value=kwargs['value']
        if value!=0:
            self.counting=True or self.counting
        else:
            self.counting=False
        
        
    def post_count(self):
        """
        Do all the necessary steps afer the counting is over i.e
            1) Calculates the transmission
            2) Reads the images and put all the necessary information together to generate an EDF file to store in correct locations
            3) Advance the image counter by 1
        """
        camonitor_clear(self.scalers['15IDC_scaler_start']['PV'])
        camonitor_clear(self.scalers['15IDD_scaler_start']['PV'])
        #self.palette.setColor(QPalette.Foreground,Qt.red)
        #self.instrumentStatus.setPalette(self.palette)
        for detname in self.usedDetectors:
            #if detname=='PhotonII':
            #    imgFile=caget('13PII_1:TIFF1:FullFileName_RBV',as_string=True)
            #else:
            #    imgFile=caget(self.detectors[detname]['PV'].split(':')[0]+':TIFF1:FullFileName_RBV',as_string=True)
            if self.darkImage:
                self.serverFileOut=os.path.join(self.detectorFolders[detname],'%s_%04d_dark.edf'%(self.sampleName,self.sampleCounter))
#                self.dataReducer.darkFile=fileout
#                self.dataReducer.darkFileLineEdit.setText(fileout)
            else:
                self.serverFileOut=os.path.join(self.detectorFolders[detname],'%s_%04d.edf'%(self.sampleName,self.sampleCounter))
#                self.dataReducer.dataFiles=[fileout]
#                self.dataReducer.dataFileLineEdit.setText('[\''+fileout+'\']')
#            self.dataReducer.extractedFolder=os.path.join(self.detectorFolders[detname],'extracted_pyFAI')
#            if not os.path.exists(self.dataReducer.extractedFolder):
#                os.makedirs(self.dataReducer.extractedFolder)
#            self.dataReducer.extractedFolderLineEdit.setText(self.dataReducer.extractedFolder)
            self.instrumentStatus.setText('<font color="Red">Saving file</font>')
            #cars_imgFile=imgFile.replace(self.detectors[detname]['det_folder'],self.detectors[detname]['cars_folder'])
            cars_imgFile=self.serverFileOut
            #print(cars_imgFile)
            #QtTest.QTest.qWait(2*1000)
            #img=fb.open(cars_imgFile)
            file=fb.edfimage.EdfImage(data=None)
            #file.data=img.data
            file.data=self.detectorWidgets[detname].imgData
            #file.header=img.header
            #file.data=random.random((100,100))
            self.monB_counts = caget(self.scalers['monitorB']['PV'])
            self.monitor_counts = caget(self.scalers['monitor']['PV'])
            self.count_time = caget(self.scalers['15IDD_scaler_count_time']['PV'])
            self.BSdiode_counts = caget(self.scalers['bs_diode']['PV'])
            if self.darkImage:
                self.direct_diode_counts = caget(self.scalers['monitor_diode']['PV'])
                self.direct_monitor_counts = caget(self.scalers['monitor']['PV'])
                self.trans_diode_counts = caget(self.scalers['trans_diode']['PV'])
                self.trans_monitor_counts = caget(self.scalers['monitor']['PV'])
                self.transmission_value=1.0
            file.header['Time'] = time.time()
            file.header['MonB'] = self.monB_counts
            file.header['MonB_Sens']=caget('15IDB:A1sens_num.VAL',as_string=True)+' '+caget(
                '15IDB:A1sens_unit.VAL',as_string=True)
            file.header['Monitor'] = self.monitor_counts#1000#caget(self.scalers['Monitor']['PV'])
            file.header['Monitor_Sens']=caget('15IDD:ionch:sens_num.VAL',as_string=True)+' '+caget(
                '15IDD:ionch:sens_unit.VAL',as_string=True)
            file.header['count_time'] = self.count_time#1.0#caget(self.scalers['count_time']['PV'])
            file.header['BSDiode'] = self.BSdiode_counts#300#caget(self.scalers['BSDiode']['PV'])
            file.header['BSDiode_Sens']=caget('15IDD:bpm1:sens_num.VAL',as_string=True)+' '+caget(
                '15IDD:bpm1:sens_unit.VAL',as_string=True)
            file.header['directDiode'] = self.direct_diode_counts
            file.header['directMonitor'] = self.direct_monitor_counts
            file.header['transDiode'] = self.trans_diode_counts
            file.header['transDiode_Sens']=caget('15IDD:bpm3:sens_num.VAL',as_string=True)+' '+caget(
                '15IDD:bpm3:sens_unit.VAL',as_string=True)
            file.header['transMonitor'] = self.trans_monitor_counts
            file.header['transMonitor_Sens'] = caget('15IDD:bpm2:sens_num.VAL', as_string=True) + ' ' + caget(
                '15IDD:bpm2:sens_unit.VAL', as_string=True)
            file.header['Transmission'] = self.transmission_value
            file.header['xcradle'] = 0.0
            file.header['Temperature']=caget(self.scalers['monitor_diode']['PV'])*1.414e-4/self.count_time+20.402
            for key in self.motors.keys():
                if key != 'Energy' and key != 'Undulator_ID15Energy' and key != 'Undulator_Energy':
                    file.header[key]=caget(self.motors[key]['PV']+'.RBV')
            file.header['Wavelength']=self.wavelength
            self.energy = caget(self.BLParams['Energy']['PV'] + 'RdbkAO')
            file.header['Energy']=self.energy
            #file.header['UndulatorEnergy']=self.energyWidget.undulatorEnergyLabel.pv.value
            file.write(self.serverFileOut)
            self.BSTransmissionLabel.setText('%.5f'%(self.BSdiode_counts/self.monitor_counts))
        #self.palette.setColor(QPalette.Foreground,Qt.green)
        #self.instrumentStatus.setPalette(self.palette)
        self.instrumentStatus.setText('<font color="Green">Done</file>')
        if not self.darkImage:
            self.sampleCounter+=1
            self.update_counter_record()        
            self.sampleImgCounterLabel.setText(str(self.sampleCounter))
        if self.autoPumpCheckBox.isChecked() and not self.darkImage:
            caput('15IDD:PHDUltra:TargetVolume',float(self.pumpVolLineEdit.text()))
            caput('15IDD:PHDUltra:Infuse',1)
            self.palette.setColor(QPalette.Foreground,Qt.red)
            self.instrumentStatus.setPalette(self.palette)
            t1=time.time()
            QtTest.QTest.qWait(5*1000)
            while caget('15IDD:PHDUltra:PumpState',as_string=True)!='Idle':
                self.instrumentStatus.setText('<font color="Red">Pumping new solution for next frame. Please wait...</font>')
                QtTest.QTest.qWait(10)
            t2=time.time()
            print(t2-t1)
            caput("15IDD:PHDUltra:ClearVolume",0)
            caput("15IDD:PHDUltra:Infuse",0)
            #self.palette.setColor(QPalette.Foreground,Qt.red)
            #self.instrumentStatus.setPalette(self.palette)
            self.instrumentStatus.setText('<font color="Green">Done</font>')
            
            
        
        
        
if __name__=='__main__':
    app=QApplication(sys.argv)
    w=XAnoS_Collector()
    w.setWindowTitle('XAnoS_Collector')
    w.setGeometry(0,0,800,800)
    
    w.show()
    sys.exit(app.exec_())
    

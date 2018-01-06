import pyqtgraph as pg
from epics import caget, caput, camonitor, camonitor_clear
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QLabel, QTableWidget, QListWidget, QCheckBox, QComboBox, QLineEdit, QPushButton, QMessageBox, QFileDialog,QAbstractItemView
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QSizePolicy
from PyQt5 import QtTest
from pyqtgraph.dockarea import DockArea, Dock
import numpy as np
from PlotWidget import PlotWidget
from Setup import Setup
import os
import sys
import time
import copy

class Scanner(QWidget):
    sigMotorMoving=pyqtSignal(int) #Signal to detect motor is moving
    
    def __init__(self, scanFolder, parent=None):
        """
        Scanning Epics motor
        scanFolder is the Folder where it will store all the scans which will be numbered automatically
        """
        QWidget.__init__(self,parent)
        self.cwd=os.getcwd()
        self.setup=Setup(os.path.join(self.cwd,'SetupData'))
        self.detectors=self.setup.detectors
        self.motors=self.setup.motors
        self.scalers=self.setup.scalers
        self.BLParams=self.setup.BLParams
        self.slitParams=self.setup.slitParams
        
        
        self.vblayout=QVBoxLayout(self)
        self.mainDock=DockArea(self,parent)
        self.vblayout.addWidget(self.mainDock)
        
        self.scanParamDock=Dock('Scan Parameters',size=(5,1))
        self.scanListDock=Dock('Scan list',size=(1,9))
        self.scanPlotDock=Dock('Scan Plots',size=(3,9))
        self.detectorListDock=Dock('Detectors',size=(1,9))
        self.mainDock.addDock(self.scanParamDock,'top')
        self.mainDock.addDock(self.scanListDock,'bottom',self.scanParamDock)
        self.mainDock.addDock(self.scanPlotDock,'right',self.scanListDock)
        self.mainDock.addDock(self.detectorListDock,'right',self.scanPlotDock)
        
        
        self.createScanParamDock()
        self.createScanListDock()
        self.createScanPlotDock()
        self.changeScanFolder(scanFolder)
        self.createDetectorListDock()
        self.detectorListWidgetChanged()
        
    def changeScanFolder(self,scanFolder=None):
        """
        Changes the scan folder to the specified scanFolder
        """
        self.scans={}
        self.scanListWidget.clear()
        if scanFolder is None:
            self.scanFolder=str(QFileDialog.getExistingDirectory(self,caption='Open scan folder',directory=os.getcwd()))
        else:
            self.scanFolder=scanFolder
        if os.path.exists(self.scanFolder):
            self.read_scan_record()
            self.load_scans()
        else:
            self.scanNum=1
            self.update_scan_record()
        
        self.scanFolderLabel.setText('%s%100s'%(self.scanFolder,''))
        self.plotWidget.plotWidget.clear()
            
        
        
    def update_scan_record(self):
        """
        Create a hidden file named .scanRecord to keep track of the next scan number in the folder
        """
        fh=open(os.path.join(self.scanFolder,'.scanRecord'),'w')
        fh.write(str(self.scanNum))
        fh.close()
        
    def read_scan_record(self):
        """
        Updates the .scanRecord file with the next scan number
        """
        try:
            fh=open(os.path.join(self.scanFolder,'.scanRecord'),'r')
            self.scanNum=int(fh.readline())
            fh.close()
        except:
            self.scanNum=1
            self.update_scan_record()
        
        
    def createScanParamDock(self):
        """
        Creates the dock for reading scan parameters
        """
        self.scanParamLayout=pg.LayoutWidget()        
        row=0
        col=0
        scanNameLabel=QLabel('Scan')
        scanMotorLabel=QLabel('Motor')
        normDetectorLabel=QLabel('Normalized by')
        scanTypeLabel=QLabel('Scan type')
        motorPositionLabel=QLabel('Motor Pos')
        scanMinLabel=QLabel('Min')
        scanMaxLabel=QLabel('Max')
        scanStepsLabel=QLabel('Steps')
        scanTimeLabel=QLabel('Count-time(s)')
        sleepTimeLabel=QLabel('Sleep-time(s)')
        self.counterLabel=QLabel('%s'%' ')
        self.scanStatus=QLabel('%s'%'')
        self.scanParamLayout.addWidget(scanNameLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(scanMotorLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(normDetectorLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(scanTypeLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(self.counterLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(self.scanStatus,row=row,col=col,colspan=2)
        
        row+=1
        col=0
        self.scanNameComboBox=QComboBox()
        self.scanNameComboBox.addItems(['MotorScan','TimeScan','EnergyScan','SlitScan'])
        self.scanMotorComboBox=QComboBox()
        self.scanMotorComboBox.addItems(list(self.motors.keys()))
        self.scanMotorComboBox.setCurrentIndex(self.scanMotorComboBox.findText('d_x'))
        self.normDetectorComboBox=QComboBox()
        self.normDetectorComboBox.addItems(['none','monitor','diode','bs-diode'])
        self.normDetectorComboBox.currentIndexChanged.connect(self.normDetectorChanged)
        self.scanTypeComboBox=QComboBox()
        self.scanTypeComboBox.addItems(['Relative','Absolute'])
        self.scanMotorPos=caget(self.motors[str(self.scanMotorComboBox.currentText())]['PV']+'.RBV')
        self.scanMotorPositionLabel=QLabel(str(self.scanMotorPos))
        self.scanMinLineEdit=QLineEdit('-1.0')
        self.scanMaxLineEdit=QLineEdit('1.0')
        self.scanStepsLineEdit=QLineEdit('11')
        self.countTimeLineEdit=QLineEdit('1.0')
        self.sleepTimeLineEdit=QLineEdit('0.0')
        self.continuousScanCheckBox=QCheckBox('Continuous')
        self.continuousScanCheckBox.setTristate(False)
        self.shutterModeCheckBox=QCheckBox('Auto Shutter')        
        self.scanAbortPushButton=QPushButton('Scan')
        self.scanParamLayout.addWidget(self.scanNameComboBox,row=row,col=col)
        self.scanNameComboBox.currentIndexChanged.connect(self.scanNameChanged)
        col+=1
        self.scanParamLayout.addWidget(self.scanMotorComboBox,row=row,col=col)
        self.scanMotorComboBox.currentIndexChanged.connect(self.scanMotorChanged)
        col+=1
        self.scanParamLayout.addWidget(self.normDetectorComboBox,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(self.scanTypeComboBox,row=row,col=col)
        self.scanTypeComboBox.currentIndexChanged.connect(self.scanTypeChanged)
        col+=1
        self.scanParamLayout.addWidget(self.continuousScanCheckBox,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(self.shutterModeCheckBox,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(self.scanAbortPushButton,row=row,col=col)      
        self.scanAbortPushButton.clicked.connect(self.startAbortScan)
        
        
        row+=1        
        col=0
        self.scanParamLayout.addWidget(motorPositionLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(scanMinLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(scanMaxLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(scanStepsLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(scanTimeLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(sleepTimeLabel,row=row,col=col)
        col+=1
        
        row+=1
        col=0
        self.scanParamLayout.addWidget(self.scanMotorPositionLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(self.scanMinLineEdit,row=row,col=col)
        self.scanMinLineEdit.returnPressed.connect(self.scanMinChanged)
        col+=1
        self.scanParamLayout.addWidget(self.scanMaxLineEdit,row=row, col=col)
        self.scanMaxLineEdit.returnPressed.connect(self.scanMaxChanged)
        col+=1
        self.scanParamLayout.addWidget(self.scanStepsLineEdit,row=row,col=col)
        self.scanStepsLineEdit.returnPressed.connect(self.scanStepsChanged)
        col+=1
        self.scanParamLayout.addWidget(self.countTimeLineEdit,row=row,col=col)
        self.countTimeLineEdit.returnPressed.connect(self.countTimeChanged)
        col+=1
        self.scanParamLayout.addWidget(self.sleepTimeLineEdit,row=row,col=col)
        self.sleepTimeLineEdit.returnPressed.connect(self.sleepTimeChanged)
        
        
        self.scanParamDock.addWidget(self.scanParamLayout)
        
        self.scanNameChanged()
        self.scanMotorChanged()
        self.normDetectorChanged()
        self.scanTypeChanged()
        self.scanMinChanged()
        self.scanMaxChanged()
        self.scanStepsChanged()
        self.countTimeChanged()
        self.sleepTimeChanged()
        
        
        
    def scanNameChanged(self):
        self.scanName=str(self.scanNameComboBox.currentText())
        self.scanMotorComboBox.currentIndexChanged.disconnect(self.scanMotorChanged)
        self.scanMotorComboBox.clear()
        if self.scanName=='MotorScan':
            self.scanMotorComboBox.addItems(list(self.motors.keys()))
        elif self.scanName=='TimeScan':
            self.scanMotorComboBox.addItem('time')
            self.scanMotorPositionLabel.setText('0.0')
        elif self.scanName=='EnergyScan':
            self.scanMotorComboBox.addItem('Energy')
            self.scanMotorPositionLabel.setText('%0.4f'%(caget('15IDA:BraggERdbkA0')))
        elif self.scanName=='SlitScan':
            self.scanMotorComboBox.addItems(list(self.slitParams.keys()))
        self.scanMotorComboBox.currentIndexChanged.connect(self.scanMotorChanged)
        
        
    def scanMotorChanged(self):
        """
        The scanning motor is changed
        """
        try:
            camonitor_clear(self.oldMotorName)
        except:
            pass
        if self.scanName=='MotorScan':
            self.scanMotorName=str(self.scanMotorComboBox.currentText())
            self.scanMotorPos=caget(self.motors[self.scanMotorName]['PV']+'.RBV')
            self.scanMotorPositionLabel.setText('%3.5f'%self.scanMotorPos)
            camonitor(self.motors[str(self.scanMotorComboBox.currentText())]['PV']+'.RBV',callback=self.motorMoved)
            camonitor(self.motors[str(self.scanMotorComboBox.currentText())]['PV']+'.DMOV',callback=self.motorStatus)
            self.oldMotorName=copy.copy(self.scanMotorName)
        elif self.scanName=='SlitScan':
            pass
        
    def motorMoved(self,**kwargs):
        value=kwargs['value']
        self.scanMotorPositionLabel.setText('%3.5f'%value)
        
    def motorStatus(self,**kwargs):
        value=kwargs['value']
        if value!=1:
            self.scanStatus.setText('Moving')
        else:
            self.scanStatus.setText('Done')
        
        
    
    def normDetectorChanged(self):
        """
        The normalization detector changed
        """
        self.normDetector=str(self.normDetectorComboBox.currentText())
        
    def detectorListWidgetChanged(self):
        """
        The selection in the detectorListWidget Changed
        """
        self.scanDetectors=[item.text() for item in self.detectorListWidget.selectedItems()]
        
    def scanTypeChanged(self):
        """
        The scan type is changed
        """
        self.scanType=str(self.scanTypeComboBox.currentText())
        
    def scanMinChanged(self):
        """
        The scan Minimum changed
        """
        try:
            self.scanMin=float(self.scanMinLineEdit.text())
        except:
            QMessageBox.warning(self,'Value error','Please input decimal numbers only',QMessageBox.Ok)
            self.scanMin=-1.0
            self.scanMinLineEdit.setText(str(self.scanMin))
            
    def scanMaxChanged(self):
        """
        The scan Maximum changed
        """
        try:
            self.scanMax=float(self.scanMaxLineEdit.text())
        except:
            QMessageBox.warning(self,'Value error','Please input decimal numbers only',QMessageBox.Ok)
            self.scanMax=1.0
            self.scanMaxLineEdit.setText(str(self.scanMax))
            
    def scanStepsChanged(self):
        """
        The scan step is changed
        """
        try:
            self.scanSteps=int(self.scanStepsLineEdit.text())
        except:
            QMessageBox.warning(self,'Value error','Please input integers only',QMessageBox.Ok)
            self.scanStep=11
            self.scanStepLineEdit.setText(str(self.scanStep))
            
    def countTimeChanged(self):
        """
        The scan time is changed
        """
        try:
            self.countTime=float(self.countTimeLineEdit.text())
        except:
            QMessageBox.warning(self,'Value error','Please input decimal numbers only',QMessageBox.Ok)
            self.countTime=1.0
            self.countTimeLineEdit.setText(str(self.countTime))
            
    def sleepTimeChanged(self):
        """
        The sleep time is changed
        """
        try:
            self.sleepTime=float(self.sleepTimeLineEdit.text())
        except:
            QMessageBox.warning(self,'Value error','Please input decimal numbers only',QMessageBox.Ok)
            self.sleepTime=0.0
            self.sleetpTimeLineEdit.setText(str(self.sleepTime))
            
        
    def startAbortScan(self):
        """
        Start a scan or Abort a running scan
        """
        if self.scanAbortPushButton.text()=='Scan':
            self.abort=False
            self.motorStopped=False
            while self.continuousScanCheckBox.isChecked() and not self.motorStopped:
                self.scan()
                #time.sleep(5)
            else:
                if not self.motorStopped:
                    self.scan()
        else:
            self.abort=True
            if self.scanName=='MotorScan':
                caput(self.motors[self.scanMotorName]['PV']+'.SPMG',0)
            elif self.scanName=='SlitScan':
                caput(self.slitParams[self.scanMotorName]['MOV1']+'.SPMG',0)
                caput(self.slitParams[self.scanMotorName]['MOV2']+'.SPMG',0)
            self.scanAbortPushButton.setText('Scan')

        
    
    def createScanPlotDock(self):
        """
        Creates the dock for the visualization of scans
        """
        
        self.scanPlotLayout=pg.LayoutWidget(self)
        row=0
        col=0
        scanFolderLabel=QLabel('Scan Folder: ')
        self.scanFolderLabel=QLabel()
        self.scanFolderLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.scanFolderPushButton=QPushButton('Change Folder')
        self.scanPlotLayout.addWidget(scanFolderLabel,row=row,col=col)
        col+=1
        self.scanPlotLayout.addWidget(self.scanFolderLabel,row=row,col=col,colspan=2)
        col+=2
        self.scanPlotLayout.addWidget(self.scanFolderPushButton,row=row,col=col)
        
        
        row+=1
        col=0
        self.plotWidget=PlotWidget(self)
        self.plotWidget.plotWidget.getPlotItem().vb.scene().sigMouseClicked.connect(self.mouseClicked)
        
        self.scanPlotLayout.addWidget(self.plotWidget,row=row,col=col,rowspan=15,colspan=4)
        
        self.scanPlotDock.addWidget(self.scanPlotLayout)
        
        
    def createScanListDock(self):
        """
        """
        self.scanListLayout=pg.LayoutWidget(self)
        row=0
        col=0
        self.scanListWidget=QListWidget(self)
        self.scanListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.scanListWidget.itemSelectionChanged.connect(self.scanSelectionChanged)
        self.scanListLayout.addWidget(self.scanListWidget,row=row,col=col,rowspan=15)
        
        self.scanListDock.addWidget(self.scanListLayout)
        

    def createDetectorListDock(self):
        """
        """
        self.detectorListLayout=pg.LayoutWidget(self)
        row=0
        col=0
        self.detectorListWidget=QListWidget(self)
        self.detectorListWidget.addItems(['monitor','diode','bs-diode'])
        self.detectorListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.detectorListWidget.itemSelectionChanged.connect(self.detectorListWidgetChanged)
        self.detectorListWidget.item(0).setSelected(True)
        self.detectorListLayout.addWidget(self.detectorListWidget,row=row,col=col,rowspan=15)
        self.detectorListDock.addWidget(self.detectorListLayout)      
        
        
    def mouseClicked(self,evt):
        if evt.double():
            pointer=self.plotWidget.plotWidget.getPlotItem().vb.mapSceneToView(evt.scenePos())
            ans=QMessageBox.question(self,'Ask to move','Move '+self.scanMotorName+' to %.5f?'%pointer.x(),QMessageBox.No,QMessageBox.Yes)
            if ans==QMessageBox.Yes:
                caput(self.motors[self.scanMotorName]['PV']+'.VAL',pointer.x())
        
    def shutter_ON(self):
        """
        Put the shutter ON
        """
        caput(self.motors['shutter']['PV'],0)
        
    def shutter_OFF(self):
        """
        Put the shutter OFF
        """
        caput(self.motors['shutter']['PV'],1)    
            
    def load_scans(self):
        """
        Loads all the scans of the file in memory
        """
        for num in range(1,self.scanNum):
            self.scans[num]={}
            fh=open(os.path.join(self.scanFolder,'Scan%04d.dat'%num),'r')
            lines=fh.readlines()
            motorName=lines[0][:-1].split()[3]
            self.scans[num]['scanHeader']=lines[0][:-1]
            self.scans[num]['scanVariables']=lines[1].split()[1:]
            self.scans[num]['scanArray']=np.array([float(val) for val in lines[2].split()[1:]])
            for line in lines[3:]:
                try:
                    self.scans[num]['scanArray']=np.vstack((self.scans[num]['scanArray'],np.array([float(val) for val in line.split()[1:]])))
                except:
                    break
            self.scanListWidget.addItem('Scan %d: %s'%(num,motorName))
            
    def tscan(self,count_time,sleep_time):
        """
        Peform the time scan with the provided count_time and sleep_time:
        """
        caput(self.scalers['scaler_count_time']['PV'],count_time)
        t=time.time()
        self.data_num=0
        while True:
            if not self.abort:
                if self.shutterModeCheckBox.isChecked():
                    self.shutter_ON()
                caput(self.scalers['scaler_start']['PV'],1,wait=True)
                while str(self.scanStatus.text())=='Counting':
                    pg.QtGui.QApplication.processEvents()
                    QtTest.QTest.qWait(10)
                if self.shutterModeCheckBox.isChecked():
                    self.shutter_OFF()
                self.count_time=caget(self.scalers['scaler_count_time']['PV'])
                self.bs_diode_counts=caget(self.scalers['bs_diode']['PV'])
                self.diode_counts=caget(self.scalers['diode']['PV'])
                self.monitor_counts=caget(self.scalers['monitor']['PV'])
                t1=time.time()-t
                if 'scanArray' in self.scans[self.scanNum]:
                    self.scans[self.scanNum]['scanArray']=np.vstack((self.scans[self.scanNum]['scanArray'],np.array([t1,count_time,self.bs_diode_counts,self.diode_counts,self.monitor_counts])))
                else:
                    self.scans[self.scanNum]['scanArray']=np.array([[t1,count_time,self.bs_diode_counts,self.diode_counts,self.monitor_counts]])
                text='%d\t%.4f\t%.4f\t%d\t%d\t%d'%(self.data_num,t1,count_time,self.bs_diode_counts,self.diode_counts,self.monitor_counts)
                names=[]
                norm=1.0
                if self.normDetectorComboBox.currentText()!='none':
                    norm_num=self.scans[self.scanNum]['scanVariables'].index(self.normDetectorComboBox.currentText())
                    norm=self.scans[self.scanNum]['scanArray'][:,norm_num]
                for det in self.scanDetectors:
                    det_num=self.scans[self.scanNum]['scanVariables'].index(det)
                    names.append('%d-%s'%(self.scanNum,det))
                    self.plotWidget.add_data(self.scans[self.scanNum]['scanArray'][:,0],self.scans[self.scanNum]['scanArray'][:,det_num]/norm,name=names[-1])
                self.plotWidget.Plot(names)
                self.scanfh.write(text+'\n')
                print(text)
                self.counterLabel.setText('#%d'%self.data_num)
                self.data_num+=1
                
                #Sleeping
                if sleep_time>1e-3:
                    self.scanStatus.setText('Sleeping')
                    QtTest.QTest.qWait(1000*sleep_time)
                self.scanStatus.clear()
            else:
                try:
                    camonitor_clear(self.scalers['scaler_start']['PV'])
                except:
                    pass
                self.continuousScanCheckBox.setCheckState(Qt.Unchecked)
                self.scanfh.write('\n')
                self.scanfh.write('##Scan Aborted after %d points'%self.data_num)
                print('\n')
                print('##Scan Aborted after %d points'%self.data_num)
                self.motorStopped=True
                break
            pg.QtGui.QApplication.processEvents()
            
    def slitscan(self,motorname,start,finish,steps,count_time,sleep_time):
        """
        do absolute scan of the motor provided by motorname which starts with [start] and ends with [finish] positions with [steps] number of steps. The detector counts at each step for 1 second
        """        
        positions=np.linspace(start,finish,steps)
        caput(self.scalers['scaler_count_time']['PV'],count_time)   
        self.data_num=0
        for pos in positions:
            if not self.abort:
                caput(self.slitParams[motorname]['PV']+'.VAL',pos,wait=False)
                QtTest.QTest.qWait(10)
                while caget(self.slitParams[motorname]['MOV1']+'.MOVN')==1 or caget(self.slitParams[motorname]['MOV2']+'.MOVN')==1:
                    pg.QtGui.QApplication.processEvents()
                    QtTest.QTest.qWait(10)
                if self.shutterModeCheckBox.isChecked():
                    self.shutter_ON()
                self.scanStatus.setText('Counting')
                caput(self.scalers['scaler_start']['PV'],1,wait=False)
                QtTest.QTest.qWait(10)
                while str(self.scanStatus.text())=='Counting':
                    pg.QtGui.QApplication.processEvents()
                    QtTest.QTest.qWait(10)
                if self.shutterModeCheckBox.isChecked():
                    self.shutter_OFF()                    
                self.count_time=caget(self.scalers['scaler_count_time']['PV'])
                self.bs_diode_counts=caget(self.scalers['bs_diode']['PV'])
                self.diode_counts=caget(self.scalers['diode']['PV'])
                self.monitor_counts=caget(self.scalers['monitor']['PV'])
                if 'scanArray' in self.scans[self.scanNum]:
                    self.scans[self.scanNum]['scanArray']=np.vstack((self.scans[self.scanNum]['scanArray'],np.array([pos,count_time,self.bs_diode_counts,self.diode_counts,self.monitor_counts])))
                else:
                    self.scans[self.scanNum]['scanArray']=np.array([[pos,count_time,self.bs_diode_counts,self.diode_counts,self.monitor_counts]])
                text='%d\t%.4f\t%.4f\t%d\t%d\t%d'%(self.data_num, pos,count_time,self.bs_diode_counts,self.diode_counts,self.monitor_counts)
                names=[]
                norm=1.0
                if self.normDetectorComboBox.currentText()!='none':
                    norm_num=self.scans[self.scanNum]['scanVariables'].index(self.normDetectorComboBox.currentText())
                    norm=self.scans[self.scanNum]['scanArray'][:,norm_num]
                for det in self.scanDetectors:
                    det_num=self.scans[self.scanNum]['scanVariables'].index(det)
                    names.append('%d-%s'%(self.scanNum,det))
                    self.plotWidget.add_data(self.scans[self.scanNum]['scanArray'][:,0],self.scans[self.scanNum]['scanArray'][:,det_num]/norm,name=names[-1])
                self.plotWidget.Plot(names)
                self.scanfh.write(text+'\n')
                print(text)
                self.counterLabel.setText('#%d'%self.data_num)
                self.data_num+=1
                #Sleeping
                if sleep_time>1e-3:
                    self.scanStatus.setText('Sleeping')
                    QtTest.QTest.qWait(1000*sleep_time)
                self.scanStatus.clear()
            else:
                try:
                    camonitor_clear(self.scalers['scaler_start']['PV'])
                except:
                    pass
                self.continuousScanCheckBox.setCheckState(Qt.Unchecked)
                self.scanfh.write('\n')
                self.scanfh.write('##Scan Aborted after %d points'%self.data_num)
                print('\n')
                print('##Scan Aborted after %d points'%self.data_num)
                self.motorStopped=True
                break
            pg.QtGui.QApplication.processEvents()
            

    def ascan(self,motorname,start,finish,steps,count_time,sleep_time):
        """
        do absolute scan of the motor provided by motorname which starts with [start] and ends with [finish] positions with [steps] number of steps. The detector counts at each step for 1 second
        """        
        positions=np.linspace(start,finish,steps)
        caput(self.scalers['scaler_count_time']['PV'],count_time)   
        self.data_num=0
        for pos in positions:
            if not self.abort:
                caput(self.motors[motorname]['PV']+'.VAL',pos,wait=False)
                QtTest.QTest.qWait(10)
                while str(self.scanStatus.text())=='Moving':
                    pg.QtGui.QApplication.processEvents()
                    QtTest.QTest.qWait(10)
                if self.shutterModeCheckBox.isChecked():
                    self.shutter_ON()
                self.scanStatus.setText('Counting')
                caput(self.scalers['scaler_start']['PV'],1,wait=False)
                QtTest.QTest.qWait(10)
                while str(self.scanStatus.text())=='Counting':
                    pg.QtGui.QApplication.processEvents()
                    QtTest.QTest.qWait(10)
                if self.shutterModeCheckBox.isChecked():
                    self.shutter_OFF()                    
                self.count_time=caget(self.scalers['scaler_count_time']['PV'])
                self.bs_diode_counts=caget(self.scalers['bs_diode']['PV'])
                self.diode_counts=caget(self.scalers['diode']['PV'])
                self.monitor_counts=caget(self.scalers['monitor']['PV'])
                if 'scanArray' in self.scans[self.scanNum]:
                    self.scans[self.scanNum]['scanArray']=np.vstack((self.scans[self.scanNum]['scanArray'],np.array([pos,count_time,self.bs_diode_counts,self.diode_counts,self.monitor_counts])))
                else:
                    self.scans[self.scanNum]['scanArray']=np.array([[pos,count_time,self.bs_diode_counts,self.diode_counts,self.monitor_counts]])
                text='%d\t%.4f\t%.4f\t%d\t%d\t%d'%(self.data_num, pos,count_time,self.bs_diode_counts,self.diode_counts,self.monitor_counts)
                names=[]
                norm=1.0
                if self.normDetectorComboBox.currentText()!='none':
                    norm_num=self.scans[self.scanNum]['scanVariables'].index(self.normDetectorComboBox.currentText())
                    norm=self.scans[self.scanNum]['scanArray'][:,norm_num]
                for det in self.scanDetectors:
                    det_num=self.scans[self.scanNum]['scanVariables'].index(det)
                    names.append('%d-%s'%(self.scanNum,det))
                    self.plotWidget.add_data(self.scans[self.scanNum]['scanArray'][:,0],self.scans[self.scanNum]['scanArray'][:,det_num]/norm,name=names[-1])
                self.plotWidget.Plot(names)
                self.scanfh.write(text+'\n')
                print(text)
                self.counterLabel.setText('#%d'%self.data_num)
                self.data_num+=1
                #Sleeping
                if sleep_time>1e-3:
                    self.scanStatus.setText('Sleeping')
                    QtTest.QTest.qWait(1000*sleep_time)
                self.scanStatus.clear()
            else:
                try:
                    camonitor_clear(self.scalers['scaler_start']['PV'])
                except:
                    pass
                self.continuousScanCheckBox.setCheckState(Qt.Unchecked)
                self.scanfh.write('\n')
                self.scanfh.write('##Scan Aborted after %d points'%self.data_num)
                print('\n')
                print('##Scan Aborted after %d points'%self.data_num)
                self.motorStopped=True
                break
            pg.QtGui.QApplication.processEvents()
        
        
        
    def pre_scan(self,motorname,start,finish,steps,count_time,sleep_time):
        """
        Things to do before doing the scan, like setting of the data file for the scan by saving some predefined parameters and resetting the plotter
        """
        #self.scanListWidget.itemSelectionChanged.disconnect(self.scanSelectionChanged)
        #self.plotWidget.plotWidget.getPlotItem().vb.scene().sigMouseClicked.disconnect(self.mouseClicked)
        #self.normDetectorComboBox.setDisabled(True)
        self.scanMotorComboBox.setDisabled(True)
        self.scanTypeComboBox.setDisabled(True)
        self.scanListWidget.setDisabled(True)
        self.scanMinLineEdit.setDisabled(True)
        self.scanMaxLineEdit.setDisabled(True)
        self.scanStepsLineEdit.setDisabled(True)
        self.countTimeLineEdit.setDisabled(True)
        self.sleepTimeLineEdit.setDisabled(True)
        #if self.scanDetector!='Diode':
        #    self.beam
        self.scanAbortPushButton.setText('Abort')
        self.scanListWidget.clearSelection()
        
        try:
            camonitor_clear(self.scalers['scaler_start']['PV'])
        except:
            pass
        if self.scanName=='MotorScan':
            high=caget(self.motors[motorname]['PV']+'.HLM')
            low=caget(self.motors[motorname]['PV']+'.LLM')
            self.plotWidget.setXLabel(motorname)
            self.plotWidget.setYLabel('Counts')
            if low<start<high and low<finish<high:
                camonitor(self.scalers['scaler_start']['PV'],callback=self.scalerStatus)
                self.scans[self.scanNum]={}
                self.scanFile=os.path.join(self.scanFolder,'Scan%04d.dat'%self.scanNum)
                self.scanfh=open(self.scanFile,'w')
                print('\n')
                text='#S %d %s %s %s %.5f %.5f %d %.5f %.5f'%(self.scanNum,self.scanName,self.scanMotorName,self.scanType,self.scanMin,self.scanMax,self.scanSteps,count_time,sleep_time)
                    
                self.scans[self.scanNum]['scanHeader']=text
                self.scanfh.write(text)
                self.scanfh.write('\n')
                print(text+'\n')
                text='#%s %s\t%s\t%s\t%s\t%s'%('Pt',self.scanMotorName,'count-time','bs-diode','diode','monitor')
                self.scans[self.scanNum]['scanVariables']=text.split()[1:]
                self.scanfh.write(text+'\n')
                #self.detectorNum=self.scans[self.scanNum]['scanVariables'].index(self.scanDetector)
                print(text)
                self.plotWidget.setTitle(self.scans[self.scanNum]['scanHeader'])
                self.preScanOK=True
            else:
                QMessageBox.warning(self,'Motor Limits','Scanning range is ouside the soft limit! Please review your scan range.',QMessageBox.Ok)
                self.preScanOK=False
        elif self.scanName=='TimeScan':
            self.scanMotorName=self.scanMotorComboBox.currentText()
            camonitor(self.scalers['scaler_start']['PV'],callback=self.scalerStatus)
            self.scans[self.scanNum]={}
            self.scanFile=os.path.join(self.scanFolder,'Scan%04d.dat'%self.scanNum)
            self.scanfh=open(self.scanFile,'w')
            print('\n')
            text='#S %d %s %s %.5f %.5f'%(self.scanNum,self.scanName,self.scanMotorName,count_time,sleep_time)
            self.scans[self.scanNum]['scanHeader']=text
            self.scanfh.write(text)
            self.scanfh.write('\n')
            print(text+'\n')
            text='#%s %s\t%s\t%s\t%s\t%s'%('Pt',self.scanMotorName,'count-time','bs-diode','diode','monitor')
            self.scans[self.scanNum]['scanVariables']=text.split()[1:]
            self.scanfh.write(text+'\n')
            #self.detectorNum=self.scans[self.scanNum]['scanVariables'].index(self.scanDetector)
            print(text)
            self.plotWidget.setTitle(self.scans[self.scanNum]['scanHeader'])
            self.preScanOK=True
        elif self.scaneName=='SlitScan':
            self.scanMotorName=self.scanMotorComboBox.currentText()
            high=caget(self.motors[motorname]['PV']+'.DRVH')
            low=caget(self.motors[motorname]['PV']+'.DRVL')
            self.plotWidget.setXLabel(self.scanMotorName)
            self.plotWidget.setYLabel('Counts')
            if low<start<high and low<finish<high:
                camonitor(self.scalers['scaler_start']['PV'],callback=self.scalerStatus)
                self.scans[self.scanNum]={}
                self.scanFile=os.path.join(self.scanFolder,'Scan%04d.dat'%self.scanNum)
                self.scanfh=open(self.scanFile,'w')
                print('\n')
                text='#S %d %s %s %s %.5f %.5f %d %.5f %.5f'%(self.scanNum,self.scanName,self.scanMotorName,self.scanType,self.scanMin,self.scanMax,self.scanSteps,count_time,sleep_time)
                    
                self.scans[self.scanNum]['scanHeader']=text
                self.scanfh.write(text)
                self.scanfh.write('\n')
                print(text+'\n')
                text='#%s %s\t%s\t%s\t%s\t%s'%('Pt',self.scanMotorName,'count-time','bs-diode','diode','monitor')
                self.scans[self.scanNum]['scanVariables']=text.split()[1:]
                self.scanfh.write(text+'\n')
                self.detectorNum=self.scans[self.scanNum]['scanVariables'].index(self.scanDetector)
                print(text)
                self.plotWidget.setTitle(self.scans[self.scanNum]['scanHeader'])
                self.preScanOK=True
            else:
                QMessageBox.warning(self,'Motor Limits','Scanning range is ouside the soft limit! Please review your scan range.',QMessageBox.Ok)
                self.preScanOK=False
                
                
                
            
    def scalerStatus(self,**kwargs):
        value=kwargs['value']
        if value==1:
            self.scanStatus.setText('Counting')
        else:
            self.scanStatus.setText('Done')
        
        
        
    def scan(self):
        self.scanMinChanged()
        self.scanMaxChanged()
        self.scanStepsChanged()
        self.countTimeChanged()
        self.sleepTimeChanged()
        self.startMotorPos=float(self.scanMotorPositionLabel.text())
        if self.scanType=='Relative':
            start=self.startMotorPos+self.scanMin
            finish=self.startMotorPos+self.scanMax
        else:
            start=self.scanMin
            finish=self.scanMax
        steps=self.scanSteps
        if self.scanName=='MotorScan':
            self.pre_scan(self.scanMotorName,start,finish,steps,self.countTime,self.sleepTime)
            if self.preScanOK:
                self.ascan(self.scanMotorName,start,finish,steps,self.countTime,self.sleepTime)
            self.post_scan(self.scanMotorName)
        elif self.scanName=='TimeScan':
            self.pre_scan(self.scanMotorName,start,finish,steps,self.countTime,self.sleepTime)
            if self.preScanOK:
                self.tscan(self.countTime,self.sleepTime)
            self.post_scan(self.scanMotorName)
        elif self.scanName=='EnergyScan':
            QMessageBox.warning(self,'Future Feature','This feature is not implemented yet!',QMessageBox.Ok)
        elif self.scanName=='SlitScan':
            self.pre_scan(self.scanMotorName,start,finish,steps,self.countTime,self.sleepTime)
            if self.preScanOK:
                self.slitscan(self.scanMotorName,start,finish,steps,self.countTime,self.sleepTime)
            self.post_scan(self.scanMotorName)
            
            
        
    def post_scan(self,motorname):
        """
        Things to do after completion of a scan
        """
        if self.preScanOK:
            if 'scanArray' not in self.scans[self.scanNum].keys():
                self.scans[self.scanNum]['scanArray']=None
            self.scanListWidget.addItem('Scan %d: %s'%(self.scanNum,motorname))
            self.scanfh.close()
            self.scanNum+=1
            self.update_scan_record()
            self.scanListWidget.setCurrentRow(self.scanNum-1)
        if self.scanName=='MotorScan':
            caput(self.motors[self.scanMotorName]['PV']+'.SPMG',3,wait=True) 
            caput(self.motors[motorname]['PV']+'.VAL',self.startMotorPos,wait=True)
        elif self.scanName=='SlitScan':
            caput(self.slitParams[self.scanMotorName]['MOV1']+'.SPMG',3,wait=True)
            caput(self.slitParams[self.scanMotorName]['MOV2']+'.SPMG',3,wait=True)
            caput(self.slitParams[self.scanMotorName]['PV']+'.VAL',self.startMotorPos,wait=True)
        #while caget(self.motors[motorname]['PV']+'.DMOV')!=1:
        #    #self.scanMotorPositionLabel.setText('%.4f'%caget(self.motors[motorname]['PV']+'.RBV'))
        #    pg.QtGui.QApplication.processEvents()
        self.scanAbortPushButton.setText('Scan')
        #self.scanStatus.setText('Done')
        
        #self.scanListWidget.itemSelectionChanged.connect(self.scanSelectionChanged)
        #self.plotWidget.plotWidget.getPlotItem().vb.scene().sigMouseClicked.connect(self.mouseClicked)
        #self.normDetectorComboBox.setDisabled(False)
        self.scanMotorComboBox.setDisabled(False)
        self.scanTypeComboBox.setDisabled(False)
        self.scanListWidget.setDisabled(False)
        self.scanMinLineEdit.setDisabled(False)
        self.scanMaxLineEdit.setDisabled(False)
        self.scanStepsLineEdit.setDisabled(False)
        self.countTimeLineEdit.setDisabled(False)
        self.sleepTimeLineEdit.setDisabled(False)
        
        
    def scanSelectionChanged(self):
        """
        Displays the selected scans of scanListwidget
        """
        motorName=[]
        for item in self.scanListWidget.selectedItems():
            motorName.append(str(item.text()).split(':')[1].strip())
        if motorName!=[]:
            if len(set(motorName))==1:
                names=[]
                for item in self.scanListWidget.selectedItems():
                    scanNum=int(str(item.text()).split(':')[0].split()[1])
                    self.normDetectorChanged()
                    self.detectorListWidgetChanged()
                    norm=1.0
                    if self.normDetectorComboBox.currentText()!='none':
                        norm_num=self.scans[scanNum]['scanVariables'].index(self.normDetectorComboBox.currentText())
                        norm=self.scans[scanNum]['scanArray'][:,norm_num]
                    for det in self.scanDetectors:
                        det_num=self.scans[scanNum]['scanVariables'].index(det)
                        if self.scans[scanNum]['scanArray'] is not None:
                            #print(self.scans[scanNum])
                            names.append('%d-%s'%(scanNum,det))
                            self.plotWidget.add_data(self.scans[scanNum]['scanArray'][:,0],self.scans[scanNum]['scanArray'][:,det_num]/norm,name=names[-1])
                self.plotWidget.Plot(names)
                self.plotWidget.setXLabel(motorName[0])
                self.plotWidget.setYLabel('Counts')
            else:
                QMessageBox.warning(self,'Scan selection error','The scans are not done on same motor. Please select scans with same motor',QMessageBox.Ok)
                self.scanListWidget.itemSelectionChanged.disconnect(self.scanSelectionChanged)
                self.scanListWidget.clearSelection()
                self.scanListWidget.itemSelectionChanged.connect(self.scanSelectionChanged)
            
            
            
        
                
    def motorMotionDetected(self, moving):
        self.sigMotorMoving
        
        
    def triggerAllDetectors(self):
        """
        trigger all the scalers and selected detectors together
        """
        #for name in self.detectors.keys():
        #    caput(self.detectors[name]['PV']+'Acquire',1)
        caput(self.scalers['scaler_start']['PV'],1)
        while caget(self.scalers['scaler_start']['PV'])!=0:
                    pg.QtGui.QApplications.processEvents()
        
        
                
if __name__=='__main__':
    app=QApplication(sys.argv)
    w=Scanner('/tmp')
    w.setWindowTitle('Scanner')
    w.setGeometry(0,0,800,500)
    
    w.show()
    sys.exit(app.exec_())                
                    
                
        
            
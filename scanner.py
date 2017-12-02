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
        
        
        self.vblayout=QVBoxLayout(self)
        self.mainDock=DockArea(self,parent)
        self.vblayout.addWidget(self.mainDock)
        
        self.scanParamDock=Dock('Scan Parameters',size=(5,1))
        self.scanListDock=Dock('Scan list',size=(1,9))
        self.scanPlotDock=Dock('Scan Plots',size=(3,9))
        self.savedPositionDock=Dock('Saved positions',size=(1,9))
        self.mainDock.addDock(self.scanParamDock,'top')
        self.mainDock.addDock(self.scanListDock,'bottom',self.scanParamDock)
        self.mainDock.addDock(self.scanPlotDock,'right',self.scanListDock)
        self.mainDock.addDock(self.savedPositionDock,'right',self.scanPlotDock)
        
        
        self.createScanParamDock()
        self.createScanListDock()
        self.createScanPlotDock()
        self.createSavedPositionDock()
        self.changeScanFolder(scanFolder)
        
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
        scanMotorLabel=QLabel('Motor')
        scanDetectorLabel=QLabel('Detector')
        scanTypeLabel=QLabel('Scan type')
        motorPositionLabel=QLabel('Motor Pos')
        scanMinLabel=QLabel('Min')
        scanMaxLabel=QLabel('Max')
        scanStepsLabel=QLabel('Steps')
        scanTimeLabel=QLabel('Count time')
        self.counterLabel=QLabel('%20s'%'#')
        self.scanStatus=QLabel('%20s'%'')
        self.scanParamLayout.addWidget(scanMotorLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(scanDetectorLabel,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(scanTypeLabel,row=row,col=col)
        col+=1
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
        self.scanParamLayout.addWidget(self.counterLabel,row=row,col=col)
        col+=2
        self.scanParamLayout.addWidget(self.scanStatus,row=row,col=col)
        
        row+=1
        col=0
        self.scanMotorComboBox=QComboBox()
        self.scanMotorComboBox.addItems(list(self.motors.keys()))
        self.scanMotorComboBox.setCurrentIndex(self.scanMotorComboBox.findText('d_x'))
        self.scanDetectorComboBox=QComboBox()
        self.scanDetectorComboBox.addItems(['monitor','diode','bs-diode'])
        self.scanDetectorComboBox.currentIndexChanged.connect(self.scanSelectionChanged)
        self.scanTypeComboBox=QComboBox()
        self.scanTypeComboBox.addItems(['Relative','Absolute'])
        self.scanMotorPos=caget(self.motors[str(self.scanMotorComboBox.currentText())]['PV']+'.RBV')
        self.scanMotorPositionLabel=QLabel(str(self.scanMotorPos))
        self.scanMinLineEdit=QLineEdit('-1.0')
        self.scanMaxLineEdit=QLineEdit('1.0')
        self.scanStepsLineEdit=QLineEdit('11')
        self.countTimeLineEdit=QLineEdit('1.0')
        self.continuousScanCheckBox=QCheckBox('Continuous')
        self.continuousScanCheckBox.setTristate(False)
        self.shutterModeCheckBox=QCheckBox('Auto Shutter')        
        self.scanAbortPushButton=QPushButton('Scan')
        self.scanParamLayout.addWidget(self.scanMotorComboBox,row=row,col=col)
        self.scanMotorComboBox.currentIndexChanged.connect(self.scanMotorChanged)
        col+=1
        self.scanParamLayout.addWidget(self.scanDetectorComboBox,row=row,col=col)
        self.scanDetectorComboBox.currentIndexChanged.connect(self.scanDetectorChanged)
        col+=1
        self.scanParamLayout.addWidget(self.scanTypeComboBox,row=row,col=col)
        self.scanTypeComboBox.currentIndexChanged.connect(self.scanTypeChanged)
        col+=1
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
        self.scanParamLayout.addWidget(self.continuousScanCheckBox,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(self.shutterModeCheckBox,row=row,col=col)
        col+=1
        self.scanParamLayout.addWidget(self.scanAbortPushButton,row=row,col=col)      
        self.scanAbortPushButton.clicked.connect(self.startAbortScan)
        
        
        self.scanParamDock.addWidget(self.scanParamLayout)
        
        self.scanMotorChanged()
        self.scanDetectorChanged()
        self.scanTypeChanged()
        self.scanMinChanged()
        self.scanMaxChanged()
        self.scanStepsChanged()
        self.countTimeChanged()
        
        
    def scanMotorChanged(self):
        """
        The scanning motor is changed
        """
        try:
            camonitor_clear(self.oldMotorName)
        except:
            pass
        self.scanMotorName=str(self.scanMotorComboBox.currentText())
        self.scanMotorPos=caget(self.motors[self.scanMotorName]['PV']+'.RBV')
        self.scanMotorPositionLabel.setText('%3.5f'%self.scanMotorPos)
        camonitor(self.motors[str(self.scanMotorComboBox.currentText())]['PV']+'.RBV',callback=self.motorMoved)
        camonitor(self.motors[str(self.scanMotorComboBox.currentText())]['PV']+'.DMOV',callback=self.motorStatus)
        self.oldMotorName=copy.copy(self.scanMotorName)
        
    def motorMoved(self,**kwargs):
        value=kwargs['value']
        self.scanMotorPositionLabel.setText('%3.5f'%value)
        
    def motorStatus(self,**kwargs):
        value=kwargs['value']
        if value!=1:
            self.scanStatus.setText('Moving')
        else:
            self.scanStatus.setText('Done')
        
        
    
    def scanDetectorChanged(self):
        """
        The scanning detector changed
        """
        self.scanDetector=str(self.scanDetectorComboBox.currentText())
        
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
        The scan time os changed
        """
        try:
            self.countTime=float(self.countTimeLineEdit.text())
        except:
            QMessageBox.warning(self,'Value error','Please input decimal numbers only',QMessageBox.Ok)
            self.countTime=1.0
            self.countTime.LineEdit.setText(str(self.countTime))
            
        
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
            caput(self.motors[self.scanMotorName]['PV']+'.SPMG',0)
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
        self.scanListWidget.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.scanListWidget.itemSelectionChanged.connect(self.scanSelectionChanged)
        self.scanListLayout.addWidget(self.scanListWidget,row=row,col=col,rowspan=15)
        
        self.scanListDock.addWidget(self.scanListLayout)
        
    def createSavedPositionDock(self):
        """
        """
        self.savedPositionLayout=pg.LayoutWidget(self)
        row=0
        col=0
        self.savedPosTreeWidget=pg.DataTreeWidget(self)
        self.savedPositionLayout.addWidget(self.savedPosTreeWidget,row=row,col=col,rowspan=15)
        self.savedPositionDock.addWidget(self.savedPositionLayout)
        
        
        
        
        
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
            motorName=lines[0][:-1].split()[2]
            self.scans[num]['scanHeader']=lines[0][:-1]
            self.scans[num]['scanVariables']=lines[1].split()[1:]
            self.scans[num]['scanArray']=np.array([float(val) for val in lines[2].split()[1:]])
            for line in lines[3:]:
                try:
                    self.scans[num]['scanArray']=np.vstack((self.scans[num]['scanArray'],np.array([float(val) for val in line.split()[1:]])))
                except:
                    self.scans[num]['scanArray']=None
            self.scanListWidget.addItem('Scan %d: %s'%(num,motorName))
            
        

    def ascan(self,motorname,start,finish,steps,count_time):
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
                self.plotWidget.add_data(self.scans[self.scanNum]['scanArray'][:,0],self.scans[self.scanNum]['scanArray'][:,self.detectorNum],name=str(self.scanNum))
                self.scanfh.write(text+'\n')
                print(text)
                self.counterLabel.setText('#%d'%self.data_num)
                self.data_num+=1
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
        
        
        
    def pre_scan(self,motorname,start,finish,steps,count_time):
        """
        Things to do before doing the scan, like setting of the data file for the scan by saving some predefined parameters and resetting the plotter
        """
        #self.scanListWidget.itemSelectionChanged.disconnect(self.scanSelectionChanged)
        #self.plotWidget.plotWidget.getPlotItem().vb.scene().sigMouseClicked.disconnect(self.mouseClicked)
        self.scanDetectorComboBox.setDisabled(True)
        self.scanMotorComboBox.setDisabled(True)
        self.scanTypeComboBox.setDisabled(True)
        self.scanListWidget.setDisabled(True)
        self.scanMinLineEdit.setDisabled(True)
        self.scanMaxLineEdit.setDisabled(True)
        self.scanStepsLineEdit.setDisabled(True)
        self.countTimeLineEdit.setDisabled(True)
        #if self.scanDetector!='Diode':
        #    self.beam
        self.scanAbortPushButton.setText('Abort')
        self.scanListWidget.clearSelection()
        high=caget(self.motors[motorname]['PV']+'.HLM')
        low=caget(self.motors[motorname]['PV']+'.LLM')
        self.plotWidget.setXLabel(motorname)
        self.plotWidget.setYLabel(self.scanDetector)
        try:
            camonitor_clear(self.scalers['scaler_start']['PV'])
        except:
            pass
        if low<start<high and low<finish<high:
            camonitor(self.scalers['scaler_start']['PV'],callback=self.scalerStatus)
            self.scans[self.scanNum]={}
            self.scanFile=os.path.join(self.scanFolder,'Scan%04d.dat'%self.scanNum)
            self.scanfh=open(self.scanFile,'w')
            print('\n')
            text='#S %d %s %s %.5f %.5f %d %.5f'%(self.scanNum,self.scanMotorName,self.scanType,self.scanMin,self.scanMax,self.scanSteps,self.countTime)
            self.scans[self.scanNum]['scanHeader']=text
            self.scanfh.write(text)
            self.scanfh.write('\n')
            print(text+'\n')        
            text='#%s %s\t%s\t%s\t%s\t%s'%('Pt', self.scanMotorName,'count-time','bs-diode','diode','monitor')
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
        self.startMotorPos=float(self.scanMotorPositionLabel.text())
        if self.scanType=='Relative':
            start=self.startMotorPos+self.scanMin
            finish=self.startMotorPos+self.scanMax
        else:
            start=self.scanMin
            finish=self.scanMax
        steps=self.scanSteps
        count_time=self.countTime
        self.pre_scan(self.scanMotorName,start,finish,steps,count_time)
        if self.preScanOK:
            self.ascan(self.scanMotorName,start,finish,steps,count_time)
        self.post_scan(self.scanMotorName)
            
        
    def post_scan(self,motorname):
        """
        Things to do after completion of a scan
        """
        if self.preScanOK:
            if 'scanArray' not in self.scans[self.scanNum].keys():
                self.scans[self.scanNum]['scanArray']=None
            self.scanListWidget.addItem('Scan %d: %s'%(self.scanNum,self.scanMotorName))
            self.scanfh.close()
            self.scanNum+=1
            self.update_scan_record()
            self.scanListWidget.setCurrentRow(self.scanNum-1)
        caput(self.motors[self.scanMotorName]['PV']+'.SPMG',3,wait=True) 
        caput(self.motors[motorname]['PV']+'.VAL',self.startMotorPos,wait=True)
        #while caget(self.motors[motorname]['PV']+'.DMOV')!=1:
        #    #self.scanMotorPositionLabel.setText('%.4f'%caget(self.motors[motorname]['PV']+'.RBV'))
        #    pg.QtGui.QApplication.processEvents()
        self.scanAbortPushButton.setText('Scan')
        #self.scanStatus.setText('Done')
        
        #self.scanListWidget.itemSelectionChanged.connect(self.scanSelectionChanged)
        #self.plotWidget.plotWidget.getPlotItem().vb.scene().sigMouseClicked.connect(self.mouseClicked)
        self.scanDetectorComboBox.setDisabled(False)
        self.scanMotorComboBox.setDisabled(False)
        self.scanTypeComboBox.setDisabled(False)
        self.scanListWidget.setDisabled(False)
        self.scanMinLineEdit.setDisabled(False)
        self.scanMaxLineEdit.setDisabled(False)
        self.scanStepsLineEdit.setDisabled(False)
        self.countTimeLineEdit.setDisabled(False)
        
        
    def scanSelectionChanged(self):
        """
        Displays the selected scans of scanListwidget
        """
        motorName=[]
        for item in self.scanListWidget.selectedItems():
            motorName.append(str(item.text()).split(':')[1])
        if len(set(motorName))==1:
            sNum=[]
            for item in self.scanListWidget.selectedItems():
                scanNum=int(str(item.text()).split(':')[0].split()[1])
                sNum.append(str(scanNum))
                self.scanDetectorChanged()
                detectorNum=self.scans[scanNum]['scanVariables'].index(self.scanDetector)
                if self.scans[scanNum]['scanArray'] is not None:
                    self.plotWidget.add_data(self.scans[scanNum]['scanArray'][:,0],self.scans[scanNum]['scanArray'][:,detectorNum],name=str(scanNum))
                else:
                    sNum.remove(str(scanNum))
            self.plotWidget.Plot(sNum)
            self.plotWidget.setXLabel(motorName[0])
            self.plotWidget.setYLabel(self.scanDetectorComboBox.currentText())
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
                    
                
        
            
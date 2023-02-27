from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QDesktopWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QFileDialog, QCheckBox, QSpinBox
from PyQt5.QtCore import Qt, QProcess, pyqtSignal
from PyQt5.QtGui import QPalette
from Image_Widget import Image_Widget
from PyQt5 import QtTest
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
import sys
import numpy as np
from epics import caget, caput, camonitor, camonitor_clear
import fabio as fb
import os
from fileWatcher import FileWatcher
from Setup import Setup
import time


class Detector_Widget(QWidget):
    """
    This Widget is developed for Area Detector Data collection and Visualization.
    """
    arrayDataUpdated=pyqtSignal()
    imageFileUpdated=pyqtSignal()

    def __init__(self, imgFName='img', parent=None):
        QWidget.__init__(self, parent=None)
        self.palette=QPalette()
        self.cwd=os.getcwd()
        self.setup=Setup(os.path.join(self.cwd,'SetupData'))
        self.detectors=self.setup.detectors
        self.motors=self.setup.motors
        self.scalers=self.setup.scalers
        self.imgFName=imgFName
        self.vblayout=QVBoxLayout(self)
        self.mainDock=DockArea(self,parent)
        self.vblayout.addWidget(self.mainDock)
        self.imageFlag=0
        
        self.pdIn=False
        self.beamIn=False
        self.mirrorIn=False
        self.align=True
        self.delay=0.1
        self.detPV='None'
        
        
        

        self.detParDock=Dock('Detector Parameters',size=(1,1))
        self.imgDock=Dock('Image',size=(1,10))
        self.mainDock.addDock(self.imgDock,'left')
        self.mainDock.addDock(self.detParDock,'left')
        self.mainDock.moveDock(self.imgDock,'bottom',self.detParDock)

        self.create_imgDock()
        self.create_detParDock()

        self.fileWatcher=FileWatcher()
        #self.fileWatcher.fileModified.connect(self.newImageObtained)
        #self.fileWatcher.fileCreated.connect(self.removePath)
        
        
            
        
    def newImageObtained(self):
        """
        Updates the image of the Detector
        """
        time.sleep(2)
        if self.currentDetector=='PhotonII':
            self.imgFile=caget('13PII_1:TIFF1:FullFileName_RBV',as_string=True)
        else:
            self.imgFile=caget(self.detPV.split(':')[0]+':TIFF1:FullFileName_RBV',as_string=True)
        self.img=fb.open(self.imgFile.replace(self.detectors[self.currentDetector]['det_folder'],self.detectors[self.currentDetector]['cars_folder']))
        self.imgData=self.img.data
        self.imgHeader=self.img.header
        self.imgWidget.setImage(self.imgData,transpose=False)
        self.imgWidget.scaleChanged()
        self.imgWidget.imageView.getView().setTitle(self.imgFile.replace(self.detectors[self.currentDetector]['det_folder'],self.detectors[self.currentDetector]['cars_folder']))
        QApplication.processEvents()
        self.monitor_counts=caget(self.scalers['monitor']['PV'])
        self.count_time=caget(self.scalers['15IDD_scaler_count_time']['PV'])
        self.diode_counts=caget(self.scalers['diode']['PV'])
        self.BSDiode_counts=caget(self.scalers['bs_diode']['PV'])
        self.img.header['Monitor']=self.monitor_counts
        self.img.header['count_time']=self.count_time
        self.img.header['BSDiode']=self.BSDiode_counts
        
        

        
        
     
                
    def reset_detector(self):
        """
        Resets the detector for default configuration
        """
        caput(self.detPV+'AcquireTime',1.0)
        caput(self.detPV+'AcquirePeriod',0.0)
        caput(self.detPV+'NumImages',1)
        #caput(self.detPV+'ImageMode',0)
        

    def create_imgDock(self):
        """
        Creates the imgDock
        """
        img=np.random.rand(100,100)
        self.imgWidget=Image_Widget(img,transpose=True)
        self.imgDock.addWidget(self.imgWidget)

    def create_detParDock(self):
        """
        Creates the control dock
        """
        row=0
        self.detParLayout=pg.LayoutWidget(self)
        detectorLabel=QLabel('Detector')
        detectorLabel.setAlignment(Qt.AlignJustify|Qt.AlignVCenter)
        self.detectorComboBox=QComboBox()
        self.detectorComboBox.addItems(['None']+list(self.detectors.keys()))
        self.detectorComboBox.currentIndexChanged.connect(self.detectorChanged)
        self.detectorConnectionLabel=QLabel()
        self.detectorConnectionLabel.setAlignment(Qt.AlignJustify|Qt.AlignVCenter)
        self.detectorMEDMScreenButton=QPushButton('Detector MEDM')
        self.detectorMEDMScreenButton.clicked.connect(self.startDetMEDM)
        self.detParLayout.addWidget(detectorLabel,row=row,col=0)
        self.detParLayout.addWidget(self.detectorComboBox,row=row,col=1)
        self.detParLayout.addWidget(self.detectorConnectionLabel,row=row,col=2)
        self.detParLayout.addWidget(self.detectorMEDMScreenButton,row=row,col=3)
        
        
        row=row+1
        detSusLabel=QLabel('Detector Status')
        self.detStatusLabel=QLabel()
        self.detParLayout.addWidget(detSusLabel,row=row,col=0)
        self.detParLayout.addWidget(self.detStatusLabel,row=row,col=1)


        row=row+1
        shutterModeLabel=QLabel('Shutter Mode')
        self.shutterModeComboBox=QComboBox()
        self.shutterModeComboBox.addItems(['None','Epics PV'])
        self.shutterModeComboBox.currentIndexChanged.connect(self.shutterModeChanged)
        self.detParLayout.addWidget(shutterModeLabel,row=row,col=0)
        self.detParLayout.addWidget(self.shutterModeComboBox,row=row,col=1)        

        row=row+1        
        detImgFolderLabel=QLabel('Image Folder (Det)')
        self.detImgFolderLineEdit=QLineEdit()
        carsImgFolderLabel=QLabel('Image Folder (CARS5)')
        self.carsImgFolderLineEdit=QLineEdit()
        self.selectCarsImgFolderPushButton=QPushButton('Select')
        self.selectCarsImgFolderPushButton.clicked.connect(lambda x: self.carsImgFolderChanged(imgFolder=None))
#        self.imgFolderStatusLabel=QLabel()
#        self.imgFolderStatusLabel.setPalette(self.palette)
        self.detParLayout.addWidget(detImgFolderLabel, row=row, col=0)
        self.detParLayout.addWidget(self.detImgFolderLineEdit, row=row, col=1, colspan=3)
        row=row+1
        self.detParLayout.addWidget(carsImgFolderLabel,row=row,col=0)
        self.detParLayout.addWidget(self.carsImgFolderLineEdit, row=row, col=1,colspan=2)
        self.detParLayout.addWidget(self.selectCarsImgFolderPushButton,row=row,col=3)
        
        row=row+1
        imgFNameLabel=QLabel('Image Prefix')
        self.imgFNameLineEdit=QLineEdit(self.imgFName)
        self.imgFNameLineEdit.returnPressed.connect(self.imgFNameChanged)
        imgFNumLabel=QLabel('%s'%'Img #')
        self.numOfImages=1
        self.numOfImagesLineEdit=QLineEdit(str(self.numOfImages))
        self.detParLayout.addWidget(imgFNameLabel,row=row,col=0)
        self.detParLayout.addWidget(self.imgFNameLineEdit,row=row,col=1)
        self.detParLayout.addWidget(imgFNumLabel,row=row,col=2)
        self.detParLayout.addWidget(self.numOfImagesLineEdit,row=row,col=3)
        

        row=row+1
        expTimeLabel=QLabel('Exp time (s)')
        self.expTime=1.0        
        self.expTimeLineEdit=QLineEdit(str(self.expTime))
        self.expTimeLineEdit.returnPressed.connect(self.expTimeChanged)
        self.detParLayout.addWidget(expTimeLabel,row=row,col=0)
        self.detParLayout.addWidget(self.expTimeLineEdit,row=row,col=1)

        
        
        row=row+1
        timeElapsedLabel = QLabel('Time Elapsed (s):')
        self.timeElapsedLabel = QLabel('%.3f' % 0.0)
        self.countPushButton=QPushButton('Count')
        self.counting=False
        self.countPushButton.clicked.connect(self.startStopCount)
        self.saveLastPushButton=QPushButton('Save last')
        self.saveLastPushButton.clicked.connect(self.saveLastImg)
        self.detParLayout.addWidget(timeElapsedLabel, row=row, col=0)
        self.detParLayout.addWidget(self.timeElapsedLabel, row=row, col=1)
        self.detParLayout.addWidget(self.countPushButton,row=row,col=2)
        self.detParLayout.addWidget(self.saveLastPushButton,row=row,col=3)
        
        
        self.detParDock.addWidget(self.detParLayout)
        
        
        
    def create_detAlignmentDock(self):
        """
        Creates the Detector Alignment dock
        """
        self.detAlignLayout=pg.LayoutWidget(self)
        row=0
        #imgModeLabel=QLabel('Img Mode')
        #self.imgModeComboBox=QComboBox()
        #self.imgModeComboBox.addItems(['Single','Continuous'])
        #self.imgModeComboBox.currentIndexChanged.connect(self.imgModeChanged)
        self.countPushButton=QPushButton('Count')
        self.counting=False
        self.countPushButton.clicked.connect(self.startStopCount)
        self.saveLastPushButton=QPushButton('Save last')
        self.saveLastPushButton.clicked.connect(self.saveLastImg)
        #self.detAlignLayout.addWidget(imgModeLabel,row=row,col=0)
        #self.detAlignLayout.addWidget(self.imgModeComboBox,row=row,col=1)
        self.detAlignLayout.addWidget(self.countPushButton,row=row,col=2)
        self.detAlignLayout.addWidget(self.saveLastPushButton,row=row,col=3)        
        
        self.detAlignDock.addWidget(self.detAlignLayout)

    def startDetMEDM(self):
        """
        Shows the DetectorMEDM screen
        """
        try:
            det_txt=str(self.detectorComboBox.currentText())
            det_name=self.detectors[det_txt]['PV']
            P,R,_=det_name.split(':')
            if 'Pilatus' in det_txt:
                QProcess.startDetached('medm -x -macro "P=%s:,R=%s:" "./adl/pilatusDetector.adl"'%(P,R))
            elif 'Mar' in det_txt:
                print('I m here')
                QProcess.startDetached(
                    'medm -x -macro "P=%s:,R=%s:" "./adl/marCCD.adl"' % (P, R))
        except:
            QMessageBox.warning(self,'Detector Error','Please select a valid detector first.',QMessageBox.Ok)
            
            
    def saveLastImg(self):
        """ 
        Saves the last image in the memory
        """
        fname=QFileDialog.getSaveFileName(self,caption='Provide Filename',directory=self.carsImgFolder,filter='Image Files (*.edf)')[0]
        file=fb.edfimage.EdfImage()
        file.data=self.imgData
        file.header['Monitor']=self.monitor_counts#1000#caget(self.scalers['Monitor']['PV'])
        file.header['count_time']=self.count_time#1.0#caget(self.scalers['count_time']['PV'])
        file.header['Diode']=self.diode_counts#300#caget(self.scalers['Diode']['PV'])
        file.header['BSDiode']=self.BSdiode_counts#300#caget(self.scalers['BSDiode']['PV'])
        file.header['xcradle']=0.0
        file.write(fname)
        
        
        
    def startStopCount(self):
        """
        Start the detector for counting
        """

        #self.detState = 'Busy'
        if self.detPV!='None':
            caput(self.scalers['15IDD_scaler_mode']['PV'],0) #Setting the counter to one-shot mode
            if not self.counting:
                #if self.align:
                #self.set_det_alignment_mode()
                self.expTimeChanged()
                self.countPushButton.setText('Stop')
                self.counting = True
                self.detStatus = 1
                caput(self.scalers['15IDD_scaler_count_time']['PV'],self.expTime,wait=True)
                caput(self.detPV+'Acquire',1)
                caput(self.scalers['15IDD_scaler_start']['PV'],1)
                stime = time.time()
                while self.detStatus==1:
                    timeElapsed=time.time()-stime
                    self.timeElapsedLabel.setText('%.3f'%timeElapsed)
                    QApplication.processEvents()
            else:
                caput(self.detPV+'Acquire',0)
                caput(self.scalers['15IDD_scaler_start']['PV'],0)
            self.counting=False
            self.countPushButton.setText('Count')
        else:
            QMessageBox.warning(self,'Detector Error','Please choose a Detector first which is connected',QMessageBox.Ok)
        #caput(self.scalers['scaler_mode']['PV'],0) #Setting back the counter to auto-count mode
        

    def start_monitor_mode(self):
        """
        Initiates the mode of the Detector in which it only updates the image
        """
        pass
            
        
    def getDetectorStatus(self,**kwargs):
        """
        Updates the status of the detector
        """
        self.detStatus=kwargs['value']
        if self.detStatus==0:            
            self.palette.setColor(QPalette.Foreground,Qt.green)
            txt='Done'
        else:
            self.palette.setColor(QPalette.Foreground,Qt.red)
            txt='Collecting'
            
        self.detStatusLabel.setPalette(self.palette)
        self.detStatusLabel.setText(txt)  
        
        
    def imgFNameChanged(self):
        """
        Changes the img file name prefix
        """
        self.imgFName=str(self.imgFNameLineEdit.text())
        if self.detectorStatus!=0:
            caput(self.detPV+'FileName',self.imgFName)
            caput(self.detPV.split(':')[0]+':TIFF1:FileName',self.imgFName)
            if self.currentDetector=='PhotonII':
                caput('13PII_1:TIFF1:FileName',self.imgFName)
            
            
    def shutterModeChanged(self):
        """
        Changes the sutter-mode depending upon the selection of the shutterModeCombobox
        """
        caput(self.detPV+'ShutterMode',self.shutterModeComboBox.currentIndex())
        self.shutterMode=self.shutterModeComboBox.currentIndex()
        

    def expTimeChanged(self):
        """
        Changes the exposure time of the detector
        """
        if self.detectorStatus!=0:
            try:
                self.expTime=float(self.expTimeLineEdit.text())
            except:
                QMessageBox.warning(self,'Value Error','Please input numbers only.\n Setting Exposure time to 1.0 s.',QMessageBox.Ok)
                self.expTime=1.0
            caput(self.detPV+'AcquireTime',self.expTime)
            caput(self.detPV+'AcquirePeriod',(self.expTime+0.1))


    def set_det_alignment_mode(self):
        """
        Sets the detector setting in alignment mode in which images will not be saved except the most recent one
        """
        if self.detectorStatus!=0:
            self.imgFNameLineEdit.setText(self.imgFName)
            self.imgFNameChanged()
            caput(self.detPV+'FileNumber', 0)
            #caput(self.detPV.split(':')[0]+':TIFF1:FileNumber', 1)
            caput(self.detPV+'AutoIncrement', 1)
            #caput(self.detPV.split(':')[0]+':TIFF1:AutoIncrement',0)
            #caput(self.detPV+'AutoSave', 1)
            #self.imgModeComboBox.setCurrentIndex(0)
            #caput(self.detPV+'ImageMode', 0)
            caput(self.detPV+'NumImages',1)
            caput(self.detPV.split(':')[0]+':image1:EnableCallbacks',1)
            caput(self.detPV.split(':')[0] + ':image1:BlockingCallbacks',1)
            caput(self.detPV.split(':')[0]+':image1:ArrayCounter',0)
            caput(self.detPV+'ArrayCounter',0)


            #caput(self.detPV+'AcquirePeriod',(self.expTime+0.1))
            #caput(self.detPV.split(':')[0]+':TIFF1:EnableCallbacks',1)
            #caput(self.detPV.split(':')[0] + ':TIFF1:AutoSave', 1)

#    def set_det_experiment_mode(self):
#        """
#        Sets the detector in Experimental mode in which all the images will be saved with a file name and a counter
#        """
#        self.numOfImages=1
#        caput(self.detPV+'FileName', self.imgFName)
#        caput(self.detPV+'FileNumber', self.numOfImages)
#        caput(self.detPV+'AutoIncrement', 1)
#        caput(self.detPV+'AutoSave', 1)
        
        
    def detectorChanged(self):
        """
        Checks and changes the detector
        """
        self.currentDetector=str(self.detectorComboBox.currentText())
        self.detectorStatus=0
        if self.currentDetector!='None':
            self.detPV=self.detectors[self.currentDetector]['PV']
            self.connection=caget(self.detPV+'AsynIO.CNCT',as_string=True)
            if self.connection is None:
                QMessageBox.warning(self,'Detector Error','Please make sure the soft-IOC of the '+self.currentDetector+' is running',QMessageBox.Ok)
            else:
                self.palette.setColor(QPalette.Foreground,Qt.green)
                self.detectorConnectionLabel.setText('Connected')
                self.detectorConnectionLabel.setPalette(self.palette)
                self.detectorStatus=1
                self.set_det_alignment_mode()
                self.detStatusLabel.setText('Done')
                self.detStatusLabel.setPalette(self.palette)
                camonitor(self.detPV+'Acquire',callback=self.getDetectorStatus)
                camonitor(self.detPV.split(':')[0]+':image1:ArrayCounter_RBV',callback=self.onArrayDataUpdate)
                #camonitor(self.detPV+'ArrayCounter_RBV',callback=self.onImageFileUpdate)
                self.expTimeLineEdit.setText(caget(self.detPV+'AcquireTime',as_string=True))
                self.shutterModeChanged()
                self.arrayDataUpdated.connect(self.updateDetectorImage)
                #self.imageFileUpdated.connect(self.updateImageInfo)
                return 1
        else:
            self.palette.setColor(QPalette.Foreground,Qt.red)
            self.detectorConnectionLabel.clear()
            self.detStatusLabel.clear()
            try:
                camonitor_clear(self.detPV+'Acquire')
                camonitor_clear(self.detPV+'DetectorState_RBV')
                camonitor_clear(self.detPV + 'ArrayCounter_RBV')
            except:
                pass
            self.detImgFolderLineEdit.clear()
            self.carsImgFolderLineEdit.clear()
            self.expTimeLineEdit.clear()
            self.sleepTimeLineEdit.clear()

    def onArrayDataUpdate(self,**kwargs):
        self.arrayDataUpdated.emit()

    def onImageFileUpdate(self,**kwargs):
        #QtTest.QTest.qWait(1000)
        self.fileWatcher.fileCreated.connect(self.removePath)
        self.imageFileUpdated.emit()

    def updateDetectorImage(self):
        data = caget(self.detPV.split(':')[0]+':image1:ArrayData')
        if 'Pilatus' in self.currentDetector:
            Ny=caget(self.detPV+'MaxSizeY_RBV')
            Nx=caget(self.detPV+'MaxSizeX_RBV')
        elif 'Mar' in self.currentDetector:
            Ny = caget(self.detPV + 'ArraySizeY_RBV')
            Ny = caget(self.detPV + 'ArraySizeY_RBV')
            Nx = caget(self.detPV + 'ArraySizeX_RBV')
        self.imgData=data.reshape(Ny,Nx)
        #self.imgData = np.rot90(data.reshape(self.detPV+'MaxSizeY_RBV', self.detPV+'MaxSizeX_RBV'), k=1, axes=(0, 1))
        self.imgWidget.setImage(self.imgData+0.001*np.random.random(size=self.imgData.shape), transpose=True)
        QApplication.processEvents()
        self.monitor_counts = caget(self.scalers['monitor']['PV'])
        self.count_time = caget(self.scalers['15IDD_scaler_count_time']['PV'])
        #self.diode_counts = caget(self.scalers['diode']['PV'])
        self.BSdiode_counts = caget(self.scalers['bs_diode']['PV'])
        self.imageFlag=1

    def removePath(self,path):
        os.remove(path)
        self.fileWatcher.fileCreated.disconnect()



    def updateImageInfo(self):
        fname = caget(self.detPV + "FullFileName_RBV", as_string=True)
        fname=fname.replace(self.detImgFolder,self.carsImgFolder)
        #fname = '/mnt/ChemData/Data/Asax/tmp/' + fname.split('/')[-1]
        self.fileWatcher.addNewPath(fname)
        self.fileWatcher.run_new()


            

    def carsImgFolderChanged(self,imgFolder=None):
        """
        Updates the image folder
        """
        if self.detectorStatus!=0:
            if imgFolder is None:
                self.carsImgFolder=str(QFileDialog.getExistingDirectory(self,caption='Select folder',directory=self.detectors[self.currentDetector]['cars_folder'],options=QFileDialog.ShowDirsOnly))
            else:
                self.carsImgFolder=imgFolder
            self.detImgFolder=self.detectors[self.currentDetector]['det_folder']
            #detFolder=self.carsImgFolder.replace(self.detectors[self.currentDetector]['cars_folder'],self.detectors[
            # self.currentDetector]['det_folder'])
            #if self.currentDetector=='Apex2':
            #    detFolder=detFolder.replace('/','\\')
            caput(self.detPV+'FilePath',self.detImgFolder)
            #caput(self.detPV.split(':')[0]+':TIFF1:FilePath',detFolder)
            #if self.currentDetector=='PhotonII':
            #    caput('13PII_1:TIFF1:FilePath',detFolder)
            
            
            self.carsImgFolderLineEdit.setText(self.carsImgFolder)
            self.detImgFolderLineEdit.setText(self.detImgFolder)
            #if self.currentDetector=='Apex2':
            #    imsave(os.path.join(self.carsImgFolder,self.imgFName+'_0001.sfrm'),np.random.random((10,10)))
            #    self.fileWatcher.addPath(os.path.join(self.carsImgFolder,self.imgFName+'_0001.sfrm'))
            #else:
            #    imsave(os.path.join(self.carsImgFolder,self.imgFName+'_0001.tif'),np.random.random((10,10)))
            #    self.fileWatcher.addPath(os.path.join(self.carsImgFolder,self.imgFName+'_0001.tif'))
            #if not self.fileWatcher.isRunning:
            #    self.fileWatcher.run()
        else:
            QMessageBox.warning(self,'Detector Error','Please select a detector first',QMessageBox.Ok)


if __name__=='__main__':
    app=QApplication(sys.argv)
    #detPV='dp_mar165_xrd72:cam1:' #MAR_CCD
    #detPV='15PIL3:cam1:' #Pilatus1M
    #imgFolder='/local/home/dpuser/15idApr2017/2017-04/Test' #MAR_CCD
    #imgFolder='/ramdisk/chemmat/Pilatus1M/Xtal/2017_1/Buffalo/YSC/GLASS' #Pilatus1M

    w=Detector_Widget()
    w.setWindowTitle('Detector Widget')
    screen=QDesktopWidget().screenGeometry()
    w.setGeometry(10,100,800,1600)
    #w.setWindowState(Qt.WindowMaximized)
    w.show()
    sys.exit(app.exec_())

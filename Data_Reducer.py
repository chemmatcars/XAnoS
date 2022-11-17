from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QCheckBox, QSpinBox, QComboBox, QListWidget, QDialog, QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem, QGridLayout, QTabWidget, QGraphicsEllipseItem
from PyQt5.QtGui import QPalette, QPainter
from PyQt5.QtCore import Qt, QPoint, QRectF
import os
import sys
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
#from epics import caput, caget, camonitor
from Setup import Setup
from multiprocessing import Process
from PlotWidget import PlotWidget
import fabio as fb
import time
from numpy import *
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
from Mask_Widget import MaskWidget
from Image_Widget import Image_Widget
from calibrationWidget import CalibrationWidget
import json
import fabio as fb
#from pyFAI.integrate_widget import AIWidget

class cake(pg.ROI):
    """
    """
    def __init__(self, pos=[0,0], rmin=0, rmax=100, amin=0, amax=270,**args):
        pos=pos[0]-rmax/2.0,pos[1]-rmax/2.0
        pg.ROI.__init__(self,pos,size=[2*rmax,2*rmax],**args)
        self.aspectLocked=True
        self.rmin=rmin
        self.rmax=rmax
        self.amin=amin
        self.amax=amax
        self.rminHandle=self.addFreeHandle((pos[0]+rmin*cos(deg2rad(amin)),pos[1]+rmin*sin(deg2rad(amin))))
        self.rmaxHandle=self.addFreeHandle((pos[0]+rmax*cos(deg2rad(amin)),pos[1]+rmax*sin(deg2rad(amin))))
        self.aminHandle=self.addFreeHandle((pos[0]+(rmax+rmin)*cos(deg2rad(amin))/2.0,pos[1]+(rmax+rmin)*sin(deg2rad(amin))/2.0))
        self.amaxHandle=self.addFreeHandle((pos[0]+(rmax+rmin)*cos(deg2rad(amax))/2.0,pos[1]+(rmax+rmin)*sin(deg2rad(amax))/2.0))
        
        
        
#    def paint(self,p,opt,widget):
#        start_angle,end_angle=deg2rad([self.start_angle,self.end_angle])
#        r=self.boundingRect()
#        p.setRenderHint(QPainter.Antialiasing)
#        p.setPen(self.currentPen)
#        p.drawLine(r.x()+r.width()*(0.5+0.05*cos(start_angle)),r.y()+r.height()*(0.5+0.05*sin(start_angle)),r.x()+r.width()*(0.5+0.5*cos(start_angle)),r.y()+r.height()*(0.5+0.5*sin(start_angle)))
#        p.drawArc(r,self.start_angle*16,(self.end_angle-self.start_angle)*16)
#        p.drawLine(r.x()+r.width()*(0.5-0.5*cos(end_angle)),r.y()+r.height()*(0.5-0.5*sin(end_angle)),r.x()+r.width()*(0.5-0.05*cos(end_angle)),r.y()+r.height()*(0.5-0.05*sin(end_angle)))
#        p.drawArc(QRectF(r.x()+r.width()*0.9/2,r.y()+r.height()*0.9/2,r.width()*0.1,r.height()*0.1),self.start_angle*16,(self.end_angle-self.start_angle)*16)
        
    def paint(self,p,*args):
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(self.currentPen)
        p.drawLine(self.rminHandle.pos(),self.rmaxHandle.pos())
        
        
            


class Data_Reducer(QWidget):
    """
    This widget is developed to reduce on the fly 2D SAXS data to azimuthally averaged 1D SAXS data
    """
    def __init__(self,poniFile=None,dataFile=None, darkFile=None, maskFile=None,extractedFolder='/tmp', npt=1000, transmission_corr=True, azimuthRange=(-180.0,180.0), parent=None):
        """
        poniFile is the calibration file obtained after Q-calibration
        """
        QWidget.__init__(self,parent)
        self.layout=QGridLayout(self)
        self.setup_dict=json.load(open('./SetupData/reducer_setup.txt','r'))
        if poniFile is not None:
            self.poniFile=poniFile
        else:
            self.poniFile=self.setup_dict['poniFile']
        if maskFile is not None:
            self.maskFile=maskFile
        else:
            self.maskFile=self.setup_dict['maskFile']
        self.dataFile=dataFile
        if darkFile is None:
            self.dark_corrected=False
            self.darkFile=''
        else:
            self.darkFile=darkFile
            self.dark_corrected=True
       
        self.curDir=os.getcwd()
        
        self.extractedFolder=extractedFolder
        self.npt=npt
        self.set_externally=False
        self.transmission_corr=transmission_corr        
        #ai=AIWidget()
        #self.layout.addWidget(ai)
        self.azimuthRange=azimuthRange
        self.create_UI()
        if os.path.exists(self.poniFile):
            self.openPoniFile(file=self.poniFile)
        if os.path.exists(self.maskFile):
            self.openMaskFile(file=self.maskFile)
        
        
        
        
    def create_UI(self):
        """
        Creates the widget user interface
        """
        row=0
        col=0
        dataFileLabel=QLabel('Data file')
        self.layout.addWidget(dataFileLabel,row,col)
        col+=1
        self.dataFileLineEdit=QLineEdit(self.dataFile)
        self.layout.addWidget(self.dataFileLineEdit,row,col,1,2)
        col+=2
        self.openDataPushButton=QPushButton('Select')
        self.openDataPushButton.clicked.connect(self.openDataFiles)
        self.layout.addWidget(self.openDataPushButton,row,col)
        col+=1
        self.reducePushButton=QPushButton('Reduce data')
        self.reducePushButton.clicked.connect(self.reduce_multiple)
        self.layout.addWidget(self.reducePushButton,row,col,1,1)
        
        row+=1
        col=0
        darkFileLabel=QLabel('Dark file')
        self.layout.addWidget(darkFileLabel,row,col)
        col+=1
        self.darkFileLineEdit=QLineEdit(self.darkFile)
        self.layout.addWidget(self.darkFileLineEdit,row,col,1,2)
        col+=2
        self.openDarkPushButton=QPushButton('Select')
        self.openDarkPushButton.clicked.connect(self.openDarkFile)
        self.layout.addWidget(self.openDarkPushButton,row,col)
        col+=1
        self.darkCheckBox=QCheckBox('Dark Correction')
        self.layout.addWidget(self.darkCheckBox,row,col)
        
        row+=1
        col=0
        poniFileLabel=QLabel('Calibration file')
        self.layout.addWidget(poniFileLabel,row,col)
        col+=1
        self.poniFileLineEdit=QLineEdit(self.poniFile)
        self.layout.addWidget(self.poniFileLineEdit,row,col,1,2)
        col+=2
        self.openPoniPushButton=QPushButton('Select')
        self.openPoniPushButton.clicked.connect(lambda x: self.openPoniFile(file=None))
        self.layout.addWidget(self.openPoniPushButton,row,col)
        col+=1
        self.calibratePushButton=QPushButton('Calibrate')
        self.calibratePushButton.clicked.connect(self.calibrate)
        self.layout.addWidget(self.calibratePushButton,row,col)
        
        row+=1
        col=0
        maskFileLabel=QLabel('Mask file')
        self.layout.addWidget(maskFileLabel,row,col)
        col+=1
        self.maskFileLineEdit=QLineEdit(self.maskFile)
        self.maskFileLineEdit.returnPressed.connect(self.maskFileChanged)
        self.layout.addWidget(self.maskFileLineEdit,row,col,1,2)
        col+=2
        self.openMaskPushButton=QPushButton('Select')
        self.openMaskPushButton.clicked.connect(lambda x: self.openMaskFile(file=None))
        self.layout.addWidget(self.openMaskPushButton,row,col)
        col+=1
        self.createMaskPushButton=QPushButton('Create mask')
        self.createMaskPushButton.clicked.connect(self.createMask)
        self.layout.addWidget(self.createMaskPushButton,row,col)
        
        
        row+=1
        col=0
        extractedFolderLabel=QLabel('Extracted folder')
        self.layout.addWidget(extractedFolderLabel,row,col)
        col+=1
        self.extractedFolderLineEdit=QLineEdit()
        self.layout.addWidget(self.extractedFolderLineEdit,row,col,1,2)
        col+=2
        self.extractedFolderPushButton=QPushButton('Select')
        self.extractedFolderPushButton.clicked.connect(self.openFolder)
        self.layout.addWidget(self.extractedFolderPushButton,row,col)
        
        row+=1
        col=0
        radialPointsLabel=QLabel('Radial Points')
        self.layout.addWidget(radialPointsLabel,row,col)
        col+=1
        self.radialPointsLineEdit=QLineEdit(str(self.npt))
        self.radialPointsLineEdit.returnPressed.connect(self.nptChanged)
        self.layout.addWidget(self.radialPointsLineEdit,row,col)
        col+=1
        azimuthRangeLabel=QLabel('Azimuthal Range (min:max)')
        self.layout.addWidget(azimuthRangeLabel,row,col)
        col+=1
        self.azimuthRangeLineEdit=QLineEdit('%.2f:%.2f'%(self.azimuthRange[0],self.azimuthRange[1]))
        self.azimuthRangeLineEdit.returnPressed.connect(self.azimuthRangeChanged)
        self.layout.addWidget(self.azimuthRangeLineEdit,row,col)
        col+=1
        self.transCorrCheckBox=QCheckBox('Transmission Correction')
        self.transCorrCheckBox.setTristate(False)
        self.transCorrCheckBox.setChecked(self.transmission_corr)
        self.layout.addWidget(self.transCorrCheckBox)
        
        
        row+=1
        col=0
        progressLabel=QLabel('Status')
        self.layout.addWidget(progressLabel,row,col,1,1)
        col+=1
        self.progressBar=QProgressBar()
        self.layout.addWidget(self.progressBar,row,col,1,1)
        col+=1
        self.statusLabel=QLabel('Idle')
        self.layout.addWidget(self.statusLabel,row,col,1,1)
        col+=1
        normLabel=QLabel('Normalized by')
        self.normComboBox=QComboBox()
        self.normComboBox.addItems(['BSDiode','Image sum','Monitor'])
        self.layout.addWidget(normLabel,row,col,1,1)
        col+=1
        self.layout.addWidget(self.normComboBox,row,col,1,1)
        
        row+=1
        col=0
        self.tabWidget=QTabWidget(self)
        self.layout.addWidget(self.tabWidget,row,col,20,5)
        self.imageWidget=Image_Widget(zeros((100,100)))
        imgNumberLabel=QLabel('Image number')
        self.imgNumberSpinBox=QSpinBox()
        self.imgNumberSpinBox.setSingleStep(1)
        self.imageWidget.imageLayout.addWidget(imgNumberLabel,row=2,col=1)
        self.imageWidget.imageLayout.addWidget(self.imgNumberSpinBox,row=2,col=2)
        self.imageView=self.imageWidget.imageView.getView()
        self.plotWidget=PlotWidget()
        self.plotWidget.setXLabel('Q, &#8491;<sup>-1</sup>',fontsize=5)
        self.plotWidget.setYLabel('Intensity',fontsize=5)
        self.tabWidget.addTab(self.plotWidget,'Reduced 1D-data')
        self.tabWidget.addTab(self.imageWidget,'Masked 2D-data')
       
        
        
    def createMask(self):
        """
        Opens a mask-widget to create mask file
        """
        fname=str(QFileDialog.getOpenFileName(self,'Select an image file', directory=self.curDir,filter='Image file (*.edf *.tif)')[0])
        if fname is not None or fname!='':
            img=fb.open(fname).data
            self.maskWidget=MaskWidget(img)
            self.maskWidget.saveMaskPushButton.clicked.disconnect()
            self.maskWidget.saveMaskPushButton.clicked.connect(self.save_mask)
            self.maskWidget.show()
        else:
            QMessageBox.warning(self,'File error','Please import a data file first for creating the mask',QMessageBox.Ok)
            
    def maskFileChanged(self):
        """
        Changes the mask file
        """
        maskFile=str(self.maskFileLineEdit.text())
        if str(maskFile)=='':
            self.maskFile=None
        elif os.path.exists(maskFile):
            self.maskFile=maskFile
        else:
            self.maskFile=None
            
    def save_mask(self):
        """
        Saves the entire mask combining all the shape ROIs
        """
        fname=str(QFileDialog.getSaveFileName(filter='Mask Files (*.msk)')[0])
        name,extn=os.path.splitext(fname)
        if extn=='':
            fname=name+'.msk'
        elif extn!='.msk':
            QMessageBox.warning(self,'File extension error','Please donot provide file extension other than ".msk". Thank you!')
            return
        else:
            tmpfile=fb.edfimage.EdfImage(data=self.maskWidget.full_mask_data.T,header=None)
            tmpfile.save(fname)
            self.maskFile=fname
            self.maskFileLineEdit.setText(self.maskFile)
            
    def calibrate(self):
        """
        Opens a calibartion widget to create calibration file
        """
        fname=str(QFileDialog.getOpenFileName(self,'Select calibration image',directory=self.curDir, filter='Calibration image (*.edf *.tif)')[0])
        if fname is not None:
            img=fb.open(fname).data
            pixel1=172.0
            pixel2=172.0
            self.calWidget=CalibrationWidget(img,pixel1,pixel2)
            self.calWidget.saveCalibrationPushButton.clicked.disconnect()
            self.calWidget.saveCalibrationPushButton.clicked.connect(self.save_calibration)
            self.calWidget.show()
        else:
            QMessageBox.warning(self,'File error','Please import a data file first for creating the calibration file',QMessageBox.Ok)
            
    def save_calibration(self):
        fname=str(QFileDialog.getSaveFileName(self,'Calibration file',directory=self.curDir,filter='Clibration files (*.poni)')[0])
        tfname=os.path.splitext(fname)[0]+'.poni'
        self.calWidget.applyPyFAI()
        self.calWidget.geo.save(tfname)      
        self.poniFile=tfname
        self.poniFileLineEdit.setText(self.poniFile)
        
        
    def openPoniFile(self,file=None):
        """
        Select and imports the calibration file
        """
        if file is None:
            self.poniFile=QFileDialog.getOpenFileName(self,'Select calibration file',directory=self.curDir,filter='Calibration file (*.poni)')[0]
            self.poniFileLineEdit.setText(self.poniFile)
        else:
            self.poniFile=file
        if os.path.exists(self.poniFile):
            self.setup_dict['poniFile']=self.poniFile
            json.dump(self.setup_dict,open('./SetupData/reducer_setup.txt','w'))
            fh=open(self.poniFile,'r')
            lines=fh.readlines()
            self.calib_data={}
            for line in lines:
                if line[0]!='#':
                    key,val=line.split(': ')
                    self.calib_data[key]=float(val)
            self.dist=self.calib_data['Distance']
            self.pixel1=self.calib_data['PixelSize1']
            self.pixel2=self.calib_data['PixelSize2']
            self.poni1=self.calib_data['Poni1']
            self.poni2=self.calib_data['Poni2']
            self.rot1=self.calib_data['Rot1']
            self.rot2=self.calib_data['Rot2']
            self.rot3=self.calib_data['Rot3']
            self.wavelength=self.calib_data['Wavelength']
            self.ai=AzimuthalIntegrator(dist=self.dist,poni1=self.poni1,poni2=self.poni2,pixel1=self.pixel1,pixel2=self.pixel2,rot1=self.rot1,rot2=self.rot2,rot3=self.rot3,wavelength=self.wavelength)
            #pos=[self.poni2/self.pixel2,self.poni1/self.pixel1]
            #self.roi=cake(pos,movable=False)
            #self.roi.sigRegionChangeStarted.connect(self.endAngleChanged)
            
            #self.imageView.addItem(self.roi)
        else:
            QMessageBox.warning(self,'File error','The calibration file '+self.poniFile+' doesnot exists.',QMessageBox.Ok)                
        
    def endAngleChanged(self,evt):
        print(evt.pos())
        
        
    def nptChanged(self):
        """
        Changes the number of radial points
        """
        try:
            self.npt=int(self.radialPointsLineEdit.text())
        except:
            QMessageBox.warning(self,'Value error', 'Please input positive integers only.',QMessageBox.Ok)
            
    def azimuthRangeChanged(self):
        """
        Changes the azimuth angular range
        """
        try:
            self.azimuthRange=tuple(map(float, self.azimuthRangeLineEdit.text().split(':')))
        except:
            QMessageBox.warning(self,'Value error','Please input min:max angles in floating point numbers',QMessageBox.Ok)
        
    def openDataFile(self):
        """
        Select and imports one data file
        """
        dataFile=QFileDialog.getOpenFileName(self,'Select data file',directory=self.curDir,filter='Data file (*.edf *.tif)')[0]
        if dataFile!='':
            self.dataFile=dataFile
            self.curDir=os.path.dirname(self.dataFile)
            self.dataFileLineEdit.setText(self.dataFile)
            self.data2d=fb.open(self.dataFile).data
            if self.darkFile is not None:
                self.applyDark()
            if self.maskFile is not None:
                self.applyMask()    
            self.imageWidget.setImage(self.data2d,transpose=True)
            self.tabWidget.setCurrentWidget(self.imageWidget)
            if not self.set_externally:
                self.extractedFolder=os.path.join(self.curDir,'extracted_pyFAI')
                if not os.path.exists(self.extractedFolder):
                    os.makedirs(self.extractedFolder)
                    
    def openDataFiles(self):
        """
        Selects and imports multiple data files
        """
        self.dataFiles=QFileDialog.getOpenFileNames(self,'Select data files', directory=self.curDir,filter='Data files (*.edf *.tif)')[0]
        if len(self.dataFiles)!=0:
            self.imgNumberSpinBox.valueChanged.connect(self.imageChanged)
            self.imgNumberSpinBox.setMinimum(0)
            self.imgNumberSpinBox.setMaximum(len(self.dataFiles)-1)
            self.dataFileLineEdit.setText(str(self.dataFiles))
            self.curDir=os.path.dirname(self.dataFiles[0])
            self.extractedFolder=os.path.join(self.curDir,'extracted_pyFAI')
            if not os.path.exists(self.extractedFolder):
                os.makedirs(self.extractedFolder)
            self.extractedFolderLineEdit.setText(self.extractedFolder)
            self.imgNumberSpinBox.setValue(0)
            self.imageChanged()
            
    def imageChanged(self):
        self.data2d=fb.open(self.dataFiles[self.imgNumberSpinBox.value()]).data
        if self.darkFile is not None:
            self.applyDark()
        if self.maskFile is not None:
            self.applyMask()    
        self.imageWidget.setImage(self.data2d,transpose=True)
            

                  
            
                
    def applyDark(self):
        if not self.dark_corrected and self.darkFile!='':
            self.dark2d=fb.open(self.darkFile).data
            self.data2d=self.data2d-self.dark2d
            self.dark_corrected=True
                
    def applyMask(self):
        self.mask2d=fb.open(self.maskFile).data
        self.data2d=self.data2d*(1+self.mask2d)/2.0
        self.mask_applied=True

    def openDarkFile(self):
        """
        Select and imports the dark file
        """
        self.darkFile=QFileDialog.getOpenFileName(self,'Select dark file',directory=self.curDir,filter='Dark file (*.edf)')[0]
        if self.darkFile!='':
            self.dark_corrected=False
            self.darkFileLineEdit.setText(self.darkFile)
            if self.dataFile is not None:
                self.data2d=fb.open(self.dataFile).data
                self.applyDark()
        
    
    def openMaskFile(self,file=None):
        """
        Select and imports the Mask file
        """
        if file is None:
            self.maskFile=QFileDialog.getOpenFileName(self,'Select mask file',directory=self.curDir,filter='Mask file (*.msk)')[0]
        else:
            self.maskFile=file
        if self.maskFile!='':
            self.mask_applied=False
            if os.path.exists(self.maskFile):
                self.curDir=os.path.dirname(self.maskFile)
                self.maskFileLineEdit.setText(self.maskFile)
                self.setup_dict['maskFile']=self.maskFile
                self.setup_dict['poniFile']=self.poniFile
                json.dump(self.setup_dict,open('./SetupData/reducer_setup.txt','w'))
            else:
                self.openMaskFile(file=None)
            if self.dataFile is not None:
                self.applyMask()
        else:
            self.maskFile=None
            self.maskFileLineEdit.clear()
            
            
        
    def openFolder(self):
        """
        Select the folder to save the reduce data
        """
        self.extractedFolder=QFileDialog.getExistingDirectory(self,'Select extracted directory',directory=self.curDir)
        if self.extractedFolder!='':
            self.extractedFolderLineEdit.setText(self.extractedFolder)
            self.set_externally=True
        
        
    def reduceData(self):
        """
        Reduces the 2d data to 1d data
        """
        print('Iloveu', self.darkFile)
        if (self.dataFile is not None) and (os.path.exists(self.dataFile)):
            if (self.poniFile is not None) and (os.path.exists(self.poniFile)):
#                self.statusLabel.setText('Busy')
#                self.progressBar.setRange(0, 0)
                imageData=fb.open(self.dataFile)
                #self.data2d=imageData.data
                #if self.maskFile is not None:
                #    self.applyMask()    
                #self.imageWidget.setImage(self.data2d,transpose=True)
                #self.tabWidget.setCurrentWidget(self.imageWidget)
                
                self.header=imageData.header
                try:
                    self.ai.set_wavelength(float(self.header['Wavelength'])*1e-10)
                except:
                    self.ai.set_wavelength(self.wavelength)
                print('Iloveu',self.darkFile)
                if os.path.exists(self.dataFile.split('.')[0]+'_dark.edf') and self.darkCheckBox.isChecked():
                    self.darkFile=self.dataFile.split('.')[0]+'_dark.edf'
                    dark=fb.open(self.darkFile)
                    self.darkFileLineEdit.setText(self.darkFile)
                    imageDark=dark.data                                     
                    self.header['BSDiode_corr']=max([1.0,(float(imageData.header['BSDiode'])-float(dark.header['BSDiode']))])
                    self.header['Monitor_corr']=max([1.0,(float(imageData.header['Monitor'])-float(dark.header['Monitor']))])
                    print("Dark File read from existing dark files")                    
                elif self.darkFile is not None and self.darkFile!='' and self.darkCheckBox.isChecked():
                    dark=fb.open(self.darkFile)
                    imageDark=dark.data                                     
                    self.header['BSDiode_corr']=max([1.0,(float(imageData.header['BSDiode'])-float(dark.header['BSDiode']))])
                    self.header['Monitor_corr']=max([1.0,(float(imageData.header['Monitor'])-float(dark.header['Monitor']))])
                    print("Dark File from memory subtracted")                
                else:
                    imageDark=None
                    try:
                        self.header['BSDiode_corr']=float(imageData.header['BSDiode'])
                        self.header['Monitor_corr']=float(imageData.header['Monitor'])
                    except:
                        self.transCorrCheckBox.setCheckState(Qt.Unchecked)
                    print("No dark correction done")
                if self.transCorrCheckBox.isChecked():
                    if str(self.normComboBox.currentText())=='BSDiode':
                        norm_factor=self.header['BSDiode_corr']#/float(self.header['count_time'])
                    elif str(self.normComboBox.currentText())=='Monitor':
                        norm_factor=self.header['Monitor_corr']
                    else:
                        norm_factor=sum(imageData.data)
                else:
                    norm_factor=1.0
                    
                if self.maskFile is not None:
                    imageMask=fb.open(self.maskFile).data
                else:
                    imageMask=None
                print(self.maskFile)
#                QApplication.processEvents()
                #print(self.azimuthRange)
                self.q,self.I,self.Ierr=self.ai.integrate1d(imageData.data,self.npt,error_model='poisson',mask=imageMask,dark=imageDark,unit='q_A^-1',normalization_factor=norm_factor,azimuth_range=self.azimuthRange)
                self.plotWidget.add_data(self.q,self.I,yerr=self.Ierr,name='Reduced data')
                self.plotWidget.setTitle(self.dataFile,fontsize=2)
#                self.progressBar.setRange(0,100)
#                self.progressBar.setValue(100)
#                self.statusLabel.setText('Idle')
#                QApplication.processEvents()
                self.saveData()
                self.tabWidget.setCurrentWidget(self.plotWidget)
            else:
                QMessageBox.warning(self,'Calibration File Error','Data reduction failed because either no calibration file provided or the provided file or path do not exists',QMessageBox.Ok)
                
        else:
            QMessageBox.warning(self,'Data File Error','No data file provided', QMessageBox.Ok)
            
    def reduce_multiple(self):
        """
        Reduce multiple files
        """
        #try:
        i=0
        self.progressBar.setRange(0,len(self.dataFiles))
        self.progressBar.setValue(i)
        self.statusLabel.setText('Busy')
        for file in self.dataFiles:
            self.dataFile=file
            QApplication.processEvents()
            self.reduceData()
            i=i+1
            self.progressBar.setValue(i)
            QApplication.processEvents()
        self.statusLabel.setText('Idle')
        #except:
        #    QMessageBox.warning(self,'File error','No data files to reduce',QMessageBox.Ok)
        
    def saveData(self):
        """
        saves the extracted data into a file
        """
        if not os.path.exists(self.extractedFolder):
            os.makedirs(self.extractedFolder)
        filename=os.path.join(self.extractedFolder,os.path.splitext(os.path.basename(self.dataFile))[0]+'.txt')
        headers='File extracted on '+time.asctime()+'\n'
        headers='Files used for extraction are:\n'
        headers+='Data file: '+self.dataFile+'\n'
        if self.darkFile is not None:
            headers+='Dark file: '+self.darkFile+'\n'
        else:
            headers+='Dark file: None\n'
        headers+='Poni file: '+self.poniFile+'\n'
        if self.maskFile is not None:
            headers+='mask file: '+self.maskFile+'\n'
        else:
            headers+='mask file: None\n'
        for key in self.header.keys():
            headers+=key+'='+str(self.header[key])+'\n'
        headers+='Q (A^-1)\t\tIntensity\t\tIntensity_err'
        data=vstack((self.q,self.I,self.Ierr)).T
        savetxt(filename,data,header=headers,comments='#')
        
        

                
        
        
        
        
if __name__=='__main__':
    app=QApplication(sys.argv)
    #poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w=Data_Reducer()
    w.setWindowTitle('Data Reducer')
    w.setGeometry(200,200,800,800)
    
    w.show()
    sys.exit(app.exec_())
        

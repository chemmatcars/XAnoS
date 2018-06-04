from pyFAI.geometry import Geometry
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
#from pyFAI.detectors import Detector
#from pyFAI.calibrant import Calibrant
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pyqtgraph.dockarea import *
import pyqtgraph as pg
import sys
import fabio as fb
import numpy as np
import os
from lmfit import Parameters, minimize, report_fit
#from matplotlib import _cntr as cntr
import legacycontour._cntr as cntr 
from Image_Widget import Image_Widget
CWD=os.getcwd()
#CWD=sys.path[0]
CALIBRANT_FOLDER=os.path.join(CWD,'calibrants')

#try:
#    sys.path.append(os.path.abspath(os.path.join(CWD,'Fortran_routines')))
#    from TwoD_Integrate import integrate_2d
#    print('Fortran compiled integrator imported')
#except:
#    if platform.system()=='Windows':
#        if platform.architecture()[0]=='64bit':
#            sys.path.append(os.path.abspath(os.path.join(CWD,'build','lib.win-amd64-3.5')))
#        else:
#            sys.path.append(os.path.abspath(os.path.join(CWD,'build','lib.win32-3.5')))
#    else:
    # sys.path.append(os.path.abspath(os.path.join(CWD,'build','lib.linux-x86_64-3.5')))##

#    from TwoD_Integrate import integrate_2d1 as integrate_2d
#    print('Cython compiled integrator imported')


class CalibrationWidget(QWidget):
    """
    Class to perform all calibration related task for XRTools. This class is heavily dependent on some of the major classes of pyFAI.
    """
    def __init__(self,img,pixel1,pixel2,mask=None,cal=None,dist=1.0,rot1=0.0,rot2=0.0,rot3=0.0,wavelength=1.0,splineFile=None,parent=None):
        """
        (pixel1, pixel2)= pixel dimensions along y and x-axis respectively in microns
        dist= sample to detector distance in meters
        (rot1,rot2,rot3)=rotations in radians
        """
        QWidget.__init__(self,parent)
        self.floatFmt='%.5f'
        self.intFmt='%d'
        self.read_data(img,pixel1,pixel2,mask=mask)            
        self.cal=cal
        self.beamPosX=self.img_hor_Npt/2
        self.beamPosY=self.img_ver_Npt/2
        self.pixel1=pixel1*1e-6
        self.pixel2=pixel2*1e-6
        self.poni1=self.pixel1*self.beamPosY
        self.poni2=self.pixel2*self.beamPosX
        self.dist=dist
        self.rot1=rot1
        self.rot2=rot2
        self.rot3=rot3
        self.wavelength=wavelength
        self.rings={}
        self.splineFile=splineFile
        self.geo=Geometry(dist=self.dist,poni1=self.poni1,poni2=self.poni2,rot1=self.rot1,rot2=self.rot2,rot3=self.rot3,pixel1=self.pixel1,pixel2=self.pixel2,wavelength=self.wavelength*1e-10,splineFile=self.splineFile)
        #self.geo.setChiDiscAtZero()
        self.Fit2D_params=self.geo.getFit2D()
        self.tilt=self.Fit2D_params['tilt']
        self.tiltPlaneRot=self.Fit2D_params['tiltPlanRotation']
        #self.cimgData=self.imgData.T
        
        #Parameters fro Geographical colormap motivated by Fit2D#
        self.colorPos=np.array([0.0,0.17,0.26,0.34,0.51,0.68,0.85,1.0])
        black=[0,0,0,255]
        blue=[0,0,255,255]
        white=[255,255,255,255]
        green=[170,255,0,255]
        yellow=[255,255,0,255]
        orange=[255,170,0,255]
        magenta=[255,85,255,255]
        self.colorVal=np.array([black,blue,white,green,yellow,orange,magenta,white])
           
        self.vblayout=QVBoxLayout(self)
        self.mainDock=DockArea(self,parent)
        self.vblayout.addWidget(self.mainDock)
        
        self.expGeomDock=Dock('Experimental Geometry')
        self.calibrationDock=Dock('Calibration tools')
        self.calibrantDock=Dock('Calibrant Info')
        self.rawImageDock=Dock('Raw image')
        self.SAImageDock=Dock('Solid Angle')
        self.cakedImageDock=Dock('Caked Image')
        
        self.mainDock.addDock(self.expGeomDock,'left')
        self.mainDock.addDock(self.calibrationDock,'left')
        self.mainDock.addDock(self.calibrantDock,'left')
        self.mainDock.addDock(self.rawImageDock,'right')
        self.mainDock.addDock(self.SAImageDock,'right')
        self.mainDock.addDock(self.cakedImageDock,'right')
        self.mainDock.moveDock(self.expGeomDock,'top',self.calibrantDock)
        self.mainDock.moveDock(self.calibrationDock,'bottom',self.calibrantDock)
        self.mainDock.moveDock(self.SAImageDock,'above',self.cakedImageDock)
        self.mainDock.moveDock(self.rawImageDock,'above',self.SAImageDock)
        
        self.create_expGeomDock()        
        self.create_rawImageDock()
        self.create_SAImageDock()
        self.create_calibrantDock()
        self.create_calibrationDock()
        self.create_cakedImageDock()

#        self.solid_angle_plot()
    

    def read_data(self,img,pixel1,pixel2,mask=None):
        self.imgData=img
        self.img_xmin=0
        self.img_xmax=self.imgData.shape[0]
        self.img_hor_Npt=self.imgData.shape[0]
        self.img_ymin=0
        self.img_ver_Npt=self.imgData.shape[1]
        self.img_ymax=self.imgData.shape[1]
        self.pixel1=pixel1*1e-6
        self.pixel2=pixel2*1e-6
        if mask is not None:
            if img.shape==mask.shape:
                self.maskData=mask
                self.imgData=np.where(self.maskData<0,0.0,self.imgData)
            else:
                self.maskData=None
                QMessageBox.warning(self,'Mask error','The mask shape doesnot match the image shape',QMessageBox.Ok)
        else:
            self.maskData=np.ones_like(self.imgData)
        #self.cimgData=self.imgData.T
        self.SA_imgData=np.ones(self.imgData.shape)
        try:
            self.calibrant_changed()
            self.rawImageWidget.setImage(self.imgData,transpose=True)#imageLogLinear()
            self.SAImageWidget.setImage(self.SA_imgData,transpose=True)
        except:
            pass
        self.X, self.Y= np.meshgrid(np.arange(self.imgData.shape[1]),np.arange(self.imgData.shape[0]))
        
    def pixel2QMap(self):
        """
        Maps the pixel of the detector to reciprocal space in inverse Angstroms
        """
        self.geo.set_dist(self.dist)
        self.geo.set_poni1(self.poni1)
        self.geo.set_poni2(self.poni2)
        self.geo.set_rot1(self.rot1)
        self.geo.set_rot2(self.rot2)
        self.geo.set_rot3(self.rot3)
        self.geo.set_pixel1(self.pixel1)
        self.geo.set_pixel2(self.pixel2)
        self.geo.set_wavelength(self.wavelength*1e-10)
        self.chi=self.geo.chiArray(self.imgData.shape)
        self.tth=self.geo.twoThetaArray(self.imgData.shape)
        self.q=self.geo.qArray(self.imgData.shape)/10
        #self.rawImageLogLinear()
        
#    def show_cal_ring(self,ring_num):
#        """
#        Show the calibration ring corresponding to the ring number using pyqtgraph's IsoCurveItem which is very slow
#        """
#        bins=self.binSize
#        try:
#            self.rings[ring_num].setData(self.q[::bins,::bins],self.cal_qvals[ring_num])
#        except:
#            self.rings[ring_num]=pg.IsocurveItem(data=self.q[::bins,::bins],level=self.cal_qvals[ring_num],axisOrder='row-major',pen=pg.mkPen(color=self.calRingColorButton.color(),width=int(self.calRingWidthLineEdit.text())))
#           self.rings[ring_num].setParentItem(self.rawImageWidget.imageView.getImageItem())
#            self.rings[ring_num].setScale(bins*1.0)


    def show_cal_ring(self,ring_num):
        """
        Show the calibration ring corresponding to the ring number using matploblib's _cntr methods which is known to be two orders of magnitude faster
        """
        #bins=self.binSize
        c=cntr.Cntr(self.X,self.Y,self.q)
        nlist=c.trace(self.cal_qvals[ring_num])
        pen=pg.mkPen(color=self.calRingColorButton.color(),width=int(self.calRingWidthLineEdit.text()))
        if nlist!=[]:
            tlist=np.vstack(nlist[:len(nlist)//2])
            x=tlist[:,0]-self.beamPosX
            y=tlist[:,1]-self.beamPosY
            r=np.sqrt(x**2+y**2)
            phi=(np.pi+np.sign(y)*(np.arccos(x/r)-np.pi))*180/np.pi
            sortedargs=np.argsort(phi)
            tlist=tlist[sortedargs[1:-1],:]
            try:
                self.rings[ring_num].setData(tlist)
            except:
                self.rings[ring_num]=pg.PlotDataItem(tlist,pen=pen,connect='pairs')
                #self.rawImageWidget.imageView.getView().addItem(self.rings[ring_num])
                self.rawImageWidget.imageView.getView().addItem(self.rings[ring_num])

       
    def ring_color_width_changed(self):
        try:
            for key in self.rings.keys():
                self.rings[key].setPen(pg.mkPen(color=self.calRingColorButton.color(),width=int(self.calRingWidthLineEdit.text())))
        except:
            QMessageBox.warning(self,'Value error','Please input positive integer as Ring width',QMessageBox.Ok)
            self.calRingWidthLineEdit.setText('2')
        
    def create_expGeomDock(self):
        """
        Creating the experimental geometry dock
        """        
        row=0
        self.expGeomLayout=pg.LayoutWidget()
        wavelengthLabel=QLabel('Wavelength (Angs)')
        self.expGeomLayout.addWidget(wavelengthLabel,row=row,col=0)
        self.wavelengthLineEdit=QLineEdit(self.floatFmt%self.wavelength)
        self.expGeomLayout.addWidget(self.wavelengthLineEdit,row=row,col=1)
        energyLabel=QLabel('Energy (keV)')
        self.expGeomLayout.addWidget(energyLabel,row=row,col=2)
        self.energy=6.625e-34*3e8/self.wavelength/1e-10/1.602e-19/1e3
        self.energyLineEdit=QLineEdit(self.floatFmt%self.energy)
        self.expGeomLayout.addWidget(self.energyLineEdit,row=row,col=3)
        self.wavelengthLineEdit.returnPressed.connect(self.wavelengthToEnergy)
        self.energyLineEdit.returnPressed.connect(self.energyToWavelength)
        tiltLabel=QLabel('Tilt (degrees)')
        self.tiltLineEdit=QLineEdit(self.floatFmt%self.tilt)
        self.tiltLineEdit.returnPressed.connect(self.applyFit2D)
        self.expGeomLayout.addWidget(tiltLabel,row=row,col=4)
        self.expGeomLayout.addWidget(self.tiltLineEdit,row=row,col=5)
        
        row=row+1
        
        pixel2Label=QLabel('Pixel X size (microns)')
        self.pixel2LineEdit=QLineEdit('%.2f'%(self.pixel2*1e6))
        self.pixel2LineEdit.returnPressed.connect(self.detectorPixelChanged)
        pixel1Label=QLabel('Pixel Y size (microns)')
        self.pixel1LineEdit=QLineEdit('%.2f'%(self.pixel1*1e6))
        self.pixel1LineEdit.returnPressed.connect(self.detectorPixelChanged)
        tiltPlaneRotLabel=QLabel('Tilt Plane Rot (degrees)')
        self.tiltPlaneRotLineEdit=QLineEdit(self.floatFmt%self.tiltPlaneRot)
        self.tiltPlaneRotLineEdit.returnPressed.connect(self.applyFit2D)
        self.expGeomLayout.addWidget(pixel2Label,row=row,col=0)
        self.expGeomLayout.addWidget(self.pixel2LineEdit,row=row,col=1)
        self.expGeomLayout.addWidget(pixel1Label,row=row,col=2)
        self.expGeomLayout.addWidget(self.pixel1LineEdit,row=row,col=3)
        self.expGeomLayout.addWidget(tiltPlaneRotLabel,row=row,col=4)
        self.expGeomLayout.addWidget(self.tiltPlaneRotLineEdit,row=row,col=5)
        
        row=row+1
        
        beamPosXLabel=QLabel('Beam Pos X (Pixel #)')
        self.expGeomLayout.addWidget(beamPosXLabel,row=row,col=0)
        self.beamPosXLineEdit=QLineEdit('%.2f'%self.beamPosX)
        self.beamPosXLineEdit.returnPressed.connect(self.applyFit2D)
        self.expGeomLayout.addWidget(self.beamPosXLineEdit,row=row,col=1)
        beamPosYLabel=QLabel('Beam Pos Y (Pixel #)')
        self.expGeomLayout.addWidget(beamPosYLabel,row=row,col=2)
        self.beamPosYLineEdit=QLineEdit('%.2f'%self.beamPosY)
        self.beamPosYLineEdit.returnPressed.connect(self.applyFit2D)
        self.expGeomLayout.addWidget(self.beamPosYLineEdit,row=row,col=3)
        self.getBeamPosPushButton=QPushButton('Get Beam Pos')
        self.getBeamPosPushButton.clicked.connect(self.getBeamPos)
        self.expGeomLayout.addWidget(self.getBeamPosPushButton,row=row,col=4)
        self.DBColorButton=pg.ColorButton(color='r')
        self.DBColorButton.sigColorChanging.connect(self.applyFit2D)
        self.DBColorButton.sigColorChanged.connect(self.applyFit2D)
        self.expGeomLayout.addWidget(self.DBColorButton,row=row,col=5)
        
        
        row=row+1
        
        self.sample2DetDistCheckBox=QCheckBox('Sam-Det dist (m)')
        self.sample2DetDistCheckBox.setTristate(on=False)
        self.sample2DetDistCheckBox.setCheckState(Qt.Checked)
        self.sample2DetDistLineEdit=QLineEdit(self.floatFmt%self.dist)
        self.sample2DetDistLineEdit.returnPressed.connect(self.applyPyFAI)
        self.expGeomLayout.addWidget(self.sample2DetDistCheckBox,row=row,col=0)
        self.expGeomLayout.addWidget(self.sample2DetDistLineEdit,row=row,col=1)        
        self.poni1CheckBox=QCheckBox('Poni1 (m)')
        self.poni1CheckBox.setTristate(on=False)
        self.poni1CheckBox.setCheckState(Qt.Checked)
        self.poni1LineEdit=QLineEdit(self.floatFmt%self.poni1)
        self.poni1LineEdit.returnPressed.connect(self.applyPyFAI)
        #self.poni1LineEdit.setReadOnly(True)
        self.poni2CheckBox=QCheckBox('Poni2 (m)')
        self.poni2CheckBox.setTristate(on=False)
        self.poni2CheckBox.setCheckState(Qt.Checked)
        self.poni2LineEdit=QLineEdit(self.floatFmt%self.poni2)
        self.poni2LineEdit.returnPressed.connect(self.applyPyFAI)
        #self.poni2LineEdit.setReadOnly(True)
        self.expGeomLayout.addWidget(self.poni1CheckBox,row=row,col=2)
        self.expGeomLayout.addWidget(self.poni1LineEdit,row=row,col=3)
        self.expGeomLayout.addWidget(self.poni2CheckBox,row=row,col=4)
        self.expGeomLayout.addWidget(self.poni2LineEdit,row=row,col=5)
        
        row=row+1
        
        self.rot1CheckBox=QCheckBox('Rot1 (radians)')
        self.rot1CheckBox.setTristate(on=False)
        self.rot1CheckBox.setCheckState(Qt.Unchecked)
        self.rot1LineEdit=QLineEdit(self.floatFmt%self.rot1)
        self.rot1LineEdit.returnPressed.connect(self.applyPyFAI)
        self.rot2CheckBox=QCheckBox('Rot2 (radians)')
        self.rot2CheckBox.setTristate(on=False)
        self.rot2CheckBox.setCheckState(Qt.Unchecked)
        self.rot2LineEdit=QLineEdit(self.floatFmt%self.rot2)
        self.rot2LineEdit.returnPressed.connect(self.applyPyFAI)
        self.rot3CheckBox=QCheckBox('Rot3 (radians)')
        self.rot3CheckBox.setTristate(on=False)
        self.rot3CheckBox.setCheckState(Qt.Unchecked)
        self.rot3LineEdit=QLineEdit(self.floatFmt%self.rot3)
        self.rot3LineEdit.returnPressed.connect(self.applyPyFAI)
        self.expGeomLayout.addWidget(self.rot1CheckBox,row=row,col=0)
        self.expGeomLayout.addWidget(self.rot1LineEdit,row=row,col=1)
        self.expGeomLayout.addWidget(self.rot2CheckBox,row=row,col=2)
        self.expGeomLayout.addWidget(self.rot2LineEdit,row=row,col=3)
        self.expGeomLayout.addWidget(self.rot3CheckBox,row=row,col=4)
        self.expGeomLayout.addWidget(self.rot3LineEdit,row=row,col=5)        
        self.expGeomDock.addWidget(self.expGeomLayout)
        
        
    def detectorPixelChanged(self):
        """
        The pixel size of the detectors changed
        """
        self.pixel1=float(self.pixel1LineEdit.text())*1e-6
        self.pixel2=float(self.pixel2LineEdit.text())*1e-6
        self.geo.set_pixel1(self.pixel1)
        self.geo.set_pixel2(self.pixel2)
        self.applyPyFAI()
        
        
    def applyFit2D(self):
        #try:
            self.tilt=float(self.tiltLineEdit.text())
            self.tiltLineEdit.setText(self.floatFmt%self.tilt)
            self.tiltPlaneRot=float(self.tiltPlaneRotLineEdit.text())
            self.tiltPlaneRotLineEdit.setText(self.floatFmt%self.tiltPlaneRot)
            self.beamPosX=float(self.beamPosXLineEdit.text())
            self.beamPosXLineEdit.setText('%.2f'%self.beamPosX)
            self.beamPosY=float(self.beamPosYLineEdit.text())
            self.beamPosYLineEdit.setText('%.2f'%self.beamPosY)
            self.dist=float(self.sample2DetDistLineEdit.text())
            self.geo.setFit2D(self.dist*1e3,self.beamPosX,self.beamPosY,tilt=self.tilt,tiltPlanRotation=self.tiltPlaneRot)
            self.poni1=self.geo.get_poni1()
            self.poni1LineEdit.setText(self.floatFmt%self.poni1)
            self.poni2=self.geo.get_poni2()
            self.poni2LineEdit.setText(self.floatFmt%self.poni2)
            self.rot1=self.geo.get_rot1()
            self.rot1LineEdit.setText(self.floatFmt%self.rot1)
            self.rot2=self.geo.get_rot2()
            self.rot2LineEdit.setText(self.floatFmt%self.rot2)
            self.rot3=self.geo.get_rot3()
            self.rot3LineEdit.setText(self.floatFmt%self.rot3)
            self.directBeam.setData([self.beamPosX],[self.beamPosY],symbol='+',symbolPen=pg.mkPen(color=self.DBColorButton.color()),symbolBrush=pg.mkBrush(color=self.DBColorButton.color()),symbolSize=10)
            self.SAdirectBeam.setData([self.beamPosX],[self.beamPosY],symbol='+',symbolPen=pg.mkPen(color=self.DBColorButton.color()),symbolBrush=pg.mkBrush(color=self.DBColorButton.color()),symbolSize=10)
            self.pixel2QMap()
            self.calibration_peak_selection_changed()
            self.solid_angle_plot()
        #except:
        #    self.beamPosXLineEdit.setText('%.2f'%self.beamPosX)
        #    self.beamPosYLineEdit.setText('%.2f'%self.beamPosY)
        #    self.poni1LineEdit.setText(self.floatFmt%self.poni1)
        #    self.poni2LineEdit.setText(self.floatFmt%self.poni2)
        #    self.rot1LineEdit.setText(self.floatFmt%self.rot1)
        #    self.rot2LineEdit.setText(self.floatFmt%self.rot2)
        #    self.rot3LineEdit.setText(self.floatFmt%self.rot3)
        #    QMessageBox.warning(self,'Value Error','Please input integers as Beam Pos X and Beam Pos Y',QMessageBox.Ok)
            
    def applyPyFAI(self):
    #def rotation_changed(self):
        try:
            self.dist=float(self.sample2DetDistLineEdit.text())
            self.sample2DetDistLineEdit.setText(self.floatFmt%self.dist)
            self.poni1=float(self.poni1LineEdit.text())
            self.poni1LineEdit.setText(self.floatFmt%self.poni1)
            self.poni2=float(self.poni2LineEdit.text())
            self.poni2LineEdit.setText(self.floatFmt%self.poni2)
            self.rot1=float(self.rot1LineEdit.text())
            self.rot1LineEdit.setText(self.floatFmt%self.rot1)
            self.rot2=float(self.rot2LineEdit.text())
            self.rot2LineEdit.setText(self.floatFmt%self.rot2)
            self.rot3=float(self.rot3LineEdit.text())
            self.rot3LineEdit.setText(self.floatFmt%self.rot3)
            self.pixel2QMap()
            self.Fit2D_params=self.geo.getFit2D()
            self.beamPosX=self.Fit2D_params['centerX']
            self.beamPosY=self.Fit2D_params['centerY']
            self.directBeam.setData([self.beamPosX],[self.beamPosY],symbol='+',symbolPen=pg.mkPen(color=self.DBColorButton.color()),symbolBrush=pg.mkBrush(color=self.DBColorButton.color()),symbolSize=10)
            self.tilt=self.Fit2D_params['tilt']
            self.tiltPlaneRot=self.Fit2D_params['tiltPlanRotation']
            self.beamPosXLineEdit.setText('%.2f'%self.beamPosX)
            self.beamPosYLineEdit.setText('%.2f'%self.beamPosY)
            self.tiltLineEdit.setText(self.floatFmt%self.tilt)
            self.tiltPlaneRotLineEdit.setText(self.floatFmt%self.tiltPlaneRot)            
            self.calibration_peak_selection_changed()
            self.solid_angle_plot()
        except:
            self.sample2DetDistLineEdit.setText(self.floatFmt%self.dist)
            self.poni1LineEdit.setText(self.floatFmt%self.poni1)
            self.poni2LineEdit.setText(self.floatFmt%self.poni2)
            self.rot1LineEdit.setText(self.floatFmt%self.rot1)
            self.rot2LineEdit.setText(self.floatFmt%self.rot2)
            self.rot3LineEdit.setText(self.floatFmt%self.rot3)
            self.beamPosXLineEdit.setText('%.2f'%self.beamPosX)
            self.beamPosYLineEdit.setText('%.2f'%self.beamPosY)
            self.tiltLineEdit.setText(self.floatFmt%self.tilt)
            self.tiltPlaneRotLineEdit.setText(self.floatFmt%self.tiltPlaneRot)
            QMessageBox.warning(self,'Value Error','Please input floating point numbers only',QMessageBox.Ok)
        
        
        
    def create_rawImageDock(self):
        """
        Creates the image dock
        """
        self.rawImageWidget=Image_Widget(self.imgData,transpose=True)
        self.rawImageDock.addWidget(self.rawImageWidget)
        self.directBeam=pg.PlotDataItem([self.beamPosX],[self.beamPosY],symbol='+',symbolPen=pg.mkPen(color=self.DBColorButton.color()),symbolBrush=pg.mkBrush(color=self.DBColorButton.color()),symbolSize=10)
        self.rawImageWidget.imageView.getView().addItem(self.directBeam)
        
    def create_SAImageDock(self):
        """
        Creates the image dock
        """
        self.SAImageWidget=Image_Widget(self.SA_imgData,transpose=True)
        self.SAImageDock.addWidget(self.SAImageWidget)
        self.SAdirectBeam=pg.PlotDataItem([self.beamPosX],[self.beamPosY],symbol='+',symbolPen=pg.mkPen(color=self.DBColorButton.color()),symbolBrush=pg.mkBrush(color=self.DBColorButton.color()),symbolSize=10)
        self.SAImageWidget.imageView.getView().addItem(self.SAdirectBeam)
        
        
    def create_cakedImageDock(self):
        """
        Creates the image dock
        """
        self.cakedImageWidget=Image_Widget(self.SA_imgData,transpose=True)
        self.cakedImageDock.addWidget(self.cakedImageWidget)
        
        
    def create_calibrantDock(self):
        """
        Creates the calibrantDock
        """
        self.calibrantLayout=pg.LayoutWidget()
        calibrantLabel=QLabel('Calibrants')
        self.calibrantComboBox=QComboBox()
        self.calibrants=os.listdir(CALIBRANT_FOLDER)
        self.calibrants.sort(key=str.lower)
        self.calibrants.append('New')
        self.calibrantComboBox.addItems(self.calibrants)
        if self.cal is not None:
            self.cal_index=self.calibrantComboBox.findText(self.cal,flags=Qt.MatchExactly|Qt.MatchCaseSensitive)
        else:
            self.cal_index=0
        self.calibrantComboBox.setCurrentIndex(self.cal_index)
        self.calibrantComboBox.currentIndexChanged.connect(self.calibrant_changed)
        self.saveCalPushButton=QPushButton('Save calibrant')
        self.saveCalPushButton.clicked.connect(self.save_calibrant)
        #binSizeLabel=QLabel('Binning size')
        #self.binSizeLineEdit=QLineEdit('1')
        #self.binSizeLineEdit.returnPressed.connect(self.binSizeChanged)
        calColorLabel=QLabel('Ring color')
        self.calRingColorButton=pg.ColorButton(color='r')
        self.calRingColorButton.sigColorChanging.connect(self.ring_color_width_changed)
        self.calRingColorButton.sigColorChanged.connect(self.ring_color_width_changed)
        calRingWidthLabel=QLabel('Ring width')
        self.calRingWidthLineEdit=QLineEdit('2')
        self.calRingWidthLineEdit.returnPressed.connect(self.ring_color_width_changed)
        self.calibrantLayout.addWidget(calibrantLabel,row=0,col=0)
        self.calibrantLayout.addWidget(self.calibrantComboBox,row=0,col=1)
        self.calibrantLayout.addWidget(self.saveCalPushButton,row=0,col=2)
        #self.calibrantLayout.addWidget(binSizeLabel,row=0,col=3)
        #self.calibrantLayout.addWidget(self.binSizeLineEdit,row=0,col=4)
        self.calibrantLayout.addWidget(calColorLabel,row=0,col=5)
        self.calibrantLayout.addWidget(self.calRingColorButton,row=0,col=6)
        self.calibrantLayout.addWidget(calRingWidthLabel,row=0,col=7)
        self.calibrantLayout.addWidget(self.calRingWidthLineEdit,row=0,col=8)
        
        self.calibrantTextEdit=QTextEdit()
        self.calibrantListWidget=QListWidget()
        self.calibrantListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.calibrantListWidget.itemSelectionChanged.connect(self.calibration_peak_selection_changed)
        self.calibrant_changed()
        self.calibrantLayout.addWidget(self.calibrantTextEdit,row=1,col=0,colspan=4)
        self.calibrantLayout.addWidget(self.calibrantListWidget,row=1,col=4,colspan=5)        
        self.calibrantDock.addWidget(self.calibrantLayout)

#    def binSizeChanged(self):
#        try:
#            self.binSize=int(self.binSizeLineEdit.text())
#            self.calibration_peak_selection_changed()
#        except:
#            QMessageBox.warning(self,'Value Error','Please enter integers only >= 1. Now using 3.',QMessageBox.Ok)
#            self.binSizeLineEdit.setText('3')
#            self.binSize=3
#            self.calibration_peak_selection_changed()

        
            
    def calibrant_changed(self):
        if str(self.calibrantComboBox.currentText())!='New':
            self.calibrantTextEdit.clear()
            self.calibrantListWidget.clear()
            self.cal=str(self.calibrantComboBox.currentText())
            calfile=os.path.join(CALIBRANT_FOLDER,self.cal)
            fh=open(calfile,'r')
            lines=fh.readlines()
            self.cal_dvals={}
            self.cal_qvals={}
            i=0
            for line in lines:
                self.calibrantTextEdit.append(line[:-1])
                if line[0]!='#':
                  self.cal_dvals[i]=float(line.split()[0])
                  self.cal_qvals[i]=2*np.pi/self.cal_dvals[i]
                  self.calibrantListWidget.addItem('Peak %d: d=%.3f Angs, q=%.3f inv Angs '%(i,self.cal_dvals[i],self.cal_qvals[i]))
                  #self.calibrantListWidget.setItemWidget(self.calibrantListWidget.item(i),QCheckBox('Peak %d'%i))
                  i=i+1
            self.pixel2QMap()
            self.calibrantListWidget.item(0).setSelected(True)
            #self.show_cal_ring(self.calibrantListWidget.selectedItems()[0])
        else:
            self.calibrantTextEdit.clear()
            self.calibrantListWidget.clear()
            for key in self.rings.keys():
                self.rawImageWidget.imageView.getImageItem().scene().removeItem(self.rings[key])
            self.rings={}
            self.calibrantTextEdit.append('# Calibrant:')
            self.calibrantTextEdit.append('# Lattice parameters: a=    ,b=    ,c=   ')
            self.calibrantTextEdit.append('# Ref:')
            
    def calibration_peak_selection_changed(self):
        try:
            for key in self.rings.keys():
                self.rawImageWidget.imageView.getImageItem().scene().removeItem(self.rings[key])
            self.rings={}
        except:
            pass
        for item in self.calibrantListWidget.selectedItems():
            self.show_cal_ring(self.calibrantListWidget.row(item))
    
            
            
    
    def save_calibrant(self):
        fname=QFileDialog.getSaveFileName(self,'Provide a filename for the calibrant',directory=os.path.join(CWD,'calibrants'),filter='Calibrant file (*.D)')[0]
        if fname[-2:]!='.D':
            fname=fname+'.D'
        with open(fname,'w') as tfile:
            tfile.write(str(self.calibrantTextEdit.toPlainText()))
        self.calibrants=os.listdir(CALIBRANT_FOLDER)
        self.calibrants.sort(key=str.lower)
        self.calibrants.append('New')
        self.calibrantComboBox.addItems(self.calibrants)
        self.cal_index=self.calibrantComboBox.findText(os.path.basename(fname))
        self.calibrantComboBox.setCurrentIndex(self.cal_index)
        
    def create_calibrationDock(self):
        self.calibrationLayout=pg.LayoutWidget()
        peakNumberLabel=QLabel('Peak #')
        self.peakNumberSpinBox=pg.SpinBox(value=0,bounds=(0,self.calibrantListWidget.count()-1),int=True,step=1)
        #self.peakNumberSpinBox.valueChanged.connect(self.addPoints)
        pickerLabel=QLabel('Picker')
        self.pickerComboBox=QComboBox()
        self.pickerComboBox.addItems(['Nearest-Max','Cen-of-Mass','None'])
        winLabel=QLabel('Search Window')
        self.searchWinLineEdit=QLineEdit('20')
        self.win_changed()
        self.searchWinLineEdit.returnPressed.connect(self.win_changed)
        self.pickPointsPushButton=QPushButton('Pick Points')
        self.pickPointsPushButton.clicked.connect(self.pick_points)
        self.removePointsPushButton=QPushButton('Remove points')
        self.removePointsPushButton.clicked.connect(self.removePoints)
        self.pointTreeWidget=QTreeWidget()
        self.pointTreeWidget.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.pointTreeWidget.setColumnCount(2)
        self.pointTreeWidget.header().setResizeMode(pg.QtGui.QHeaderView.ResizeToContents)
        self.pointTreeWidget.header().setStretchLastSection(False)
        self.calibratePushButton=QPushButton('Calibrate')
        self.calibratePushButton.clicked.connect(self.calibrate)
        self.showChiPlotPushButton=QPushButton('Chi-Plot')
        self.showChiPlotPushButton.clicked.connect(self.chi_plot)
        self.showSolidAnglePushButton=QPushButton('Solid-Angle')
        self.showSolidAnglePushButton.clicked.connect(self.show_solid_angle)
        self.checkCalibrationPushButton=QPushButton('Check Calibration')
        self.checkCalibrationPushButton.clicked.connect(self.checkCalibration)
        self.saveCalibrationPushButton=QPushButton('Save Calibration')
        self.saveCalibrationPushButton.clicked.connect(self.save_calibration)
        self.calibrationLayout.addWidget(peakNumberLabel,row=0,col=0)
        self.calibrationLayout.addWidget(self.peakNumberSpinBox,row=0,col=1)
        self.calibrationLayout.addWidget(pickerLabel,row=0,col=2)
        self.calibrationLayout.addWidget(self.pickerComboBox,row=0,col=3)
        self.calibrationLayout.addWidget(winLabel,row=0,col=4)
        self.calibrationLayout.addWidget(self.searchWinLineEdit,row=0,col=5)
        self.calibrationLayout.addWidget(self.pickPointsPushButton,row=0,col=6)
        self.calibrationLayout.addWidget(self.removePointsPushButton,row=0,col=7)
        self.calibrationLayout.addWidget(self.pointTreeWidget,row=1,col=0,colspan=8)
        self.calibrationLayout.addWidget(self.calibratePushButton,row=2,col=0,colspan=2)
        self.calibrationLayout.addWidget(self.showChiPlotPushButton,row=2,col=2)
        self.calibrationLayout.addWidget(self.showSolidAnglePushButton,row=2,col=3)
        self.calibrationLayout.addWidget(self.checkCalibrationPushButton,row=2,col=4)
        self.calibrationLayout.addWidget(self.saveCalibrationPushButton,row=2,col=5) 
        self.calibrationDock.addWidget(self.calibrationLayout)
        self.pointTreeWidgetItems={}
        self.points={}
        self.pointsPlotItems={}
        self.pointColorWidget={}
        
    def checkCalibration(self):
        """
        After calibration is done performs caking of the calibrant image to check the goodness of calibration
        """
        ai=AzimuthalIntegrator(dist=self.dist,poni1=self.poni1,poni2=self.poni2,rot1=self.rot1,rot2=self.rot2,rot3=self.rot3,pixel1=self.pixel1,pixel2=self.pixel2,wavelength=self.wavelength*1e-10,splineFile=self.splineFile)
        cakedArray,qr,phir=ai.integrate2d(self.imgData,1000,error_model='poisson',mask=self.maskData,dark=None,unit='q_A^-1')
        xmin=qr[0]
        xmax=qr[-1]
        ymin=phir[0]
        ymax=phir[-1]
        self.cakedImageWidget.setImage(cakedArray,xmin=xmin,xmax=xmax,ymin=ymin,ymax=ymax,transpose=True)
        self.cakedImageWidget.imageView.view.setAspectLocked(False)
        i=0
        pen=pg.mkPen(color=self.calRingColorButton.color(),width=int(self.calRingWidthLineEdit.text()))
        line={}
        while self.cal_qvals[i]<xmax:
            line[i]=pg.InfiniteLine(pos=self.cal_qvals[i],angle=90,movable=False,pen=pen)
            self.cakedImageWidget.imageView.getView().addItem(line[i])
            i+=1
        self.mainDock.moveDock(self.cakedImageDock,'above',self.rawImageDock)
        
        
    def pick_points(self):
        try:
            self.rawImageWidget.imageView.getView().vb.scene().sigMouseClicked.disconnect()
        except:
            pass
        self.rawImageWidget.imageView.getView().vb.scene().sigMouseClicked.connect(self.points_picked)
        self.pickPointsPushButton.setEnabled(False)
        self.timer=QTimer()
        self.timer.timeout.connect(self.pick_points_disabled)
        self.timer.start(20000)
        
    def pick_points_disabled(self):
        try:
            self.rawImageWidget.imageView.getView().vb.scene().sigMouseClicked.disconnect(self.points_picked)
        except:
            pass
        self.pickPointsPushButton.setEnabled(True)
        
    
    def points_picked(self,evt):
        val=self.peakNumberSpinBox.value()
        try:
            for key in self.pointTreeWidgetItems.keys():
                self.pointTreeWidgetItems[key].setExpanded(False)
            self.pointTreeWidget.setCurrentItem(self.pointTreeWidgetItems[val])
        except:
            self.points[val]=[]
            self.pointTreeWidgetItems[val]=QTreeWidgetItem(['Peak %d'%val])
            self.pointTreeWidget.addTopLevelItem(self.pointTreeWidgetItems[val])
            self.pointColorWidget[val]=pg.ColorButton(color=np.random.randint(256,size=4))
            self.pointColorWidget[val].sigColorChanging.connect(self.updatePoints)
            self.pointColorWidget[val].sigColorChanged.connect(self.updatePoints)
            self.pointTreeWidget.setItemWidget(self.pointTreeWidgetItems[val],1,self.pointColorWidget[val])
            self.pointsPlotItems[val]=pg.PlotDataItem(symbol='o',symbolSize=10,symbolBrush=pg.mkBrush(color=self.pointColorWidget[val].color()),pen=None)
            self.rawImageWidget.imageView.getView().addItem(self.pointsPlotItems[val])
        if evt.button()==Qt.LeftButton:
            self.timer.stop()
            self.timer.start(20000)
            pos=self.rawImageWidget.imageView.getImageItem().mapFromScene(evt.scenePos())
            x1=pos.x()
            y1=pos.y()
            Nx,Ny=self.imgData.T.shape
            if (0<=x1<=Nx) and (0<=y1<=Ny):        
                x,y=self.peak_search(x1,y1,method=str(self.pickerComboBox.currentText()))
                self.pointTreeWidgetItems[val].setExpanded(True)
                self.pointTreeWidgetItems[val].addChild(QTreeWidgetItem(['[%.2f,%.2f]'%(x,y)]))
                self.points[val].append([x,y])
                self.pointsPlotItems[val].setData(np.array(self.points[val]),symbol='o',symbolSize=10,symbolBrush=pg.mkBrush(color=self.pointColorWidget[val].color()),pen=None)
            else:
                QMessageBox.warning(self,'Click Error','Please click inside the image',QMessageBox.Ok)
            
            
    def win_changed(self):
        try:
            self.win=int(int(self.searchWinLineEdit.text())/2.0)
        except:
            QMessageBox.warning(self,'Value Error','Please input positive even integers only',QMessageBox.Ok)
            self.searchWinLineEdit.setText(str(self.win))
            
    def peak_search(self,x,y,method=None):
        Nx,Ny=self.imgData.T.shape
        if method=='None':
            return x,y
        elif method=='Nearest-Max':
            x,y=np.int(x),np.int(y)
            chunk=self.imgData.T[np.max([x-self.win,0]):np.min([x+self.win,Nx-1]),np.max([y-self.win,0]):np.min([y+self.win,Ny])]
            i,j=np.unravel_index(chunk.argmax(),chunk.shape)
            return np.max([x-self.win,0])+i,np.max([y-self.win,0])+j
        elif method=='Cen-of-Mass':
            x,y=np.int(x),np.int(y)
            chunk=self.imgData.T[np.max([x-self.win,0]):np.min([x+self.win,Nx-1]),np.max([y-self.win,0]):np.min([y+self.win,Ny])]
            xc,yc=np.meshgrid(range(chunk.shape[1]),range(chunk.shape[0]))
            return np.max([x-self.win,0])+np.sum(yc*chunk)/np.sum(chunk),np.max([y-self.win,0])+np.sum(xc*chunk)/np.sum(chunk)
            
            
    def updatePoints(self, btn):
        key=[k for k in self.pointColorWidget.keys() if self.pointColorWidget[k]==btn]
        self.pointsPlotItems[key[0]].setData(np.array(self.points[key[0]]),symbol='o',symbolSize=10,symbolBrush=pg.mkBrush(color=self.pointColorWidget[key[0]].color()),pen=None)
        
        
    def removePoints(self):
        self.pick_points_disabled()
        items=self.pointTreeWidget.selectedItems()
        for item in items:
            if str(item.text(0))[:4]!='Peak':
                index=item.parent().indexOfChild(item)
                key=int(str(item.parent().text(0)).split()[1])
                self.points[key].pop(index)
                if len(self.points[key])!=0:
                    self.pointsPlotItems[key].setData(np.array(self.points[key]),symbol='o',symbolSize=10,symbolBrush=pg.mkBrush(color=self.pointColorWidget[key].color()),pen=None)
                else:
                    self.rawImageWidget.imageView.getView().vb.scene().removeItem(self.pointsPlotItems[key])
                    self.pointsPlotItems[key]=pg.PlotDataItem(symbol='o',symbolSize=10,symbolBrush=pg.mkBrush(color=self.pointColorWidget[key].color()),pen=None)
                    self.rawImageWidget.imageView.getView().addItem(self.pointsPlotItems[key])
                item.parent().removeChild(item)
            else:
                index=self.pointTreeWidget.indexOfTopLevelItem(item)
                self.pointTreeWidget.takeTopLevelItem(index)
                del self.pointTreeWidgetItems[int(str(item.text(0)).split()[1])]
                self.rawImageWidget.imageView.getView().vb.scene().removeItem(self.pointsPlotItems[int(str(item.text(0)).split()[1])])
                self.points[int(str(item.text(0)).split()[1])]=[]
    
            
    def residual_points(self, param):
        self.geo.set_dist(param['dist'].value)
        self.geo.set_poni1(param['poni1'].value)
        self.geo.set_poni2(param['poni2'].value)
        self.geo.set_rot1(param['rot1'].value)
        self.geo.set_rot2(param['rot2'].value)
        self.geo.set_rot3(param['rot3'].value)
        residue=[]
        for key in self.points.keys():
            for point in self.points[key]:
                d1=point[1]
                d2=point[0]
                q=self.geo.qFunction(np.array([d1]),np.array([d2]))
                residue.append(q[0]/10-self.cal_qvals[key])
        return np.array(residue)
        
    def cal_q_points(self,param):
        q_points={}
        self.geo.set_dist(param['dist'].value)
        self.geo.set_poni1(param['poni1'].value)
        self.geo.set_poni2(param['poni2'].value)
        self.geo.set_rot1(param['rot1'].value)
        self.geo.set_rot2(param['rot2'].value)
        self.geo.set_rot3(param['rot3'].value)
        for key in self.points.keys():
            q_points[key]=[]
            for point in self.points[key]:
                d1=point[1]
                d2=point[0]
                #self.geo.setChiDiscAtZero()
                q=self.geo.qFunction(np.array([d1]),np.array([d2]))
                chi=self.geo.chi(np.array([d1]),np.array([d2]))
                q_points[key].append([chi,q[0]/10])
        return q_points
        
    
        
    def calibrate(self):
        if sum([len(self.points[key]) for key in self.points.keys()])>=6:
            param=Parameters()
            param.add('dist',value=self.dist,vary=self.sample2DetDistCheckBox.isChecked())
            param.add('poni1',value=self.poni1,vary=self.poni1CheckBox.isChecked())
            param.add('poni2',value=self.poni2,vary=self.poni2CheckBox.isChecked())
            param.add('rot1',value=self.rot1,vary=self.rot1CheckBox.isChecked(),min=-np.pi,max=np.pi)
            param.add('rot2',value=self.rot2,vary=self.rot2CheckBox.isChecked(),min=-np.pi,max=np.pi)
            param.add('rot3',value=self.rot3,vary=self.rot3CheckBox.isChecked(),min=-np.pi,max=np.pi)
            out=minimize(self.residual_points,param,method='leastsq')
            fparam=out.params
            self.dist=fparam['dist'].value
            self.sample2DetDistLineEdit.setText(self.floatFmt%self.dist)
            self.poni1=fparam['poni1'].value
            self.poni1LineEdit.setText(self.floatFmt%self.poni1)
            self.poni2=fparam['poni2'].value
            self.poni2LineEdit.setText(self.floatFmt%self.poni2)
            self.rot1=fparam['rot1'].value
            self.rot1LineEdit.setText(self.floatFmt%self.rot1)
            self.rot2=fparam['rot2'].value
            self.rot2LineEdit.setText(self.floatFmt%self.rot2)
            self.rot3=fparam['rot3'].value
            self.rot3LineEdit.setText(self.floatFmt%self.rot3)
            self.applyPyFAI()
            #self.pixel2QMap()
            #self.calibration_peak_selection_changed()
            self.rawImageWidget.imageView.getView().setTitle(title='<span><font size=\"'+'3'+'\">'+'&#967;<sup>2</sup>=%.3e, Red-&#967;<sup>2</sup>=%.3e'%(out.chisqr,out.redchi)+'</font></span>')
            self.q_points=self.cal_q_points(fparam)
            self.solid_angle_plot()
            QMessageBox.information(self,'Calibration Info','Calibration is done with the provided points',QMessageBox.Ok)
            #self.solid_angle=self.geo.solidAngleArray(shape=self.imgData.shape)
        else:
            QMessageBox.warning(self,'Calibration Error','Please select 6 or more points to perform the calibration',QMessageBox.Ok)

        
    def chi_plot(self):
        try:
            self.residual_plot=pg.plot(title='Chi-Plot')
            self.residual_plot.setLabels(bottom='Points',left='Q (inv-Angs)')
            for key in self.q_points.keys():
                data=pg.PlotDataItem(np.array(self.q_points[key]),pen=None,symbol='o')
                self.residual_plot.addItem(data)
                self.residual_plot.addLine(y=self.cal_qvals[key])
        except:
            QMessageBox.warning(self,'Calibration Error','Please do the calibration first.',QMessageBox.Ok)
    
    def solid_angle_plot(self):
        self.pixel2QMap()
        self.SA_imgData=self.geo.solidAngleArray(shape=self.imgData.shape)
        self.SAImageWidget.setImage(self.SA_imgData,transpose=True)
        #self.SAImageWidget.imageLogLinear()
        #self.mainDock.moveDock(self.SAImageDock,'above',self.rawImageDock)
        
        
    def show_solid_angle(self):
        self.mainDock.moveDock(self.SAImageDock,'above',self.rawImageDock)
        
    
        
        
    def save_calibration(self):
        fname=str(QFileDialog.getSaveFileName(self,'Calibration file',directory=CWD,filter='Clibration files (*.poni)')[0])
        tfname=os.path.splitext(fname)[0]+'.poni'
        self.applyPyFAI()
        self.geo.save(tfname)      
        self.poniFile=tfname
        
    def wavelengthToEnergy(self):
        """
        Calculates energy corresponding to a wavelength
        """
        try:
            wavelength=float(self.wavelengthLineEdit.text())
        except:
            QMessageBox.warning(self,'Value error','Please input decimal numbers only',QMessageBox.Ok)
            self.wavelengthLineEdit.setText(self.wavelength)
            wavelength=self.wavelength
            return
        self.wavelength=wavelength
        self.geo.set_wavelength(self.wavelength*1e-10)
        self.wavelengthLineEdit.setText(self.floatFmt%self.wavelength)
        self.energy=6.62607004e-34*2.99792458e8/self.wavelength/1e-10/1.60217662e-19/1e3
        self.energyLineEdit.setText(self.floatFmt%self.energy)
        self.pixel2QMap()
        self.show_cal_ring(0)
        self.solid_angle_plot()
        
    def energyToWavelength(self):
        """
        Calculates energy corresponding to a wavelength
        """
        try:
            energy=float(self.energyLineEdit.text())
        except:
            QMessageBox.warning(self,'Value error','Please input decimal numbers only',QMessageBox.Ok)
            energy=6.62607004e-34*2.99792458e8/self.wavelength/1e-10/1.60217662e-19/1e3
            self.energyLineEdit.setText(self.floatFmt%energy)            
            return
        self.energy=energy
        self.energyLineEdit.setText(self.floatFmt%self.energy)
        self.wavelength=6.62607004e-34*2.99792458e8/self.energy/1e-10/1.60217662e-19/1e3
        self.geo.set_wavelength(self.wavelength*1e-10)
        self.wavelengthLineEdit.setText(self.floatFmt%self.wavelength)
        self.pixel2QMap()
        self.show_cal_ring(0)
        self.solid_angle_plot()
        
        
        
    #def rawImage_mouseMoved(self,pos):
    #    """
    #    Shows the mouse position of 2D Image on its crosshair label
    #    """
    #    pointer=self.rawImageWidget.imageView.getView().vb.mapSceneToView(pos)
    #    x,y=pointer.x(),pointer.y()
    #    if (x>self.img_xmin) and (x<self.img_xmax) and (y>self.img_ymin) and (y<self.img_ymax):
    #        self.rawImageCrossHair.setText('X=%d, Y=%d, I=%.5e'%(x,y,self.imgData[int((x-self.img_xmin)*self.img_hor_Npt/(self.img_xmax-self.img_xmin)),int((y-self.img_ymin)*self.img_ver_Npt/(self.img_ymax-self.img_ymin))]))
    #    else:
    #        self.rawImageCrossHair.setText('X=%d, Y=%d, I=%.5e'%(x,y,0.0))            
    
    #def SAImage_mouseMoved(self,pos):
    #    """
    #    Shows the mouse position of 2D Image on its crosshair label
    #    """
    #    pointer=self.SAImageView.getView().vb.mapSceneToView(pos)
    #    x,y=pointer.x(),pointer.y()
    #    if (x>self.img_xmin) and (x<self.img_xmax) and (y>self.img_ymin) and (y<self.img_ymax):
    #        self.SAImageCrossHair.setText('X=%.6f, Y=%.6f, I=%.5e'%(x,y,self.SA_imgData[int((x-self.img_xmin)*self.img_hor_Npt/(self.img_xmax-self.img_xmin)),int((y-self.img_ymin)*self.img_ver_Npt/(self.img_ymax-self.img_ymin))]))
    #    else:
    #        self.SAImageCrossHair.setText('X=%.6f, Y=%.6f, I=%.5e'%(x,y,0.0)) 
    
    def getBeamPos(self):
        """
        Get direct beam position on the detector plane by clicking on the image
        """
        try:
            self.rawImageWidget.imageView.getView().vb.scene().sigMouseClicked.disconnect()
        except:
            pass
        self.rawImageWidget.imageView.getView().vb.scene().sigMouseClicked.connect(self.image_mouseClicked)
        
    def image_mouseClicked(self,evt):
        pos=self.rawImageWidget.imageView.getImageItem().mapFromScene(evt.scenePos())
        self.beamPosX=pos.x()
        self.beamPosY=pos.y()
        #self.clicked=self.clicked+1
        self.rawImageWidget.imageView.getView().vb.scene().sigMouseClicked.disconnect()
        self.beamPosXLineEdit.setText('%.2f'%self.beamPosX)
        self.beamPosYLineEdit.setText('%.2f'%self.beamPosY)        
        self.applyFit2D()
        self.pixel2QMap()
        self.show_cal_ring(0)
        self.solid_angle_plot()
        
            
    def create_colorMap(self,imageView,min,max,scale='linear'):
        """
        Creates a colorMap with min and max values with linear or log scale
        """        
        if scale=='linear':
            colorPos=self.colorPos
        else:
            colorPos=10**np.linspace(np.log10(min),np.log10(max),7)
            colorPos=np.insert(colorPos,2,10**(np.log10(min)+1.0*(np.log10(max)-np.log10(min))/4.0))
        map=pg.ColorMap(colorPos,self.colorVal)
        imageView.ui.histogram.gradient.setColorMap(map)
        
    #def rawImageLogLinear(self):
    #    """
    #    Converts the image log-linear scale
    #    """
    #    min,max=np.median(self.imgData)*np.array([1e-1,1e2])
    #    if self.rawImageLogCheckBox.isChecked():
    #        tmpData=np.where(self.imgData<=1e-12,1e-12,self.imgData)
    #        tmpData=np.where(self.maskData<0,1e-12,tmpData)
    #        self.rawImageWidget.imageView.setImage(np.log10(tmpData),levels=(np.log10(min),np.log10(max)))
    #    else:
    #        self.rawImageWidget.imageView.setImage(self.imgData,levels=(min,max))
    #    #self.imageView.view.invertY()
    #    pg.QtGui.QApplication.processEvents() 
    
    #def SAImageLogLinear(self):
    #    """
    #    Converts the image log-linear scale
    #    """
    #    min,max=np.min(self.SA_imgData),np.max(self.SA_imgData)
    #    if self.SAImageLogCheckBox.isChecked():
    #        tmpData=np.where(self.SA_imgData<=1e-12,1e-12,self.SA_imgData)
    #        self.SAImageView.setImage(np.log10(tmpData),levels=(np.log10(min),np.log10(max)))
    #    else:
    #        self.SAImageView.setImage(self.SA_imgData,levels=(min,max))
    #    #self.imageView.view.invertY()
    #    pg.QtGui.QApplication.processEvents()    
        
        
if __name__=='__main__':
    # create application
    app = QApplication(sys.argv)
    app.setApplicationName('Calibration Widget')
    pixel1=80.0
    pixel2=80.0
    dist=1.0
    # create widget
    if len(sys.argv)>1:
        img=fb.open(sys.argv[1]).data
    else:
        img=np.random.random(size=(1000,1000))
    if len(sys.argv)>2:
        mask=fb.open(sys.argv[2]).data
    else:
        mask=None
    w = CalibrationWidget(img,pixel1,pixel2,mask=mask,dist=dist)
    #w.setWindowState(Qt.WindowMaximized)
    w.setWindowTitle('Calibration Widget')
    screen=QDesktopWidget().screenGeometry()
    w.setGeometry(10,100,int(screen.width()*0.9),int(screen.height()*0.9))
    w.setWindowState(Qt.WindowMaximized)
    w.show()

    # execute application
    sys.exit(app.exec_())
        
        

import os
from PyQt5.QtCore import pyqtSignal, QObject, QThread

class Setup(QObject):
    def __init__(self,setupDir):
        """
        Setup all the detectors, motors and scalers for X-ray scattering measurement
        """
        self.setupDir=setupDir
        QObject.__init__(self)
        self.detectorSetup()
        self.motorSetup()
        self.scalerSetup()
        self.beamlineSetup()
        
        
    def detectorSetup(self):
        """
        Loads the information about the detectors from currently existing Detector setup file located in ./SetupData/detector_setup.txt
        """
        f=open(os.path.join(self.setupDir,'detector_params.txt'),'r')
        lines=f.readlines()
        self.detectors={}
        for line in lines:
            if (line[0]!='#') and (line[0]!='\n'):
                name,info=line.split('@')
                pv,det_folder,cars_folder=info.strip()[1:-1].split(',')
                self.detectors[name]={'PV':pv.split('=')[1],'det_folder':det_folder.split('=')[1],'cars_folder':cars_folder.split('=')[1]}
                
    def scalerSetup(self):
        """
        Loads the information about the components necessary for SAXS data. The file is located in ./SetupData/saxs_param.txt
        """
        f=open(os.path.join(self.setupDir,'scaler_params.txt'),'r')
        lines=f.readlines()
        self.scalers={}
        for line in lines:
            if line[0]!='#' and line[0]!='\n':
                name,info=line.split('@')
                pv=info.strip()[1:-1]
                self.scalers[name]={'PV':pv.split('=')[1]}
                
    def motorSetup(self):
        """
        Loads the information about other beamline components necessary for SAXS measurements
        """
        f=open(os.path.join(self.setupDir,'motor_params.txt'),'r')
        lines=f.readlines()
        self.motors={}
        for line in lines:
            if line[0]!='#' and line[0]!='\n':
                name,info=line.split('@')
                pv=info.strip()[1:-1]
                self.motors[name]={'PV':pv.split('=')[1]}
                
                
    def beamlineSetup(self):
        """
        Loads the information about 
        """
        f=open(os.path.join(self.setupDir,'beamline_params.txt'),'r')
        lines=f.readlines()
        self.BLParams={}
        for line in lines:
            if line[0]!='#' and line[0]!='\n':
                name,info=line.split('@')
                pv=info.strip()[1:-1]
                self.BLParams[name]={'PV':pv.split('=')[1]}
from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QCheckBox, QSpinBox, QComboBox, QListWidget, QDialog, QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem, QAbstractItemView, QSpinBox, QShortcut, QSplitter, QProgressDialog
from PyQt5.QtGui import QPalette, QKeySequence
from PyQt5.QtCore import Qt
import os
import sys
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
from xraydb import XrayDB
from PlotWidget import PlotWidget
import copy
import numpy as np
import scipy as sp
from scipy.signal import fftconvolve, savgol_filter
from scipy.interpolate import interp1d
from scipy.optimize import minimize
from numpy.linalg import lstsq, solve
from lmfit import Parameters
from lmfit import minimize as lmfit_minimize
import time
from calc_cf import calc_cf
from utils import calc_prm
from readData import read1DSAXS
from itertools import combinations
import periodictable as pdt

class ASAXS_Widget(QWidget):
    """
    This widget class is developed to perform to decouple various scattering contributions of ASAXS data. The contributions include
    1) Non resonant scattering term
    2) Cross term
    3) Resonant term
    """
    def __init__(self,parent=None):
        QWidget.__init__(self,parent)
        self.xrdb=XrayDB()
        self.cwd=os.getcwd()
        self.dataDir=copy.copy(self.cwd)
        
        self.data={}
        self.xrf_bkg={}
        self.energyLines={}
        self.ffactors={}
        self.fCounter=0
        self.xrf_base=0.0
        self.minEnergy=1000000.0
        self.metaKeys=[]
        self.CF=1.0
        
        self.vblayout=QVBoxLayout(self)
        self.mainDock=DockArea(self,parent)
        self.vblayout.addWidget(self.mainDock)
        
        self.dataDock=Dock('Data Dock',size=(2,8))
        self.dataPlotDock=Dock('Data Plot',size=(6,8))
        self.metaDataPlotDock=Dock('Metadata Plot',size=(6,8))
        self.edgePlotDock=Dock('Edge Plot',size=(6,8))
        self.ASAXSCheckPlotDock=Dock('ASAXS Check Plot',size=(6,8))
        self.ASAXSPlotDock=Dock('ASAXS components',size=(6,8))
        self.mainDock.addDock(self.dataDock)
        self.mainDock.addDock(self.dataPlotDock,'right')
        self.mainDock.addDock(self.metaDataPlotDock,'right')
        self.mainDock.addDock(self.edgePlotDock,'right')
        self.mainDock.addDock(self.ASAXSCheckPlotDock,'right')
        self.mainDock.addDock(self.ASAXSPlotDock,'right')
        self.mainDock.moveDock(self.ASAXSCheckPlotDock,'above',self.ASAXSPlotDock)
        self.mainDock.moveDock(self.edgePlotDock,'above',self.ASAXSCheckPlotDock)
        self.mainDock.moveDock(self.metaDataPlotDock,'above',self.edgePlotDock)
        self.mainDock.moveDock(self.dataPlotDock,'above',self.metaDataPlotDock)
        
        self.create_dataDock()
        self.create_dataPlotDock()
        self.create_metaDataPlotDock()
        self.create_edgePlotDock()
        self.create_ASAXSCheckPlotDock()
        self.create_ASAXSPlotDock()
        
        self.edgeEnergy=float(self.elementEdgeComboBox.currentText().split(':')[1].lstrip())
        self.EminLineEdit.setText('%.4f'%(0.9*self.edgeEnergy))
        self.EmaxLineEdit.setText('%.4f'%(1.1*self.edgeEnergy))
        self.update_edgePlot()
        self.initialize_metaDataPlotDock()
        
        
        
    def create_dataDock(self):
        """
        This dock is to hold the information about the resonant element of interest and a list of data 
        """
        self.dataDockLayout=pg.LayoutWidget(self)
        row=0
        col=0
        dataBaseLabel=QLabel('Xray database')
        self.xrayDataBaseComboBox=QComboBox()
        self.dataDockLayout.addWidget(dataBaseLabel,row=row,col=col)
        col+=1
        self.xrayDataBaseComboBox.addItems(['NIST','Henke'])
        self.dataBase='NIST'
        self.xrayDataBaseComboBox.currentIndexChanged.connect(self.dataBaseChanged)
        self.dataDockLayout.addWidget(self.xrayDataBaseComboBox,row=row,col=col,colspan=2)
        
        row+=1
        col=0        
        elementLabel=QLabel('Resonant Element')
        self.elementComboBox=QComboBox()        
        self.elements=self.xrdb.atomic_symbols
        self.elementComboBox.addItems([str(self.xrdb.atomic_number(element))+': '+element for element in self.elements])
        self.elementComboBox.setCurrentIndex(37)
        self.dataDockLayout.addWidget(elementLabel,row=row,col=col)
        col+=1
        self.dataDockLayout.addWidget(self.elementComboBox,row=row,col=col,colspan=2)
        
        row+=1
        col=0
        elementEdge=QLabel('Energy Edge (keV)')
        self.elementEdgeComboBox=QComboBox()
        element=str(self.elementComboBox.currentText().split(': ')[1])
        edges=self.xrdb.xray_edges(element)
        self.elementEdgeComboBox.addItems([key+': %.4f'%(edges[key].edge/1000) for key in edges.keys()])
        self.dataDockLayout.addWidget(elementEdge,row=row,col=col)
        col+=1
        self.dataDockLayout.addWidget(self.elementEdgeComboBox,row=row,col=col,colspan=2)
        self.elementComboBox.currentIndexChanged.connect(self.elementChanged)
        self.elementEdgeComboBox.currentIndexChanged.connect(self.edgeChanged)
        
        row+=1
        col=0
        EOffLabel=QLabel('Energy offset (keV)')
        self.EOffLineEdit=QLineEdit('%.4f'%0.0)
        self.EOffLineEdit.returnPressed.connect(self.dataSelectionChanged)
        self.dataDockLayout.addWidget(EOffLabel,row=row,col=col)
        col+=1
        self.dataDockLayout.addWidget(self.EOffLineEdit,row=row,col=col,colspan=2)
        
        row+=1
        col=0
        delELabel=QLabel('Energy resolution (keV)')
        self.delELineEdit=QLineEdit('%.4f'%0.0)
        self.delELineEdit.returnPressed.connect(self.dataSelectionChanged)
        self.dataDockLayout.addWidget(delELabel,row=row,col=col)
        col+=1
        self.dataDockLayout.addWidget(self.delELineEdit,row=row,col=col,colspan=2)
        
        row+=1
        col=0
        linearOffsetLabel=QLabel('Linear offset')
        self.dataDockLayout.addWidget(linearOffsetLabel,row=row,col=col)
        col+=1
        self.linearOffsetLineEdit=QLineEdit('0.0')
        self.linearOffsetLineEdit.returnPressed.connect(self.dataSelectionChanged)
        self.dataDockLayout.addWidget(self.linearOffsetLineEdit,row=row,col=col,colspan=2)        
        
        row+=1
        col=0
        self.xrfBkgCheckBox=QCheckBox('XRF-Bkg Q-range (%)')
        self.xrfBkgCheckBox.setTristate(False)
        self.xrfBkgCheckBox.setEnabled(False)
        self.xrfBkgCheckBox.stateChanged.connect(self.dataSelectionChanged)
        self.xrfBkgRangeLineEdit=QLineEdit('95:100')
        self.xrfBkgRangeLineEdit.returnPressed.connect(self.dataSelectionChanged)
        self.xrfBkgRangeLineEdit.setEnabled(False)
        self.dataDockLayout.addWidget(self.xrfBkgCheckBox,row=row,col=col)
        col+=1
        self.dataDockLayout.addWidget(self.xrfBkgRangeLineEdit,row=row,col=col,colspan=2)        
        
        row+=1
        col=0
        XRFLabel=QLabel('XRF Baseline')
        self.dataDockLayout.addWidget(XRFLabel,row=row,col=col)
        col+=1
        self.xrfBkgLineEdit=QLineEdit('0.0')
        self.dataDockLayout.addWidget(self.xrfBkgLineEdit,row=row,col=col)
        col+=1
        self.xrfBkgCalcPushButton=QPushButton('Calc XRF-Bkg')
        self.xrfBkgCalcPushButton.clicked.connect(self.calc_XRF_baseline)
        self.dataDockLayout.addWidget(self.xrfBkgCalcPushButton,row=row,col=col)
        
        
        row+=1
        col=0
        dataLabel=QLabel('Data files')
        self.dataDockLayout.addWidget(dataLabel,row=row,col=col)
        self.openDataPushButton=QPushButton('Import data')
        self.openDataPushButton.clicked.connect(self.import_data)
        col+=1
        self.dataDockLayout.addWidget(self.openDataPushButton,row=row,col=col,colspan=2)
        
        
        row+=1
        col=0
        self.dataListWidget=QListWidget()
        self.dataListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.dataListWidget.itemSelectionChanged.connect(self.dataSelectionChanged)
        self.dataDockLayout.addWidget(self.dataListWidget,row=row,col=col,rowspan=10,colspan=3)
        
        row+=10
        col=0
        self.removeDataPushButton=QPushButton('Remove selected Data')
        self.removeDataPushButton.clicked.connect(self.remove_data)
        self.deleteShortCut=QShortcut(QKeySequence.Delete,self)
        self.deleteShortCut.activated.connect(self.remove_data)
        self.dataDockLayout.addWidget(self.removeDataPushButton,row=row,col=col)
        col+=1
        self.batchProcessorPushButton=QPushButton('Open Batch Processor')
        self.dataDockLayout.addWidget(self.batchProcessorPushButton,row=row,col=col,colspan=2)
        self.batchProcessorPushButton.clicked.connect(self.batchProcess)
        
        row+=1
        col=0
        self.bkgScaleLineEdit=QLineEdit('1.0')
        self.dataDockLayout.addWidget(self.bkgScaleLineEdit,row=row,col=col)
        self.bkgScaleLineEdit.returnPressed.connect(self.subtract_bkg)
        col+=1
        self.bkgSubPushButton=QPushButton('Subtract Bkg')
        self.bkgSubPushButton.clicked.connect(self.subtract_bkg)
        self.bkgSubPushButton.setEnabled(False)
        self.dataDockLayout.addWidget(self.bkgSubPushButton,row=row,col=col,colspan=2)
        
        row+=1
        col=0
        self.processTypeComboBox=QComboBox()
        self.processTypeComboBox.addItems(['Mean','Sum'])
        self.processPushButton=QPushButton('Process')
        self.processPushButton.clicked.connect(self.processData)
        self.dataDockLayout.addWidget(self.processTypeComboBox,row=row,col=col)
        col+=1
        self.dataDockLayout.addWidget(self.processPushButton,row=row,col=col,colspan=1)
        col += 1
        self.saveDataPushButton = QPushButton('Save processed data')
        self.dataDockLayout.addWidget(self.saveDataPushButton, row=row, col=col, colspan=1)
        self.saveDataPushButton.clicked.connect(self.save_processed_data)
        
        
        row+=1
        col=0
#        self.thicknessCheckBox=QCheckBox('Sample thickness (cm)')
#        self.thicknessCheckBox.setTristate(False)
#        self.thicknessCheckBox.stateChanged.connect(self.thicknessChanged)
#        self.dataDockLayout.addWidget(self.thicknessCheckBox,row,col)
        thicknessLabel=QLabel('Sample Thickness (cm)')
        self.dataDockLayout.addWidget(thicknessLabel,row,col)
        col+=1
        self.thicknessLineEdit=QLineEdit('1.0')
        self.thicknessLineEdit.returnPressed.connect(self.thicknessChanged)
        self.dataDockLayout.addWidget(self.thicknessLineEdit,row=row,col=col,colspan=2)
        #self.thicknessLineEdit.returnPressed.connect(self.subtract_bkg)
        
        row+=1
        col=0
        standardLabel=QLabel('Standard')
        self.dataDockLayout.addWidget(standardLabel,row=row,col=col)
        col+=1
        self.standardComboBox=QComboBox()
        self.standardComboBox.addItems(['GC','Water'])
        self.dataDockLayout.addWidget(self.standardComboBox,row=row,col=col,colspan=2)
        
        row+=1
        col=0
        self.CFLineEdit=QLineEdit('1.0')
        self.CF=float(self.CFLineEdit.text())
        self.dataDockLayout.addWidget(self.CFLineEdit,row=row,col=col)
        self.CFLineEdit.returnPressed.connect(self.CF_changed)
        col+=1
        #qminqmaxLabel=QLabel('Q-range')
        self.qminqmaxLineEdit=QLineEdit('0.0:1.0')
        self.dataDockLayout.addWidget(self.qminqmaxLineEdit,row=row,col=col,colspan=2)
        self.qminqmaxLineEdit.setToolTip('Qmin:Qmax for CF calculation')
        
        
        row+=1
        col=0
        self.calcCFPushButton=QPushButton('Calculate CF')
        self.calcCFPushButton.clicked.connect(self.calc_cal_factor)
        self.dataDockLayout.addWidget(self.calcCFPushButton,row=row,col=col)
        col+=1
        self.applyCFPushButton=QPushButton('Apply CF')
        self.applyCFPushButton.clicked.connect(self.apply_calc_factor)
        self.dataDockLayout.addWidget(self.applyCFPushButton,row=row,col=col,colspan=2)
   
        
        row+=1
        col=0
        self.checkDataSpinBox=QSpinBox(self)
        self.dataDockLayout.addWidget(self.checkDataSpinBox,row=row,col=col)
        
        col+=1
        self.checkDataPushButton=QPushButton('Check Data')
        self.checkDataPushButton.clicked.connect(self.checkData)
        self.dataDockLayout.addWidget(self.checkDataPushButton,row=row,col=col)
        col+=1
        self.saveCheckDataPushButton=QPushButton('Save Data')
        self.saveCheckDataPushButton.clicked.connect(self.saveCheckData)
        self.dataDockLayout.addWidget(self.saveCheckDataPushButton,row=row,col=col)
        
        
        row+=1
        col=0
        self.elementCheckBox=QCheckBox('Elements')
        self.dataDockLayout.addWidget(self.elementCheckBox,row=row,col=col)
        col+=1
        self.elementsLineEdit=QLineEdit('x, Rb')
        self.dataDockLayout.addWidget(self.elementsLineEdit,row=row,col=col,colspan=2)
        
        
        row+=1
        col=0
        self.ASAXSCalcTypeComboBox=QComboBox()
        self.ASAXSCalcTypeComboBox.addItems(['single-mono','single-poly','single-free','multiple'])
        self.dataDockLayout.addWidget(self.ASAXSCalcTypeComboBox,row=row,col=col)
        col+=1
        self.calcASAXSPushButton=QPushButton('Calculate scattering components')
        self.calcASAXSPushButton.clicked.connect(self.ASAXS_split)
        self.dataDockLayout.addWidget(self.calcASAXSPushButton,row=row,col=col,colspan=2)

        row+=1
        col=0
        self.ASAXSProgressBar=QProgressBar(self)
        self.ASAXSProgressBar.reset()
        self.dataDockLayout.addWidget(self.ASAXSProgressBar,row=row,col=col,colspan=3)

        #row+=1
        #col=0
        #self.checkComponentsPushButton=QPushButton('Check component ratios')
        #self.checkComponentsPushButton.clicked.connect(self.check_components)
        #self.dataDockLayout.addWidget(self.checkComponentsPushButton,row=row,col=col,colspan=3)
        
        row+=1
        col=0
        self.saveASAXSPushButton=QPushButton('Save Scattering Components')
        self.saveASAXSPushButton.clicked.connect(self.save_ASAXS)
        self.saveASAXSPushButton.setEnabled(False)
        self.dataDockLayout.addWidget(self.saveASAXSPushButton,row=row,col=col,colspan=3)
        
        self.dataDock.addWidget(self.dataDockLayout)

    def batchProcess(self):
        pass

    def calc_cal_factor(self):
        """
        Calculates the calibration factor using Intensity calibration sample. At present only Glassy carbon is used.
        """
        if len(self.dataListWidget.selectedItems())==1:
            fname=self.dataListWidget.selectedItems()[0].text().split(': ')[1]
            xmin,xmax=self.qminqmaxLineEdit.text().split(':')
#            try:
            xmin=float(xmin)
            xmax=float(xmax)
            standard=str(self.standardComboBox.currentText())
            thickness=float(self.thicknessLineEdit.text())
            energy,self.CF,x,y=calc_cf(fname,standard=standard,thickness=thickness,xmin=xmin,xmax=xmax)
            self.CFLineEdit.setText('%.5f'%(self.CF))
            self.dataPlotWidget.add_data(x,y,yerr=None,name='std-data')
            self.apply_calc_factor()
            self.dataPlotWidget.Plot([self.dataListWidget.selectedItems()[0].text().split(': ')[0],'std-data'])
#            except:
#                QMessageBox.warning(self,'Value Error','Please provide the Qmin and QMax in qmin:qmax format and Thickness in numerical values in centimeters')
#                return
        else:
            QMessageBox.warning(self,'Selection Error','Please select a single file for calibration factor calculation.',QMessageBox.Ok)
            
    def dataBaseChanged(self):
        """
        Selects the X-ray database
        """
        self.dataBase=str(self.xrayDataBaseComboBox.currentText())
        self.elementChanged()

    def apply_calc_factor(self):
        """
        Apply the current calibration factor to all the selected data
        """
        ans=QMessageBox.question(self,'Confirm','Are you sure of applying CF to the selected data?',QMessageBox.No,QMessageBox.Yes)
        if ans==QMessageBox.Yes:
            for item in self.dataListWidget.selectedItems():
                fname=item.text().split(': ')[1]
                self.data[fname]['CF']=self.CF
            self.dataSelectionChanged()
        
    def elementChanged(self):
        """
        This function is triggered when the current index of elementComboBox changed
        """
        self.elementEdgeComboBox.currentIndexChanged.disconnect()
        self.elementEdgeComboBox.clear()
        element=str(self.elementComboBox.currentText().split(': ')[1])
        edges=self.xrdb.xray_edges(element)
        self.elementEdgeComboBox.addItems([key+': %.4f'%(edges[key].edge/1000) for key in edges.keys()])
        self.elementEdgeComboBox.setCurrentIndex(0)
        self.elementEdgeComboBox.currentIndexChanged.connect(self.edgeChanged)
        self.edgeChanged()
        
        
    def edgeChanged(self):
        """
        This function is triggerred when the current index ov edgeComboBox Changed
        """     
        self.edgeEnergy=float(self.elementEdgeComboBox.currentText().split(': ')[1])
        self.EminLineEdit.setText('%.4f'%(0.9*self.edgeEnergy))
        self.EmaxLineEdit.setText('%.4f'%(1.1*self.edgeEnergy))
        self.dataSelectionChanged()
        
        
        
    def update_edgePlot(self):
        """
        Updates the edgePlot
        """
        #try:
        emin=float(self.EminLineEdit.text())
        emax=float(self.EmaxLineEdit.text())
        esteps=int(self.EstepsLineEdit.text())
        self.EOff = float(self.EOffLineEdit.text())
        self.delE = float(self.delELineEdit.text())
        self.edgeEnergy=float(self.elementEdgeComboBox.currentText().split(':')[1].lstrip())
        element=str(self.elementComboBox.currentText().split(': ')[1])    
        self.Evals=np.linspace(emin,emax,esteps)
        self.calc_f1,self.calc_f2=self.get_f1_f2(element=element,energy=(self.Evals-self.EOff))
        #self.calc_f1=self.xrdb.f1_chantler(element=element,energy=(self.Evals-self.EOff)*1000)
        #self.calc_f2=self.xrdb.f2_chantler(element=element,energy=(self.Evals-self.EOff)*1000)
        if self.delE>=(self.Evals[1]-self.Evals[0]):
            # dE=np.arange(-20.0*self.delE,20.0*self.delE,self.Evals[1]-self.Evals[0])
            # kern=np.exp(-dE**2/2.0/self.delE**2)/np.sqrt(2*np.pi)/self.delE
            # self.calc_f1=fftconvolve(self.calc_f1,kern,mode='valid')*(self.Evals[1]-self.Evals[0])
            # self.calc_f2=fftconvolve(self.calc_f2,kern,mode='valid')*(self.Evals[1]-self.Evals[0])
            self.edgePlotWidget.setYLabel('Effective scattering factors')
        else:                         
            self.edgePlotWidget.setYLabel('Scattering factors')
        # win=int((len(self.Evals)-len(self.calc_f1))/2)
        # if win>0:
        #     self.edgePlotWidget.add_data(self.Evals[win:-win],self.calc_f1,name='f1')
        #     self.edgePlotWidget.add_data(self.Evals[win:-win],self.calc_f2,name='f2')
        # else:
        self.edgePlotWidget.add_data(self.Evals, self.calc_f1, name='f1')
        self.edgePlotWidget.add_data(self.Evals, self.calc_f2, name='f2')
        self.edgePlotWidget.Plot(['f1','f2'])
        self.edgePlotWidget.updatePlot()
        #except:
        #    QMessageBox.warning(self,'Value error','Please input numeric values only',QMessageBox.Ok)
        
    def import_data(self):
        """
        Imports data to populate the dataListWidget
        """
        if self.dataListWidget.count()==0:
            self.fCounter=0
        self.dataFiles=QFileDialog.getOpenFileNames(self,caption='Import data',directory=self.dataDir,filter='Data files (*.dat *.txt *.chi)')[0]
        if len(self.dataFiles)>0:
            self.dataDir=os.path.dirname(self.dataFiles[0])
            self.progressDialog=QProgressDialog(self)
            self.progressDialog.setAutoClose(True)
            self.progressDialog.setMinimum(0)
            self.progressDialog.setMaximum(len(self.dataFiles))
            self.progressDialog.open()
            fnum=0
            for file in self.dataFiles:
                if file not in self.data.keys():
                    item=str(self.fCounter)+': '+file
                    self.dataListWidget.addItem(item)
                    self.read_data(item)
                    self.dataListWidget.item(self.dataListWidget.count()-1).setToolTip('%.4f keV'%self.data[file]['Energy'])
                    self.fCounter+=1
                    fnum+=1
                    self.progressDialog.setValue(fnum)
                    self.progressDialog.setLabelText('Read file: %s successfully.'%file)
                    QApplication.processEvents()
                else:
                    QMessageBox.warning(self,'Import error','%s is already imported. Please remove the file to import it again'%file,QMessageBox.Ok)
            self.initialize_metaDataPlotDock()
            self.xAxisComboBox.addItems(self.metaKeys)
            self.yAxisComboBox.addItems(self.metaKeys)
            self.normAxisComboBox.addItems(self.metaKeys)
        
        
            
    def calc_XRF_baseline(self):
        """
        Calculates the XRF baseline for estimating XRF-backgrounds from the selected data
        """
        if len(self.dataListWidget.selectedItems())==1:
            fname=str(self.dataListWidget.selectedItems()[0].text().split(': ')[1])
            self.xrfFile=fname
            minf,maxf=self.xrfBkgRangeLineEdit.text().split(':')
            xf_bkg_min,xf_bkg_max=float(minf)*np.max(self.data[self.xrfFile]['x'])/100.0,float(maxf)*np.max(self.data[self.xrfFile]['x'])/100.0
            try:
                self.xrf_base=np.mean(self.data[self.xrfFile]['y'][np.argwhere(self.data[self.xrfFile]['x']>xf_bkg_min)[0][0]:np.argwhere(self.data[self.xrfFile]['x']<xf_bkg_max)[-1][0]])
            except:
                self.xrf_base=0.0
            self.xrfBkgLineEdit.setText('%.3e'%self.xrf_base)
        else:
            QMessageBox.warning(self,'Selection Error','Please select only one data set.',QMessageBox.Ok)
        
    def read_data(self,item):
        """
        Reads the data while importing the files in the listWidget
        """
        self.smoothCheckBox.setChecked(False)
        self.mooreACSmoothingCheckBox.setChecked(False)
        num,fname=item.split(': ')
        self.data=read1DSAXS(fname,data=self.data)
        for key in self.data[fname].keys():
            if key not in self.metaKeys:
                self.metaKeys.append(key)
        self.CFLineEdit.setText('%.3f'%self.data[fname]['CF'])
        self.thicknessLineEdit.setText('%.5f'%self.data[fname]['Thickness'])
        self.dataPlotWidget.add_data(self.data[fname]['x'],self.data[fname]['CF']*self.data[fname]['y']/self.data[fname]['Thickness'],yerr=self.data[fname]['CF']*self.data[fname]['yerr']/self.data[fname]['Thickness'],name=num)
        
    def remove_data(self):
        """
        Removes selected data from the dataListWidget
        """
        ans=QMessageBox.question(self,'Confirm','Are you sure you want to remove the data from the program?',QMessageBox.No,QMessageBox.Yes)
        if ans==QMessageBox.Yes:
            self.dataListWidget.itemSelectionChanged.disconnect()
            sel_rows=[self.dataListWidget.row(item) for item in self.dataListWidget.selectedItems()]
            sel_rows.sort(reverse=True)
            for row in sel_rows:
                fname=str(self.dataListWidget.item(row).text().split(': ')[1])
                #if fname!=self.xrfFile:
                del self.data[fname]
                self.dataListWidget.takeItem(row)
            self.dataListWidget.itemSelectionChanged.connect(self.dataSelectionChanged)
        self.dataSelectionChanged()
            
    def save_processed_data(self):
        """
        Saves the data with currently processed settings
        """
        if len(self.fnames)>0:
            for fname in self.fnames:
                pfname=os.path.splitext(fname)[0]+'_proc'+os.path.splitext(fname)[1]
                header='Processed data on %s\n'%time.asctime()
                header='Original file=%s\n'%fname
                for key in self.data[fname].keys():
                    if key!='x' and key!='y' and key!='yerr' and key!='xintp' and key!='yintp' and key!='yintperr' and key!='y-flb':
                        header=header+'%s=%s\n'%(key,self.data[fname][key])
                header=header+'Q (A^-1)\tIntensity\tIntensity_error\n'
                np.savetxt(pfname,np.vstack((self.data[fname]['x'],self.data[fname]['y'],self.data[fname]['yerr'])).T,comments='#',header=header)
            QMessageBox.information(self,'Saving info','The selected processed file/s is/are saved in the same folder as the selected data.',QMessageBox.Ok)
        else:
            QMessageBox.warning(self,'Selection error','No data selected to save',QMessageBox.Ok)
        
    def CF_changed(self):
        """
        Calibration factor changed for the selected data
        """
        try:
            for fname in self.fnames:
                self.data[fname]['CF']=float(self.CFLineEdit.text())
            self.dataSelectionChanged()
        except:
            QMessageBox.warning(self,'Selection Error','Please select a data set or group of data set to change the calibraiton factor',QMessageBox.Ok)
            
    def dataSelectionChanged(self):
        """
        This triggers when the item selection changes in the dataListWidget
        """
        self.update_edgePlot()
        self.datanames=[item.text().split(': ')[0] for item in self.dataListWidget.selectedItems()]
        self.fnames=[item.text().split(': ')[1] for item in self.dataListWidget.selectedItems()]
        #self.initialize_metaDataPlotDock()
        self.metaData={}
        self.metaData['x']=[]
        self.metaData['y']=[]
        self.metaData['norm']=[]
        xname=str(self.xAxisComboBox.currentText())
        yname=str(self.yAxisComboBox.currentText())
        normname=str(self.normAxisComboBox.currentText())
        for i in range(len(self.fnames)):
            fname=self.fnames[i]
            self.CFLineEdit.setText('%.3f'%self.data[fname]['CF'])
            self.thicknessLineEdit.setText('%.5f'%self.data[fname]['Thickness'])
            #Collecting meta data to plot
            if xname in self.data[fname].keys() and yname in self.data[fname].keys():
                self.metaData['x'].append(self.data[fname][xname])
                self.metaData['y'].append(self.data[fname][yname])
                if normname in self.data[fname].keys():
                    self.metaData['norm'].append(self.data[fname][normname])
                else:
                    self.metaData['norm']=1.0
            #Doing the fluorescence correction
            if self.xrfBkgCheckBox.isChecked():
                minf,maxf=self.xrfBkgRangeLineEdit.text().split(':')
                xf_bkg_min,xf_bkg_max=float(minf)*np.max(self.data[fname]['x'])/100.0,float(maxf)*np.max(self.data[fname]['x'])/100.0
                try:
                    self.data[fname]['xrf_bkg']=np.mean(self.data[fname]['y'][np.argwhere(self.data[fname]['x']>xf_bkg_min)[0][0]:np.argwhere(self.data[fname]['x']<xf_bkg_max)[-1][0]])-self.xrf_base
                except:#In case no data found between the range provided
                    self.data[fname]['xrf_bkg']=0.0
                #self.data[fname]['y-flb']=self.data[fname]['CF']*(self.data[fname]['y']-self.xrf_bkg[fname])/self.data[fname]['Thickness']
                #self.dataPlotWidget.add_data(self.data[fname]['x'],self.data[fname]['y-flb'],yerr=self.data[fname]['CF']*self.data[fname]['yerr']/self.data[fname]['Thickness'],name=self.datanames[i])
            else:
                self.data[fname]['xrf_bkg']=0.0
            self.dataPlotWidget.add_data(self.data[fname]['x'],self.data[fname]['CF']*(self.data[fname]['y']-self.data[fname]['xrf_bkg'])/self.data[fname]['Thickness'],yerr=self.data[fname]['CF']*self.data[fname]['yerr']/self.data[fname]['Thickness'],name=self.datanames[i])
        self.metaData['x']=np.array(self.metaData['x'])
        self.metaData['y']=np.array(self.metaData['y'])
        self.metaData['norm']=np.array(self.metaData['norm'])
        self.metaDataPlotWidget.setXLabel(self.xAxisComboBox.currentText())
        self.metaDataPlotWidget.setYLabel(self.yAxisComboBox.currentText())
        self.metaDataPlotWidget.add_data(self.metaData['x'],self.metaData['y']/self.metaData['norm'],name=self.yAxisComboBox.currentText())
        self.metaDataPlotWidget.Plot([self.yAxisComboBox.currentText()])
        self.dataPlotWidget.Plot(self.datanames)
        element=str(self.elementComboBox.currentText().split(': ')[1])
        try:
            self.minEnergy=np.min([self.data[key]['Energy'] for key in self.data.keys()])
        except:
            self.minEnergy=0.0
        for item in self.dataListWidget.selectedItems():
            dataname, fname=item.text().split(': ')
            self.energyLines[fname]=pg.InfiniteLine(pos=self.data[fname]['Energy'],pen=self.dataPlotWidget.data[dataname].opts['pen'])
            self.edgePlotWidget.plotWidget.addItem(self.energyLines[fname])
            self.data[fname]['f1'], self.data[fname]['f2']=self.get_f1_f2(element=element,energy=self.data[fname]['Energy']-self.EOff)
            self.data[fname]['f1']=self.data[fname]['f1']*(1.0+float(self.linearOffsetLineEdit.text())*(self.data[fname]['Energy']-self.minEnergy))
            self.edgePlotWidget.plotWidget.plot([self.data[fname]['Energy']],[self.data[fname]['f1']],pen=None,symbol='o',symbolPen=self.dataPlotWidget.data[dataname].opts['pen'],symbolBrush=None)
        if len(self.datanames)>0:
            self.xrfBkgCheckBox.setEnabled(True)
            self.xrfBkgRangeLineEdit.setEnabled(True)
        else:
            self.xrfBkgCheckBox.setCheckState(Qt.Unchecked)
            self.xrfBkgCheckBox.setEnabled(False)
            self.xrfBkgRangeLineEdit.setEnabled(False)
        
        self.bkgSubPushButton.setDisabled(True)
        if len(self.datanames)==2:
            self.bkgSubPushButton.setEnabled(True)
        #self.raiseDock(self.dataPlotDock)
        
    def subtract_bkg(self):
        """
        Out of the two selected data subtracts one from the other to do background subtraction
        """
        if len(self.dataListWidget.selectedItems())==2:
            self.bkgScale=float(self.bkgScaleLineEdit.text())
            #self.bkgScale=self.data[self.fnames[0]]['BSDiode_corr']*self.data[self.fnames[1]]['Monitor_corr']/self.data[self.fnames[0]]['Monitor_corr']/self.data[self.fnames[1]]['BSDiode_corr']
            #self.bkgScaleLineEdit.setText('%.5f'%self.bkgScale)
            self.interpolate_data(kind='linear')
            tmp=(self.data[self.fnames[0]]['yintp']-self.bkgScale*self.data[self.fnames[1]]['yintp'])\
                *self.data[self.fnames[0]]['Thickness']/self.data[self.fnames[0]]['CF']
            tmperr=np.sqrt(self.data[self.fnames[0]]['yintperr']**2+self.bkgScale**2*self.data[self.fnames[1]]['yintperr']**2)\
                *self.data[self.fnames[0]]['Thickness']/self.data[self.fnames[0]]['CF']
            data=np.vstack((self.qintp,tmp,tmperr)).T
            filename=QFileDialog.getSaveFileName(self,caption='Save as',directory=os.path.dirname(self.fnames[0]),filter='Text files (*.txt)')[0]
            if filename!='':
                self.data[filename]={}
                header='Background subtracted data obtained from data1-data2 where\n data1=%s \n data2=%s\n'%(self.fnames[0],self.fnames[1])
                for key in self.data[self.fnames[0]].keys():
                    if key!='x' and key!='y' and key!='yerr' and key!='xintp' and key!='yintp' and key!='yintperr':
                        self.data[filename][key]=self.data[self.fnames[0]][key]
                        header=header+key+'='+str(self.data[self.fnames[0]][key])+'\n'
                self.data[filename]['CF']=self.data[self.fnames[0]]['CF']
                self.data[filename]['Thickness']=self.data[self.fnames[0]]['Thickness']
                np.savetxt(filename,data,header=header,comments='#')
                self.data[filename]['x']=self.qintp
                self.data[filename]['y']=tmp
                self.data[filename]['yerr']=tmperr
                item=str(self.fCounter)+': '+filename
                self.dataListWidget.addItem(item)
                self.dataListWidget.item(self.dataListWidget.count()-1).setToolTip(str(self.data[filename]['Energy']))
                self.dataPlotWidget.add_data(self.data[filename]['x'],self.data[filename]['y'],yerr=self.data[filename]['yerr'],name=str(self.fCounter))
                self.fCounter+=1
                self.dataListWidget.item(self.dataListWidget.count()-1).setSelected(True)
        else:
            QMessageBox.warning(self,'Data selection error','Please select only two data for background selection.',QMessageBox.Ok)
        #self.fnames.append(filename)
        #self.dataPlotWidget.Plot(self.fnames)
        
    def processData(self):
        """
        Process the selected data for calculating mean and sum
        """
        self.interpolate_data(kind='linear')
        tdata=np.zeros_like(self.data[self.fnames[0]]['yintp'])
        tdata_err=np.zeros_like(tdata)
        tlen=len(self.fnames)
        monitor=0.0
        pDiode=0.0
        diode=0.0
        pDiodeCorr=0.0
        monitorCorr=0.0
        for fname in self.fnames:
            tdata=tdata+self.data[fname]['yintp']
            tdata_err=tdata_err+self.data[fname]['yintperr']**2
            try:
                monitor=monitor+self.data[fname]['Monitor']
                pDiode=pDiode+self.data[fname]['BSDiode']
                diode=diode+self.data[fname]['Diode']
                pDiodeCorr=pDiodeCorr+self.data[fname]['BSDiode_corr']
                monitorCorr=monitorCorr+self.data[fname]['Monitor_corr']
            except:
                monitor=1.0
                pDiode=1.0
                diode=1.0
                pDiodeCorr=1.0
                monitorCorr=1.0
        if self.processTypeComboBox.currentText()=='Mean':
            tdata=tdata/tlen
            tdata_err=np.zeros_like(tdata)
            for fname in self.fnames:
                tdata_err=tdata_err+(tdata-self.data[fname]['yintp'])**2
            tdata_err=np.sqrt(tdata_err/tlen)
            monitor=monitor/tlen
            pDiode=pDiode/tlen
            diode=diode/tlen
            pDiodeCorr=pDiodeCorr/tlen
            monitorCorr=monitorCorr/tlen
        data=np.vstack((self.qintp,tdata,tdata_err)).T
        reply=QMessageBox.question(self,'Question','Do you like to save the processed data as a new file as well?',QMessageBox.Yes,QMessageBox.
                             No)
        if reply==QMessageBox.Yes:
            filename=QFileDialog.getSaveFileName(self,caption='Save as', directory=os.path.dirname(self.fnames[0]),filter='Text files (*.txt)')[0]
            if filename!='':
                self.data[filename]=copy.copy(self.data[self.fnames[0]])
                self.data[filename]['x']=self.qintp
                self.data[filename]['y']=tdata*(self.data[filename]['Thickness']+self.data[filename]['xrf_bkg'])/self.data[filename]['CF']
                self.data[filename]['yerr']=tdata_err*self.data[filename]['Thickness']/self.data[filename]['CF']
                self.data[filename]['Monitor']=monitor
                self.data[filename]['Monitor_corr']=monitorCorr
                self.data[filename]['BSDiode']=pDiode
                self.data[filename]['BSDiode_corr']=pDiodeCorr
                header='Processed data obtained by taking '+self.processTypeComboBox.currentText()+' over the following files:\n'
                for fname in self.fnames:
                    header=header+fname+'\n'
                for key in self.data[filename].keys():
                    if key!='x' and key!='y' and key!='yerr' and key!='xintp' and key!='yintp' and key!='yintperr':
                        header=header+key+'='+str(self.data[filename][key])+'\n'
                    
                np.savetxt(filename,data,header=header,comments='#')
                item=str(self.fCounter)+': '+filename
                self.dataListWidget.addItem(item)
                self.dataListWidget.item(self.dataListWidget.count()-1).setToolTip(str(self.data[filename]['Energy']))
                self.dataPlotWidget.add_data(self.data[filename]['x'],self.data[filename]['y'],yerr=self.data[filename]['yerr'],name=str(self.fCounter))
                self.fCounter+=1
                self.dataListWidget.item(self.dataListWidget.count()-1).setSelected(True)         
            
        
        
        
    def thicknessChanged(self):
        """
        Changing sample thickness of the selected data
        """
        if float(self.thicknessLineEdit.text())>1e-3:
            for item in self.dataListWidget.selectedItems():
                fname=item.text().split(': ')[1]
                self.data[fname]['Thickness']=float(self.thicknessLineEdit.text())
            self.dataSelectionChanged()
        else:
            QMessageBox.warning(self,'Value error','Please enter the thickness value above 0.001 or else you need to change the program',QMessageBox.Ok)
        
            
    
    def create_dataPlotDock(self):
        """
        This dock holds the plot of all the selected data for further analysis
        """
        self.dataPlotLayout=pg.LayoutWidget(self)
        row=0
        col=0
        self.smoothCheckBox=QCheckBox('Smoothing data')
        self.smoothCheckBox.setTristate(False)
        self.smoothCheckBox.stateChanged.connect(self.smoothData)
        self.dataPlotLayout.addWidget(self.smoothCheckBox,row=row,col=col)
        col+=1
        windowLabel=QLabel('Window size')
        self.dataPlotLayout.addWidget(windowLabel,row=row,col=col)
        col+=1
        self.windowSpinBox=QSpinBox()
        self.windowSpinBox.setMinimum(3)
        self.windowSpinBox.setMaximum(101)
        self.windowSpinBox.setSingleStep(2)
        self.windowSpinBox.valueChanged.connect(self.windowChanged)
        self.dataPlotLayout.addWidget(self.windowSpinBox,row=row,col=col)
        col+=1
        polyDegLabel=QLabel('Degree')
        self.dataPlotLayout.addWidget(polyDegLabel,row=row,col=col)
        col+=1
        self.polyDegSpinBox=QSpinBox()
        self.polyDegSpinBox.setMaximum(self.windowSpinBox.value()-1)
        self.polyDegSpinBox.setMinimum(1)
        self.polyDegSpinBox.valueChanged.connect(self.polyDegreeChanged)
        self.dataPlotLayout.addWidget(self.polyDegSpinBox,row=row,col=col)
        
        row+=1
        col=0
        self.mooreACSmoothingCheckBox=QCheckBox('Moore\'s Auto Corr. Smoothing')
        self.mooreACSmoothingCheckBox.setTristate(False)
        self.mooreACSmoothingCheckBox.stateChanged.connect(self.applyMooresAC)
        self.dataPlotLayout.addWidget(self.mooreACSmoothingCheckBox,row=row,col=col)
        col+=1
        DmaxLabel=QLabel('Dmax (Angs)')
        self.dataPlotLayout.addWidget(DmaxLabel,row=row,col=col)
        col+=1
        self.DmaxLineEdit=QLineEdit('100.0')
        self.DmaxLineEdit.returnPressed.connect(self.applyMooresAC)
        self.dataPlotLayout.addWidget(self.DmaxLineEdit,row=row,col=col)
        col+=1
        NrLabel=QLabel('Nr')
        self.dataPlotLayout.addWidget(NrLabel,row=row,col=col)
        col+=1
        self.NrLineEdit=QLineEdit('101')
        self.dataPlotLayout.addWidget(self.NrLineEdit,row=row,col=col)
        self.NrLineEdit.returnPressed.connect(self.applyMooresAC)
        col+=1
        self.plotPDDFPushButton=QPushButton('Plot PDDF')
        self.plotPDDFPushButton.clicked.connect(self.plotPDDF)
        self.dataPlotLayout.addWidget(self.plotPDDFPushButton,row=row,col=col)
        
        row+=1
        col=0
        self.dataPlotWidget=PlotWidget(self)
        self.dataPlotWidget.setXLabel('Q')
        self.dataPlotWidget.setYLabel('Intensity')
        self.dataPlotLayout.addWidget(self.dataPlotWidget,row=row,col=col,colspan=6)        
        self.dataPlotDock.addWidget(self.dataPlotLayout)
        
    def create_metaDataPlotDock(self):
        """
        Creates the metaPlotDataDock
        """
        self.metaDataPlotLayout=pg.LayoutWidget(self)
        row=0
        col=0
        xAxisLabel=QLabel('X-Axis')
        self.metaDataPlotLayout.addWidget(xAxisLabel,row=row,col=col)
        col+=1
        self.xAxisComboBox=QComboBox()
        self.xAxisComboBox.currentIndexChanged.connect(self.dataSelectionChanged)
        self.metaDataPlotLayout.addWidget(self.xAxisComboBox,row=row,col=col)
        col+=2
        yAxisLabel=QLabel('Y-Axis')
        self.metaDataPlotLayout.addWidget(yAxisLabel,row=row,col=col)
        col+=1
        self.yAxisComboBox=QComboBox()
        self.yAxisComboBox.currentIndexChanged.connect(self.dataSelectionChanged)
        self.metaDataPlotLayout.addWidget(self.yAxisComboBox,row=row,col=col)
        col+=2
        normLabel=QLabel('Normalized by')
        self.metaDataPlotLayout.addWidget(normLabel,row=row,col=col)
        col+=1
        self.normAxisComboBox=QComboBox()
        self.normAxisComboBox.currentIndexChanged.connect(self.dataSelectionChanged)
        self.metaDataPlotLayout.addWidget(self.normAxisComboBox,row=row,col=col)
        
        row+=1
        col=0
        self.metaDataPlotWidget=PlotWidget(self)
        self.metaDataPlotLayout.addWidget(self.metaDataPlotWidget,row=row,col=col,colspan=8)
        self.metaDataPlotDock.addWidget(self.metaDataPlotLayout)
        
        
    def create_ASAXSCheckPlotDock(self):
        self.ASAXSCheckPlotLayout=pg.LayoutWidget(self)
        row=0
        col=0
        self.ASAXSCheckPlotWidget=PlotWidget(self)
        self.ASAXSCheckPlotLayout.addWidget(self.ASAXSCheckPlotWidget,row=row,col=col)
        self.ASAXSCheckPlotDock.addWidget(self.ASAXSCheckPlotLayout)
        
        
    def initialize_metaDataPlotDock(self):
        """
        Initialize metaDataPlotDock
        """
        self.xAxisComboBox.clear()
        self.yAxisComboBox.clear()
        self.normAxisComboBox.clear()
        self.xAxisComboBox.addItem('None')
        self.yAxisComboBox.addItem('None')
        self.normAxisComboBox.addItem('None')
        
        
        
    def applyMooresAC(self):
        """
        Apply Moore's autocorrelation function operated smoothing
        """
        if self.mooreACSmoothingCheckBox.isChecked():
            self.smoothCheckBox.setChecked(False)
            dmax=float(self.DmaxLineEdit.text())
            Nr=int(self.NrLineEdit.text())
            for i,fname in enumerate(self.fnames):
                r,pr,dpr,q,iqc=calc_prm(self.data[fname]['x'],self.data[fname]['yraw'],self.data[fname]['yerr'],dmax=dmax,Nr=Nr)
                self.data[fname]['r']=r
                self.data[fname]['pr']=pr
                self.data[fname]['pr_err']=dpr
                self.data[fname]['y']=iqc
#                res=self.dataPlotWidget.add_data(self.data[fname]['x'],self.data[fname]['CF']*self.data[fname]['y']/self.data[fname]['Thickness'],name=self.datanames[i],fit=True)
#            self.dataPlotWidget.Plot(self.datanames)
        else:
            for fname in self.fnames:
                self.data[fname]['r']=None
                self.data[fname]['pr']=None
                self.data[fname]['y']=self.data[fname]['yraw']
        self.dataSelectionChanged()
    
    def plotPDDF(self):
        """
        Plots the moore's autocorrelation function of the selected data
        """
        try:
            plt=pg.plot()
            for fname in self.fnames:
                plt.plot(self.data[fname]['r'],self.data[fname]['pr'],pen='r')
        #pg.plot(self.data[self.fnames[0]]['r'],self.data[self.fnames[0]]['pr'],pen=pg.mkPen('r',width=2))
        except:
            QMessageBox.warning(self,'Data error','Please select Moore\'s autocorrelation first',QMessageBox.Ok)
        
    def smoothData(self):
        """
        Smooth the selected data with Savitizky-Golay method
        """
        if self.smoothCheckBox.isChecked():
            self.mooreACSmoothingCheckBox.setChecked(False)
            window=self.windowSpinBox.value()
            degree=self.polyDegSpinBox.value()
            for fname in self.fnames:
                self.data[fname]['y']=savgol_filter(self.data[fname]['yraw'],window,degree,mode='nearest')
        else:
            for fname in self.fnames:
                self.data[fname]['y']=copy.copy(self.data[fname]['yraw'])
        self.dataSelectionChanged()
                
    def windowChanged(self):
        """
        Changes the window size for smoothing
        """
        self.polyDegSpinBox.setMaximum(self.windowSpinBox.value()-1)
        self.smoothData()
        
    def polyDegreeChanged(self):
        """
        Changes the degree of polynomial for smoothing
        """
        self.smoothData()
        
    def create_ASAXSPlotDock(self):
        """
        This dock holds the plots of different scattering contributions.
        """
        splitter=QSplitter(Qt.Horizontal)
        self.ASAXSCompLayout=pg.LayoutWidget(self)
        self.ASAXSPlotLayout=pg.LayoutWidget(self)
        splitter.addWidget(self.ASAXSCompLayout)
        splitter.addWidget(self.ASAXSPlotLayout)
        row=0
        col=0
        directComponentLabel=QLabel('Direct components')
        self.ASAXSCompLayout.addWidget(directComponentLabel,row=row,col=col)
        
        row=1
        col=0
        self.directComponentListWidget=QListWidget(self)
        self.directComponentListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ASAXSCompLayout.addWidget(self.directComponentListWidget,row=row,col=col)
        
        row=2
        crossComponentLabel=QLabel('Cross components')
        self.ASAXSCompLayout.addWidget(crossComponentLabel,row=row,col=col)
        
        row=3
        self.crossComponentListWidget=QListWidget(self)
        self.crossComponentListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ASAXSCompLayout.addWidget(self.crossComponentListWidget,row=row,col=col)
        
        row=0
        col=1
        self.directComponentPlotWidget=PlotWidget(self)
        self.directComponentPlotWidget.setXLabel('Q',fontsize=5)
        self.directComponentPlotWidget.setYLabel('Intensity',fontsize=5)
        self.ASAXSPlotLayout.addWidget(self.directComponentPlotWidget,row=row,col=col,rowspan=2)
        
        row=2
        col=1
        self.crossComponentPlotWidget=PlotWidget(self)
        self.crossComponentPlotWidget.setXLabel('Q',fontsize=5)
        self.crossComponentPlotWidget.setYLabel('Intensity',fontsize=5)
        self.ASAXSPlotLayout.addWidget(self.crossComponentPlotWidget,row=row,col=col,rowspan=2)
        
        self.directComponentListWidget.itemSelectionChanged.connect(self.directComponentSelectionChanged)
        self.crossComponentListWidget.itemSelectionChanged.connect(self.crossComponentSelectionChanged)
        
        
        
        #self.ASAXSPlotWidget=PlotWidget(self)
        #self.ASAXSPlotWidget.setXLabel('Q',fontsize=5)
        #self.ASAXSPlotWidget.setYLabel('Intensity',fontsize=5)
        #self.ASAXSPlotLayout.addWidget(self.ASAXSPlotWidget,row=row,col=col)        
        self.ASAXSPlotDock.addWidget(splitter)
        
        
        
    def create_edgePlotDock(self):
        """
        This dock holds the plots for scattering factors at the selected energy edge
        """
        self.edgePlotLayout=pg.LayoutWidget(self)
        row=0
        col=0
        EminLabel=QLabel('E-min (keV)')
        EmaxLabel=QLabel('E-max (keV)')
        EstepsLabel=QLabel('# of points')
        self.EminLineEdit=QLineEdit()
        self.EmaxLineEdit=QLineEdit()
        self.EstepsLineEdit=QLineEdit('1000')
        self.edgePlotLayout.addWidget(EminLabel,row=row,col=col)
        col+=1
        self.edgePlotLayout.addWidget(self.EminLineEdit,row=row,col=col)
        self.EminLineEdit.returnPressed.connect(self.dataSelectionChanged)
        col+=1        
        self.edgePlotLayout.addWidget(EmaxLabel,row=row,col=col)
        col+=1
        self.edgePlotLayout.addWidget(self.EmaxLineEdit,row=row,col=col)
        self.EmaxLineEdit.returnPressed.connect(self.dataSelectionChanged)
        col+=1
        self.edgePlotLayout.addWidget(EstepsLabel,row=row,col=col)
        col+=1
        self.edgePlotLayout.addWidget(self.EstepsLineEdit,row=row,col=col)
        self.EstepsLineEdit.returnPressed.connect(self.dataSelectionChanged)
        row+=1
        col=0
        self.edgePlotWidget=PlotWidget(self)
        self.edgePlotWidget.lineWidthLineEdit.returnPressed.connect(self.dataSelectionChanged)
        self.edgePlotWidget.pointSizeLineEdit.returnPressed.connect(self.dataSelectionChanged)
        self.edgePlotWidget.pointSizeLineEdit.setText('0')
        self.edgePlotWidget.setXLabel('Energy (keV)')
        self.edgePlotWidget.setYLabel('Scattering factors (el/Atom)')
        self.edgePlotLayout.addWidget(self.edgePlotWidget,row=row,col=col,colspan=6)        
        self.edgePlotDock.addWidget(self.edgePlotLayout)
        
        
    def interpolate_data(self,kind='linear'):
        """
        Interpolates all the selected data with the common q values
        Npt=No. of common q-values on which interpolated values will be calculated
        kind='linear','cubic'...please check the documentation of scipy.interpolate.interp1d for more options
        """
        qmin=0.0
        qmax=1e15
        
        #For getting the appropriate qmin and qmax of the interpolated data
        #for item in self.dataListWidget.selectedItems():
        for fname in self.fnames:
            #dataname, fname=item.text().split(': ')
            tmin=np.min(self.data[fname]['x'])
            tmax=np.max(self.data[fname]['x'])
            if tmin>qmin:
                qmin=copy.copy(tmin)
            if tmax<qmax:
                qmax=copy.copy(tmax)                
        self.qintp=np.linspace(qmin,qmax,len(self.data[self.fnames[0]]['x']))
        for item in self.dataListWidget.selectedItems():
            dataname, fname=item.text().split(': ')
            self.data[fname]['xintp']=self.qintp
            #if self.xrfBkgCheckBox.isChecked():
            #    fun=interp1d(self.data[fname]['x'],self.data[fname]['y-flb'],kind=kind) #Calibration factor and thickness no#rmalization are already applied
            #else:
            fun=interp1d(self.data[fname]['x'],self.data[fname]['CF']*(self.data[fname]['y']-self.data[fname]['xrf_bkg'])/self.data[fname]['Thickness'],kind=kind)
            funerr=interp1d(self.data[fname]['x'],self.data[fname]['CF']*self.data[fname]['yerr']/self.data[fname]['Thickness'],kind=kind)
            self.data[fname]['yintp']=fun(self.qintp)
            self.data[fname]['yintperr']=funerr(self.qintp)
            
    def get_f1_f2(self,element,energy):
        """
        Obtains f1 and f2 either from NIST table or Henke's function with element=element symbol and energy in keV
        """
        self.delE = float(self.delELineEdit.text())
        if self.delE>1e-4:
            if type(energy) is list or type(energy) is np.ndarray:
                f1=[]
                f2=[]
                for e in energy:
                    evals=np.arange(e-5*self.delE,e+5*self.delE,0.0001)
                    calc_f1 = self.xrdb.f1_chantler(element=element, energy=evals * 1000, smoothing=0)
                    calc_f2 = self.xrdb.f2_chantler(element=element, energy=evals * 1000, smoothing=0)
                    kern = np.exp(-(evals-e) ** 2 / 2.0 / self.delE ** 2) / np.sqrt(2 * np.pi) / self.delE
                    ksum = np.sum(kern)
                    f1.append(np.sum(kern*calc_f1)/ksum)
                    f2.append(np.sum(kern*calc_f2)/ksum)
                return np.array(f1),np.array(f2)
            else:
                e=energy
                evals = np.arange(e - 5 * self.delE, e + 5 * self.delE, 0.0001)
                calc_f1 = self.xrdb.f1_chantler(element=element, energy=evals * 1000, smoothing=0)
                calc_f2 = self.xrdb.f2_chantler(element=element, energy=evals * 1000, smoothing=0)
                kern = np.exp(-(evals - e) ** 2 / 2.0 / self.delE ** 2) / np.sqrt(2 * np.pi) / self.delE
                ksum = np.sum(kern)
                f1=np.sum(kern * calc_f1) / ksum
                f2=np.sum(kern * calc_f2) / ksum
                return f1, f2
        else:
            if self.dataBase=='NIST':
                f1=self.xrdb.f1_chantler(element=element,energy=energy*1000,smoothing=0)
                f2=self.xrdb.f2_chantler(element=element,energy=energy*1000,smoothing=0)
            else:
                f1=eval('-pdt.%s.number+pdt.%s.xray.scattering_factors(energy=energy)[0]'%(element,element))
                f2=eval('pdt.%s.xray.scattering_factors(energy=energy)[1]'%(element))
            return f1, f2
    
    def checkData(self):
        """
        Do initial check on the selected data for further ASAXS analysis
        """
        if len(self.dataListWidget.selectedItems())>0:
            self.interpolate_data()
            self.prepareData()
            dataChk=[]
            errChk=[]
            f1val=[]
            energy=[]
            for item in self.dataListWidget.selectedItems():
                dataname, fname=item.text().split(': ')
                dataChk.append(self.data[fname]['yintp'])
                errChk.append(self.data[fname]['yintperr'])
                f1val.append(self.data[fname]['f1'])
                energy.append(self.data[fname]['Energy'])
            dataChk=np.array(dataChk)
            errChk=np.array(errChk)
            dataChk=dataChk
            errChk=errChk
            f1val=np.array(f1val)
            energy=np.array(energy)
            self.pdata=[[energy,f1val,dataChk[:,i],errChk[:,i]] for i in range(dataChk.shape[1])]
            #print(self.pdata[0][0],self.pdata[0][1],self.pdata[0][2]/self.pdata[0][2][0])#/self.pdata[0][2][0])
            #print(len(self.pdata[0][0]), len(self.pdata[0][1]), len(self.pdata[0][2]))
            self.dataCheckWidget=pg.plot(self.pdata[0][1],self.pdata[0][2]/self.pdata[0][2][0],pen=None,symbol='o')
            self.checkDataSpinBox.setMinimum(0)
            self.checkDataSpinBox.setMaximum(dataChk.shape[1]-1)
            self.checkDataSpinBox.setValue(0)            
            self.checkDataLocLine=pg.InfiniteLine(pos=self.qintp[0],pen='w')
            self.dataPlotWidget.plotWidget.addItem(self.checkDataLocLine)
            self.checkDataSpinBox.valueChanged.connect(self.update_dataCheckPlot)
            self.update_dataCheckPlot()
            
    def saveCheckData(self):
        """
        Save the checked data
        """
        try:
            fname=QFileDialog.getSaveFileName(self,caption='Save checked data as',directory=self.dataDir,filter='Text files (*.txt)')[0]
            if fname !='':
                i=self.checkDataSpinBox.value()
                data=np.vstack((self.pdata[i][0],self.pdata[i][1],self.pdata[i][2],self.pdata[i][3])).T
                header='Data extracted at Q=%.6f\n'%self.qintp[i]
                header+='col_names=["Energy","f1","Intensity","Intensity_err"]'
                np.savetxt(fname,data,header=header,comments='#')            
        except:
            QMessageBox.warning(self,'Data error','No checked data to be saved. Please click Check Data button first',QMessageBox.Ok)
        
        
    def update_dataCheckPlot(self):
        """
        Updates the dataCheckplot
        """
        i=self.checkDataSpinBox.value()
        self.dataCheckWidget.clear()
        self.dataCheckWidget.plot(self.pdata[i][1],self.pdata[i][2]/self.pdata[i][2][0],symbol='o',pen=None)
        if self.dataPlotWidget.plotWidget.getPlotItem().ctrl.logXCheck.isChecked():
            self.checkDataLocLine.setValue(np.log10(self.qintp[i]))
        else:
            self.checkDataLocLine.setValue(self.qintp[i])
        
        
    def prepareData(self):
        """
        Prepares the selected data for ASAXS splitting i.e.
        1) Interpolate the all data sets with same q values. SAXS data collection at different energies can bring different q-values
        2) Calculates the scattering factors f1 and f2 for energies at which the data were collected
        """
        self.interpolate_data()
        element=str(self.elementComboBox.currentText().split(': ')[1])
        self.AMatrix=[]
        self.BMatrix=None
        self.ErrMatrix=None
        self.EOff=float(self.EOffLineEdit.text())
        #self.calc_XRF_baseline()
        self.minEnergy=np.min([self.data[key]['Energy'] for key in self.data.keys()])
        for item in self.dataListWidget.selectedItems():
            dataname, fname=item.text().split(': ')
            self.data[fname]['f1'], self.data[fname]['f2']=self.get_f1_f2(element,(self.data[fname]['Energy']-self.EOff))
            self.data[fname]['f1']=self.data[fname]['f1']*(1.0+float(self.linearOffsetLineEdit.text())*(self.data[fname]['Energy']-self.minEnergy))
            
            #self.data[fname]['f1']=self.xrdb.f1_chantler(element=element,energy=(self.data[fname]['Energy']-self.EOff)*1000)
            #self.data[fname]['f2']=self.xrdb.f2_chantler(element=element,energy=(self.data[fname]['Energy']-self.EOff)*1000)
            self.AMatrix.append([1.0, 2*self.data[fname]['f1'], self.data[fname]['f1']**2+self.data[fname]['f2']**2])
            if self.BMatrix is not None:
                self.BMatrix=np.vstack((self.BMatrix, self.data[fname]['yintp']))
                self.ErrMatrix=np.vstack((self.ErrMatrix,self.data[fname]['yintperr']))
            else:
                self.BMatrix=self.data[fname]['yintp']
                self.ErrMatrix=self.data[fname]['yintperr']
        self.AMatrix=np.array(self.AMatrix)
        energies=np.array([self.data[item.text().split(': ')[1]]['Energy'] for item in self.dataListWidget.selectedItems()])
        index=np.argsort(energies)
        self.energies=energies[index]
        self.AMatrix=self.AMatrix[index]
        self.BMatrix=self.BMatrix[index]
        
    def ASAXS_split(self):
        #try:
        self.ASAXSProgressBar.reset()
        if self.ASAXSCalcTypeComboBox.currentText()=='single-free':
            #self.ASAXS_split_1()
            self.ASAXS_split_w_errbars(constraint=False,mono=False)
        elif self.ASAXSCalcTypeComboBox.currentText()=='single-mono':
            self.ASAXS_split_w_errbars(constraint=True, mono=True)
        elif self.ASAXSCalcTypeComboBox.currentText()=='single-poly':
            self.ASAXS_split_w_errbars(constraint=True, mono=False)
        else:
            self.ASAXS_split_3()
            
        #self.ASAXS_split_3()
#        if str(self.ASAXSCalcTypeComboBox.currentText())=='np.linalg.lstsq':
#            if len(self.fnames)==3:
#                self.ASAXS_split_0()
#            else:
#                #self.ASAXS_split_1()
#                self.ASAXS_split_3()
#        else:
#            if len(self.fnames)==3:
#                self.ASAXS_split_0()
#            else:
#                self.ASAXS_split_2()
#        #except:
        #    QMessageBox.warning(self,'Selection error','Please select atleast three data sets to calculate the components',QMessageBox.Ok)
        
            
    def ASAXS_split_0(self):
        """
        This calculates scattering compononents out
        """
        self.prepareData()
        self.XMatrix=[]
        for i in range(len(self.qintp)):
            x=solve(self.AMatrix,self.BMatrix[:,i])
            self.XMatrix.append(x)
        self.XMatrix=np.array(self.XMatrix)
        self.ASAXSPlotWidget.add_data(self.qintp,self.XMatrix[:,0],name='SAXS-term')
        #if np.all(self.XMatrix[:,1]>0):
        self.ASAXSPlotWidget.add_data(self.qintp,self.XMatrix[:,1],name='Cross-term')
        #else:
        #    QMessageBox.warning(self,'Negative Log error','Cross terms are all negative so plotting the -ve of cross terms',QMessageBox.Ok)
        #    self.ASAXSPlotWidget.add_data(self.qintp,-self.XMatrix[:,1],name='neg Cross-term')
        self.ASAXSPlotWidget.add_data(self.qintp,self.XMatrix[:,2],name='Resonant-term')
        self.ASAXSPlotWidget.add_data(self.qintp,np.sum(np.dot([self.AMatrix[0,:]],self.XMatrix.T),axis=0),name='Total')
        self.update_ASAXSPlot()
        self.saveASAXSPushButton.setEnabled(True)
            
            
    def ASAXS_split_1(self):
        """
        This calculates scattering compononents out
        """
        if len(self.dataListWidget.selectedItems())>=3:
            self.prepareData()
            self.XMatrix=[]
            for i in range(len(self.qintp)):
                x,residuals,rank,s=lstsq(self.AMatrix,self.BMatrix[:,i])
                self.XMatrix.append(x)
            self.XMatrix=np.array(self.XMatrix)
            
            self.directComponentPlotWidget.add_data(self.qintp,self.XMatrix[:,0],name='SAXS-term')
            self.directComponentPlotWidget.add_data(self.qintp,self.XMatrix[:,2],name='Resonant-term')
            tot=np.sum(np.dot([self.AMatrix[0,:]],self.XMatrix.T),axis=0)
            self.directComponentPlotWidget.add_data(self.qintp,tot,name='Total')           
            self.directComponentPlotWidget.add_data(self.qintp,self.data[self.fnames[0]]['yintp'],name='Data_%s'%self.datanames[0])
            self.directComponentListWidget.clear()
            self.crossComponentListWidget.clear()
            try:
                self.directComponentListWidget.itemSelectionChanged.disconnect()
                self.crossComponentListWidget.itemSelectionChanged.disconnect()
            except:
                pass
            self.directComponentListWidget.addItems(['SAXS-term','Resonant-term','Total','Data_%s'%self.datanames[0]])
            self.crossComponentListWidget.addItem('Cross-term')
            self.crossComponentPlotWidget.add_data(self.qintp,self.XMatrix[:,1],name='Cross-term')
            self.components={}
            self.components['SAXS-term']=self.XMatrix[:,0]
            self.components['Resonant-term']=self.XMatrix[:,2]
            self.components['Cross-term']=self.XMatrix[:,1]
            self.components['Data_%s'%self.datanames[0]]=self.data[self.fnames[0]]['yintp']
            self.update_ASAXSPlot()
            self.saveASAXSPushButton.setEnabled(True)
            self.directComponentListWidget.itemSelectionChanged.connect(self.directComponentSelectionChanged)
            self.crossComponentListWidget.itemSelectionChanged.connect(self.crossComponentSelectionChanged)
            self.directComponentListWidget.item(0).setSelected(True)
            self.directComponentListWidget.item(1).setSelected(True)
            self.crossComponentListWidget.item(0).setSelected(True)
        else:
            #self.saveASAXSPushButton.setEnabled(True)
            QMessageBox.warning(self,'Data Error','Please select three or more data sets to do the calculation',QMessageBox.Ok)


    def lmfit_residual(self, param, A, B,Err,constraint):
        """
        Calculates the residual for lmfit to obtain the errorbars in the parameters
        :param param:
        :param A: Amatrix
        :param B: BMatrix
        :return: residual
        """
        if not constraint:
            x=np.array([param['x1'],param['x2'],param['x3']])
        else:
            x=np.array([param['x1'], param['x2'],param['x2']**2/param['x1']+param['x3']])
        return (np.dot(A,x)-B)

    def lmfit_finderrbars(self,x,A,B,Err,constraint=False,mono=False):
        fac=min(B)
        param=Parameters()
        param.add('x1',value = x[0]/fac,min=x[0]*1e-3/fac)
        param.add('x2',value = x[1]/fac)
        if not constraint:
            param.add('x3', value=x[2]/fac)
        else:
            if not mono:
                param.add('x3',value=x[2]/fac,min=0.0)
            else:
                param.add('x3', value=0.0,vary=False)
        out = lmfit_minimize(self.lmfit_residual, param, args=(A,B/fac,Err,constraint))
        x1 = out.params['x1'].value
        x1err = out.params['x1'].stderr
        x2 = out.params['x2'].value
        x2err = out.params['x2'].stderr
        x3 = out.params['x3'].value
        x3err = out.params['x3'].stderr
        if x1err is None:
            x1err=x1*0.1
        if x2err is None:
            x2err=x2*0.1
        if x3err is None:
            x3err=x3*0.1
        if constraint:
            if not mono:
                x3err=np.sqrt((2*x2*x2err/x1)**2+(x2**2*x1err/x1**2)**2+x3err**2)
            else:
                x3err=np.sqrt((2*x2*x2err/x1)**2+(x2**2*x1err/x1**2)**2)
        #print(x1,x1err)
        #print(x2,x2err)
        # if not constraint:
        #     x3 = out.params['x3'].value
        #     x3err = out.params['x3'].stderr
        # else:
        #     x3 = x2**2/x1
        #     x3err = np.sqrt((2*x2*x3*x2err/x1)**2+(x2**2*x3*x1err/x1**2)**2)
        return x1*fac, x1err*fac, x2*fac, x2err*fac, x3*fac, x3err*fac

    def brute_finderrbars(self,A,B):
        i,j,k=0,int(A.shape[0]/2),A.shape[0]-1
        a1,a2,a3=A[i,1],A[j,1],A[k,1]
        b1,b2,b3=A[i,2],A[j,2],A[k,2]
        c1,c2,c3=B[i],B[j],B[k]
        Amat=[[b2-b1, a1*b2-a2*b1],[b3-b2, a2*b3-a3*b2]]
        Bmat=[c1*b2-c2*b1,c2*b3-c3*b2]
        [x1,x2]=solve(Amat,Bmat)
        x3=x2**2/x1
        return [x1,x2,x3]

    def ASAXS_split_w_errbars(self,constraint=False,mono=False):
        """
        This calculates scattering compononents out
        """
        if len(self.dataListWidget.selectedItems()) >= 3:
            self.prepareData()
            self.XMatrix = []
            self.XMatrixErr = []
            ans = QMessageBox.question(self, 'Question', 'Do you like to look at each individual Q for this analysis?',
                                       QMessageBox.Yes, QMessageBox.No)
            tot=[]
            f1 = [self.xrdb.f1_chantler(element=str(self.elementComboBox.currentText().split(': ')[1]), energy=(energy-self.EOff) * 1e3,
                                        smoothing=0) for energy in self.energies]
            self.ASAXSProgressBar.setMinimum(0)
            self.ASAXSProgressBar.setMaximum(len(self.qintp))
            for i in range(len(self.qintp)):
                x=self.brute_finderrbars(self.AMatrix,self.BMatrix[:,i])
                #x=[self.BMatrix[0,i],self.BMatrix[0,i]*1e-3,self.BMatrix[0,i]*1e-6]
                #print(x)
                #x=[self.BMatrix[0,i],1,0.0]
                #x, residuals, rank, s = lstsq(self.AMatrix, self.BMatrix[:, i],rcond=None)
                x1, x1err, x2, x2err, x3, x3err = self.lmfit_finderrbars(x, self.AMatrix, self.BMatrix[:, i],self.ErrMatrix[:,i], constraint=constraint,mono=mono)
                if constraint:
                    xn=[x1,x2,x2**2/x1+x3]
                else:
                    xn=[x1,x2,x3]
                self.XMatrix.append(xn)
                print(x1err,x2err,x3err)
                tot.append(np.dot(self.AMatrix, self.XMatrix[-1]))
                self.ASAXSCheckPlotWidget.errorbarCheckBox.setChecked(True)
                if ans == QMessageBox.Yes:
                    self.ASAXSCheckPlotWidget.setTitle('Point=%d, Q=%.5f' % (i,self.qintp[i]))
                    self.ASAXSCheckPlotWidget.add_data(f1, self.BMatrix[:, i], yerr=self.ErrMatrix[:,i],name='Data')
                    self.ASAXSCheckPlotWidget.add_data(f1, tot[-1], name='Fit', fit=True)
                    self.ASAXSCheckPlotWidget.Plot(['Data', 'Fit'])
                    self.raiseDock(self.ASAXSCheckPlotDock)
                    ans = QMessageBox.question(self, 'Question', 'Do you like to see the next Q?', QMessageBox.Yes,
                                               QMessageBox.No)
                xnerr=[x1err, x2err, x3err]
                self.XMatrixErr.append(xnerr)
                self.ASAXSProgressBar.setValue(i)
            self.XMatrix = np.array(self.XMatrix)
            self.XMatrixErr = np.array(self.XMatrixErr)

            self.directComponentPlotWidget.add_data(self.qintp, self.XMatrix[:, 0], yerr=self.XMatrixErr[:, 0], name='SAXS-term')
            self.directComponentPlotWidget.add_data(self.qintp, self.XMatrix[:, 2], yerr=self.XMatrixErr[:, 2], name='Resonant-term')
            tot = np.sum(np.dot([self.AMatrix[0, :]], self.XMatrix.T), axis=0)
            self.directComponentPlotWidget.add_data(self.qintp, tot, name='Total')
            self.directComponentPlotWidget.add_data(self.qintp, self.data[self.fnames[0]]['yintp'],
                                                    name='Data_%s' % self.datanames[0])
            self.directComponentListWidget.clear()
            self.crossComponentListWidget.clear()
            try:
                self.directComponentListWidget.itemSelectionChanged.disconnect()
                self.crossComponentListWidget.itemSelectionChanged.disconnect()
            except:
                pass
            self.directComponentListWidget.addItems(
                ['SAXS-term', 'Resonant-term', 'Total', 'Data_%s' % self.datanames[0]])
            self.crossComponentListWidget.addItem('Cross-term')
            self.crossComponentPlotWidget.add_data(self.qintp, self.XMatrix[:, 1], yerr=self.XMatrixErr[:, 1], name='Cross-term')
            self.components = {}
            self.components['SAXS-term'] = self.XMatrix[:, 0]
            self.components['SAXS-term_err'] = self.XMatrixErr[:, 0]
            self.components['Resonant-term'] = self.XMatrix[:, 2]
            self.components['Resonant-term_err'] = self.XMatrixErr[:, 2]
            self.components['Cross-term'] = self.XMatrix[:, 1]
            self.components['Cross-term_err'] = self.XMatrixErr[:, 1]
            self.components['Total'] = tot
            self.components['Data_%s' % self.datanames[0]] = self.data[self.fnames[0]]['yintp']
            self.update_ASAXSPlot()
            self.saveASAXSPushButton.setEnabled(True)
            self.directComponentListWidget.itemSelectionChanged.connect(self.directComponentSelectionChanged)
            self.crossComponentListWidget.itemSelectionChanged.connect(self.crossComponentSelectionChanged)
            self.directComponentListWidget.item(0).setSelected(True)
            self.directComponentListWidget.item(1).setSelected(True)
            self.crossComponentListWidget.item(0).setSelected(True)
            self.ASAXSProgressBar.setValue(len(self.qintp))
        else:
            # self.saveASAXSPushButton.setEnabled(True)
            QMessageBox.warning(self, 'Data Error', 'Please select three or more data sets to do the calculation',
                                QMessageBox.Ok)
            self.ASAXSProgressBar.reset()

    def residual(self,x,A,B):
        """
        Calculates the residual for ASAXS_split_2
        """
        return np.sum(np.array([np.sum([A[i,j]*x[j]-B[i] for j in range(3)]) for i in range(A.shape[0])])**2)
            
    def ASAXS_split_2(self):
        """
        This calculates the scattering components by constraining the SAXS and anomalous term to be positive
        """
        if len(self.fnames)>3:
            self.prepareData()
            self.XMatrix=[]
            cons=({'type': 'ineq', 'fun': lambda x: x[0]},
                   {'type': 'ineq', 'fun': lambda x: x[2]},)
            for i in range(len(self.qintp)):
                res=minimize(self.residual,[0.0,0.0,0.0],args=(self.AMatrix,self.BMatrix[:,i]),constraints=cons,bounds=((0,None),(None,None),(0,None)))
                self.XMatrix.append(res.x)
            self.XMatrix=np.array(self.XMatrix)
            self.ASAXSPlotWidget.add_data(self.qintp,self.XMatrix[:,0],name='SAXS-term')
            #if np.all(self.XMatrix[:,1]>0):
            self.ASAXSPlotWidget.add_data(self.qintp,self.XMatrix[:,1],name='Cross-term')
            #else:
            #    QMessageBox.warning(self,'Negative Log error','Cross terms are all negative so plotting the -ve of cross terms',QMessageBox.Ok)
            #    self.ASAXSPlotWidget.add_data(self.qintp,-self.XMatrix[:,1],name='neg Cross-term')
            self.ASAXSPlotWidget.add_data(self.qintp,self.XMatrix[:,2],name='Resonant-term')
            self.ASAXSPlotWidget.add_data(self.qintp,np.sum(np.dot([self.AMatrix[0,:]],self.XMatrix.T),axis=0),name='Total')
            self.update_ASAXSPlot()
            self.saveASAXSPushButton.setEnabled(True)
        else:
            #self.saveASAXSPushButton.setEnabled(True)
            QMessageBox.warning(self,'Data error','Please select more than three data sets to do the calculation',QMessageBox.Ok)
            
    def prepareNewData(self):
        """
        Prepares the selected data for new ASAXS splitting provided by ASAXS_split_3 i.e.
        1) Interpolate the all data sets with same q values. SAXS data collection at different energies can bring different q-values
        2) Calculates the scattering factors f1 and f2 for energies at which the data were collected
        """
        self.interpolate_data()
        #element=str(self.elementComboBox.currentText().split(': ')[1])
        self.EOff=float(self.EOffLineEdit.text())
        #self.calc_XRF_baseline()
        self.minEnergy=np.min([self.data[key]['Energy'] for key in self.data.keys()])
        self.elements=self.elementsLineEdit.text().replace(' ','').split(',')
        fe={}
        Ne=len(self.fnames)
        Np=len(self.elements)
        self.AIndex={}
        self.AMatrix=np.zeros((Ne,Np+int(sp.misc.comb(Np,2))))
        self.BMatrix=None
        for k in range(Ne):
            ind=0
            for i in range(Np):
                if self.elements[i]=='x':
                    fe[self.elements[i]]=np.complex(1.0,0.0)
                else:
                    f0=self.xrdb.f0(self.elements[i],0.0)
                    f1,f2=self.get_f1_f2(self.elements[i],(self.data[self.fnames[k]]['Energy']-self.EOff))
                    fe[self.elements[i]]=np.complex(f0+f1,f2)
                self.AMatrix[k,ind]=np.absolute(fe[self.elements[i]])**2
                self.AIndex['S_%s-%s'%(self.elements[i],self.elements[i])]=ind
                ind+=1
            for i in range(Np-1):
                for j in range(i+1,Np):
                    self.AMatrix[k,ind]=2*np.real(fe[self.elements[i]]*np.conjugate(fe[self.elements[j]]))
                    self.AIndex['S_%s-%s'%(self.elements[i],self.elements[j])]=ind
                    ind+=1

            if self.BMatrix is not None:
                self.BMatrix=np.vstack((self.BMatrix, self.data[self.fnames[k]]['yintp']))
            else:
                self.BMatrix=self.data[self.fnames[k]]['yintp']
        self.directComponentListWidget.itemSelectionChanged.disconnect(self.directComponentSelectionChanged)
        self.crossComponentListWidget.itemSelectionChanged.disconnect(self.crossComponentSelectionChanged)
        self.directComponentListWidget.clear()
        self.crossComponentListWidget.clear()
        for i in range(Np):
            self.directComponentListWidget.addItem('S_%s-%s'%(self.elements[i],self.elements[i]))
        for i in range(Np-1):
            for j in range(i+1,Np):
                self.crossComponentListWidget.addItem('S_%s-%s'%(self.elements[i],self.elements[j]))
        self.directComponentListWidget.itemSelectionChanged.connect(self.directComponentSelectionChanged)
        self.crossComponentListWidget.itemSelectionChanged.connect(self.crossComponentSelectionChanged)
        return Ne,Np
            
    def ASAXS_split_3(self):
        """
        Splits the energy dependent SAXS data into partial scattering factors i.e. contribution of scattering intensity 
        from different elements mentioned in Elements List Widget
        Please use x if you do not wish to put the element information of the elements other than the edge elements
        """
        if len(self.fnames)>=3:
            Ne,Np=self.prepareNewData()
            X=[]
            tot=[]
            self.components={}
            ans=QMessageBox.Yes
            f1=[self.xrdb.f1_chantler(element=self.elements[Np-1],energy=self.data[self.fnames[k]]['Energy']*1e3,smoothing=0) for k in range(Ne)]
            ans=QMessageBox.question(self,'Question','Do you like to look at each individual Q for this analysis?',QMessageBox.Yes, QMessageBox.No)
            self.ASAXSProgressBar.setMinimum(0)
            self.ASAXSProgressBar.setMaximum(self.BMatrix.shape[1])
            for i in range(self.BMatrix.shape[1]):
                X.append(sp.linalg.lstsq(self.AMatrix,self.BMatrix[:,i],lapack_driver='gelsd',check_finite=False,overwrite_a=True,overwrite_b=True)[0])
                tot.append(np.dot(self.AMatrix,X[-1]))            
                if ans==QMessageBox.Yes:
                    self.ASAXSCheckPlotWidget.setTitle('Q=%.5f'%self.qintp[i])
                    self.ASAXSCheckPlotWidget.add_data(f1,self.BMatrix[:,i],name='Data')
                    self.ASAXSCheckPlotWidget.add_data(f1,tot[-1],name='Fit',fit=True)
                    self.ASAXSCheckPlotWidget.Plot(['Data','Fit'])
                    self.raiseDock(self.ASAXSCheckPlotDock)
                    ans=QMessageBox.question(self,'Question','Do you like to see the next Q?',QMessageBox.Yes, QMessageBox.No)
                for key in self.AIndex.keys():
                    try:
                        self.components[key].append(X[-1][self.AIndex[key]]) 
                    except:
                        self.components[key]=[X[-1][self.AIndex[key]]]
                self.ASAXSProgressBar.setValue(i)
            #try:
            #    fplot.close()
            #except:
            #    pass
            for i in range(Np):
                key='S_%s-%s'%(self.elements[i],self.elements[i])
                self.components[key]=np.array(self.components[key])
                self.directComponentPlotWidget.add_data(self.qintp,self.components[key],name=key)
            tot=np.array(tot)
            #print(len(self.qintp),tot.shape)
            self.directComponentPlotWidget.add_data(self.qintp,tot[:,0],name='Total')
            self.directComponentListWidget.addItem('Total')
            self.directComponentPlotWidget.add_data(self.qintp,self.data[self.fnames[0]]['yintp'],name='data_%s'%self.datanames[0])
            self.directComponentListWidget.addItem('data_%s'%self.datanames[0])
            for i in range(Np-1):
                for j in range(i+1,Np):
                    key='S_%s-%s'%(self.elements[i],self.elements[j])
                    self.components[key]=np.array(self.components[key])
                    self.crossComponentPlotWidget.add_data(self.qintp,self.components[key],name=key)
            self.update_ASAXSPlot()
            self.directComponentListWidget.item(0).setSelected(True)
            self.crossComponentListWidget.item(0).setSelected(True)
            self.saveASAXSPushButton.setEnabled(True)
            self.ASAXSProgressBar.setValue(self.BMatrix.shape[1])
        else:
            QMessageBox.information(self,"ASAXS Error","Please select three or more data sets to get ASAXS components",QMessageBox.Ok)
            self.ASAXSProgressBar.reset()

    def directComponentSelectionChanged(self):
        items=[item.text() for item in self.directComponentListWidget.selectedItems()]
        self.directComponentPlotWidget.Plot(items)
        self.update_ASAXSPlot()
        
    def crossComponentSelectionChanged(self):
        items=[item.text() for item in self.crossComponentListWidget.selectedItems()]
        self.crossComponentPlotWidget.Plot(items)
        self.update_ASAXSPlot()
            
    def raiseDock(self,dock):
        """
        Raises the dock as the topmost
        """
        stack=dock.container().stack
        current=stack.currentWidget()
        current.label.setDim(True)
        stack.setCurrentWidget(dock)
        dock.label.setDim(False)
            
        
    def update_ASAXSPlot(self):
        """
        Updates the ASAXS plot
        """
        #datanames=[item.text().split(': ')[0] for item in self.dataListWidget.selectedItems()] 
        #if np.all(self.XMatrix[:,1]>0):
        #self.ASAXSPlotWidget.Plot(['Total','SAXS-term','Cross-term','Resonant-term'])
        #else:
        #    self.ASAXSPlotWidget.Plot(['Total','SAXS-term','neg Cross-term','Resonant-term'])
        self.raiseDock(self.ASAXSPlotDock)
        #self.mainDock.moveDock(self.ASAXSPlotDock,'above',self.dataPlotDock)
        
    def check_components(self):
        """
        Checks the scattering components
        """
        try:
            pg.plot(self.qintp,self.XMatrix[:,0]*self.XMatrix[:,2]/self.XMatrix[:,1]**2,line=None,symbol='o')
        except:
            QMessageBox.warning(self,'Components not found','Please split into the components first',QMessageBox.Ok)
        
        
    def save_ASAXS(self):
        fname=QFileDialog.getSaveFileName(self,caption='Save as',directory=self.dataDir,filter='Text files (*.txt)')[0]
        if fname!='':
            if os.path.splitext(fname)[1]=='':
                fname=fname+'.txt'
            #fh=open(fname,'w')
            header='Scattering components extracted on '+time.asctime()+'\n'
            header=header+'Data files used for the the scattering components calculations are:\n'
            for file in self.fnames:
                header=header+file+'\n'
            header=header+'col_names='+str(['Q(inv Angs)']+list(self.components.keys()))+'\n'
            header=header+'Q(inv Angs)\t'
            data=self.qintp
            for key in self.components.keys():
                header=header+key+'\t'
                data=np.vstack((data,self.components[key]))
            np.savetxt(fname,data.T,header=header)
        
    def open_ASAXS(self):
        fname=QFileDialog.getOpenFileName(self,caption='Save as',directory=self.dataDir,filter='Text files (*.txt)')[0]
        fh=open(fname,'r')
        lines=fh.readlines()
        data=[]
        for line in lines:
            if line[0]=='#':
                comment=line
            else:
               data.append(list(map(float, line.split())))
        data=np.array(data)
        keys=comment.split()
        self.components=={}
        i=0
        self.qintp=data[:,0]
        for key in keys[1:]:
            self.comoponents[key]=data[:,i]
            i+=1
        
        
        
        
        
if __name__=='__main__':
    app=QApplication(sys.argv)
    w=ASAXS_Widget()
    w.setWindowTitle('XAnoS Components')
    w.setGeometry(20,20,1000,800)
    
    w.show()
    sys.exit(app.exec_())
        
        
        
    

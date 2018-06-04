from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
from pyqtgraph.dockarea import *
import copy
import sys
import fabio as fb

class ImageCutWidget(QWidget):
    def __init__ ( self,parent=None):
        """
        A QWidget class to show a 2D image along with capabilities of generating and plotting several vertical and horizontal cuts image. The widget is using the libraries from pyqtgraph extensively
        """
        QWidget.__init__(self,parent)
        self.vblayout=QVBoxLayout(self)
        self.intDock=DockArea(self,parent)
        self.vblayout.addWidget(self.intDock)
        
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
        
        self.img_array=np.random.random(size=(1000,1000))
        self.caked_img_array=np.random.random(size=(1000,1000))
        self.caked_image_header=None
        self.caked_image_fname=None
        self.weights=np.where(self.caked_img_array>0,1,0)
        self.caked_img_err_array=np.zeros((1000,1000))
        self.hor_val=np.linspace(1,1000,1000)
        self.img_hor_val=copy.copy(self.hor_val)
        self.hor_Npt=1000
        self.img_hor_Npt=copy.copy(self.hor_Npt)
        self.ver_val=np.linspace(1,1000,1000)
        self.img_ver_val=copy.copy(self.ver_val)
        self.ver_Npt=1000
        self.img_ver_Npt=copy.copy(self.ver_Npt)
        self.xmin,self.xmax=(1,1000)
        self.img_xmin,self.img_xmax=(1,1000)
        self.ymin,self.ymax=(1,1000)
        self.img_ymin,self.img_ymax=(1,1000)
        self.imageParamDock=Dock("Image Parameters",size=(500,100))
        self.imageDock = Dock("Raw Image", size=(500,400))
        self.cakedImageDock=Dock("Caked Image", size=(500,400))
        self.verCutDock = Dock("Vertical Cuts", size=(500,200))
        self.horCutDock = Dock("Horizontal Cuts", size=(500,200))
        self.cutInfoDock = Dock("Cut Info", size=(500,200))
        
        ##Positioning the docks##
        self.intDock.addDock(self.cutInfoDock, 'left')
        self.intDock.addDock(self.imageParamDock, 'left')
        self.intDock.addDock(self.cakedImageDock,'left')
        self.intDock.addDock(self.imageDock, 'left')
        self.intDock.addDock(self.verCutDock, 'right')
        self.intDock.addDock(self.horCutDock, 'right')
        
        self.intDock.moveDock(self.cutInfoDock,'top',self.cakedImageDock)
        self.intDock.moveDock(self.imageParamDock,'top',self.imageDock)
        self.intDock.moveDock(self.cutInfoDock,'above',self.imageParamDock)
        self.intDock.moveDock(self.cakedImageDock,'above',self.imageDock)
        self.intDock.moveDock(self.horCutDock, 'top', self.verCutDock)
        
        ##Creating ImageParam Dock##
        self.imageParamLayout=pg.LayoutWidget()
        self.horMinLabel=QLabel('Horizontal Min')
        self.imageParamLayout.addWidget(self.horMinLabel,row=0,col=0)
        self.horMinLineEdit=QLineEdit('1')
        self.imageParamLayout.addWidget(self.horMinLineEdit,row=0,col=1)
        self.horMaxLabel=QLabel('Horizontal Max')
        self.imageParamLayout.addWidget(self.horMaxLabel,row=0,col=2)
        self.horMaxLineEdit=QLineEdit('1000')
        self.imageParamLayout.addWidget(self.horMaxLineEdit,row=0,col=3)
        self.horNptLabel=QLabel('Horizontal NPts')
        self.imageParamLayout.addWidget(self.horNptLabel,row=0,col=4)
        self.horNptLineEdit=QLineEdit('1000')
        self.imageParamLayout.addWidget(self.horNptLineEdit,row=0,col=5)
        self.horMinLabel=QLabel('Horizontal Min')
        
        self.verMinLabel=QLabel('Vertical Min')
        self.imageParamLayout.addWidget(self.verMinLabel,row=1,col=0)
        self.verMinLineEdit=QLineEdit('1')
        self.imageParamLayout.addWidget(self.verMinLineEdit,row=1,col=1)
        self.verMaxLabel=QLabel('Vertical Max')
        self.imageParamLayout.addWidget(self.verMaxLabel,row=1,col=2)
        self.verMaxLineEdit=QLineEdit('1000')
        self.imageParamLayout.addWidget(self.verMaxLineEdit,row=1,col=3)
        self.verNptLabel=QLabel('Vertical NPts')
        self.imageParamLayout.addWidget(self.verNptLabel,row=1,col=4)
        self.verNptLineEdit=QLineEdit('1000')
        self.imageParamLayout.addWidget(self.verNptLineEdit,row=1,col=5)
        self.imageParamDock.addWidget(self.imageParamLayout)
        
        
        ##Creating the 2D Image dock## 
        ##Raw image view##
        self.imageLayout=pg.LayoutWidget()
        self.imageView=pg.ImageView(view=pg.PlotItem(labels={'left':('Vertical scale'),'bottom':'Horizontal scale'}))
        self.create_colorMap(self.imageView,np.amin(self.img_array),np.amax(self.img_array),scale='linear')
        self.imageView.setImage(self.img_array)
        self.imageView.view.invertY(False)
        self.imageLayout.addWidget(self.imageView,row=0,col=0,colspan=6)
        self.imageLogCheckBox=QCheckBox('Log Intensity')
        self.imageLogCheckBox.setCheckState(True)
        self.imageLayout.addWidget(self.imageLogCheckBox,row=1,col=0,colspan=1)
        self.imageCrossHair=QLabel()
        self.imageCrossHair.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.imageLayout.addWidget(self.imageCrossHair,row=1,col=1,colspan=5)
        self.imageDock.addWidget(self.imageLayout)
        self.imageView.getView().vb.scene().sigMouseMoved.connect(self.image_mouseMoved)
        
        ##Caked image view##
        self.cakedImageLayout=pg.LayoutWidget()
        self.cakedImageView=pg.ImageView(view=pg.PlotItem(labels={'left':('Vertical scale'),'bottom':'Horizontal scale'}))
        self.create_colorMap(self.cakedImageView,np.amin(self.caked_img_array),np.amax(self.caked_img_array),scale='linear')
        self.cakedImageView.setImage(self.caked_img_array)
        self.cakedImageView.view.invertY(False)
        self.cakedImageLayout.addWidget(self.cakedImageView,row=0,col=0,colspan=6) 
        self.cakedImageLogCheckBox=QCheckBox('Log Intensity')
        self.cakedImageLogCheckBox.setChecked(False)
        self.cakedImageLayout.addWidget(self.cakedImageLogCheckBox,row=1,col=0,colspan=1)       
        self.cakedImageCrossHair=QLabel()
        self.cakedImageCrossHair.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.cakedImageLayout.addWidget(self.cakedImageCrossHair,row=1,col=1,colspan=5)
        self.cakedImageDock.addWidget(self.cakedImageLayout)
        self.cakedImageView.getView().vb.scene().sigMouseMoved.connect(self.cakedImage_mouseMoved)
        
        
        ##Creating Cut Info Table Widget##
        self.cutItems={}
        self.colorButtons={}
        self.lineColors={}
        self.lineWidths={}
        self.cut_pos={} #Positions of the cuts
        self.cut_width={} #Widths of the cuts
        self.cut_data={}
        self.avg_count=0
        self.linked_keys={}
        self.cut_plot_items={}
        self.cut_topErr_plot_items={}
        self.cut_botErr_plot_items={}
        self.err_fillBetwin={}
        self.errBarColor=[0,0,0,50]
        self.cutInfoLayout=pg.LayoutWidget()
        self.cutInfoDock.addWidget(self.cutInfoLayout)
        cutTypeLabel=QLabel('Cut type')
        cutTypeLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.cutInfoLayout.addWidget(cutTypeLabel,row=0,col=0)
        self.cutTypeComboBox=pg.ComboBox(items=['Horizontal','Vertical'])
        self.cutInfoLayout.addWidget(self.cutTypeComboBox,row=0,col=1)
        self.addCutPushButton=QPushButton('Add')
        self.cutInfoLayout.addWidget(self.addCutPushButton,row=0,col=2)
        self.removeSelectedPushButton=QPushButton('Remove Selected')
        self.cutInfoLayout.addWidget(self.removeSelectedPushButton,row=0,col=3)
        self.avgSelectedPushButton=QPushButton('Avergage Selected')
        self.cutInfoLayout.addWidget(self.avgSelectedPushButton,row=0,col=4)
        self.saveAllPushButton=QPushButton('Save all cuts')
        self.cutInfoLayout.addWidget(self.saveAllPushButton,row=0,col=5)
        self.cutInfoTableWidget=QTableWidget(0,7)
        self.cutInfoTableWidget.setHorizontalHeaderLabels(['Cut','Position','Width','Line color','Line width','Show','AutoSave'])
        self.cutInfoTableWidget.resizeColumnsToContents()
        self.cutInfoLayout.addWidget(self.cutInfoTableWidget,row=1,col=0,colspan=6)
        
        
        ##Creating the Horizontal Cut plot##
        self.horPlotLayout=pg.LayoutWidget()
        self.horCutDock.addWidget(self.horPlotLayout)
        self.horCutPlot=pg.PlotWidget(labels={'left':'Intensity','bottom':'Horizontal scale'},title='Horizontal Cuts')
        self.horPlotLayout.addWidget(self.horCutPlot,row=0,col=0,colspan=4)
        self.horXLogCheckBox=QCheckBox('LogX')
        self.horPlotLayout.addWidget(self.horXLogCheckBox,row=1,col=0)
        self.horYLogCheckBox=QCheckBox('LogY')
        self.horPlotLayout.addWidget(self.horYLogCheckBox,row=1,col=1)
        self.horCrossHair=QLabel('X=%.6f, I=%.3e'%(0.0,0.0))
        self.horCrossHair.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.horPlotLayout.addWidget(self.horCrossHair,row=1,col=2,colspan=2)
        self.horVB=self.horCutPlot.plotItem.vb
        self.horCutPlot.scene().sigMouseMoved.connect(self.horCut_mouseMoved)
        self.horCutPlot.addLegend()
        
        
        ##Creating the Vertical Cut plot##
        self.verPlotLayout=pg.LayoutWidget()
        self.verCutDock.addWidget(self.verPlotLayout)
        self.verCutPlot=pg.PlotWidget(labels={'left':'Intensity','bottom':'Vertical scale'},title='Vertical cuts')
        self.verPlotLayout.addWidget(self.verCutPlot,row=0,col=0,colspan=4)
        self.verXLogCheckBox=QCheckBox('LogX')
        self.verPlotLayout.addWidget(self.verXLogCheckBox,row=1,col=0)
        self.verYLogCheckBox=QCheckBox('LogY')
        self.verPlotLayout.addWidget(self.verYLogCheckBox,row=1,col=1)
        self.verLineWidthSpinBox=pg.SpinBox(value=2,bounds=(1,10),step=1,int=True)
        self.verCrossHair=QLabel('X=%.6f, I=%.3e'%(0.0,0.0))
        self.verCrossHair.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.verPlotLayout.addWidget(self.verCrossHair,row=1,col=2,colspan=2)
        self.verVB=self.verCutPlot.plotItem.vb
        self.verCutPlot.scene().sigMouseMoved.connect(self.verCut_mouseMoved)
        self.verCutPlot.addLegend()
        
        self.init_signals()
        pg.QtGui.QApplication.processEvents()
        
    
        
    def init_signals(self):
        """
        Initialize all the signals
        """
        #Signals corresponding to pushbuttons
        self.addCutPushButton.clicked.connect(lambda x: self.add_cut(show=True,autoSave=False))
        self.removeSelectedPushButton.clicked.connect(self.remove_cut)
        self.avgSelectedPushButton.clicked.connect(self.create_avg_data)
        self.saveAllPushButton.clicked.connect(self.save_all_cuts)
        
        self.cutInfoTableWidget.itemChanged.connect(self.change_cut)
        self.horXLogCheckBox.stateChanged.connect(self.cutLogLinearMode)
        self.verXLogCheckBox.stateChanged.connect(self.cutLogLinearMode)
        self.horYLogCheckBox.stateChanged.connect(self.cutLogLinearMode)
        self.verYLogCheckBox.stateChanged.connect(self.cutLogLinearMode)
        self.imageLogCheckBox.stateChanged.connect(self.imageLogLinear)
        self.cakedImageLogCheckBox.stateChanged.connect(self.cakedImageLogLinear)
        
        
    def set_image_labels(self,xlabel='Horizontal',ylabel='Vertical',title='Caked Image',fontsize=3):
        """
        Sets the x and y labels of the image
        
        :xlabel: Any text or html code is acceptable
        :ylabel: Any text or html code is acceptable
        """
        self.cakedImageView.getView().setLabels(bottom= ['<span><font size=\"'+str(fontsize)+'\">'+xlabel+'</font></span>','<span><font size=\"'+str(fontsize)+'\">'+self.unit[0]+'</font></span>'],left=['<span><font size=\"'+str(fontsize)+'\">'+ylabel+'</font></span>','<span><font size=\"'+str(fontsize)+'\">'+self.unit[1]+'</font></span>'])
        self.cakedImageView.getView().setTitle(title='<span><font size=\"'+str(fontsize)+'\">'+title+'</font></span>')
        
    def set_horCut_labels(self,xlabel='hor_val',ylabel='I',title='Horizontal Cuts',fontsize=3):
        """
        Sets the x and y labels of the the horizontal cut plot
        
        :xlabel: Any text or html code is acceptable
        :ylabel: Any text or html code is acceptable
        """
        self.horCutPlot.setLabels(bottom= ['<span><font size=\"'+str(fontsize)+'\">'+xlabel+'</font></span>','<span><font size=\"'+str(fontsize)+'\">'+self.unit[0]+'</font></span>'],left=['<span><font size=\"'+str(fontsize)+'\">'+ylabel+'</font></span>',''])
        self.horCutPlot.setTitle(title='<span><font size=\"'+str(fontsize)+'\">'+title+'</font></span>')
        
    def set_verCut_labels(self,xlabel='hor_val',ylabel='I',title='Vertical Cuts', fontsize=3):
        """
        Sets the x and y labels of the verical cut plots
        
        :xlabel: Any text or html code is acceptable
        :ylabel: Any text or html code is acceptable
        """
        self.verCutPlot.setLabels(bottom= ['<span><font size=\"'+str(fontsize)+'\">'+xlabel+'</font></span>','<span><font size=\"'+str(fontsize)+'\">'+self.unit[1]+'</font></span>'],left=['<span><font size=\"'+str(fontsize)+'\">'+ylabel+'</font></span>',''])
        self.verCutPlot.setTitle(title='<span><font size=\"'+str(fontsize)+'\">'+title+'</font></span>')

    def create_colorMap(self,imageView,min,max,scale='linear'):
        """
        Creates a colorMap with min and max values with linear or log scale
        """        
        if scale=='linear':
            colorPos=min+(max-min)*self.colorPos
        else:
            colorPos=10**np.linspace(np.log10(min),np.log10(max),7)
            colorPos=np.insert(colorPos,2,10**(np.log10(min)+1.0*(np.log10(max)-np.log10(min))/4.0))
        map=pg.ColorMap(colorPos,self.colorVal)
        imageView.ui.histogram.gradient.setColorMap(map)
        
    def imageLogLinear(self):
        """
        Converts the image log-linear scale
        """
        array_masked=np.ma.masked_less(self.img_array,1e-12)
        min,max=np.ma.min(array_masked),np.ma.max(array_masked)
        if self.imageLogCheckBox.isChecked():
            self.imageView.setImage(np.log10(np.where(self.img_array<=0.0,1e-12,self.img_array)),levels=(np.log10(min),np.log10(max)),pos=self.img_pos,scale=self.img_scale)
        else:
            self.imageView.setImage(self.img_array,levels=(min,max),pos=self.img_pos,scale=self.img_scale)
        pg.QtGui.QApplication.processEvents()
        
    def cakedImageLogLinear(self):
        """
        Converts the image log-linear scale of the caked Image
        """
        array_masked=np.ma.masked_less(self.caked_img_array,1e-12)
        min,max=np.ma.min(array_masked),np.ma.max(array_masked)
        if self.cakedImageLogCheckBox.isChecked():
            self.cakedImageView.setImage(np.log10(np.where(self.caked_img_array<=0.0,1e-12,self.caked_img_array)),levels=(np.log10(min),np.log10(max)),pos=self.pos,scale=self.scale)
        else:
            self.cakedImageView.setImage(self.caked_img_array,levels=(min,max),pos=self.pos,scale=self.scale)
        self.cakedImageView.view.setAspectLocked(False)
        pg.QtGui.QApplication.processEvents()
        
        
    def cakedImage_mouseMoved(self,pos):
        """
        Shows the mouse position of 2D Caked Image on its crosshair label
        """
        pointer=self.cakedImageView.getView().vb.mapSceneToView(pos)
        x,y=pointer.x(),pointer.y()
        if (x>self.xmin) and (x<self.xmax) and (y>self.ymin) and (y<self.ymax):
            self.cakedImageCrossHair.setText('X=%.6f, Y=%.6f, I=%.5e'%(x,y,self.caked_img_array[int((x-self.xmin)*self.hor_Npt/(self.xmax-self.xmin)),int((y-self.ymin)*self.ver_Npt/(self.ymax-self.ymin))]))
        else:
            self.cakedImageCrossHair.clear()
            
    def image_mouseMoved(self,pos):
        """
        Shows the mouse position of 2D Image on its crosshair label
        """
        pointer=self.imageView.getView().vb.mapSceneToView(pos)
        x,y=pointer.x(),pointer.y()
        if (x>self.img_xmin) and (x<self.img_xmax) and (y>self.img_ymin) and (y<self.img_ymax):
            self.imageCrossHair.setText('X=%.6f, Y=%.6f, I=%.5e'%(x,y,self.img_array[int((x-self.img_xmin)*self.img_hor_Npt/(self.img_xmax-self.img_xmin)),int((y-self.img_ymin)*self.img_ver_Npt/(self.img_ymax-self.img_ymin))]))
        else:
            self.imageCrossHair.clear()
            
    def horCut_mouseMoved(self,pos):
        """
        Shows the mouse position of horizontal cut plot on its crosshair label
        """
        if self.horCutPlot.sceneBoundingRect().contains(pos):
            point = self.horVB.mapSceneToView(pos)
            x,y=point.x(),point.y()
            if self.horXLogCheckBox.isChecked():
                x=10**x
            if self.horYLogCheckBox.isChecked():
                y=10**y
            self.horCrossHair.setText('X=%.6f, I=%.3e'%(x,y))
        else:
            self.horCrossHair.clear()
            
    def verCut_mouseMoved(self,pos):
        """
        Shows the mouse position of horizontal cut plot on its crosshair label
        """
        if self.verCutPlot.sceneBoundingRect().contains(pos):
            point = self.verVB.mapSceneToView(pos)
            x,y=point.x(),point.y()
            if self.verXLogCheckBox.isChecked():
                x=10**x
            if self.verYLogCheckBox.isChecked():
                y=10**y
            self.verCrossHair.setText('X=%.6f, I=%.3e'%(x,y))
        else:
            self.verCrossHair.clear()
            
    def addCakedImage(self,caked_img_array,caked_img_err_array,hor_val=None,ver_val=None,header=None,fname=None,unit=['pixels','pixels']):
        """
        Imports caked_image_array or processed image array with horizontal and vertical scale values.
        
        This function is used in SAXS/WAXS data reduction process
        
        :caked_img_array: A 2D array corresponding to the caked image
        :caked_img_err: A 2D array of same dimension as :caked_img_array: which stores the error estimates of the image
        :hor_val: A list of values containing the horizontal pixel co-ordinates of the image (default=None)
        :ver_val: A list of values containing the vertical pixel co-ordinates of the image (default=None)
        :header: Header information in the form of a dictionary (default=None)
        :fname: Any file name with path and without extension associated with the image (defaul=None).
        :unit: Unit of the horizontal and vertical scales of the image          
        
        """
        self.caked_img_array=caked_img_array
        self.caked_image_header=header
        self.caked_image_fname=fname
        self.unit=unit
        self.weights=np.where(self.caked_img_array>0,1,0)
        self.caked_img_err_array=caked_img_err_array
        if hor_val is not None:
            self.hor_val=hor_val
        else:
            self.hor_val=np.arange(caked_img_array.shape[0])
        if ver_val is not None:
            self.ver_val=ver_val
        else:
            self.ver_val=np.arange(caked_img_array.shape[1])
        self.hor_Npt=len(self.hor_val)
        self.ver_Npt=len(self.ver_val)
        self.xmin=np.amin(self.hor_val)
        self.xmax=np.amax(self.hor_val)
        self.ymin=np.amin(self.ver_val)
        self.ymax=np.amax(self.ver_val)
        self.horMinLineEdit.setText('%.5f'%self.xmin)
        self.horMaxLineEdit.setText('%.5f'%self.xmax)
        self.verMinLineEdit.setText('%.5f'%self.ymin)
        self.verMaxLineEdit.setText('%.5f'%self.ymax)
        self.horNptLineEdit.setText('%d'%self.hor_Npt)
        self.verNptLineEdit.setText('%d'%self.ver_Npt)
        self.pos=[np.amin(self.hor_val),np.amin(self.ver_val)]
        self.scale=[np.abs(self.hor_val[1]-self.hor_val[0]),np.abs(self.ver_val[1]-self.ver_val[0])]
        #self.cakedImageView.setImage(self.caked_img_array,pos=pos,scale=scale)
        self.cakedImageLogLinear()
        for key in self.cutItems.keys():
            self.get_cut_data(key)
            self.update_avg_data()
            tableItem=self.cutInfoTableWidget.findItems(key,Qt.MatchExactly)
            row=self.cutInfoTableWidget.row(tableItem[0])
            if self.cutInfoTableWidget.item(row,5).checkState()>0:
                self.plot_cut_data(key)
        self.auto_save_cuts()
        pg.QtGui.QApplication.processEvents()
            
        
        
        
    def addImage(self,img_array,hor_val,ver_val,header=None,fname=None,unit=['pixels','pixels']):
        """
        Imports raw image along with the horizontal and vertical scale values.
        
        :img_array: A 2D array corresponding to an image_file
        :hor_val: A list of values containing the horizontal pixel co-ordinates of the image
        :ver_val: A list of values containing the vertical pixel co-ordinates of the image
        :header: Header information in the form of a dictionary (default=None)
        :fname: Any file name with path and without extension associated with the image (defaul=None). 
        :unit: Unit of the horizontal and vertical scales of the image     
        """
        self.img_array=img_array
        self.img_header=header
        self.img_fname=fname
        self.unit=unit
        if hor_val is not None:
            self.img_hor_val=hor_val
        else:
            self.img_hor_val=np.range(img_array.shape[0])
        if ver_val is not None:
            self.img_ver_val=ver_val
        else:
            self.img_ver_val=np.range(img_array.shape[1])  
        
        self.img_hor_Npt=len(self.img_hor_val)
        self.img_ver_Npt=len(self.img_ver_val)
        self.img_xmin=np.amin(self.hor_val)
        self.img_xmax=np.amax(self.hor_val)
        self.img_ymin=np.amin(self.ver_val)
        self.img_ymax=np.amax(self.ver_val)
        self.img_pos=[np.amin(self.img_hor_val),np.amin(self.img_ver_val)]
        self.img_scale=[np.abs(self.hor_val[1]-self.hor_val[0]),np.abs(self.ver_val[1]-self.ver_val[0])]
        self.imageLogLinear(pos=self.img_pos,scale=self.img_scale)
        #self.imageView.setImage(self.img_array,pos=pos,scale=scale)
        
            
    def add_cut(self,pos=None,width=None,show=True,autoSave=False):
        """
        Adds cut into the CutTableWidget and in the plots simultaneously
        """
        try:
            self.cutInfoTableWidget.itemChanged.disconnect(self.change_cut)
        except:
            pass
        row=self.cutInfoTableWidget.rowCount()
        self.cutInfoTableWidget.insertRow(row)
        if str(self.cutTypeComboBox.currentText())=='Horizontal':
            key='hor_'+str(row)
            #self.intDock.moveDock(self.horCutDock, 'above', self.verCutDock)
            self.cutInfoTableWidget.setItem(row,0,QTableWidgetItem('hor_'+str(row)))
            max=float(self.verMaxLineEdit.text())
            min=float(self.verMinLineEdit.text())
            if pos is not None:
                self.cut_pos[key]=pos
            else:
                self.cut_pos[key]=(max+min)/2.0
            if width is not None:
                self.cut_width[key]=width
            else:
                self.cut_width[key]=(max-min)
            self.cutInfoTableWidget.setItem(row,1,QTableWidgetItem('%.5f'%self.cut_pos[key])) #Setting the position
            self.cutInfoTableWidget.setItem(row,2,QTableWidgetItem('%.6f'%(self.cut_width[key]))) #Setting the width
            color=np.random.randint(256,size=4)
            color[3]=50
            self.colorButtons[key]=pg.ColorButton(self.cutInfoTableWidget,color=color)
            self.cutInfoTableWidget.setCellWidget(row,3,self.colorButtons[key])
            self.lineColors[key]=self.colorButtons[key].color().getRgb()[:3]
            self.colorButtons[key].sigColorChanging.connect(self.colorChanged)
            self.colorButtons[key].sigColorChanging.connect(self.colorChanged)
            self.lineWidths[key]=2
            self.cutInfoTableWidget.setItem(row,4,QTableWidgetItem('%d'%(self.lineWidths[key])))
            self.cutItems[key]=pg.LinearRegionItem(values=[self.cut_pos[key]-self.cut_width[key]/2.0,self.cut_pos[key]+self.cut_width[key]/2],orientation=pg.LinearRegionItem.Horizontal,bounds=[min,max],movable=True,brush=pg.mkBrush(self.colorButtons[key].color()))
            self.cakedImageView.addItem(self.cutItems['hor_'+str(row)])
            self.cutItems[key].sigRegionChanged.connect(self.cut_item_changed)
            self.cutItems[key].sigRegionChangeFinished.connect(self.cut_item_change_finished)           
        else:
            key='ver_'+str(row)
            #self.intDock.moveDock(self.verCutDock, 'above', self.horCutDock)
            self.cutInfoTableWidget.setItem(row,0,QTableWidgetItem('ver_'+str(row)))
            max=float(self.horMaxLineEdit.text())
            min=float(self.horMinLineEdit.text())
            if pos is not None:
                self.cut_pos[key]=pos
            else:
                self.cut_pos[key]=(max+min)/2.0
            if width is not None:
                self.cut_width[key]=width
            else:
                self.cut_width[key]=(max-min)
            self.cutInfoTableWidget.setItem(row,1,QTableWidgetItem('%.5f'%self.cut_pos[key])) #Setting the position
            self.cutInfoTableWidget.setItem(row,2,QTableWidgetItem('%.6f'%(self.cut_width[key]))) #Setting the width
            color=np.random.randint(256,size=4)
            color[3]=50
            self.colorButtons[key]=pg.ColorButton(self.cutInfoTableWidget,color=color)
            self.cutInfoTableWidget.setCellWidget(row,3,self.colorButtons[key])
            self.lineColors[key]=self.colorButtons[key].color().getRgb()[:3]
            self.colorButtons[key].sigColorChanging.connect(self.colorChanged)
            self.colorButtons[key].sigColorChanging.connect(self.colorChanged)
            self.lineWidths[key]=2
            self.cutInfoTableWidget.setItem(row,4,QTableWidgetItem('%d'%(self.lineWidths[key])))
            self.cutItems[key]=pg.LinearRegionItem(values=[self.cut_pos[key]-self.cut_width[key]/2.0,self.cut_pos[key]+self.cut_width[key]/2.0],orientation=pg.LinearRegionItem.Vertical,bounds=[min,max],movable=True,brush=pg.mkBrush(self.colorButtons[key].color()))
            self.cakedImageView.addItem(self.cutItems['ver_'+str(row)])
            self.cutItems[key].sigRegionChanged.connect(self.cut_item_changed)
            self.cutItems[key].sigRegionChangeFinished.connect(self.cut_item_change_finished)
        
        self.cutInfoTableWidget.setItem(row,5,QTableWidgetItem(''))
        item=self.cutInfoTableWidget.item(row,5)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        if show:
            self.cutInfoTableWidget.item(row,5).setCheckState(Qt.Checked)
        else:
            self.cutInfoTableWidget.item(row,5).setCheckState(Qt.Unchecked)
        self.cutInfoTableWidget.setItem(row,6,QTableWidgetItem(''))
        item=self.cutInfoTableWidget.item(row,6)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)        
        if autoSave:
            self.cutInfoTableWidget.item(row,6).setCheckState(Qt.Checked)
        else:
            self.cutInfoTableWidget.item(row,6).setCheckState(Qt.Unchecked)
            
        for i in [1,2]:
            item=self.cutInfoTableWidget.item(row,i)
            item.setFlags(item.flags()|Qt.ItemIsSelectable)
        self.cutInfoTableWidget.resizeColumnsToContents()
        self.get_cut_data(key)
        self.plot_cut_data(key)
        self.old_key=key
        self.cutInfoTableWidget.itemChanged.connect(self.change_cut)
        
    def colorChanged(self,btn):
        """
        Changes the color or LinearRegionItem and the integrated plots corresponding to the button
        """
        key=[k for k in self.colorButtons.keys() if self.colorButtons[k]==btn]
        try:
            self.cutItems[key[0]].setBrush(self.colorButtons[key[0]].color())
        except:
            pass
        self.lineColors[key[0]]=self.colorButtons[key[0]].color().getRgb()[:3]
        self.cut_plot_items[key[0]].setPen(pg.mkPen(color=self.lineColors[key[0]],width=self.lineWidths[key[0]]))
        
        
    def remove_cut(self):
        """
        Removes the selected cuts from the cutInfoTableWidget
        """
        sel_items=self.cutInfoTableWidget.selectedItems()
        rows=list(set([item.row() for item in sel_items]))
        for row in rows:
            #row=item.row()
            key=str(self.cutInfoTableWidget.item(row,0).text())
            if np.all(key not in self.linked_keys[tkey] for tkey in self.linked_keys.keys()):
                try: #This is implemented such that for the avg cuts the function doesnot read the pos and width of the cuts
                    self.cakedImageView.getView().removeItem(self.cutItems[key])
                except:
                    pass
                if key[:3]=='hor':
                    self.horCutPlot.removeItem(self.cut_plot_items[key])
                    self.horCutPlot.removeItem(self.cut_topErr_plot_items[key])
                    self.horCutPlot.removeItem(self.cut_botErr_plot_items[key])
                    self.horCutPlot.removeItem(self.err_fillBetwin[key])
                    self.horCutPlot.plotItem.legend.removeItem(key)
                else:
                    self.verCutPlot.removeItem(self.cut_plot_items[key])
                    self.verCutPlot.removeItem(self.cut_topErr_plot_items[key])
                    self.verCutPlot.removeItem(self.cut_botErr_plot_items[key])
                    self.verCutPlot.removeItem(self.err_fillBetwin[key])
                    self.verCutPlot.plotItem.legend.removeItem(key)                
                del self.cut_plot_items[key]
                del self.cut_data[key]
                try: #This is implemented such that for the avg cuts the function doesnot read the pos and width of the cuts
                    del self.cut_pos[key]
                    del self.cut_width[key]
                except:
                    pass
                del self.lineColors[key]
                del self.lineWidths[key]
                self.cutInfoTableWidget.removeRow(row)
            else:
                QMessageBox.warning(self, 'Some of the selected keys are involved in the average calculation. Please remove the average first.')
            

    def change_cut(self,item):
        """
        Change the ROIs and the cuts reading the info from CutInfoTableWidget
        """
        row=item.row()
        key=str(self.cutInfoTableWidget.item(row,0).text())
        try: #This is implemented such that for the avg cuts the function doesnot read the pos and width of the cuts
            self.cut_pos[key]=float(self.cutInfoTableWidget.item(row,1).text())
            self.cut_width[key]=float(self.cutInfoTableWidget.item(row,2).text())
        except:
            pass
        self.lineWidths[key]=int(self.cutInfoTableWidget.item(row,4).text())
        if self.cutInfoTableWidget.item(row,5).checkState()>0:
            try: #This is implemented such that for the avg cuts the function doesnot read the pos and width of the cuts
                self.cutItems[key].setRegion((self.cut_pos[key]-self.cut_width[key]/2.0,self.cut_pos[key]+self.cut_width[key]/2.0))
                self.get_cut_data(key)
            except:
                pass
            if key[:3]=='hor':
                self.horCutPlot.plotItem.legend.removeItem(key)
                self.horCutPlot.removeItem(self.cut_plot_items[key])
                self.horCutPlot.removeItem(self.cut_topErr_plot_items[key])
                self.horCutPlot.removeItem(self.cut_botErr_plot_items[key])
                self.horCutPlot.removeItem(self.err_fillBetwin[key])
                self.cut_plot_items[key]=self.horCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1],connect='finite',pen=pg.mkPen(self.lineColors[key],width=self.lineWidths[key]),name=key)
                self.cut_topErr_plot_items[key]=self.horCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]+self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
                self.cut_botErr_plot_items[key]=self.horCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]-self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
                self.err_fillBetwin[key]=pg.FillBetweenItem(self.cut_topErr_plot_items[key],self.cut_botErr_plot_items[key],brush=pg.mkBrush(self.errBarColor))
                self.horCutPlot.addItem(self.err_fillBetwin[key])
            else:
                self.verCutPlot.plotItem.legend.removeItem(key)
                self.verCutPlot.removeItem(self.cut_plot_items[key])
                self.verCutPlot.removeItem(self.cut_topErr_plot_items[key])
                self.verCutPlot.removeItem(self.cut_botErr_plot_items[key])
                self.verCutPlot.removeItem(self.err_fillBetwin[key])
                self.cut_plot_items[key]=self.verCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1],connect='finite',pen=pg.mkPen(self.lineColors[key],width=self.lineWidths[key]),name=key)
                self.cut_topErr_plot_items[key]=self.verCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]+self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
                self.cut_botErr_plot_items[key]=self.verCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]-self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
                self.err_fillBetwin[key]=pg.FillBetweenItem(self.cut_topErr_plot_items[key],self.cut_botErr_plot_items[key],brush=pg.mkBrush(self.errBarColor))
                self.verCutPlot.addItem(self.err_fillBetwin[key])
        else:
            if key[:3]=='hor':
                self.horCutPlot.removeItem(self.cut_plot_items[key])
                self.horCutPlot.removeItem(self.cut_topErr_plot_items[key])
                self.horCutPlot.removeItem(self.cut_botErr_plot_items[key])
                self.horCutPlot.removeItem(self.err_fillBetwin[key])
                self.horCutPlot.plotItem.legend.removeItem(key)
            else:
                self.verCutPlot.removeItem(self.cut_plot_items[key])
                self.verCutPlot.removeItem(self.cut_topErr_plot_items[key])
                self.verCutPlot.removeItem(self.cut_botErr_plot_items[key])
                self.verCutPlot.removeItem(self.err_fillBetwin[key])
                self.verCutPlot.plotItem.legend.removeItem(key)                
        self.cutLogLinearMode()
    
    def cutLogLinearMode(self):
        if self.horXLogCheckBox.isChecked():
            self.horCutPlot.setLogMode(x=True)
        else:
            self.horCutPlot.setLogMode(x=False)
        if self.horYLogCheckBox.isChecked():
            self.horCutPlot.setLogMode(y=True)
        else:
            self.horCutPlot.setLogMode(y=False)
        if self.verXLogCheckBox.isChecked():
            self.verCutPlot.setLogMode(x=True)
        else:
            self.verCutPlot.setLogMode(x=False)
        if self.verYLogCheckBox.isChecked():
            self.verCutPlot.setLogMode(y=True)
        else:
            self.verCutPlot.setLogMode(y=False)
            
    def cut_item_changed(self,cut):
        """        
        """
        key=self.cutItemKey_from_cutObject(cut)
        #if key!=self.old_key:
        #    if key[:3]=='hor':
        #        self.intDock.moveDock(self.horCutDock, 'above', self.verCutDock)
        #    else:
        #        self.intDock.moveDock(self.verCutDock, 'above', self.horCutDock)
        #    self.old_key=key
        min,max=self.cutItems[key].getRegion()
        self.cut_pos[key],self.cut_width[key]=(max+min)/2.0,max-min
        tableItem=self.cutInfoTableWidget.findItems(key,Qt.MatchExactly)
        row=self.cutInfoTableWidget.row(tableItem[0])
        try:
            self.cutInfoTableWidget.itemChanged.disconnect(self.change_cut)
        except:
            pass
        self.cutInfoTableWidget.item(row,1).setText('%.5f'%self.cut_pos[key])
        self.cutInfoTableWidget.item(row,2).setText('%.6f'%self.cut_width[key])
        self.cutInfoTableWidget.itemChanged.connect(self.change_cut)
        self.get_cut_data(key)
        self.update_avg_data()
        if self.cutInfoTableWidget.item(row,5).checkState()>0:
            self.plot_cut_data(key)
        
    def cut_item_change_finished(self,cut):
        """
        """
        self.change_cut_view=1
        self.auto_save_cuts()              
    
        
    def plot_cut_data(self,key):
        """
        Add a line plot to either horizontal cut plot or vertical cut plot depending on the key
        """
        if key in self.cut_plot_items.keys():
            self.cut_plot_items[key].setData(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1],connect='finite',pen=pg.mkPen(self.lineColors[key],width=self.lineWidths[key]),name=key)
            self.cut_topErr_plot_items[key].setData(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]+self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
            self.cut_botErr_plot_items[key].setData(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]-self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
            self.err_fillBetwin[key].setCurves(self.cut_topErr_plot_items[key],self.cut_botErr_plot_items[key])
            self.err_fillBetwin[key].setBrush(pg.mkBrush(self.errBarColor))
        else:
            if key[:3]=='hor':
                self.cut_plot_items[key]=self.horCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1],connect='finite',pen=pg.mkPen(self.lineColors[key],width=self.lineWidths[key]),name=key)
                self.cut_topErr_plot_items[key]=self.horCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]+self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
                self.cut_botErr_plot_items[key]=self.horCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]-self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
                self.err_fillBetwin[key]=pg.FillBetweenItem(self.cut_topErr_plot_items[key],self.cut_botErr_plot_items[key],brush=pg.mkBrush(self.errBarColor))
                self.horCutPlot.addItem(self.err_fillBetwin[key])
            else:
                self.cut_plot_items[key]=self.verCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1],connect='finite',pen=pg.mkPen(self.lineColors[key],width=self.lineWidths[key]),name=key)
                self.cut_topErr_plot_items[key]=self.verCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]+self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
                self.cut_botErr_plot_items[key]=self.verCutPlot.plot(self.cut_data[key]['data'][:,0],self.cut_data[key]['data'][:,1]-self.cut_data[key]['data'][:,2]/2.0,connect='finite',pen=pg.mkPen(self.errBarColor,width=1))
                self.err_fillBetwin[key]=pg.FillBetweenItem(self.cut_topErr_plot_items[key],self.cut_botErr_plot_items[key],brush=pg.mkBrush(self.errBarColor))
                self.verCutPlot.addItem(self.err_fillBetwin[key])
        self.cutLogLinearMode()

        
    def get_cut_data(self,key):
        """
        Computes the integrated cut data corresponding to a key
        """
        self.cut_data[key]={}
        if key[:3]=='hor':
            min,max=self.cutItems[key].getRegion()
            if min!=max:
                start=np.argwhere(self.ver_val>min)[0][0]
                end=np.argwhere(self.ver_val<max)[-1][0]
                int_data=np.ma.average(self.caked_img_array[:,start:end],axis=1,weights=self.weights[:,start:end])
                int_data_err=np.sqrt(np.ma.average(self.caked_img_err_array[:,start:end]**2,axis=1,weights=self.weights[:,start:end]))/np.sqrt(np.sum(self.weights[:,start:end],axis=1))
                self.cut_data[key]['data']=np.vstack((self.hor_val,int_data,int_data_err)).T
            else:
                self.cut_data[key]['data']=np.vstack((self.hor_val,np.zeros_like(self.hor_val),np.zeros_like(self.hor_val))).T
            self.cut_data[key]['info']='# Horzontal cut at %.6f with width=%.6f\n'%(self.cut_pos[key],self.cut_width[key])
        else:
            min,max=self.cutItems[key].getRegion()
            if min!=max:
                start=np.argwhere(self.hor_val>min)[0][0]
                end=np.argwhere(self.hor_val<max)[-1][0]
                int_data=np.ma.average(self.caked_img_array[start:end,:],axis=0,weights=self.weights[start:end,:])
                int_data_err=np.sqrt(np.ma.average(self.caked_img_err_array[start:end,:]**2,axis=0,weights=self.weights[start:end,:]))/np.sqrt(np.sum(self.weights[start:end,:],axis=0))
                self.cut_data[key]['data']=np.vstack((self.ver_val,int_data,int_data_err)).T                
            else:
                self.cut_data[key]['data']=np.vstack((self.ver_val,np.zeros_like(self.ver_val),np.zeros_like(self.ver_val))).T
            self.cut_data[key]['info']='#Vertical cut at %.6f with width=%.6f\n'%(self.cut_pos[key],self.cut_width[key])    
        #self.cut_data[key]['data']=self.check_for_logScale(self.cut_data[key]['data'])
            
    def check_for_logScale(self,data):
        """
        Check the data for log-scaling and remove the data points which are zero or negative
        """
        tdata=[]
        for row in range(data.shape[0]):
            if data[row,1]<=0:
                tdata.append([data[row,0],1e-30,1e-30])
        return np.array(tdata)
            
    def create_avg_data(self):
        """
        Creates the average data calculated from selected horizontal or vertical cuts
        """
        try:
            self.cutInfoTableWidget.itemChanged.disconnect(self.change_cut)
        except:
            pass
        sel_rows=list(set([item.row() for item in self.cutInfoTableWidget.selectedItems()]))
        if len(sel_rows)>0:
            keys=[str(self.cutInfoTableWidget.item(row,0).text()) for row in sel_rows]
            tmp_sum=np.zeros_like(self.cut_data[keys[0]]['data'][:,1])
            tmp_err=np.zeros_like(self.cut_data[keys[0]]['data'][:,1])
            for key in keys:
                tmp_sum=tmp_sum+self.cut_data[key]['data'][:,1]
                tmp_err=tmp_err+self.cut_data[key]['data'][:,2]**2        
            if np.all([key[:3]=='hor' for key in keys]):
                cur_key='hor_avg'+str(self.avg_count)            
            elif np.all([key[:3]=='ver' for key in keys]):
                cur_key='ver_avg'+str(self.avg_count)
            else:
                QMessageBox.warning(self,'Same cut type error','Please select cuts of same type to average',QMessageBox.Ok)
                return
            self.linked_keys[cur_key]=keys #keys to link the averaged key with the keys of the cuts
            cur_row=self.cutInfoTableWidget.rowCount()
            self.cutInfoTableWidget.insertRow(cur_row)
            self.cut_data[cur_key]={}
            self.cut_data[cur_key]['data']=np.vstack((self.cut_data[keys[0]]['data'][:,0],tmp_sum/len(keys),np.sqrt(tmp_err)/len(keys))).T
            self.cut_data[cur_key]['info']='#Averaged over cuts done at\n'
            for key in keys:
                self.cut_data[cur_key]['info']=self.cut_data[cur_key]['info']+'#pos=%.5f and width=%.6f\n'%(self.cut_pos[key],self.cut_width[key])
            self.cutInfoTableWidget.setItem(cur_row,0,QTableWidgetItem(cur_key))
            color=np.random.randint(256,size=4)
            color[3]=50
            self.colorButtons[cur_key]=pg.ColorButton(self.cutInfoTableWidget,color=color)
            self.cutInfoTableWidget.setCellWidget(cur_row,3,self.colorButtons[cur_key])
            self.lineColors[cur_key]=self.colorButtons[cur_key].color().getRgb()[:3]
            self.colorButtons[cur_key].sigColorChanging.connect(self.colorChanged)
            self.colorButtons[cur_key].sigColorChanging.connect(self.colorChanged)
            self.lineWidths[cur_key]=2
            self.cutInfoTableWidget.setItem(cur_row,4,QTableWidgetItem('%d'%(self.lineWidths[cur_key])))
            self.cutInfoTableWidget.setItem(cur_row,5,QTableWidgetItem(''))
            item=self.cutInfoTableWidget.item(cur_row,5)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.cutInfoTableWidget.item(cur_row,5).setCheckState(Qt.Checked)
            self.cutInfoTableWidget.setItem(cur_row,6,QTableWidgetItem(''))
            item=self.cutInfoTableWidget.item(cur_row,6)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.cutInfoTableWidget.item(cur_row,6).setCheckState(Qt.Unchecked)
            self.avg_count=self.avg_count+1
            self.cutInfoTableWidget.itemChanged.connect(self.change_cut)
            self.plot_cut_data(cur_key)
        else:
            QMessageBox.warning(self,'Selection Error', 'Please create some cuts first and select similar types of cuts from the table widget for averging.')
        
    def update_avg_data(self):
        """
        Updates replots the averaged data depending upon the changes made on individual cuts
        """
        for key in self.linked_keys.keys():
            tkeys=self.linked_keys[key]
            tmp_sum=np.zeros_like(self.cut_data[tkeys[0]]['data'][:,1])
            tmp_err=np.zeros_like(self.cut_data[tkeys[0]]['data'][:,1])
            self.cut_data[key]['info']='#Averaged over cuts done at\n'
            for tkey in tkeys:
                tmp_sum=tmp_sum+self.cut_data[tkey]['data'][:,1]
                tmp_err=tmp_err+self.cut_data[tkey]['data'][:,2]**2
                self.cut_data[key]['info']=self.cut_data[key]['info']+'#pos=%.5f and width=%.6f\n'%(self.cut_pos[tkey],self.cut_width[tkey])
            self.cut_data[key]['data']=np.vstack((self.cut_data[tkeys[0]]['data'][:,0],tmp_sum/len(tkeys),np.sqrt(tmp_err)/len(tkeys))).T
            self.plot_cut_data(key)
        
        
    def cutItemKey_from_cutObject(self,cutObject):
        """
        Provides the cut linear region item from cut linera region object
        """
        for key in self.cutItems.keys():
            if cutObject==self.cutItems[key]:
                return key
    
    def auto_save_cuts(self):
        """
        Depending upon the settings of the auto_save in the cutInfoTable widget the cuts will be saved automatically
        """
        for row in range(self.cutInfoTableWidget.rowCount()):
            key=str(self.cutInfoTableWidget.item(row,0).text())
            if self.cutInfoTableWidget.item(row,6).checkState():
                if self.caked_image_fname is not None:
                    fname=self.caked_image_fname+'_'+key+'_cut.txt'
                else:
                    fname='unnamed_'+key+'_cut.txt'
                fh=open(fname,'w')
                fh.write(self.cut_data[key]['info'])
                if self.caked_image_header is not None:
                    for tkey in self.caked_image_header.keys():
                        fh.write('#'+str(tkey)+'='+str(self.caked_image_header[tkey])+'\n')
                if key[:3]=='hor':
                    fh.write('#'+key[:3]+'_val('+self.unit[0]+') \t Intensity \t Intensity Err \n')
                else:
                    fh.write('#'+key[:3]+'_val('+self.unit[1]+') \t Intensity \t Intensity Err \n')
                for i in range(len(self.cut_data[key]['data'])):
                    fh.write('%.3e \t %.3e \t %.3e \n'%(self.cut_data[key]['data'][i,0],self.cut_data[key]['data'][i,1],self.cut_data[key]['data'][i,2]))                
                fh.close()
                
    def save_all_cuts(self):
        """
        Save all the 1D cuts extracted from the data
        """
        for row in range(self.cutInfoTableWidget.rowCount()):
            key=str(self.cutInfoTableWidget.item(row,0).text())
            if self.caked_image_fname is not None:
                fname=self.caked_image_fname+'_'+key+'_cut.txt'
            else:
                fname='unnamed_'+key+'_cut.txt'
            fh=open(fname,'w')
            fh.write(self.cut_data[key]['info'])
            if self.caked_image_header is not None:
                for tkey in self.caked_image_header.keys():
                    fh.write('#'+str(tkey)+'='+str(self.caked_image_header[tkey])+'\n')
            if key[:3]=='hor':
                fh.write('#'+key[:3]+'_val('+self.unit[0]+') \t Intensity \t Intensity Err \n')
            else:
                fh.write('#'+key[:3]+'_val('+self.unit[1]+') \t Intensity \t Intensity Err \n')
            for i in range(len(self.cut_data[key]['data'])):
                fh.write('%.3e \t %.3e \t %.3e \n'%(self.cut_data[key]['data'][i,0],self.cut_data[key]['data'][i,1],self.cut_data[key]['data'][i,2]))                
            fh.close()
        
                
        
        
        
if __name__=='__main__':
    # create application
    app = QApplication(sys.argv)
    app.setApplicationName('Image Cut Widget')

    # create widget
    w = ImageCutWidget()
    #w.setWindowState(Qt.WindowMaximized)
    #w.set_horCut_labels(xlabel='&Aring;',ylabel='&Aring;',fontsize=5)
    if len(sys.argv)>2:
        img=fb.open(sys.argv[1]).data
        w.addCakedImage(img,np.zeros_like(img))
        w.set_image_labels(xlabel='&Aring;',ylabel='&Aring;',title='My plot',fontsize=20)
    w.setGeometry(100,100,800,600)
    #w.showMaximized()
    w.show()

    # connection
    #QObject.lastWindowClosed.connect(app,SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))

    # execute application
    sys.exit(app.exec_())

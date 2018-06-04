from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QCheckBox, QLabel, QLineEdit, QApplication, QVBoxLayout, QMessageBox, QPushButton
import pyqtgraph as pg
import fabio as fb
import numpy as np
import sys
import copy
from ImageCutWidget import ImageCutWidget

class Image_Widget(QWidget):
    def __init__(self,img,min=None,max=None,xmin=None,xmax=None,ymin=None,ymax=None,logScale=False,transpose=False,parent=None):
        """
        The widget to show 2D data where
        
        :img: 2D array
        :min: Minumum z-value of the image to be shown. Default=None
        :max: Maximum z-value of the image to be shown. Default=None
        :xmin: Minimum value of horizontal scale. Default=None
        :xmax: Maximum value of horizontal scale. Default=None
        :ymin: Minimum value of horizontal scale. Default=None
        :ymax: Maximum value of vertical scale. Default=None
        :logScale: The z-value in log/Linear scale. Default=False
        :transpose: The array to be transposed first before plotting
        """
        QWidget.__init__(self,parent)
        #Parameters for Geographical colormap motivated by Fit2D#
        self.colorPos=np.array([0.0,0.17,0.26,0.34,0.51,0.68,0.85,1.0])
        black=[0,0,0,255]
        blue=[0,0,255,255]
        white=[255,255,255,255]
        green=[170,255,0,255]
        yellow=[255,255,0,255]
        orange=[255,170,0,255]
        magenta=[255,85,255,255]
        pg.graphicsItems.GradientEditorItem.Gradients['geography']={'mode':'rgb','ticks':[(0.0,black),(0.17,blue),(0.26,white),(0.34,green),(0.51,yellow),(0.68,orange),(0.85,magenta),(1.0,white)]}
        
        
        self.colorVal=np.array([black,blue,white,green,yellow,orange,magenta,white])
        if min is None:
            self.image_min=np.min(img)
        else:
            self.image_min=min
        if max is None:
            self.image_max=np.max(img)
        else:
            self.image_max=max
        self.logScale=logScale
        self.transpose=transpose
        if self.transpose:
            self.imageData=img.T
        else:
            self.imageData=img
        if xmin is None:
            self.xmin=0
        else:
            self.xmin=xmin
        if ymin is None:
            self.ymin=0
        else:
            self.ymin=ymin
        if xmax is None:
            self.xmax=self.imageData.shape[0]
        else:
            self.xmax=xmax
        if ymax is None:
            self.ymax=self.imageData.shape[1]
        else:
            self.ymax=ymax
            
        self.hor_Npt=self.imageData.shape[0]
        self.ver_Npt=self.imageData.shape[1]
        self.vbLayout=QVBoxLayout(self)
        self.imageLayout=pg.LayoutWidget()
        self.vbLayout.addWidget(self.imageLayout)
        
        self.autoMinMaxCheckBox=QCheckBox('Auto')
        self.autoMinMaxCheckBox.setTristate(False)
        self.autoMinMaxCheckBox.setChecked(True)#setCheckState(Qt.Checked)
        self.autoMinMaxCheckBox.stateChanged.connect(self.autoScale)
        minLabel=QLabel('Min')
        minLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.minLineEdit=QLineEdit(str(self.image_min))
        self.minLineEdit.returnPressed.connect(self.scaleChanged)
        maxLabel=QLabel('Max')
        maxLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.applyDefaultCMapPushButton=QPushButton('Apply default Colormap')
        self.applyDefaultCMapPushButton.clicked.connect(self.applyDefaultCMap)
        self.maxLineEdit=QLineEdit(str(self.image_max))
        self.maxLineEdit.returnPressed.connect(self.scaleChanged)
        self.imageLayout.addWidget(self.autoMinMaxCheckBox,row=0,col=0)
        self.imageLayout.addWidget(minLabel,row=0,col=1)
        self.imageLayout.addWidget(self.minLineEdit,row=0,col=2)
        self.imageLayout.addWidget(maxLabel,row=0,col=3)
        self.imageLayout.addWidget(self.maxLineEdit,row=0,col=4)
        self.imageLayout.addWidget(self.applyDefaultCMapPushButton,row=0,col=5)
        
        self.ylabel='Vertical'
        self.xlabel='Horizontal'
        self.unit=['pixels','pixels']
        self.imageView=pg.ImageView(view=pg.PlotItem(labels={'left':(self.ylabel,self.unit[1]),'bottom':(self.xlabel,self.unit[0])}))
        #self.imageView.ui.roiBtn.deleteLater()
        #self.imageView.ui.menuBtn.deleteLater()
        #self.imageView.view.removeItem(self.normRoi)
        self.create_default_colorMap(self.image_min,self.image_max)
        self.color_map=self.default_color_map
        self.imageLogLinear()
        self.imageLayout.addWidget(self.imageView,row=1,col=0,colspan=6)
        self.logScaleCheckBox=QCheckBox('Log scale')
        self.logScaleCheckBox.setTristate(False)
        self.logScaleCheckBox.stateChanged.connect(self.logScale_changed)
        self.imageLayout.addWidget(self.logScaleCheckBox,row=2,col=0)
        self.imageCrossHair=QLabel()
        self.imageCrossHair.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.imageLayout.addWidget(self.imageCrossHair,row=2,col=3)
        self.imageCutButton=QPushButton('Image Cuts')
        self.imageCutButton.clicked.connect(self.openImageCutWidget)
        self.imageLayout.addWidget(self.imageCutButton,row=2,col=5)
        self.imageHistogram=self.imageView.getHistogramWidget()
        self.imageHistogram.sigLevelsChanged.connect(self.scaleMoved)
        self.imageView.getView().vb.scene().sigMouseMoved.connect(self.image_mouseMoved)
        
    def openImageCutWidget(self):
        self.imageCutWidget=ImageCutWidget()
        self.imageCutWidget.addCakedImage(self.imageData,self.imageData*0.01,hor_val=np.linspace(self.xmin,self.xmax,self.imageData.shape[0]),ver_val=np.linspace(self.ymin,self.ymax,self.imageData.shape[1]),unit=self.unit)
        self.imageCutWidget.set_image_labels(xlabel=self.xlabel,ylabel=self.ylabel,title='')
        self.imageCutWidget.set_horCut_labels(xlabel=self.xlabel)
        self.imageCutWidget.set_verCut_labels(xlabel=self.ylabel)
        self.imageCutWidget.setWindowTitle('Cut Widget')
        self.imageCutWidget.showMaximized()
        
        
    def scaleMoved(self):
        """
        Changes the min/max LineEdit values corresponding to the changes in the Movable region  
        """
        self.autoMinMaxCheckBox.setCheckState(Qt.Unchecked)
        img_min,img_max=self.imageHistogram.getLevels()
        if self.logScale:
            self.image_min=10**img_min
            self.image_max=10**img_max
        else:
            self.image_min=img_min
            self.image_max=img_max
        self.minLineEdit.setText(str(self.image_min))
        self.maxLineEdit.setText(str(self.image_max))
        
        
    def scaleChanged(self):
        try:
            self.image_min,self.image_max=(float(self.minLineEdit.text()),float(self.maxLineEdit.text()))
            self.autoMinMaxCheckBox.setCheckState(Qt.Unchecked)
            self.imageLogLinear()
            if self.logScale:
                self.imageHistogram.setHistogramRange(np.log10(np.max([self.image_min,1e-12])),np.log10(self.image_max))
            else:
                self.imageHistogram.setHistogramRange(self.image_min,self.image_max)
            #self.autoMinMaxCheckBox.setCheckState(Qt.Unchecked)
            #self.imageHistogram.setLevels(self.image_min,self.image_max)            
        except:
            QMessageBox.warning(self,'Value Error','Please input numbers only.\n',QMessageBox.Ok)
            self.minLineEdit.setText(str(self.image_min))
            self.maxLineEdit.setText(str(self.image_max))
            
        
    def autoScale(self):
        """
        Autoscale the Z value of the plate to min max of the array
        """
        if self.autoMinMaxCheckBox.isChecked():
            self.imageView.autoLevels()
            #self.imageHistogram.autoHistogramRange()
            self.image_min,self.image_max=self.imageHistogram.getLevels()
            if self.logScale:
                self.image_min=10**self.image_min
                self.image_max=10**self.image_max
            self.minLineEdit.setText(str(self.image_min))
            self.maxLineEdit.setText(str(self.image_max))
                
    def setImage(self,img,min=None,max=None,xmin=None,xmax=None,ymin=None,ymax=None,transpose=False,xlabel='Horizontal',ylabel='Vertical',unit=['pixels','pixels']):

        if transpose:
            self.imageData=img.T
        else:
            self.imageData=img
        if xmin is None:
            self.xmin=0
        else:
            self.xmin=xmin
        if ymin is None:
            self.ymin=0
        else:
            self.ymin=ymin
        if xmax is None:
            self.xmax=self.imageData.shape[0]
        else:
            self.xmax=xmax
        if ymax is None:
            self.ymax=self.imageData.shape[1]
        else:
            self.ymax=ymax
        if self.logScaleCheckBox.isChecked():
            self.logScale=True
        self.xlabel=xlabel
        self.ylabel=ylabel
        self.unit=unit
        self.imageLogLinear()
        if self.autoMinMaxCheckBox.isChecked():
            self.autoScale()
        self.hor_Npt=self.imageData.shape[0]
        self.ver_Npt=self.imageData.shape[1]
        self.imageView.getView().vb.scene().sigMouseMoved.connect(self.image_mouseMoved)
        
        
    def create_default_colorMap(self,imin,imax,scale='linear'):
        """
        Creates a colorMap with min and max values with linear or log scale
        """        
        if scale=='linear':
            colorPos=self.colorPos
        else:
            colorPos=10**np.linspace(np.log10(imin),np.log10(imax),7)
            colorPos=np.insert(colorPos,2,10**(np.log10(imin)+1.0*(np.log10(imax)-np.log10i(imin))/4.0))
        self.default_color_map=pg.ColorMap(colorPos,self.colorVal)
        
        
    def update_color_map(self):
        """
        Updates the colormap
        """
        self.imageView.ui.histogram.gradient.setColorMap(self.color_map)
         
    def get_color_map(self):
        """
        Changes the color map
        """
        self.color_map=self.imageView.ui.histogram.gradient.colorMap()
        
    def applyDefaultCMap(self):
        """
        Apply default colormap
        """
        self.color_map=copy.copy(self.default_color_map)
        self.update_color_map()
        
        
        
    def logScale_changed(self):
        if self.logScaleCheckBox.isChecked():
            self.logScale=True
        else:
            self.logScale=False
        self.imageLogLinear()
        self.imageHistogram.autoHistogramRange()
        

    def image_mouseMoved(self,pos):
        """
        Shows the mouse position of 2D Image on its crosshair label
        """
        pointer=self.imageView.getView().vb.mapSceneToView(pos)
        x,y=pointer.x(),pointer.y()
        #if int(self.xmax-self.xmin)<self.imageData.shape[1] or int(self.ymax-self.ymin)<self.imageData.shape[0]:
        if (x>self.xmin) and (x<self.xmax) and (y>self.ymin) and (y<self.ymax):
            self.imageCrossHair.setText('X=%0.4f, Y=%0.4f, I=%.5e'%(x,y,self.imageData[int((x-self.xmin)*self.hor_Npt/(self.xmax-self.xmin)),int((y-self.ymin)*self.ver_Npt/(self.ymax-self.ymin))]))
        else:
            self.imageCrossHair.setText('X=%0.4f, Y=%0.4f, I=%.5e'%(x,y,0)) 
#        else:
#            if (x>self.xmin) and (x<self.xmax) and (y>self.ymin) and (y<self.ymax):
#                self.imageCrossHair.setText('X=%04d, Y=%04d, I=%.5e'%(x,y,self.imageData[int((x-self.xmin)*self.hor_Npt/(self.xmax-self.xmin)),int((y-self.ymin)*self.ver_Npt/(self.ymax-self.ymin))]))
#            else:
#                self.imageCrossHair.setText('X=%04d, Y=%04d, I=%.5e'%(x,y,0))
            
        
    def imageLogLinear(self):
        """
        Change the z-scale of the image from linear to log and vice-versa depending on the state of the logScaleCheckBox
        """
        pos=[self.xmin,self.ymin]
        scale=[(self.xmax-self.xmin)/self.imageData.shape[0],(self.ymax-self.ymin)/self.imageData.shape[1]]
        if self.logScale:
            if self.image_min<=0:#np.any(self.imageData<=0):
                self.image_min=0.1*np.mean(np.abs(self.imageData))
                self.minLineEdit.setText(str(self.image_min))
            tmpData=np.where(self.imageData<=0,1,self.imageData)
            self.imageView.setImage(np.log10(tmpData),levels=(np.log10(self.image_min),np.log10(self.image_max)),pos=pos,scale=scale,autoRange=True)
        else:
            self.imageView.setImage(self.imageData,levels=(self.image_min,self.image_max),pos=pos,scale=scale,autoRange=True)
        #self.get_color_map()
        self.update_color_map()
        self.imageView.ui.histogram.autoHistogramRange()
        self.imageView.getView().setLabels(bottom=(self.xlabel,self.unit[0]),left=(self.ylabel,self.unit[1]))
        #self.imageView.view.setRange(xRange=(self.xmin,self.xmax),yRange=(self.ymin,self.ymax))
        #pg.QtGui.QApplication.processEvents() 
        
if __name__=='__main__':
    # create application
    app = QApplication(sys.argv)
    app.setApplicationName('Mask Widget')
    # create widget
    try:
        img=fb.open(sys.argv[1]).data
    except:
        img=np.random.rand(1000,1000)
    w = Image_Widget(img,transpose=True)
    w.setMinimumSize(1000,1000)
    #w.setWindowState(Qt.WindowMaximized)
    w.setWindowTitle('XRTools-Image Viewer')
    w.show()

    # execute application
    sys.exit(app.exec_())
        

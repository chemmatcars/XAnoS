import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QLineEdit, QColorDialog, QCheckBox, QApplication
from PyQt5.QtCore import Qt
import numpy as np
import sys
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget
import copy


class PlotWidget(QWidget):
    """
    This class inherited from pyqtgraphs Plotwidget and MatplotlibWidget and adds additional compononets like:
        1) Cross-hair to view X, Y coordinates
        2) Changing plot-styles interactively
    """
    def __init__(self,parent=None,matplotlib=False):
        QWidget.__init__(self,parent)
        self.matplotlib=matplotlib
        self.mplPlotData={}
        self.mplErrorData={}
        self.xLabelFontSize=10
        self.yLabelFontSize=10
        self.titleFontSize=12
        self.xLabel='x'
        self.yLabel='y'
        self.title='Plot'            
        self.createPlotWidget()
        self.data={}
        self.dataErrPos={}
        self.dataErrNeg={}
        self.dataErr={}
        self.err={}
        self.data_num=0
        self.yerr={}
        self.fit={}
        
       
    def createPlotWidget(self):
        """
        Creates the plotWidget
        """
        self.vbLayout=QVBoxLayout(self)
        self.plotLayout=pg.LayoutWidget()
        self.vbLayout.addWidget(self.plotLayout)
        
        row=0
        col=0
        lineWidthLabel=QLabel('Line width')
        self.lineWidthLineEdit=QLineEdit('2')
        self.lineWidthLineEdit.returnPressed.connect(self.updatePlot)
        pointSizeLabel=QLabel('Point size')
        self.pointSizeLineEdit=QLineEdit('5')
        self.pointSizeLineEdit.returnPressed.connect(self.updatePlot)
        self.errorbarCheckBox=QCheckBox('Errorbar')
        self.errorbarCheckBox.stateChanged.connect(self.errorbarChanged)
        self.plotLayout.addWidget(lineWidthLabel,row=row,col=col)
        col+=1
        self.plotLayout.addWidget(self.lineWidthLineEdit,row=row,col=col)
        col+=1
        self.plotLayout.addWidget(pointSizeLabel,row=row,col=col)
        col+=1
        self.plotLayout.addWidget(self.pointSizeLineEdit,row=row,col=col)
        col+=1
        self.plotLayout.addWidget(self.errorbarCheckBox,row=row,col=col)
        col=0
        row+=1
        if self.matplotlib:
            self.plotWidget=MatplotlibWidget()
            self.subplot=self.plotWidget.getFigure().add_subplot(111)
            self.plotWidget.fig.set_tight_layout(True)
            self.plotWidget.draw()
        else:
            self.plotWidget=pg.PlotWidget(background='k')
            self.plotWidget.getPlotItem().vb.scene().sigMouseMoved.connect(self.mouseMoved)
            self.legendItem=pg.LegendItem(offset=(0.0,1.0))
            self.legendItem.setParentItem(self.plotWidget.getPlotItem())
            
        self.plotLayout.addWidget(self.plotWidget,row=row,col=col,colspan=5)
        row+=1
        col=0 
        self.crosshairLabel=QLabel(u'X={: .5f} , y={: .5f}'.format(0.0,0.0))                                 
        self.xLogCheckBox=QCheckBox('LogX')
        self.xLogCheckBox.setTristate(False)
        self.xLogCheckBox.stateChanged.connect(self.updatePlot)
        self.yLogCheckBox=QCheckBox('LogY')
        self.yLogCheckBox.setTristate(False)
        self.yLogCheckBox.stateChanged.connect(self.updatePlot)
        if not self.matplotlib:
            self.plotLayout.addWidget(self.crosshairLabel,row=row,col=col,colspan=3)
        self.plotLayout.addWidget(self.xLogCheckBox,row=row,col=3)
        self.plotLayout.addWidget(self.yLogCheckBox,row=row,col=4)
        
        
        
        
        
    def mouseMoved(self,pos):
        try:
            pointer=self.plotWidget.getPlotItem().vb.mapSceneToView(pos)
            x,y=pointer.x(),pointer.y()
            if self.plotWidget.getPlotItem().ctrl.logXCheck.isChecked():
                x=10**x
            if self.plotWidget.getPlotItem().ctrl.logYCheck.isChecked():
                y=10**y
            self.crosshairLabel.setText(u'X={: .5g} , Y={: .5g}'.format(x,y))
            # if x>1e-3 and y>1e-3:
            #     self.crosshairLabel.setText(u'X={: .5f} , Y={: .5f}'.format(x,y))
            # if x<1e-3 and y>1e-3:
            #     self.crosshairLabel.setText(u'X={: .3e} , Y={: .5f}'.format(x,y))
            # if x>1e-3 and y<1e-3:
            #     self.crosshairLabel.setText(u'X={: .5f} , Y={: .3e}'.format(x,y))
            # if x<1e-3 and y<1e-3:
            #     self.crosshairLabel.setText(u'X={: .3e} , Y={: .3e}'.format(x,y))
        except:
            pass
                
        #self.crosshairLabel.setText(u'X=%+0.5f, Y=%+0.5e'%(x,y))
        
        
    def add_data(self,x,y,yerr=None,name=None,fit=False):
        """
        Adds data into the plot where:
        x=Array of x-values
        y=Array of y-values
        yerr=Array of yerr-values. If None yerr will be set to sqrt(y)
        name=any string to be used for the key to put the data
        fit= True if the data corresponds to a fit
        """
        if not (isinstance(yerr,list) or isinstance(yerr,np.ndarray)):
            yerr=np.ones_like(y)
        if len(x)==len(y) and len(y)==len(yerr):
            if name is None:
                dname=str(self.data_num)
            else:
                dname=name
            if np.all(yerr==1):
                self.yerr[dname]=False
            else:
                self.yerr[dname]=True
            self.fit[dname]=fit
            if dname in self.data.keys():
                color=self.data[dname].opts['symbolPen'].color()
                pen=pg.mkPen(color=color,width=float(self.lineWidthLineEdit.text()))
                symbol='o'
                if self.fit[dname]:
                    symbol=None
                self.data[dname].setData(x,y,pen=pen,symbol=symbol,symbolSize=float(self.pointSizeLineEdit.text()),symbolPen=pg.mkPen(color=color),symbolBrush=pg.mkBrush(color=color))
                #self.data[dname].setPen(pg.mkPen(color=pg.intColor(np.random.choice(range(0,210),1)[0]),width=int(self.lineWidthLineEdit.text())))
                #if self.errorbarCheckBox.isChecked():
                # self.dataErrPos[dname].setData(x,np.where(y+yerr/2.0>0,y+yerr/2.0,y))
                # self.dataErrNeg[dname].setData(x,np.where(y-yerr/2.0>0,y-yerr/2.0,y))
                self.err[dname]= yerr/2.0
                self.dataErr[dname].setData(x=x, y=y, top=self.err[dname], bottom=self.err[dname],beam=min(np.abs(x))*0.01*float(self.pointSizeLineEdit.text()),pen='w')
            #self.dataErr[dname].setCurves(self.dataErrPos[dname],self.dataErrNeg[dname])
            else: 
                color=pg.intColor(np.random.choice(range(0,210),1)[0])
                #color=self.data[dname].opts['pen'].color()
                pen=pg.mkPen(color=color,width=float(self.lineWidthLineEdit.text()))
                symbol='o'
                if self.fit[dname]:
                    symbol=None
                self.data[dname]=pg.PlotDataItem(x,y,pen=pen,symbol=symbol,symbolSize=float(self.pointSizeLineEdit.text()),symbolPen=pg.mkPen(color=color),symbolBrush=pg.mkBrush(color=color))
                self.dataErr[dname] = pg.ErrorBarItem()
                self.err[dname]=yerr/2.0
                self.dataErr[dname].setData(x=x,y=y,top=self.err[dname],bottom=self.err[dname], beam=min(np.abs(x))*0.01*float(self.pointSizeLineEdit.text()),pen='w')
                self.data[dname].curve.setClickable(True,width=10)
                self.data[dname].sigClicked.connect(self.colorChanged)
                #if self.errorbarCheckBox.isChecked():
                # self.dataErrPos[dname]=pg.PlotDataItem(x,np.where(y+yerr/2.0>0,y+yerr/2.0,y))
                # self.dataErrNeg[dname]=pg.PlotDataItem(x,np.where(y-yerr/2.0>0,y-yerr/2.0,y))
                #self.dataErr[dname]=pg.FillBetweenItem(curve1=self.dataErrPos[dname],curve2=self.dataErrNeg[dname],brush=pg.mkBrush(color=pg.hsvColor(1.0,sat=0.0,alpha=0.2)))
                self.data_num+=1
                #if len(x)>1:
                self.Plot([dname])
            return True
        else:
            QMessageBox.warning(self,'Data error','The dimensions of x, y or yerr are not matching',QMessageBox.Ok)
            return False
            
    def colorChanged(self,item):
        """
        Color of the item changed
        """
        color=item.opts['symbolPen'].color()
        newcolor=QColorDialog.getColor(initial=color)
        if newcolor.isValid():
            #if self.lineWidthLineEdit.text()!='0':
            item.setPen(pg.mkPen(color=newcolor,width=int(self.lineWidthLineEdit.text())))
            if self.pointSizeLineEdit.text()!='0':
                item.setSymbolBrush(pg.mkBrush(color=newcolor))
                item.setSymbolPen(pg.mkPen(color=newcolor))
    
    def errorbarChanged(self):
        """
        Updates the plot checking the Errorbar is checked or not
        """
        self.Plot(self.selDataNames)
            
        
    def Plot(self,datanames):
        """
        Plots all the data in the memory with errorbars where:
            datanames is the list of datanames
        """
        self.selDataNames=datanames
        if self.matplotlib: #Plotting with matplotlib
            self.xLabel=self.subplot.get_xlabel()
            self.yLabel=self.subplot.get_ylabel()
            self.title=self.subplot.get_title()
            #self.subplot.axes.cla()
            for dname in self.selDataNames:                
                if self.errorbarCheckBox.checkState()==Qt.Checked:
                    try:
                        self.mplPlotData[dname].set_xdata(self.data[dname].xData)
                        self.mplPlotData[dname].set_ydata(self.data[dname].yData)
                        self.mplPlotData[dname].set_markersize(int(self.pointSizeLineEdit.text()))
                        self.mplPlotData[dname].set_linewidth(int(self.lineWidthLineEdit.text()))
                        
                        self.mplErrorData[dname].set_segments(np.array([[x,yt],[x,yb]]) for x,yt,yb in zip(self.data[dname].xData,self.dataErrPos[dname].yData,self.dataErrNeg[dname].yData))
                        self.mplErrorData[dname].set_linewidth(2)
                    except:
                        try:
                            self.mplPlotData[dname].remove()
                            del self.mplPlotData[dname]
                        except:
                            pass
                        ln,err,bar =self.subplot.errorbar(self.data[dname].xData,self.data[dname].yData,xerr=None,yerr=self.dataErr[dname].opts['top']*2,fmt='.-',markersize=int(self.pointSizeLineEdit.text()),linewidth=int(self.lineWidthLineEdit.text()),label=dname)
                        self.mplPlotData[dname]=ln
                        self.mplErrorData[dname],=bar
                else:
                    try:
                        self.mplPlotData[dname].set_xdata(self.data[dname].xData)
                        self.mplPlotData[dname].set_ydata(self.data[dname].yData)
                        self.mplPlotData[dname].set_markersize(int(self.pointSizeLineEdit.text()))
                        self.mplPlotData[dname].set_linewidth(int(self.lineWidthLineEdit.text()))
                    except:
                        self.mplPlotData[dname], =self.subplot.plot(self.data[dname].xData,self.data[dname].yData,'.-',markersize=int(self.pointSizeLineEdit.text()),linewidth=int(self.lineWidthLineEdit.text()),label=dname)
            if self.xLogCheckBox.checkState()==Qt.Checked:
                self.subplot.set_xscale('log')
            else:
                self.subplot.set_xscale('linear')
            if self.yLogCheckBox.checkState()==Qt.Checked:
                self.subplot.set_yscale('log')
            else:
                self.subplot.set_yscale('linear')
            self.subplot.set_xlabel(self.xLabel,fontsize=self.yLabelFontSize)
            self.subplot.set_ylabel(self.yLabel,fontsize=self.yLabelFontSize)
            self.subplot.set_title(self.title,fontsize=self.titleFontSize)
#            try:
#                self.leg.draggable()
#            except:
            self.leg=self.subplot.legend()
            self.leg.draggable()
            self.plotWidget.fig.set_tight_layout(True)
            self.plotWidget.draw()
                
        else:
            self.plotWidget.plotItem.setLogMode(x=False,y=False) #This step is necessary for checking the zero values
            self.plotWidget.clear()
            for names in self.data.keys():
                self.legendItem.removeItem(names)
            xlog_res=True
            ylog_res=True
            for dname in self.selDataNames:
                if np.all(self.data[dname].yData==0) and self.yLogCheckBox.checkState()==Qt.Checked:
                    QMessageBox.warning(self,'Zero error','All the yData are zeros. So Cannot plot Logarithm of yData for %s'%dname,QMessageBox.Ok)
                    ylog_res=ylog_res and False
                    if not ylog_res:
                        self.yLogCheckBox.stateChanged.disconnect(self.updatePlot)
                        self.yLogCheckBox.setCheckState(Qt.Unchecked)
                        self.yLogCheckBox.stateChanged.connect(self.updatePlot)
                if np.all(self.data[dname].xData==0) and self.xLogCheckBox.checkState()==Qt.Checked:
                    QMessageBox.warning(self,'Zero error','All the xData are zeros. So Cannot plot Logarithm of xData for %s'%dname,QMessageBox.Ok)
                    xlog_res=xlog_res and False
                    if not xlog_res:
                        self.xLogCheckBox.stateChanged.disconnect(self.updatePlot)
                        self.xLogCheckBox.setCheckState(Qt.Unchecked)
                        self.xLogCheckBox.stateChanged.connect(self.updatePlot)
                self.plotWidget.addItem(self.data[dname])
                if self.errorbarCheckBox.isChecked() and self.yerr[dname]:
                    x=self.data[dname].xData
                    y=self.data[dname].yData
                    top=copy.copy(self.err[dname])
                    bottom= copy.copy(self.err[dname])
                    if self.xLogCheckBox.checkState() == Qt.Checked:
                         x=np.log10(x)
                    if self.yLogCheckBox.checkState() == Qt.Checked:
                        top=np.log10(1+top/y)
                        bottom=np.log10(1+bottom/y)
                        y = np.log10(y)
                    self.dataErr[dname].setData(x=x,y=y,top=top,bottom=bottom,beam=min(np.abs(x))*0.01*float(self.pointSizeLineEdit.text()),pen='w')
                    self.plotWidget.addItem(self.dataErr[dname])
                    # self.plotWidget.addItem(self.dataErrPos[dname])
                    # self.plotWidget.addItem(self.dataErrNeg[dname])
                    #self.plotWidget.addItem(self.dataErr[dname])
                    #self.dataErr[dname].setCurves(self.dataErrPos[dname],self.dataErrNeg[dname])
                self.legendItem.addItem(self.data[dname],dname)
            if self.xLogCheckBox.checkState()==Qt.Checked:
                self.plotWidget.plotItem.setLogMode(x=True)
            else:
                self.plotWidget.plotItem.setLogMode(x=False)
            if self.yLogCheckBox.checkState()==Qt.Checked:
                self.plotWidget.plotItem.setLogMode(y=True)
            else:
                self.plotWidget.plotItem.setLogMode(y=False)

                
    def remove_data(self,datanames):
        for dname in datanames:
            if self.matplotlib:
                self.mplPlotData[dname].remove()
                del self.mplPlotData[dname]
                if self.errorbarCheckBox.isChecked() and self.yerr[dname]:
                    self.mplErrorData[dname].remove()
                    del self.mplErrorData[dname]
            else:
                self.plotWidget.removeItem(self.data[dname])
                self.legendItem.removeItem(dname)
                if self.errorbarCheckBox.isChecked() and self.yerr[dname]:
                    self.plotWidget.removeItem(self.dataErrPos[dname])
                    self.plotWidget.removeItem(self.dataErrNeg[dname])
            del self.data[dname]
            del self.dataErrPos[dname]
            del self.dataErrNeg[dname]
            
            
    def updatePlot(self):
        # try:
        for dname in self.selDataNames:
            if self.lineWidthLineEdit.text()=='0' and not self.fit[dname]:
                self.data[dname].opts['pen']=None
                self.data[dname].updateItems()
            else:
                #try:
                self.data[dname].setPen(self.data[dname].opts['symbolPen']) #setting the same color as the symbol
                color=self.data[dname].opts['pen'].color()
                self.data[dname].setPen(pg.mkPen(color=color,width=float(self.lineWidthLineEdit.text())))
                #except:
                #    self.data[dname].setPen(pg.mkPen(color='b',width=float(self.lineWidthLineEdit.text())))
            self.data[dname].opts['symbol']='o'
            if self.fit[dname]:
                self.data[dname].setSymbolSize(0)
            else:
                self.data[dname].setSymbolSize(float(self.pointSizeLineEdit.text()))
        self.Plot(self.selDataNames)
        # except:
        #     QMessageBox.warning(self,'Data Error','No data to plot',QMessageBox.Ok)
            
    def setXLabel(self,label,fontsize=4):
        """
        sets the X-label of the plot
        """
        self.xLabel=label
        self.xLabelFontSize=fontsize
        if self.matplotlib:
            self.subplot.set_xlabel(label,fontsize=fontsize)
            self.plotWidget.draw()
        else:
            self.plotWidget.getPlotItem().setLabel('bottom','<font size='+str(fontsize)+'>'+label+'</font>')
            
    def setYLabel(self,label,fontsize=4):
        """
        sets the y-label of the plot
        """
        self.yLabel=label
        self.yLabelFontSize=fontsize
        if self.matplotlib:
            self.subplot.set_ylabel(label,fontsize=fontsize)
            self.plotWidget.draw()
        else:
            self.plotWidget.getPlotItem().setLabel('left','<font size='+str(fontsize)+'>'+label+'</font>')        
            
            
    def setTitle(self,title,fontsize=6):
        """
        Sets the y-label of the plot
        """
        self.title=title
        self.titleFontSize=fontsize
        if self.matplotlib:
            self.subplot.set_title(title,fontsize=fontsize)
            self.plotWidget.draw()
        else:
            self.plotWidget.getPlotItem().setTitle(title='<font size='+str(fontsize)+'>'+title+'</font>')

    def addROI(self,values=(0,1),orientation='horizontal',movable=True):
        if orientation=='vertical':
            self.roi=pg.LinearRegionItem(values=values,orientation=pg.LinearRegionItem.Vertical,movable=movable)
        else:
            self.roi = pg.LinearRegionItem(values=values, orientation=pg.LinearRegionItem.Horizontal,movable=movable)
        self.plotWidget.addItem(self.roi)

 
    
if __name__=='__main__':
    app=QApplication(sys.argv)
    w=PlotWidget(matplotlib=False)
    x=np.arange(0,np.pi,0.01)
    y=np.sin(x)
    yerr=0.1*y
    w.add_data(x,y,yerr=yerr,name='sin')
    w.setXLabel('x',fontsize=15)
    w.setYLabel('y',fontsize=15)
    w.setTitle('My Plot',fontsize=15)
    w.setWindowTitle('Plot Widget')
    w.setGeometry(100,100,1000,800)
    
    w.show()
    sys.exit(app.exec_())
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QWidget,QDialog,QMessageBox,QTableWidgetItem,QFileDialog,QComboBox
from PyQt5.QtCore import QFileSystemWatcher
from PyQt5.QtTest import QTest
import sys
import pandas as pd
import os
import numpy as np
import time
from PlotWidget import PlotWidget

class Data_Widget(QDialog):
    def __init__(self,fname=None,data=None,comment='#',skiprows=0,delimiter=' ',autoupdate=False,parent=None,matplotlib=False):
        QWidget.__init__(self,parent=parent)
        loadUi('UI_Forms/Data_Widget.ui',self)
        self.plotWidget=PlotWidget(parent=self,matplotlib=matplotlib)
        self.plotTab=self.tabWidget.addTab(self.plotWidget,'Plots')
        self.tabWidget.setCurrentIndex(0)
        #self.plotTab.vertialLayout_7.addWidget(self.plotWidget)
        self.init_signals()
        self.show()
        self.fileWatcher=QFileSystemWatcher()
        self.fileWatcher.fileChanged.connect(self.fileUpdated)
        self.cwd=None
        self.plotNum=0
        if data is not None:
            self.data=data
        elif fname is not None:
            self.data=self.readData(fname,comment=comment,skiprows=skiprows,delimiter=delimiter)
        if self.data is not None:
            self.setMeta2Table()
            self.setData2Table()
            self.addPlots()
            
        
            
    def init_signals(self):
        self.closePushButton.clicked.connect(self.closeWidget)
        self.openDataFilePushButton.clicked.connect(self.openFile)
        self.autoUpdateCheckBox.stateChanged.connect(self.autoUpdate_ON_OFF)
        self.saveDataPushButton.clicked.connect(self.saveData)
        self.addPlotPushButton.clicked.connect(self.addPlots)
        
     
     
                   
    def closeWidget(self):
        self.close()
            

            
    def setMeta2Table(self):
        """
        Populates the metaDataTable widget with metadata avaiable from the data
        """
        self.metaDataTableWidget.clear()
        self.metaDataTableWidget.setColumnCount(2)
        self.metaDataTableWidget.setRowCount(len(self.data['meta'].keys()))
        for num,key in enumerate(self.data['meta'].keys()):
            self.metaDataTableWidget.setItem(num,0,QTableWidgetItem(key))
            self.metaDataTableWidget.setItem(num,1,QTableWidgetItem(str(self.data['meta'][key])))
        self.metaDataTableWidget.setHorizontalHeaderLabels(['Parameter','Value'])
        
            
    def getMetaFromTable(self):
        self.data['meta']={}
        for i in range(self.metaDataTableWidget.rowCount()):
            self.data['meta'][self.metaDataTableWidget.item(i,0).text()]=eval(self.metaDataTableWidget.item(i,1).text())
            
    def setData2Table(self):
        """
        Populates the dataTableWidget with data available from data
        """
        self.dataTableWidget.clear()
        self.dataTableWidget.setColumnCount(len(self.data['data'].columns))
        self.dataTableWidget.setRowCount(len(self.data['data'].index))
        for j,colname in enumerate(self.data['data'].columns):
            for i in range(len(self.data['data'].index)):
                self.dataTableWidget.setItem(i,j,QTableWidgetItem(str(self.data['data'][colname][i])))
        self.dataTableWidget.setHorizontalHeaderLabels(self.data['data'].columns.values.tolist())
            
        
    def getDataFromTable(self):
        self.data['data']=pd.DataFrame()
        for col in range(self.dataTableWidget.columnCount()):
            label=self.dataTableWidget.horizontalHeaderItem(col).text()
            self.data['data'][label]=np.array([float(self.dataTableWidget.item(i,col).text()) for i in range(self.dataTableWidget.rowCount())])
        
            
            
            
    def readData(self,fname,skiprows=0,comment='#',delimiter=' '):
        """
        Read data from a file and put it in dictionary structure with keys 'meta' and 'data' and the data would look like the following
        data={'meta':meta_dictionary,'data'=pandas_dataframe}
        """
        if os.path.exists(os.path.abspath(fname)):
            self.data={}
            self.fname=fname
            self.dataFileLineEdit.setText(self.fname)
            self.cwd=os.path.dirname(self.fname)
            fh=open(os.path.abspath(self.fname),'r')
            lines=fh.readlines()
            fh.close()
            self.data['meta']={}
            for line in lines[skiprows:]:
                if line[0]==comment:
                    try:
                        key,value=line[1:].strip().split('=')
                        self.data['meta'][key]=eval(value)
                    except:
                        pass
                else:
                    break
            if 'col_names' in self.data['meta'].keys():
                self.data['data']=pd.read_csv(self.fname,comment=comment,names=self.data['meta']['col_names'],header=None,delimiter=delimiter)
            else:
                self.data['data']=pd.read_csv(self.fname,comment=comment,header=None,delimiter=delimiter)
                self.data['data'].columns=['Col_%d'%i for i in self.data['data'].columns.values.tolist()]
                self.data['meta']['col_names']=self.data['data'].columns.values.tolist()
            self.autoUpdate_ON_OFF()
            return self.data                
        else:
            QMessageBox.warning(self,'File Error','The file doesnot exists!')
            return None
        
    def fileUpdated(self,fname):
        QTest.qWait(1000)
        self.readData(fname=fname)
        if self.data is not None:
            self.setMeta2Table()
            self.setData2Table()
    
    def autoUpdate_ON_OFF(self):
        files=self.fileWatcher.files()
        if len(files)!=0:
            self.fileWatcher.removePaths(files)
        if self.autoUpdateCheckBox.isChecked():
            self.fileWatcher.addPath(self.fname)
            
    def saveData(self):
        """
        Save data to a file
        """
        fname=QFileDialog.getSaveFileName(self,'Save file as',self.cwd,filter='*.*')[0]
        ext=os.path.splitext(fname)[1]
        if ext=='':
            ext='.txt'
            fname=fname+ext
        header='File saved on %s\n'%time.asctime()
        for key in self.data['meta'].keys():
            header=header+'%s=%s\n'%(key,str(self.data['meta'][key]))
        if 'col_names' not in self.data['meta'].keys():
            header=header+'col_names=%s\n'%str(self.data['data'].columns.tolist())
        np.savetxt(fname,self.data['data'].as_matrix(),header=header,comments='#')
        
            
        
        
    def openFile(self):
        """
        Opens a openFileDialog to open a data file
        """
        if self.cwd is not None:
            fname=QFileDialog.getOpenFileName(self,'Select a data file to open',directory=self.cwd,filter='*.*')[0]
        else:
            fname=QFileDialog.getOpenFileName(self,'Select a data file to open',directory='',filter='*.*')[0]
        self.data=self.readData(fname=fname)
        if self.data is not None:
            self.setMeta2Table()
            self.setData2Table()
            
            
    def addPlots(self):
        #self.plotSetupTableWidget.clear()
        columns=self.data['data'].columns.tolist()
        if len(columns)>=2:
            self.plotSetupTableWidget.insertRow(self.plotSetupTableWidget.rowCount())
            row=self.plotSetupTableWidget.rowCount()-1
            self.plotSetupTableWidget.setItem(row,0,QTableWidgetItem('Data_%d'%self.plotNum))
            for i in range(1,3):
                self.plotSetupTableWidget.setCellWidget(row,i,QComboBox())
                self.plotSetupTableWidget.cellWidget(row,i).addItems(columns)
                self.plotSetupTableWidget.cellWidget(row,i).setCurrentIndex(i-1)
            self.plotSetupTableWidget.setCellWidget(row,3,QComboBox())
            self.plotSetupTableWidget.cellWidget(row,3).addItems(['None']+columns)
            xcol=self.plotSetupTableWidget.cellWidget(row,1).currentText()
            ycol=self.plotSetupTableWidget.cellWidget(row,2).currentText()
            yerrcol=self.plotSetupTableWidget.cellWidget(row,3).currentText()
            name=self.plotSetupTableWidget.item(row,0).text()
            if yerrcol!='None':
                self.plotWidget.add_data(self.data['data'][xcol].values,self.data['data'][ycol].values,yerr=self.data['data'][yerrcol].values,name=name)
            else:
                self.plotWidget.add_data(self.data['data'][xcol].values,self.data['data'][ycol].values,name=name)
            self.plotNum+=1
            return True
            self.updatePlot()
        else:
            return False
        
        
    def updatePlot(self):
        names=[self.plotSetupTableWidget.item(i,0).text() for i in range(self.plotSetupTableWidget.rowCount())]
        self.plotWidget.Plot(names)
        
        
if __name__=='__main__':
    app=QApplication(sys.argv)
    fname=r'C:\Users\Mrinal Bera\Desktop\India_collab\Fe50A_SW\SAXS\extracted_pyFAI\Fe50A_SW_SAXS_0000.txt'
    #data={'meta':{'a':1,'b':2},'data':pd.DataFrame({'x':np.arange(1000),'y':np.arange(1000),'y_err':np.arange(1000)})}
    w=Data_Widget(fname=fname,matplotlib=True)
    sys.exit(app.exec_())
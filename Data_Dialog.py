from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QDialog,QMessageBox,QTableWidgetItem,QFileDialog,QComboBox
from PyQt5.QtCore import QFileSystemWatcher, Qt
from PyQt5.QtTest import QTest
import sys
import pandas as pd
import os
import numpy as np
import time
from PlotWidget import PlotWidget
import copy

class QCustomTableWidgetItem (QTableWidgetItem):
    def __init__ (self, value):
        super(QCustomTableWidgetItem, self).__init__('%s' % value)

    def __lt__ (self, other):
        if (isinstance(other, QCustomTableWidgetItem)):
            selfDataValue  = float(self.data(Qt.EditRole))
            otherDataValue = float(other.data(Qt.EditRole))
            return selfDataValue < otherDataValue
        else:
            return QTableWidgetItem.__lt__(self, other)


class MetaData_Dialog(QDialog):
    def __init__(self,name='para',value=0.0, parent=None):
        QDialog.__init__(self,parent)
        loadUi('UI_Forms/MetaData_Dialog.ui',self)
        self.parNameLineEdit.setText(name)
        self.parValueLineEdit.setText(str(value))
        self.setWindowTitle('Metadata Dilaog')
        self.show()
        
class InsertCol_Dialog(QDialog):
    def __init__(self,colName='colx',minCounter=0,maxCounter=100, expr=None,parent=None):
        QDialog.__init__(self,parent)
        loadUi('UI_Forms/InsertCol_Dialog.ui',self)
        self.colNameLineEdit.setText(colName)
        if expr is not None:
            self.colExprTextEdit.setText(expr)
        self.minCounterLineEdit.setText(str(minCounter))
        self.maxCounterLineEdit.setText(str(maxCounter))
        self.setWindowTitle('Data Column Dialog')
        self.show()
        
        

class Data_Dialog(QDialog):
    def __init__(self,fname=None,data=None,comment='#',skiprows=0,delimiter=' ',autoupdate=False,parent=None,matplotlib=False,plotIndex=None):
        QDialog.__init__(self,parent=parent)
        loadUi('UI_Forms/Data_Dialog.ui',self)
        self.plotWidget=PlotWidget(parent=self,matplotlib=matplotlib)
        self.plotTab=self.tabWidget.addTab(self.plotWidget,'Plots')
        self.tabWidget.setCurrentIndex(0)
        self.show()
        self.fileWatcher=QFileSystemWatcher()
        self.fileWatcher.fileChanged.connect(self.fileUpdated)
        self.cwd=None
        self.plotNum=0
        self.xlabel=[]
        self.ylabel=[]
        self.oldPlotIndex={}
        self.dataAltered=False
        if data is not None:
            self.data=data
        elif fname is not None:
            self.data=self.readData(fname,comment=comment,skiprows=skiprows,delimiter=delimiter)
        if self.data is not None:
            self.setMeta2Table()
            self.setData2Table()
            self.addPlots(plotIndex=plotIndex)
        self.init_signals()
        self.okPushButton.setAutoDefault(False)
        self.closePushButton.setAutoDefault(False)
        self.openDataFilePushButton.setAutoDefault(False)
        self.okPushButton.setDefault(False)
        self.closePushButton.setDefault(False)
        self.openDataFilePushButton.setDefault(False)
        self.setWindowTitle('Data Dialog')
        #self.setWindowSize((600,400))
            
    def init_signals(self):
        self.closePushButton.clicked.connect(self.closeWidget)
        self.okPushButton.clicked.connect(self.acceptWidget)
        
        self.openDataFilePushButton.clicked.connect(self.openFile)
        self.autoUpdateCheckBox.stateChanged.connect(self.autoUpdate_ON_OFF)
        self.saveDataPushButton.clicked.connect(self.saveData)
        self.addPlotPushButton.clicked.connect(self.addPlots)
        self.plotSetupTableWidget.cellChanged.connect(self.updatePlotData)
        self.removePlotPushButton.clicked.connect(self.removePlots)
        
        self.addMetaDataPushButton.clicked.connect(self.addMetaData)
        self.metaDataTableWidget.itemChanged.connect(self.metaDataChanged)
        self.metaDataTableWidget.itemClicked.connect(self.metaDataClicked)
        self.metaDataTableWidget.itemSelectionChanged.connect(self.metaDataSelectionChanged)
        self.removeMetaDataPushButton.clicked.connect(self.removeMetaData)
        
        self.dataTableWidget.itemChanged.connect(self.dataChanged)
        self.addColumnPushButton.clicked.connect(lambda x: self.addDataColumn(colName='colX'))
        self.removeColumnPushButton.clicked.connect(self.removeDataColumn)
        self.removeRowsPushButton.clicked.connect(self.removeDataRows)
        self.dataTableWidget.horizontalHeader().sortIndicatorChanged.connect(self.dataSorted)
        self.addRowPushButton.clicked.connect(self.addDataRow)
        
           
                   
    def closeWidget(self):
        self.reject()
        
    def acceptWidget(self):
        self.accept()
        
    def addMetaData(self):
        """
        Opens a MetaData Dialog and by accepting the dialog inputs the data to the MetaDataTable
        """
        
        self.metaDialog=MetaData_Dialog()
        if self.metaDialog.exec_():
            name,value=self.metaDialog.parNameLineEdit.text(),self.metaDialog.parValueLineEdit.text()
            if name not in self.data['meta'].keys():
                row=self.metaDataTableWidget.rowCount()
                self.metaDataTableWidget.insertRow(row)
                self.metaDataTableWidget.setItem(row,0,QTableWidgetItem(name))
                self.metaDataTableWidget.setItem(row,1,QTableWidgetItem(value))
                try:
                    self.data['meta'][name]=eval(value)
                except:
                    self.data['meta'][name]=value
            else:
                QMessageBox.warning(self,"Parameter Exists","The parameter %s already exists in meta data. Please provide a different parameter name"%name,QMessageBox.Ok)
                self.addMetaData()
                
    def removeMetaData(self):
        """
        Removes the selected Metadata from the table
        """
        self.metaDataTableWidget.itemSelectionChanged.disconnect()
        rows=list(set([item.row() for item in self.metaDataTableWidget.selectedItems()]))
        for row in rows:
            key=self.metaDataTableWidget.item(row,0).text()
            if key!='col_names':
                del self.data['meta'][key]
                self.metaDataTableWidget.removeRow(row)
            else:
                QMessageBox.warning(self,'Restricted Parameter','You cannot delete the parameter %s'%key,QMessageBox.Ok)
        self.metaDataTableWidget.itemSelectionChanged.connect(self.metaDataSelectionChanged)
            
        
    def metaDataChanged(self,item):
        """
        Updates the value metadata as per the changes in the metaDataTableWidget
        """
        row=item.row()
        col=item.column()
        key=self.metaDataTableWidget.item(row,0).text()
        if col!=0:
            try:
                self.data['meta'][key]=eval(item.text())
            except:
                self.data['meta'][key]=item.text()
            if self.metaDataTableWidget.item(row,0).text()=='col_names' and len(self.data['meta'][key])!=len(self.data['data'].columns):
                QMessageBox.warning(self,'Restricted Parameter','Please provide same length of col_names as the number of the column of the data')
                self.data['meta'][key]=eval(self.oldMetaText)
                item.setText(self.oldMetaText)
            elif self.metaDataTableWidget.item(row,0).text()=='col_names' and len(self.data['meta'][key])==len(self.data['data'].columns):
                self.data['data'].columns=self.data['meta'][key]
                self.dataTableWidget.setHorizontalHeaderLabels(self.data['meta'][key])
                self.dataAltered=True
                self.resetPlotSetup()
                self.dataAltered=False
        else:
            if self.oldMetaText=='col_names':
                QMessageBox.warning(self,'Restricted Parameter','col_names is a restricted parameter the name of which cannot be changed',QMessageBox.Ok)
                item.setText(self.oldMetaText)
            elif item.text() not in self.data['meta'].keys():
                self.data['meta'][key]=self.data['meta'][self.oldMetaText]
                del self.data['meta'][self.oldMetaText]
            else:
                self.metaDataTableWidget.itemChanged.disconnect()
                QMessageBox.warning(self,"Parameter Exists","The parameter %s already exists in meta data. Please provide a different parameter name"%item.text(),QMessageBox.Ok)
                item.setText(self.oldMetaText)
                self.metaDataTableWidget.itemChanged.connect(self.metaDataChanged)
        self.oldMetaText=item.text()
                
                
    def metaDataClicked(self,item):
        self.oldMetaText=item.text()
        
    def metaDataSelectionChanged(self):
        self.oldMetaText=self.metaDataTableWidget.selectedItems()[0].text()

    def dataChanged(self,item):
        row,col=item.row(),item.column()
        key=self.dataTableWidget.horizontalHeaderItem(col).text()
        self.data['data'][key][row]=eval(item.text())
        self.dataAltered=True
        self.resetPlotSetup()
        self.dataAltered=False
        
    def dataSorted(self):
        """
        Updates the data after sorting the DataTableWidget
        """
        self.getDataFromTable()
        self.dataAltered=True
        self.resetPlotSetup()
        self.dataAltered=False
        
    def addDataRow(self):
        try:
            self.dataTableWidget.itemChanged.disconnect()
        except:
            pass
        row=self.dataTableWidget.currentRow()
        self.dataTableWidget.insertRow(row+1)
        for col in range(self.dataTableWidget.columnCount()):
            self.dataTableWidget.setItem(row+1,col,QCustomTableWidgetItem(float(self.dataTableWidget.item(row,col).text())))
        self.getDataFromTable()
        self.dataAltered=True
        self.resetPlotSetup()
        self.dataAltered=False
        self.dataTableWidget.itemChanged.connect(self.dataChanged)
        
        
        
        
    def addDataColumn(self,colName='colx',expr=None):
        row,col=self.data['data'].shape
        self.insertColDialog=InsertCol_Dialog(colName=colName,minCounter=1,maxCounter=row,expr=expr)
        if self.insertColDialog.exec_():
            imin=eval(self.insertColDialog.minCounterLineEdit.text())
            imax=eval(self.insertColDialog.maxCounterLineEdit.text())
            i=np.arange(imin,imax+1)            
            colname=self.insertColDialog.colNameLineEdit.text()
            if colname not in self.data['data'].columns:
                try:
                    self.data['data'][colname]=eval(expr)
                except:
                    try:
                        expr=self.insertColDialog.colExprTextEdit.toPlainText()
                        expr=expr.replace('col.','self.data[\'data\'].')
                        self.data['data'][colname]=eval(expr)
                    except:
                        QMessageBox.warning(self,'Column Error','Please check the expression',QMessageBox.Ok)
                        self.addDataColumn(colName='colx',minCounter=imin,maxCounter=imax,expr=expr)
                self.setData2Table()
                self.dataAltered=True
                self.resetPlotSetup()
                self.dataAltered=False
            else:
                QMessageBox.warning(self,'Column Name Error','Please choose different column name than the exisiting ones',QMessageBox.Ok)
                self.addDataColumn(colName='colx',minCounter=imin,maxCounter=imax,expr=expr)
                
    def removeDataColumn(self):
        """
        Removes selected columns from dataTableWidget
        """
        colIndexes=self.dataTableWidget.selectionModel().selectedColumns()
        if self.dataTableWidget.columnCount()-len(colIndexes)>=2:
            for index in colIndexes:
                self.dataTableWidget.removeColumn(index.column())
            self.getDataFromTable()
            self.dataAltered=True
            self.resetPlotSetup()
            self.dataAltered=False
        else:
            QMessageBox.warning(self,'Remove Error','Cannot these many column because Datawidget needs to have atleast two columns',QMessageBox.Ok)
                
    def removeDataRows(self):
        rowIndexes=[index.row() for index in self.dataTableWidget.selectionModel().selectedRows()]
        rowIndexes.sort(reverse=True)
        if len(rowIndexes)>0:
            ans=QMessageBox.question(self,'Confirmation','Are you sure of removing the selected rows?',QMessageBox.Yes,QMessageBox.No)
            if ans==QMessageBox.Yes:
                for i in rowIndexes:
                    self.dataTableWidget.removeRow(i)
                self.getDataFromTable()
                self.dataAltered=True
                self.resetPlotSetup()
                self.dataAltered=False
                        
            
            
    def setMeta2Table(self):
        """
        Populates the metaDataTable widget with metadata avaiable from the data
        """
        try:
            self.metaDataTableWidget.itemChanged.disconnect()
            self.metaDataTableWidget.itemSelectionChanged.disconnect()
        except:
            pass
        self.metaDataTableWidget.clear()
        self.metaDataTableWidget.setColumnCount(2)
        self.metaDataTableWidget.setRowCount(len(self.data['meta'].keys()))
        for num,key in enumerate(self.data['meta'].keys()):
            self.metaDataTableWidget.setItem(num,0,QTableWidgetItem(key))
            self.metaDataTableWidget.setItem(num,1,QTableWidgetItem(str(self.data['meta'][key])))
        if 'col_names' not in self.data['meta'].keys():
            self.data['meta']['col_names']=self.data['data'].columns.tolist()
            self.metaDataTableWidget.insertRow(self.metaDataTableWidget.rowCount())
            self.metaDataTableWidget.setItem(num+1,0,QTableWidgetItem('col_names'))
            self.metaDataTableWidget.setItem(num+1,1,QTableWidgetItem(str(self.data['meta']['col_names'])))
        self.metaDataTableWidget.setHorizontalHeaderLabels(['Parameter','Value'])
        self.metaDataTableWidget.itemChanged.connect(self.metaDataChanged)
        self.metaDataTableWidget.itemSelectionChanged.connect(self.metaDataSelectionChanged)
        
            
    def getMetaFromTable(self):
        self.data['meta']={}
        for i in range(self.metaDataTableWidget.rowCount()):
            try:
                self.data['meta'][self.metaDataTableWidget.item(i,0).text()]=eval(self.metaDataTableWidget.item(i,1).text())
            except:
                self.data['meta'][self.metaDataTableWidget.item(i,0).text()]=self.metaDataTableWidget.item(i,1).text()
            
    def setData2Table(self):
        """
        Populates the dataTableWidget with data available from data
        """
        try:
            self.dataTableWidget.itemChanged.disconnect()
        except:
            pass
        self.dataTableWidget.clear()
        self.dataTableWidget.setColumnCount(len(self.data['data'].columns))
        self.dataTableWidget.setRowCount(len(self.data['data'].index))
        for j,colname in enumerate(self.data['data'].columns):
            for i in range(len(self.data['data'].index)):
                #self.dataTableWidget.setItem(i,j,QTableWidgetItem(str(self.data['data'][colname][i])))
                self.dataTableWidget.setItem(i,j,QCustomTableWidgetItem(self.data['data'][colname][i]))
        self.dataTableWidget.setHorizontalHeaderLabels(self.data['data'].columns.values.tolist())
        self.dataTableWidget.itemChanged.connect(self.dataChanged)
            
        
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
                        try:
                            self.data['meta'][key]=eval(value) # When the value is either valid number, lists, arrays, dictionaries
                        except:
                            self.data['meta'][key]=value # When the value is just a string
                    except:
                        pass
                else:
                    if '\t' in line:
                        delimiter='\t'
                    elif ',' in line:
                        delimiter=','                            
                    break
            if 'col_names' in self.data['meta'].keys():
                self.data['data']=pd.read_csv(self.fname,comment=comment,names=self.data['meta']['col_names'],header=None,delimiter=delimiter)
            else:
                self.data['data']=pd.read_csv(self.fname,comment=comment,header=None,delimiter=delimiter)
                self.data['data'].columns=['Col_%d'%i for i in self.data['data'].columns.values.tolist()]
                self.data['meta']['col_names']=self.data['data'].columns.values.tolist()
            #print(self.data['data'])
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
            self.dataAltered=True
            self.resetPlotSetup()
            self.dataAltered=False
    
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
        if fname!='':
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
        if fname!='':
            self.data=self.readData(fname=fname)
            if self.data is not None:
                self.setMeta2Table()
                self.setData2Table()
                self.dataAltered=True
                self.resetPlotSetup()
                self.dataAltered=False
                
            
    def resetPlotSetup(self):
        try:
            self.plotSetupTableWidget.cellChanged.disconnect()
        except:
            pass
        columns=self.data['data'].columns.tolist()
        self.xlabel=[]
        self.ylabel=[]
        for row in range(self.plotSetupTableWidget.rowCount()):
            for i in range(1,3):
                self.plotSetupTableWidget.cellWidget(row,i).currentIndexChanged.disconnect()
                self.plotSetupTableWidget.cellWidget(row,i).clear()
                self.plotSetupTableWidget.cellWidget(row,i).addItems(columns)
                self.plotSetupTableWidget.cellWidget(row,i).setCurrentIndex(i-1)
                self.plotSetupTableWidget.cellWidget(row,i).currentIndexChanged.connect(self.updatePlotData)
            self.xlabel.append('[%s]'%self.plotSetupTableWidget.cellWidget(row,1).currentText())
            self.ylabel.append('[%s]'%self.plotSetupTableWidget.cellWidget(row,2).currentText())
            self.plotSetupTableWidget.cellWidget(row,3).currentIndexChanged.disconnect()
            self.plotSetupTableWidget.cellWidget(row,3).clear()
            self.plotSetupTableWidget.cellWidget(row,3).addItems(['None']+columns)
            self.plotSetupTableWidget.cellWidget(row,3).setCurrentIndex(0)
            self.plotSetupTableWidget.cellWidget(row,3).currentIndexChanged.connect(self.updatePlotData)
            self.plotSetupTableWidget.setCurrentCell(row,3)
            self.updatePlotData()
        self.plotSetupTableWidget.cellChanged.connect(self.updatePlotData)         
                
        
            
            
    def addPlots(self,plotIndex=None):
        #self.plotSetupTableWidget.clear()
        try:
            self.plotSetupTableWidget.cellChanged.disconnect()
        except:
            pass
        columns=self.data['data'].columns.tolist()
        if len(columns)>=2:
            self.plotSetupTableWidget.insertRow(self.plotSetupTableWidget.rowCount())
            row=self.plotSetupTableWidget.rowCount()-1
            self.plotSetupTableWidget.setItem(row,0,QTableWidgetItem('Data_%d'%self.plotNum))
            for i in range(1,3):
                self.plotSetupTableWidget.setCellWidget(row,i,QComboBox())
                self.plotSetupTableWidget.cellWidget(row,i).addItems(columns)
                if plotIndex is not None:
                    self.plotSetupTableWidget.cellWidget(row,i).setCurrentIndex(plotIndex[i-1])
                else:
                    self.plotSetupTableWidget.cellWidget(row,i).setCurrentIndex(i-1)
                self.plotSetupTableWidget.cellWidget(row,i).currentIndexChanged.connect(self.updatePlotData)
            self.xlabel.append('[%s]'%self.plotSetupTableWidget.cellWidget(row,1).currentText())
            self.ylabel.append('[%s]'%self.plotSetupTableWidget.cellWidget(row,2).currentText())
            self.plotSetupTableWidget.setCellWidget(row,3,QComboBox())
            self.plotSetupTableWidget.cellWidget(row,3).addItems(['None']+columns)
            if plotIndex is not None:
                self.plotSetupTableWidget.cellWidget(row,3).setCurrentIndex(plotIndex[-1])
            else:
                try:
                    self.plotSetupTableWidget.cellWidget(row,3).setCurrentIndex(3)
                except:
                    self.plotSetupTableWidget.cellWidget(row,3).setCurrentIndex(0)
            self.plotSetupTableWidget.cellWidget(row,3).currentIndexChanged.connect(self.updatePlotData)
            self.plotSetupTableWidget.cellWidget(row,3).currentIndexChanged.connect(self.updatePlotData)
            self.plotSetupTableWidget.setCurrentCell(row,3)
            self.updatePlotData()
            self.plotNum+=1
        else:
            QMessageBox.warning(self,'Data file error','The data file do not have two or more columns to be plotted.',QMessageBox.Ok)
        self.plotSetupTableWidget.cellChanged.connect(self.updatePlotData)
        
    def removePlots(self):
        """
        Removes data for PlotSetup
        """
        try:
            self.plotSetupTableWidget.cellChanged.disconnect()
        except:
            pass
        rowIndexes=self.plotSetupTableWidget.selectionModel().selectedRows()
        if self.plotSetupTableWidget.rowCount()-len(rowIndexes)>=1:
            for index in rowIndexes:
                row=index.row()
                name=self.plotSetupTableWidget.item(row,0).text()
                self.plotWidget.remove_data([name])
                self.dataTableWidget.removeRow(index.row())            
        self.plotSetupTableWidget.cellChanged.connect(self.updatePlotData)
            
        
        
    def updatePlotData(self):
        row=self.plotSetupTableWidget.currentRow()
        name=self.plotSetupTableWidget.item(row,0).text()
        if self.dataAltered:
            for i in range(1,4):
                try:
                    self.plotSetupTableWidget.cellWidget(row,i).setCurrentIndex(self.oldPlotIndex[name][i-1]) 
                except:
                    pass           
        xcol,ycol,yerrcol=[self.plotSetupTableWidget.cellWidget(row,i).currentText() for i in range(1,4)] 
        #ycol=self.plotSetupTableWidget.cellWidget(row,2).currentText()
        #yerrcol=self.plotSetupTableWidget.cellWidget(row,3).currentText()
        if yerrcol!='None':
            if ycol=='fit':
                self.plotWidget.add_data(self.data['data'][xcol].values,self.data['data'][ycol].values,yerr=self.data['data'][yerrcol].values,name=name,fit=True)
            else:
                self.plotWidget.add_data(self.data['data'][xcol].values,self.data['data'][ycol].values,yerr=self.data['data'][yerrcol].values,name=name,fit=False)
        else:
            if ycol=='fit':
                self.plotWidget.add_data(self.data['data'][xcol].values,self.data['data'][ycol].values,name=name,fit=True)
            else:
                self.plotWidget.add_data(self.data['data'][xcol].values,self.data['data'][ycol].values,name=name,fit=False)
        self.xlabel[row]='[%s]'%self.plotSetupTableWidget.cellWidget(row,1).currentText()
        self.ylabel[row]='[%s]'%self.plotSetupTableWidget.cellWidget(row,2).currentText()
        self.updatePlot()
        self.oldPlotIndex[name]=[self.plotSetupTableWidget.cellWidget(row,i).currentIndex() for i in range(1,4)]
        
            
    def updatePlot(self):
        names=[self.plotSetupTableWidget.item(i,0).text() for i in range(self.plotSetupTableWidget.rowCount())]
        self.plotColIndex=[self.plotSetupTableWidget.cellWidget(0,i).currentIndex() for i in range(1,4)]
        self.externalData=copy.copy(self.data['meta'])
        self.externalData['x']=copy.copy(self.data['data'][self.plotSetupTableWidget.cellWidget(0,1).currentText()].values)
        self.externalData['y']=copy.copy(self.data['data'][self.plotSetupTableWidget.cellWidget(0,2).currentText()].values)
        if self.plotSetupTableWidget.cellWidget(0,3).currentText()=='None':
            self.externalData['yerr']=np.ones_like(self.externalData['x'])
        else:
            self.externalData['yerr']=copy.copy(self.data['data'][self.plotSetupTableWidget.cellWidget(0,3).currentText()].values)
        self.plotWidget.Plot(names)
        self.plotWidget.setXLabel(' '.join(self.xlabel))
        self.plotWidget.setYLabel(' '.join(self.ylabel))
        
if __name__=='__main__':
    app=QApplication(sys.argv)
    fname=r'X:/2018-04/Y_corrected_energy_flu.txt'
    #data={'meta':{'a':1,'b':2},'data':pd.DataFrame({'x':np.arange(1000),'y':np.arange(1000),'y_err':np.arange(1000)})}
    try:
        w=Data_Dialog(fname=fname,matplotlib=False)
    except:
        w=Data_Dialog(data=data,matplotlib=False)
    w.resize(600,400)
#    w.showFullScreen()
    sys.exit(app.exec_())
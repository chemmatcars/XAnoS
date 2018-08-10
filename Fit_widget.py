from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QCheckBox, QSpinBox, QComboBox, QListWidget, QDialog, QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem, QAbstractItemView, QSpinBox, QSplitter, QSizePolicy, QAbstractScrollArea, QHBoxLayout, QTextEdit
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt, QThread
import os
import sys
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
from PlotWidget import PlotWidget
import copy
import numpy as np
from Data_Dialog import Data_Dialog
from readData import read1DSAXS
from importlib import import_module, reload
from Fit_Routines import Fit
import numbers
import time
import shutil
from FunctionEditor import FunctionEditor
from lmfit import conf_interval, printfuncs

class minMaxDialog(QDialog):
    def __init__(self,value,minimum=None,maximum=None,expr=None,brute_step=None,parent=None):
        QDialog.__init__(self,parent)
        self.value=value
        if minimum is None:
            self.minimum=-np.inf
        else:
            self.minimum=minimum
        if maximum is None:
            self.maximum=np.inf
        else:
            self.maximum=maximum
        self.expr=expr
        self.brute_step=brute_step
        self.createUI()
        
    def createUI(self):
        self.vblayout=QVBoxLayout(self)
        self.layoutWidget=pg.LayoutWidget()
        self.vblayout.addWidget(self.layoutWidget)
        
        valueLabel=QLabel('Value:')
        self.layoutWidget.addWidget(valueLabel)
        self.layoutWidget.nextColumn()
        self.valueLineEdit=QLineEdit(str(self.value))
        self.layoutWidget.addWidget(self.valueLineEdit)
        
        self.layoutWidget.nextRow()
        minLabel=QLabel('Minimum')
        self.layoutWidget.addWidget(minLabel)
        self.layoutWidget.nextColumn()
        self.minimumLineEdit=QLineEdit(str(self.minimum))
        self.layoutWidget.addWidget(self.minimumLineEdit)
        
        self.layoutWidget.nextRow()
        maxLabel=QLabel('Maximum')
        self.layoutWidget.addWidget(maxLabel)
        self.layoutWidget.nextColumn()
        self.maximumLineEdit=QLineEdit(str(self.maximum))
        self.layoutWidget.addWidget(self.maximumLineEdit)
        
        self.layoutWidget.nextRow()
        exprLabel=QLabel('Expr')
        self.layoutWidget.addWidget(exprLabel)
        self.layoutWidget.nextColumn()
        self.exprLineEdit=QLineEdit(str(self.expr))
        self.layoutWidget.addWidget(self.exprLineEdit)
        
        self.layoutWidget.nextRow()
        bruteStepLabel=QLabel('Brute step')
        self.layoutWidget.addWidget(bruteStepLabel)
        self.layoutWidget.nextColumn()
        self.bruteStepLineEdit=QLineEdit(str(self.brute_step))
        self.layoutWidget.addWidget(self.bruteStepLineEdit)
        
        self.layoutWidget.nextRow()
        self.cancelButton=QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.cancelandClose)
        self.layoutWidget.addWidget(self.cancelButton)
        self.layoutWidget.nextColumn()
        self.okButton=QPushButton('OK')
        self.okButton.clicked.connect(self.okandClose)
        self.layoutWidget.addWidget(self.okButton)
        self.okButton.setDefault(True)
        
    def okandClose(self):
        try:
            self.value=float(self.valueLineEdit.text())
            self.minimum=float(self.minimumLineEdit.text())
            self.maximum=float(self.maximumLineEdit.text())
            self.expr=self.exprLineEdit.text()
            if self.bruteStepLineEdit.text()!='None':
                self.brute_step=float(self.bruteStepLineEdit.text())
            else:
                self.brute_step=None
            self.accept()
        except:
            QMessageBox.warning('Value Error','Value, Min, Max should be floating point numbers',QMessageBox.Ok)

    def cancelandClose(self):
        self.reject()

class FitResultDialog(QDialog):
    def __init__(self,fit_report,fit_info,parent=None):
        QDialog.__init__(self,parent)
        self.fit_report=fit_report
        self.fit_info=fit_info
        self.createUI()
        self.resize(600,400)
        
    def createUI(self):
        self.vblayout=QVBoxLayout(self)
        self.layoutWidget=pg.LayoutWidget()
        self.vblayout.addWidget(self.layoutWidget)
        
        fitReportLabel=QLabel('Fit Report')
        self.layoutWidget.addWidget(fitReportLabel,colspan=2)
        self.layoutWidget.nextRow()
        self.fitReportTextEdit=QTextEdit()
        self.fitReportTextEdit.setText(self.fit_report)
        self.layoutWidget.addWidget(self.fitReportTextEdit,colspan=2)
        
        self.layoutWidget.nextRow()
        fitInfoLabel=QLabel('Fit Info')
        self.layoutWidget.addWidget(fitInfoLabel,colspan=2)
        self.layoutWidget.nextRow()
        self.fitInfoTextEdit=QTextEdit()
        self.fitInfoTextEdit.setText(self.fit_info)
        self.layoutWidget.addWidget(self.fitInfoTextEdit,colspan=2)
        
        self.layoutWidget.nextRow()
        self.cancelButton=QPushButton('Reject')
        self.cancelButton.clicked.connect(self.cancelandClose)
        self.layoutWidget.addWidget(self.cancelButton,col=0)
        self.okButton=QPushButton('Accept')
        self.okButton.clicked.connect(self.okandClose)
        self.layoutWidget.addWidget(self.okButton,col=1)
        self.okButton.setDefault(True)
        
    def okandClose(self):
        self.accept()
        
    def cancelandClose(self):
        self.reject()


class Fit_Widget(QWidget):
    """
    This widget class is developed to provide an end-user a *Graphical User Interface* by which either they can develop their own fitting functions in python or use the existing fitting functions under different categories to analyze different kinds of one-dimensional data sets. 'LMFIT':https://lmfit.github.io/lmfit-py/ is extensively used within this widget.
    
    **Features**
    
    1. Read and fit multiple data files
    2. Already available functions are categorized as per the function types and techniques
    3. Easy to add more catergories and user-defined functions
    4. Once the function is defined properly all the free and fitting parameters will be available within the GUI as tables.
    5. An in-built Function editor with a function template is provided.
    6. The function editor is enabled with python syntax highlighting.
    
    **Usage**
    
    :class:`Fit_Widget` can be used as stand-alone python fitting package by running it in terminal as::
    
        $python Fit_widget.py
        
    .. image:: Figures/Fit_widget.png
       :scale: 80
       
       `Fit_widget` in action.
    
    Also it can be used as a widget with any other python application.
    """
    
    def __init__(self,parent=None):
        
        QWidget.__init__(self,parent)
               
        self.vblayout=QVBoxLayout(self)
        self.mainDock=DockArea(self,parent)
        self.vblayout.addWidget(self.mainDock)
        
        self.funcDock=Dock('Functions',size=(1,8))
        self.dataDock=Dock('Data',size=(1,8))
        self.paramDock=Dock('Parameters',size=(2,8))
        self.plotDock=Dock('Data and Fit',size=(5,8))
        self.mainDock.addDock(self.dataDock)
        self.mainDock.addDock(self.paramDock,'right')
        self.mainDock.addDock(self.plotDock,'right')
        self.mainDock.addDock(self.funcDock,'above',self.dataDock)
        self.special_keys=['x','params','choices','output_params','__mpar__']
        self.curr_funcClass={}
        
        
        self.data={}
        self.dlg_data={}
        self.plotColIndex={}
        self.curDir=os.getcwd()
        self.fileNumber=0
        self.fileNames={}
        self.fchanged=True

        self.fitMethods={'Levenberg-Marquardt':'leastsq',
                         'Trust-Region-Reflection': 'least_sq',
                         'Differential-Evolution': 'differential_evolution',
                         'Brute-Force':'brute',
                         'Nelder-Mead':'nelder',
                         'L-BFGS-B':'lbfgsb',
                         'Powell':'powell',
                         'Congugate-Gradient':'cg',
                         'Newton-Congugate-Gradient':'newton',
                         'Cobyla':'cobyla',
                         'Truncate-Newton':'tnc',
                         'Trust-Newton-Conjugate-Gradient':'trust-ncg',
                         'Dogleg':'dogleg',
                         'Sequential-Linear -quare':'slsqp'}
        
        
        self.create_funcDock()
        self.create_dataDock()
        self.create_plotDock()
        self.update_catagories()
        self.create_paramDock()
        self.xminmaxChanged()

        
    def create_funcDock(self):
        self.funcLayoutWidget=pg.LayoutWidget(self)
        row=0
        col=0
        funcCategoryLabel=QLabel('Function Categories:')
        self.funcLayoutWidget.addWidget(funcCategoryLabel,row=row,col=col,colspan=2)
        
        row+=1
        col=0
        self.addCategoryButton=QPushButton('Create')
        self.addCategoryButton.clicked.connect(self.addCategory)
        self.funcLayoutWidget.addWidget(self.addCategoryButton,row=row,col=col)
        col+=1
        self.removeCategoryButton=QPushButton('Remove')
        self.removeCategoryButton.clicked.connect(self.removeCategory)
        self.funcLayoutWidget.addWidget(self.removeCategoryButton,row=row,col=col)
        
        row+=1
        col=0
        self.categoryListWidget=QListWidget()
        self.categoryListWidget.currentItemChanged.connect(self.update_functions)
        self.funcLayoutWidget.addWidget(self.categoryListWidget,row=row,col=col,colspan=2)
        
        row+=1
        col=0
        funcLabel=QLabel('Functions:')
        self.funcLayoutWidget.addWidget(funcLabel,row=row,col=col,colspan=2)
        
        row+=1
        col=0
        self.addFuncButton=QPushButton('Create')
        self.addFuncButton.clicked.connect(self.addFunction)
        self.funcLayoutWidget.addWidget(self.addFuncButton,row=row,col=col)
        col+=1
        self.removeFuncButton=QPushButton('Remove')
        self.removeFuncButton.clicked.connect(self.removeFunction)
        self.funcLayoutWidget.addWidget(self.removeFuncButton,row=row,col=col)
        
        row+=1
        col=0
        self.funcListWidget=QListWidget()
        self.funcListWidget.itemSelectionChanged.connect(self.functionChanged)
        self.funcListWidget.itemDoubleClicked.connect(self.openFunction)
        self.funcLayoutWidget.addWidget(self.funcListWidget,row=row,col=col,colspan=2)
        
        self.funcDock.addWidget(self.funcLayoutWidget)
        
    def addCategory(self):
        tdir=QFileDialog.getExistingDirectory(self,'Select a folder','self.curDir',QFileDialog.ShowDirsOnly)
        if tdir!='': 
            cdir=os.path.basename(os.path.normpath(tdir))
            fh=open(os.path.join(tdir,'__init__.py'),'w')
            fh.write('__all__=[]')
            fh.close()
            if cdir not in self.categories:
                self.categories.append(cdir)
                self.categoryListWidget.addItem(cdir)
            else:
                QMessageBox.warning(self,'Category error','Category already exist!',QMessageBox.Ok)
        
    def removeCategory(self):
        self.funcListWidget.clear()
        if len(self.categoryListWidget.selectedItems())==1:
            ans=QMessageBox.question(self,'Delete warning','Are you sure you would like to delte the category?',QMessageBox.No,QMessageBox.Yes)
            if ans==QMessageBox.Yes:
                category=os.path.abspath('./Functions/%s'%self.categoryListWidget.currentItem().text())
                #os.rename(category,)
                shutil.rmtree(category)
                self.categories.remove(self.categoryListWidget.currentItem().text())
                self.categoryListWidget.takeItem(self.categoryListWidget.currentRow())
        elif len(self.categoryListWidget.selectedItems())>1:
            QMessageBox.warning(self,'Warning','Please select only one category at a time to remove',QMessageBox.Ok)
        else:
            QMessageBox.warning(self,'Warning','Please select one category atleast to remove',QMessageBox.Ok)
            
            
    def openFunction(self):
        dirName=os.path.abspath('./Functions/%s'%self.categoryListWidget.currentItem().text())
        funcName=self.funcListWidget.currentItem().text()
        try:
            if not self.funcEditor.open: 
                self.funcEditor=FunctionEditor(funcName=funcName,dirName=dirName)
                self.funcEditor.setWindowTitle('Function editor')
                self.funcEditor.show()
                self.funcOpen=self.funcEditor.open
                self.funcEditor.closeEditorButton.clicked.connect(self.postAddFunction)
            else:
                QMessageBox.warning(self,'Warning','You cannot edit two functions together',QMessageBox.Ok)
        except:
            self.funcEditor=FunctionEditor(funcName=funcName,dirName=dirName)
            self.funcEditor.setWindowTitle('Function editor')
            self.funcEditor.show()
            self.funcEditor.closeEditorButton.clicked.connect(self.postAddFunction)
                
    def addFunction(self):
        dirName=os.path.abspath('./Functions/%s'%self.categoryListWidget.currentItem().text())
        self.funcEditor=FunctionEditor(dirName=dirName)
        self.funcEditor.setWindowTitle('Function editor')
        self.funcEditor.show()
        self.funcEditor.closeEditorButton.clicked.connect(self.postAddFunction)
        
        
    def postAddFunction(self):
        if self.funcEditor.funcNameLineEdit.text()!='tmpxyz':
            dirName=os.path.abspath('./Functions/%s'%self.categoryListWidget.currentItem().text())
            fh=open(os.path.join(dirName,'__init__.py'),'r')
            line=fh.readlines()
            fh.close()
            funcList=eval(line[0].split('=')[1])
            funcName=self.funcEditor.funcNameLineEdit.text()
            if funcName not in funcList:
                funcList.append(funcName)
                funcList=sorted(list(set(funcList)),key=str.lower)
                os.remove(os.path.join(dirName,'__init__.py'))
                fh=open(os.path.join(dirName,'__init__.py'),'w')
                fh.write('__all__='+str(funcList))
                fh.close()
            self.update_functions()
        
        
    
    def removeFunction(self):
        if len(self.funcListWidget.selectedItems())==1:
            ans=QMessageBox.question(self,'Warning','Are you sure you would like to remove the function',QMessageBox.No,QMessageBox.Yes)
            if ans==QMessageBox.Yes:
                dirName=os.path.abspath('./Functions/%s'%self.categoryListWidget.currentItem().text())
                fname=self.funcListWidget.currentItem().text()
                fh=open(os.path.join(dirName,'__init__.py'),'r')
                line=fh.readlines()
                fh.close()
                funcList=eval(line[0].split('=')[1])
                try:
                    os.remove(os.path.join(dirName,fname+'.py'))
                    os.remove(os.path.join(dirName,'__init__.py'))
                    fh=open(os.path.join(dirName,'__init__.py'),'w')
                    fh.write('__all__='+str(funcList))
                    fh.close()
                    self.update_functions()
                except:
                    QMessageBox.warning(self,'Remove error','Cannot remove the function becuase the function file might be open elsewhere.',QMessageBox.Ok)
        elif len(self.funcListWidget.selectedItems())>1:
            QMessageBox.warning(self,'Warning','Please select only one function at a time to remove',QMessageBox.Ok)
        else:
            QMessageBox.warning(self,'Warning','Please select one function atleast to remove',QMessageBox.Ok)
            
        
        
        
                
        
    def create_dataDock(self):
        self.dataLayoutWidget=pg.LayoutWidget(self)
        
        datafileLabel=QLabel('Data files')
        self.dataLayoutWidget.addWidget(datafileLabel,colspan=2)
        
        self.dataLayoutWidget.nextRow()
        self.addDataButton=QPushButton('Add files')
        self.dataLayoutWidget.addWidget(self.addDataButton)
        self.addDataButton.clicked.connect(lambda x: self.addData())
        self.removeDataButton=QPushButton('Remove Files')
        self.dataLayoutWidget.addWidget(self.removeDataButton,col=1)
        self.removeDataButton.clicked.connect(self.removeData)
        
        
        
        self.dataLayoutWidget.nextRow()
        self.dataListWidget=QListWidget()
        self.dataListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.dataListWidget.itemSelectionChanged.connect(self.dataFileSelectionChanged)
        self.dataListWidget.itemDoubleClicked.connect(self.openDataDialog)
        self.dataLayoutWidget.addWidget(self.dataListWidget,colspan=2)
        
        self.dataLayoutWidget.nextRow()
        xminmaxLabel=QLabel('Xmin:Xmax')
        self.dataLayoutWidget.addWidget(xminmaxLabel)
        self.xminmaxLineEdit=QLineEdit('0:1')
        self.xminmaxLineEdit.returnPressed.connect(self.xminmaxChanged)
        self.dataLayoutWidget.addWidget(self.xminmaxLineEdit,col=1)
        
        self.dataLayoutWidget.nextRow()
        fitMethodLabel=QLabel('Fit Method')
        self.dataLayoutWidget.addWidget(fitMethodLabel)
        self.fitMethodComboBox=QComboBox()
        self.fitMethodComboBox.addItems(list(self.fitMethods.keys()))
        self.dataLayoutWidget.addWidget(self.fitMethodComboBox,col=1)        
        
        self.dataLayoutWidget.nextRow()
        fitScaleLabel=QLabel('Fit Scale')
        self.dataLayoutWidget.addWidget(fitScaleLabel)
        self.fitScaleComboBox=QComboBox()
        self.fitScaleComboBox.addItems(['Linear','Log'])
        self.dataLayoutWidget.addWidget(self.fitScaleComboBox,col=1)
        
        self.dataLayoutWidget.nextRow()
        fitIterationLabel=QLabel('Fit Iterations')
        self.dataLayoutWidget.addWidget(fitIterationLabel)
        self.fitIterationLineEdit=QLineEdit('1000')
        self.dataLayoutWidget.addWidget(self.fitIterationLineEdit,col=1)
        
        self.dataLayoutWidget.nextRow()
        self.fitButton=QPushButton('Fit')
        self.fitButton.clicked.connect(self.doFit)
        self.unfitButton=QPushButton('Undo fit')
        self.unfitButton.clicked.connect(self.undoFit)
        self.dataLayoutWidget.addWidget(self.unfitButton)
        self.dataLayoutWidget.addWidget(self.fitButton,col=1)
        
        self.dataLayoutWidget.nextRow()
        self.autoCICheckBox=QCheckBox()
        self.autoCICheckBox.setTristate(False)
        self.autoCICheckBox.setCheckState(Qt.Unchecked)
        self.autoCICheckBox.setDisabled(True)
        self.calcConfInterButton=QPushButton('Calculate Confidence Interval')
        self.calcConfInterButton.clicked.connect(self.calcConfInterval)
        self.calcConfInterButton.setDisabled(True)
        self.dataLayoutWidget.addWidget(self.autoCICheckBox)
        self.dataLayoutWidget.addWidget(self.calcConfInterButton,col=1)      
        
        self.dataDock.addWidget(self.dataLayoutWidget)
        
    def dataFileSelectionChanged(self):
        self.sfnames=[item.text().split('<>')[1] for item in self.dataListWidget.selectedItems()]
        self.pfnames=[item.text().split('<>')[0] for item in self.dataListWidget.selectedItems()]
        if len(self.sfnames)>0:
            xmin=np.min([np.min(self.data[fname]['x']) for fname in self.sfnames])
            xmax=np.max([np.max(self.data[fname]['x']) for fname in self.sfnames])
            self.xminmaxLineEdit.setText('%0.3f:%0.3f'%(xmin,xmax))
            self.xminmaxChanged()
            text='np.linspace(%.3f,%.3f,100)'%(xmin,xmax)
            self.xLineEdit.setText(text)
            self.xChanged()
            
    def openDataDialog(self,item):
        fnum,fname=item.text().split('<>')
        data_dlg=Data_Dialog(data=self.dlg_data[fname],parent=self,plotIndex=self.plotColIndex[fname])
        if data_dlg.exec_():
            self.plotColIndex[fname]=data_dlg.plotColIndex
            self.dlg_data[fname]=copy.copy(data_dlg.data)
            self.data[fname]=copy.copy(data_dlg.externalData)
            self.plotWidget.add_data(self.data[fname]['x'],self.data[fname]['y'],yerr=self.data[fname]['yerr'],name=fnum)
            self.update_plot()
            
    
    def xminmaxChanged(self):
        self.xmin=float(self.xminmaxLineEdit.text().split(':')[0])
        self.xmax=float(self.xminmaxLineEdit.text().split(':')[1])
    
    def doFit(self):
        self.sfitParamTableWidget.cellChanged.disconnect(self.fitParamChanged)
        self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        self.fit_method=self.fitMethods[self.fitMethodComboBox.currentText()]
        self.fit_scale=self.fitScaleComboBox.currentText()
        self.fit.functionCalled.connect(self.fitCallback)
        for fname in self.sfnames:
            self.fit.x=self.data[fname]['x']
            self.fit.y=self.data[fname]['y']
            self.fit.yerr=self.data[fname]['yerr']
            if len(np.where(self.data[fname]['yerr']<1e-30)[0])>0:
                QMessageBox.warning(self,'Zero Errorbars','Some or all the errorbars of the selected data are zeros. Please select None for the Errorbar column in the Plot options of the data',QMessageBox.Ok)
                break
            self.oldParams=copy.copy(self.fit.params)
            if self.fit.params['__mpar__']!={}:
                self.oldmpar=copy.copy(self.mfitParamData)
            try:
                self.showFitInfoDlg()
                self.runFit()
                #self.fit_report,self.fit_message=self.fit.perform_fit(self.xmin,self.xmax,fit_scale=self.fit_scale,fit_method=self.fit_method,callback=self.fitCallback)

                self.fit_info='Fit Message: %s\n'%self.fit_message

    #            if self.autoCICheckBox.isChecked():
    #                self.confInterval(minimizer=self.fit.fitter,fit_result=self.fit.result)
                self.closeFitInfoDlg()
                for row in range(self.sfitParamTableWidget.rowCount()):
                    key=self.sfitParamTableWidget.item(row,0).text()
                    self.sfitParamTableWidget.item(row,1).setText('%.6e'%(self.fit.result.params[key].value))
                self.sfitParamTableWidget.resizeRowsToContents()
                self.sfitParamTableWidget.resizeColumnsToContents()
                for row in range(self.mfitParamTableWidget.rowCount()):
                    for col in range(self.mfitParamTableWidget.columnCount()):
                        parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                        key='__%s__%03d'%(parkey,row)
                        self.mfitParamTableWidget.item(row,col).setText('%.6e'%(self.fit.result.params[key].value))
                self.sfitParamTableWidget.resizeRowsToContents()
                self.sfitParamTableWidget.resizeColumnsToContents()
                self.mfitParamTableWidget.resizeRowsToContents()
                self.mfitParamTableWidget.resizeColumnsToContents()

                self.update_plot()
                fitResultDlg=FitResultDialog(fit_report=self.fit_report,fit_info=self.fit_info)
                #ans=QMessageBox.question(self,'Accept fit results?',self.fit_report,QMessageBox.Yes, QMessageBox.No)
                if fitResultDlg.exec_():
                    for row in range(self.sfitParamTableWidget.rowCount()):
                        key=self.sfitParamTableWidget.item(row,0).text()
                        try:
                            self.sfitParamTableWidget.item(row,1).setToolTip('%.3e \u00B1 %.3e'%(self.fit.result.params[key].value,self.fit.result.params[key].stderr))
                        except:
                            pass
                        if self.fit.params['__mpar__']!={}:
                            for row in range(self.mfitParamTableWidget.rowCount()):
                                for col in range(self.mfitParamTableWidget.columnCount()):
                                    parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                                    key='__%s__%03d'%(parkey,row)
                                    self.mfitParamTableWidget.item(row,col).setToolTip('%.3e \u00B1 %0.3e'%(self.fit.result.params[key].value,self.fit.result.params[key].stderr))
                                    self.mfitParamData[parkey][row]=self.fit.result.params[key].value
                    ofname=os.path.splitext(fname)[0]
                    header='Data fitted with model: %s on %s\n'%(self.funcListWidget.currentItem().text(),time.asctime())
                    header+='Fixed Parameters\n'
                    header+='----------------\n'
                    for key in self.fit.params.keys():
                        if key not in self.fit.fit_params.keys() and key not in self.special_keys and key[:2]!='__':
                            header+=key+'='+str(self.fit.params[key])+'\n'
                    header+=self.fit_report+'\n'
                    header+='x \t y\t yerr \t yfit'
                    fitdata=np.vstack((self.fit.x[self.fit.imin:self.fit.imax+1],self.fit.y[self.fit.imin:self.fit.imax+1],self.fit.yerr[self.fit.imin:self.fit.imax+1],self.fit.yfit)).T
                    np.savetxt(ofname+'_fit.txt',fitdata,header=header,comments='#')
                else:
                    self.undoFit()
            except:
                try:
                    self.closeFitInfoDlg()
                except:
                    pass
                QMessageBox.warning(self,'Minimization failed','The initial guesses of the parameters are too far probably!',QMessageBox.Ok)
                self.update_plot()
                break
        self.sfitParamTableWidget.cellChanged.connect(self.fitParamChanged)
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
        self.fit.functionCalled.disconnect(self.fitCallback)
        
    def calcConfInterval(self):
        self.autoCICheckBox.setCheckState(Qt.Unchecked)
        self.confInterval(minimizer=self.fit.fitter,fit_result=self.fit.result)
        
    def confInterval(self,minimizer=None,fit_result=None):
        """
        """
        if minimizer is not None and fit_result is not None:
#            try:
            self.confIntervalStatus=QMessageBox(parent=self)
            self.confIntervalStatus.setWindowTitle('Confidence Interval Calculation')
            self.confIntervalStatus.setText('Calulationg confidence intervals for all the fitting parameters. Please wait...\n')
            self.confIntervalStatus.addButton(QMessageBox.Close)
            self.fit.functionCalled.connect(self.conf_interv_status)
            self.confIntervalStatus.open()
            ci= conf_interval(minimizer,fit_result,sigmas=[1,2,3],maxiter=int(self.fitIterationLineEdit.text()))
            if self.autoCICheckBox.isChecked():
                self.fitIterLabel.setText('Calculating confidence intervals of the parameters. Please wait...')
                self.fit_report+='Confidence Intervals\n'
                self.fit_report+='--------------------\n'
                self.fit_report+=printfuncs.report_ci(ci)+'\n'
            else:
                text='Confidence Intervals are:\n'
                text+=('{:>10s} '+'{:>10s} '*7+'\n').format('Parameters','-3sig','-2sig','-1sig','Best','1sig','2sig','3sig')
                for key in ci.keys():
                    text+=('{:>10s} '+'{:.4e} '*7+'\n').format(key,*[ci[key][i][1] for i in range(7)])
                self.confIntervalStatus.setText(text)
            self.fit.functionCalled.disconnect(self.conf_interv_status)
#            except:
#                QMessageBox.information(self,'Info','Couldnot calculate confidence interval because the error estimated couldnot be calculated.',QMessageBox.Ok)
        else:
            QMessageBox.warning(self,'Fit warning','Please fit the data first before calculating confidence intervals',QMessageBox.Ok)
                
    def conf_interv_status(self,params,iterations,residual,fit_scale):
        self.confIntervalStatus.setText(self.confIntervalStatus.text().split('\n')[0]+'\n\n {:^s} = {:10d}'.format('Iteration',iterations))            
        QApplication.processEvents()
        
    def runFit(self):
        self.fit_report,self.fit_message=self.fit.perform_fit(self.xmin,self.xmax,fit_scale=self.fit_scale,fit_method=self.fit_method,maxiter=int(self.fitIterationLineEdit.text()))
        
    
    def showFitInfoDlg(self):
        self.fitInfoDlg=QDialog()        
        vblayout=QVBoxLayout(self.fitInfoDlg)
        self.fitIterLabel=QLabel('Iteration: 0,\t Chi-sqr: Not Available',self.fitInfoDlg)
        vblayout.addWidget(self.fitIterLabel)
        self.stopFitPushButton=QPushButton('Stop')
        vblayout.addWidget(self.stopFitPushButton)
        self.stopFitPushButton.clicked.connect(self.stopFit)
        self.fitInfoDlg.setWindowTitle('Please wait for the fitting to be completed')
        self.fitInfoDlg.setModal(True)
        self.fitInfoDlg.show()
        
    def stopFit(self):
        self.fit.fit_abort=True
        self.closeFitInfoDlg()
        
    def closeFitInfoDlg(self):
        self.fitInfoDlg.done(0)
        
    def fitCallback(self,params,iterations,residual,fit_scale):
        self.fitIterLabel.setText('Iteration=%d,\t Chi-sqr=%.5e'%(iterations,np.sum(residual**2)))
        #self.fit.evaluate()
        self.plotWidget.add_data(x=self.fit.x[self.fit.imin:self.fit.imax+1],y=self.fit.yfit,name=self.funcListWidget.currentItem().text(),fit=True)
        QApplication.processEvents()
        pg.QtGui.QApplication.processEvents()
        
        
    def undoFit(self):
        for row in range(self.sfitParamTableWidget.rowCount()):
            key=self.sfitParamTableWidget.item(row,0).text()
            self.sfitParamTableWidget.item(row,1).setText('%.6e'%(self.oldParams[key]))
        if self.fit.params['__mpar__']!={}:
            for row in range(self.mfitParamTableWidget.rowCount()):
                for col in range(self.mfitParamTableWidget.columnCount()):
                    parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                    key='__%s__%03d'%(parkey,row)
                    self.mfitParamTableWidget.item(row,col).setText('%.6e'%(self.oldmpar[parkey][row]))
            self.mfitParamData=copy.copy(self.oldmpar)
        self.update_plot()                    

        
        
    def addData(self,fnames=None):
        """
        fnames        :List of filenames
        """
        if self.dataListWidget.count()==0:
            self.fileNumber=0
        self.dataListWidget.itemSelectionChanged.disconnect(self.dataFileSelectionChanged)
        #try:
        if fnames is None:
            fnames,_=QFileDialog.getOpenFileNames(self,caption='Open data files',directory=self.curDir,filter='Data files (*.txt *.dat *.chi *.rrf)')
        if len(fnames)!=0:
            self.curDir=os.path.dirname(fnames[0])
            for fname in fnames:
                if fname not in self.data.keys():
                    data_dlg=Data_Dialog(fname=fname,parent=self)
                    data_dlg.accept()
                    self.dlg_data[fname]=data_dlg.data
                    self.plotColIndex[fname]=data_dlg.plotColIndex
                    self.data[fname]=data_dlg.externalData
                    self.plotWidget.add_data(self.data[fname]['x'],self.data[fname]['y'],yerr=self.data[fname]['yerr'],name='%d'%self.fileNumber)
                    self.dataListWidget.addItem(str(self.fileNumber)+'<>'+fname)
                    self.fileNames[self.fileNumber]=fname
                    self.fileNumber+=1
                else:
                    QMessageBox.warning(self,'Import Error','Data file has been imported before. Please remove the data file before importing again')
            #except:
            #    QMessageBox.warning(self,'File error','The file(s) do(es) not look like a data file. Please format it in x,y[,yerr] column format',QMessageBox.Ok)
        self.dataListWidget.itemSelectionChanged.connect(self.dataFileSelectionChanged)
                
                
        
    def removeData(self):
        """
        """
        self.dataListWidget.itemSelectionChanged.disconnect(self.dataFileSelectionChanged)
        for item in self.dataListWidget.selectedItems():
            fnum,fname=item.text().split('<>')
            self.dataListWidget.takeItem(self.dataListWidget.row(item))
            self.plotWidget.remove_data([fnum])
            del self.data[fname]
            del self.plotColIndex[fname]
            del self.dlg_data[fname]
            
        self.dataFileSelectionChanged()
        self.dataListWidget.itemSelectionChanged.connect(self.dataFileSelectionChanged)
            
        
        
    def create_paramDock(self):
        self.parSplitter=QSplitter(Qt.Vertical)
                
        self.fixedparamLayoutWidget=pg.LayoutWidget(self)
        
        xlabel=QLabel('x')
        self.fixedparamLayoutWidget.addWidget(xlabel)
        self.xLineEdit=QLineEdit('np.linspace(0.001,1,100)')
        self.fixedparamLayoutWidget.addWidget(self.xLineEdit,col=1)
        
        self.fixedparamLayoutWidget.nextRow()
        fixedParamLabel=QLabel('Fixed Parameters')
        self.fixedparamLayoutWidget.addWidget(fixedParamLabel,colspan=2)
        
        self.fixedparamLayoutWidget.nextRow()
        self.fixedParamTableWidget=pg.TableWidget()
        self.fixedParamTableWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.fixedParamTableWidget.setEditable(editable=True)
        self.fixedParamTableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.fixedparamLayoutWidget.addWidget(self.fixedParamTableWidget,colspan=2)
        
        self.parSplitter.addWidget(self.fixedparamLayoutWidget)
        
        self.sfitparamLayoutWidget=pg.LayoutWidget()
        sfitParamLabel=QLabel('Single fitting parameters')
        self.sfitparamLayoutWidget.addWidget(sfitParamLabel,colspan=2)
        
        self.sfitparamLayoutWidget.nextRow()
        self.sfitParamTableWidget=pg.TableWidget()
        self.sfitParamTableWidget.setEditable(editable=True)
        self.sfitParamTableWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.sfitParamTableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        #self.sfitParamTableWidget.cellDoubleClicked.connect(self.editFitParam)
        self.sfitparamLayoutWidget.addWidget(self.sfitParamTableWidget,colspan=2)
        
        self.parSplitter.addWidget(self.sfitparamLayoutWidget)
        
        self.mfitparamLayoutWidget=pg.LayoutWidget()
        mfitParamLabel=QLabel('Mutiple fitting parameters')
        self.mfitparamLayoutWidget.addWidget(mfitParamLabel,col=0)
        self.add_mpar_button=QPushButton('Add')
        self.add_mpar_button.clicked.connect(self.add_mpar)
        self.add_mpar_button.setDisabled(True)
        self.mfitparamLayoutWidget.addWidget(self.add_mpar_button,col=1)
        self.remove_mpar_button=QPushButton('Remove')
        self.mfitparamLayoutWidget.addWidget(self.remove_mpar_button,col=2)      
        self.remove_mpar_button.clicked.connect(self.remove_mpar)
        self.remove_mpar_button.setDisabled(True)
        
        self.mfitparamLayoutWidget.nextRow()
        self.mfitParamTableWidget=pg.TableWidget(sortable=False)
        self.mfitParamTableWidget.cellDoubleClicked.connect(self.mparDoubleClicked)
        self.mfitParamTableWidget.setEditable(editable=True)
        self.mfitParamTableWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.mfitParamTableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        #self.sfitParamTableWidget.cellDoubleClicked.connect(self.editFitParam)
        self.mfitparamLayoutWidget.addWidget(self.mfitParamTableWidget,colspan=3)        
        
        self.mfitparamLayoutWidget.nextRow()
        self.saveParamButton=QPushButton('Save Parameters')
        self.saveParamButton.clicked.connect(self.saveParameters)
        self.mfitparamLayoutWidget.addWidget(self.saveParamButton,col=1)
        self.loadParamButton=QPushButton('Load Parameters')
        self.loadParamButton.clicked.connect(self.loadParameters)
        self.mfitparamLayoutWidget.addWidget(self.loadParamButton,col=2)
        
        self.parSplitter.addWidget(self.mfitparamLayoutWidget)       
        
        self.genparamLayoutWidget=pg.LayoutWidget()
        genParameters=QLabel('Generated Parameters')
        self.genparamLayoutWidget.addWidget(genParameters,colspan=2)
        
        self.genparamLayoutWidget.nextRow()
        self.genParamListWidget=QListWidget()
        self.genParamListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.genParamListWidget.itemSelectionChanged.connect(self.plot_extra_param)
        #self.genParamListWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.genparamLayoutWidget.addWidget(self.genParamListWidget,colspan=2)
        
        self.genparamLayoutWidget.nextRow()
        self.saveGenParamButton=QPushButton('Save Generated Parameters')
        self.saveGenParamButton.clicked.connect(self.saveGenParameters)
        self.genparamLayoutWidget.addWidget(self.saveGenParamButton,colspan=2)
        
        self.parSplitter.addWidget(self.genparamLayoutWidget)
        
        self.paramDock.addWidget(self.parSplitter)
        
    def mparDoubleClicked(self,row,col):
        parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
        key='__%s__%03d'%(parkey,row)
        value=self.fit.fit_params[key].value
        minimum=self.fit.fit_params[key].min
        maximum=self.fit.fit_params[key].max
        expr=self.fit.fit_params[key].expr
        brute_step=self.fit.fit_params[key].brute_step
        dlg=minMaxDialog(value,minimum=minimum,maximum=maximum,expr=expr,brute_step=brute_step)
        if dlg.exec_():
            value,maximum,minimum,expr,brute_step=(dlg.value,dlg.maximum,dlg.minimum,dlg.expr,dlg.brute_step)
        self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        self.mfitParamTableWidget.item(row,col).setText(str(value))
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
        self.mfitParamData[parkey][row]=value
        self.fit.fit_params[key].min=minimum
        self.fit.fit_params[key].max=maximum
        if expr!='None':
            self.fit.fit_params[key].expr=expr
        self.fit.fit_params[key].brute_step=brute_step
        self.fit.fit_params[key].value=value
        self.update_plot()

        
        
    def add_mpar(self):
        self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        try:
            curRow=self.mfitParamTableWidget.currentRow()
            #if curRow!=0:
            self.mfitParamTableWidget.insertRow(curRow)
            self.mfitParamTableWidget.setRow(curRow,self.mfitParamData[curRow])
            self.mfitParamData=np.insert(self.mfitParamData,curRow,self.mfitParamData[curRow],0)
                
            for col in range(self.mfitParamTableWidget.columnCount()):
                parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                for row in range(curRow+1,self.mfitParamTableWidget.rowCount()):
                    key='__%s__%03d'%(parkey,row)
                    if key in self.fit.fit_params.keys():
                        self.fit.fit_params[key].value=self.mfitParamData[row][col]
                    else:
                        self.fit.fit_params.add(key,value=self.mfitParamData[row][col],vary=0)
                self.fit.params['__mpar__'][parkey].insert(curRow,self.mfitParamData[curRow][col])
                #This is to make the newly inserted row chekable
                item=self.mfitParamTableWidget.item(curRow,col)
                item.setFlags(Qt.ItemIsUserCheckable|Qt.ItemIsEnabled|Qt.ItemIsEditable|Qt.ItemIsSelectable)
                item.setCheckState(Qt.Unchecked)
            self.update_plot()
            self.remove_mpar_button.setEnabled(True)
        except:
            QMessageBox.warning(self,'Warning','Please select a row at which you would like to add a set of parameters',QMessageBox.Ok)
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
            
    def remove_mpar(self):
        selrows=list(set([item.row() for item in self.mfitParamTableWidget.selectedItems()]))
        num=self.mfitParamTableWidget.rowCount()-len(selrows)
        if num<self.mpar_N:
            QMessageBox.warning(self,'Selection error','The minimum number of rows required for this function to work is %d. You can only remove %d rows'%(self.mpar_N,num),QMessageBox.Ok)
            return
        self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        if selrows!=[]:
            selrows.sort(reverse=True)
            for row in selrows:
                maxrow=self.mfitParamTableWidget.rowCount()
                for trow in range(row,maxrow-1):
                    for col in range(self.mfitParamTableWidget.columnCount()):
                        parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                        if trow<maxrow-1:
                            key1='__%s__%03d'%(parkey,trow)
                            key2='__%s__%03d'%(parkey,trow+1)
                            self.fit.fit_params[key1]=copy.copy(self.fit.fit_params[key2])
                            del self.fit.params['__mpar__'][parkey][row]
                            del self.fit.fit_params[key2]
                        else:
                            key1='__%s__%03d'%(parkey,trow)
                            del self.fit.params['__mpar__'][parkey][row]
                            del self.fit.fit_params[key1]
                self.mfitParamTableWidget.removeRow(row)
                self.mfitParamData=np.delete(self.mfitParamData,row)
        else:
            QMessageBox.warning(self,'Nothing selected','No item is selected for removal',QMessageBox.Ok)
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
        self.update_plot()
        if self.mfitParamTableWidget.rowCount()==self.mpar_N:
            self.remove_mpar_button.setDisabled(True)
            
        
    def saveGenParameters(self):
        if len(self.genParamListWidget.selectedItems())==1:
            text=self.genParamListWidget.selectedItems()[0].text()
            name,var=text.split(':')
            fname=QFileDialog.getSaveFileName(self,'Save generated data as',self.curDir,'Text files (*.txt)')[0]
            if fname!='':
                if fname[-4:]!='.txt':
                    fname=fname+'.txt'
                header='Generated output file on %s\n'%time.asctime()
                if var=="['x', 'y']":
                    header+='x\ty\n'
                    res=np.vstack((self.fit.params['output_params'][name]['x'], self.fit.params['output_params'][name]['y'])).T
                    np.savetxt(fname,res,header=header,comments='#')
                elif var=="['x', 'y', 'z']":
                    res=[]
                    header+='x\ty\tz\n'
                    for i in range(self.fit.params['output_params'][name]['x'].shape[1]):
                        for j in range(self.fit.params['output_params'][name]['x'].shape[0]):
                            res.append([self.fit.params['output_params'][name][t][i,j] for t in ['x','y','z']])
                    res=np.array(res)
                    np.savetxt(fname,res,header=header,comments='#')
                else:
                    QMessageBox.warning(self,'Format error','The data is in some different format and couldnot be saved.',QMessageBox.Ok)
        else:
            QMessageBox.warning(self,'Selection Error','Please select a single generated data to be saved.',QMessageBox.Ok)
        
        
    def saveParameters(self):
        """
        Saves all the fixed and fitted parameteres in a file
        """
        fname,_=QFileDialog.getSaveFileName(self,caption='Save parameters as',directory=self.curDir,filter='Parameter files (*.par)')
        if fname!='':
            if fname[-4:]!='.par':
                fname=fname+'.par'
            fh=open(fname,'w')
            fh.write('#File saved on %s\n'%time.asctime())
            fh.write('#Category: %s\n'%self.categoryListWidget.currentItem().text())
            fh.write('#Function: %s\n'%self.funcListWidget.currentItem().text())
            fh.write('#Fixed Parameters:\n')
            fh.write('#param\tvalue\n')
            for row in range(self.fixedParamTableWidget.rowCount()):
                fh.write(self.fixedParamTableWidget.item(row,0).text()+'\t'+self.fixedParamTableWidget.item(row,1).text()+'\n')
            fh.write('#Single fitting parameters:\n')
            fh.write('#param\tvalue\tfit\tmin\tmax\texpr\tbrute_step\n')
            for row in range(self.sfitParamTableWidget.rowCount()):
                parname=self.sfitParamTableWidget.item(row,0).text()
                par=self.sfitParamTableWidget.item(row,1)
                parval=par.text()
                if par.checkState()==Qt.Checked:
                    parfit='1'
                else:
                    parfit='0'
                parmin=self.sfitParamTableWidget.item(row,2).text()
                parmax=self.sfitParamTableWidget.item(row,3).text()
                parexpr=self.sfitParamTableWidget.item(row,4).text()
                parbrute=self.sfitParamTableWidget.item(row,5).text()
                fh.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\n'%(parname,parval,parfit,parmin,parmax,parexpr,parbrute))
            if self.fit.params['__mpar__']!={}:
                fh.write('#Multiple fitting parameters:\n')
                fh.write('#param\tvalue\tfit\tmin\tmax\texpr\tbrute_step\n')
                for col in range(self.mfitParamTableWidget.columnCount()):
                    parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                    for row in range(self.mfitParamTableWidget.rowCount()):
                        parname='__%s__%03d'%(parkey,row)
                        par=self.mfitParamTableWidget.item(row,col)
                        parval=par.text()
                        if par.checkState()==Qt.Checked:
                            parfit='1'
                        else:
                            parfit='0'
                        parmin=str(self.fit.fit_params[parname].min)
                        parmax=str(self.fit.fit_params[parname].max)
                        parexpr=str(self.fit.fit_params[parname].expr)
                        parbrute=str(self.fit.fit_params[parname].brute_step)
                        fh.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\n'%(parname,parval,parfit,parmin,parmax,parexpr,parbrute))
            fh.close()
        
        
    def loadParameters(self):
        """
        loads parameters from a parameter file
        """
        fname,_=QFileDialog.getOpenFileName(self,caption='Open parameter file',directory=self.curDir,filter='Parameter files (*.par)')
        if fname!='':
            fh=open(fname,'r')
            lines=fh.readlines()
            func=lines[2].split(': ')[1].strip()
            if func==self.funcListWidget.currentItem().text():
                lnum=3
                sfline=None
                mfline=None
                for line in lines[3:]:
                    if line=='#Fixed Parameters:\n':
                        fline=lnum+2                        
                    elif line=='#Single fitting parameters:\n':
                        sfline=lnum+2
                    elif line=='#Multiple fitting parameters:\n':
                        mfline=lnum+2
                    lnum+=1
                if sfline is None:
                    sendnum=lnum
                else:
                    sendnum=sfline-2
                if mfline is None:
                    mendnum=lnum
                else:
                    mendnum=mfline-2
                for line in lines[fline:sendnum]:
                    key,val=line.strip().split('\t')
                    try:
                        val=eval(val.strip())
                    except:
                        val=val.strip()
                    self.fit.params[key]=val
                if sfline is not None:
                    for line in lines[sfline:mendnum]:
                        parname,parval,parfit,parmin,parmax,parexpr,parbrute=line.strip().split('\t')
                        self.fit.params[parname]=float(parval)
                        self.fit.fit_params[parname].value=float(parval)
                        self.fit.fit_params[parname].fit=int(parfit)
                        self.fit.fit_params[parname].min=float(parmin)
                        self.fit.fit_params[parname].max=float(parmax)
                        try:
                            self.fit.fit_params[parname].expr=eval(parexpr)
                        except:
                            self.fit.fit_params[parname].expr=str(parexpr)
                        try:
                            self.fit.fit_params[parname].brute_step=eval(parbrute)
                        except:
                            self.fit.fit_params[parname].brute_step=str(parbrute)

                if mfline is not None:
                    for line in lines[mfline:]:
                        parname,parval,parfit,parmin,parmax,parexpr,parbrute=line.strip().split('\t')
                        try:
                            expr=eval(parexpr)
                        except:
                            expr=str(parexpr)
                        try:
                            brute_step=eval(parbrute)
                        except:
                            brute_step=str(parbrute)
                        try:
                            self.fit.fit_params[parname].value=float(parval)
                            self.fit.fit_params[parname].vary=int(parfit)
                            self.fit.fit_params[parname].min=float(parmin)
                            self.fit.fit_params[parname].max=float(parmax)
                            self.fit.fit_params[parname].expr=expr
                            self.fit.fit_params[parname].brute_step=brute_step
                        except:
                            self.fit.fit_params.add(parname,value=float(parval),vary=int(parfit),min=float(parmin),max=float(parmax),expr=expr,brute_step=brute_step)
                        _,par,num=parname.split('__')
                        num=int(num)
                        try:
                            self.fit.params['__mpar__'][par][num]=float(parval)
                        except:
                            self.fit.params['__mpar__'][par].insert(num,float(parval))
                try:
                    self.fixedParamTableWidget.cellChanged.disconnect(self.fixedParamChanged)
                    self.sfitParamTableWidget.cellChanged.disconnect(self.fitParamChanged)
                    self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
                except:
                    pass
                self.update_fixed_parameters()
                self.update_fit_parameters()
                self.fixedParamTableWidget.cellChanged.connect(self.fixedParamChanged)
                self.sfitParamTableWidget.cellChanged.connect(self.fitParamChanged)
                self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
                self.update_plot()
            else:
                QMessageBox.warning(self,'File error','This parameter file doesnot belong to function: %s'% func,QMessageBox.Ok)
        
    def create_plotDock(self):
        self.plotSplitter=QSplitter(Qt.Vertical)
        #self.plotLayoutWidget=pg.LayoutWidget(self)
        self.plotWidget=PlotWidget()
        self.plotWidget.setXLabel('X',fontsize=5)
        self.plotWidget.setYLabel('Y',fontsize=5)
        self.plotSplitter.addWidget(self.plotWidget)
        self.extra_param_1DplotWidget=PlotWidget()
        self.extra_param_1DplotWidget.setXLabel('X',fontsize=5)
        self.extra_param_1DplotWidget.setYLabel('Y',fontsize=5)
        self.plotSplitter.addWidget(self.extra_param_1DplotWidget)
        
        self.plotDock.addWidget(self.plotSplitter)
        
    def update_catagories(self):
        """
        Reads all the modules in the the Functions directory and populates the funcListWidget
        """
        self.categoryListWidget.clear()
        self.categories=sorted([path for path in os.listdir('./Functions/') if path[:2]!='__' and os.path.isdir('./Functions/'+path)])
        #self.catagories=sorted([m.split('.')[0] for m in modules if m[:2]!='__'],key=str.lower)
        self.categoryListWidget.addItems(self.categories)
        
    def update_functions(self):
        """
        Depending upon the selected category this populates the funcListWidget
        """
        self.funcListWidget.clear()
        self.curr_category=self.categoryListWidget.currentItem().text()
        self.modules=[]
        for module in os.listdir('./Functions/'+self.curr_category):
            if module!='__init__.py' and module[-2:]=='py':
                self.modules.append(module[:-3])
        self.modules=sorted(self.modules,key=str.lower)
        self.funcListWidget.addItems(self.modules)
        for i in range(self.funcListWidget.count()):
            mname=self.funcListWidget.item(i).text()
            module='Functions.%s.%s'%(self.curr_category,mname)
            if module not in sys.modules:
                self.curr_funcClass[module]=import_module(module)
            else:
                self.curr_funcClass[module]=reload(self.curr_funcClass[module])
            self.funcListWidget.item(i).setToolTip(getattr(self.curr_funcClass[module],self.funcListWidget.item(i).text()).__init__.__doc__)
        
    def functionChanged(self):
        self.curr_module=self.funcListWidget.currentItem().text()
        module='Functions.%s.%s'%(self.curr_category,self.curr_module)
        try:
            if module not in sys.modules:
                self.curr_funcClass[module]=import_module(module)
            else:
                self.curr_funcClass[module]=reload(self.curr_funcClass[module])
            self.fchanged = True
            self.update_parameters()
        except:
            QMessageBox.warning(self,'Function Error','Some syntax error in the function still exists.',QMessageBox.Ok)
        
    def update_parameters(self):
        """
        Depending upon the selection of the function this updates the reloads the parameters required for the function
        """
        try:
            self.fixedParamTableWidget.cellChanged.disconnect(self.fixedParamChanged)
            self.sfitParamTableWidget.cellChanged.disconnect(self.fitParamChanged)
            self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        except:
            pass
        self.x=eval(self.xLineEdit.text())
        self.curr_module=self.funcListWidget.currentItem().text()
        module='Functions.%s.%s'%(self.curr_category,self.curr_module)
        self.fit=Fit(getattr(self.curr_funcClass[module],self.funcListWidget.currentItem().text()),self.x)
        self.update_fixed_parameters()
        self.update_fit_parameters()
        self.update_plot()
        self.xLineEdit.returnPressed.connect(self.xChanged)
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
        self.fixedParamTableWidget.cellChanged.connect(self.fixedParamChanged)
        self.sfitParamTableWidget.cellChanged.connect(self.fitParamChanged)

    def update_fixed_parameters(self):
        fpdata=[]        
        for key in self.fit.params.keys():
            if key not in self.fit.fit_params.keys() and key not in self.special_keys and key[:2]!='__':
                fpdata.append((key,str(self.fit.params[key])))
        self.fixedParamData=np.array(fpdata,dtype=[('Params',object),('Value',object)])
        self.fixedParamTableWidget.setData(self.fixedParamData)
        for row in range(self.fixedParamTableWidget.rowCount()):
            self.fixedParamTableWidget.item(row,0).setFlags(Qt.ItemIsEnabled)
        self.fixedParamTableWidget.resizeRowsToContents()
        self.fixedParamTableWidget.resizeColumnsToContents()
                
    def update_fit_parameters(self):
        self.update_sfit_parameters()
        self.update_mfit_parameters()
        
    def update_sfit_parameters(self):
        tpdata=[]
        for key in self.fit.fit_params.keys():
            if key[:2]!='__':
                tpdata.append((key,self.fit.fit_params[key].value,self.fit.fit_params[key].min,self.fit.fit_params[key].max,self.fit.fit_params[key].expr,self.fit.fit_params[key].brute_step))        
        self.fitParamData=np.array(tpdata,dtype=[('Params',object),('Value',object),('Min',object),('Max',object),('Expr',object),('Brute step',object)])
        self.sfitParamTableWidget.setData(self.fitParamData)
        for row in range(self.sfitParamTableWidget.rowCount()):
            self.sfitParamTableWidget.item(row,0).setFlags(Qt.ItemIsEnabled)
            par=self.sfitParamTableWidget.item(row,0).text()
            item=self.sfitParamTableWidget.item(row,1)
            item.setFlags(Qt.ItemIsUserCheckable|Qt.ItemIsEnabled|Qt.ItemIsEditable|Qt.ItemIsSelectable)
            if self.fit.fit_params[par].vary==0:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
        self.sfitParamTableWidget.resizeRowsToContents()
        self.sfitParamTableWidget.resizeColumnsToContents()
        
    def update_mfit_parameters(self):
        if '__mpar__' in self.fit.params.keys() and self.fit.params['__mpar__']!={}:
            self.mpar_keys=list(self.fit.params['__mpar__'].keys())
            self.mpar_N=len(self.fit.params['__mpar__'][self.mpar_keys[0]])
            tpdata=[]
            for i in range(self.mpar_N):
                tpdata.append(tuple([self.fit.fit_params['__%s__%03d'%(key,i)].value for key in self.mpar_keys]))
            self.mfitParamData=np.array(tpdata,dtype=[(key,object) for key in self.mpar_keys])
            self.mfitParamTableWidget.setData(self.mfitParamData)
            self.add_mpar_button.setEnabled(True)
            #self.remove_mpar_button.setEnabled(True)
            for row in range(self.mfitParamTableWidget.rowCount()):
                for col in range(self.mfitParamTableWidget.columnCount()):
                    item=self.mfitParamTableWidget.item(row,col)
                    item.setFlags(Qt.ItemIsUserCheckable|Qt.ItemIsEnabled|Qt.ItemIsEditable|Qt.ItemIsSelectable)
                    item.setCheckState(Qt.Unchecked)
            self.mfitParamTableWidget.resizeRowsToContents()
            self.mfitParamTableWidget.resizeColumnsToContents()
        else:
            self.add_mpar_button.setDisabled(True)
            self.remove_mpar_button.setDisabled(True)
            self.mfitParamTableWidget.setData([])
        
    def fixedParamChanged(self,row,col):
        txt=self.fixedParamTableWidget.item(row,0).text()
        try:
            val=eval(self.fixedParamTableWidget.item(row,col).text())
        except:
            val=self.fixedParamTableWidget.item(row,col).text()
        try:
            oldVal=self.fit.params[txt]
            self.fit.params[txt]=val
            self.fchanged=False
            self.update_plot()
        except:
            QMessageBox.warning(self,'Value Error','The value just entered is not seem to be right',QMessageBox.Ok)
            self.fixedParamTableWidget.item(row,col).setText(str(oldVal))
        self.fixedParamTableWidget.resizeRowsToContents()
        self.fixedParamTableWidget.resizeColumnsToContents()

            
        
        
    def fitParamChanged(self,row,col):
        txt=self.sfitParamTableWidget.item(row,0).text()
        try:
            val=float(self.sfitParamTableWidget.item(row,col).text())
        except:
            val=self.sfitParamTableWidget.item(row,col).text()
        if col==1:
            oldVal=self.fit.params[txt]
        elif col==2:
            oldVal=self.fit.fit_params[txt].min
        elif col==3:
            oldVal=self.fit.fit_params[txt].vary
        elif col==4:
            oldVal=self.fit.fit_params[txt].expr
        elif col==5:
            oldVal=self.fit.fit_params[txt].brute_step
        if isinstance(val,numbers.Number):
            if col==1:
                self.fit.params[txt]=val
                self.fchanged=False
                self.update_plot()
            elif col==2:
                self.fit.fit_params[txt].min=val
            elif col==3:
                self.fit.fit_params[txt].max=val
            elif col==5:
                self.fit.fit_params[txt].brute_step=val
        elif isinstance(val,str):
            if col==4:
                self.fit.fit_params[txt].expr=val
        else:
            QMessageBox.warning(self,'Value Error','Please input numbers only',QMessageBox.Ok)
            self.sfitParamTableWidget.item(row,col).setText(str(oldVal))
        if self.sfitParamTableWidget.item(row,1).checkState()==Qt.Checked:
            self.fit.fit_params[txt].vary=1
        else:
            self.fit.fit_params[txt].vary=0
        self.sfitParamTableWidget.resizeRowsToContents()
        self.sfitParamTableWidget.resizeColumnsToContents()
        
    def mfitParamChanged(self,row,col):
        parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
        txt=self.mfitParamTableWidget.item(row,col).text()
        try:
            key='__%s__%03d'%(parkey,row)
            oldval=self.fit.fit_params[key].value
            self.fit.fit_params[key].value=float(txt)
            if self.mfitParamTableWidget.item(row,col).checkState()==Qt.Checked:
                self.fit.fit_params[key].vary=1
            else:
                self.fit.fit_params[key].vary=0
            self.mfitParamData[row][col]=float(txt)
            self.fchanged=False
            self.update_plot()
        except:
            QMessageBox.warning(self,'Value Error','Please input numbers only',QMessageBox.Ok)
            self.mfitParamTableWidget.item(row,col).setText(str(oldval))
        self.mfitParamTableWidget.resizeRowsToContents()
        self.mfitParamTableWidget.resizeColumnsToContents() 
        
            
    def xChanged(self):
        #try:
            x=eval(self.xLineEdit.text())
            try:
                self.fit.params['x']=x
                self.fit.x=x
                self.fit.imin=0
                self.fit.imax=len(self.fit.x)
            except:
                pass
            self.fchanged=False
            self.update_plot()
        #except:
        #    QMessageBox.warning(self,'Value Error','The value just entered is not seem to be right',QMessageBox.Ok)
        #    self.xLineEdit.setText('np.linspace(0.001,0.1,100)')
            
        
    def update_plot(self):
        for row in range(self.fixedParamTableWidget.rowCount()):
            txt=self.fixedParamTableWidget.item(row,0).text()
            val=self.fixedParamTableWidget.item(row,1).text()
            try:
                self.fit.params[txt]=eval(val)
            except:
                self.fit.params[txt]=str(val)
        for row in range(self.sfitParamTableWidget.rowCount()):
            txt=self.sfitParamTableWidget.item(row,0).text()
            self.fit.params[txt]=float(self.sfitParamTableWidget.item(row,1).text())
            self.fit.fit_params[txt].value=float(self.sfitParamTableWidget.item(row,1).text())
        for row in range(self.mfitParamTableWidget.rowCount()):
            for col in range(self.mfitParamTableWidget.columnCount()):
                parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                txt=self.mfitParamTableWidget.item(row,col).text()
                self.fit.fit_params['__%s__%03d'%(parkey,row)].value=float(txt)
        try:
            pfnames=copy.copy(self.pfnames)
        except:
            pfnames=[]
        if len(self.funcListWidget.selectedItems())>0:
            #try:
            self.fit.evaluate()
            #except:
            #    QMessageBox.warning(self,'Value error','Something wrong with the value of the parameters which you just entered',QMessageBox.Ok)
            #    return
            self.gen_rows=[self.genParamListWidget.row(item) for item in self.genParamListWidget.selectedItems()]
            self.genParamListWidget.itemSelectionChanged.disconnect(self.plot_extra_param)
            self.genParamListWidget.clear()
            if len(self.fit.params['output_params'])>0:
                for key in self.fit.params['output_params'].keys():
                    self.genParamListWidget.addItem(str(key)+':'+str(list(self.fit.params['output_params'][key].keys())))
            if not self.fchanged:
                for row in self.gen_rows:
                    self.genParamListWidget.item(row).setSelected(True)
                self.plot_extra_param()
            self.genParamListWidget.itemSelectionChanged.connect(self.plot_extra_param)
            self.plotWidget.add_data(x=self.fit.x[self.fit.imin:self.fit.imax+1],y=self.fit.yfit,name=self.funcListWidget.currentItem().text(),fit=True)
            pfnames=pfnames+[self.funcListWidget.currentItem().text()]
        #except:
        #    pass
        self.plotWidget.Plot(pfnames)
        pg.QtGui.QApplication.processEvents()
        
        
    def plot_extra_param(self):
        """
        """
        fdata=[]
        for item in self.genParamListWidget.selectedItems():
            txt,axes=item.text().split(':')
            axes=eval(axes)
            if len(axes)==2:
                x=self.fit.params['output_params'][txt][axes[0]]
                y=self.fit.params['output_params'][txt][axes[1]]
                self.extra_param_1DplotWidget.add_data(x=x,y=y,name=txt,fit=True)
                fdata.append(txt)
    #            pg.plot(self.fit.params['output_params'][txt][axes[0]],self.fit.params['output_params'][txt][axes[1]],title=txt,left=axes[1],bottom=axes[0])
            #else:
            #    QMessageBox.information(self,'Info','Plotting 3d data is not available now!',QMessageBox.Ok)
                #X,Y=self.fit.params['output_params'][txt][axes[0]],self.fit.params['output_params'][txt][axes[1]]
                #scale=np.abs(X[0,1]-X[0,0]),np.abs(Y[1,0]-Y[0,0])
                #pg.image(self.fit.params['output_params'][txt][axes[-1]],scale=scale)
        self.extra_param_1DplotWidget.Plot(fdata)
        pg.QtGui.QApplication.processEvents()

        
        
        
if __name__=='__main__':
    app=QApplication(sys.argv)
    w=Fit_Widget()
    w.setWindowTitle('Fit Widget')
    w.setGeometry(100,100,1000,800)
    
    w.show()
    sys.exit(app.exec_())
        
        
        
    

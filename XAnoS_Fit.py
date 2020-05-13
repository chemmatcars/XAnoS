from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QCheckBox,\
    QSpinBox, QComboBox, QListWidget, QDialog, QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem,\
    QAbstractItemView, QSpinBox, QSplitter, QSizePolicy, QAbstractScrollArea, QHBoxLayout, QTextEdit, QShortcut,\
    QProgressDialog, QDesktopWidget
from PyQt5.QtGui import QPalette, QKeySequence, QFont, QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt, QThread
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
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
from tabulate import tabulate
import lmfit, corner
import numbers
import time, datetime
import shutil
from FunctionEditor import FunctionEditor
from lmfit import conf_interval, printfuncs
from MultiInputDialog import MultiInputDialog
import traceback

class minMaxDialog(QDialog):
    def __init__(self,value,vary=False, minimum=None,maximum=None,expr=None,brute_step=None,parent=None):
        QDialog.__init__(self,parent)
        self.value=value
        self.vary = vary
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
        
        valueLabel=QLabel('Value')
        self.layoutWidget.addWidget(valueLabel)
        self.layoutWidget.nextColumn()
        self.valueLineEdit=QLineEdit(str(self.value))
        self.layoutWidget.addWidget(self.valueLineEdit)

        self.layoutWidget.nextRow()
        varyLabel=QLabel('Fit')
        self.layoutWidget.addWidget(varyLabel)
        self.layoutWidget.nextColumn()
        self.varyCheckBox=QCheckBox()
        self.layoutWidget.addWidget(self.varyCheckBox)
        if self.vary:
            self.varyCheckBox.setCheckState(Qt.Checked)
        else:
            self.varyCheckBox.setCheckState(Qt.Unchecked)

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
            if self.varyCheckBox.checkState() == Qt.Checked:
                self.vary=True
            else:
                self.vary=False
            self.minimum=float(self.minimumLineEdit.text())
            self.maximum=float(self.maximumLineEdit.text())
            self.expr=self.exprLineEdit.text()
            if self.bruteStepLineEdit.text()!='None':
                self.brute_step=float(self.bruteStepLineEdit.text())
            else:
                self.brute_step=None
            self.accept()
        except:
            QMessageBox.warning(self,'Value Error','Value, Min, Max should be floating point numbers\n\n'+traceback.format_exc(),QMessageBox.Ok)

    def cancelandClose(self):
        self.reject()

class FitResultDialog(QDialog):
    def __init__(self,fit_report,fit_info,parent=None):
        QDialog.__init__(self,parent)
        self.setWindowTitle('Fit Results')
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


class XAnoS_Fit(QWidget):
    """
    This widget class is developed to provide an end-user a *Graphical User Interface* by which either they can \
    develop their own fitting functions in python or use the existing fitting functions under different categories\
     to analyze different kinds of one-dimensional data sets. `LMFIT <https://lmfit.github.io/lmfit-py/>`_ is extensively\
      used within this widget.
    
    **Features**
    
    1. Read and fit multiple data files
    2. Already available functions are categorized as per the function types and techniques
    3. Easy to add more catergories and user-defined functions
    4. Once the function is defined properly all the free and fitting parameters will be available within the GUI as tables.
    5. An in-built Function editor with a function template is provided.
    6. The function editor is enabled with python syntax highlighting.
    
    **Usage**
    
    :class:`Fit_Widget` can be used as stand-alone python fitting package by running it in terminal as::
    
        $python XAnoS_Fit.py
        
    .. figure:: Figures/Fit_widget.png
       :figwidth: 100%
       
       **Fit Widget** in action.
    
    Also it can be used as a widget with any other python application.
    """
    
    def __init__(self,parent=None):
        
        QWidget.__init__(self,parent)
               
        self.vblayout=QVBoxLayout(self)
        self.mainDock=DockArea(self,parent)
        self.vblayout.addWidget(self.mainDock)
        
        self.funcDock=Dock('Functions',size=(1,6),closable=False)
        self.fitDock=Dock('Fit options',size=(1,2),closable=False)
        self.dataDock=Dock('Data',size=(1,8),closable=False)
        self.paramDock=Dock('Parameters',size=(2,8),closable=False)
        self.plotDock=Dock('Data and Fit',size=(5,8),closable=False)
        self.mainDock.addDock(self.dataDock)
        self.mainDock.addDock(self.fitDock,'bottom')
        self.mainDock.addDock(self.paramDock,'right')
        self.mainDock.addDock(self.plotDock,'right')
        self.mainDock.addDock(self.funcDock,'above',self.dataDock)
        self.special_keys=['x','params','choices','output_params','__mpar__']
        self.curr_funcClass={}
        
        
        self.data={}
        self.dlg_data={}
        self.plotColIndex={}
        self.plotColors={}
        self.curDir=os.getcwd()
        self.fileNumber=0
        self.fileNames={}
        self.fchanged=True
        self.chisqr='None'
        self.gen_param_items=[]
        self.fitMethods={'Levenberg-Marquardt':'leastsq',
                         'Scipy-Least-Squares':'least_squares',
                         'Differential-Evolution': 'differential_evolution',
                         'Brute-Force-Method':'brute',
                         'Nelder-Mead':'nelder',
                         'L-BFGS-B':'lbfgsb',
                         'Powell':'powell',
                         'Congugate-Gradient':'cg',
                         'Newton-CG-Trust-Region':'trust-ncg',
                         'COBLYA':'cobyla',
                         'Truncate-Newton':'tnc',
                         'Exact-Trust-Region':'trust-exact',
                         'Dogleg':'dogleg',
                         'Sequential-Linear-Square':'slsqp',
                         'Adaptive-Memory-Programming':'ampgo',
                         'Maximum-Likelihood-MC-Markov-Chain':'emcee'}
        
        
        self.create_funcDock()
        self.create_fitDock()
        self.create_dataDock()
        self.create_plotDock()
        self.update_catagories()
        self.create_paramDock()
        self.xminmaxChanged()
        self.sfnames=None
        self.expressions={}
        
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
        tdir=QFileDialog.getExistingDirectory(self,'Select a folder','./Functions/',QFileDialog.ShowDirsOnly)
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
            ans=QMessageBox.question(self,'Delete warning','Are you sure you would like to delete the category?',\
                                     QMessageBox.No,QMessageBox.Yes)
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
            ans=QMessageBox.question(self,'Warning','Are you sure you would like to remove the function',\
                                     QMessageBox.No,QMessageBox.Yes)
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
                    QMessageBox.warning(self,'Remove error','Cannot remove the function because the function file\
                     might be open elsewhere.\n\n'+traceback.format_exc(),QMessageBox.Ok)
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
        self.removeDataShortCut = QShortcut(QKeySequence.Delete, self)
        self.removeDataShortCut.activated.connect(self.removeData)
        
        
        self.dataLayoutWidget.nextRow()
        self.dataListWidget=QListWidget()
        self.dataListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.dataListWidget.itemSelectionChanged.connect(self.dataFileSelectionChanged)
        self.dataListWidget.itemDoubleClicked.connect(self.openDataDialog)
        self.dataLayoutWidget.addWidget(self.dataListWidget,colspan=2)
        
        self.dataDock.addWidget(self.dataLayoutWidget)

    def create_fitDock(self):
        self.fitLayoutWidget=pg.LayoutWidget(self)

        xminmaxLabel = QLabel('Xmin:Xmax')
        self.fitLayoutWidget.addWidget(xminmaxLabel)
        self.xminmaxLineEdit = QLineEdit('0:1')
        self.xminmaxLineEdit.returnPressed.connect(self.xminmaxChanged)
        self.fitLayoutWidget.addWidget(self.xminmaxLineEdit, col=1)

        self.fitLayoutWidget.nextRow()
        fitMethodLabel = QLabel('Fit Method')
        self.fitLayoutWidget.addWidget(fitMethodLabel)
        self.fitMethodComboBox = QComboBox()
        self.fitMethodComboBox.addItems(list(self.fitMethods.keys()))
        self.fitLayoutWidget.addWidget(self.fitMethodComboBox, col=1)

        self.fitLayoutWidget.nextRow()
        fitScaleLabel = QLabel('Fit Scale')
        self.fitLayoutWidget.addWidget(fitScaleLabel)
        self.fitScaleComboBox = QComboBox()
        self.fitScaleComboBox.addItems(['Linear', 'Linear w/o error', 'Log', 'Log w/o error'])
        self.fitLayoutWidget.addWidget(self.fitScaleComboBox, col=1)

        self.fitLayoutWidget.nextRow()
        fitIterationLabel = QLabel('Fit Iterations')
        self.fitLayoutWidget.addWidget(fitIterationLabel)
        self.fitIterationLineEdit = QLineEdit('1000')
        self.fitLayoutWidget.addWidget(self.fitIterationLineEdit, col=1)

        self.fitLayoutWidget.nextRow()
        self.fitButton = QPushButton('Fit')
        self.fitButton.clicked.connect(lambda x: self.doFit())
        self.unfitButton = QPushButton('Undo fit')
        self.unfitButton.clicked.connect(self.undoFit)
        self.fitLayoutWidget.addWidget(self.unfitButton)
        self.fitLayoutWidget.addWidget(self.fitButton, col=1)

        self.fitLayoutWidget.nextRow()
        self.showConfIntervalButton = QPushButton('Show Param Error')
        self.showConfIntervalButton.setDisabled(True)
        self.showConfIntervalButton.clicked.connect(self.fitErrorDialog)
        self.calcConfInterButton = QPushButton('Calculate Param Error')
        self.calcConfInterButton.clicked.connect(self.confInterval_emcee)
        # self.calcConfInterButton.setDisabled(True)
        self.fitLayoutWidget.addWidget(self.showConfIntervalButton)
        self.fitLayoutWidget.addWidget(self.calcConfInterButton, col=1)

        self.fitDock.addWidget(self.fitLayoutWidget)


    def dataFileSelectionChanged(self):
        self.sfnames=[]
        self.pfnames=[]
        for item in self.dataListWidget.selectedItems():
            self.sfnames.append(item.text())
            txt=item.text()
            self.pfnames=self.pfnames+[txt.split('<>')[0]+':'+key for key in self.data[txt].keys()]
        if len(self.sfnames)>0:
            self.curDir = os.path.dirname(self.sfnames[-1].split('<>')[1])
            xmin=np.min([np.min([np.min(self.data[key][k1]['x']) for k1 in self.data[key].keys()]) for key in self.sfnames])
            xmax=np.max([np.max([np.max(self.data[key][k1]['x']) for k1 in self.data[key].keys()]) for key in self.sfnames])
            self.xminmaxLineEdit.setText('%0.3f:%0.3f'%(xmin,xmax))
            self.xminmaxChanged()
            if len(self.data[self.sfnames[-1]].keys())>1:
                text='{'
                for key in self.data[self.sfnames[-1]].keys():
                    text+='"'+key+'":np.linspace(%.3f,%.3f,%d),'%(xmin,xmax,100)
                text=text[:-1]+'}'
            else:
                text='np.linspace(%.3f,%.3f,100)'%(xmin,xmax)
            self.xLineEdit.setText(text)
        self.update_plot()
        self.xChanged()
            
    def openDataDialog(self,item):
        fnum,fname=item.text().split('<>')
        data_dlg=Data_Dialog(data=self.dlg_data[item.text()],parent=self,expressions=self.expressions[item.text()],plotIndex=self.plotColIndex[item.text()],colors=self.plotColors[item.text()])
        data_dlg.closePushButton.setText('Cancel')
        data_dlg.tabWidget.setCurrentIndex(1)
        data_dlg.dataFileLineEdit.setText(fname)
        if data_dlg.exec_():
            self.plotWidget.remove_data(datanames=self.pfnames)
            newFname=data_dlg.dataFileLineEdit.text()
            if fname==newFname:
                self.plotColIndex[item.text()]=data_dlg.plotColIndex
                self.plotColors[item.text()]=data_dlg.plotColors
                self.dlg_data[item.text()]=copy.copy(data_dlg.data)
                self.data[item.text()]=copy.copy(data_dlg.externalData)
                self.expressions[item.text()]=data_dlg.expressions
                for key in self.data[item.text()].keys():
                    self.plotWidget.add_data(self.data[item.text()][key]['x'],self.data[item.text()][key]['y'],yerr=self.data[item.text()][key]['yerr'],name='%s:%s'%(fnum,key),color=self.plotColors[item.text()][key])
            else:
                text = '%s<>%s' % (fnum, newFname)
                self.data[text] = self.data.pop(item.text())
                self.dlg_data[text] = self.dlg_data.pop(item.text())
                item.setText(text)
                self.dlg_data[text]=copy.copy(data_dlg.data)
                self.data[text]=copy.copy(data_dlg.externalData)
                self.plotColIndex[text]=data_dlg.plotColIndex
                self.plotColors[text]=data_dlg.plotColors
                self.expressions[text]=data_dlg.expressions
                for key in self.data[text].keys():
                    self.plotWidget.add_data(self.data[text][key]['x'], self.data[text][key]['y'], yerr=self.data[text][key][
                    'yerr'],name='%s:%s'%(fnum,key),color=self.plotColors[text][key])
        # self.sfnames = []
        # self.pfnames = []
        # for item in self.dataListWidget.selectedItems():
        #     self.sfnames.append(item.text())
        #     txt=item.text()
        #     self.pfnames=self.pfnames+[txt.split('<>')[0]+':'+key for key in self.data[txt].keys()]
        self.dataFileSelectionChanged()
        self.xChanged()
        #self.update_plot()

    def xminmaxChanged(self):
        try:
            xmin,xmax=self.xminmaxLineEdit.text().split(':')
            self.xmin, self.xmax=float(xmin),float(xmax)
        except:
            QMessageBox.warning(self,"Value Error", "Please supply the Xrange in this format: xmin:xmax",QMessageBox.Ok)
    


    def doFit(self, fit_method=None, emcee_steps=100, emcee_burn=30):
        if self.sfnames is None or self.sfnames==[]:
            QMessageBox.warning(self,'Data Error','Please select a dataset first before fitting',QMessageBox.Ok)
            return
        try:
            if len(self.fit.fit_params)>0:
                pass
            else:
                QMessageBox.warning(self, 'Fit Warning', 'Please select atleast a single parameter to fit', QMessageBox.Ok)
                return
        except:
            QMessageBox.warning(self, 'Fit Function Warning', 'Please select a function to fit', QMessageBox.Ok)
            return
        try:
            self.sfitParamTableWidget.cellChanged.disconnect(self.sfitParamChanged)
            self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        except:
            QMessageBox.warning(self,'Function Error','Please select a function first to fit.\n'+traceback.format_exc(),QMessageBox.Ok)
            return
        if fit_method is None:
            self.fit_method=self.fitMethods[self.fitMethodComboBox.currentText()]
        else:
            self.fit_method=fit_method
        if self.fit_method not in ['leastsq','brute','differential_evolution','least_squares','emcee']:
            QMessageBox.warning(self,'Fit Method Warning','This method is under development and will be available '
                                                          'soon. Please use only Lavenberg-Marquardt for the time '
                                                          'being.', QMessageBox.Ok)
            return
        self.fit_scale=self.fitScaleComboBox.currentText()
        if self.fit_method!='emcee':
            self.fit.functionCalled.connect(self.fitCallback)
        else:
            self.fit.functionCalled.connect(self.fitErrorCallback)

        for fname in self.sfnames:
            if len(self.data[fname].keys())>1:
                x={}
                y={}
                yerr={}
                for key in self.data[fname].keys():
                    x[key]=self.data[fname][key]['x']
                    y[key]=self.data[fname][key]['y']
                    yerr[key]=self.data[fname][key]['yerr']
            else:
                key=list(self.data[fname].keys())[0]
                x=self.data[fname][key]['x']
                y=self.data[fname][key]['y']
                yerr=self.data[fname][key]['yerr']
                # if len(np.where(self.data[fname][key]['yerr']<1e-30)[0])>0:
                #     QMessageBox.warning(self,'Zero Errorbars','Some or all the errorbars of the selected data are zeros.\
                #      Please select None for the Errorbar column in the Plot options of the Data_Dialog',QMessageBox.Ok)
                #     break
            # if self.fitScaleComboBox.currentText()=='Log' and len(np.where(self.data[fname]['y']<1e-30)[0])>0:
            #     posval=np.argwhere(self.fit.y>0)
            #     self.fit.y=self.data[fname]['y'][posval].T[0]
            #     self.fit.x=self.data[fname]['x'][posval].T[0]
            #     self.fit.yerr=self.data[fname]['yerr'][posval].T[0]
            self.fit.set_x(x,y=y,yerr=yerr)
            #self.update_plot()
            self.oldParams=copy.copy(self.fit.params)
            if self.fit.params['__mpar__']!={}:
                self.oldmpar=copy.copy(self.mfitParamData)
            try:
                self.showFitInfoDlg(emcee_steps=emcee_steps, emcee_burn = emcee_burn)
                self.runFit(emcee_steps=emcee_steps, emcee_burn=emcee_burn)
                #self.fit_report,self.fit_message=self.fit.perform_fit(self.xmin,self.xmax,fit_scale=self.fit_scale,\
                # fit_method=self.fit_method,callback=self.fitCallback)

                self.fit_info='Fit Message: %s\n'%self.fit_message

                self.closeFitInfoDlg()
                if self.fit_method != 'emcee':
                    self.errorAvailable=False
                    self.showConfIntervalButton.setDisabled(True)
                    self.fit.functionCalled.disconnect(self.fitCallback)
                    try:
                        self.sfitParamTableWidget.cellChanged.disconnect(self.sfitParamChanged)
                        self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
                    except:
                        pass
                    for row in range(self.sfitParamTableWidget.rowCount()):
                        key=self.sfitParamTableWidget.item(row,0).text()
                        self.sfitParamTableWidget.item(row,1).setText('%.6e'%(self.fit.result.params[key].value))
                    self.sfitParamTableWidget.resizeRowsToContents()
                    self.sfitParamTableWidget.resizeColumnsToContents()
                    for row in range(self.mfitParamTableWidget.rowCount()):
                        for col in range(1,self.mfitParamTableWidget.columnCount()):
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
                                if self.fit.result.params[key].stderr is None:
                                    self.fit.result.params[key].stderr=0.0
                                self.sfitParamTableWidget.item(row,1).setToolTip(key+' = %.3e \u00B1 %.3e'%\
                                                                                 (self.fit.result.params[key].value,\
                                                                                  self.fit.result.params[key].stderr))
                            except:
                                pass
                        if self.fit.params['__mpar__']!={}:
                            for row in range(self.mfitParamTableWidget.rowCount()):
                                for col in range(1,self.mfitParamTableWidget.columnCount()):
                                    parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                                    key='__%s__%03d'%(parkey,row)
                                    if self.fit.result.params[key].stderr is None:
                                        self.fit.result.params[key].stderr = 0.0
                                    self.mfitParamTableWidget.item(row,col).setToolTip(key+' = %.3e \u00B1 %0.3e'%\
                                                                                       (self.fit.result.params[key].value,\
                                                                                        self.fit.result.params[key].stderr))
                                    self.mfitParamData[parkey][row]=self.fit.result.params[key].value

                        ofname=os.path.splitext(fname.split('<>')[1])[0]
                        header='Data fitted with model: %s on %s\n'%(self.funcListWidget.currentItem().text(),time.asctime())
                        header+='Fixed Parameters\n'
                        header+='----------------\n'
                        for key in self.fit.params.keys():
                            if key not in self.fit.fit_params.keys() and key not in self.special_keys and key[:2]!='__':
                                header+=key+'='+str(self.fit.params[key])+'\n'
                        header+=self.fit_report+'\n'
                        header+="col_names=['x','y','yerr','yfit']\n"
                        header+='x \t y\t yerr \t yfit\n'
                        if type(self.fit.x)==dict:
                            for key in self.fit.x.keys():
                                fitdata=np.vstack((self.fit.x[key][self.fit.imin[key]:self.fit.imax[key]+1],self.fit.y[key][self.fit.imin[key]:self.fit.imax[key]+1],\
                                                   self.fit.yerr[key][self.fit.imin[key]:self.fit.imax[key]+1],self.fit.yfit[key])).T
                                np.savetxt(ofname+'_'+key+'_fit.txt',fitdata,header=header,comments='#')
                        else:
                            fitdata = np.vstack((self.fit.x[self.fit.imin:self.fit.imax + 1],
                                                 self.fit.y[self.fit.imin:self.fit.imax + 1], \
                                                 self.fit.yerr[self.fit.imin:self.fit.imax + 1],
                                                 self.fit.yfit)).T
                            np.savetxt(ofname + '_fit.txt', fitdata, header=header, comments='#')
                        self.xChanged()
                    else:
                        self.undoFit()
                else:
                    self.fit.functionCalled.disconnect(self.fitErrorCallback)
                    self.fitErrorDialog()
                    self.errorAvailable = True
                    self.showConfIntervalButton.setEnabled(True)
            except:
                try:
                    self.closeFitInfoDlg()
                except:
                    pass
                QMessageBox.warning(self,'Minimization failed','Some of the parameters have got unreasonable values.\n'+traceback.format_exc(),QMessageBox.Ok)
                self.update_plot()
                break
        self.sfitParamTableWidget.cellChanged.connect(self.sfitParamChanged)
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
        try:
            self.fit.functionCalled.disconnect(self.fitCallback)
        except:
            pass
        try:
            self.fit.functionCalled.disconnect(self.fitErrorCallback)
        except:
            pass

        
    def confInterval_emcee(self):
        """
        """
        multiInputDlg=MultiInputDialog(inputs={'EMCEE Steps':100, 'EMCEE Burn':10},parent=self)
        # multiInputDlg.show()
        if multiInputDlg.exec_():
            self.emcee_steps = int(multiInputDlg.inputs['EMCEE Steps'])
            self.emcee_burn = int(multiInputDlg.inputs['EMCEE Burn'])
            self.doFit(fit_method='emcee', emcee_steps=self.emcee_steps, emcee_burn=self.emcee_burn)


    def conf_interv_status(self,params,iterations,residual,fit_scale):
        self.confIntervalStatus.setText(self.confIntervalStatus.text().split('\n')[0]+'\n\n {:^s} = {:10d}'.format('Iteration',iterations))            
        pg.QtGui.QApplication.processEvents()
        
    def runFit(self, emcee_steps=100, emcee_burn=30):
        self.start_time=time.time()
        self.fit_report,self.fit_message=self.fit.perform_fit(self.xmin,self.xmax,fit_scale=self.fit_scale, fit_method=self.fit_method,
                                                              maxiter=int(self.fitIterationLineEdit.text()), emcee_steps=emcee_steps, emcee_burn=emcee_burn)
        
    
    def showFitInfoDlg(self, emcee_steps=100, emcee_burn=30):
        if self.fit_method!='emcee':
            self.fitInfoDlg=QDialog(self)
            vblayout=QVBoxLayout(self.fitInfoDlg)
            self.fitIterLabel=QLabel('Iteration: 0,\t Chi-sqr: Not Available',self.fitInfoDlg)
            vblayout.addWidget(self.fitIterLabel)
            self.stopFitPushButton=QPushButton('Stop')
            vblayout.addWidget(self.stopFitPushButton)
            self.stopFitPushButton.clicked.connect(self.stopFit)
            self.fitInfoDlg.setWindowTitle('Please wait for the fitting to be completed')
            self.fitInfoDlg.setModal(True)
            self.fitInfoDlg.show()
        else:
            self.fitInfoDlg=QProgressDialog("Please Wait for %.3f min"%0.0, "Cancel", 0, 100, self)
            self.fitInfoDlg.setAutoClose(True)
            self.fitInfoDlg.setMaximum(100*emcee_steps)
            self.fitInfoDlg.setValue(0)
            self.fitInfoDlg.canceled.connect(self.stopFit)
            self.fitInfoDlg.show()
        
    def stopFit(self):
        self.fit.fit_abort=True
        self.closeFitInfoDlg()
        
    def closeFitInfoDlg(self):
        self.fitInfoDlg.done(0)
        
    def fitCallback(self,params,iterations,residual,fit_scale):
        self.fitIterLabel.setText('Iteration=%d,\t Chi-sqr=%.5e'%(iterations,np.sum(residual**2)))
        # if np.any(self.fit.yfit):
        if type(self.fit.x)==dict:
            for key in self.fit.x.keys():
                self.plotWidget.add_data(x=self.fit.x[key][self.fit.imin[key]:self.fit.imax[key]+1],y=self.fit.yfit[key],\
                                 name=self.funcListWidget.currentItem().text()+':'+key,fit=True)
                self.fit.params['output_params']['Residuals_%s'%key] = {'x': self.fit.x[key][self.fit.imin[key]:self.fit.imax[key]+1],
                                                                        'y': (self.fit.y[key][self.fit.imin[key]:self.fit.imax[key]+1]-self.fit.yfit[key])
                /self.fit.yerr[key][self.fit.imin[key]:self.fit.imax[key]+1]}
        else:
            self.plotWidget.add_data(x=self.fit.x[self.fit.imin:self.fit.imax + 1], y=self.fit.yfit, \
                                     name=self.funcListWidget.currentItem().text(), fit=True)
        # else:
        #     QMessageBox.warning(self,'Parameter Value Error','One or more fitting parameters has got unphysical values perhaps to make all the yvalues zeros!',QMessageBox.Ok)
        #     self.fit.fit_abort=True
            self.fit.params['output_params']['Residuals']={'x':self.fit.x[self.fit.imin:self.fit.imax + 1],
                                                           'y': (self.fit.y[self.fit.imin:self.fit.imax + 1]-self.fit.yfit)/self.fit.yerr[self.fit.imin:self.fit.imax + 1]}
        pg.QtGui.QApplication.processEvents()
        # pg.QtGui.QApplication.processEvents()

    def fitErrorCallback(self, params, iterations, residual, fit_scale):
        time_taken=time.time()-self.start_time
        time_left=time_taken*(100*self.emcee_steps-iterations)/iterations
        self.fitInfoDlg.setLabelText('Please wait for %.3f mins'%(time_left/60))
        self.fitInfoDlg.setValue(iterations)
        pg.QtGui.QApplication.processEvents()
        # pg.QtGui.QApplication.processEvents()

    def fitErrorDialog(self):
        mesg=[['Parameters', 'Value', 'Left-error', 'Right-error']]
        for key in self.fit.fit_params.keys():
            if self.fit.fit_params[key].vary:
                l,p,r = np.percentile(self.fit.result.flatchain[key], [15.9, 50, 84.2])
                mesg.append([key, p, l-p, r-p])
        names=[name for name in self.fit.result.var_names if name!='__lnsigma']
        values=[self.fit.result.params[name].value for name in names]
        fig = corner.corner(self.fit.result.flatchain[names], labels=names, bins=50,
                            truths = values, quantiles = [0.159, 0.5, 0.842], show_titles = True, title_fmt='.3f',
                            use_math_text=True)
        for ax in fig.get_axes():
            ax.set_xlabel('')
        dlg=QDialog(self)
        dlg.setWindowTitle('Error Estimates')
        dlg.resize(800, 600)
        vblayout = QVBoxLayout(dlg)
        splitter=QSplitter(Qt.Vertical)
        plotWidget=QWidget()
        clabel = QLabel('Parameter Correlations')
        canvas=FigureCanvas(fig)
        toolbar=NavigationToolbar(canvas, self)
        playout=QVBoxLayout()
        playout.addWidget(clabel)
        playout.addWidget(canvas)
        playout.addWidget(toolbar)
        plotWidget.setLayout(playout)
        splitter.addWidget(plotWidget)
        fig.tight_layout()
        canvas.draw()
        statWidget=QWidget()
        slayout=QVBoxLayout()
        label = QLabel('Error Estimates of the parameters')
        slayout.addWidget(label)
        textEdit = QTextEdit()
        textEdit.setFont(QFont("Courier",10))
        txt=tabulate(mesg,headers='firstrow',stralign='left',numalign='left',tablefmt='simple')
        textEdit.setText(txt)
        slayout.addWidget(textEdit)
        saveWidget=QWidget()
        hlayout=QHBoxLayout()
        savePushButton=QPushButton('Save Parameters')
        savePushButton.clicked.connect(lambda x: self.saveParameterError(text=txt))
        hlayout.addWidget(savePushButton)
        closePushButton=QPushButton('Close')
        closePushButton.clicked.connect(dlg.accept)
        hlayout.addWidget(closePushButton)
        saveWidget.setLayout(hlayout)
        slayout.addWidget(saveWidget)
        statWidget.setLayout(slayout)
        splitter.addWidget(statWidget)
        vblayout.addWidget(splitter)
        dlg.setWindowTitle('Parameter Errors')
        dlg.setModal(True)
        dlg.show()
        # QMessageBox.information(self, 'Parameter Errors', tabulate(mesg, headers='firstrow',stralign='right',numalign='right',tablefmt='rst'), QMessageBox.Ok)

    def saveParameterError(self, text=''):
        fname=QFileDialog.getSaveFileName(caption='Save Parameter Errors as',filter='Parameter Error files (*.perr)',directory=self.curDir)[0]
        if os.path.splitext(fname)=='':
            fname=fname+'.perr'
        fh=open(fname,'w')
        fh.writelines(text)
        fh.close()


    def undoFit(self):
        try:
            self.sfitParamTableWidget.cellChanged.disconnect(self.sfitParamChanged)
            self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        except:
            pass
        for row in range(self.sfitParamTableWidget.rowCount()):
            key=self.sfitParamTableWidget.item(row,0).text()
            self.sfitParamTableWidget.item(row,1).setText('%.6e'%(self.oldParams[key]))
        if self.fit.params['__mpar__']!={}:
            for row in range(self.mfitParamTableWidget.rowCount()):
                for col in range(1,self.mfitParamTableWidget.columnCount()):
                    parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                    key='__%s__%03d'%(parkey,row)
                    self.mfitParamTableWidget.item(row,col).setText('%.6e'%(self.oldmpar[parkey][row]))
            self.mfitParamData=copy.copy(self.oldmpar)
        self.sfitParamTableWidget.cellChanged.connect(self.sfitParamChanged)
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
        self.update_plot()                    

        
        
    def addData(self,fnames=None):
        """
        fnames        :List of filenames
        """
        if self.dataListWidget.count()==0:
            self.fileNumber=0
        try:
            self.dataListWidget.itemSelectionChanged.disconnect(self.dataFileSelectionChanged)
        except:
            pass
        #try:
        if fnames is None:
            fnames,_=QFileDialog.getOpenFileNames(self,caption='Open data files',directory=self.curDir,\
                                                  filter='Data files (*.txt *.dat *.chi *.rrf)')
        if len(fnames)!=0:
            self.curDir=os.path.dirname(fnames[0])
            for fname in fnames:
                data_key=str(self.fileNumber)+'<>'+fname
                data_dlg=Data_Dialog(fname=fname,parent=self)
                data_dlg.closePushButton.setText('Cancel')
                if len(fnames)>1:
                    data_dlg.accept()
                else:
                    data_dlg.exec_()
                if data_dlg.acceptData:
                    self.dlg_data[data_key]=data_dlg.data
                    self.plotColIndex[data_key]=data_dlg.plotColIndex
                    self.plotColors[data_key]=data_dlg.plotColors
                    self.data[data_key]=data_dlg.externalData
                    self.expressions[data_key]=data_dlg.expressions
                    for key in self.data[data_key].keys():
                        self.plotWidget.add_data(self.data[data_key][key]['x'],self.data[data_key][key]['y'],\
                                                 yerr=self.data[data_key][key]['yerr'],name='%d:%s'%(self.fileNumber,key),color=self.data[data_key][key]['color'])
                    self.dataListWidget.addItem(data_key)
                    self.fileNames[self.fileNumber]=fname
                    self.fileNumber+=1
            #     else:
            #         QMessageBox.warning(self,'Import Error','Data file has been imported before.\
            #          Please remove the data file before importing again')
            # #except:
            # #    QMessageBox.warning(self,'File error','The file(s) do(es) not look like a data file. Please format it in x,y[,yerr] column format',QMessageBox.Ok)
        self.dataListWidget.clearSelection()
        self.dataListWidget.itemSelectionChanged.connect(self.dataFileSelectionChanged)
        self.dataListWidget.setCurrentRow(self.fileNumber-1)

                
                
        
    def removeData(self):
        """
        """
        try:
            self.dataListWidget.itemSelectionChanged.disconnect(self.dataFileSelectionChanged)
        except:
            pass
        for item in self.dataListWidget.selectedItems():
            fnum,fname=item.text().split('<>')
            self.dataListWidget.takeItem(self.dataListWidget.row(item))
            for key in self.data[item.text()].keys():
                self.plotWidget.remove_data(['%s:%s'%(fnum,key)])
            del self.data[item.text()]
            del self.expressions[item.text()]
            del self.plotColIndex[item.text()]
            del self.plotColors[item.text()]
            del self.dlg_data[item.text()]

        if self.dataListWidget.count()>0:
            self.dataFileSelectionChanged()
        self.dataListWidget.itemSelectionChanged.connect(self.dataFileSelectionChanged)
            
        
        
    def create_paramDock(self):
        self.parSplitter=QSplitter(Qt.Vertical)
                
        self.fixedparamLayoutWidget=pg.LayoutWidget(self)
        
        xlabel=QLabel('x')
        self.fixedparamLayoutWidget.addWidget(xlabel)
        self.xLineEdit=QLineEdit('np.linspace(0.001,1,100)')
        self.fixedparamLayoutWidget.addWidget(self.xLineEdit,col=1)
        self.saveSimulatedButton=QPushButton("Save Simulated Curve")
        self.saveSimulatedButton.setEnabled(False)
        self.saveSimulatedButton.clicked.connect(self.saveSimulatedCurve)
        self.fixedparamLayoutWidget.addWidget(self.saveSimulatedButton,col=2)

        self.fixedparamLayoutWidget.nextRow()
        self.saveParamButton = QPushButton('Save Parameters')
        self.saveParamButton.clicked.connect(self.saveParameters)
        self.fixedparamLayoutWidget.addWidget(self.saveParamButton,col=1)
        self.loadParamButton = QPushButton('Load Parameters')
        self.loadParamButton.clicked.connect(lambda x: self.loadParameters(fname=None))
        self.fixedparamLayoutWidget.addWidget(self.loadParamButton, col=2)
        
        self.fixedparamLayoutWidget.nextRow()
        fixedParamLabel=QLabel('Fixed Parameters')
        self.fixedparamLayoutWidget.addWidget(fixedParamLabel, colspan=3)

        self.fixedparamLayoutWidget.nextRow()
        self.fixedParamTableWidget=pg.TableWidget()
        self.fixedParamTableWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.fixedParamTableWidget.setEditable(editable=True)
        self.fixedParamTableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.fixedparamLayoutWidget.addWidget(self.fixedParamTableWidget,colspan=3)
        
        self.parSplitter.addWidget(self.fixedparamLayoutWidget)
        
        self.sfitparamLayoutWidget=pg.LayoutWidget()
        sfitParamLabel=QLabel('Single fitting parameters')
        self.sfitparamLayoutWidget.addWidget(sfitParamLabel)

        
        self.sfitparamLayoutWidget.nextRow()
        self.sfitParamTableWidget=pg.TableWidget()
        self.sfitParamTableWidget.setEditable(editable=True)
        self.sfitParamTableWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.sfitParamTableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        #self.sfitParamTableWidget.cellDoubleClicked.connect(self.editFitParam)
        self.sfitparamLayoutWidget.addWidget(self.sfitParamTableWidget,colspan=3)
        
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
        
        # self.mfitparamLayoutWidget.nextRow()
        # self.saveParamButton=QPushButton('Save Parameters')
        # self.saveParamButton.clicked.connect(self.saveParameters)
        # self.mfitparamLayoutWidget.addWidget(self.saveParamButton,col=1)
        # self.loadParamButton=QPushButton('Load Parameters')
        # self.loadParamButton.clicked.connect(lambda x: self.loadParameters(fname=None))
        # self.mfitparamLayoutWidget.addWidget(self.loadParamButton,col=2)
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


    def saveSimulatedCurve(self):
        """
        Saves the simulated curve in a user-supplied ascii file
        :return:
        """
        fname=QFileDialog.getSaveFileName(caption='Save As',filter='Text files (*.dat, *.txt)',directory=self.curDir)[0]
        if fname!='':
            header='Simulated curve generated on %s\n'%time.asctime()
            header+='Category:%s\n'%self.curr_category
            header+='Function:%s\n'%self.funcListWidget.currentItem().text()
            for i in range(self.fixedParamTableWidget.rowCount()):
                header += '%s=%s\n' % (
                self.fixedParamTableWidget.item(i, 0).text(), self.fixedParamTableWidget.item(i, 1).text())
            for i in range(self.sfitParamTableWidget.rowCount()):
                header += '%s=%s\n' % (
                self.sfitParamTableWidget.item(i, 0).text(), self.sfitParamTableWidget.item(i, 1).text())
            for i in range(self.mfitParamTableWidget.rowCount()):
                vartxt = self.mfitParamTableWidget.item(i, 0).text()
                for j in range(1, self.mfitParamTableWidget.columnCount()):
                    header += '%s_%s=%s\n' % (vartxt, self.mfitParamTableWidget.horizontalHeaderItem(j).text(),
                                              self.mfitParamTableWidget.item(i, j).text())
            if type(self.fit.x)==dict:
                text='col_names=[\'q\','
                keys=list(self.fit.x.keys())
                data=self.fit.x[keys[0]]
                for key in keys:
                    text+='\''+key+'\','
                    data=np.vstack((data,self.fit.yfit[key]))
                header+=text[:-1]+']\n'
                np.savetxt(fname,data.T,header=header,comments='#')
            else:
                header+='col_names=[\'q\',\'I\']'
                np.savetxt(fname,np.vstack((self.fit.x,self.fit.yfit)).T,header=header,comments='#')
        else:
            pass

        
    def mparDoubleClicked(self,row,col):
        if col!=0:
            try:
                self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
            except:
                pass
            parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
            key='__%s__%03d'%(parkey,row)
            value=self.fit.fit_params[key].value
            vary=self.fit.fit_params[key].vary
            minimum=self.fit.fit_params[key].min
            maximum=self.fit.fit_params[key].max
            expr=self.fit.fit_params[key].expr
            brute_step=self.fit.fit_params[key].brute_step
            dlg=minMaxDialog(value,vary=vary,minimum=minimum,maximum=maximum,expr=expr,brute_step=brute_step)
            if dlg.exec_():
                value,vary,maximum,minimum,expr,brute_step=(dlg.value,dlg.vary,dlg.maximum,dlg.minimum,dlg.expr,dlg.brute_step)
            self.mfitParamTableWidget.item(row,col).setText(str(value))
            if vary:
                self.mfitParamTableWidget.item(row, col).setCheckState(Qt.Checked)
            else:
                self.mfitParamTableWidget.item(row, col).setCheckState(Qt.Unchecked)
            self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
            self.mfitParamData[parkey][row]=value
            self.fit.fit_params[key].set(value=value)
            if expr=='None':
                expr=''
            self.fit.fit_params[key].set(value=value,vary=vary,min=minimum,max=maximum,expr=expr,brute_step=brute_step)
            self.update_plot()


        
        
    def add_mpar(self):
        try:
            self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        except:
            pass
        NCols=self.mfitParamTableWidget.columnCount()
        if len(self.mfitParamTableWidget.selectedItems())!=0:
            curRow=self.mfitParamTableWidget.currentRow()
            #if curRow!=0:
            self.mfitParamTableWidget.insertRow(curRow)
            self.mfitParamTableWidget.setRow(curRow,self.mfitParamData[curRow])
            self.mfitParamData=np.insert(self.mfitParamData,curRow,self.mfitParamData[curRow],0)
            NRows = self.mfitParamTableWidget.rowCount()
            for col in range(NCols):
                parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                if col!=0:
                    for row in range(curRow,NRows):
                        key='__%s__%03d'%(parkey,row)
                        if key in self.fit.fit_params.keys():
                            self.fit.fit_params[key].set(value=self.mfitParamData[row][col])
                        else:
                            self.fit.fit_params.add(key,value=self.mfitParamData[row][col])
                    fvals=[self.fit.fit_params['__%s__%03d'%(parkey,row)].vary for row in range(NRows-1)]
                    minvals = [self.fit.fit_params['__%s__%03d' % (parkey, row)].min for row in range(NRows - 1)]
                    maxvals = [self.fit.fit_params['__%s__%03d' % (parkey, row)].max for row in range(NRows - 1)]
                    exprvals= [self.fit.fit_params['__%s__%03d' % (parkey, row)].expr for row in range(NRows - 1)]
                    bsvals = [self.fit.fit_params['__%s__%03d' % (parkey, row)].brute_step for row in range(NRows - 1)]
                    for row in range(curRow+1,NRows):# This is to keep intact the fitting flag of the rest of the parameters
                        key='__%s__%03d'%(parkey,row)
                        self.fit.fit_params[key].set(vary=fvals[row-1], min=minvals[row-1],max=maxvals[row-1],
                                                     expr=exprvals[row-1],brute_step=bsvals[row-1])
                    key = '__%s__%03d' % (parkey, curRow)
                    self.fit.fit_params[key].set(min = minvals[curRow], max=maxvals[curRow],expr=exprvals[curRow],brute_step=bsvals[curRow])
                    # This is to make the newly inserted row checkable
                    item = self.mfitParamTableWidget.item(curRow, col)
                    item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
                    if fvals[curRow]>0:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                self.fit.params['__mpar__'][parkey].insert(curRow, self.mfitParamData[curRow][col])
            #self.update_mfit_parameters()
            self.update_plot()
            self.remove_mpar_button.setEnabled(True)
        else:
            QMessageBox.warning(self,'Warning','Please select a row at which you would like to add a set of parameters',QMessageBox.Ok)
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
            
    def remove_mpar(self):
        selrows=list(set([item.row() for item in self.mfitParamTableWidget.selectedItems()]))
        num=self.mfitParamTableWidget.rowCount()-len(selrows)
        if num<self.mpar_N:
            QMessageBox.warning(self,'Selection error','The minimum number of rows required for this function to work is %d.\
             You can only remove %d rows'%(self.mpar_N,num),QMessageBox.Ok)
            return
        if self.mfitParamTableWidget.rowCount()-1 in selrows:
            QMessageBox.warning(self, 'Selection error',
                                'Cannot remove the last row. Please select the rows other than the last row', QMessageBox.Ok)
            return
        try:
            self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        except:
            pass
        if selrows!=[]:
            selrows.sort(reverse=True)
            for row in selrows:
                maxrow=self.mfitParamTableWidget.rowCount()
                for trow in range(row,maxrow):
                    for col in range(self.mfitParamTableWidget.columnCount()):
                        parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                        if trow<maxrow-1:
                            key1='__%s__%03d'%(parkey,trow)
                            key2='__%s__%03d'%(parkey,trow+1)
                            self.fit.params['__mpar__'][parkey][trow] = copy.copy(self.fit.params['__mpar__'][parkey][trow + 1])
                            if col!=0:
                                self.fit.fit_params[key1]=copy.copy(self.fit.fit_params[key2])
                                del self.fit.fit_params[key2]
                        else:
                            key1='__%s__%03d'%(parkey,trow)
                            # if col!=0:
                            del self.fit.params['__mpar__'][parkey][trow]
                                # del self.fit.fit_params[key1]

                self.mfitParamTableWidget.removeRow(row)
                self.mfitParamData=np.delete(self.mfitParamData,row,axis=0)
        else:
            QMessageBox.warning(self,'Nothing selected','No item is selected for removal',QMessageBox.Ok)
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
        self.update_plot()
        if self.mfitParamTableWidget.rowCount()==self.mpar_N:
            self.remove_mpar_button.setDisabled(True)
            
        
    def saveGenParameters(self):
        if len(self.genParamListWidget.selectedItems())==1:
            text=self.genParamListWidget.selectedItems()[0].text()
            name,var=text.split(' : ')
            fname=QFileDialog.getSaveFileName(self,'Save generated data as',self.curDir,'Text files (*.txt)')[0]
            if fname!='':
                if fname[-4:]!='.txt':
                    fname=fname+'.txt'
                header='Generated output file on %s\n'%time.asctime()
                header += 'Category=%s\n' % self.curr_category
                header += 'Function=%s\n' % self.funcListWidget.currentItem().text()
                for i in range(self.fixedParamTableWidget.rowCount()):
                    header+='%s=%s\n'%(self.fixedParamTableWidget.item(i,0).text(),self.fixedParamTableWidget.item(i,1).text())
                for i in range(self.sfitParamTableWidget.rowCount()):
                    header+='%s=%s\n'%(self.sfitParamTableWidget.item(i,0).text(),self.sfitParamTableWidget.item(i,1).text())
                for i in range(self.mfitParamTableWidget.rowCount()):
                    vartxt=self.mfitParamTableWidget.item(i,0).text()
                    for j in range(1,self.mfitParamTableWidget.columnCount()):
                        header+='%s_%s=%s\n'%(vartxt,self.mfitParamTableWidget.horizontalHeaderItem(j).text(),self.mfitParamTableWidget.item(i,j).text())
                if 'names' in self.fit.params['output_params'][name]:
                    header += "col_names=%s\n" % str(self.fit.params['output_params'][name]['names'])
                else:
                    header += "col_names=%s\n" % var
                if var=="['x', 'y']":
                    header+='x\ty\n'
                    res=np.vstack((self.fit.params['output_params'][name]['x'], self.fit.params['output_params'][name]['y'])).T
                    np.savetxt(fname,res,header=header,comments='#')
                elif var=="['x', 'y', 'yerr']":
                    header+='x\ty\tyerr\n'
                    res=np.vstack((self.fit.params['output_params'][name]['x'], self.fit.params['output_params'][name]['y'],self.fit.params['output_params'][name]['yerr'])).T
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
                txt=self.fixedParamTableWidget.item(row,0).text()
                if txt in self.fit.params['choices'].keys():
                    fh.write(txt+'\t'+self.fixedParamTableWidget.cellWidget(row, 1).currentText()+'\n')
                else:
                    fh.write(txt+'\t'+self.fixedParamTableWidget.item(row,1).text()+'\n')
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
                    parkey = self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                    if col!=0:
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
                    else:
                        for row in range(self.mfitParamTableWidget.rowCount()):
                            parname = '__%s__%03d' % (parkey, row)
                            par = self.mfitParamTableWidget.item(row, col)
                            parval = par.text()
                            fh.write('%s\t%s\n' % (parname, parval))

            fh.close()
        
        
    def loadParameters(self,fname=None):
        """
        loads parameters from a parameter file
        """
        # if self.funcListWidget.currentItem() is not None:
        if fname is None:
            fname,_=QFileDialog.getOpenFileName(self,caption='Open parameter file',directory=self.curDir,filter='Parameter files (*.par)')
        else:
            fname=fname
        if fname!='':
            fh=open(fname,'r')
            lines=fh.readlines()
            category=lines[1].split(': ')[1].strip()
            cat_item=self.categoryListWidget.findItems(category,Qt.MatchExactly)
            self.categoryListWidget.setCurrentItem(cat_item[0])
            self.funcListWidget.clearSelection()
            func=lines[2].split(': ')[1].strip()
            func_item=self.funcListWidget.findItems(func,Qt.MatchExactly)
            self.funcListWidget.setCurrentItem(func_item[0])
            #self.fit.func.init_params()
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
                        self.fit.fit_params[parname].set(value=float(parval),vary=int(parfit),min=float(parmin),max=float(parmax))
                        try:
                            self.fit.fit_params[parname].set(expr=eval(parexpr))
                        except:
                            self.fit.fit_params[parname].set(expr=str(parexpr))
                        try:
                            self.fit.fit_params[parname].set(brute_step=eval(parbrute))
                        except:
                            self.fit.fit_params[parname].set(brute_step=str(parbrute))

                if mfline is not None:
                    for line in lines[mfline:]:
                        tlist=line.strip().split('\t')
                        if len(tlist)>2:
                            parname,parval,parfit,parmin,parmax,parexpr,parbrute=tlist
                            try:
                                expr=eval(parexpr)
                            except:
                                expr=str(parexpr)
                            try:
                                brute_step=eval(parbrute)
                            except:
                                brute_step=str(parbrute)
                            try:
                                self.fit.fit_params.set(value=float(parval),vary=int(parfit),min=float(parmin),max=float(parmax),expr=expr,brute_step=brute_step)
                            except:
                                self.fit.fit_params.add(parname,value=float(parval),vary=int(parfit),min=float(parmin),\
                                                        max=float(parmax),expr=expr,brute_step=brute_step)
                            _, par, num = parname.split('__')
                            num = int(num)
                            try:
                                self.fit.params['__mpar__'][par][num] = float(parval)
                            except:
                                self.fit.params['__mpar__'][par].insert(num, float(parval))
                        else:
                            parname,parval=tlist

                            _,par,num=parname.split('__')
                            num=int(num)
                            try:
                                self.fit.params['__mpar__'][par][num]=parval
                            except:
                                self.fit.params['__mpar__'][par].insert(num,parval)
                try:
                    self.fixedParamTableWidget.cellChanged.disconnect(self.fixedParamChanged)
                    self.sfitParamTableWidget.cellChanged.disconnect(self.sfitParamChanged)
                    self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
                except:
                    pass
                self.update_fixed_parameters()
                self.update_fit_parameters()
                self.fixedParamTableWidget.cellChanged.connect(self.fixedParamChanged)
                self.sfitParamTableWidget.cellChanged.connect(self.sfitParamChanged)
                self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
                self.update_plot()
            else:
                QMessageBox.warning(self,'File error','This parameter file does not belong to function: %s'% func,QMessageBox.Ok)
        # else:
            #     QMessageBox.warning(self,'Function error','Please select a function first before loading parameter file.',QMessageBox.Ok)

        
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

        self.fitResultsLayoutWidget = pg.LayoutWidget()
        fitResults = QLabel('Fit Results')
        self.fitResultsLayoutWidget.addWidget(fitResults, colspan=1)
        self.fitResultsLayoutWidget.nextRow()
        self.fitResultsListWidget = QListWidget()
        self.fitResultsLayoutWidget.addWidget(self.fitResultsListWidget, colspan=1)
        self.plotSplitter.addWidget(self.fitResultsLayoutWidget)

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
        self.saveSimulatedButton.setEnabled(False)
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
        self.gen_param_items=[]
        self.curr_module=self.funcListWidget.currentItem().text()
        module='Functions.%s.%s'%(self.curr_category,self.curr_module)
        # try:
        if module not in sys.modules:
            self.curr_funcClass[module]=import_module(module)
        else:
            self.curr_funcClass[module]=reload(self.curr_funcClass[module])

        self.fchanged = True
        self.update_parameters()
        self.saveSimulatedButton.setEnabled(True)
        # except:
        #     QMessageBox.warning(self,'Function Error','Some syntax error in the function still exists.',QMessageBox.Ok)
        
    def update_parameters(self):
        """
        Depending upon the selection of the function this updates the reloads the parameters required for the function
        """
        try:
            self.fixedParamTableWidget.cellChanged.disconnect(self.fixedParamChanged)
            self.sfitParamTableWidget.cellChanged.disconnect(self.sfitParamChanged)
            self.mfitParamTableWidget.cellChanged.disconnect(self.mfitParamChanged)
        except:
            pass
        try:
            self.x=eval(self.xLineEdit.text())
        except:
            QMessageBox.warning(self,'Parameter Error','The value you just entered is not correct.\n'+traceback.format_exc(),QMessageBox.Ok)
        self.curr_module=self.funcListWidget.currentItem().text()
        module='Functions.%s.%s'%(self.curr_category,self.curr_module)
        self.fit=Fit(getattr(self.curr_funcClass[module],self.funcListWidget.currentItem().text()),self.x)
        if '__mpar__' in self.fit.params.keys() and self.fit.params['__mpar__'] != {}:
            self.mpar_keys = list(self.fit.params['__mpar__'].keys())
            self.mpar_N = len(self.fit.params['__mpar__'][self.mpar_keys[0]])
        self.update_fixed_parameters()
        self.update_fit_parameters()
        self.update_plot()
        self.xLineEdit.returnPressed.connect(self.xChanged)
        self.mfitParamTableWidget.cellChanged.connect(self.mfitParamChanged)
        self.fixedParamTableWidget.cellChanged.connect(self.fixedParamChanged)
        self.sfitParamTableWidget.cellChanged.connect(self.sfitParamChanged)

    def update_fixed_parameters(self):
        fpdata=[]        
        for key in self.fit.params.keys():
            if key not in self.fit.fit_params.keys() and key not in self.special_keys and key[:2]!='__':
                fpdata.append((key,str(self.fit.params[key])))
        self.fixedParamData=np.array(fpdata,dtype=[('Params',object),('Value',object)])
        self.fixedParamTableWidget.setData(self.fixedParamData)
        for row in range(self.fixedParamTableWidget.rowCount()):
            self.fixedParamTableWidget.item(row,0).setFlags(Qt.ItemIsEnabled)
            if self.fixedParamTableWidget.item(row, 0).text() in self.fit.params['choices'].keys():
                items=[str(item) for item in self.fit.params['choices'][self.fixedParamTableWidget.item(row,0).text()]]
                combobox=QComboBox()
                combobox.addItems(items)
                self.fixedParamTableWidget.setCellWidget(row,1,combobox)
                index = combobox.findText(str(self.fit.params[self.fixedParamTableWidget.item(row, 0).text()]))
                combobox.setCurrentIndex(index)
                combobox.currentIndexChanged.connect(self.update_plot)
        self.fixedParamTableWidget.resizeRowsToContents()
        self.fixedParamTableWidget.resizeColumnsToContents()


    def update_fit_parameters(self):
        self.update_sfit_parameters()
        self.update_mfit_parameters()
        
    def update_sfit_parameters(self):
        tpdata=[]
        for key in self.fit.fit_params.keys():
            if key[:2]!='__':
                tpdata.append((key,self.fit.fit_params[key].value,self.fit.fit_params[key].min,\
                               self.fit.fit_params[key].max,str(self.fit.fit_params[key].expr),self.fit.fit_params[key].brute_step))
        self.fitParamData=np.array(tpdata,dtype=[('Params',object),('Value',object),('Min',object),('Max',object),\
                                                 ('Expr',object),('Brute step',float)])
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
            item.setToolTip(par + ' = %.3e \u00B1 %.3e' % \
                                                              (self.fit.fit_params[par].value, \
                                                               0.0))
        self.sfitParamTableWidget.resizeRowsToContents()
        self.sfitParamTableWidget.resizeColumnsToContents()
        
    def update_mfit_parameters(self):
        if '__mpar__' in self.fit.params.keys() and self.fit.params['__mpar__']!={}:
            mpar_keys=list(self.fit.params['__mpar__'].keys())
            mpar_N=len(self.fit.params['__mpar__'][mpar_keys[0]])
            tpdata=[]
            for i in range(mpar_N):
                temp=[]
                for key in mpar_keys:
                    if key in self.fit.fit_params.keys():
                        temp.append(self.fit.fit_params['__%s__%03d'%(key,i)].value)
                    else:
                        temp.append(self.fit.params['__mpar__'][key][i])
                tpdata.append(tuple(temp))
                #tpdata.append(tuple([self.fit.fit_params['__%s__%03d'%(key,i)].value for key in mpar_keys]))
            self.mfitParamData=np.array(tpdata,dtype=[(key,object) for key in mpar_keys])
            self.mfitParamTableWidget.setData(self.mfitParamData)
            self.add_mpar_button.setEnabled(True)
            self.remove_mpar_button.setEnabled(True)
            for row in range(self.mfitParamTableWidget.rowCount()):
                for col in range(1,self.mfitParamTableWidget.columnCount()):
                    item=self.mfitParamTableWidget.item(row,col)
                    item.setFlags(Qt.ItemIsUserCheckable|Qt.ItemIsEnabled|Qt.ItemIsEditable|Qt.ItemIsSelectable)
                    key='__%s__%03d'%(self.mfitParamTableWidget.horizontalHeaderItem(col).text(),row)
                    if self.fit.fit_params[key].vary==0:
                        item.setCheckState(Qt.Unchecked)
                    else:
                        item.setCheckState(Qt.Checked)
                    item.setToolTip(key + ' = %.3e \u00B1 %0.3e' % \
                                                                (self.fit.fit_params[key].value, \
                                                                 0.0))
            self.mfitParamTableWidget.resizeRowsToContents()
            self.mfitParamTableWidget.resizeColumnsToContents()
        else:
            self.add_mpar_button.setDisabled(True)
            self.remove_mpar_button.setDisabled(True)
            self.mfitParamTableWidget.setData([])
        
    def fixedParamChanged(self,row,col):
        txt=self.fixedParamTableWidget.item(row,0).text()
        if txt in self.fit.params['choices'].keys():
            self.fit.params[txt]=eval(self.fixedParamTableWidget.cellWidget(row,1).currentText())
            self.fchanged = False
            self.update_plot()
        else:
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
                QMessageBox.warning(self,'Value Error','The value just entered is not seem to be right.\n'+traceback.format_exc(),QMessageBox.Ok)
                self.fixedParamTableWidget.item(row,col).setText(str(oldVal))
        self.fixedParamTableWidget.resizeRowsToContents()
        self.fixedParamTableWidget.resizeColumnsToContents()


        
        
    def sfitParamChanged(self,row,col):
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
                if val!=self.fit.fit_params[txt].value:
                    self.fit.params[txt]=val
                    self.fit.fit_params[txt].set(value=val)
                    self.fchanged=False
                    self.update_plot()
            elif col==2:
                self.fit.fit_params[txt].set(min=val)
            elif col==3:
                self.fit.fit_params[txt].set(max=val)
            elif col==5:
                self.fit.fit_params[txt].set(brute_step=val)
        elif isinstance(val,str):
            if col==4:
                self.fit.fit_params[txt].expr= None if val == 'None' else val
        else:
            QMessageBox.warning(self,'Value Error','Please input numbers only',QMessageBox.Ok)
            self.sfitParamTableWidget.item(row,col).setText(str(oldVal))
        if self.sfitParamTableWidget.item(row,1).checkState()==Qt.Checked:
            self.fit.fit_params[txt].vary=1
        else:
            self.fit.fit_params[txt].vary=0
        self.sfitParamTableWidget.item(row,1).setToolTip(txt + ' = %.3e \u00B1 %0.3e' % \
                                                                (self.fit.fit_params[txt].value, \
                                                                 0.0))
        self.sfitParamTableWidget.resizeRowsToContents()
        self.sfitParamTableWidget.resizeColumnsToContents()
        
    def mfitParamChanged(self,row,col):
        parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
        txt=self.mfitParamTableWidget.item(row,col).text()
        try:
            key='__%s__%03d'%(parkey,row)
            if col!=0:
                oldval = self.fit.fit_params[key].value
                if float(txt)!=self.fit.fit_params[key].value:
                    pchanged=True
                else:
                    pchanged=False
                self.fit.fit_params[key].set(value=float(txt))
                if self.mfitParamTableWidget.item(row,col).checkState()==Qt.Checked:
                    self.fit.fit_params[key].set(vary=1)
                else:
                    self.fit.fit_params[key].set(vary=0)
                self.mfitParamData[row][col]=float(txt)
                self.fit.fit_params[key].set(value=float(txt))
                self.mfitParamTableWidget.item(row, col).setToolTip(key + ' = %.3e \u00B1 %0.3e' % \
                                                                    (self.fit.fit_params[key].value, \
                                                                     0.0))
            else:
                oldval = self.fit.params['__mpar__'][parkey][row]
                self.fit.params['__mpar__'][parkey][row] = txt
                self.mfitParamData[row][col] = txt
                pchanged=True
            self.fchanged=False
            if pchanged:
                self.update_plot()
        except:
            if col!=0:
                QMessageBox.warning(self,'Value Error','Please input numbers only',QMessageBox.Ok)
            else:
                QMessageBox.warning(self, 'Value Error', 'The text enter is not valid', QMessageBox.Ok)
            self.mfitParamTableWidget.item(row,col).setText(str(oldval))
        self.mfitParamTableWidget.resizeRowsToContents()
        self.mfitParamTableWidget.resizeColumnsToContents()
        
            
    def xChanged(self):
        try:
            x=eval(self.xLineEdit.text())
            #x=np.array(x)
            try:
                self.fit.params['x']=x
                self.fit.set_x(x)
            #self.fit.imin=0
            #self.fit.imax=len(self.fit.x)
            except:
                pass
            self.fchanged=False
            if len(self.funcListWidget.selectedItems())>0:
                try:
                    self.fit.evaluate()
                except:
                    QMessageBox.warning(self, 'Value error',
                                        'Something wrong with the value of the parameter which you just entered.\n'+traceback.format_exc(),
                                        QMessageBox.Ok)
                    return
                try:
                    self.genParamListWidget.itemSelectionChanged.disconnect(self.plot_extra_param)
                except:
                    pass
                self.genParamListWidget.clear()
                self.fit.params['output_params']['scaler_parameters']['Chi-Sqr']=self.chisqr
                if len(self.fit.params['output_params']) > 0:
                    for key in self.fit.params['output_params'].keys():
                        if key == 'scaler_parameters':
                            for k in self.fit.params['output_params'][key].keys():
                                self.genParamListWidget.addItem(k + ' : ' + str(self.fit.params['output_params'][key][k]))
                        else:
                            var=[]
                            for k in self.fit.params['output_params'][key].keys():
                                if k!='names':
                                    var.append(k)
                            self.genParamListWidget.addItem(
                                str(key) + ' : ' + str(var))
                    if not self.fchanged:
                        for item in self.gen_param_items:
                            try:
                                self.genParamListWidget.item.setSelected(True)
                            except:
                                pass
                    self.plot_extra_param()
                    self.genParamListWidget.itemSelectionChanged.connect(self.plot_extra_param)
                try:
                    pfnames=copy.copy(self.pfnames)
                except:
                    pfnames=[]
                if type(self.fit.x)==dict:
                    for key in self.fit.x.keys():
                        self.plotWidget.add_data(x=self.fit.x[key][self.fit.imin[key]:self.fit.imax[key] + 1], y=self.fit.yfit[key], \
                                         name=self.funcListWidget.currentItem().text()+':'+key, fit=True)
                    pfnames = pfnames + [self.funcListWidget.currentItem().text() + ':' + key for key in
                                             self.fit.x.keys()]
                else:
                    self.plotWidget.add_data(x=self.fit.x[self.fit.imin:self.fit.imax + 1], y=self.fit.yfit, \
                                             name=self.funcListWidget.currentItem().text(), fit=True)
                    pfnames = pfnames + [self.funcListWidget.currentItem().text()]

                self.plotWidget.Plot(pfnames)
                # pg.QtGui.QApplication.processEvents()
                pg.QtGui.QApplication.processEvents()
        except:
            QMessageBox.warning(self,'Value Error','The value just entered is not seem to be right.\n'+traceback.format_exc(),QMessageBox.Ok)
            self.xLineEdit.setText('np.linspace(0.001,0.1,100)')

        
    def update_plot(self):
        for row in range(self.fixedParamTableWidget.rowCount()):
            txt=self.fixedParamTableWidget.item(row,0).text()
            if txt in self.fit.params['choices'].keys():
                val = self.fixedParamTableWidget.cellWidget(row, 1).currentText()
            else:
                val=self.fixedParamTableWidget.item(row,1).text()
            try:
                self.fit.params[txt]=eval(val)
            except:
                self.fit.params[txt]=str(val)
        for row in range(self.sfitParamTableWidget.rowCount()):
            txt=self.sfitParamTableWidget.item(row,0).text()
            self.fit.params[txt]=float(self.sfitParamTableWidget.item(row,1).text())
            self.fit.fit_params[txt].set(value=float(self.sfitParamTableWidget.item(row,1).text()))
        for row in range(self.mfitParamTableWidget.rowCount()):
            parkey = self.mfitParamTableWidget.horizontalHeaderItem(0).text()
            txt = self.mfitParamTableWidget.item(row, 0).text()
            self.fit.params['__mpar__'][parkey][row] = txt
            for col in range(1,self.mfitParamTableWidget.columnCount()):
                parkey=self.mfitParamTableWidget.horizontalHeaderItem(col).text()
                txt=self.mfitParamTableWidget.item(row,col).text()
                self.fit.fit_params['__%s__%03d'%(parkey,row)].set(value=float(txt))
        try:
            pfnames=copy.copy(self.pfnames)
        except:
            pfnames=[]
        self.chisqr='None'
        if len(self.dataListWidget.selectedItems()) > 0:
            if len(self.data[self.sfnames[-1]].keys()) > 1:
                x = {}
                y = {}
                yerr = {}
                for key in self.data[self.sfnames[-1]].keys():
                    x[key] = self.data[self.sfnames[-1]][key]['x']
                    y[key] = self.data[self.sfnames[-1]][key]['y']
                    yerr[key] = self.data[self.sfnames[-1]][key]['yerr']
            else:
                key = list(self.data[self.sfnames[-1]].keys())[0]
                x = self.data[self.sfnames[-1]][key]['x']
                y = self.data[self.sfnames[-1]][key]['y']
                yerr = self.data[self.sfnames[-1]][key]['yerr']
            try:
                self.fit.set_x(x, y=y, yerr=yerr)
                residual = self.fit.residual(self.fit.fit_params, self.fitScaleComboBox.currentText())
                self.chisqr=np.sum(residual**2)
            except:
                pass
        if len(self.funcListWidget.selectedItems())>0:
            try:
                self.fit.evaluate()
            except:
                QMessageBox.warning(self, 'Evaluation Error', traceback.format_exc(), QMessageBox.Ok)
                self.fit.yfit = self.fit.func.x
            try:
                self.genParamListWidget.itemSelectionChanged.disconnect(self.plot_extra_param)
            except:
                pass
            self.fitResultsListWidget.clear()
            try:
                self.fitResultsListWidget.addItem('Chi-Square : %f' % self.fit.result.chisqr)
                self.fitResultsListWidget.addItem('Reduced Chi-Square : %f' % self.fit.result.redchi)
                self.fitResultsListWidget.addItem('Fit Message : %s' % self.fit.result.lmdif_message)
            except:
                self.fitResultsListWidget.clear()
            self.genParamListWidget.clear()
            self.fit.params['output_params']['scaler_parameters']['Chi-Square'] = self.chisqr
            if len(self.fit.params['output_params'])>0:
                for key in self.fit.params['output_params'].keys():
                    if key=='scaler_parameters':
                        for k in self.fit.params['output_params'][key].keys():
                            self.genParamListWidget.addItem(k + ' : ' + str(self.fit.params['output_params'][key][k]))
                    else:
                        var = []
                        for k in self.fit.params['output_params'][key].keys():
                            if k != 'names':
                                var.append(k)
                        self.genParamListWidget.addItem(
                            str(key) + ' : ' + str(var))
                if not self.fchanged:
                    for item in self.gen_param_items:
                        try:
                            self.genParamListWidget.item.setSelected(True)
                        except:
                            pass
            self.plot_extra_param()
            self.genParamListWidget.itemSelectionChanged.connect(self.plot_extra_param)
            if type(self.fit.x)==dict:
                for key in self.fit.x.keys():
                    self.plotWidget.add_data(x=self.fit.x[key][self.fit.imin[key]:self.fit.imax[key] + 1], y=self.fit.yfit[key], \
                                     name=self.funcListWidget.currentItem().text()+':'+key, fit=True)
                pfnames = pfnames + [self.funcListWidget.currentItem().text() + ':' + key for key in
                                         self.fit.x.keys()]
            else:
                self.plotWidget.add_data(x=self.fit.x[self.fit.imin:self.fit.imax + 1], y=self.fit.yfit, \
                                         name=self.funcListWidget.currentItem().text(), fit=True)
                pfnames=pfnames+[self.funcListWidget.currentItem().text()]
        self.plotWidget.Plot(pfnames)
        # pg.QtGui.QApplication.processEvents()
        pg.QtGui.QApplication.processEvents()
        
        
    def plot_extra_param(self):
        """
        """
        fdata=[]
        for item in self.genParamListWidget.selectedItems():
            txt,axes=item.text().split(':')
            txt=txt.strip()
            axes=eval(axes)
            if type(axes)==list:
                if len(axes)>=2:
                    x=self.fit.params['output_params'][txt][axes[0]]
                    y=self.fit.params['output_params'][txt][axes[1]]
                    try:
                        yerr=self.fit.params['output_params'][txt][axes[2]]
                    except:
                        yerr=None
                    self.extra_param_1DplotWidget.add_data(x=x,y=y,yerr=yerr,name=txt,fit=True)
                    if 'names' in self.fit.params['output_params'][txt]:
                        self.extra_param_1DplotWidget.setXLabel(self.fit.params['output_params'][txt]['names'][0])
                        self.extra_param_1DplotWidget.setYLabel(self.fit.params['output_params'][txt]['names'][1])
                    fdata.append(txt)
        self.extra_param_1DplotWidget.Plot(fdata)
        self.gen_param_items=self.genParamListWidget.selectedItems()
        # pg.QtGui.QApplication.processEvents()
        pg.QtGui.QApplication.processEvents()

if __name__=='__main__':
    app=pg.QtGui.QApplication(sys.argv)
    w=XAnoS_Fit()
    w.setWindowTitle('XAnoS-Fit')
    screen=QDesktopWidget().screenGeometry()
    w.setGeometry(0,0,screen.width(),screen.height())
    try:
        fname = sys.argv[1]
        w.addData(fnames=[fname])
    except:
        pass
    try:
        pname=sys.argv[2]
        w.loadParameters(fname=pname)
    except:
        pass
    w.showMaximized()
    sys.exit(app.exec_())
        
        
        
    

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
import sys
import tempfile
import os
from Highlighter import Highlighter
import os

class FunctionEditor(QWidget):
    def __init__(self, funcName=None, dirName=None, parent=None):
        """
        funcName         : Class name
        dirName          : Path of the Class file name
        """
        QWidget.__init__(self,parent)
        self.dirName=dirName
        self.curDir=os.getcwd()
        self.create_ui()
        self.fileSaved=True
        self.foundError=True
        if funcName==None:
            self.funcName='tmpxyz'
            self.funcNameLineEdit.setText(self.funcName)
            fh=open('functionTemplate.txt')
            lines=fh.readlines()
            for line in lines:
                if '<*>' in line:
                    line=line.replace('<*>',self.funcName)
                self.funcTextEdit.appendPlainText(line.rstrip())
        else:
            self.funcName=funcName
            self.funcNameLineEdit.setText(self.funcName)
            fh=open(os.path.join(self.dirName,self.funcName+'.py'),'r')
            lines=fh.readlines()
            for line in lines:
                self.funcTextEdit.appendPlainText(line.rstrip())
        self.funcTextEdit.cursorPositionChanged.connect(self.cursorPositionChanged)
        self.cursorPositionChanged()
        self.funcTextEdit.textChanged.connect(self.textChanged)
        self.open=True
        
    def closeEvent(self,evt):
        self.open=False
        
    def create_ui(self):
        self.vblayout=QVBoxLayout(self)
        
        self.parSplitter=QSplitter(Qt.Vertical)
        
        self.funcLayoutWidget=pg.LayoutWidget()
        row=0
        col=0
        funcNameLabel=QLabel('Function name')
        self.funcLayoutWidget.addWidget(funcNameLabel,row=row,col=col)
        col+=1
        self.funcNameLineEdit=QLineEdit()
        self.funcNameLineEdit.returnPressed.connect(self.funcNameChanged)
        self.funcLayoutWidget.addWidget(self.funcNameLineEdit,row=row,col=col,colspan=2)
        col+=2
        self.replaceTabButton=QPushButton('Replace tabs')
        self.replaceTabButton.clicked.connect(self.replaceTabWithSpaces)
        self.funcLayoutWidget.addWidget(self.replaceTabButton,row=row,col=col)
                
        row+=1
        col=0
        self.funcTextEdit=QPlainTextEdit()
        self.funcTextEdit.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.funcLayoutWidget.addWidget(self.funcTextEdit,row=row,col=col,colspan=4)
        self.highlighter=Highlighter(self.funcTextEdit.document())
        self.funcTextEdit.setTabStopWidth(16)
        
        row+=1
        col=0
        self.cursorPositionLabel=QLabel()
        self.cursorPositionLabel.setAlignment(Qt.AlignCenter)
        self.funcLayoutWidget.addWidget(self.cursorPositionLabel,row=row,col=col,colspan=4)
        
        self.parSplitter.addWidget(self.funcLayoutWidget)
        
        self.debugLayoutWidget=pg.LayoutWidget()
        row+=1
        col=0
        checkRunLabel=QLabel('Check/Run results')
        self.debugLayoutWidget.addWidget(checkRunLabel,row=row,col=col)
        
        row+=1
        col=0
        self.debugTextEdit=QPlainTextEdit()
        self.debugTextEdit.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.debugLayoutWidget.addWidget(self.debugTextEdit,row=row,col=col,colspan=4)
        
        row+=1
        col=0
        self.testPushButton=QPushButton('Test function')
        self.testPushButton.clicked.connect(self.testFunction)
        self.debugLayoutWidget.addWidget(self.testPushButton,row=row,col=col)
        col+=1
        self.runPushButton=QPushButton('Run function')
        self.runPushButton.clicked.connect(self.runFunction)
        self.debugLayoutWidget.addWidget(self.runPushButton,row=row,col=col)
        col+=1
        self.savePushButton=QPushButton('Save function')
        self.savePushButton.clicked.connect(self.saveFunction)
        self.debugLayoutWidget.addWidget(self.savePushButton,row=row,col=col)
        col+=1
        self.closeEditorButton=QPushButton('Close Editor')
        self.closeEditorButton.clicked.connect(self.closeEditor)
        self.debugLayoutWidget.addWidget(self.closeEditorButton,row=row,col=col)
        
        self.parSplitter.addWidget(self.debugLayoutWidget)
        
        self.vblayout.addWidget(self.parSplitter)
        
    def cursorPositionChanged(self):
        self.cursor=self.funcTextEdit.textCursor()
        self.cursorPositionLabel.setText('Line: %d, Column: %d'%(self.cursor.blockNumber()+1,self.cursor.columnNumber()+1))
        
    def funcNameChanged(self):
        fname=self.funcNameLineEdit.text()
        text=self.funcTextEdit.toPlainText().replace(self.funcName,fname)
        self.funcTextEdit.clear()
        self.funcTextEdit.setPlainText(text)
        self.funcName=fname
        
    def textChanged(self):
        number=self.cursor.blockNumber()
        doc=self.funcTextEdit.document()
        txt=doc.findBlockByLineNumber(number).text()
        if 'class' in txt:
            fname=txt.split(':')[0].split()[1]
            self.funcNameLineEdit.setText(fname)
        self.fileSaved=False
        
        
    def testFunction(self):
        self.debugTextEdit.clear()
        if self.funcNameLineEdit.text()!='':
            fobj=tempfile.NamedTemporaryFile(mode='w')
            fdir=os.path.dirname(fobj.name)
            fobj.close()
            fname=os.path.join(fdir,self.funcName)+'.py'
            fh=open(fname,'w')
            fh.write(self.funcTextEdit.toPlainText()+'\n')
            fh.close()
            self.process=QProcess()
            self.foundError=False
            self.process.readyReadStandardOutput.connect(self.readTestOutput)
            self.process.start('pylint -E '+fname)
            self.process.finished.connect(self.finishedTesting)
            
    def replaceTabWithSpaces(self):
        text=self.funcTextEdit.toPlainText()
        text=text.replace('\t','    ')        
        self.funcTextEdit.textChanged.disconnect(self.textChanged)
        self.funcTextEdit.clear()
        self.funcTextEdit.appendPlainText(text)
        self.funcTextEdit.textChanged.connect(self.textChanged)
            
    def finishedTesting(self):
        self.debugTextEdit.appendPlainText('****************No more errors*************** ')
            
            
    def readTestOutput(self):
        output=str(self.process.readAllStandardOutput())
        outputs=output[2:-1].split('\\n')
        for text in outputs:
            self.debugTextEdit.appendPlainText(text)
        
    def runFunction(self):
        self.debugTextEdit.clear()
        if self.funcNameLineEdit.text()!='' and not self.foundError:
            fobj=tempfile.NamedTemporaryFile(mode='w')
            fdir=os.path.dirname(fobj.name)
            fobj.close()
            fname=os.path.join(fdir,self.funcName)+'.py'
            fh=open(fname,'w')
            fh.write(self.funcTextEdit.toPlainText()+'\n')
            fh.close()
            self.process=QProcess()
            self.process.readyReadStandardOutput.connect(self.readRunOutput)
            self.process.start('python -E '+fname)
            self.process.finished.connect(self.finishRunning)
        else:
            QMessageBox.warning(self,'Error','Please check for syntax error in the function',QMessageBox.Ok)
            
    def readRunOutput(self):
        output=str(self.process.readAllStandardOutput())
        outputs=output[2:-1].split('\\n')
        for text in outputs:
            self.debugTextEdit.appendPlainText(text)
            
    def finishRunning(self):
        self.debugTextEdit.appendPlainText('Finished running!')
        
        
    def saveFunction(self):
        if not self.foundError:
            if self.dirName is None:
                self.dirName=QFileDialog.getExistingDirectory(self,'Directory to save the function',self.curDir,QFileDialog.ShowDirsOnly)
            fname=os.path.join(self.dirName,self.funcNameLineEdit.text()+'.py')
            if os.path.exists(fname):
                ans=QMessageBox.question(self,'Confirmation','Do you really like to replace the existing function with the new one?',QMessageBox.No,QMessageBox.Yes)
                if ans==QMessageBox.Yes:
                    fh=open(fname,'w')
                    fh.write(self.funcTextEdit.toPlainText()+'\n')
                    fh.close()
                    self.fileSaved=True
            else:
                fh=open(fname,'w')
                fh.write(self.funcTextEdit.toPlainText()+'\n')
                fh.close()
                self.fileSaved=True
        else:
            QMessageBox.warning(self,'Save error','Please test the function before saving',QMessageBox.Ok)
        
    def closeEditor(self):
        if self.fileSaved:
            self.close()
        else:
            ans=QMessageBox.question(self,'File modified','The file has been modified since you last saved it. Do you like to save before closing?',QMessageBox.Yes, QMessageBox.No)
            if ans==QMessageBox.Yes:
                self.close()
        
            
            
        


if __name__=='__main__':
    app=QApplication(sys.argv)
    w=FunctionEditor()
    w.setWindowTitle('Function Editor')
    w.setGeometry(0,0,1000,800)
    
    w.show()
    sys.exit(app.exec_())
        
                
        

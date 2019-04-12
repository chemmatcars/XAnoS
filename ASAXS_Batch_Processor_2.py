from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog
from PyQt5.QtGui import QDoubleValidator, QIntValidator
import sys
from readData import average1DSAXS, interpolate_data, read1DSAXS, bkgSub1DSAXS
import copy
import numpy as np
from calc_cf import calc_cf
import os
import time

class ASAXS_Batch_Processor(QWidget):
    """
    """
    def __init__(self,parent=None):
        QWidget.__init__(self, parent = None)
        loadUi('UI_Forms/ASAXS_Batch_Processor_2.ui',self)
        self.open_settings()
        self.initUI()
        self.init_signals()


        
    def initUI(self):
        """
        initialize the GUI components
        """
        self.sampleFileName = self.sampleFileNameLineEdit.text()
        self.doubleValidator = QDoubleValidator()
        self.integerValidator = QIntValidator()
        if self.sampleFileName == '':
            self.sampleFileName = None
        self.firstSampleNumChanged()
        self.firstBkgNumLineEdit.setValidator(self.integerValidator)
        self.firstStdNumLineEdit.setValidator(self.integerValidator)
        self.firstBkgNumChanged()
        self.firstStdNumChanged()
        self.sampleThicknessLineEdit.setValidator(self.doubleValidator)
        self.bkgThicknessLineEdit.setValidator(self.doubleValidator)
        self.stdThicknessLineEdit.setValidator(self.doubleValidator)
        self.sampleThickness = float(self.sampleThicknessLineEdit.text())
        self.bkgThickness = float(self.bkgThicknessLineEdit.text())
        self.energyNpts = self.energyNptsSpinBox.value()
        self.repeatNpts = self.repeatSpinBox.value()
        self.normStd = self.normStdSampleComboBox.currentText()
        self.stdThickness = float(self.stdThicknessLineEdit.text())
        self.xMinMaxText = self.xMinMaxLineEdit.text()
        self.xMin, self.xMax = list(map(float, self.xMinMaxText.split(':')))
        self.interpType = self.interpComboBox.currentText()
        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)

    def init_signals(self):
        """
        Initialize signals
        :return:
        """
        self.selectFileNamePushButton.clicked.connect(self.openSampleFname)
        self.firstSampleNumsLineEdit.returnPressed.connect(self.firstSampleNumChanged)
        self.firstSampleNumsLineEdit.textEdited.connect(self.firstSampleNumChanged)
        self.firstBkgNumLineEdit.returnPressed.connect(self.firstBkgNumChanged)
        self.firstBkgNumLineEdit.textEdited.connect(self.firstBkgNumChanged)
        self.firstStdNumLineEdit.returnPressed.connect(self.firstStdNumChanged)
        self.firstStdNumLineEdit.textEdited.connect(self.firstStdNumChanged)
        self.sampleThicknessLineEdit.returnPressed.connect(self.sampleThicknessChanged)
        self.sampleThicknessLineEdit.textEdited.connect(self.sampleThicknessChanged)
        self.stdThicknessLineEdit.returnPressed.connect(self.stdThicknessChanged)
        self.stdThicknessLineEdit.textEdited.connect(self.stdThicknessChanged)
        self.bkgThicknessLineEdit.returnPressed.connect(self.bkgThicknessChanged)
        self.bkgThicknessLineEdit.textEdited.connect(self.bkgThicknessChanged)
        self.energyNptsSpinBox.valueChanged.connect(self.energyNptsChanged)
        self.repeatSpinBox.valueChanged.connect(self.repeatNptsChanged)
        self.normStdSampleComboBox.currentIndexChanged.connect(self.normStdChanged)
        self.xMinMaxLineEdit.returnPressed.connect(self.xMinMaxChanged)
        self.interpComboBox.currentIndexChanged.connect(self.interpTypeChanged)
        self.processPushButton.clicked.connect(self.process)


    def process(self):
        if self.sampleFileName is not None:
            bg_num = self.bkgNum
            gc_num = self.stdNum
            fdir = os.path.dirname(self.sampleFileName)
            mean_dir = os.path.join(fdir, 'Mean')
            ctimes = self.sampleNumberSpinBox.value() * self.repeatNpts
            print(ctimes)
            data = {}

            if not os.path.exists(mean_dir):
                os.makedirs(os.path.join(fdir, 'Mean'))
            snames = {}
            bnames = {}
            gnames = {}

            self.progressBar.setMaximum(self.energyNpts-1)
            self.progressBar.setMinimum(0)
            self.progressBar.setValue(0)

            outputNames=[]
            self.outputFnames=[]
            for j in range(0, self.energyNpts):
                fnum = []
                for i in range(bg_num + ctimes * j, bg_num + ctimes * j + self.repeatNpts):
                    fnum.append(i)
                    bnames[i] = self.sampleFileName + '%04d.txt' % i
                data, obname = average1DSAXS(self.sampleFileName, num=fnum, delete_prev=False, data=data, extra_key=fnum[0])

                # Calculating mean of GC
                fnum = []
                for i in range(gc_num + ctimes * j, gc_num + ctimes * j + self.repeatNpts):
                    fnum.append(i)
                    gnames[i] = self.sampleFileName + '%04d.txt' % i
                data, ogname = average1DSAXS(self.sampleFileName, num=fnum, delete_prev=False, data=data, extra_key=fnum[0])

                ene, cf, a, b = calc_cf(ogname, standard=self.normStd, thickness=self.stdThickness, xmin=self.xMin, xmax=self.xMax,
                                        interpolation_type=self.interpType)

                # Calculating mean of samples
                for sam_num in self.samNums:
                    fnum = []
                    for i in range(sam_num + ctimes * j, sam_num + ctimes * j + self.repeatNpts):
                        fnum.append(i)
                        snames[i] = self.sampleFileName + '%04d.txt' % i
                    data, ofname = average1DSAXS(self.sampleFileName, num=fnum, delete_prev=False, data=data, extra_key=fnum[0])

                    # Performing background subtraction
                    obsname = os.path.basename(self.sampleFileName + '_%04d_bsub.txt' % fnum[0])

                    bg_factor= self.sampleThickness/self.bkgThickness

                    data, bsfname = bkgSub1DSAXS(data, ofname, data, obname, obsname, thickness= self.sampleThickness, cf=cf,
                                                 bg_factor = bg_factor, norm=1.0, data={})
                    self.plotWidget.add_data(x=data[bsfname]['x'],y=data[bsfname]['CF']*data[bsfname]['y']/data[bsfname]['Thickness'],\
                                             yerr=data[bsfname]['CF']*data[bsfname]['yerr']/data[bsfname]['Thickness'],name=str(fnum[0])+'_bsub')
                    #self.plotWidget.Plot([str(fnum[0])+'_bsub'])
                    outputNames.append(str(fnum[0])+'_bsub')
                    self.outputFnames.append(bsfname)
                    self.progressBar.setValue(j)
                    self.plotWidget.Plot(outputNames)
                    QApplication.processEvents()
            self.data=data
        else:
            QMessageBox.warning(self,'File Error','Please select first sample file',QMessageBox.Ok)

    def openSampleFname(self):
        fname=QFileDialog.getOpenFileName(caption='Select sample file name',filter="Sample Files (*.txt)")[0]
        self.sampleFileNameLineEdit.setText(fname[:-9])
        self.sampleNameChanged()

    def firstSampleNumChanged(self):
        txt=self.firstSampleNumsLineEdit.text().replace(" ","")
        try:
            samNums=list(map(int, txt.split(",")))
            if all(isinstance(x, int) for x in samNums):
                self.samNums=samNums
            else:
                QMessageBox.warning(self,
                                    'Please provide integer values and if multiple seperate them by commas in between',\
                                    QMessageBox.Ok)
                self.samNums=1
                self.firstSampleNumsLineEdit.setText('1')
            self.save_settings()
        except:
            pass

    def firstBkgNumChanged(self):
        try:
            bkgNum = int(self.firstBkgNumLineEdit.text())
            if bkgNum in self.samNums:
                response = QMessageBox.question(self, 'As this number also exists as sample number, are you sure this number\
                 belongs to backgroud?', QMessageBox.Yes, QMessageBox.No)
                if response == QMessageBox.Yes:
                    self.bkgNum = bkgNum
                else:
                    self.firstBkgNumLineEdit.setText(str(self.bkgNum))
            else:
                self.bkgNum = bkgNum
            self.save_settings()
        except:
            pass

    def firstStdNumChanged(self):
        try:
            stdNum = int(self.firstStdNumLineEdit.text())
            if stdNum in self.samNums or stdNum==self.bkgNum:
                response = QMessageBox.question(self, 'As this number also exists as sample number, are you sure this number\
                 belongs to background?', QMessageBox.Yes, QMessageBox.No)
                if response == QMessageBox.Yes:
                    self.stdNum = stdNum
                else:
                    self.firstStdNumLineEdit.setText(str(self.stdNum))
            else:
                self.stdNum = stdNum
            self.save_settings()
        except:
            pass

    def sampleNameChanged(self):
        self.sampleFileName = self.sampleFileNameLineEdit.text()
        if self.sampleFileName == '':
            self.sampleFileName = None

    def sampleThicknessChanged(self):
        self.sampleThickness= float(self.sampleThicknessLineEdit.text())
        self.save_settings()

    def bkgThicknessChanged(self):
        self.bkgThickness= float(self.bkgThicknessLineEdit.text())
        self.save_settings()

    def stdThicknessChanged(self):
        self.stdThickness = float(self.stdThicknessLineEdit.text())
        self.save_settings()

    def energyNptsChanged(self):
        self.energyNpts = self.energyNptsSpinBox.value()
        self.save_settings()

    def repeatNptsChanged(self):
        self.repeatNpts = self.repeatSpinBox.value()
        self.save_settings()

    def normStdChanged(self):
        self.normStd = self.normStdSampleComboBox.currentText()
        self.save_settings()

    def xMinMaxChanged(self):
        self.xMinMaxText = self.xMinMaxLineEdit.text()
        try:
            self.xMin, self.xMax = list(map(float, self.xMinMaxText.split(':')))
        except:
            self.xMin, self.xMax = 0.0, 1.0
            self.xMinMaxLineEdit.setText('%.1f:%.1f'%self.xMin, self.xMax)
        self.save_settings()

    def interpTypeChanged(self):
        self.interpType=self.interpTypeComboBox.currentText()
        self.save_settings()

    def save_settings(self):
        fh=open('./batch_settings.txt','w+')
        fh.write('samNums='+str(self.samNums)+'\n')
        fh.write('bkgNum='+str(self.bkgNum)+'\n')
        fh.write('stdNum='+str(self.stdNum)+'\n')
        fh.write('sampleThickness='+str(self.sampleThickness)+'\n')
        fh.write('bkgThickness='+str(self.bkgThickness)+'\n')
        fh.write('stdThickness='+str(self.stdThickness)+'\n')
        fh.write('normStd='+self.normStd+'\n')
        fh.write('xMinMax='+self.xMinMaxText+'\n')
        fh.write('interpType='+self.interpType+'\n')
        fh.write('energyNpts='+str(self.energyNpts)+'\n')
        fh.write('repeatNpts='+str(self.repeatNpts))
        fh.close()

    def open_settings(self):
        fh=open('./batch_settings.txt','r')
        lines=fh.readlines()
        fh.close()
        self.samNums=eval(lines[0].strip().split('=')[1])
        samNums=''
        for i in self.samNums:
            samNums+=str(i)+','
        self.firstSampleNumsLineEdit.setText(samNums[:-1])

        self.bkgNum=int(lines[1].strip().split('=')[1])
        self.firstBkgNumLineEdit.setText(str(self.bkgNum))

        self.stdNum=int(lines[2].strip().split('=')[1])
        self.firstStdNumLineEdit.setText(str(self.stdNum))

        self.sampleThickness=float(lines[3].strip().split('=')[1])
        self.sampleThicknessLineEdit.setText(str(self.sampleThickness))

        self.bkgThickness=float(lines[4].strip().split('=')[1])
        self.bkgThicknessLineEdit.setText(str(self.bkgThickness))

        self.stdThickness=float(lines[5].strip().split('=')[1])
        self.stdThicknessLineEdit.setText(str(self.stdThickness))

        self.normStd=lines[6].strip().split('=')[1]
        self.normStdSampleComboBox.setCurrentIndex(self.normStdSampleComboBox.findText(self.normStd))

        self.xMinMaxText=lines[7].strip().split('=')[1]
        self.xMinMaxLineEdit.setText(self.xMinMaxText)
        self.xMin, self.xMax = list(map(float, self.xMinMaxText.split(':')))

        self.interpType=lines[8].strip().split('=')[1]
        self.interpComboBox.setCurrentIndex(self.interpComboBox.findText(self.interpType))

        self.energyNpts=int(lines[9].strip().split('=')[1])
        self.energyNptsSpinBox.setValue(self.energyNpts)

        self.repeatNpts=int(lines[10].strip().split('=')[1])
        self.repeatSpinBox.setValue(self.repeatNpts)


        


if __name__=='__main__':
    app=QApplication(sys.argv)
    w=ASAXS_Batch_Processor()
    w.setWindowTitle('ASAXS Batch Processor 2')
    w.resize(800,600)
    w.show()
    sys.exit(app.exec_())
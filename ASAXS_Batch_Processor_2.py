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
        self.initUI()
        self.init_signals()
        
    def initUI(self):
        """
        initialize the GUI components
        """
        self.sampleFileName = self.sampleFileNameLineEdit.text()
        self.doubleValidator = QDoubleValidator()
        if self.sampleFileName == '':
            self.sampleFileName = None
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
        self.sampleThicknessLineEdit.returnPressed.connect(self.sampleThicknessChanged)
        self.stdThicknessLineEdit.returnPressed.connect(self.stdThicknessChanged)
        self.energyNptsSpinBox.valueChanged.connect(self.energyNptsChanged)
        self.repeatSpinBox.valueChanged.connect(self.repeatNptsChanged)
        self.normStdSampleComboBox.currentIndexChanged.connect(self.normStdChanged)
        self.xMinMaxLineEdit.returnPressed.connect(self.xMinMaxChanged)
        self.interpComboBox.currentIndexChanged.connect(self.interpTypeChanged)
        self.processPushButton.clicked.connect(self.process)

    def process(self):
        if self.sampleFileName is not None:
            sam_num = 1
            bg_num = sam_num + self.repeatNpts
            gc_num = bg_num + self.repeatNpts
            fdir = os.path.dirname(self.sampleFileName)
            mean_dir = os.path.join(fdir, 'Mean')
            ctimes = 3 * self.repeatNpts
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

                # Calculating mean of sample
                fnum = []
                for i in range(sam_num + ctimes * j, sam_num + ctimes * j + self.repeatNpts):
                    fnum.append(i)
                    snames[i] = self.sampleFileName + '%04d.txt' % i
                data, ofname = average1DSAXS(self.sampleFileName, num=fnum, delete_prev=False, data=data, extra_key=fnum[0])

                # Performing background subtraction
                obsname = os.path.basename(self.sampleFileName + '_%04d_bsub.txt' % fnum[0])

                data, bsfname = bkgSub1DSAXS(data, ofname, data, obname, obsname, thickness= self.sampleThickness, cf=cf,
                                             bg_factor = self.sampleThickness / self.bkgThickness, norm=1.0)
                self.plotWidget.add_data(x=data[bsfname]['x'],y=data[bsfname]['CF']*data[bsfname]['y'],yerr=data[bsfname]['CF']*data[bsfname]['yerr'],name=str(fnum[0])+'_bsub')
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

    def sampleNameChanged(self):
        self.sampleFileName = self.sampleFileNameLineEdit.text()
        if self.sampleFileName == '':
            self.sampleFileName = None

    def sampleThicknessChanged(self):
        self.sampleThickness= float(self.sampleThicknessLineEdit.text())

    def stdThicknessChanged(self):
        self.stdThickness = float(self.stdThicknessLineEdit.text())

    def energyNptsChanged(self):
        self.energyNpts = self.energyNptsSpinBox.value()

    def repeatNptsChanged(self):
        self.repeatNpts = self.repeatSpinBox.value()

    def normStdChanged(self):
        self.normStd = self.normStdSampleComboBox.currentText()

    def xMinMaxChanged(self):
        self.xMinMaxText = self.xMinMaxLineEdit.text()
        try:
            self.xMin, self.xMax = list(map(float, self.xMinMaxText.split(':')))
        except:
            self.xMin, self.xMax = 0.0, 1.0
            self.xMinMaxLineEdit.setText('%.1f:%.1f'%self.xMin, self.xMax)

    def interpTypeChanged(self):
        self.interpType=self.interpTypeComboBox.currentText()

        


if __name__=='__main__':
    app=QApplication(sys.argv)
    w=ASAXS_Batch_Processor()
    w.setWindowTitle('ASAXS Batch Processor 2')
    w.resize(800,600)
    w.show()
    sys.exit(app.exec_())
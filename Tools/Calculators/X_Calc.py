from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QMainWindow, QFileDialog, QDialog, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt, QRegExp
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont, QRegExpValidator
from PyQt5.QtTest import QTest
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import re
import scipy.constants
from xraydb import XrayDB
xdb = XrayDB()


class PlotDialog(QDialog):
    def __init__(self,parent):
        QDialog.__init__(self,parent)
        loadUi('./Tools/Calculators/UI_Forms/mplPlot.ui',self)


class XCalc(QMainWindow):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi('./Tools/Calculators/UI_Forms/X_Calc.ui', self)


        #font=QFont('Monospace')
        #font.setStyleHint(QFont.TypeWriter)
        #font.setPointSize(8)
        #self.resultTextEdit.setCurrentFont(font)
        #self.resultTextBrowser.setCurrentFont(font)


        self.initParameters()
        self.initSignals()
        self.initValidator()

       # self.enableButtons(enable=False)


    # def enableButtons(self,enable=True):
    #     #Disabling some of the buttons to start with
    #     self.addFilterPushButton.setEnabled(enable)
    #     self.saveFilterPushButton.setEnabled(enable)
    #     self.loadFilterPushButton.setEnabled(enable)
    #     self.duplicatePushButton.setEnabled(enable)
    #     self.blsPushButton.setEnabled(enable)
    #     self.upPushButton.setEnabled(enable)
    #     self.downPushButton.setEnabled(enable)
    #     self.removePushButton.setEnabled(enable)
    #     self.calPushButton.setEnabled(enable)
    #     self.exportStatPushButton.setEnabled(enable)
    #     self.exportDataPushButton.setEnabled(enable)
    #     self.plotStatPushButton.setEnabled(enable)
    #

    def initParameters(self):
        self.eleraius = scipy.constants.physical_constants["classical electron radius"][0]*1e10   # in unit of \AA
        self.avoganum = scipy.constants.Avogadro
        self.etolam = scipy.constants.c*scipy.constants.Planck/scipy.constants.eV*1e7   # energy in keV, wavelength in \AA
        self.parseFormula()
        #print(self.formula)
        self.massden = float(self.massdenLE.text())
        self.xrayeng = float(self.xenLE.text())
        self.plotDlg = PlotDialog(self)
        self.updateCal()

    def initSignals(self):
        self.chemforLE.returnPressed.connect(self.updateFormula)
        self.massdenLE.returnPressed.connect(self.updateMassDen)
        self.xenLE.returnPressed.connect(self.updateXrayEng)
        self.attfacCB.currentIndexChanged.connect(lambda x: self.calAbsLength(energy=self.xrayeng))
        self.plotPB.clicked.connect(self.updatePlot)
        self.plotDlg.closePB.clicked.connect(self.plotDlg.done)
        self.plotDlg.dataPB.clicked.connect(self.saveData)

    def initValidator(self):
        regex = QRegExp(r'([A-Z][A-Za-z0-9\.]+)|([A-Z])')
        validator = QRegExpValidator(regex)
        self.chemforLE.setValidator(validator)

        doubleValidator = QDoubleValidator()
        self.massdenLE.setValidator(doubleValidator)
        self.xenLE.setValidator(doubleValidator)
        self.eminLE.setValidator(doubleValidator)
        self.emaxLE.setValidator(doubleValidator)

        intValidator = QIntValidator()
        self.numpointLE.setValidator(intValidator)

    def updateFormula(self):
        self.parseFormula()
        self.validateFormula()
        if self.validate==1:
            self.messageBox('Warning: Please input a valid chemical formula!\n Example:Al2O3')
        else:
           # print(self.formula)
            self.massden = xdb.density(list(self.formula.keys())[0])
           # print(self.massden)
            self.massdenLE.setText(str(self.massden))
            self.updateCal()

    def parseFormula(self):
        a = re.findall(r'[A-Z][a-z]?|[0-9]+[.][0-9]+|[0-9]+', self.chemforLE.text())
        if not a[-1].replace('.', '').isdigit():
            a.append('1')
        formula = {}
        i = 1
        while i <= len(a):
            if not a[i].replace('.', '').isdigit():
                a.insert(i, '1')
            if a[i - 1] in formula.keys():
                formula[a[i - 1]] = float(a[i]) + formula[a[i - 1]]
            else:
                formula[a[i - 1]] = float(a[i])
            i += 2
        self.formula=formula

    def validateFormula(self):
        try:
            a=np.sum([xdb.molar_mass(key) for key in self.formula.keys()])
            self.validate=0
        except:
            self.validate=1

    def updateMassDen(self):
        self.massden = float(self.massdenLE.text())
        self.updateCal()

    def updateXrayEng(self):
        self.xrayeng = float(self.xenLE.text())
        self.updateCal()


    def updateCal(self):
        self.calMolarMass()
        self.calAbsLength(energy=self.xrayeng)
        self.calCriAng(energy=self.xrayeng)

    def calMolarMass(self):
        self.molarmass=np.sum([xdb.molar_mass(key)*self.formula[key] for key in self.formula.keys()])
        self.molarmassLabel.setText(str(self.molarmass))
        self.massratio={}
        for key in self.formula.keys():
            self.massratio[key]=xdb.molar_mass(key)*self.formula[key]/self.molarmass

    def updateAttFac(self):
        self.calAbsLength(energy=self.xrayeng)

    def calAbsLength(self, energy=None):
        if type(energy) == float:
            tot_mu = np.sum([xdb.mu_elam(key, energy * 1000) * self.massratio[key] * self.massden for key in self.massratio.keys()])
        else:
            tot_mu=[np.sum([xdb.mu_elam(key, e*1000)*self.massratio[key]*self.massden for key in self.massratio.keys()]) for e in energy]
        self.abslength = 10000/np.array(tot_mu)
        self.attfact = np.exp(float(self.attfacCB.currentText())/self.abslength)
       # print(self.abslength, self.attfact)
        if type(energy) == float:
            self.abslenLabel.setText(format(self.abslength, '.4f'))
            self.attLabel.setText(format(self.attfact, '.4f'))

    def calCriAng(self, energy=None):
        self.molarele = np.sum([xdb.atomic_number(key)*self.formula[key] for key in self.formula.keys()])
        self.eleden = self.massden/self.molarmass*self.molarele*self.avoganum/1e24
        self.qc = 4*np.sqrt(np.pi*self.eleraius*self.eleden)
        energyarray=np.array(energy)
        self.wavelength = self.etolam/energyarray
        self.criangrad = np.arcsin(self.qc*self.wavelength/4/np.pi)
        self.criangdeg = np.rad2deg(self.criangrad)
        #print(self.wavelength)
        if type(energy) == float:
            self.criangmradLabel.setText(format(self.criangrad * 1000, '.4f'))
            self.criangdegLabel.setText(format(self.criangdeg, '.4f'))
        #print(self.qc, self.eleraius, self.eleden)

    # def updatePlot(self):
    #     xmin = float(self.eminLE.text())
    #     xmax = float(self.emaxLE.text())
    #     numpoint = int(self.numpointLE.text())
    #     plt.xlabel("X-ray Energy (keV)")
    #     plt.ylabel(str(self.yaxisCB.currentText()))
    #     title="Chemical Formula: " + str(self.chemforLE.text()) + "; Mass Density: " + str(self.massden) +" g/ml"
    #     if xmin < xmax and numpoint > 1:
    #         x=np.linspace(xmin, xmax, numpoint)
    #         if self.yaxisCB.currentIndex() == 0:
    #             self.calAbsLength(energy=x)
    #             y = list(self.abslength)
    #         elif self.yaxisCB.currentIndex() == 1:
    #             self.calAbsLength(energy=x)
    #             y = list(self.attfact)
    #             title += "\nThickness "+ str(self.attfacCB.currentText())+" um"
    #         elif self.yaxisCB.currentIndex() == 2:
    #             self.calCriAng(energy=x)
    #             y = list(self.criangdeg)
    #         elif self.yaxisCB.currentIndex() == 3:
    #             self.calCriAng(energy = x)
    #             y = list(self.criangrad*1000)
    #         plt.plot(x, y)
    #         plt.title(title)
    #         plt.show()
    #     else:
    #         self.messageBox("Warning: Max energy has to be larger than min energy!\n and number of points has to be larger than 2!")

    def updatePlot(self):
        self.xmin = float(self.eminLE.text())
        self.xmax = float(self.emaxLE.text())
        self.numpoint = int(self.numpointLE.text())
        if self.xmin < self.xmax and self.numpoint > 1:
            self.plotDlg.show()
            self.showPlot()
        else:
            self.messageBox(
                "Warning: Max energy has to be larger than min energy!\n and number of points has to be larger than 2!")


    def showPlot(self):
        self.plotDlg.mplWidget.canvas.figure.clear()
        self.plotAxes = self.plotDlg.mplWidget.figure.add_subplot(111)
        title = "Chemical Formula: " + str(self.chemforLE.text()) + "; Mass Density: " + str(self.massden) + " g/ml"
        self.datax=np.linspace(self.xmin, self.xmax, self.numpoint)
        if self.yaxisCB.currentIndex() == 0:
            self.calAbsLength(energy=self.datax)
            self.datay = list(self.abslength)
        elif self.yaxisCB.currentIndex() == 1:
            self.calAbsLength(energy=self.datax)
            self.datay = list(self.attfact)
            title += "\nThickness "+ str(self.attfacCB.currentText())+" um"
        elif self.yaxisCB.currentIndex() == 2:
            self.calCriAng(energy=self.datax)
            self.datay = list(self.criangdeg)
        elif self.yaxisCB.currentIndex() == 3:
            self.calCriAng(energy = self.datax)
            self.datay = list(self.criangrad*1000)
        self.plotAxes.set_xlabel("X-ray Energy (keV)")
        self.plotAxes.set_ylabel(str(self.yaxisCB.currentText()))
        self.plotAxes.set_title(title)
        self.plotAxes.plot(self.datax, self.datay)
        self.plotDlg.mplWidget.canvas.figure.tight_layout()
        self.plotDlg.mplWidget.canvas.draw()
        self.plotDlg.dataTB.clear()
        datainfo = "X\tY\n"
        for i in range(len(self.datax)):
            datainfo = datainfo + format(self.datax[i], '.3f')+'\t'+format(self.datay[i], '.4f')+'\n'
        self.plotDlg.dataTB.append(datainfo)
        cursor = self.plotDlg.dataTB.textCursor()
        cursor.setPosition(0)
        self.plotDlg.dataTB.setTextCursor(cursor)


    def saveData(self):
        self.saveFileName = str(QFileDialog.getSaveFileName(caption='Save Data')[0])
        fid = open(self.saveFileName+'.txt', 'w')
        fid.write('# X-ray Energy (keV)\t' + str(self.yaxisCB.currentText()) + '\n')
        for i in range(len(self.datax)):
            fid.write(format(self.datax[i], '.3f')+'\t\t\t'+format(self.datay[i], '.4f')+'\n')
        fid.close()

    def messageBox(self,text,title='Warning'):
        mesgbox=QMessageBox()
        mesgbox.setText(text)
        mesgbox.setWindowTitle(title)
        mesgbox.exec_()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = XCalc()
    w.setWindowTitle('X-ray Calculator')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())
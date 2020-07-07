from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QMainWindow, QFileDialog, QDialog, QInputDialog, QTableWidgetItem, QLineEdit
from PyQt5.QtCore import pyqtSignal, Qt, QRegExp
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont, QRegExpValidator
from PyQt5.QtTest import QTest
import sys
import os
import numpy as np
import re
import scipy.constants
from xraydb import XrayDB
xdb = XrayDB()




class XCalc(QMainWindow):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi('./Tools/Calculators/UI_Forms/Den_Calc.ui', self)


        #font=QFont('Monospace')
        #font.setStyleHint(QFont.TypeWriter)
        #font.setPointSize(8)
        #self.resultTextEdit.setCurrentFont(font)
        #self.resultTextBrowser.setCurrentFont(font)


        self.initParameters()
        self.initSignals()
        self.initValidator()
        self.eledenLabel.setText('e/'+u'\u212b'+u'\u00b3')

        self.createTW()
        self.updateCal()


    def initParameters(self):
        self.avoganum = scipy.constants.Avogadro


    def initSignals(self):
        self.updatePB.clicked.connect(self.updateCal)
        self.addPB.clicked.connect(self.addCom)
        self.removePB.clicked.connect(self.rmCom)

    def initValidator(self):
        regex = QRegExp(r'[A-Za-z0-9\.]+')
        posfloat = QRegExp(r'^(([0-9]+(?:\.[0-9]+)?)|([0-9]*(?:\.[0-9]+)?))$')
        self.validator = QRegExpValidator(regex)

        self.posValidator = QRegExpValidator(posfloat)
        self.doubleValidator = QDoubleValidator(bottom=0)
        self.bulkconLE.setValidator(self.doubleValidator)

    # def updateFormula(self):
    #     self.parseFormula()
    #     self.validateFormula()
    #     if self.validate==1:
    #         self.messageBox('Warning: Please input a valid chemical formula!\n Example:Al2O3')
    #     else:
    #        # print(self.formula)
    #         self.massden = xdb.density(list(self.formula.keys())[0])
    #        # print(self.massden)
    #         self.massdenLE.setText(str(self.massden))
    #         self.updateCal()

    def parseFormula(self, chemformula):
        a = re.findall(r'[A-Z][a-z]?|[0-9]+[.][0-9]+|[0-9]+', chemformula)
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
        return formula

    def validateFormula(self, chemformula):
        try:
            a=np.sum([xdb.molar_mass(key) for key in chemformula.keys()])
            return 0
        except:
            return 1

    # def updateMassDen(self):
    #     self.massden = float(self.massdenLE.text())
    #     self.updateCal()

    # def updateXrayEng(self):
    #     self.xrayeng = float(self.xenLE.text())
    #     self.updateCal()

    def createTW(self):  # create a TW with validator
        self.subphaseTW.setRowCount(2)
        self.subphaseTW.setColumnCount(3)
        self.subphaseTW.setHorizontalHeaderLabels(['Component', 'Composition', 'Radius' + ' (' + u'\u212b' + ')'])
        for j in range(3):
            self.subphaseTW.setItem(0,j, QTableWidgetItem(''))
            lineedit=QLineEdit('Sr/1/1.25'.split('/')[j], parent=self)
            if j!=0:
                lineedit.setValidator(self.doubleValidator)
            else:
                lineedit.setValidator(self.validator)
            self.subphaseTW.setCellWidget(0,j,lineedit)
        self.setTW(1)

    def setTW(self,row):
        for j in range(3):
            self.subphaseTW.setItem(row,j,QTableWidgetItem(''))
            lineedit=QLineEdit('Cl/2/1.80'.split('/')[j], parent=self)
            if j!=0:
                lineedit.setValidator(self.doubleValidator)
            else:
                lineedit.setValidator(self.validator)
            self.subphaseTW.setCellWidget(row,j,lineedit)


    def addCom(self):  # add one component in the subphase
        rows = self.subphaseTW.rowCount()
        self.subphaseTW.insertRow(rows)
        self.setTW(rows)
        # for i in range(3):
        #         self.subphaseTW.setItem(rows,i, QTableWidgetItem(('Cl/2/1.80'.split('/')[i])))




    def rmCom(self):  # remove one component in the subphase
        rmrows = self.subphaseTW.selectionModel().selectedRows()
        removerows = []
        for rmrow in rmrows:
            removerows.append(self.subphaseTW.row(self.subphaseTW.itemFromIndex(rmrow)))
        removerows.sort(reverse=True)
        if len(removerows) == 0:
            self.messageBox('Warning:: No row is selected!!')
        else:
            for i in range(len(removerows)):
                self.subphaseTW.removeRow(removerows[i])




    def updateCal(self):
        self.checkemptyinput()
        #print(self.bulkconLE.text())
        self.bulkcon = float(self.bulkconLE.text())
        chemfor=[]
        composition=[]
        radius=[]
        validator=[]
        volume=0
        for i in range(self.subphaseTW.rowCount()):
            chemfor.append(self.parseFormula(str(self.subphaseTW.cellWidget(i,0).text())))
            validator.append(self.validateFormula(chemfor[i]))
            composition.append(float(self.subphaseTW.cellWidget(i,1).text()))
            radius.append(float(self.subphaseTW.cellWidget(i,2).text()))
        #print(chemfor, composition, radius, validator)
        if np.sum(np.array(validator))==0:
            totalformula={}
            for i in range(self.subphaseTW.rowCount()):
                volume=volume+composition[i]*pow(radius[i],3)
                for j in range(len(chemfor[i])):  # merge components at all rows.
                    key=list(chemfor[i].keys())[j]
                    if key in totalformula:
                        totalformula[key]=totalformula[key]+ chemfor[i][key]*composition[i]*self.bulkcon
                    else:
                        totalformula[key] = chemfor[i][key]*composition[i]*self.bulkcon
            #print(totalformula)

            totalvolume=volume*self.bulkcon/1000*self.avoganum*1e-27*4/3*np.pi  #total volume of all components in unit of liter
            watervolume=1-totalvolume   #water volume in unit of liter
            watermolar=watervolume*997/18.01528  #molar number of water use 0.997 as the mass density of water at RT

            # add H2O into total formula
            if 'H' in totalformula:
                totalformula['H']=totalformula['H']+watermolar*2000
            else:
                totalformula['H'] = watermolar * 2000
            if 'O' in totalformula:
                totalformula['O']=totalformula['O']+watermolar*1000
            else:
                totalformula['O'] = watermolar*1000

            chemstr=self.formStr(totalformula)
            molarmass = np.sum([xdb.molar_mass(key) * totalformula[key] for key in totalformula.keys()])/1e6
            self.chemforLE.setText(chemstr)
            self.massdenLE.setText(str(format(molarmass,'.4f')))
            #print(molarmass)
            #print(chemstr)
            #print(totalformula)
            #print(self.parseFormula(chemstr))
            eleden = np.sum([xdb.atomic_number(key) * totalformula[key] for key in totalformula.keys()])/1000*self.avoganum/1e27
            self.eledenLE.setText(str(format(eleden,'.4f')))
            #print(self.eleden)

        else:
            rows=', '.join(map(str, list(np.where(np.array(validator)==1)[0]+1)))
            self.messageBox('Warning: Please input a valid chemical formula in row '+rows+'!\nExample:\tAl2O3')
            self.chemforLE.setText('N/A')
            self.massdenLE.setText('N/A')
            self.eledenLE.setText('N/A')

    def formStr(self, chemfor):
        string=''
        for i in range(len(chemfor)):
            key=list(chemfor.keys())[i]
            if chemfor[key]>0:
                string=string+key+str('{0:.3f}'.format(chemfor[key]).rstrip('0').rstrip('.'))
        return string

    def checkemptyinput(self):
        if self.bulkconLE.text()=='':
            self.bulkconLE.setText('1')
        for i in range(self.subphaseTW.rowCount()):
            if self.subphaseTW.cellWidget(i,0).text()=='':
                self.subphaseTW.cellWidget(i,0).setText('Cl')
            if self.subphaseTW.cellWidget(i,1).text()=='':
                self.subphaseTW.cellWidget(i,1).setText('1')
            if self.subphaseTW.cellWidget(i,2).text()=='':
                self.subphaseTW.cellWidget(i,2).setText('1')




    # def calMolarMass(self):
    #     self.molarmass=np.sum([xdb.molar_mass(key)*self.formula[key] for key in self.formula.keys()])
    #     self.molarmassLabel.setText(str(self.molarmass))
    #     self.massratio={}
    #     for key in self.formula.keys():
    #         self.massratio[key]=xdb.molar_mass(key)*self.formula[key]/self.molarmass
    #
    # def updateAttFac(self):
    #     self.calAbsLength(energy=self.xrayeng)

    # def calAbsLength(self, energy=None):
    #     if type(energy) == float:
    #         tot_mu = np.sum([xdb.mu_elam(key, energy * 1000) * self.massratio[key] * self.massden for key in self.massratio.keys()])
    #     else:
    #         tot_mu=[np.sum([xdb.mu_elam(key, e*1000)*self.massratio[key]*self.massden for key in self.massratio.keys()]) for e in energy]
    #     self.abslength = 10000/np.array(tot_mu)
    #     self.attfact = np.exp(float(self.attfacCB.currentText())/self.abslength)
    #    # print(self.abslength, self.attfact)
    #     if type(energy) == float:
    #         self.abslenLabel.setText(format(self.abslength, '.4f'))
    #         self.attLabel.setText(format(self.attfact, '.4f'))

    # def calCriAng(self, energy=None):
    #     self.molarele = np.sum([xdb.atomic_number(key)*self.formula[key] for key in self.formula.keys()])
    #     self.eleden = self.massden/self.molarmass*self.molarele*self.avoganum/1e24
    #     self.qc = 4*np.sqrt(np.pi*self.eleraius*self.eleden)
    #     energyarray=np.array(energy)
    #     self.wavelength = self.etolam/energyarray
    #     self.criangrad = np.arcsin(self.qc*self.wavelength/4/np.pi)
    #     self.criangdeg = np.rad2deg(self.criangrad)
    #     #print(self.wavelength)
    #     if type(energy) == float:
    #         self.criangmradLabel.setText(format(self.criangrad * 1000, '.4f'))
    #         self.criangdegLabel.setText(format(self.criangdeg, '.4f'))
    #     #print(self.qc, self.eleraius, self.eleden)

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

    # def updatePlot(self):
    #     self.xmin = float(self.eminLE.text())
    #     self.xmax = float(self.emaxLE.text())
    #     self.numpoint = int(self.numpointLE.text())
    #     if self.xmin < self.xmax and self.numpoint > 1:
    #         self.plotDlg.show()
    #         self.showPlot()
    #     else:
    #         self.messageBox(
    #             "Warning: Max energy has to be larger than min energy!\n and number of points has to be larger than 2!")


    # def showPlot(self):
    #     self.plotDlg.mplWidget.canvas.figure.clear()
    #     self.plotAxes = self.plotDlg.mplWidget.figure.add_subplot(111)
    #     title = "Chemical Formula: " + str(self.chemforLE.text()) + "; Mass Density: " + str(self.massden) + " g/ml"
    #     self.datax=np.linspace(self.xmin, self.xmax, self.numpoint)
    #     if self.yaxisCB.currentIndex() == 0:
    #         self.calAbsLength(energy=self.datax)
    #         self.datay = list(self.abslength)
    #     elif self.yaxisCB.currentIndex() == 1:
    #         self.calAbsLength(energy=self.datax)
    #         self.datay = list(self.attfact)
    #         title += "\nThickness "+ str(self.attfacCB.currentText())+" um"
    #     elif self.yaxisCB.currentIndex() == 2:
    #         self.calCriAng(energy=self.datax)
    #         self.datay = list(self.criangdeg)
    #     elif self.yaxisCB.currentIndex() == 3:
    #         self.calCriAng(energy = self.datax)
    #         self.datay = list(self.criangrad*1000)
    #     self.plotAxes.set_xlabel("X-ray Energy (keV)")
    #     self.plotAxes.set_ylabel(str(self.yaxisCB.currentText()))
    #     self.plotAxes.set_title(title)
    #     self.plotAxes.plot(self.datax, self.datay)
    #     self.plotDlg.mplWidget.canvas.figure.tight_layout()
    #     self.plotDlg.mplWidget.canvas.draw()
    #     self.plotDlg.dataTB.clear()
    #     datainfo = "X\tY\n"
    #     for i in range(len(self.datax)):
    #         datainfo = datainfo + format(self.datax[i], '.3f')+'\t'+format(self.datay[i], '.4f')+'\n'
    #     self.plotDlg.dataTB.append(datainfo)
    #     cursor = self.plotDlg.dataTB.textCursor()
    #     cursor.setPosition(0)
    #     self.plotDlg.dataTB.setTextCursor(cursor)


    # def saveData(self):
    #     self.saveFileName = str(QFileDialog.getSaveFileName(caption='Save Data')[0])
    #     fid = open(self.saveFileName+'.txt', 'w')
    #     fid.write('# X-ray Energy (keV)\t' + str(self.yaxisCB.currentText()) + '\n')
    #     for i in range(len(self.datax)):
    #         fid.write(format(self.datax[i], '.3f')+'\t\t\t'+format(self.datay[i], '.4f')+'\n')
    #     fid.close()

    def messageBox(self,text,title='Warning'):
        mesgbox=QMessageBox()
        mesgbox.setText(text)
        mesgbox.setWindowTitle(title)
        mesgbox.exec_()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = XCalc()
    w.setWindowTitle('Subphase Density Calculator')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QMainWindow, QFileDialog, QDialog, QInputDialog, QTableWidgetItem, QLineEdit
from PyQt5.QtCore import pyqtSignal, Qt, QRegExp
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont, QRegExpValidator, QValidator
from PyQt5.QtTest import QTest
import sys
import os
import numpy as np
import re
import scipy.constants
from xraydb import XrayDB
xdb = XrayDB()


class DoubleValidator(QDoubleValidator):
    def __init__(self, parent, bottom=0):
        QDoubleValidator.__init__(self, parent, bottom=bottom)
        self.bottom=bottom

    def validate(self, text, pos):
        try:
            if float(text)>= self.bottom:
                state = QDoubleValidator.Acceptable
            else:
                state = QDoubleValidator.Invalid
        except:
            state = QDoubleValidator.Invalid
        return state, text, pos


class RegExpValidator(QRegExpValidator):

    def validate(self, text, pos):
        regex=re.compile('[A-Z][A-Za-z0-9\.]+|[A-Z]')
        if bool(re.match(regex,text)):
            m=regex.match(text)
            if m.end()<len(text):
                state = QRegExpValidator.Invalid
            else:
                state = QRegExpValidator.Acceptable
        else:
            state = QRegExpValidator.Invalid
        return state, text, pos


class XCalc(QMainWindow):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi('./Tools/Calculators/UI_Forms/Den_Calc.ui', self)

        self.initParameters()
        self.initSignals()
        self.initValidator()
        self.eledenLabel.setText('e/'+u'\u212b'+u'\u00b3')

        self.createTW()
        self.updateCal()


    def initParameters(self):
        self.avoganum = scipy.constants.Avogadro


    def initSignals(self):
        self.solchemforLE.returnPressed.connect(self.updateCal)
        self.solmassdenLE.returnPressed.connect(self.updateCal)
        self.bulkconLE.returnPressed.connect(self.updateCal)
        self.addPB.clicked.connect(self.addCom)
        self.removePB.clicked.connect(self.rmCom)


    def initValidator(self):
        regex = QRegExp(r'([A-Z][A-Za-z0-9\.]+)|([A-Z])')
        self.validator = QRegExpValidator(regex)
        self.doubleValidator = QDoubleValidator(bottom=0)

        self.bulkconLE.setValidator(self.doubleValidator)
        self.solmassdenLE.setValidator(self.doubleValidator)
        self.solchemforLE.setValidator(self.validator)

        # validator=DoubleValidator(self.bulkconLE, bottom=0)
        # self.bulkconLE.setValidator(validator)
        # validator=DoubleValidator(self.solmassdenLE, bottom=0)
        # self.solmassdenLE.setValidator(validator)
        # validator=RegExpValidator(self.solchemforLE)
        # self.solchemforLE.setValidator(validator)


    def parseFormula(self, chemformula):
        a = re.findall(r'[A-Za-z][a-z]?|[0-9]+[.][0-9]+|[0-9]+', chemformula)
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


    def createTW(self):  # create a TW with validator
        self.subphaseTW.setRowCount(2)
        self.subphaseTW.setColumnCount(3)
        self.subphaseTW.setHorizontalHeaderLabels(['Component', 'Composition', 'Radius' + ' (' + u'\u212b' + ')'])
        self.twlineedit={}
        for j in range(3):
            self.subphaseTW.setItem(0,j, QTableWidgetItem(''))
            self.twlineedit[(0,j)]=QLineEdit('Sr/1/1.25'.split('/')[j], parent=self)
            self.twlineedit[(0,j)].returnPressed.connect(self.updateCal)
            if j!=0:
                self.twlineedit[(0,j)].setValidator(self.doubleValidator)
            else:
                self.twlineedit[(0,j)].setValidator(self.validator)
            self.subphaseTW.setCellWidget(0,j,self.twlineedit[(0,j)])
        self.setTW(1)

    def setTW(self,row):
        for j in range(3):
            self.subphaseTW.setItem(row,j,QTableWidgetItem(''))
            self.twlineedit[(row,j)]=QLineEdit('Cl/2/1.80'.split('/')[j], parent=self)
            self.twlineedit[(row,j)].returnPressed.connect(self.updateCal)
            if j!=0:
                self.twlineedit[(row,j)].setValidator(self.doubleValidator)
            else:
                self.twlineedit[(row,j)].setValidator(self.validator)
            self.subphaseTW.setCellWidget(row,j,self.twlineedit[(row,j)])


    def addCom(self):  # add one component at the last row
        rows = self.subphaseTW.rowCount()
        self.subphaseTW.insertRow(rows)
        self.setTW(rows)
        self.updateCal()




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
            self.updateCal()




    def updateCal(self):
        self.checkemptyinput()
        self.bulkcon = float(self.bulkconLE.text())
        self.solmassden = float(self.solmassdenLE.text())
        self.solchem = str(self.solchemforLE.text())
        solformula = self.parseFormula(self.solchem)  # solvent formula
        solvalidator = self.validateFormula(solformula)
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
        if np.sum(np.array(validator))+solvalidator==0:
            totalformula={}
            for i in range(self.subphaseTW.rowCount()):
                volume=volume+composition[i]*pow(radius[i],3)
                for j in range(len(chemfor[i])):  # merge components at all rows.
                    key=list(chemfor[i].keys())[j]
                    if key in totalformula:
                        totalformula[key]=totalformula[key]+ chemfor[i][key]*composition[i]*self.bulkcon
                    else:
                        totalformula[key] = chemfor[i][key]*composition[i]*self.bulkcon

            totalvolume=volume*self.bulkcon/1000*self.avoganum*1e-27*4/3*np.pi  #total volume of all components in unit of liter
            solvolume = 1- totalvolume  # solvent volume in unit of liter

            solmolarmass = np.sum([xdb.molar_mass(key) * solformula[key] for key in solformula.keys()])  # molar mass for the solvent
            solmolar = solvolume*self.solmassden/solmolarmass* 1e6  # solvent molarity in mM


            for key in solformula.keys():  #add solvent into the totalformula
                if key in totalformula:
                    totalformula[key]=totalformula[key] + solformula[key]*solmolar
                else:
                    totalformula[key]=solformula[key]*solmolar

            chemstr=self.formStr(totalformula)
            molarmass = np.sum([xdb.molar_mass(key) * totalformula[key] for key in totalformula.keys()])/1e6
            self.chemforLE.setText(chemstr)
            self.massdenLE.setText(str(format(molarmass,'.4f')))
            eleden = np.sum([xdb.atomic_number(key) * totalformula[key] for key in totalformula.keys()])/1000*self.avoganum/1e27
            self.eledenLE.setText(str(format(eleden,'.4f')))
        else:
            if solvalidator !=0:
                self.messageBox('Warning: Please input a valid chemical formula for the solvent!\nExample:\tAl2O3')
            if np.sum(np.array(validator)) !=0:
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
        if self.solmassdenLE.text()=='':
            self.solmassdenLE.setText('1')
        if  self.solchemforLE.text()=='':
            self.solchemforLE.setText('H2O')
        for i in range(self.subphaseTW.rowCount()):
            if self.subphaseTW.cellWidget(i,0).text()=='':
                self.subphaseTW.cellWidget(i,0).setText('Cl')
            if self.subphaseTW.cellWidget(i,1).text()=='':
                self.subphaseTW.cellWidget(i,1).setText('1')
            if self.subphaseTW.cellWidget(i,2).text()=='':
                self.subphaseTW.cellWidget(i,2).setText('1')




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
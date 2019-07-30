import epics
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QComboBox, QMessageBox, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDoubleValidator,QIntValidator

from epics.utils import BYTES2STR

class PVText(QLabel):
    pvChanging=pyqtSignal(str,float)
    def __init__(self, pvname, parent=None):
        QLabel.__init__(self,'',parent)
        self.pv = None
        self.cb_index = None
        if pvname is not None:
            self.setPV(pvname)
        
    def setPV(self, pvname,prec=5,type=float):
        self.prec=prec
        self.type=type
        if self.pv is not None and self.cb_index is not None:
            self.pvChanging.disconnect()
            self.pv.remove_callback(self.cb_index)
        
        self.pv = epics.PV(BYTES2STR(pvname))
        self.setText(self.pv.get(as_string=True))
        self.cb_index = self.pv.add_callback(self.onPVChange)
        self.pvChanging.connect(self.updatePV)

    def onPVChange(self, pvname=None, value=None, char_value=None, **kws):
        self.pvChanging.emit(char_value,value)

    def updatePV(self,char_value,value):
        if self.type==float:
            self.setText(('%.'+str(self.prec)+'f')%value)
        elif self.type==int:
            self.setText('%d'%value)
        else:
            self.setText(char_value)
        
class PVLineEdit(QLineEdit):
    pvChanged=pyqtSignal(str)
    def __init__(self, pvname=None,  parent=None):
        QLineEdit.__init__(self, parent)
        self.returnPressed.connect(self.onReturn)
        self.pv = None
        self.cb_index = None
        if pvname is not None:
            self.setPV(pvname)
        
    def setPV(self, pvname, type=float, prec=5):
        if self.pv is not None and self.cb_index is not None:
            self.pv.remove_callback(self.cb_index)
            self.pvChanged.disconnect(self.updatePV)
        self.prec=prec
        self.type=type
        self.pv = epics.PV(BYTES2STR(pvname))
        self.cb_index = self.pv.add_callback(self.onPVChange)
        self.pvChanged.connect(self.updatePV)
        if self.type==float:
            self.validator=QDoubleValidator()
            self.setValidator(self.validator)
        elif self.type==int:
            self.validator=QIntValidator()
            self.setValidator(self.validator)
        #self.updatePV(self.pv.char_value)

    def onPVChange(self, pvname=None, char_value=None, **kws):
        self.pvChanged.emit(char_value)

    def updatePV(self,char_value):
        if self.type==float:
            text=float(char_value)
            self.setText(("{:."+str(self.prec)+"f}").format(text))
        else:
            self.setText(char_value)


    def onReturn(self):
        if (self.type==float or self.type==int):
            if self.validator.validate(self.text(),0)[0]==self.validator.Acceptable:
                self.pv.put(BYTES2STR(self.text()))
            else:
                QMessageBox.warning(self,'Value Error','Please input floating point numbers only',QMessageBox.Ok)
        else:
            self.pv.put(BYTES2STR(self.text()))


class PVComboBox(QComboBox):
    def __init__(self,parent=None,pvname=None):
        QComboBox.__init__(self,parent)
        self.pv = None
        if pvname is not None:
            self.setPV(pvname)
            
    def setPV(self,pvname):
        if self.pv is not None:
            self.currentIndexChanged.disconnect()
        self.pv=epics.PV(BYTES2STR(pvname))
        self.clear()
        self.addItems(self.pv.enum_strs)
        self.setCurrentIndex(self.pv.value)
        self.currentIndexChanged.connect(self.stateChanged)
    
    def stateChanged(self,index):
        text=self.itemText(index)
        self.pv.put(BYTES2STR(text))
        self.setCurrentIndex(index)

# class PVPushButton(QPushButton):
#     def __init__(self,parent=None,pvname=None):
#         QPushButton.__init__(self,parent)
#         self.pv = None
#         self.buttonText=None
#         if pvname is not None:
#             self.setPV(pvname)
#
#     def setPV(self,pvname):
#         self.pv=epics.PV(BYTES2STR(pvname))
#         self.clicked.connect(self.changePV)
#         self.cb_index = self.pv.add_callback(self.onPVChange)
#         #self.pvChanged.connect(self.updatePushButton)
#
#
#     def changePV(self):
#         if self.pv.value==1:
#             self.pv.put(0)
#         else:
#             self.pv.put(1)

    def onPVChange(self,pvname=None, value=None, **kws):
        print(value)
        if self.pv.value==1:
            self.setText(self.buttonText)
        else:
            self.setText('Stop')



        
    
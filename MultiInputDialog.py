from PyQt5.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QCheckBox,\
    QSpinBox, QComboBox, QListWidget, QDialog, QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem,\
    QAbstractItemView, QSpinBox, QSplitter, QSizePolicy, QAbstractScrollArea, QHBoxLayout, QTextEdit, QShortcut,\
    QProgressDialog
from PyQt5.QtGui import QPalette, QKeySequence, QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt, QThread, QSignalMapper
import sys
import pyqtgraph as pg

class MultiInputDialog(QDialog):
    def __init__(self, inputs={'Input':'default value'}, title='Multi Input Dialog', parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        self.inputs=inputs
        self.intValidator = QIntValidator()
        self.floatValidator = QDoubleValidator()
        self.createUI()

    def createUI(self):
        self.vblayout = QVBoxLayout(self)
        self.layoutWidget = pg.LayoutWidget()
        self.vblayout.addWidget(self.layoutWidget)
        self.labels={}
        self.inputFields={}
        for key, value in self.inputs.items():
            self.labels[key] = QLabel(key)
            self.layoutWidget.addWidget(self.labels[key])
            if type(value)==int:
                self.signalMapper1 = QSignalMapper(self)
                self.inputFields[key]=QLineEdit(str(value))
                self.inputFields[key].setValidator(self.intValidator)
                self.inputFields[key].textChanged.connect(self.signalMapper1.map)
                self.signalMapper1.setMapping(self.inputFields[key], key)
                self.signalMapper1.mapped[str].connect(self.inputChanged)
            elif type(value)==float:
                self.signalMapper2 = QSignalMapper(self)
                self.inputFields[key]=QLineEdit(str(value))
                self.inputFields[key].setValidator(self.floatValidator)
                self.inputFields[key].textChanged.connect(self.signalMapper2.map)
                self.signalMapper2.setMapping(self.inputFields[key], key)
                self.signalMapper2.mapped[str].connect(self.inputChanged)
            elif type(value)==bool:
                self.signalMapper3 = QSignalMapper(self)
                self.inputFields[key]=QCheckBox()
                self.inputFields[key].setTristate(False)
                self.inputFields[key].stateChanged.connect(self.signalMapper3.map)
                self.signalMapper3.setMapping(self.inputFields[key], key)
                self.signalMapper3.mapped[str].connect(self.inputStateChanged)
            elif type(value)==str:
                self.signalMapper4 = QSignalMapper(self)
                self.inputFields[key] = QLineEdit(value)
                self.inputFields[key].textChanged.connect(self.signalMapper4.map)
                self.signalMapper4.setMapping(self.inputFields[key], key)
                self.signalMapper4.mapped[str].connect(self.inputChanged)
            elif type(value)==list:
                self.signalMapper5 = QSignalMapper(self)
                self.inputFields[key] = QComboBox()
                self.inputFields[key].addItems(value)
                self.inputFields[key].currentTextChanged.connect(self.signalMapper5.map)
                self.signalMapper5.setMapping(self.inputFields[key], key)
                self.signalMapper5.mapped[str].connect(self.inputTextChanged)
            self.layoutWidget.addWidget(self.inputFields[key])
            self.layoutWidget.nextRow()
        self.layoutWidget.nextRow()
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.cancelandClose)
        self.layoutWidget.addWidget(self.cancelButton, col=0)
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.okandClose)
        self.layoutWidget.addWidget(self.okButton, col=1)
        self.okButton.setDefault(True)

    def inputChanged(self, key):
        self.inputs[key]=self.inputFields[key].text()

    def inputStateChanged(self, key):
        if self.inputFields[key].checkState():
            self.inputs[key]=True
        else:
            self.inputs[key]=False

    def inputTextChanged(self, key):
        self.inputs[key]=self.inputFields[key].currentText()
        print(self.inputs[key])

    def okandClose(self):
        self.accept()

    def cancelandClose(self):
        self.reject()

if __name__=='__main__':
    app = QApplication(sys.argv)
    dlg = MultiInputDialog(inputs={'value':100,'value2':10.0,'fit':True,'func':['Lor','Gau']})
    dlg.show()
    sys.exit(app.exec_())
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
        self.signalMapper = QSignalMapper(self)
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
                self.inputFields[key] = QLineEdit(str(value))
                self.inputFields[key].setValidator(self.intValidator)
            elif type(value)==float:
                self.inputFields[key] = QLineEdit(str(value))
                self.inputFieldsp[key].setValidator(self.floatValidator)
            else:
                self.inputFields[key] = QLineEdit(value)
            self.inputFields[key].textChanged.connect(self.signalMapper.map)
            self.signalMapper.setMapping(self.inputFields[key],key)
            self.signalMapper.mapped[str].connect(self.inputChanged)
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

    def okandClose(self):
        self.accept()

    def cancelandClose(self):
        self.reject()

if __name__=='__main__':
    app = QApplication(sys.argv)
    dlg = MultiInputDialog(inputs={'value':100})
    dlg.show()
    sys.exit(app.exec_())
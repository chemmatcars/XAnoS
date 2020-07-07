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
import numpy as np
import corner
from tabulate import tabulate

class MCMC_Dialog(QDialog)
    def __init__(self,fit_result, fit_params, bins=50, quantiles=[0.159,0.5,0.842], parent=None):
        QDialog.__init__(parent=parent)
        mesg = [['Parameters', 'Value', 'Left-error', 'Right-error']]
        for key in fit_params.keys():
            if fit_params[key].vary:
                l, p, r = np.percentile(self.fit.result.flatchain[key], [15.9, 50, 84.2])
                mesg.append([key, p, l - p, r - p])
        names = [name for name in fit_result.var_names if name != '__lnsigma']
        values = [fit_result.params[name].value for name in names]
        fig = corner.corner(fit_result.flatchain[names], labels=names, bins=bins,
                            truths=values, quantiles=quantiles, show_titles=True, title_fmt='.3f',
                            use_math_text=True)
        for ax in fig.get_axes():
            ax.set_xlabel('')
        vblayout = QVBoxLayout(self)
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
        slayout=QVBoxLayout(self)
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
        closePushButton.clicked.connect(self.closeDlg)
        hlayout.addWidget(closePushButton)
        saveWidget.setLayout(hlayout)
        slayout.addWidget(saveWidget)
        statWidget.setLayout(slayout)
        splitter.addWidget(statWidget)
        vblayout.addWidget(splitter)
        self.setWindowTitle('Error Estimates')
        self.resize(800, 600)
        dlg.setModal(True)
        dlg.show()

    def generate_plot(self,fig):


    def closeDlg(self):
        self.accept()
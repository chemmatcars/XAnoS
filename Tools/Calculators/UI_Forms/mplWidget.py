from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton
from PyQt5.QtGui import QIcon

class PlotCanvas(QWidget):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        QWidget.__init__(self,parent=parent)
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.canvas=FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        self.toolbar=NavigationToolbar(self.canvas,self)
        layout=QVBoxLayout(self)
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)

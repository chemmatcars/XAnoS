from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QMainWindow,QPushButton
from PyQt5.Qt import QProcess
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
import sys
import XAnoS_Components


class XAnoS(QMainWindow):
    def __init__(self,parent=None):
        QMainWindow.__init__(self,parent=parent)
        loadUi('UI_Forms/XAnoS.ui',self)
        self.init_UI()
        self.init_signals()

    def init_UI(self):
        self.ASAXS_Widget_running=False
        self.Fit_Widget_running=False
        self.ASAXS_Batch_Processor_1_running = False
        self.ASAXS_Batch_Processor_2_running = False
        self.Data_Reduction_Client_running = False
        self.Data_Collector_Server_running = False

    def init_signals(self):
        self.Start_Data_Collector_Server_PushButton.clicked.connect(self.launch_Data_Collector_Server)
        self.Stop_Data_Collector_Server_PushButton.clicked.connect(self.stop_Data_Collector_Server)
        self.Start_Data_Reduction_Client_PushButton.clicked.connect(self.launch_Data_Reduction_Client)
        self.Stop_Data_Reduction_Client_PushButton.clicked.connect(self.stop_Data_Reduction_Client)
        self.Start_ASAXS_Batch_Processor_1_PushButton.clicked.connect(self.launch_ASAXS_Batch_Processor_1)
        self.Stop_ASAXS_Batch_Processor_1_PushButton.clicked.connect(self.stop_ASAXS_Batch_Processor_1)
        self.Start_ASAXS_Batch_Processor_2_PushButton.clicked.connect(self.launch_ASAXS_Batch_Processor_2)
        self.Stop_ASAXS_Batch_Processor_2_PushButton.clicked.connect(self.stop_ASAXS_Batch_Processor_2)
        self.Start_ASAXS_Reducer_PushButton.clicked.connect(self.launch_ASAXSWidget)
        self.Stop_ASAXS_Reducer_PushButton.clicked.connect(self.stop_ASAXSWidget)
        self.Start_Data_Fitting_PushButton.clicked.connect(self.launch_FitWidget)
        self.Stop_Data_Fitting_PushButton.clicked.connect(self.stop_FitWidget)

    def launch_Data_Collector_Server(self):
        if not self.Data_Collector_Server_running:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.Data_Collector_Server=QProcess()
            self.Data_Collector_Server.start('python ./XAnoS_Collector.py')
            self.Data_Collector_Server_running=True
            self.Start_Data_Collector_Server_PushButton.setText('Running')
            self.Data_Collector_Server.finished.connect(self.stop_Data_Collector_Server)
            QApplication.restoreOverrideCursor()

    def stop_Data_Collector_Server(self):
        if self.Data_Collector_Server_running:
            self.Data_Collector_Server.close()
        self.Data_Collector_Server_running=False
        self.Start_Data_Collector_Server_PushButton.setText('Start')

    def launch_Data_Reduction_Client(self):
        if not self.Data_Reduction_Client_running:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.Data_Reduction_Client=QProcess()
            self.Data_Reduction_Client.start('python ./XAnoS_Reducer.py')
            self.Data_Reduction_Client_running=True
            self.Start_Data_Reduction_Client_PushButton.setText('Running')
            self.Data_Reduction_Client.finished.connect(self.stop_Data_Reduction_Client)
            QApplication.restoreOverrideCursor()

    def stop_Data_Reduction_Client(self):
        if self.Data_Reduction_Client_running:
            self.Data_Reduction_Client.close()
        self.Data_Reduction_Client_running=False
        self.Start_Data_Reduction_Client_PushButton.setText('Start')

    def launch_ASAXS_Batch_Processor_1(self):
        if not self.ASAXS_Batch_Processor_1_running:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.ASAXS_Batch_Processor_1=QProcess()
            self.ASAXS_Batch_Processor_1.start('python ./XAnoS_Batch_Processor_1.py')
            self.ASAXS_Batch_Processor_1_running=True
            self.Start_ASAXS_Batch_Processor_1_PushButton.setText('Running')
            self.ASAXS_Batch_Processor_1.finished.connect(self.stop_ASAXS_Batch_Processor_1)
            QApplication.restoreOverrideCursor()

    def stop_ASAXS_Batch_Processor_1(self):
        if self.ASAXS_Batch_Processor_1_running:
            self.ASAXS_Batch_Processor_1.close()
        self.ASAXS_Batch_Processor_1_running=False
        self.Start_ASAXS_Batch_Processor_1_PushButton.setText('Start')

    def launch_ASAXS_Batch_Processor_2(self):
        if not self.ASAXS_Batch_Processor_2_running:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.ASAXS_Batch_Processor_2=QProcess()
            self.ASAXS_Batch_Processor_2.start('python ./XAnoS_Batch_Processor_2.py')
            self.ASAXS_Batch_Processor_2_running=True
            self.Start_ASAXS_Batch_Processor_2_PushButton.setText('Running')
            self.ASAXS_Batch_Processor_2.finished.connect(self.stop_ASAXS_Batch_Processor_2)
            QApplication.restoreOverrideCursor()

    def stop_ASAXS_Batch_Processor_2(self):
        if self.ASAXS_Batch_Processor_2_running:
            self.ASAXS_Batch_Processor_2.close()
        self.ASAXS_Batch_Processor_2_running=False
        self.Start_ASAXS_Batch_Processor_2_PushButton.setText('Start')

    def launch_ASAXSWidget(self):
        if not self.ASAXS_Widget_running:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.ASAXS_Widget=QProcess()
            self.ASAXS_Widget.start('python ./XAnoS_Components.py')
            self.ASAXS_Widget_running=True
            self.Start_ASAXS_Reducer_PushButton.setText('Running')
            self.ASAXS_Widget.finished.connect(self.stop_ASAXSWidget)
            QApplication.restoreOverrideCursor()

    def stop_ASAXSWidget(self):
        if self.ASAXS_Widget_running:
            self.ASAXS_Widget.close()
        self.ASAXS_Widget_running=False
        self.Start_ASAXS_Reducer_PushButton.setText('Start')


    def launch_FitWidget(self):
        if not self.Fit_Widget_running:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.Fit_Widget=QProcess()
            self.Fit_Widget.start('python ./XAnoS_Fit.py')
            self.Fit_Widget_running=True
            self.Start_Data_Fitting_PushButton.setText('Running')
            self.Fit_Widget.finished.connect(self.stop_FitWidget)
            QApplication.restoreOverrideCursor()

    def stop_FitWidget(self):
        if self.Fit_Widget_running:
            self.Fit_Widget.close()
        self.Fit_Widget_running=False
        self.Start_Data_Fitting_PushButton.setText('Start')


if __name__=='__main__':
    app=QApplication(sys.argv)
    w=XAnoS()
    w.show()
    w.setWindowTitle('XAnoS Suite')
    sys.exit(app.exec_())
import sys
import zmq

from PyQt5 import QtCore, QtWidgets      
                
class ZeroMQ_Listener(QtCore.QObject):
    messageReceived = QtCore.pyqtSignal(str)
    
    def __init__(self,addr):
       
        QtCore.QObject.__init__(self)
        
        # Socket to talk to server
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
#        print ("Collecting updates from weather server")
        self.socket.connect ("tcp://%s"%addr)
        self.socket.setsockopt_string(zmq.SUBSCRIBE,'')
        self.running = True
    
    def loop(self):
        while self.running:
            try:
                mess= self.socket.recv(zmq.NOBLOCK).decode()
                self.messageReceived.emit(mess)
            except:
                pass
            
class ZeroMQ_Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        
        frame = QtWidgets.QFrame()
        label = QtWidgets.QLabel("listening")
        self.text_edit = QtWidgets.QTextEdit()
        
        layout = QtWidgets.QVBoxLayout(frame)
        layout.addWidget(label)
        layout.addWidget(self.text_edit)
        
        self.setCentralWidget(frame)

        self.thread = QtCore.QThread()
        self.zeromq_listener = ZeroMQ_Listener()
        self.zeromq_listener.moveToThread(self.thread)
        
        self.thread.started.connect(self.zeromq_listener.loop)
        self.zeromq_listener.messageReceived.connect(self.signal_received)
        
        QtCore.QTimer.singleShot(0, self.thread.start)
    
    def signal_received(self, message):
        self.text_edit.append("%s"% message)

    def closeEvent(self, event):
        self.zeromq_listener.running = False
        self.thread.quit()
        self.deleteLater()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    mw = ZeroMQ_Window()
    mw.show()
    
    sys.exit(app.exec_())
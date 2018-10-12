import os
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication
import sys

class FileWatcher(QObject):
    fileModified=pyqtSignal()
    fileCreated=pyqtSignal(str)
    def __init__(self,path=None, parent=None):
        QObject.__init__(self,parent)
        if path is not None:
            self.addPath(path)
        self.watcher=QThread()
        self.moveToThread(self.watcher)
        self.isRunning=False
        
    def addPath(self,path):
        if (path is not None) and (os.path.exists(path)):
            self.path=path
            self.mtime=int(os.path.getmtime(self.path))
        else:
            print('%s doesnot exist!'%path)

    def addNewPath(self,path):
        if path is not None:
            self.newPath=path
        else:
            print('Please provide a path')
            
    def fileIsModified(self):
        if os.path.exists(self.path):
            time=int(os.path.getmtime(self.path))
            if time>self.mtime:
                print('File is modified on ', time)
                self.fileModified.emit()
                self.mtime=time
        else:
            print('%s doesnot exist in the system'%self.path)
            self.path=None

    def fileIsCreated(self):
        if os.path.exists(self.newPath):
            self.fileCreated.emit(self.newPath)

                
                
    def watch(self):
        while self.path is not None:
            try:
                self.fileIsModified()
            except (KeyboardInterrupt, SystemExit):
                print('File watcher terminated cleanly!')
                raise

    def watchNew(self):
        while self.newPath is not None:
            try:
                self.fileIsCreated()
            except (keyboardInterrupt, SystemExit):
                print('File watcher terminated cleanly')

            
    def run(self):
        self.watcher.started.connect(self.watch)
        self.watcher.start()
        self.isRunning=True
        
    def run_new(self):
        self.watcher.started.connect(self.watchNew)
        self.watcher.start()
        self.isRunning=True
        
            
if __name__=='__main__':
    app=QApplication(sys.argv)
    w=FileWatcher(path='/home/epics/CARS5/Data/Data/saxs/2017-08/img_PhotonII_0001.tif')
    w.run()
    sys.exit(app.exec_())        

# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 11:32:01 2018

@author: Mrinal Bera
"""
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtTest import QTest
from PyQt5 import QtCore
import zmq
import time
import sys
import glob
import os

class ZeroMQ_Server(QtCore.QObject):
    messageEmitted = QtCore.pyqtSignal(str)
    folderFinished = QtCore.pyqtSignal(bool)
    stopped=QtCore.pyqtSignal(bool)
    
    def __init__(self,addr,folderName):
       
        QtCore.QObject.__init__(self)
        
        # Socket to talk to server
        context = zmq.Context()
#        self.socket = context.socket(zmq.SUB)
        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://%s" % addr)
#        except:
#            self.socket.unbind(self.socket.last_endpoint)
#            self.socket.bind("tcp://%s" % addr)
        self.fnames=glob.glob(os.path.join(folderName,'**','*.edf'),recursive=True)
        self.fnames.sort()
        self.running=True
        
        
        
        
   
    def loop(self):
        for i in range(10): #This is to make sure the communication starts with no lose of data
            self.socket.send_string('test')
            QTest.qWait(100)
        for fname in self.fnames:
            if self.running:
                if 'dark.edf' not in fname:
                    print(fname)
                    self.socket.send_string(fname)
                    self.messageEmitted.emit(fname)
                    QTest.qWait(1000)
            else:
                self.stopped.emit(True)
                return                
        self.folderFinished.emit(True)


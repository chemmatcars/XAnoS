# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 11:32:01 2018

@author: Mrinal Bera
"""

import zmq
import time
import sys
import glob
import os

port = "2036"
try:
    folder=sys.argv[1]
except:
    folder=None
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)

fnames=glob.glob(os.path.join(folder,'**','*.edf'),recursive=True)

for fname in fnames:
    mesg=fname
    print(mesg)
    socket.send_string(mesg)
    time.sleep(1)
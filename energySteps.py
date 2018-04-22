#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 18:38:00 2017

@author: epics
"""


from xraydb import XrayDB
import sys
import numpy as np

if len(sys.argv)==5:
    element=sys.argv[1]
    edge_energy=1e3*float(sys.argv[2])
    min_energy=1e3*float(sys.argv[3])
    steps=int(sys.argv[4])
    try:
        fname=sys.argv[5]
    except:
        fname='/tmp/positionerFile.txt'
    
    xrdb=XrayDB()
    evals=np.linspace(edge_energy,min_energy,steps)
    f1=xrdb.f1_chantler(element=element,energy=evals,smoothing=0)
    f1vals=np.linspace(f1[0],f1[-1],steps)
    e1vals=np.interp(f1vals,f1,evals)
    evaltxt=''
    print("f_value\tMono_E\tUnd_E")
    for i in range(steps):
       # print("%.5f\t%.3f"%(f1vals[i],e1vals[i]/1e3))
        evaltxt=evaltxt+'%.3f,'%(e1vals[i]/1e3)
        print("%.5f\t%.3f\t%.3f"%(f1vals[i],e1vals[i]/1e3,e1vals[i]/1e3+0.17))
    fh=open(fname,'w')
    txt='Energy ['+evaltxt[:-1]+'] absolute coupled'
    fh.write(txt)
    fh.close()
else:
    print("Usage: python energySteps.py element_symbol edge_energy min_energy steps [file to save the steps]\n"+
          "For example: python energySteps.py Y 17.038 16.738 20 positionerFile.txt")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  3 20:13:05 2017

@author: epics
"""

from readData import read1DSAXS
import sys
import numpy as np
import pylab as pl

data={}
start=int(sys.argv[1])
end=int(sys.argv[2])

for num in range(start,end+1):
    fname='/home/epics/CARS5/Data/chemmat/Data/saxs/2017-10/Align/GlassyCarbon/GC/pilatus_100k/extracted_pyFAI/GC_%04d.txt'%num
    read1DSAXS(fname,data=data,key=num)
    
    
for num in range(start,end+1):
    pl.plot(num,np.sum(data[num]['y'][200:]),'ro')
    #pl.plot(num,np.sum(data[num]['y'][100:200])*data[num]['Monitor_corr'],'ro')
    #pl.plot(num,data[num]['BSDiode_corr']/data[num]['Monitor_corr'],'ro')
    #pl.plot(num,data[num]['Monitor_corr'],'bo')
pl.show()
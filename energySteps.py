#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 18:38:00 2017

@author: epics
"""


from xraydb import XrayDB
import sys
import numpy as np
import pylab as pl

print (sys.argv)

if len(sys.argv)==7:
    element=sys.argv[1]
    edge_energy=1e3*float(sys.argv[2])
    min_energy=1e3*float(sys.argv[3])
    steps=int(sys.argv[4])
    eoff=float(sys.argv[5])
    try:
        fname=sys.argv[6]
    except:
        fname='/tmp/positionerFile.txt'
    
    xrdb=XrayDB()
    evals=np.linspace(edge_energy,min_energy,steps)
    efine=np.linspace(edge_energy,min_energy,1001)
    f1=xrdb.f1_chantler(element=element,energy=efine,smoothing=0)
    f1vals=np.linspace(f1[0],f1[-1],steps)
    e1vals=np.interp(f1vals,f1,efine)
    print(np.diff(f1vals))
    print(np.diff(e1vals))
    evaltxt=''
    pl.figure()
    etemp=np.linspace(min_energy,edge_energy+(edge_energy-min_energy),1001)
    f1temp=xrdb.f1_chantler(element=element,energy=etemp,smoothing=0)
    pl.plot(etemp,f1temp,'r-',label=element+'-Energy Edge')
    print("%10s\t%10s\t%10s\t%10s\t%10s"%("Step","f_value","Mono_E","Und_E","f_1"))
    for i in range(steps):
       # print("%.5f\t%.3f"%(f1vals[i],e1vals[i]/1e3))
        evaltxt=evaltxt+'%.3f,'%(e1vals[i]/1e3+eoff)
        print("%10d\t%10.7f\t%10.3f\t%10.3f\t%10.7f"%(i,f1vals[i],e1vals[i]/1e3+eoff,e1vals[i]/1e3+0.17+eoff,
                                                   xrdb.f1_chantler(
            element=element,energy=e1vals[i],smoothing=0)))
    fh=open(fname,'w')
    txt='Energy ['+evaltxt[:-1]+'] absolute coupled'
    fh.write(txt)
    fh.close()
    #pl.plot(e1vals,xrdb.f1_chantler(element=element,energy=e1vals,smoothing=0),'go',label='Equal f1 steps')
    pl.plot(e1vals, f1vals, 'go', label='Equal f\' steps')
    leg=pl.legend(loc='best')
    leg.draggable()
    pl.show()
else:
    print("Usage: python energySteps.py element_symbol edge_energy min_energy steps energy_offset [file to save the "
          "steps]\n"+
          "For example: python energySteps.py Y 17.038 16.738 20 0.0 positionerFile.txt")

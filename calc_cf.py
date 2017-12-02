#!/home/epics/anaconda3/bin/python
#This calculates the calibration factor using the data obtained from NIST and the data obtained during a SAXS run at the beamline from Glassy Carbon
#Basic syntax: 

import sys
import os
import numpy as np
from scipy.interpolate import interp1d
import pylab
from lmfit import minimize, Parameters

def fun(params,x,ycal,exp_dat,thickness):
    cf=params['cf'].value
    qoff=params['qoff'].value
    expdf=interp1d(exp_dat[:,0]-qoff,exp_dat[:,1]/thickness,kind='cubic')
    return ycal(x)-cf*expdf(x-qoff)

def calc_cf(fname, standard='GC',thickness=1.0,plot=False,xmin=None,xmax=None):
    """
    Calculates the calibration factor by using different chosen standards like
    GC: Glassy Carbon with thickness 0.1055 cm from NIST
    Water: Water with the the known thickness as the samples
    thickness: Thickness of Standard sample in cm. It should be 0.1055 for NIST GC standard.
    """
    if os.path.exists(fname):
        if standard=='GC':
            std_dat=np.loadtxt('/home/epics/CARS5/Users/ChemMat/Beamline Operations/15IDD/SAXS/SAXS_Drive/SetupData/glassy_carbon_saxs_std.txt')
        elif standard=='Water':
            qst=np.linspace(0.003,1.0,1000)
            std_dat=np.vstack((qst,np.ones_like(qst)*1.68e-2)).T
        tmp_dat=np.loadtxt(fname)
        fh=open(fname,'r')
        lines=fh.readlines()
        for line in lines:
            if line[0]=='#':
                try:
                    header,value=line[1:].split('=')
                    if header=='Energy':
                        energy=float(value)
                except:
                    pass
    
        #Checking the data for zeros
        exp_dat=[]
        for i in range(tmp_dat.shape[0]):
            if tmp_dat[i,1]>1e-20:
                exp_dat.append(tmp_dat[i,:])
        exp_dat=np.array(exp_dat)
        if xmin is None:    
            xmin=np.max([np.min(std_dat[:,0]),np.min(exp_dat[:,0])])
        if xmax is None:
            xmax=np.min([np.max(std_dat[:,0]),np.max(exp_dat[:,0])])
        istdmin=np.argwhere(std_dat[:,0]>=xmin)[0][0]
        istdmax=np.argwhere(std_dat[:,0]<=xmax)[-1][0]
        expdmin=np.argwhere(exp_dat[:,0]>=xmin)[0][0]
        expdmax=np.argwhere(exp_dat[:,0]<=xmax)[-1][0]
    
        xmin=np.max([std_dat[istdmin,0],exp_dat[expdmin,0]])
        xmax=np.min([std_dat[istdmax,0],exp_dat[expdmax,0]])
        x=np.linspace(1.05*xmin,0.95*xmax,100)
        istdf=interp1d(std_dat[:,0],std_dat[:,1],kind='cubic')
        #expdf=interp1d(exp_dat[:,0],exp_dat[:,1]/.1055,kind='cubic')
        param=Parameters()
        param.add('cf',value=1.0,vary=True)
        param.add('qoff',value=0.000,vary=False)
        res=minimize(fun,param,args=(x,istdf,exp_dat,thickness))
        cf,qoff=res.params['cf'].value,res.params['qoff'].value
        #print(cf,qoff)
        
        #cf=np.mean(istdf(x)/expdf(x))
        if plot:
            pylab.loglog(std_dat[:,0],std_dat[:,1],'r-',lw=3,label='NIST std')
            pylab.loglog(x,+istdf(x)-res.residual,'g-',lw=3,label='15IDD data')
            pylab.xlabel(u'Q, \u212B$^{-1}$',fontsize=fs)
            pylab.ylabel(u'I, cm$^{-1}$',fontsize=fs)
            pylab.legend(loc='best',prop={'size':fs*0.6})
            pylab.xticks(fontsize=fs)
            pylab.yticks(fontsize=fs)
            pylab.tight_layout()
            pylab.show()
        return energy,cf,qoff,x,istdf(x)
    else:
        print('%s doesnot exist!'%fname)

if __name__=="__main__":
    fs=15
    fname=sys.argv[1]
    try:
        plot=sys.argv[2]
        xmin=float(sys.argv[3])
        xmax=float(sys.argv[4])
    except:
        plot=False
        xmin=None
        xmax=None
    energy,cf,qoff,x,istdf=calc_cf(fname,plot=True,xmin=xmin,xmax=xmax)
    print('Energy(keV)\tCf\tqOf')
    print('%.4f\t%.4f\t%.5f'%(energy,cf,qoff))

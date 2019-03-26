#!/home/epics/anaconda3/bin/python
#This calculates the calibration factor using the data obtained from NIST and the data obtained during a SAXS run at the beamline from Glassy Carbon
#Basic syntax: 

import sys
import os
import numpy as np
from scipy.interpolate import interp1d
import pylab
from lmfit import minimize, Parameters

def fun(params,x,ycal,yexp,thickness):
    cf=params['cf'].value
    return ycal(x)-cf*yexp(x)/thickness

def calc_cf(fname, standard='GC',thickness=1.0,plot=False,xmin=None,xmax=None,interpolation_type='linear'):
    """
    Calculates the calibration factor by using different chosen standards like
    fname              : filename containing the experimental data done on standard sample
    standard           : 'GC' or 'Water' for (Glassy Carbon with thickness 0.1055cm from NIST) or (Water with the the known thickness as the samples)
    thickness          : Thickness of Standard sample in cm. It should be 0.1055 for NIST GC standard.
    interpolation_type : 'linear','quadratic'or 'cubic'
    plot : True or False for plotting or not plotting to view the goodness of fit
    xmin,xmax : minimum and maximum Q-value between which the experimental data will be fitted with the standard data available
    """
    if os.path.exists(fname):
        if standard=='GC':
            std_dat=np.loadtxt('./SetupData/glassy_carbon_saxs_std.txt')
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
        istdf=interp1d(std_dat[:,0],std_dat[:,1],kind=interpolation_type)
        expdf=interp1d(exp_dat[:,0],exp_dat[:,1],kind=interpolation_type)
        param=Parameters()
        param.add('cf',value=1.0,vary=True)
        res=minimize(fun,param,args=(x,istdf,expdf,thickness))
        cf=res.params['cf'].value
        #print(cf,qoff)
        
        #cf=np.mean(istdf(x)/expdf(x))
        if plot:
            pylab.loglog(std_dat[:,0],std_dat[:,1],'r-',lw=3,label='NIST std')
            pylab.loglog(x,istdf(x)-res.residual,'g-',lw=3,label='15IDD data')
            pylab.xlabel(u'Q, \u212B$^{-1}$',fontsize=fs)
            pylab.ylabel(u'I, cm$^{-1}$',fontsize=fs)
            pylab.legend(loc='best',prop={'size':fs*0.6})
            pylab.xticks(fontsize=fs)
            pylab.yticks(fontsize=fs)
            pylab.tight_layout()
            pylab.show()
        return energy,cf,x,istdf(x)
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
    energy,cf,x,istdf=calc_cf(fname,plot=plot,xmin=xmin,xmax=xmax,interpolation_type='linear')
    print('Energy(keV)\tCf')
    print('%.4f\t%.4f'%(energy,cf))

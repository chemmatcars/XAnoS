####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
from math import log, erf
import sys
import os
import matplotlib.pyplot as plt
from lmfit import fit_report, Minimizer
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox
import traceback
from numpy import loadtxt
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_routines/'))
from functools import lru_cache
####Please do not remove lines above####

####Import your modules below if needed####
from xr_ref import parratt


class AsymSphere: #Please put the class name same as the function name
    def __init__(self,x = 0.1, E = 10.0, R0 = 25.00, rhoc = 4.68, D = 66.6, rhosh = 0.200, h1 = -25.0, h1sig = 0.0, h2 = 3.021,
                 rhoup = 0.00, rhodown = 0.334, sig = 3.0, cov = 0.901, fix_sig = False,
                 mpar={'Layers':['Top', 'Bottom'], 'd':[0.0,1.0],'rho':[0.0,0.334],'beta':[0.0,0.0],'sig':[0.0,3.00]},
                 rrf = 1, qoff=0.0,zmin=-120,zmax=120,dz=1):
        """
        Calculates X-ray reflectivity from multilayers of core-shell spherical nanoparticles assembled near an interface
        x       : array of wave-vector transfer along z-direction
        E      	: Energy of x-rays in inverse units of x
        Rc     	: Radius of the core of the nanoparticles
        rhoc   	: Electron density of the core
        D       : Seperation between Nanoparticles
        h1      : Distance between the center for the core and the interface
        h1sig   : width of the Fluctuations in h1
        rhosh  	: Electron Density of the outer shell. If 0, the electron density the shell region will be assumed to be filled by the bulk phases depending upon the position of the nanoparticles
        rhoup   : Electron density of the upper bulk phase
        rhodown : Electron density of the lower bulk phase
        sig     : Roughness of the interface
        mpar    : The monolayer parameters where, Layers: Layer description, d: thickness of each layer, rho:Electron density of each layer, beta: Absorption coefficient of each layer, sig: roughness of interface separating each layer. The upper and lower thickness should be always  fixed. The roughness of the topmost layer should be always kept 0. 
        fix_sig : 'True' for forcing all the rougnesses of all the layers in monolayers to be same and 'False' for not same
        rrf     : 1 for Frensnel normalized refelctivity and 0 for just reflectivity
        qoff    : q-offset to correct the zero q of the instrument
        zmin    : minimum depth for electron density calculation
        zmax    : maximum depth for electron density calculation
        dz      : minimum slab thickness
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.E=E
        self.R0=R0
        self.rhoc=rhoc
        self.D=D
        self.rhosh=rhosh
        self.h2=h2
        self.h1 = h1
        self.h1sig = h1sig
        self.rhoup=rhoup
        self.rhodown=rhodown
        self.cov=cov
        self.zmin=zmin
        self.zmax=zmax
        self.sig=sig
        self.dz=dz
        self.fix_sig = fix_sig
        self.__mpar__= mpar
        self.rrf=rrf
        self.qoff=qoff
        self.choices={'rrf' : [1,0] ,'fix_sig' : [True, False]}
        self.init_params()
        self.output_params={'scaler_parameters':{}}


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('R0', value=self.R0,vary=0,min=0,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('rhoc', value=self.rhoc,vary=0,min=0,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('D', value=self.D,vary=0,min=0,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('h1', value = self.h1, vary = 0, min=-np.inf, max=np.inf, expr = None, brute_step=0.1)
        self.params.add('h1sig', value=self.h1sig, vary=0, min=0, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('h2',value=self.h2,vary=1,min=0,max=7.338,expr=None,brute_step=0.1)
        self.params.add('rhosh',value=self.rhosh,vary=0,min=0,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('sig',value=self.sig,vary=0,min=0,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('cov',value=self.cov,vary=0,min=0.00,max=1,expr=None,brute_step=0.1)
        self.params.add('qoff',self.qoff,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
    
        for key in self.__mpar__.keys():
            if key!='Layers':
                if key != 'sig':
                    for i in range(len(self.__mpar__[key])):
                        self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
                else:
                    if self.fix_sig:
                        for i in range(2):
                            self.params.add('__%s__%03d' % (key, i), value=self.__mpar__[key][i], vary=0, min=-np.inf, max=np.inf,
                                        expr=None, brute_step=0.1)
                        for i in range(2,len(self.__mpar__[key])):
                            self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=0,max=np.inf,expr='__sig__001',brute_step=0.1)
                    else:
                        for i in range(len(self.__mpar__[key])):
                                self.params.add('__%s__%03d' % (key, i), value=self.__mpar__[key][i], vary=0, min=0,
                                            max=np.inf, expr=None, brute_step=0.1)

    @lru_cache(maxsize=10)
    def NpRho(self,z,R0=25,rhoc=4.68,D=66.0,rhosh=0.2,h2=8,h1=-35,rhoup=0.0,rhodown=0.334):
        z=np.array(z)
        Tsh=D/2.0-R0
        Atot=np.sqrt(3)*D**2/2
        Re=np.where(-R0-h2<h1<R0+Tsh,(D**2/4-h1**2+(h2+R0+h1)**2)/(2*(h2+R0+h1)),D/2)
        rhos=np.where(z>0,rhodown,rhoup)
        Acore=np.pi*np.sqrt(np.where(z>h1+R0,0.0,R0**2-(z-h1)**2)*np.where(z<h1-R0,0.0,R0**2-(z-h1)**2))
        ANp=np.pi*np.sqrt(np.where(z>=0,0.0,D**2/4-(z-h1)**2)*np.where(z<h1-D/2,0.0,D**2/4-(z-h1)**2))\
            +np.pi*np.sqrt(np.where(z<0,0.0,Re**2-(Re-h2-R0-h1+z)**2)*np.where(z>h2+R0+h1,0.0,Re**2-(Re-h2-R0-h1+z)**2))
        return  ((Atot-ANp)*rhos+rhosh*(ANp-Acore)+rhoc*Acore)/Atot

    @lru_cache(maxsize=10)
    def NpRhoGauss(self,z,R0=25,rhoc=4.68,D=66.6,rhosh=0.2,h2=10,h1=(-30,),h1sig=(0,),rhoup=0.0,rhodown=0.334,sig=3.0,Nc=20):
        z=np.array(z)
        if sig<1e-3:
            zt=z
        else:
            zmin=z[0]-5*sig
            zmax=z[-1]+5*sig
            zt=np.arange(zmin,zmax,self.dz)
        rhosum=np.zeros_like(zt)
        
        rhos=np.where(zt>0,rhodown,rhoup)
        
        for i in range(len(h1)):
            if h1sig[i]<1e-3:
                rhosum=rhosum+self.NpRho(tuple(zt),R0=R0,rhoc=rhoc,D=D,rhosh=rhosh,h2=h2,h1=h1[i],rhoup=rhoup,rhodown=rhodown)
            else:
                Z1=np.linspace(h1[i]-5*h1sig[i],h1[i]+5*h1sig[i],201)
                dist=np.where(Z1<h1, np.exp(-(Z1-h1[i])**2/2/h1sig[i]**2),0.0)
                norm=np.sum(dist)
                tsum=np.zeros_like(len(zt))
                for j in range(len(Z1)):
                    nprho=self.NpRho(tuple(zt),R0=R0,rhoc=rhoc,D=D,rhosh=rhosh,h2=h2,h1=Z1[j],rhoup=rhoup,rhodown=rhodown)
                    tsum=tsum+nprho*dist[j]
                rhosum=rhosum+tsum/norm
        rho=rhosum-(len(h1)-1)*rhos 
        if sig<1e-3:
            return rho
        else:
            Np = 10*sig/self.dz
            x=np.arange(-5*sig,5*sig,self.dz)
            rough=np.exp(-x**2/2/sig**2)/np.sqrt(2*np.pi)/sig
            res=np.convolve(rho,rough,mode='valid')*self.dz
            if len(res)>len(z):
                return res[0:len(z)]
            elif len(res)<len(z):
                res=np.append(res,[res[-1]])
            else:
                return res

    def calcProfile1(self):
        """
        Calculates the electron and absorption density profiles
        """
        self.__z__=np.arange(self.zmin,self.zmax,self.dz)
        self.__d__=self.dz*np.ones_like(self.__z__)
        self.__rho__=self.NpRhoGauss(tuple(self.__z__),R0=self.R0,rhoc=self.rhoc,D=self.D,rhosh=self.rhosh,h2=self.h2,h1=tuple([self.h1]),h1sig=tuple([self.h1sig]),rhoup=self.rhoup,rhodown=self.rhodown,sig=self.sig)
        self.output_params['Nanoparticle EDP']={'x':self.__z__,'y':self.__rho__, 'names':['z (Angs)', 'Electron Density (el/Angs^3)']}

    def calcProfile2(self):
        """
        Calculates the electron and absorption density profiles of the additional monolayer
        """
        d = np.array([self.params['__d__%03d' % i].value for i in range(len(self.__mpar__['d']))])
        rho = np.array([self.params['__rho__%03d' % i].value for i in range(len(self.__mpar__['rho']))])
        beta = np.array([self.params['__beta__%03d' % i].value for i in range(len(self.__mpar__['beta']))])
        sig = np.array([self.params['__sig__%03d' % i].value for i in range(len(self.__mpar__['sig']))])
        if self.fix_sig:
            for i in range(1, len(sig)):
                sig[i] = sig[1]
        # n = len(d)
        # maxsig = max(np.abs(np.max(sig[1:])), 3)
        # Nlayers = int((np.sum(d[:-1]) + 10 * maxsig) / self.Minstep)
        # halfstep = (np.sum(d[:-1]) + 10 * maxsig) / 2 / Nlayers
        self.__z2__ = np.arange(self.zmin,self.zmax,self.dz)#np.linspace(-5 * maxsig + halfstep, np.sum(d[:-1]) + 5 * maxsig - halfstep, Nlayers)
        self.__d2__=self.dz*np.ones_like(self.__z2__)
        self.__rho2__ = self.sldCalFun(d, rho, sig, self.__z2__)
        self.__beta2__ = self.sldCalFun(d, beta, sig, self.__z2__)
        if not self.__fit__:
            self.output_params['Monolayer EDP'] = {'x': self.__z__-np.sum(d[1:-1]), 'y': self.__rho2__, 'names':['z (Angs)','Elecron Density (el/Angs^3)']}
            self.output_params['Monolayer ADP'] = {'x': self.__z__-np.sum(d[1:-1]), 'y': self.__beta2__, 'names':['z (Angs)','Beta']}


    def sldCalFun(self,d,y,sigma,x):
        wholesld=[]
        for j in range(len(x)):
            sld=0
            for i in range(len(d)-1):
                pos=np.sum(d[:i+1])
                sld=sld+erf((x[j]-pos)/sigma[i+1]/np.sqrt(2))*(y[i+1]-y[i])
            wholesld.append(max((sld+y[0]+y[-1])/2,0))
        return wholesld

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        cov=self.cov
        self.calcProfile1()
        x=self.x+self.qoff
        lam=6.62607004e-34*2.99792458e8*1e10/self.E/1e3/1.60217662e-19
        refq,r2=parratt(x,lam,self.__d__,self.__rho__,np.zeros_like(self.__rho__))

        self.calcProfile2()
        refq2,r2=parratt(x,lam,self.__d2__,self.__rho2__,self.__beta2__)
        
        if self.rrf>0:
            rhos1=[self.__rho__[0],self.__rho__[-1]]
            betas1=[0,0]
            ref,r2=parratt(x-self.qoff,lam,[0.0,1.0],rhos1,betas1)
            refq=refq/ref
            refq2=refq2/ref
            
        refqt=refq*cov+refq2*(1-cov)
        return refqt     
    
        

if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=AsymSphere(x=x)
    print(fun.y())

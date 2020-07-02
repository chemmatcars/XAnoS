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
                 sig = 3.0, cov = 0.901, fix_sig = False,
                 mpar={'Multilayer':{'Layers':['Top', 'Bottom'], 'd':[0.0,1.0],'rho':[0.0,0.334],'beta':[0.0,0.0],'sig':[0.0,3.00]}},
                 rrf = True, qoff=0.0,zmin=-120,zmax=120,dz=1,coherrent=False,yscale=1.0,bkg=0.0):
        """
        Calculates X-ray reflectivity from multilayers of core-shell spherical nanoparticles assembled near an interface
        x         : array of wave-vector transfer along z-direction
        E      	  : Energy of x-rays in inverse units of x
        Rc     	  : Radius of the core of the nanoparticles
        rhoc   	  : Electron density of the core
        D         : Separation between Nanoparticles
        h1        : Distance between the center for the core and the interface
        h1sig     : width of the Fluctuations in h1
        rhosh  	  : Electron Density of the outer shell. If 0, the electron density the shell region will be assumed to be filled by the bulk phases depending upon the position of the nanoparticles
        sig       : Roughness of the interface
        mpar      : The monolayer parameters where, Layers: Layer description, d: thickness of each layer, rho:Electron density of each layer, beta: Absorption coefficient of each layer, sig: roughness of interface separating each layer. The upper and lower thickness should be always  fixed. The roughness of the topmost layer should be always kept 0.
        fix_sig   : 'True' for forcing all the rougnesses of all the layers in monolayers to be same and 'False' for not same
        rrf       : True or False for Frensnel normalized or not normalized reflectivity
        qoff      : q-offset to correct the zero q of the instrument
        zmin      : minimum depth for electron density calculation
        zmax      : maximum depth for electron density calculation
        dz        : minimum slab thickness
        yscale    : a scale factor for R or R/Rf
        bkg       : in-coherrent background
        cov       : coverage of nanoparticles
        coherrent : True or False for coherrent or in-coherrent addition of reflectivities from nanoparticles and lipid layer
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
        self.cov=cov
        self.zmin=zmin
        self.zmax=zmax
        self.sig=sig
        self.dz=dz
        self.yscale=yscale
        self.bkg=bkg
        self.fix_sig = fix_sig
        self.__mpar__= mpar
        self.rrf=rrf
        self.coherrent=coherrent
        self.qoff=qoff
        self.choices={'rrf' : [True,False] ,'fix_sig' : [True, False],'coherrent':[True, False]}
        self.__mkeys__=list(self.__mpar__.keys())
        self.__fit__=False
        self.init_params()


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

        for mkey in self.__mpar__.keys():
            for key in self.__mpar__[mkey].keys():
                if key!='Layers':
                    if key != 'sig':
                        for i in range(len(self.__mpar__[mkey][key])):
                            self.params.add('__%s_%s_%03d'%(mkey,key,i),value=self.__mpar__[mkey][key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
                    else:
                        if self.fix_sig:
                            for i in range(2):
                                self.params.add('__%s_%s_%03d' % (mkey,key,i), value=self.__mpar__[mkey][key][i], vary=0, min=-np.inf, max=np.inf,
                                            expr=None, brute_step=0.1)
                            for i in range(2,len(self.__mpar__[mkey][key])):
                                self.params.add('__%s_%s_%03d'%(mkey,key,i),value=self.__mpar__[mkey][key][i],vary=0,min=0,
                                                max=np.inf,expr='__%s_sig_001'%mkey,brute_step=0.1)
                        else:
                            for i in range(len(self.__mpar__[mkey][key])):
                                    self.params.add('__%s_%s_%03d' % (mkey,key,i), value=self.__mpar__[mkey][key][i], vary=0, min=0,
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
                dist=np.exp(-(Z1-h1[i])**2/2/h1sig[i]**2)
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

    @lru_cache(maxsize=10)
    def calcProfile1(self,R0,rhoc,D,rhosh,h2,h1,h1sig,rhoup,rhodown,sig,zmin,zmax,dz):
        """
        Calculates the electron and absorption density profiles from the nanoparticle layer
        """
        __z__=np.arange(self.zmin,self.zmax,self.dz)
        __d__=self.dz*np.ones_like(__z__)
        __rho__=self.NpRhoGauss(tuple(__z__),R0=R0,rhoc=rhoc,D=D,rhosh=rhosh,h2=h2,h1=tuple([h1]),h1sig=tuple([h1sig]),
                                rhoup=rhoup,rhodown=rhodown,sig=sig)
        return __z__,__d__,__rho__


    @lru_cache(maxsize=10)
    def calcProfile2(self,d,rho,beta,sig,zmin,zmax,dz):
        """
        Calculates the electron and absorption density profiles of the additional monolayer
        """
        # n = len(d)
        # maxsig = max(np.abs(np.max(sig[1:])), 3)
        # Nlayers = int((np.sum(d[:-1]) + 10 * maxsig) / self.Minstep)
        # halfstep = (np.sum(d[:-1]) + 10 * maxsig) / 2 / Nlayers
        __z2__ = np.arange(zmin,zmax,dz)#np.linspace(-5 * maxsig + halfstep, np.sum(d[:-1]) + 5 * maxsig - halfstep, Nlayers)
        __d2__=dz*np.ones_like(__z2__)
        __rho2__ = self.sldCalFun(d, tuple(rho), tuple(sig), tuple(__z2__))
        __beta2__ = self.sldCalFun(d, tuple(beta), tuple(sig), tuple(__z2__))
        return __z2__-np.sum(d[1:-1]),__d2__,__rho2__,__beta2__

    @lru_cache(maxsize=10)
    def sldCalFun(self,d,y,sigma,x):
        wholesld=[]
        for j in range(len(x)):
            sld=0
            for i in range(len(d)-1):
                pos=np.sum(d[:i+1])
                sld=sld+erf((x[j]-pos)/sigma[i+1]/np.sqrt(2))*(y[i+1]-y[i])
            wholesld.append(max((sld+y[0]+y[-1])/2,0))
        return wholesld

    @lru_cache(maxsize=10)
    def py_parratt(self, x, lam, d, rho, beta):
        return parratt(x, lam, d, rho, beta)

    def update_parameters(self):
        mkey = self.__mkeys__[0]
        self.__d__ = tuple([self.params['__%s_d_%03d' % (mkey, i)].value for i in range(len(self.__mpar__[mkey]['d']))])
        self.__rho__ = tuple(
            [self.params['__%s_rho_%03d' % (mkey, i)].value for i in range(len(self.__mpar__[mkey]['rho']))])
        self.__beta__ = tuple(
            [self.params['__%s_beta_%03d' % (mkey, i)].value for i in range(len(self.__mpar__[mkey]['beta']))])
        self.__sig__ = tuple(
            [self.params['__%s_sig_%03d' % (mkey, i)].value for i in range(len(self.__mpar__[mkey]['sig']))])

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params = {'scaler_parameters': {}}
        if not self.__fit__:
            for mkey in self.__mpar__.keys():
                Nlayers = len(self.__mpar__[mkey]['sig'])
                for i in range(2,Nlayers):
                    if self.fix_sig:
                        self.params['__%s_%s_%03d' % (mkey, 'sig', i)].expr = '__%s_%s_%03d' % (mkey, 'sig', 1)
                    else:
                        self.params['__%s_%s_%03d' % (mkey, 'sig', i)].expr = None
        self.update_parameters()
        rhoup=self.__rho__[0]
        rhodown=self.__rho__[-1]
        z1,d1,rho1=self.calcProfile1(self.R0,self.rhoc,self.D,self.rhosh,self.h2,self.h1,self.h1sig,rhoup,
                                     rhodown,self.sig,self.zmin,self.zmax,self.dz)
        x=self.x+self.qoff
        lam=6.62607004e-34*2.99792458e8*1e10/self.E/1e3/1.60217662e-19
        refq1,r1=self.py_parratt(tuple(x),lam,tuple(d1),tuple(rho1),tuple(np.zeros_like(rho1)))

        z2,d2,rho2,beta2=self.calcProfile2(self.__d__,self.__rho__,self.__beta__,self.__sig__,self.zmin,self.zmax,self.dz)
        refq2,r2=self.py_parratt(tuple(x),lam,tuple(d2),tuple(rho2),tuple(beta2))
        refq=self.cov*refq1+(1-self.cov)*refq2
        crefq=np.abs(self.cov*r1+(1-self.cov)*r2)**2
        if not self.__fit__:
            self.output_params['Nanoparticle EDP'] = {'x': z1, 'y': rho1,
                                                      'names': ['z (Angs)', 'Electron Density (el/Angs^3)']}
            self.output_params['Monolayer EDP'] = {'x': z2, 'y': rho2, 'names':['z (Angs)','Electron Density (el/Angs^3)']}
            self.output_params['Monolayer ADP'] = {'x': z2, 'y': beta2, 'names':['z (Angs)','Beta']}

        if self.rrf:
            rhos1=(rho1[0],rho1[-1])
            betas1=(0,0)
            ref,r2=self.py_parratt(tuple(x-self.qoff),lam,(0.0,1.0),rhos1,betas1)
            refq=refq/ref
            crefq=crefq/ref
        if self.coherrent:
            return crefq
        else:
            return refq



if __name__=='__main__':
    x=np.linspace(0.001,1.0,100)
    fun=AsymSphere(x=x)
    print(fun.y())

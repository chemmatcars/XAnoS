####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
import sys
import os
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_routines/'))
from functools import lru_cache
####Please do not remove lines above####

####Import your modules below if needed####
from xr_ref import parratt


class Parratt: #Please put the class name same as the function name
    def __init__(self,x=0.1,E=10.0,mpar={'Model':
                                             {'Layers':['top','Bottom'],'d':[0.0,1.0],'rho':[0.0,0.334],'beta':[0.0,0.0],'sig':[0.0,3.0]}},
    Nlayers=101,rrf=True,qoff=0.0,yscale=1.0,bkg=0.0):
        """
        Calculates X-ray reflectivity from a system of multiple layers using Parratt formalism

        x     	: array of wave-vector transfer along z-direction
        E     	: Energy of x-rays in invers units of x
        mpar  	: The layer parameters where, Layers: Layer description, d: thickness of each layer, rho:Electron density of each layer, beta: Absorption coefficient of each layer, sig: roughness of interface separating each layer. The upper and lower thickness should be always  fixed. The roughness of the topmost layer should be always kept 0.
        Nlayers : The number of layers in which the layers will be subdivided for applying Parratt formalism
        rrf   	: True for Frensnel normalized refelctivity and False for just reflectivity
        qoff  	: q-offset to correct the zero q of the instrument
        yscale  : a scale factor for R or R/Rf
        bkg     : in-coherrent background
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.E=E
        self.__mpar__=mpar
        self.Nlayers=Nlayers
        self.rrf=rrf
        self.qoff=qoff
        self.yscale=yscale
        self.bkg=bkg
        self.choices={'rrf':[True,False]}
        self.__fit__=False
        self.__mkeys__=list(self.__mpar__.keys())
        self.init_params()


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('qoff', self.qoff, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('yscale', self.yscale, vary=0, min=0.9, max=1.1, expr=None, brute_step=0.1)
        self.params.add('bkg', self.bkg, vary=0, min=0, max=np.inf, expr=None, brute_step=0.1)
        for mkey in self.__mpar__.keys():
            for key in self.__mpar__[mkey].keys():
                if key != 'Layers':
                    for i in range(len(self.__mpar__[mkey][key])):
                        self.params.add('__%s_%s_%03d' % (mkey, key, i), value=self.__mpar__[mkey][key][i], vary=0,
                                        min=0, max=np.inf, expr=None, brute_step=0.05)

    @lru_cache(maxsize=10)
    def calcProfile(self,d,rho,beta,sig,Nlayers):
        """
        Calculates the electron and absorption density profiles
        """
        d=np.array(d)
        rho=np.array(rho)
        beta=np.array(beta)
        sig=np.array(sig)
        n=len(d)
        maxsig=np.max(sig[1:])
        __z__=np.linspace(-5*maxsig,np.sum(d[:-1])+5*maxsig,Nlayers)
        zlayer=__z__[1]-__z__[0]
        #Condition imposed on sig for rougness less than the thicknesses of the sublayers
        #sig=np.where(sig<zlayer,0.1*zlayer,sig)
        drho=np.zeros(Nlayers)
        dbeta=np.zeros(Nlayers)
        __d__=np.diff(__z__)
        __d__=np.append(__d__,[__d__[-1]])
        z=d[0]
        for i in range(n-1):
            drho=drho+(rho[i+1]-rho[i])*np.exp(-(__z__-z)**2/2.0/sig[i+1]**2)/2.50663/sig[i+1]
            dbeta=dbeta+(beta[i+1]-beta[i])*np.exp(-(__z__-z)**2/2.0/sig[i+1]**2)/2.50663/sig[i+1]
            z=z+d[i+1]
        __rho__=np.cumsum(drho)*__d__[0]+rho[0]
        __beta__=np.cumsum(dbeta)*__d__[0]+beta[0]
        if not self.__fit__:
            self.output_params['Electro density profile']={'x':__z__,'y':__rho__}
            self.output_params['Absorption density profile']={'x':__z__,'y':__beta__}
        return n, tuple(__d__),tuple(__rho__),tuple(__beta__)

    @lru_cache(maxsize=10)
    def py_parratt(self,x,lam,d,rho,beta):
        return parratt(x,lam,d,rho,beta)

    def update_parameters(self):
        mkey=self.__mkeys__[0]
        self.__d__ = tuple([self.params['__%s_d_%03d' % (mkey,i)].value for i in range(len(self.__mpar__[mkey]['d']))])
        self.__rho__ = tuple([self.params['__%s_rho_%03d' % (mkey,i)].value for i in range(len(self.__mpar__[mkey]['rho']))])
        self.__beta__ = tuple([self.params['__%s_beta_%03d' % (mkey,i)].value for i in range(len(self.__mpar__[mkey]['beta']))])
        self.__sig__ = tuple([self.params['__%s_sig_%03d' % (mkey,i)].value for i in range(len(self.__mpar__[mkey]['sig']))])


    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params = {'scaler_parameters': {}}
        self.update_parameters()
        mkey=self.__mkeys__[0]
        n,d,rho,beta=self.calcProfile(self.__d__, self.__rho__, self.__beta__, self.__sig__, self.Nlayers)
        x=self.x+self.qoff
        lam=6.62607004e-34*2.99792458e8*1e10/self.E/1e3/1.60217662e-19
        refq,r2=self.py_parratt(tuple(x),lam,d,rho,beta)
        if self.rrf:
            rhos=(self.params['__%s_rho_000'%mkey].value,self.params['__%s_rho_%03d'%(mkey, n-1)].value)
            betas=(self.params['__%s_beta_000'%mkey].value,self.params['__%s_beta_%03d'%(mkey, n-1)].value)
            ref,r2=self.py_parratt(tuple(x-self.qoff),lam,(0.0,1.0),rhos,betas)
            refq=refq/ref
        return refq


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Parratt(x=x)
    print(fun.y())

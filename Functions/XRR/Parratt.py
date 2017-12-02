####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
import sys
import os
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_routines/'))
####Please do not remove lines above####

####Import your modules below if needed####
from xr_ref import parratt


class Parratt: #Please put the class name same as the function name
    def __init__(self,x=0.1,E=10.0,mpar={'d':[0.0,1.0],'rho':[0.0,0.334],'beta':[0.0,0.0],'sig':[0.0,3.0]},Nlayers=101,rrf=1,qoff=0.0):
        """
        Calculates X-ray reflectivity from a system of multiple layers using Parratt formalism
        x               : array of wave-vector transfer along z-direction
        E               : Energy of x-rays in invers units of x
        mpar            : The layer parameters where, d: thickness of each layer, rho:Electron ensity of each layer, beta: Absorption coefficient of each layer, sig: roughness of interface separating each layer. The upper and lower thickness should be always  fixed. The roughness of the topmost layer should be always kept 0.
        Nlayers         : The number of layers in which the layers will be subdivided for applying Parratt formalism
        rrf             : 1 for Frensnel normalized refelctivity and 0 for just reflectivity
        qoff            : q-offset to correct the zero q of the instrument
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
        self.choices={'rrf':[1,0]}
        self.output_params={}
        self.init_params()


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        for key in self.__mpar__.keys():
            for i in range(len(self.__mpar__[key])):
                self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('qoff',self.qoff,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)

    def calcProfile(self):
        """
        Calculates the electron and absorption density profiles
        """
        d=np.array([self.params['__d__%03d'%i].value for i in range(len(self.__mpar__['d']))])
        rho=np.array([self.params['__rho__%03d'%i].value for i in range(len(self.__mpar__['rho']))])
        beta=np.array([self.params['__beta__%03d'%i].value for i in range(len(self.__mpar__['beta']))])
        sig=np.array([self.params['__sig__%03d'%i].value for i in range(len(self.__mpar__['sig']))])
        n=len(d)
        maxsig=np.max(sig)
        self.__z__=np.linspace(-5*maxsig,np.sum(d[:-1])+5*maxsig,self.Nlayers)
        zlayer=self.__z__[1]-self.__z__[0]
        #Condition imposed on sig for rougness less than the thicknesses of the sublayers
        sig=np.where(sig<zlayer,0.1*zlayer,sig)
        drho=np.zeros(self.Nlayers)
        dbeta=np.zeros(self.Nlayers)
        self.__d__=np.diff(self.__z__)
        self.__d__=np.append(self.__d__,[self.__d__[-1]])
        z=d[0]
        for i in range(n-1):
            drho=drho+(rho[i+1]-rho[i])*np.exp(-(self.__z__-z)**2/2.0/sig[i+1]**2)/2.50663/sig[i+1]
            dbeta=dbeta+(beta[i+1]-beta[i])*np.exp(-(self.__z__-z)**2/2.0/sig[i+1]**2)/2.50663/sig[i+1]
            z=z+d[i+1]
        self.__rho__=np.cumsum(drho)*self.__d__[0]
        self.__beta__=np.cumsum(dbeta)*self.__d__[0]
        self.output_params['Electro density profile']={'x':self.__z__,'y':self.__rho__}
        self.output_params['Absorption density profile']={'x':self.__z__,'y':self.__beta__}
        return n




    def y(self):
        """
        Define the function in terms of x to return some value
        """
        n=self.calcProfile()
        x=self.x+self.qoff
        lam=6.62607004e-34*2.99792458e8*1e10/self.E/1e3/1.60217662e-19
        refq,r2=parratt(x,lam,self.__d__,self.__rho__,self.__beta__)
        if self.rrf>0:
            rhos=[self.params['__rho__000'].value,self.params['__rho__%03d'%(n-1)].value]
            betas=[self.params['__beta__000'].value,self.params['__beta__%03d'%(n-1)].value]
            ref,r2=parratt(x,lam,[0.0,1.0],rhos,betas)
            refq=refq/ref
        return refq


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Parratt(x=x)
    print(fun.y())

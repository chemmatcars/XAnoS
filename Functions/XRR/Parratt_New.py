####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
import sys
import os
import math
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_routines/'))
####Please do not remove lines above####

####Import your modules below if needed####
from xr_ref import parratt


class Parratt_New: #Please put the class name same as the function name
    def __init__(self,x=0.1,E=10.0,mpar={'Layers':['top','Bottom'],'d':[0.0,1.0],'rho':[0.0,0.333],'beta':[0.0,0.0],'sig':[0.0,3.0]}, Minstep=0.5, rrf=1, fix_sig=False, qoff=0.0, yscale=1):
        """
        Calculates X-ray reflectivity from a system of multiple layers using Parratt formalism

        x     	: array of wave-vector transfer along z-direction
        E     	: Energy of x-rays in invers units of x
        mpar  	: The layer parameters where, Layers: Layer description, d: thickness of each layer, rho:Electron density of each layer, beta: Absorption coefficient of each layer, sig: roughness of interface separating each layer. The upper and lower thickness should be always  fixed. The roughness of the topmost layer should be always kept 0.
        Minstep 	: The thickness (Angstrom) of each layer for applying Parratt formalism
        rrf   	: 1 for Frensnel normalized refelctivity and 0 for just reflectivity
        qoff  	: q-offset to correct the zero q of the instrument
        yscale  : a scale factor for R or R/Rf
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.E=E
        self.__mpar__=mpar
        self.Minstep=Minstep
        self.rrf=rrf
        self.fix_sig=fix_sig
        self.qoff=qoff
        self.yscale=yscale
        self.choices={'rrf':[1,0],'fix_sig': [True,False]}
        self.output_params={}
        self.init_params()
        self.__fit__=False


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('qoff', self.qoff, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('yscale', self.yscale, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        for key in self.__mpar__.keys():
            if key!='Layers':
                for i in range(len(self.__mpar__[key])):
                    if key=='sig':
                        self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=1e-5,max=np.inf,expr=None,brute_step=0.1)
                    else:
                        self.params.add('__%s__%03d' % (key, i), value=self.__mpar__[key][i], vary=0, min=0, max=np.inf, expr=None, brute_step=0.1)

    def calcProfile(self, d, rho, beta, sig):
        """
        Calculates the electron and absorption density profiles
        """

        if self.fix_sig:
            for i in range(1,len(sig)):
                sig[i]=sig[1]
        n=len(d)
        maxsig=max(np.abs(np.max(sig[1:])),3)
        Nlayers=int((np.sum(d[:-1])+10*maxsig)/self.Minstep)
        halfstep=(np.sum(d[:-1])+10*maxsig)/2/Nlayers
        self.__z__=np.linspace(-5*maxsig+halfstep,np.sum(d[:-1])+5*maxsig-halfstep,Nlayers)
        self.__d__=np.diff(self.__z__)
        self.__d__=np.append(self.__d__,[self.__d__[-1]])
        self.__rho__=self.sldCalFun(d,rho,sig, self.__z__)
        self.__beta__=self.sldCalFun(d,beta,sig, self.__z__)
        if not self.__fit__:
            self.output_params['Electron density profile']={'x':self.__z__,'y':self.__rho__}
            self.output_params['Absorption density profile']={'x':self.__z__,'y':self.__beta__}
        return n

    def sldCalFun(self,d,y,sigma,x):
        wholesld=[]
        for j in range(len(x)):
            sld=0
            for i in range(len(d)-1):
                pos=np.sum(d[:i+1])
                sld=sld+math.erf((x[j]-pos)/sigma[i+1]/math.sqrt(2))*(y[i+1]-y[i])
            wholesld.append(max((sld+y[0]+y[-1])/2,0))
        return wholesld

    def update_parameters(self):
        self.qoff = self.params['qoff'].value
        self.yscale = self.params['yscale'].value
        d = np.array([self.params['__d__%03d' % i].value for i in range(len(self.__mpar__['d']))])
        rho = np.array([self.params['__rho__%03d' % i].value for i in range(len(self.__mpar__['rho']))])
        beta = np.array([self.params['__beta__%03d' % i].value for i in range(len(self.__mpar__['beta']))])
        sig = np.array([self.params['__sig__%03d' % i].value for i in range(len(self.__mpar__['sig']))])
        return d,rho,beta,sig


    def y(self):
        """
        Define the function in terms of x to return some value
        """
        d,rho,beta,sig=self.update_parameters()
        n=self.calcProfile(d,rho,beta,sig)
        x=self.x+self.qoff
        lam=6.62607004e-34*2.99792458e8*1e10/self.E/1e3/1.60217662e-19
        refq,r2=parratt(x,lam,self.__d__,self.__rho__,self.__beta__)
        if self.rrf>0:
            rhos=[self.params['__rho__000'].value,self.params['__rho__%03d'%(n-1)].value]
            betas=[self.params['__beta__000'].value,self.params['__beta__%03d'%(n-1)].value]
            ref,r2=parratt(x-self.qoff,lam,[0.0,1.0],rhos,betas)
            refq=refq/ref
        return refq*self.yscale


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Parratt_New(x=x)
    print(fun.y())

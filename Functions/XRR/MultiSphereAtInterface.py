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


class MultiSphereAtInterface: #Please put the class name same as the function name
    def __init__(self,x=0.1,E=10.0,Rc=10.0,rhoc=4.68,Tsh=20.0,rhosh=0.0,rhoup=0.333,rhodown=0.38,sig=3.0,
                 mpar={'Layers':{'Layers':['Layer 1'],'Z0':[20],'cov':[1.0],'Z0sig':[0.0]}},rrf=True,qoff=0.0,zmin=-10,zmax=100,dz=1.0):
        """
        Calculates X-ray reflectivity from multilayers of core-shell spherical nanoparticles assembled near an interface
        x       	: array of wave-vector transfer along z-direction
        E      	: Energy of x-rays in inverse units of x
        Rc     	: Radius of the core of the nanoparticles
        rhoc   	: Electron density of the core
        Tsh     	: Thickness of the outer shell
        rhosh  	: Electron Density of the outer shell. If 0, the electron density the shell region will be assumed to be filled by the bulk phases depending upon the position of the nanoparticles
        rhoup   	: Electron density of the upper bulk phase
        rhodown 	: Electron density of the lower bulk phase
        sig      	: Roughness of the interface
        mpar     	: The layer parameters where, Z0: position of the layer, cov: coverage of the nanoparticles in the layer, Z0sig: Width of distribution of the nanoparticles in the layer
        rrf     	: 1 for Frensnel normalized refelctivity and 0 for just reflectivity
        qoff    	: q-offset to correct the zero q of the instrument
        zmin    	: minimum depth for electron density calculation
        zmax    	: maximum depth for electron density calculation
        dz      	: minimum slab thickness
        ----------- -----------
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.E=E
        self.Rc=Rc
        self.rhoc=rhoc
        self.Tsh=Tsh
        self.rhosh=rhosh
        self.rhoup=rhoup
        self.rhodown=rhodown
        self.zmin=zmin
        self.zmax=zmax
        self.sig=sig
        self.dz=dz
        self.__mpar__=mpar
        self.rrf=rrf
        self.qoff=qoff
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
        self.params.add('Rc',value=self.Rc,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('rhoc',value=self.rhoc,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('Tsh',value=self.Tsh,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('rhosh',value=self.rhosh,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('sig',value=self.sig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        for mkey in self.__mpar__.keys():
            for key in self.__mpar__[mkey].keys():
                if key !='Layers':
                    for i in range(len(self.__mpar__[mkey][key])):
                        self.params.add('__%s_%s_%03d'%(mkey,key,i),value=self.__mpar__[mkey][key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('qoff',self.qoff,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    @lru_cache(maxsize=10)
    def NpRho(self,z,Rc=10,rhoc=4.68,Tsh=20,rhosh=0.0,Z0=20,rhoup=0.333,rhodown=0.38,cov=1.0):
        z=np.array(z)
        D=Rc+Tsh
        Atot=2*np.sqrt(3)*D**2
        rhos=np.where(z>0,rhodown,rhoup)
        Acore=np.pi*np.sqrt(np.where(z>Z0+Rc,0.0,Rc**2-(z-Z0)**2)*np.where(z<Z0-Rc,0.0,Rc**2-(z-Z0)**2))
        ANp=np.pi*np.sqrt(np.where(z>Z0+D,0.0,D**2-(z-Z0)**2)*np.where(z<Z0-D,0.0,D**2-(z-Z0)**2))
        if rhosh<1e-3:
            return (1-cov)*rhos+cov*((Atot-ANp)*rhos+Acore*(rhoc-rhos)+ANp*rhos)/Atot
        else:
            return (1-cov)*rhos+cov*((Atot-ANp)*rhos+Acore*(rhoc-rhosh)+ANp*rhosh)/Atot

    @lru_cache(maxsize=10)
    def NpRhoGauss(self,z,Rc=10,rhoc=4.68,Tsh=20,rhosh=0.0,Z0=(20),cov=(1.0),Z0sig=(0.0),rhoup=0.333,rhodown=0.38,sig=3.0,Nc=20):
        z=np.array(z)
        if sig<1e-3:
            zt=z
        else:
            zmin=z[0]-5*sig
            zmax=z[-1]+5*sig
            zt=np.arange(zmin,zmax,self.dz)
        rhosum=np.zeros_like(zt)
        for i in range(len(Z0)):
            if Z0sig[i]<1e-3:
                rhosum=rhosum+self.NpRho(tuple(zt),Rc=Rc,rhoc=rhoc,Tsh=Tsh,rhosh=rhosh,Z0=Z0[i],rhoup=rhoup,rhodown=rhodown,cov=cov[i])
            else:
                Z1=np.linspace(Z0[i]-5*Z0sig[i],Z0[i]+5*Z0sig[i],101)
                dist=np.exp(-(Z1-Z0[i])**2/2/Z0sig[i]**2)
                norm=np.sum(dist)
                tsum=np.zeros_like(len(zt))
                for j in range(len(Z1)):
                    tsum=tsum+self.NpRho(tuple(zt),Rc=Rc,rhoc=rhoc,Tsh=Tsh,rhosh=rhosh,Z0=Z1[j],rhoup=rhoup,rhodown=rhodown,cov=cov[i])*dist[j]
                rhosum=rhosum+tsum/norm
        rhos=np.where(zt>0,rhodown,rhoup)
        rho=rhosum-(len(Z0)-1)*rhos
        if sig<1e-3:
            return rho
        else:
            x=np.arange(-5*sig,5*sig,self.dz)
            rough=np.exp(-x**2/2/sig**2)/np.sqrt(2*np.pi)/sig
            res=np.convolve(rho,rough,mode='valid')*self.dz
            if len(res)>len(z):
                return res[0:len(z)]
            else:
                return res

    @lru_cache(maxsize=10)
    def calcProfile(self,Rc,rhoc,rhosh,Z0,cov,Z0sig,Tsh,rhoup,rhodown,sig,zmin,zmax,dz):
        """
        Calculates the electron and absorption density profiles
        """

        __z__=np.arange(zmin,zmax,dz)
        __d__=dz*np.ones_like(__z__)
        __rho__=self.NpRhoGauss(tuple(__z__),Rc=Rc,rhoc=rhoc,Tsh=Tsh,rhosh=rhosh,Z0=tuple(Z0),cov=tuple(cov),
                                Z0sig=tuple(Z0sig),rhoup=rhoup,rhodown=rhodown,sig=sig)
        return __z__,__d__,__rho__


    def update_parameters(self):
        mkey=self.__mkeys__[0]
        self.__Z0__ = tuple([self.params['__%s_Z0_%03d' %(mkey,i)].value for i in range(len(self.__mpar__[mkey]['Z0']))])
        self.__cov__ = tuple([self.params['__%s_cov_%03d' %(mkey,i)].value for i in range(len(self.__mpar__[mkey]['cov']))])
        self.__Z0sig__ = tuple([self.params['__%s_Z0sig_%03d' %(mkey, i)].value for i in range(len(self.__mpar__[mkey]['Z0sig']))])

    @lru_cache(maxsize=10)
    def py_parratt(self, x, lam, d, rho, beta):
        return parratt(x, lam, d, rho, beta)

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params = {'scaler_parameters': {}}
        self.update_parameters()
        z,d,rho=self.calcProfile(self.Rc,self.rhoc,self.rhosh,self.__Z0__,self.__cov__,self.__Z0sig__,self.Tsh,self.rhoup,self.rhodown,
                         self.sig,self.zmin,self.zmax,self.dz)
        if not self.__fit__:
            self.output_params['Total density profile']={'x':z,'y':rho}
            for i in range(len(self.__Z0__)):
                rhonp=self.NpRhoGauss(tuple(z),Rc=self.Rc,rhoc=self.rhoc,Tsh=self.Tsh,rhosh=self.rhosh,Z0=tuple([self.__Z0__[i]]),
                                    cov=tuple([self.__cov__[i]]),Z0sig=tuple([self.__Z0sig__[i]]),rhoup=self.rhoup,rhodown=self.rhodown,sig=self.sig)
                self.output_params['Layer %d contribution'%(i+1)]={'x':z,'y':rhonp,'names':['depth (Angs)','Electron Density (el/Angs^3)']}
        x=self.x+self.qoff
        lam=6.62607004e-34*2.99792458e8*1e10/self.E/1e3/1.60217662e-19
        refq,r2=self.py_parratt(tuple(x),lam,tuple(d),tuple(rho),tuple(np.zeros_like(rho)))
        if self.rrf:
            rhos=(rho[0],rho[-1])
            betas=(0,0)
            ref,r2=self.py_parratt(tuple(x-self.qoff),lam,(0.0,1.0),rhos,betas)
            refq=refq/ref
        return refq


if __name__=='__main__':
    x=np.linspace(0.001,1.0,100)
    fun=MultiSphereAtInterface(x=x)
    print(fun.y())

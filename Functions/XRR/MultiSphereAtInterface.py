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


class MultiSphereAtInterface: #Please put the class name same as the function name
    def __init__(self,x=0.1,E=10.0,Rc=10.0,rhoc=4.68,Tsh=20.0,rhosh=0.0,rhoup=0.333,rhodown=0.38,sig=3.0, mpar={'Layers':['Layer 1'],'Z0':[20],'cov':[1.0],'Z0sig':[0.0]},rrf=1,qoff=0.0,zmin=-10,zmax=100,dz=1.0):
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
        self.choices={'rrf':[1,0]}
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
        for key in self.__mpar__.keys():
            if key !='Layers':
                for i in range(len(self.__mpar__[key])):
                    self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('qoff',self.qoff,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    def NpRho(self,z,Rc=10,rhoc=4.68,Tsh=20,rhosh=0.0,Z0=20,rhoup=0.333,rhodown=0.38,cov=1.0):
        D=Rc+Tsh
        Atot=2*np.sqrt(3)*D**2
        rhos=np.where(z>0,rhodown,rhoup)
        Acore=np.pi*np.sqrt(np.where(z>Z0+Rc,0.0,Rc**2-(z-Z0)**2)*np.where(z<Z0-Rc,0.0,Rc**2-(z-Z0)**2))
        ANp=np.pi*np.sqrt(np.where(z>Z0+D,0.0,D**2-(z-Z0)**2)*np.where(z<Z0-D,0.0,D**2-(z-Z0)**2))
        if rhosh<1e-3:
            return (1-cov)*rhos+cov*((Atot-ANp)*rhos+Acore*(rhoc-rhos)+ANp*rhos)/Atot
        else:
            return (1-cov)*rhos+cov*((Atot-ANp)*rhos+Acore*(rhoc-rhosh)+ANp*rhosh)/Atot

    def NpRhoGauss(self,z,Rc=10,rhoc=4.68,Tsh=20,rhosh=0.0,Z0=[20],cov=[1.0],Z0sig=[0.0],rhoup=0.333,rhodown=0.38,sig=3.0,Nc=20):
        if sig<1e-3:
            zt=z
        else:
            zmin=z[0]-5*sig
            zmax=z[-1]+5*sig
            zt=np.arange(zmin,zmax,self.dz)
        rhosum=np.zeros_like(zt)
        for i in range(len(Z0)):
            if Z0sig[i]<1e-3:
                rhosum=rhosum+self.NpRho(zt,Rc=Rc,rhoc=rhoc,Tsh=Tsh,rhosh=rhosh,Z0=Z0[i],rhoup=rhoup,rhodown=rhodown,cov=cov[i])
            else:
                Z1=np.linspace(Z0[i]-5*Z0sig[i],Z0[i]+5*Z0sig[i],101)
                dist=np.exp(-(Z1-Z0[i])**2/2/Z0sig[i]**2)
                norm=np.sum(dist)
                tsum=np.zeros_like(len(zt))
                for j in range(len(Z1)):
                    tsum=tsum+self.NpRho(zt,Rc=Rc,rhoc=rhoc,Tsh=Tsh,rhosh=rhosh,Z0=Z1[j],rhoup=rhoup,rhodown=rhodown,cov=cov[i])*dist[j]
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

    def calcProfile(self, Z0, cov, Z0sig):
        """
        Calculates the electron and absorption density profiles
        """
        self.__z__=np.arange(self.zmin,self.zmax,self.dz)
        self.__d__=self.dz*np.ones_like(self.__z__)
        self.__rho__=self.NpRhoGauss(self.__z__,Rc=self.Rc,rhoc=self.rhoc,Tsh=self.Tsh,rhosh=self.rhosh,Z0=Z0,cov=cov,Z0sig=Z0sig,rhoup=self.rhoup,rhodown=self.rhodown,sig=self.sig)
        self.output_params['Total density profile']={'x':self.__z__,'y':self.__rho__}
        for i in range(len(Z0)):
            rho=self.NpRhoGauss(self.__z__,Rc=self.Rc,rhoc=self.rhoc,Tsh=self.Tsh,rhosh=self.rhosh,Z0=[Z0[i]],cov=[cov[i]],Z0sig=[Z0sig[i]],rhoup=self.rhoup,rhodown=self.rhodown,sig=self.sig)
            self.output_params['Layer %d contribution'%(i+1)]={'x':self.__z__,'y':rho}

    def update_parameters(self):
        self.Rc = self.params['Rc'].value
        self.rhoc = self.params['rhoc'].value
        self.Tsh = self.params['Tsh'].value
        self.rhosh = self.params['rhosh'].value
        self.sig = self.params['sig'].value
        Z0 = np.array([self.params['__Z0__%03d' % i].value for i in range(len(self.__mpar__['Z0']))])
        cov = np.array([self.params['__cov__%03d' % i].value for i in range(len(self.__mpar__['cov']))])
        Z0sig = np.array([self.params['__Z0sig__%03d' % i].value for i in range(len(self.__mpar__['Z0sig']))])
        return Z0, cov, Z0sig

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params={}
        Z0, cov, Z0sig = self.update_parameters()
        self.calcProfile(Z0, cov, Z0sig)
        x=self.x+self.qoff
        lam=6.62607004e-34*2.99792458e8*1e10/self.E/1e3/1.60217662e-19
        refq,r2=parratt(x,lam,self.__d__,self.__rho__,np.zeros_like(self.__rho__))
        if self.rrf>0:
            rhos=[self.__rho__[0],self.__rho__[-1]]
            betas=[0,0]
            ref,r2=parratt(x-self.qoff,lam,[0.0,1.0],rhos,betas)
            refq=refq/ref
        return refq


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=MultiSphereAtInterface(x=x)
    print(fun.y())

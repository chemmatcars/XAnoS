import numpy as np
from lmfit import Parameters
import sys
import os
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
from utils import find_minmax
from PeakFunctions import Gaussian, LogNormal

class Sphere:
    def __init__(self, x=0.001, R=1.0, Rsig=0.0, dist='Gaussian', N=50, rhoc=1.0, rhosol=0.0, norm=1.0, bkg=0.0,mpar={}):
        """
        Calculates the form factor of a solid sphere with size distribution
        x     	: Array of q-values in the same reciprocal unit as R and Rsig
        R     	: Mean radius of the solid spheres
        Rsig  	: Width of the distribution of solid spheres
        dist  	: Gaussian or LogNormal
        N     	: No. of points on which the distribution will be calculated
        rhoc  	: Electron density of the particle
        rhosol	: Electron density of the solvent or surrounding environment
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.R=R
        self.Rsig=Rsig
        self.dist=dist
        self.rhoc=rhoc
        self.rhosol=rhosol
        self.norm=norm
        self.bkg=bkg
        self.N=N
        self.__mpar__=mpar
        self.choices={'dist':['Gaussian','LogNormal']}
        self.init_params()

    def init_params(self):
        self.params=Parameters()
        self.params.add('R',value=self.R,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('Rsig',value=self.Rsig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('rhoc',value=self.rhoc,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('rhosol',value=self.rhosol,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    def y(self):
        rho=self.rhoc-self.rhosol
        self.output_params={}
        if self.Rsig<1e-3:
            return self.norm*rho**2*(np.sin(self.x*self.R)-self.x*self.R*np.cos(self.x*self.R))**2/self.x**6+self.bkg
        else:
            if self.dist=='Gaussian':
                gau=Gaussian.Gaussian(x=0.001,pos=self.R,wid=self.Rsig)
                rmin,rmax=find_minmax(gau,self.R,self.Rsig)
                r=np.linspace(rmin,rmax,self.N)
                gau.x=r
                dist=gau.y()
                sumdist=np.sum(dist)
                self.output_params['Distribution']={'x':r,'y':dist/sumdist}
                if type(self.x)==np.ndarray:
                    ffactor=[]
                    for x in self.x:
                        f=np.sum((np.sin(x*r)-x*r*np.cos(x*r))**2*dist/x**6)
                        ffactor.append(f/sumdist)
                    return self.norm*rho**2*np.array(ffactor)+self.bkg
                else:
                    return self.norm*rho**2*np.sum((np.sin(self.x*r)-self.x*r*np.cos(self.x*r))**2*dist/self.x**6)/sumdist+self.bkg
            elif self.dist=='LogNormal':
                lgn=LogNormal.LogNormal(x=0.001,pos=self.R,wid=self.Rsig)
                rmin,rmax=find_minmax(lgn,self.R,self.Rsig)
                r=np.linspace(rmin,rmax,self.N)
                lgn.x=r
                dist=lgn.y()
                sumdist=np.sum(dist)
                self.output_params['Distribution']={'x':r,'y':dist/sumdist}
                if type(self.x)==np.ndarray:
                    ffactor=[]
                    for x in self.x:
                        f=np.sum((np.sin(x*r)-x*r*np.cos(x*r))**2*dist/x**6)
                        ffactor.append(f/sumdist)
                    return self.norm*rho**2*np.array(ffactor)+self.bkg
                else:
                    return self.norm*rho**2*np.sum((np.sin(self.x*r)-self.x*r*np.cos(self.x*r))**2*dist/self.x**6)/sumdist+self.bkg
            else:
                return np.ones_like(x)


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Sphere(x=x)
    print(fun.y())

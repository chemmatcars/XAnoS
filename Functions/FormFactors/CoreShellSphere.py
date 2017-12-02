import numpy as np
from lmfit import Parameters
import sys
import os
sys.path.append(os.path.abspath('./'))
sys.path.append(os.path.abspath('./Functions'))
from utils import find_minmax
from PeakFunctions import Gaussian, LogNormal


class CoreShellSphere:
    def __init__(self, x=0.001, R=1.0, Rsig=0.0, rhoc=1.0, sh=1.0, shsig=0.0, dist='Gaussian', N=50, rhosh=0.5, rhosol=0.0, norm=1.0, bkg=0.0,mpar={}):
        """
        This class calculates the form factor of a spherical core-shell structure with size and shell thickness distribution
        x: single or Array of q-values in the reciprocal unit as R and Rsig
        R: Mean radius of the solid spheres
        Rsig: Width of the distribution of solid spheres
        rhoc: Electron density of the core
        sh: Shell thicknes
        shsig: Width of distribution of shell thicknesses
        rhosh: Electron density of the shell
        dist: Gaussian or LogNormal
        N: No. of points on which the distribution will be calculated
        rhosol: Electron density of the surrounding solvent/media
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.R=R
        self.Rsig=Rsig
        self.rhoc=rhoc
        self.sh=sh
        self.shsig=shsig
        self.rhosh=rhosh
        self.rhosol=rhosol
        self.dist=dist
        self.norm=norm
        self.bkg=bkg
        self.N=N
        self.__mpar__=mpar
        self.choices={'dist':['Gaussian','LogNormal']}
        self.output_params={}

    def init_params(self):
        self.params=Parameters()
        self.params.add('R',value=self.R,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('Rsig',value=self.Rsig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('rhoc',value=self.rhoc,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('sh',value=self.sh,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('shsig',value=self.shsig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('rhosh',value=self.rhosh,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('rhosol',value=self.rhosol,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)

    def coreshell(self,x,R,rhoc,sh,rhosh,rhosol):
        """
        Computes the form factor a monodisperse core-shell structure
        """
        Rsh=R+sh
        amp=((rhoc-rhosh)*(np.sin(x*R)-x*R*np.cos(x*R))+(rhosh-rhosol)*(np.sin(x*Rsh)-x*Rsh*np.cos(x*Rsh)))/x**3
        return amp, amp**2


    def y(self):
        if self.Rsig<1e-3 and self.shsig<1e-3:
            amp,res= self.coreshell(self.x,self.R,self.rhoc,self.sh,self.rhosh,self.rhosol)
            self.rdist=None
            self.sdist=None
            return self.norm*res+self.bkg
        elif self.Rsig>1e-3 and self.shsig<1e-3:
            if self.dist=='Gaussian':
                gau=Gaussian.Gaussian(x=0.001,mu=self.R,sig=self.Rsig)
                rmin,rmax=find_minmax(gau,self.R,self.Rsig)
                r=np.linspace(rmin,rmax,self.N)
                gau.x=r
                dist=gau.y()
                sumdist=np.sum(dist)
                self.output_params['Distribution']={'x':r,'y':dist/sumdist}
                if type(self.x)==np.ndarray:
                    ffactor=[]
                    for x in self.x:
                        amp,res=self.coreshell(x,r,self.rhoc,self.sh,self.rhosh,self.rhosol)
                        f=np.sum(res*dist)
                        ffactor.append(f/sumdist)
                    return self.norm*np.array(ffactor)+self.bkg
                else:
                    amp,res=self.coreShell(self.x,r,self.rhoc,self.sh,self.rhosh,self.rhosol)
                    return self.norm*np.sum(res*dist)/sumdist+self.bkg
            elif self.dist=='LogNormal':
                lgn=LogNormal.LogNormal(x=0.001,mu=self.R,sig=self.Rsig)
                rmin,rmax=find_minmax(lgn,self.R,self.Rsig)
                r=np.linspace(rmin,rmax,self.N)
                lgn.x=r
                dist=lgn.y()
                sumdist=np.sum(dist)
                self.output_params['Distribution']={'x':r,'y':dist/sumdist}
                if type(self.x)==np.ndarray:
                    ffactor=[]
                    for x in self.x:
                        amp,res=self.coreshell(x,r,self.rhoc,self.sh,self.rhosh,self.rhosol)
                        f=np.sum(res*dist)
                        ffactor.append(f/sumdist)
                    return self.norm*np.array(ffactor)+self.bkg
                else:
                   amp,res=self.coreshell(self.x,r,self.rhoc,self.sh,self.rhosh,self.rhosol)
                   return self.norm*np.sum(res*dist)/sumdist+self.bkg
            else:
                #amp,res=self.coreshell(self.x,self.R,self.rhoc,self.sh,self.rhosh)
                return np.ones_like(self.x)
        elif self.Rsig<1e-3 and self.shsig>1e-3:
            if self.dist=='Gaussian':
                gau=Gaussian.Gaussian(x=0.001,mu=self.sh,sig=self.shsig)
                shmin,shmax=find_minmax(gau,self.sh,self.shsig)
                sh=np.linspace(shmin,shmax,self.N)
                gau.x=sh
                dist=gau.y()
                sumdist=np.sum(dist)
                self.output_params['Distribution']={'x':sh,'y':dist/sumdist}
                if type(self.x)==np.ndarray:
                    ffactor=[]
                    for x in self.x:
                        amp,res=self.coreshell(x,self.R,self.rhoc,sh,self.rhosh,self.rhosol)
                        f=np.sum(res*dist)
                        ffactor.append(f/sumdist)
                    return self.norm*np.array(ffactor)+self.bkg
                else:
                    amp,res=self.coreShell(self.x,self.R,self.rhoc,sh,self.rhosh,self.rhosol)
                    return self.norm*np.sum(res*dist)/sumdist+self.bkg
            elif self.dist=='LogNormal':
                lgn=LogNormal.LogNormal(x=0.001,mu=self.sh,sig=self.shsig)
                shmin,shmax=find_minmax(lgn,self.sh,self.shsig)
                sh=np.linspace(shmin,shmax,self.N)
                lgn.x=sh
                dist=lgn.y()
                sumdist=np.sum(dist)
                self.output_params['Distribution']={'x':sh,'y':dist/sumdist}
                if type(self.x)==np.ndarray:
                    ffactor=[]
                    for x in self.x:
                        amp,res=self.coreshell(x,self.R,self.rhoc,sh,self.rhosh,self.rhosol)
                        f=np.sum(res*dist)
                        ffactor.append(f/sumdist)
                    return self.norm*np.array(ffactor)+self.bkg
                else:
                   amp,res=self.coreshell(self.x,self.R,self.rhoc,sh,self.rhosh,self.rhosol)
                   return self.norm*np.sum(res*dist)/sumdist+self.bkg
            else:
                #amp,res=self.coreshell(self.x,self.R,self.rhoc,self.sh,self.rhosh)
                return np.ones_like(self.x)
        else:
            if self.dist=='Gaussian':
                gau=Gaussian.Gaussian(x=0.001,mu=self.R,sig=self.Rsig)
                rmin,rmax=find_minmax(gau,self.R,self.Rsig)
                r=np.linspace(rmin,rmax,self.N)
                shmin,shmax=find_minmax(gau,self.sh,self.shsig)
                sh=np.linspace(shmin,shmax,self.N)
                R,Sh=np.meshgrid(r,sh)
                dist=np.exp(-(R-self.R)**2/2.0/self.Rsig**2)*np.exp(-(Sh-self.sh)**2/2.0/self.shsig**2)
                sumdist=np.sum(dist)
                self.output_params['Distribution']={'x':R,'y':Sh,'z':dist/sumdist}
                if type(self.x)==np.ndarray:
                    ffactor=[]
                    for x in self.x:
                        amp,res=self.coreshell(x,R,self.rhoc,Sh,self.rhosh,self.rhosol)
                        f=np.sum(res*dist)
                        ffactor.append(f/sumdist)
                    return self.norm*np.array(ffactor)+self.bkg
                else:
                    amp,res=self.coreShell(self.x,R,self.rhoc,Sh,self.rhosh,self.rhosol)
                    return self.norm*np.sum(res*dist)/sumdist+self.bkg
            elif self.dist=='LogNormal':
                lgn=LogNormal.LogNormal(x=0.001,mu=self.R,sig=self.Rsig)
                rmin,rmax=find_minmax(lgn,self.R,self.Rsig)
                r=np.linspace(rmin,rmax,self.N)
                shmin,shmax=find_minmax(lgn,self.sh,self.shsig)
                sh=np.linspace(shmin,shmax,self.N)
                R,Sh=np.meshgrid(r,sh)
                dist=np.exp(-(np.log(R)-np.log(self.R))**2/2.0/self.Rsig**2)*np.exp(-(np.log(Sh)-np.log(self.sh))**2/2.0/self.shsig**2)/R/Sh
                sumdist=np.sum(dist)
                self.rdist,self.shdist=R,Sh
                self.srshdist=dist/sumdist
                if type(self.x)==np.ndarray:
                    ffactor=[]
                    for x in self.x:
                        amp,res=self.coreshell(x,R,self.rhoc,Sh,self.rhosh,self.rhosol)
                        f=np.sum(res*dist)
                        ffactor.append(f/sumdist)
                    return self.norm*np.array(ffactor)+self.bkg
                else:
                    amp,res=self.coreShell(self.x,R,self.rhoc,Sh,self.rhosh,self.rhosol)
                    return self.norm*np.sum(res*dist)/sumdist+self.bkg
            else:
                #amp,res=self.coreshell(self.x,self.R,self.rhoc,self.sh,self.rhosh)
                return np.ones_like(self.x)







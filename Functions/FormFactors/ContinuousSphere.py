import numpy as np
from lmfit import Parameters
import sys
import os
sys.path.append(os.path.abspath('./'))
sys.path.append(os.path.abspath('./Functions'))
from utils import find_minmax
from PeakFunctions import Gaussian, LogNormal



class ContinuousSphere:

    def __init__(self,x=0.001,Rsig=0.0,dist='Gaussian',N=50,norm=1.0,bkg=0.0,mpar={'R':[10.0,11.0],'rho':[1.0,0.0]}):
        """
        This calculates the form factor of a sphere with continous electron density gradient along the radial direction

        x			: single or array of q-values in the reciprocal unit as R
        R			: An array of radial locations
        rho		: Electron density at the locations R
        Rsig		: Width of the distribution of all the radial locations
        N			: No. of points on which the distribution will be calculated
        dist		: 'Gaussian' or 'LogNormal'
        norm		: Normalization constant
        bkg		: Constant Bkg
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.Rsig=Rsig
        self.norm=norm
        self.dist=dist
        self.bkg=bkg
        self.N=N
        self.__mpar__=mpar
        self.choices={'dist':['Gaussian','LogNormal']}
        self.output_params={}
        self.init_params()

    def init_params(self):
        self.params=Parameters()
        for key in self.__mpar__.keys():
            for i in range(len(self.__mpar__[key])):
                self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('Rsig',value=self.Rsig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)

    def csphere(self,r,rho):
        r=np.array(r)
        drho=np.diff(rho)
        res=[]
        for x in self.x:
            res.append(np.sum(drho*(np.sin(x*r[1:])-x*r[1:]*np.cos(x*r[1:]))/x**3))
        return np.array(res)**2

    def y(self):
        self.output_params={}
        R=[self.params['__R__%03d'%i] for i in range(len(self.__mpar__['R']))]
        rho=[self.params['__rho__%03d'%i] for i in range(len(self.__mpar__['rho']))]
        if self.Rsig<0.001:
            return self.norm*self.csphere(R,rho)+self.bkg
        else:
            if self.dist=='Gaussian':
                gau=Gaussian.Gaussian(x=0.0,pos=R[0],wid=self.Rsig)
                rmin,rmax=find_minmax(gau,pos=R[0],wid=self.Rsig)
                dr=np.linspace(rmin,rmax,self.N)
                gau.x=dr
                dist=gau.y()
                sumdist=np.sum(dist)
                self.output_params['Distribution']={'x':dr,'y':dist/sumdist}
                res=np.zeros_like(self.x)
                for i in range(len(dr)):
                    r=R+dr[i]-R[0]
                    res=res+dist[i]*self.csphere(r,rho)
                return self.norm*res/sumdist+self.bkg

            elif self.dist=='LogNormal':
                lgn=LogNormal.LogNormal(x=0.0,pos=R[0],wid=self.Rsig)
                rmin,rmax=find_minmax(lgn,pos=R[0],wid=self.Rsig)
                dr=np.linspace(rmin,rmax,self.N)
                lgn.x=dr
                dist=lgn.y()
                sumdist=np.sum(dist)
                self.output_params['Distribution']={'x':dr,'y':dist/sumdist}
                res=np.zeros_like(self.x)
                for i in range(len(dr)):
                    r=R+dr[i]-R[0]
                    res=res+dist[i]*self.csphere(r,rho)
                return self.norm*res/sumdist+self.bkg
            else:
                return np.ones_like(self.x)






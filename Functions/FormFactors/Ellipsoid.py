import numpy as np
from lmfit import Parameters
import sys
import os
sys.path.append(os.path.abspath('./'))
sys.path.append(os.path.abspath('./Functions'))
from functools import lru_cache

from ff_ellipsoid import ff_ellipsoid
from PeakFunctions import Gaussian, LogNormal
from utils import find_minmax



class Ellipsoid:

    def __init__(self, x=0.001,R=1.0,Rsig=0.0,RHratio=1.0,aspect=1.0,Nalf=200,Np=20,norm=1.0,bkg=0.0,dist='Gaussian',
                 mpar={}):
        """
        Calculates the form factor of an ellipsoid with particle size distribution

        x      	: Single or Array of q-values in the reciprocal unit as R1 and R2
        R    	: Most probable Semi major axis
        Rsig    : Width of the distribution of Semi-major axis
        dist    : 'Gaussian' or 'LogNormal' distribution for the particle size distribution
        aspect  : Aspect Ratio H/R
        Nalf    : Number of azimuthal angles between 0 and 180 degrees for azimuthal integration
        Np      : Number of particle sizes drawn from the distribution to implement particle size distribution
        norm  	: Normalization constant
        bkg   	: Constant Bkg
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.R = R
        self.Rsig = Rsig
        self.dist = dist
        self.aspect = aspect
        self.Nalf = Nalf
        self.Np = Np
        self.norm = norm
        self.bkg = bkg
        self.choices = {'dist':['Gaussian', 'LogNormal']}
        self.__mpar__=mpar
        self.output_params={'scaler_parameters':{}}
        self.init_params()

    def init_params(self):
        self.params=Parameters()
        self.params.add('R',value=self.R,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('Rsig',value=self.Rsig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('aspect',value=self.aspect,vary=0,min=0,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    @lru_cache(maxsize=10)
    def calc_Rdist(self, R, Rsig, dist, Np):
        if Rsig > 0.001:
            fdist = eval(dist + '.' + dist + '(x=0.001, pos=R, wid=Rsig)')
            rmin, rmax = find_minmax(fdist, R, Rsig)
            dr = np.linspace(rmin, rmax, Np)
            fdist.x = dr
            rdist = fdist.y()
            sumdist = np.sum(rdist)
            rdist = rdist / sumdist
            self.output_params['Distribution'] = {'x': dr, 'y': rdist}
            return dr, rdist
        else:
            return [R], [1.0]


    @lru_cache(maxsize=10)
    def ellipsoid_dist(self,q,R,Rsig,dist,aspect,Nalf,Np):
        r,rdist=self.calc_Rdist(R,Rsig,dist,Np)
        form=np.zeros_like(q)
        for i,tr in enumerate(r):
            form=form+rdist[i]*self.py_ellipsoid(q,tr,aspect,Nalf)
        return form

    @lru_cache(maxsize=10)
    def py_ellipsoid(self,q,R,aspect,Nalf):
        ff,aff=ff_ellipsoid(q,R,aspect,Nalf)
        return ff

    def y(self):
        """
        Computes the form factor of an ellipsoid
        """
        self.output_params={'scaler_paramters':{}}
        return self.norm*self.ellipsoid_dist(tuple(self.x),self.R,self.Rsig,self.dist,self.aspect,self.Nalf,self.Np)+self.bkg






import numpy as np
from lmfit import Parameters
import sys
import os
sys.path.append(os.path.abspath('./'))
sys.path.append(os.path.abspath('./Functions'))



class Ellipsoid:

    def __init__(self, x=0.001,R1=1.0,R2=1.0,rhoc=1.0,rhosol=0.0,norm=1.0,bkg=0.0,mpar={}):
        """
        Calculates the form factor of an ellipsoid

        x			: Single or Array of q-values in the reciprocal unit as R1 and R2
        R1		:  Semi-minor of the ellipsoid
        R2		: Semi-major axis of the ellipsoid
        rhoc				: Electron density of the ellipsoid
        rhosol			: Electron density of the surrounding media/solvent
        norm		: Normalization constant
        bkg		: Constant Bkg
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.R1=R1
        self.R2=R2
        self.rhoc=rhoc
        self.rhosol=rhosol
        self.norm=norm
        self.bkg=bkg
        self.choices=None
        self.__mpar__=mpar
        self.output_params={}

    def init_params(self):
        self.params=Parameters()
        self.params.add('R1',value=self.R1,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('R2',value=self.R2,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('rhoc',value=self.rhoc,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('rhosol',value=self.rhosol,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)


    def y(self):
        """
        Computes the form factor of an ellipsoid
        """
        self.output_params={}
        r=lambda a: np.sqrt((self.R1*np.sin(a))**2+(self.R2*np.cos(a))**2)
        ang=np.linspace(0,np.pi/2.0,91)
        if type(self.x)==np.ndarray:
            ffactor=[]
            for x in self.x:
                f=lambda a: (np.sin(x*r(a))-x*r(a)*np.cos(x*r(a)))**2/(x*r(a))**6*np.sin(a)
                ffactor.append(np.sum(f(ang)))
            return self.norm*9*(self.rhoc-self.rhosol)**2*np.array(ffactor)+self.bkg
        else:
            f=lambda a: (np.sin(self.x*r(a))-self.x*r(a)*np.cos(self.x*r(a)))**2/(self.x*r(a))**6*np.sin(a)
            ffactor=np.sum(f(ang))
            return self.norm*9*(self.rhoc-self.rhosol)**2*ffactor+self.bkg






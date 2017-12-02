import numpy as np
from lmfit import Parameters

class Gaussian:
    def __init__(self,x=0.0,mu=0.5,sig=0.1,norm=1.0,bkg=0.0,mpar={}):
        """
        Provides Gaussian function
        x: Scalar or array of values
        mu: Peak position
        sig: Width
        norm: Normalization constant
        bkg: Constant background
        """
        self.x=x
        self.mu=mu
        self.sig=sig
        self.norm=norm
        self.bkg=0.0
        self.__mpar__=mpar
        self.choices={}
        self.output_params={}

    def init_params(self):
        self.params=Parameters()
        self.params.add('mu',value=self.mu,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('sig',value=self.sig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)


    def y(self):
        return self.norm*np.exp(-(self.x-self.mu)**2/2.0/self.sig**2)/self.sig/2.5066+self.bkg

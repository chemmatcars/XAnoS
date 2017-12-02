import numpy as np
from lmfit import Parameters

class LogNormal:
    """
    Provides log-normal function
    """
    def __init__(self,x=0.0,mu=0.5,sig=0.1,norm=1.0,bkg=0.0,mpar={}):
        """
        Provides log-normal function y=norm*exp(-(log(x)-log(mu))**2/2/sig**2)/sqrt(2*pi)/sig/x+bkg
        x: scalar or array of values
        mu: Peak of the Gaussian part of the distribution
        sig: Width of the Gaussian part of the distribution
        norm: Normalization constant
        bkg: Constant background
        """
        self.x=x
        self.mu=mu
        self.sig=sig
        self.norm=norm
        self.bkg=bkg
        self.__mpar__=mpar
        self.choices=None
        self.output_params={}

    def init_params(self):
        self.params=Parameters()
        self.params.add('mu',value=self.mu,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('sig',value=self.sig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)


    def y(self):
        return self.norm*np.exp(-(np.log(self.x)-np.log(self.mu))**2/2.0/self.sig**2)/self.x/self.sig/2.5066+self.bkg


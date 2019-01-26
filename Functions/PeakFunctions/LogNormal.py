import numpy as np
from lmfit import Parameters

class LogNormal:
    """
    Provides log-normal function
    """
    def __init__(self,x=0.0,pos=0.5,wid=0.1,norm=1.0,bkg=0.0,mpar={}):
        """
        Provides log-normal function y=norm*exp(-(log(x)-log(pos))**2/2/wid**2)/sqrt(2*pi)/wid/x+bkg
        x: scalar or array of values
        pos: Peak of the Gaussian part of the distribution
        wid: Width of the Gaussian part of the distribution
        norm: Normalization constant
        bkg: Constant background
        """
        self.x=x
        self.pos=pos
        self.wid=wid
        self.norm=norm
        self.bkg=bkg
        self.__mpar__=mpar
        self.choices=None
        self.init_params()

    def init_params(self):
        self.params=Parameters()
        self.params.add('pos',value=self.pos,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('wid',value=self.wid,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        
    def update_params(self):
        self.params['pos'].value=self.pos
        self.params['wid'].value=self.wid
        self.params['norm'].value=self.norm
        self.params['bkg'].value=self.bkg


    def y(self):
        self.output_params={}
        self.update_params()
        return self.norm*np.exp(-(np.log(self.x)-np.log(self.pos))**2/2.0/self.wid**2)/self.x/self.wid/2.5066+self.bkg


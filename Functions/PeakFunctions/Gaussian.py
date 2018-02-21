import numpy as np
from lmfit import Parameters

class Gaussian:
    def __init__(self,x=0.0,pos=0.5,wid=0.1,norm=1.0,bkg=0.0,mpar={}):
        """
        Documentation:
        Provides Gaussian function
        x       : Scalar or array of values
        pos     : Peak position
        wid     : Width
        norm    : Normalization constant
        bkg     : Constant background
        """
        self.x=x
        self.pos=pos
        self.wid=wid
        self.norm=norm
        self.bkg=0.0
        self.__mpar__=mpar
        self.choices={}
        self.output_params={}
        self.init_params()
    
    def gau(self,x,pos,wid,norm):
        """
        Gaussian function
        """
        return norm*np.exp(-4.0*np.log(2)*(x-pos)**2/wid**2)

    def init_params(self):
        self.params=Parameters()
        self.params.add('pos',value=self.pos,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('wid',value=self.wid,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)


    def y(self):
        pos=self.params['pos'].value
        wid=self.params['wid'].value
        norm=self.params['norm'].value
        return self.gau(self.x,pos,wid,norm)+self.bkg

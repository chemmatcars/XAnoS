####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
import sys
import os
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_rountines'))
####Please do not remove lines above####

####Import your modules below if needed####
from scipy.special import j1
from scipy.integrate import quad, romb



class Cylinder: #Please put the class name same as the function name
    def __init__(self,x=0, R=1.0, Rsig=0.0, H=1.0, Hsig=0.0, dist='Gaussian', norm=1.0,bkg=0.0, mpar={}):
        """
        Form factor of a poly-dispersed cylinder
        x           : Independent variable in the form of a scalar or an array of Q-values
        R           : Radius of the cylinder in the same inverse unit as Q
        Rsig        : Width of the distribution in R
        H           : Length/Height of the cylinder in the same inverse unit as Q
        Hsig        : Width of the distribution in H
        dist        : The type of distribution: "Gaussian" or "LogNormal"
        norm        : Normalization constant
        bkg         : Additive constant background
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.R=R
        self.Rsig=Rsig
        self.H=H
        self.Hsig=Hsig
        self.dist=dist
        self.norm=norm
        self.bkg=bkg
        self.__mpar__=mpar #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.init_params()

    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value = 0, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = None)
        """
        self.params=Parameters()
        self.params.add('R',value=self.R,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('Rsig',value=self.Rsig,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('H',value=self.H,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('Hsig',value=self.Hsig,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('R',value=self.R,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',value=self.norm,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg', value=self.bkg, min=-np.inf, max=np.inf, expr=None, brute_step=None)

    def cyl_form(self,mu,q,R,H):
        """
        Computes the amplitute of cylinderical form factor
        """
        x=q*mu*H/2
        y=q*np.sqrt(1-mu**2)*R
        if mu==0.0:
            return (2*j1(y)/y)**2
        elif np.abs(mu)==1.0:
            return (2*np.sin(x)/x)**2
        else:
            return (np.sin(x)/x*2*j1(y)/y)**2

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params={}
        R=self.params['R'].value
        Rsig=self.params['Rsig'].value
        H=self.params['H'].value
        Hsig=self.params['Hsig'].value
        norm=self.params['norm'].value
        bkg=self.params['bkg'].value
        mu=np.linspace(-1,1,101)
        res=[]
        for q in self.x:
            res.append(romb(self.cyl_form(mu,q,R,H)))
        res=np.array(res)/2.0
        return norm*res+bkg


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Cylinder(x=x)
    print(fun.y())

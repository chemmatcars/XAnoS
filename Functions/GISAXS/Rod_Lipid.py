# import necessary modules for the class
from lmfit import Parameters #Please do not remove this line
import numpy as np
import sys
import os
from scipy import special
sys.path.append(os.path.abspath('./Functions'))

class Rod_Lipid: #Please put the class name same as the function name
    def __init__(self,x=0, E=10.0, alpha=0.1,  H_lipid=20, qc=0.0217,sig=0.0,norm=1.0, qz_cen=0.0, qoff=0.0, bkg=0.0,mpar={}):
        """
        Provides rod scan from spherical objects dispersed on a substrate
        x       	: Array of Qz values of rod scan
        E           : Energy of X-ray in unit of keV
        alpha       : incident angle in unit of degree
        H_lipid      : height of lipids in unit of \AA
        qc     	: Critcal wave-vector for the substrate on which sphere are aranged
        sig         : relative rms fluctuation between two particles
        norm   	: Normalization constant
        qz_cen  : center for the out-of-plane peak; or 0 for the in-plane peak
        qoff    : qz offset in unit of \AA^-1
        bkg    	: Constant background
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.E=E
        self.alpha=alpha
        self.H_lipid=H_lipid
        self.qc=qc
        self.norm=norm
        self.qz_cen=qz_cen
        self.qoff=qoff
        self.bkg=bkg
        self.sig=sig
        self.__mpar__=mpar
        self.choices={}
        self.output_params={'scaler_parameters':{}}


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('H_lipid',value=self.H_lipid,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('qc',value=self.qc,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('qz_cen', value=self.qz_cen, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('sig',value=self.sig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('qoff', value=self.qoff, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)


    def trans(self,qz,qc):
        """
        Calculates the transmission Coefficient
        """
        qz = qz.clip(min=0)
        tr=2.0*qz/(qz+np.sqrt(qz**2-qc**2+0j))
        return np.abs(tr)**2

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        x=self.x+self.qoff
        k0=2*np.pi*self.E/12.3984
        qbeta=x-k0*np.sin(self.alpha/180*np.pi)
        x=x-self.qz_cen
        formfac = special.spherical_jn(0,x*self.H_lipid/2)**2
        #formfac = ((np.sin(x * self.H_lipid / 2)) / (x * self.H_lipid / 2)) ** 2
        res = self.trans(qbeta, self.qc / 2) * formfac * self.norm * np.exp(-x ** 2 * self.sig ** 2) + self.bkg

        if not self.__fit__:
            self.output_params['scaler_parameters'] = {}
        return res


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Rod_Sphere(x=x)
    print(fun.y())

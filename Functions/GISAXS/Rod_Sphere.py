# import necessary modules for the class
from lmfit import Parameters #Please do not remove this line
import numpy as np
import sys
import os
sys.path.append(os.path.abspath('./Functions'))
from FormFactors import Sphere

class Rod_Sphere: #Please put the class name same as the function name
    def __init__(self,x=0, R=10.0, Rsig=1.0, dist='Gaussian', qc=0.0217, qpar=0.1, qparsig=0.0,N=50,sig=0.0,norm=1.0, bkg=0.0,mpar={}):
        """
        Provides rod scan from spherical objects dispersed on a substrate
        x       	: Array of Qz values of rod scan
        R       	: Mean radius of spheres in inverse units of Qz
        Rsig   	: Width of distribution of spheres in inverse units of Qz
        dist   	: 'Gaussian' or 'LogNormal'
        qc     	: Critcal wave-vector for the substrate on which sphere are aranged
        qpar   	: In-plane wave-vector at which the rod was measured
        qparsig	: The width of the peak at which the rod was measured
        sig         : relative rms fluctuation between two particles
        norm   	: Normalization constant
        bkg    	: Constant background
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.R=R
        self.Rsig=Rsig
        self.dist=dist
        self.qc=qc
        self.qpar=qpar
        self.qparsig=qparsig
        self.norm=norm
        self.bkg=bkg
        self.sig=sig
        self.N=N
        self.__mpar__=mpar
        self.choices={'dist':['Gaussian','LogNormal']}
        self.output_params={}


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('R',value=self.R,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('Rsig',value=self.Rsig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('qc',value=self.qc,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('sig',value=self.sig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    def trans(self,qz,qc):
        """
        Calculates the transmission Coefficient
        """
        tr=2.0*qz/(qz+np.sqrt(qz**2-qc**2+0j))
        return np.abs(tr)**2

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params={}
        R=self.params['R']
        Rsig=self.params['Rsig']
        qc=self.params['qc']
        norm=self.params['norm']
        sig=self.params['sig']
        bkg=self.params['bkg']
        if self.qparsig>1e-3:
            qpar=np.linspace(self.qpar-5*self.qparsig,self.qpar+5*self.qparsig,10)
            peak=np.exp(-(qpar-self.qpar)**2/2.0/self.qparsig**2)
            peaksum=np.sum(peak)
            distsum=np.zeros_like(self.x)
            for i in range(len(qpar)):
                q=np.sqrt(self.x**2+qpar[i]**2)
                sphere=Sphere.Sphere(x=q,R=R,Rsig=Rsig,dist=self.dist,N=self.N)
                distsum=distsum+sphere.y()*peak[i]
            res=norm*distsum*self.trans(self.x,qc)*np.exp(-self.x**2*sig**2)/peaksum+bkg
        else:
            q=np.sqrt(self.x**2+self.qpar**2)
            sphere=Sphere.Sphere(x=q,R=R,Rsig=Rsig,dist=self.dist,N=self.N)
            res=norm*sphere.y()*self.trans(self.x,qc)*np.exp(-self.x**2*sig**2)+bkg
        if self.Rsig>1e-3:
            self.output_params['Distribution']=sphere.output_params['Distribution']
        return res


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Rod_Sphere(x=x)
    print(fun.y())

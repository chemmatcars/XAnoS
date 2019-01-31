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



class FirstCumulant: #Please put the class name same as the function name
    def __init__(self,x=0,tfac=1e-6,lam=6370,n=1.33,theta=90,T=295,D=1.0,norm=1.0,bkg=0.0,mpar={}):
        """
        Calculates auto-correlation function for DLS measurements in water as a solvent

        x     	: Independent variable in the form of scalar or array of time intervals in microseconds
        tfac 	: factor to change from time units of from data to seconds
        lam  	: Wavelength of light in Angstroms
        n    	: Refractive index of solvent
        theta	: Angle of the detector in degrees with respect to the beam direction
        T     	: Temperature of the solvent in kelvin scale
        D	     	: Hydrodynamic diameter in Angstroms
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.tfac=tfac
        self.lam=lam
        self.n=n
        self.theta=theta
        self.T=T
        self.D=D
        self.norm=norm
        self.bkg=bkg
        self.__mpar__=mpar #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters

    def eta(self,T):
        """
        Returns the viscosity of water at a temperature T in kelvin.
        Check https://en.wikipedia.org/wiki/Temperature_dependence_of_liquid_viscosity#cite_note-5
        """
        return 2.414e-5*10**(247.8/(T-140.0))

    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('D',value=self.D,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params={}
        q=4*np.pi*self.n*np.sin(self.theta*np.pi/180.0/2.0)/self.lam/1e-10
        Dt=1.38065e-23*self.T/(3.0*np.pi*self.eta(self.T)*self.D*1e-10)
        gamma=q**2*Dt
        return self.norm*np.exp(-2*gamma*self.x*self.tfac)+self.bkg


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=FirstCumulant(x=x)
    print(fun.y())

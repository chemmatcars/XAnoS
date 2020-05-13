####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
import sys
import os
from scipy.special import erf
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_rountines'))
####Please do not remove lines above####

####Import your modules below if needed####



class Unified_Guinier: #Please put the class name same as the function name
    def __init__(self,x=0,G=1.0,Rg=1.0,B=1.0,P=1.0,mpar={'type':['1']}):
        """
        Documentation
        x           : Independent variable in the form of a scalar or an array
        G          : Guinier Constant
        Rg         : Radius of Gyration
        B           : Prefactor for power-law scattering
        P           : Exponent for the power-law
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.G=G
        self.Rg=Rg
        self.B=B
        self.P=P
        self.__mpar__=mpar #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.init_params()
        self.__fit__=False
        self.output_params={'scaler_parameters': {}}

    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value = 0, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        """
        self.params=Parameters()
        self.params.add('G',value = self.G, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('Rg',value = self.Rg, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('B',value = self.B, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('P',value = self.P,vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        for key in self.__mpar__.keys():
            if key!='type':
                for i in range(len(self.__mpar__[key])):
                        self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    def update_params(self):
        self.G = self.params['G'].value
        self.Rg = self.params['Rg'].value
        self.B = self.params['B'].value
        self.P = self.params['P'].value 

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params={}
        self.update_params()
        qs=self.x/erf(self.x*self.Rg/2.4495)**3
        I=self.G*np.exp(-self.x**2*self.Rg**2/3)+self.B*(1/qs)**self.P
        if not self.__fit__:
            self.output_params['scaler_parameters']={}
        return I


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Unified_Guinier(x=x)
    print(fun.y())

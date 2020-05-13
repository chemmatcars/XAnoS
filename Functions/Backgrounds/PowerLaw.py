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



class PowerLaw: #Please put the class name same as the function name
    def __init__(self,x=0,A=1,n=0,mpar={}):
        """
        The power law function is y=Ax^n

        x 	: Independent variable in the form of a scalar or an array
        A 	: Amplitude
        n 	: Exponent
        """

        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.A=A
        self.n=n
        self.__mpar__={} #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.output_params={'scaler_parameters':{}}


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('A',value=self.A,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('n',value=self.n,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        return self.A*self.x**self.n


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=PowerLaw(x=x)
    print(fun.y())

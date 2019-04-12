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
from FormFactors.Sphere import Sphere


class Sphere_Uniform: #Please put the class name same as the function name
    def __init__(self,x=0,Ru=1.0,Ru_sig=0.0,dist='Gaussian',rhou=1.0,density_u=1.0,bkg=0.0,mpar={'Layers':['Layer1'],'Re':[1.0],'rhoe':[1.0]}):
        """
        Documentation
        x           : Independent variable in the form of a scalar or an array
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.Ru=Ru
        self.Ru_sig=Ru_sig
        self.rhou=rhou
        self.density_u=density_u
        self.bkg=bkg
        self.dist=dist
        self.__mpar__=mpar #If there is any multivalued parameter
        self.choices={'dist':['Gaussian','LogNormal']} #If there are choices available for any fixed parameters
        self.init_params()
        self.__sphere__=Sphere(self.x)

    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value = 0, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = None)
        """
        self.params=Parameters()
        self.params.add('Ru',value=self.Ru,vary=0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('Ru_sig',value=self.Ru_sig,vary=0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('rhou',value=self.rhou,vary=0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('density_u',value=self.density_u,vary=0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('bkg',value=self.bkg,vary=0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        for key in self.__mpar__.keys():
            if key!='Layers':
                for i in range(len(self.__mpar__[key])):
                        self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.__sphere__.x=self.x
        self.__sphere__.dist=self.dist
        self.__sphere__.R=self.params['Ru'].value
        self.__sphere__.Rsig=self.params['Ru_sig'].value
        self.__sphere__.norm=self.params['density_u'].value*4.7829389852000006e-05
        self.output_params={}
        return self.__sphere__.y()


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Sphere_Uniform(x=x)
    print(fun.y())

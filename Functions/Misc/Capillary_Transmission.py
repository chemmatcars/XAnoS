####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
import sys
import os
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_routines'))
from functools import lru_cache
####Please do not remove lines above####

####Import your modules below if needed####



class Capillary_Transmission: #Please put the class name same as the function name
    def __init__(self,x=0,x_center=0.5,Di=1.0,thickness=0.01,l_wall=1.0,l_in=1.0,l_beam=0.1,norm=1.0,Npts=11,mpar={}):
        """
        Documentation
        Provides the transmission of X-ray through a capillary tube
        x           : Independent variable in the form of a scalar or an array
        x_center    : Center of the capillary tube
        norm        : Normalization factor
        Di          : Inner diameter of the capillary tubein mm
        thickness   : thickness of glass wall in mm
        l_wall      : absorption length of wall in mm
        l_in        : absorption length of material inside the capillary tube
        l_beam      : width of the X-ray beam in mm, considering the beam profile to rectanglar
        Npt         : No. of points to be used for beam profile convolution
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.x_center=x_center
        self.Di=Di
        self.thickness=thickness
        self.l_wall=l_wall
        self.norm=norm
        self.l_in=l_in
        self.l_beam=l_beam
        self.Npts=Npts
        self.__mpar__=mpar #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.__fit__=False
        self.__mkeys__=list(self.__mpar__.keys())
        self.output_params={'scaler_parameters':{}}
        self.init_params()

    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value = 0, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = None)
        """
        self.params=Parameters()
        self.params.add('Di',value=self.Di,vary=0,min=0.0,max=np.inf,expr=None,brute_step=self.Di/10)
        self.params.add('x_center',value=self.x_center,vary=0,min=-np.inf,max=np.inf,brute_step=max(self.x_center/10,0.1))
        self.params.add('thickness',value=self.thickness,vary=0,min=0.001,max=np.inf,expr=None,brute_step=self.thickness/10)
        self.params.add('l_wall',value=self.l_wall,vary=0,min=1e-6,max=np.inf,expr=None,brute_step=self.l_wall/10)
        self.params.add('l_in', value=self.l_in, vary=0, min=1e-6, max=np.inf, expr=None, brute_step=self.l_in/10)
        self.params.add('l_beam', value=self.l_beam, vary=0, min=1e-3, max=np.inf, expr=None, brute_step=self.l_beam/10)
        self.params.add('norm',value=self.norm, vary=0,min=0,max=np.inf,expr=None,brute_step=self.norm/10)
        for mkey in self.__mkeys__:
            for key in self.__mpar__[mkey].keys():
                if key!='type':
                    for i in range(len(self.__mpar__[mkey][key])):
                            self.params.add('__%s_%s_%03d'%(mkey,key,i),value=self.__mpar__[mkey][key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    def update_parameters(self):
        """
        update all the multifit parameters
        """
        pass
    @lru_cache(maxsize=10)
    def absorption(self,x,Di,thickness,x_center,l_in,l_wall):
        R1 = Di / 2
        R2 = R1 + thickness
        x = np.array(x) - x_center
        fac1 = np.where(abs(x) > R1, 1.0, np.exp(-2 * np.sqrt(R1 ** 2 - x ** 2) / l_in) *
                        np.exp(-2 * (np.sqrt(R2 ** 2 - x ** 2) - np.sqrt(R1 ** 2 - x ** 2)) / l_wall))
        fac2 = np.where((abs(x) > R1) & (abs(x) < R2), np.exp(-2 * np.sqrt(R2 ** 2 - x ** 2) / l_wall), 1.0)
        fac = self.norm * fac1 * fac2
        return fac

    def beam_convovle_abs(self,x,Di,thickness,x_center,l_in,l_wall,l_beam,N=11):
        gx=np.linspace(-l_beam/2,l_beam/2,N)
        if l_beam>1e-3:
            tmean=[]
            for tx in x:
                tmean.append(np.mean(self.absorption(tuple(tx-gx),Di,thickness,x_center,l_in,l_wall)))
            return np.array(tmean)
        else:
            return self.absorption(tuple(x),Di,thickness,x_center,l_in,l_wall)

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.update_parameters()
        fac=self.beam_convovle_abs(self.x,self.Di,self.thickness,self.x_center,self.l_in,self.l_wall,self.l_beam,N=self.Npts)
        if not self.__fit__:
            #Update all the output_params within the if loop for example
            #self.output_params['param1']={'x':x,'y':y,names=['x','y']}
            #self.output_params['scaler_parameters']['par1']=value
            pass

        return fac


if __name__=='__main__':
    x=np.linspace(0.0,1.0,101)
    fun=Capillary_Transmission(x=x)
    print(fun.y())

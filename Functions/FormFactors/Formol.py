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
import copy
from xraydb import XrayDB # Need to install xraydb from https://github.com/scikit-beam/XrayDB
from itertools import combinations

class Formol: #Please put the class name same as the function name
    def __init__(self,x=0,E=12.0,fname=None,sig=0.0,norm=1,bkg=0.0,__mpar__={}):
        """
        Calculates the form factor for a molecule for which the XYZ coordinates of the all the atoms composing the molecule is known
        x           :  scalar or array of reciprocal wave vectors
        E           : Energy of the X-rays at which the scattering pattern is measured
        fname   : Name of the .xyz file with path containing X, Y, Z coordinates of all the atoms of the molecules
        sig      : Debye-waller factor
        norm     : Normalization constant
        bkg        : Background
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.fname=fname
        self.norm=norm
        self.bkg=bkg
        self.E=E
        self.sig=sig
        self.__mpar__={} #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.output_params={}
        self.__fname__=copy.copy(self.fname)
        self.__xdb__=XrayDB()


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('sig',value=self.sig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        
    def readXYZ(self):
        """
        Reads the X,Y,Z coordinates from the file
        """
        self.__atoms__={}
        fh=open(self.fname,'r')
        lines=fh.readlines()
        self.__Natoms__=int(lines[0].strip())
        pos=[]
        f1=[]
        for i in range(self.__Natoms__):
            ele,x,y,z=lines[i+2].strip().split()
            pos.append([float(x),float(y),float(z)])
            f1.append(self.__xdb__.f1_chantler(ele,energy=self.E*1e3,smoothing=0))
        self.__pos__=np.array(pos)
        self.__f1__=np.array(f1)
            
        self.__fname__=copy.copy(self.fname)
        self.__E__=self.E

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        if self.fname is not None:
            if self.__fname__!=self.fname or self.__E__!=self.E:
                self.readXYZ()
            self.__form__=0.0
            for i,j in combinations(range(self.__Natoms__),2):
                d=np.sqrt(np.sum((self.__pos__[i]-self.__pos__[j])**2))
                self.__form__+=2*self.__f1__[i]*self.__f1__[j]*np.sin(self.x*d)/(self.x*d)
            self.__form__+=np.sum([self.__f1__[i]**2 for i in range(self.__Natoms__)])
            return self.__form__*self.norm*np.exp(-self.x**2*self.sig**2)+self.bkg
        else:
            return self.x


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Formol(x=x)
    print(fun.y())

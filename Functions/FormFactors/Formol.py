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
import os

class Formol: #Please put the class name same as the function name
    def __init__(self,x=0,E=12.0,fname1='/media/sf_Mrinal_Bera/Documents/MA-Collab/XTal_data/P8W48.xyz',eta1=1.0,fname2='/media/sf_Mrinal_Bera/Documents/MA-Collab/XTal_data/P2W12.xyz',eta2=0.0,qoff=0.0,sol=18.0,sig=0.0,norm=1,bkg=0.0,__mpar__={}):
        """
        Calculates the form factor for two different kinds of  molecules for which the XYZ coordinates of the all the atoms composing the molecules are known

        =======   =======================================================================
        x         scalar or array of reciprocal wave vectors
        E         Energy of the X-rays at which the scattering pattern is measured
        fname1    Name with path of the .xyz file containing X, Y, Z coordinates of all the atoms of the molecule of type 1
        eta 1     Fraction of molecule type 1
        fname2    Name with path of the .xyz file containing X, Y, Z coordinates of all the atoms of the moleucule of type 2
        eta 2     Fraction of molecule type 2
        qoff      Q-offset may be required due to uncertainity in Q-calibration
        sol       No of electrons in solvent molecule (Ex: H2O has 18 electrons)
        sig       Debye-waller factor
        norm      Normalization constant
        bkg       Background
        =======   ========================================================================
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=np.array([x])
        if os.path.exists(fname1):
            self.fname1=fname1
        else:
            self.fname1=None
        self.eta1=eta1
        if os.path.exists(fname2):
            self.fname2=fname2
        else:
            self.fname2=None
        self.eta2=eta2
        self.norm=norm
        self.bkg=bkg
        self.E=E
        self.sol=sol
        self.qoff=qoff
        self.sig=sig
        self.__mpar__={} #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.output_params={}
        self.__fnames__=[self.fname1,self.fname2]
        self.__E__=E
        self.__xdb__=XrayDB()
        if self.fname1 is not None:
            self.__Natoms1__,self.__pos1__,self.__f11__=self.readXYZ(self.fname1)
        if self.fname2 is not None:
            self.__Natoms2__,self.__pos2__,self.__f12__=self.readXYZ(self.fname2)
        self.__x__=self.x
        self.__qoff__=self.qoff


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('eta1',value=self.eta1,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('eta2',value=self.eta2,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('qoff',value=self.qoff,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('norm',value=self.norm,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('bkg',value=self.bkg,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('sig',value=self.sig,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)

    def readXYZ(self,fname):
        """
        Reads the X,Y,Z coordinates from the file
        """
        fh=open(fname,'r')
        lines=fh.readlines()
        fh.close()
        Natoms=int(lines[0].strip())
        pos=[]
        f1=[]
        for i in range(Natoms):
            ele,x,y,z=lines[i+2].strip().split()
            pos.append([float(x),float(y),float(z)])
            f1.append(self.__xdb__.f1_chantler(ele,energy=self.E*1e3,smoothing=0)*self.__xdb__.f0(ele,(self.x+self.qoff)/4.0/np.pi)/self.__xdb__.f0(ele,0)-self.sol)
        return Natoms, np.array(pos), np.array(f1)

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        form1=0.0
        form2=0.0

        #if self.__fnames__!=[None,None]:
        #Contribution from first molecule
        if self.fname1 is not None:
            if self.__fnames__[0]!=self.fname1 or self.__E__!=self.E or len(self.__x__)!=len(self.x) or self.__x__[-1]!=self.x[-1] or self.__qoff__!=self.qoff:
                self.__Natoms1__,self.__pos1__,self.__f11__=self.readXYZ(self.fname1)
            for i,j in combinations(range(self.__Natoms1__),2):
                d=np.sqrt(np.sum((self.__pos1__[i]-self.__pos1__[j])**2))
                form1+=2*self.__f11__[i,:]*self.__f11__[j,:]*np.sin((self.x+self.qoff)*d)/((self.x+self.qoff)*d)
            form1+=np.sum([self.__f11__[i,:]**2 for i in range(self.__Natoms1__)],axis=0)
        #Contribution from second molecule
        if self.fname2 is not None:
            if self.__fnames__[1]!=self.fname2 or self.__E__!=self.E or len(self.__x__)!=len(self.x) or self.__x__[-1]!=self.x[-1]:
                self.__Natoms2__,self.__pos2__,self.__f12__=self.readXYZ(self.fname2)
            for i,j in combinations(range(self.__Natoms2__),2):
                d=np.sqrt(np.sum((self.__pos2__[i]-self.__pos2__[j])**2))
                form2+=2*self.__f12__[i,:]*self.__f12__[j,:]*np.sin((self.x+self.qoff)*d)/((self.x+self.qoff)*d)
            form2+=np.sum([self.__f12__[i,:]**2 for i in range(self.__Natoms2__)],axis=0)

        self.__fnames__=[self.fname1,self.fname2]
        self.__E__=self.E
        self.__x__=self.x
        self.__qoff__=self.qoff
        if self.__fnames__!=[None,None]:
            self.output_params[self.fname1]={'x':self.x,'y':self.norm*self.eta1*form1}
            self.output_params[self.fname2]={'x':self.x,'y':self.norm*self.eta2*form2}
            self.output_params['bkg']={'x':self.x,'y':self.bkg*np.ones_like(self.x)}
            return (self.eta1*form1+self.eta2*form2)*self.norm*np.exp(-self.x**2*self.sig**2)+self.bkg
        else:
            return np.ones_like(self.x)


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Formol(x=x)
    fun.fname1='/media/sf_Mrinal_Bera/Documents/MA-Collab/XTal_data/P8W48.xyz'
    print(fun.y())

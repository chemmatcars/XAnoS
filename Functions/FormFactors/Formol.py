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
    re=2.818e-5 #Classical electron radius in Angstroms
    No=6.023e23 #Avagadro's number
    def __init__(self,x=0,E=12.0,fname1='W:/Tianbo_Collab/Mo132.xyz',eta1=1.0,fname2='/media/sf_Mrinal_Bera/Documents/MA-Collab/XTal_data/P2W12.xyz',eta2=0.0,rmin=0.0,rmax=10.0,Nr=100, qoff=0.0,sol=18.0,sig=0.0,norm=1,bkg=0.0,mpar={}):
        """
        Calculates the form factor for two different kinds of  molecules in cm^-1 for which the XYZ coordinates of the all the atoms composing the molecules are known

        x    	scalar or array of reciprocal wave vectors
        E    	Energy of the X-rays at which the scattering pattern is measured
        fname1	Name with path of the .xyz file containing X, Y, Z coordinates of all the atoms of the molecule of type 1
        eta1 	Fraction of molecule type 1
        fname2	Name with path of the .xyz file containing X, Y, Z coordinates of all the atoms of the moleucule of type 2
        eta2 	Fraction of molecule type 2
        rmin 	Minimum radial distance for calculating electron density
        rmax 	Maximum radial distance for calculating electron density
        Nr    	Number of points at which electron density will be calculated
        qoff 	Q-offset may be required due to uncertainity in Q-calibration
        sol	 	No of electrons in solvent molecule (Ex: H2O has 18 electrons)
        sig  	Debye-waller factor
        norm 	Normalization constant which can be the molar concentration of the particles
        bkg 	Background
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
        self.rmin=rmin
        self.__rmin__=rmin
        self.rmax=rmax
        self.__rmax__=rmax
        self.Nr=Nr
        self.__Nr__=Nr
        self.norm=norm
        self.bkg=bkg
        self.E=E
        self.sol=sol
        self.qoff=qoff
        self.sig=sig
        self.__mpar__=mpar #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.__fnames__=[self.fname1,self.fname2]
        self.__E__=E
        self.__xdb__=XrayDB()
        #if self.fname1 is not None:
        #    self.__Natoms1__,self.__pos1__,self.__f11__=self.readXYZ(self.fname1)
        #if self.fname2 is not None:
        #    self.__Natoms2__,self.__pos2__,self.__f12__=self.readXYZ(self.fname2)
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
        Reads the xyz file to read the atomic positions and put it in dictionary
        """
        fh=open(fname,'r')
        lines=fh.readlines()
        Natoms=eval(lines[0])
        atoms={'Natoms':Natoms}
        cen=np.zeros(3)
        atoms['elements']=[]
        for i in range(Natoms):
            line=lines[i+2].split()
            pos=np.array(list((map(eval,line[1:]))))
            if line[0] not in atoms['elements']:
                atoms['elements'].append(line[0])
            atoms[i]={'element':line[0],'pos':pos}
            cen=cen+pos
        cen=cen/Natoms
        for i in range(Natoms):
            atoms[i]['pos']=atoms[i]['pos']-cen
            atoms[i]['distance']=np.sqrt(np.sum(atoms[i]['pos']**2))
        return atoms

    def calc_xtal_rho(self, fname,rmin=0,rmax=10,Nr=81,energy=None):
        """
        Calculates radially averaged complex electron density in el/Angs^3 of a molecule from the co-ordinates obtained from X-ray crystallography.

        fname   :: .xyz file having all the X, Y, Z coordinates of atoms of the molecule in Angstroms
        rmin    :: Minimum radial distance in Angstroms (If rmin=0 then calculaiton will be done with rmin=1e-3 to avoid r=0 in the density calculation)
        rmax    :: Maximum radial distance in Angstroms
        Nr      :: (Use odd numbers only) No. of points between rmin and rmax at which the electron density has to be calculated
        energy  :: Energy in keV at which the electron density will be calculated
        """
        atoms=self.readXYZ(fname)
        if rmin<1e-6:
            rmin=1e-3
        r=np.linspace(rmin,rmax,Nr)
        dr=r[1]-r[0]
        rho=np.zeros(Nr)*(1.0+0.0j)
        for ele in atoms['elements']:
            distances=[atoms[i]['distance'] for i in range(atoms['Natoms']) if atoms[i]['element']==ele]
            Nrho,_=np.histogram(distances,bins=Nr,range=(rmin-dr/2,rmax+dr/2))
            if energy is None:
                rho=rho+Nrho*(self.__xdb__.f0(ele,0.0))#+xrdb.f1_chantler(element=ele,energy=energy*1e3,smoothing=0))
            else:
                f1=self.__xdb__.f1_chantler(element=ele,energy=energy*1e3,smoothing=0)
                f2=self.__xdb__.f2_chantler(element=ele,energy=energy*1e3,smoothing=0)
                rho=rho+Nrho*(self.__xdb__.f0(ele,0.0)+f1+1.0j*f2)
    #print(r[:-1]+(),rho)
        return r,rho/4/np.pi/r**2/dr+self.sol*np.where(rho<1e-6,1.0,0.0)

    def calc_form(self,q,r,rho):
        """
        Calculates the isotropic form factor in cm^-1 using the isotropic electron density as a funciton of radial distance

        q       :: scaler or array of reciprocal reciprocal wave vector in inv. Angstroms at which the form factor needs to be calculated in
        r       :: array of radial distances at which he electron density in known in Angstroms
        rho     :: array of electron densities as a funciton of radial distance in el/Angstroms^3. Note: The electron density should decay to zero at the last radial distance
        """
        dr=r[1]-r[0]
        form=np.zeros_like(q)
        for r1, rho1 in zip(r,rho):
            form=form+4*np.pi*r1*rho1*np.sin(q*r1)/q
        form=self.No*self.re**2*np.absolute(form)**2*dr**2*1e-16/1e3 # in cm^-1/moles
        return form

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params={}
        #if self.__fnames__!=[None,None]:
        #Contribution from first molecule
        if self.fname1 is not None:
            if self.__fnames__[0]!=self.fname1 or self.__E__!=self.E or len(self.__x__)!=len(self.x) or self.__x__[-1]!=self.x[-1] or self.__qoff__!=self.qoff or self.__Nr__!=self.Nr or self.__rmin__!=self.rmin or self.__rmax__!=self.rmax:
                self.__r1__,self.__rho1__=self.calc_xtal_rho(self.fname1,rmin=self.rmin,rmax=self.rmax,Nr=self.Nr,energy=self.E)
            form1=self.calc_form(self.x,self.__r1__,self.__rho1__)
            self.output_params['rho_1']={'x':self.__r1__,'y':np.real(self.__rho1__)}
        #Contribution from second molecule
        if self.fname2 is not None:
            if self.__fnames__[1]!=self.fname2 or self.__E__!=self.E or len(self.__x__)!=len(self.x) or self.__x__[-1]!=self.x[-1] or self.__qoff__!=self.qoff or self.__Nr__!=self.Nr or self.__rmin__!=self.rmin or self.__rmax__!=self.rmax:
                self._r2__,self.__rho2__=self.calc_xtal_rho(self.fname2,rmin=self.rmin,rmax=self.rmax,Nr=self.Nr,energy=self.E)
            form2=self.calc_form(self.x,self.__r2__,self.__rho2__)
            self.output_params['rho_2']={'x':self.__r2__,'y':np.real(self.__rho2__)}

        self.__fnames__=[self.fname1,self.fname2]
        self.__E__=self.E
        self.__x__=self.x
        self.__rmin__=self.rmin
        self.__rmax__=self.rmax
        self.__Nr__=self.Nr
        self.__qoff__=self.qoff
        if self.__fnames__[0] is not None and self.__fnames__[1] is not None:
            self.output_params[os.path.basename(self.fname1)+'_1']={'x':self.x,'y':self.norm*self.eta1*form1}
            self.output_params[os.path.basename(self.fname2)+'_1']={'x':self.x,'y':self.norm*self.eta2*form2}
            self.output_params['bkg']={'x':self.x,'y':self.bkg*np.ones_like(self.x)}
            return (self.eta1*form1+self.eta2*form2)*self.norm*np.exp(-self.x**2*self.sig**2)+self.bkg
        elif self.__fnames__[0] is not None and self.__fnames__[1] is None:
            self.output_params[os.path.basename(self.fname1)+'_1']={'x':self.x,'y':self.norm*self.eta1*form1}
            self.output_params['bkg']={'x':self.x,'y':self.bkg*np.ones_like(self.x)}
            return self.eta1*form1*self.norm*np.exp(-self.x**2*self.sig**2)+self.bkg
        elif self.__fnames__[0] is None and self.__fnames__[1] is not None:
            self.output_params[os.path.basename(self.fname2)+'_1']={'x':self.x,'y':self.norm*self.eta2*form2}
            self.output_params['bkg']={'x':self.x,'y':self.bkg*np.ones_like(self.x)}
            return self.eta2*form2*self.norm*np.exp(-self.x**2*self.sig**2)+self.bkg
        else:
            return np.ones_like(self.x)


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Formol(x=x)
    fun.fname1='/media/sf_Mrinal_Bera/Documents/MA-Collab/XTal_data/P8W48.xyz'
    print(fun.y())

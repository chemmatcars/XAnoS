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
from xraydb import XrayDB
#from pyEQL import chemical_formula


class SphericalShell_expDecay: #Please put the class name same as the function name
    No = 6.023e23  # Avagadro number
    re2= (2.817e-5)**2 # Square of classical electron radius in Angs^2
    def __init__(self, x=0, rmin=0.0, rmax=30.0, Nr=31, Rc=10.0, strho=1.0, tst=2.0, lrho=0.5, lexp=10.0, rhosol=0.0, norm=1.0, bkg=0.0, mpar={}):
        """
        Documentation
        x     	: independent variable in the form of a scalar or an array
        Rc    	: Radial distance in Angstroms after which the solvent contribution starts
        strho 	: Concentration of the ions of interest in the stern layer in Molar
        tst   	: Thickness of stern layer in Angstroms
        lrho  	: The maximum concentration of the diffuse layer in Molars
        lexp  	: The decay length of the diffuse layer assuming exponential decay
        rhosol	: The surrounding bulk density
        norm  	: Density of particles in Moles/Liter
        bkg  	: Constant background
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.rmin=rmin
        self.rmax=rmax
        self.Nr=Nr
        self.Rc=Rc
        self.strho=strho
        self.tst=tst
        self.lrho=lrho
        self.lexp=lexp
        self.rhosol=rhosol
        self.norm=norm
        self.bkg=bkg
        self.__mpar__=mpar #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.__xrdb__=XrayDB()
        self.init_params()

    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('Rc',value=self.Rc,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('strho', value=self.strho, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('tst', value=self.tst, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('lrho', value=self.lrho, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('lexp', value=self.lexp, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('norm', value=self.norm, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('bkg', value=self.bkg, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)



    def solrho(self, r, Rc=12.5, strho=1.0, tst=2.0, lrho=0.5, lexp=10.0, rhosol=0.0):
        """
        Calculates the electron density for the distribution of ions as a function of radial distance surrouning a spherical particle

        element  :: Symbol of ion of interest
        Rc     :: Radial distance in Angstroms after which the solvent contribution starts
        strho    :: Concentration of the ions of interest in the stern layer in Molar
        tst      :: Thickness of stern layer in Angstroms
        lrho     :: The maximum concentration of the diffuse layer in Molars
        lexp     :: The decay length of the diffuse layer assuming exponential decay
        rhosol   :: The surrounding bulk density
        """
        stern = np.where(r > Rc, strho, 0.0) * np.where(r > Rc + tst, 0.0, 1.0)
        diffuse = np.where(r > Rc + tst, lrho * np.exp(-(r - Rc - tst) / lexp) + rhosol, 0.0)
        rho = (stern + diffuse)
        return rho # in Moles/Liter


    def calc_form(self, q, r, rho):
        """
        Calculates the isotropic form factor using the isotropic electron density as a funciton of radial distance

        q       :: scaler or array of reciprocal reciprocal wave vector in inv. Angstroms at which the form factor needs to be calculated in
        r       :: array of radial distances at which the element/ion density in known in Angstroms
        rho     :: array of element/ion densities as a function of radial distance in el/Angstroms^3. Note: The electron density should decay to zero at the last radial distance
        """
        dr = r[1] - r[0]
        form = np.zeros_like(q)
        rho = (rho - rho[-1])* self.No/1e27 #converting it to moles/Angs^3
        for r1, rho1 in zip(r, rho):
            form = form + 4 * np.pi * r1 * rho1 * np.sin(q * r1) / q
        form = (np.absolute(form) * dr)**2
        return self.re2 * form * 1e-16 * self.No / 1e3 # in cm^-1

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params={}
        r=np.linspace(self.rmin, self.rmax, self.Nr)
        strho=self.params['strho'].value
        tst=self.params['tst'].value
        lrho=self.params['lrho'].value
        lexp=self.params['lexp'].value
        #rhosol=self.params['rhosol'].value
        norm=self.params['norm'].value
        bkg=self.params['bkg'].value
        Rc = self.params['Rc'].value
        rho=self.solrho(r, Rc=Rc, strho=strho, tst=tst, lrho=lrho, lexp=lexp, rhosol=self.rhosol)
        self.output_params['Electron_Density']={'x':r,'y':rho}
        form=norm*self.calc_form(self.x,r,rho)+bkg
        return form

if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=SphericalShell_expDecay(x=x)
    print(fun.y())

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
from Chemical_Formula import Chemical_Formula
from PeakFunctions import LogNormal, Gaussian
from utils import find_minmax
import time



class Sphere_Double_Layer: #Please put the class name same as the function name
    def __init__(self, x=0, Np=50, flux=1e13, dist='Gaussian', Energy=None, relement='Au', NrDep='True', norm=1.0e-4,
                 sbkg=0.0, cbkg=0.0, abkg=0.0, nearIon='Rb', farIon='Cl', ionDensity=0.0, stThickness=1.0,
                 stDensity=0.0, dbLength=1.0, dbDensity=0.0,Ndb=20,
                 mpar={'Material': ['Au', 'H2O'], 'Density': [19.32, 1.0], 'Sol_Density': [1.0, 1.0],'Rmoles': [1.0, 0.0], 'R': [1.0, 0.0], 'Rsig': [0.0, 0.0]}):
        """
        Documentation
        Calculates the Energy dependent form factor of multilayered nanoparticles with different materials

        x           : Reciprocal wave-vector 'Q' inv-Angs in the form of a scalar or an array
        relement    : Resonant element of the nanoparticle. Default: 'Au'
        Energy      : Energy of X-rays in keV at which the form-factor is calculated. Default: None
        Np          : No. of points with which the size distribution will be computed. Default: 10
        NrDep       : Energy dependence of the non-resonant element. Default= 'True' (Energy Dependent), 'False' (Energy independent)
        dist        : The probablity distribution fucntion for the radii of different interfaces in the nanoparticles. Default: Gaussian
        norm        : The density of the nanoparticles in Molar (Moles/Liter)
        sbkg        : Constant incoherent background for SAXS-term
        cbkg        : Constant incoherent background for cross-term
        abkg        : Constant incoherent background for Resonant-term
        nearIon     : The ionic layer closer to the particle
        farIon      : The ionic layer farther from the particle
        ionDensity  : The bulk density of the ions in Moles per liter
        stThickness : Thickness of the stern layer
        stDensity   : Density of the ions in the stern layer in Moles per liter
        dbLength    : The decay length of the debye layer in Angstroms
        dbDensity   : The maximum density of the debye layer in Moles per liter
        Ndb         : Number of layers used to represent the double layer region
        flux        : Total X-ray flux to calculate the errorbar to simulate the errorbar for the fitted data
        mpar        : Multi-parameter which defines the following including the solvent/bulk medium which is the last one. Default: 'H2O'
                        Material ('Materials' using chemical formula),
                        Density ('Density' in gm/cubic-cms),
                        Density of solvent ('Sol_Density' in gm/cubic-cms) of the particular layer
                        Mole-fraction ('Rmoles') of resonant element in the material)
                        Radii ('R' in Angs), and
                        Widths of the distributions ('Rsig' in Angs) of radii of all the interfaces present in the nanoparticle system. Default: [0.0]
        """
        if type(x) == list:
            self.x = np.array(x)
        else:
            self.x = x
        self.norm = norm
        self.sbkg = sbkg
        self.cbkg = cbkg
        self.abkg = abkg
        self.dist = dist
        self.nearIon=nearIon
        self.farIon=farIon
        self.ionDensity=ionDensity
        self.stThickness=stThickness
        self.stDensity=stDensity
        self.dbLength=dbLength
        self.dbDensity=dbDensity
        self.Ndb=Ndb
        self.Np = Np
        self.Energy = Energy
        self.relement = relement
        self.NrDep = NrDep
        # self.rhosol=rhosol
        self.flux = flux
        self.__mpar__ = mpar  # If there is any multivalued parameter
        self.choices = {'dist': ['Gaussian', 'LogNormal'],
                        'NrDep': ['True', 'False']}  # If there are choices available for any fixed parameters
        self.init_params()
        self.__cf__ = Chemical_Formula()
        self.__fit__ = False

    def init_params(self):
        """
        Define all the fitting parameters like
        self.params.add('sig',value = 0, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = None)
        """
        self.params = Parameters()
        self.params.add('norm', value=self.norm, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('stThickness', value=self.stThickness, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('stDensity',value=self.stDensity, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('dbLength', value=self.dbLength, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('dbDensity', value=self.dbDensity, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('sbkg', value=self.sbkg, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('cbkg', value=self.cbkg, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('abkg', value=self.abkg, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        for key in self.__mpar__.keys():
            if key != 'Material':
                for i in range(len(self.__mpar__[key])):
                    self.params.add('__%s__%03d' % (key, i), value=self.__mpar__[key][i], vary=0, min=-np.inf,
                                    max=np.inf, expr=None, brute_step=0.1)

    def calc_rho(self, R=[1.0, 0.0], material=['Au', 'H2O'], density=[19.3, 1.0], sol_density=[1.0, 1.0],
                 Rmoles=[1.0, 0.0], Energy=None, NrDep='True', stThickness=2.0, stDensity=0.0, dbLength=1.0, dbDensity=0.0, ionDensity=0.0, nearIon='Rb', farIon='Cl'):
        """
        Calculates the complex electron density of core-shell type multilayered particles in el/Angstroms^3

        R         :: list of Radii and subsequent shell thicknesses in Angstroms of the nanoparticle system
        material  :: list of material of all the shells starting from the core to outside
        density   :: list of density of all the materials in gm/cm^3 starting from the inner core to outside
        Rmoles    :: mole-fraction of the resonant element in the materials
        Energy    :: Energy in keV
        """
        #self.output_params['scaler_parameters'] = {}

        if len(material) == len(density):
            Nl = len(material)
            rho = []
            adensity = []  # Density of anomalous element
            eirho = []  # Energy independent electron density
            r = 0.0
            rhor = []
            eirhor = []
            adensityr = []
            for i in range(Nl):
                mat = material[i].split(':')
                if len(mat) == 2:
                    solute, solvent = mat

                    solute_formula = self.__cf__.parse(solute)
                    if self.relement in solute_formula.keys():
                        self.__cf__.formula_dict[self.relement] = Rmoles[i]
                    solute_elements = self.__cf__.elements()
                    solute_mw = self.__cf__.molecular_weight()
                    solute_mv = self.__cf__.molar_volume()
                    solute_mole_ratio = self.__cf__.element_mole_ratio()

                    solvent_formula = self.__cf__.parse(solvent)
                    solvent_elements = self.__cf__.elements()
                    solvent_mw = self.__cf__.molecular_weight()
                    solvent_mole_ratio = self.__cf__.element_mole_ratio()

                    solvent_moles = sol_density[i] / solvent_mw
                    solute_moles = density[i] / solute_mw
                    total_moles = solvent_moles + solute_moles
                    solvent_mole_fraction = solvent_moles / total_moles
                    solute_mole_fraction = solute_moles / total_moles
                    comb_material = ''
                    for ele in solute_mole_ratio.keys():
                        comb_material += '%s%.10f' % (ele, solute_mole_ratio[ele] * solute_mole_fraction)
                    for ele in solvent_mole_ratio.keys():
                        comb_material += '%s%.10f' % (ele, solvent_mole_ratio[ele] * solvent_mole_fraction)
                    tdensity = density[i] + sol_density[i] * (1 - solute_mv * density[i] / solute_mw)
                    # self.output_params['scaler_parameters']['density[%s]' % material[i]]=tdensity
                else:
                    formula = self.__cf__.parse(material[i])
                    if self.relement in formula.keys():
                        self.__cf__.formula_dict[self.relement] = Rmoles[i]
                    mole_ratio = self.__cf__.element_mole_ratio()
                    comb_material = ''
                    for ele in mole_ratio.keys():
                        comb_material += '%s%.10f' % (ele, mole_ratio[ele])
                    # comb_material=material[i]
                    tdensity = density[i]
                    # self.output_params['scaler_parameters']['density[%s]' % material[i]] = tdensity
                formula = self.__cf__.parse(comb_material)
                molwt = self.__cf__.molecular_weight()
                elements = self.__cf__.elements()
                mole_ratio = self.__cf__.element_mole_ratio()
                # numbers=np.array(chemical_formula.get_element_numbers(material[i]))
                moles = [mole_ratio[ele] for ele in elements]
                nelectrons = 0.0
                felectrons = complex(0.0, 0.0)
                aden = 0.0
                for j in range(len(elements)):
                    f0 = self.__cf__.xdb.f0(elements[j], 0.0)[0]
                    nelectrons = nelectrons + moles[j] * f0
                    if Energy is not None:
                        if elements[j] != self.relement:
                            if NrDep:
                                f1 = self.__cf__.xdb.f1_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                                f2 = self.__cf__.xdb.f2_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                                felectrons = felectrons + moles[j] * complex(f1, f2)
                        else:
                            f1 = self.__cf__.xdb.f1_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                            f2 = self.__cf__.xdb.f2_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                            felectrons = felectrons + moles[j] * complex(f1, f2)
                    if elements[j] == self.relement:
                        aden += 0.6023 * moles[j] * tdensity / molwt
                adensity.append(
                    aden)  # * np.where(r > Radii[i - 1], 1.0, 0.0) * pl.where(r <= Radii[i], 1.0, 0.0) / molwt
                eirho.append(0.6023 * (
                    nelectrons) * tdensity / molwt)  # * np.where(r > Radii[i - 1], 1.0,0.0) * pl.where(r <= Radii[i], 1.0,0.0) / molwt
                rho.append(0.6023 * (
                            nelectrons + felectrons) * tdensity / molwt)  # * np.where(r > Radii[i - 1], 1.0,0.0) * pl.where(r <= Radii[i], 1.0, 0.0) / molwt
                # else:
                #     eirho.append(0.6023 * (nelectrons) * density[i]/molwt)# * np.where(r <= Radii[i], 1.0, 0.0) / molwt
                #     rho.append(0.6023 * (nelectrons + felectrons) * density[i]/molwt)# * np.where(r <= Radii[i], 1.0,0.0) / molwt
                # self.output_params['scaler_parameters']['rho[%s]' % material[i]]=rho[-1]
                # self.output_params['scaler_parameters']['eirho[%s]' % material[i]] = eirho[-1]
                # self.output_params['scaler_parameters']['adensity[%s]' % material[i]] = adensity[-1]
                rhor.append([r, np.real(rho[-1])])
                eirhor.append([r, np.real(eirho[-1])])
                adensityr.append([r, np.real(adensity[-1])])
                r = r + R[i]
                rhor.append([r, np.real(rho[-1])])
                eirhor.append([r, np.real(eirho[-1])])
                adensityr.append([r, np.real(adensity[-1])])
            rhor, eirhor, adensityr = np.array(rhor), np.array(eirhor), np.array(adensityr)
            rhor[-1, 0] = rhor[-1, 0] + R[-2]
            eirhor[-1, 0] = eirhor[-1, 0] + R[-2]
            adensityr[-1, 0] = adensityr[-1, 0] + R[-2]
            return np.array(rho), np.array(eirho), np.array(adensity), rhor, eirhor, adensityr

    def solrho(self, Rp=100.0, Rc=12.5, strho=1.0, tst=2.0, lrho=0.5, lexp=10.0, rhosol=0.0, R=[1.0],
                                material=['H2O'],density=[1.0],sol_density=[1.0]):
        """
        Calculates the electron density for the bulk distribution of ions following double layer distribution surrounding a spherical particle

        Rp     :: Radius of the sphere in Angstroms enclosing the spherical particle
        Rc     :: Radial distance in Angstroms after which the solvent contribution starts
        strho    :: Concentration of the ions of interest in the stern layer in Molar
        tst      :: Thickness of stern layer in Angstroms
        lrho     :: The maximum concentration of the diffuse layer in Molars
        lexp     :: The decay length of the diffuse layer assuming exponential decay
        rhosol   :: The surrounding bulk density
        """
        R1=Rc
        R2=Rc+tst
        #integral=np.sum([r1**2*np.exp(-(r1-R2)/lexp) for r1 in np.linspace(R2,Rp,1001)])*(Rp-R2)/1000
        #integral=lexp*(R2**2*np.exp(-R2/lexp)-Rp**2*np.exp(-Rp/lexp))+2*lexp**2*(R2*np.exp(-R2/lexp)-Rp*np.exp(-Rp/lexp))+2*lexp**3*(np.exp(-Rp/lexp)-np.exp(-R2/lexp))
        r1=0
        tnear=0.0
        tfar=0.0
        nion = self.__cf__.parse(self.nearIon)
        mwnion = self.__cf__.molecular_weight()
        fion = self.__cf__.parse(self.farIon)
        mwfion = self.__cf__.molecular_weight()
        salt=self.nearIon+self.farIon
        salt_formula=self.__cf__.parse(salt)
        saltmw=self.__cf__.molecular_weight()
        salt_mole_ratio=self.__cf__.element_mole_ratio()
        for i, tR in enumerate(R):
            r2=r1+tR
            mat = material[i].split(':')
            if len(mat) == 2:
                solute, solvent = mat

                solute_formula = self.__cf__.parse(solute)
                if self.relement in solute_formula.keys():
                    self.__cf__.formula_dict[self.relement] = self.__Rmoles__[i]
                solute_elements = self.__cf__.elements()
                solute_mw = self.__cf__.molecular_weight()
                solute_mv = self.__cf__.molar_volume()
                solute_mole_ratio = self.__cf__.element_mole_ratio()

                solvent_formula = self.__cf__.parse(solvent)
                solvent_elements = self.__cf__.elements()
                solvent_mw = self.__cf__.molecular_weight()
                solvent_mole_ratio = self.__cf__.element_mole_ratio()

                solvent_moles = sol_density[i] / solvent_mw
                solute_moles = density[i] / solute_mw
                total_moles = solvent_moles + solute_moles
                solvent_mole_fraction = solvent_moles / total_moles
                solute_mole_fraction = solute_moles / total_moles
                comb_material = ''
                for ele in solute_mole_ratio.keys():
                    comb_material += '%s%.10f' % (ele, solute_mole_ratio[ele] * solute_mole_fraction)
                for ele in solvent_mole_ratio.keys():
                    comb_material += '%s%.10f' % (ele, solvent_mole_ratio[ele] * solvent_mole_fraction)
                tdensity = density[i] + sol_density[i] * (1 - solute_mv * density[i] / solute_mw)
                # self.output_params['scaler_parameters']['density[%s]' % material[i]]=tdensity
            else:
                formula = self.__cf__.parse(material[i])
                if self.relement in formula.keys():
                    self.__cf__.formula_dict[self.relement] = self.__Rmoles__[i]
                mole_ratio = self.__cf__.element_mole_ratio()
                comb_material = ''
                for ele in mole_ratio.keys():
                    comb_material += '%s%.10f' % (ele, mole_ratio[ele])
                # comb_material=material[i]
                tdensity = density[i]
                # self.output_params['scaler_parameters']['density[%s]' % material[i]] = tdensity
            formula = self.__cf__.parse(comb_material)
            molwt = self.__cf__.molecular_weight()
            elements = self.__cf__.elements()
            mole_ratio = self.__cf__.element_mole_ratio()
            if self.nearIon in material[i]:
                if len(nion) > 1:
                    nmratio = 1.0
                else:
                    nmratio = mole_ratio[self.nearIon]
                tnear=tnear+(r2**3-r1**3)*tdensity*1e3*nmratio/mwnion
            elif self.farIon in material[i]:
                if len(fion) > 1:
                    fmratio = 1.0
                else:
                    fmratio = mole_ratio[self.farIon]
                tfar=tfar+(r2**3-r1**3)*tdensity*1e3*fmratio/mwfion
            r1=r2+0.0
        integral=(R2**2*lexp+2*R2*lexp**2+2*lexp**3)*np.exp(-R2/lexp)-(Rp**2*lexp+2*Rp*lexp**2+2*lexp**3)*np.exp(-Rp/lexp)
        if 3*lrho*integral>=rhosol*(Rp**3-R1**3)-strho*(R2**3-R1**3)-tnear:
            near=0.00
            lrho=(rhosol*(Rp**3-R1**3)-strho*(R2**3-R1**3)-tnear)/3/integral
        else:
            near=(rhosol*(Rp**3-R1**3)-strho*(R2**3-R1**3)-3*lrho*integral-tnear)/(Rp**3-R2**3)
        far=(rhosol*(Rp ** 3 - R1 ** 3)+3*lrho*integral-tfar)/(Rp**3 - R2**3)
        self.output_params['scaler_parameters']['tnear']=tnear
        self.output_params['scaler_parameters']['tfar']=tfar
        self.output_params['scaler_parameters']['rho_near']=near
        self.output_params['scaler_parameters']['rho_far']=far
        return near, far # in Moles/Liter

    def calc_form(self, q, r, rho):
        """
        Calculates the isotropic form factor in cm^-1 using the isotropic electron density as a function of radial distance

        q       :: scaler or array of reciprocal reciprocal wave vector in inv. Angstroms at which the form factor needs to be calculated in
        r       :: array of radial distances at which he electron density in known in Angstroms
        rho     :: array of electron densities as a funciton of radial distance in el/Angstroms^3. Note: The electron density should decay to zero at the last radial distance
        """
        dr = r[1] - r[0]
        amp = np.zeros_like(q)
        rho = rho - rho[-1]
        for r1, rho1 in zip(r, rho):
            amp = amp + 4 * np.pi * r1 * rho1 * np.sin(q * r1) / q
        form = 2.818e-5 ** 2 * np.absolute(amp) ** 2 * dr ** 2 * 1e-16
        return form, 2.818e-5 * amp * dr * 1e-8

    def calc_mesh(self, R=[1.0], Rsig=[0.0], Np=100):
        """
        Computes a multi-dimensional meshgrid of radii (R) of interfaces with a finite widths (Rsig>0.001) of distribution
        :param R:
        :param Rsig:
        :return:
        """
        r1 = 'np.meshgrid('
        for (i, r) in enumerate(R):
            if Rsig[i] > 0.001:
                lgn = eval(self.dist + '.' + self.dist + '(x=0.001, pos=r, wid=Rsig[i])')
                rmin, rmax = find_minmax(lgn, r, Rsig[i])
                r1 = r1 + 'np.linspace(%.10f,%.10f,%d),' % (rmin, rmax, Np)
            else:
                r1 = r1 + '[%.10f],' % r
        r1 = r1[:-1] + ',sparse=True)'
        return (eval(r1))

    def sphere(self, q, R, dist, rho, eirho, adensity):
        fform = 0.0
        feiform = 0.0
        faform = 0.0
        fcross = 0.0
        sdist = 0.0
        if R.ndim>1:
            for j in range(R.shape[1]):
                tdist = 1.0
                eiform = 0.0
                aform = 0.0
                form = 0.0
                r1=0.0
                for i in range(R.shape[0]):
                    drho = rho[i] - rho[i + 1]
                    deirho = eirho[i] - eirho[i + 1]
                    darho = adensity[i] - adensity[i + 1]
                    r1 += R[i,j]
                    fact = 4 * np.pi * 2.818e-5 * 1.0e-8 * (np.sin(q * r1) - q * r1 * np.cos(q * r1)) / q ** 3
                    eiform = eiform + deirho * fact
                    aform = aform + darho * fact
                    form = form + drho * fact
                    tdist = tdist * dist[i, j]
                feiform = feiform + abs(eiform) ** 2 * tdist
                faform = faform + abs(aform) ** 2 * tdist
                fform = fform + abs(form) ** 2 * tdist
                fcross = fcross + abs(eiform * aform) * tdist
                sdist = sdist + tdist
            feiform = feiform / sdist
            faform = faform / sdist
            fform = fform / sdist
            fcross = fcross / sdist
        else:
            tdist = 1.0
            eiform = 0.0
            aform = 0.0
            form = 0.0
            r1=0.0
            for i in range(R.shape[0]):
                drho = rho[i] - rho[i + 1]
                deirho = eirho[i] - eirho[i + 1]
                darho = adensity[i] - adensity[i + 1]
                r1 += R[i]
                fact = 4 * np.pi * 2.818e-5 * 1.0e-8 * (np.sin(q * r1) - q * r1 * np.cos(q * r1)) / q ** 3
                eiform = eiform + deirho * fact
                aform = aform + darho * fact
                form = form + drho * fact
                tdist = tdist * dist[i]
            feiform = feiform + abs(eiform) ** 2 * tdist
            faform = faform + abs(aform) ** 2 * tdist
            fform = fform + abs(form) ** 2 * tdist
            fcross = fcross + abs(eiform * aform) * tdist
            sdist = sdist + tdist
        feiform = feiform / sdist
        faform = faform / sdist
        fform = fform / sdist
        fcross = fcross / sdist

        return fform, feiform, faform, fcross  # in cm^2

    def sphere_dict(self, q, R, dist, rho, eirho, adensity, key='SAXS-term'):
        fform = 0.0
        feiform = 0.0
        faform = 0.0
        fcross = 0.0
        sdist=0.0
        if R.ndim > 1:
            for j in range(R.shape[1]):
                tdist=1.0
                eiform=0.0
                aform=0.0
                form=0.0
                r1=0.0
                for i in range(R.shape[0]):
                    drho = rho[i] - rho[i + 1]
                    deirho = eirho[i] - eirho[i + 1]
                    darho = adensity[i] - adensity[i + 1]
                    r1 += R[i]
                    fact = 4 * np.pi * 2.818e-5 * 1.0e-8 * (np.sin(q * r1) - q * r1 * np.cos(q * r1)) / q ** 3
                    eiform = eiform + deirho * fact
                    aform = aform + darho * fact
                    form = form + drho * fact
                    tdist=tdist*dist[i,j]
                feiform=feiform+abs(eiform)**2*tdist
                faform=faform+abs(aform)**2*tdist
                fform=fform+abs(form)**2*tdist
                fcross=fcross+abs(eiform*aform)*tdist
                sdist=sdist+tdist
        else:
            tdist = 1.0
            eiform = 0.0
            aform = 0.0
            form = 0.0
            r1=0.0
            for i in range(R.shape[0]):
                drho = rho[i] - rho[i + 1]
                deirho = eirho[i] - eirho[i + 1]
                darho = adensity[i] - adensity[i + 1]
                r1 += R[i]
                fact = 4 * np.pi * 2.818e-5 * 1.0e-8 * (np.sin(q * r1) - q * r1 * np.cos(q * r1)) / q ** 3
                eiform = eiform + deirho * fact
                aform = aform + darho * fact
                form = form + drho * fact
                tdist = tdist * dist[i]
            feiform = feiform + abs(eiform) ** 2 * tdist
            faform = faform + abs(aform) ** 2 * tdist
            fform = fform + abs(form) ** 2 * tdist
            fcross = fcross + abs(eiform * aform) * tdist
            sdist = sdist + tdist
        feiform = feiform / sdist
        faform = faform / sdist
        fform = fform / sdist
        fcross = fcross / sdist

        if key == 'SAXS-term':
            return feiform  # in cm^2
        elif key == 'Resonant-term':
            return faform  # in cm^2
        elif key == 'Cross-term':
            return fcross  # in cm^2
        elif key == 'Total':
            return fform  # in cm^2

    def update_params(self):
        self.norm = self.params['norm'].value
        self.sbkg = self.params['sbkg'].value
        self.cbkg = self.params['cbkg'].value
        self.abkg = self.params['abkg'].value
        self.stThickness=self.params['stThickness'].value
        self.stDensity=self.params['stDensity'].value
        self.dbLength=self.params['dbLength'].value
        self.dbDensity=self.params['dbDensity'].value
        key = 'Density'
        self.__density__ = [self.params['__%s__%03d' % (key, i)].value for i in range(len(self.__mpar__[key]))]
        key = 'Sol_Density'
        self.__sol_density__ = [self.params['__%s__%03d' % (key, i)].value for i in range(len(self.__mpar__[key]))]
        key = 'Rmoles'
        self.__Rmoles__ = [self.params['__%s__%03d' % (key, i)].value for i in range(len(self.__mpar__[key]))]
        key = 'R'
        self.__R__ = [self.params['__%s__%03d' % (key, i)].value for i in range(len(self.__mpar__[key]))]
        key = 'Rsig'
        self.__Rsig__ = [self.params['__%s__%03d' % (key, i)].value for i in range(len(self.__mpar__[key]))]
        key = 'Material'
        self.__material__ = [self.__mpar__[key][i] for i in range(len(self.__mpar__[key]))]

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params = {}
        self.output_params['scaler_parameters']={}
        self.update_params()
        tR=self.__R__[:-1]
        tRsig=self.__Rsig__[:-1]
        tnmaterial=self.__material__[:-1]
        tfmaterial = self.__material__[:-1]
        tndensity=self.__density__[:-1]
        tfdensity = self.__density__[:-1]
        tsoldensity=self.__sol_density__[:-1]
        tRmoles=self.__Rmoles__[:-1]
        Rp = (3 / (4 * np.pi * self.norm * 6.022e23)) ** (1.0 / 3.0) * 1e9
        Rc=np.sum(tR)
        near, far = self.solrho(Rp=Rp, Rc=Rc, strho=self.stDensity, tst=self.stThickness, lrho=self.dbDensity,
                                lexp=self.dbLength, rhosol=self.ionDensity, R=tR,
                                material=tnmaterial,density=tndensity,sol_density=tsoldensity)
        dbr=[self.stThickness]
        dbr=dbr+[(Rp-Rc-self.stThickness)/self.Ndb for i in range(self.Ndb)]
        nden=[self.stDensity]
        fden=[0.0]
        nden=np.append(nden,self.dbDensity*np.exp(-np.cumsum(dbr[1:])/self.dbLength)+near)
        fden=np.append(fden,far*(1-np.exp(-np.cumsum(dbr[1:])/self.dbLength)))
        self.output_params['scaler_parameters']['Rp']=Rp
        nmf=self.__cf__.parse(self.nearIon)
        nmw=self.__cf__.molecular_weight()
        fmf=self.__cf__.parse(self.farIon)
        fmw=self.__cf__.molecular_weight()
        for i in range(len(dbr)):
            tR.append(dbr[i])
            tRsig.append(self.__Rsig__[-1])
            tsoldensity.append(self.__sol_density__[-1])

            tndensity.append(2*nden[i]*nmw/1000) # converting int gms/cubic-cms
            tfdensity.append(2*fden[i]*fmw/1000) # converting int gms/cubic-cms
            tnmaterial.append('%s:%s'%(self.nearIon,self.__material__[-1]))
            tfmaterial.append('%s:%s' % (self.farIon, self.__material__[-1]))
            if self.relement in self.nearIon:
                tRmoles.append(1.0)
            elif self.relement in self.farIon:
                tRmoles.append(1.0)
            else:
                tRmoles.append(1.0)

        rhon, eirhon, adensityn, rhorn, eirhorn, adensityrn = self.calc_rho(R=tR, material=tnmaterial, density=tndensity, sol_density=tsoldensity, Energy=self.Energy, Rmoles=tRmoles, NrDep=self.NrDep)
        rhof, eirhof, adensityf, rhorf, eirhorf, adensityrf = self.calc_rho(R=tR, material=tfmaterial, density=tfdensity, sol_density=tsoldensity, Energy=self.Energy, Rmoles=tRmoles, NrDep=self.NrDep)

        rho, eirho, adensity = (rhon+rhof)/2, (eirhon+eirhof)/2, (adensityn+adensityf)/2
        rhor,eirhor, adensityr = rhorn, eirhorn, adensityrn
        rhor[:,1]=(rhor[:,1]+rhorf[:,1])/2
        eirhor[:, 1] = (eirhor[:, 1] + eirhorf[:, 1])/2
        adensityr[:,1]=(adensityr[:,1]+adensityrf[:,1])/2

        r=[]
        adist = []

        if np.any(np.array(tRsig)>0.001):
            for i in range(len(tR) - 1):
                if tRsig[i] > 0.001:
                    if self.dist == 'LogNormal':
                        r.append(np.abs(np.sort(np.random.lognormal(np.log(tR[i]),tRsig[i],self.Np))))
                        td=np.exp(-(np.log(r[i]) - np.log(tR[i])) ** 2 / 2 / tR[i] ** 2) / r[i] / 2.5066 / self.tRsig[i]
                        adist.append(td)
                    else:
                        r.append(np.abs(np.sort(np.random.normal(tR[i], tRsig[i], self.Np))))
                        td=np.exp(-(r[i] - tR[i]) ** 2 / 2 / tRsig[i] ** 2) / 2.5066 / tRsig[i]
                        adist.append(td)
                    self.output_params['dist_layer_%d' % i] = {'x': r[i], 'y': td}
                else:
                    r.append(np.ones(self.Np)*tR[i])
                    adist.append(np.ones(self.Np))
        else:
            r=np.array(tR[:-1]).T
            adist=np.ones_like(r).T

        r=np.array(r)
        adist=np.array(adist)

        if type(self.x) == dict:
            sqf = {}
            for key in self.x.keys():
                sq = []
                for q1 in self.x[key]:
                    sq.append(self.sphere_dict(q1, r, adist, rho, eirho, adensity, key=key))
                sqf[key] = self.norm * np.array(sq) * 6.022e20  # in cm^-1
                if key == 'SAXS-term':
                    sqf[key] = sqf[key] + self.sbkg
                if key == 'Cross-term':
                    sqf[key] = sqf[key] + self.cbkg
                if key == 'Resonant-term':
                    sqf[key] = sqf[key] + self.abkg
            key1 = 'Total'
            sqt = []
            for q1 in self.x[key]:
                sqt.append(self.sphere_dict(q1, r, adist, rho, eirho, adensity, key=key1))
            total = self.norm * np.array(sqt) * 6.022e20 + self.sbkg  # in cm^-1
            if not self.__fit__:
                self.output_params['Simulated_total_wo_err'] = {'x': self.x[key], 'y': total}
                self.output_params['rho_r'] = {'x': rhor[:, 0], 'y': rhor[:, 1]}
                self.output_params['eirho_r'] = {'x': eirhor[:, 0], 'y': eirhor[:, 1]}
                self.output_params['adensity_r'] = {'x': adensityr[:, 0], 'y': adensityr[:, 1]}
                self.output_params['rhon_r'] = {'x': rhorn[:, 0], 'y': rhorn[:, 1]}
                self.output_params['eirhon_r'] = {'x': eirhorn[:, 0], 'y': eirhorn[:, 1]}
                self.output_params['adensityn_r'] = {'x': adensityrn[:, 0], 'y': adensityrn[:, 1]}
                self.output_params['rhof_r'] = {'x': rhorf[:, 0], 'y': rhorf[:, 1]}
                self.output_params['eirhof_r'] = {'x': eirhorf[:, 0], 'y': eirhorf[:, 1]}
                self.output_params['adensityf_r'] = {'x': adensityrf[:, 0], 'y': adensityrf[:, 1]}
        else:
            sqf = []
            asqf = []
            eisqf = []
            csqf = []
            for q1 in self.x:
                tsq, eisq, asq, csq = self.sphere(q1, r, adist, rho, eirho, adensity)
                sqf.append(tsq)
                asqf.append(asq)
                eisqf.append(eisq)
                csqf.append(csq)
            sqf = self.norm * np.array(sqf) * 6.022e20 + self.sbkg  # in cm^-1
            if not self.__fit__:  # Generate all the quantities below while not fitting
                asqf = self.norm * np.array(asqf) * 6.022e20 + self.abkg  # in cm^-1
                eisqf = self.norm * np.array(eisqf) * 6.022e20 + self.sbkg  # in cm^-1
                csqf = self.norm * np.array(csqf) * 6.022e20 + self.cbkg  # in cm^-1
                svol = 0.2 ** 2 * 1.5 * 1e-3  # scattering volume in cm^3
                sqerr = np.sqrt(self.flux * sqf * svol)
                sqwerr = (sqf * svol * self.flux + 2 * (0.5 - np.random.rand(len(sqf))) * sqerr)
                self.output_params['simulated_total_w_err'] = {'x': self.x, 'y': sqwerr, 'yerr': sqerr}
                self.output_params['simulated_total_wo_err'] = {'x': self.x, 'y': sqf * svol * self.flux}
                self.output_params['simulated_anomalous'] = {'x': self.x, 'y': asqf}
                self.output_params['simulated_saxs'] = {'x': self.x, 'y': eisqf}
                self.output_params['simulated_cross'] = {'x': self.x, 'y': csqf}
                self.output_params['rho_r'] = {'x': rhor[:, 0], 'y': rhor[:, 1]}
                self.output_params['eirho_r'] = {'x': eirhor[:, 0], 'y': eirhor[:, 1]}
                self.output_params['adensity_r'] = {'x': adensityr[:, 0], 'y': adensityr[:, 1]}
                self.output_params['rhon_r'] = {'x': rhorn[:, 0], 'y': rhorn[:, 1]}
                self.output_params['eirhon_r'] = {'x': eirhorn[:, 0], 'y': eirhorn[:, 1]}
                self.output_params['adensityn_r'] = {'x': adensityrn[:, 0], 'y': adensityrn[:, 1]}
                self.output_params['rhof_r'] = {'x': rhorf[:, 0], 'y': rhorf[:, 1]}
                self.output_params['eirhof_r'] = {'x': eirhorf[:, 0], 'y': eirhorf[:, 1]}
                self.output_params['adensityf_r'] = {'x': adensityrf[:, 0], 'y': adensityrf[:, 1]}
        return sqf


if __name__ == '__main__':
    x = np.arange(0.001, 1.0, 0.1)
    fun = Sphere_Double_Layer(x=x)
    print(fun.y())

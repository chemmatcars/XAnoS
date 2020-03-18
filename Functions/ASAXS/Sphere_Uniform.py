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
from Structure_Factors import hard_sphere_sf, sticky_sphere_sf
from utils import find_minmax


class Sphere_Uniform: #Please put the class name same as the function name
    def __init__(self, x=0, Np=10, flux=1e13, dist='Gaussian', Energy=None, relement='Au', NrDep='True', norm=1.0, sbkg=0.0, cbkg=0.0, abkg=0.0, D=1.0, phi=0.1, U=-1.0, SF='None', mpar={'Material':['Au','H2O'],'Density':[19.32,1.0],'Sol_Density':[1.0,1.0],'Rmoles':[1.0,0.0],'R':[1.0,0.0],'Rsig':[0.0,0.0]}):
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
        flux        : Total X-ray flux to calculate the errorbar to simulate the errorbar for the fitted data
        D           : Hard Sphere Diameter
        phi         : Volume fraction of particles
        U           : The sticky-sphere interaction energy
        SF          : Type of structure factor. Default: 'None'
        mpar        : Multi-parameter which defines the following including the solvent/bulk medium which is the last one. Default: 'H2O'
                        Material ('Materials' using chemical formula),
                        Density ('Density' in gm/cubic-cms),
                        Density of solvent ('Sol_Density' in gm/cubic-cms) of the particular layer
                        Mole-fraction ('Rmoles') of resonant element in the material)
                        Radii ('R' in Angs), and
                        Widths of the distributions ('Rsig' in Angs) of radii of all the interfaces present in the nanoparticle system. Default: [0.0]
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.norm=norm
        self.sbkg=sbkg
        self.cbkg=cbkg
        self.abkg=abkg
        self.dist=dist
        self.Np=Np
        self.Energy=Energy
        self.relement=relement
        self.NrDep=NrDep
        #self.rhosol=rhosol
        self.flux=flux
        self.D=D
        self.phi=phi
        self.U=U
        self.__mpar__=mpar #If there is any multivalued parameter
        self.SF=SF
        self.choices={'dist':['Gaussian','LogNormal'],'NrDep':['True','False'],'SF':['None','Hard-Sphere', 'Sticky-Sphere']} #If there are choices available for any fixed parameters
        self.init_params()
        self.__cf__=Chemical_Formula()
        self.__fit__=False

    def init_params(self):
        """
        Define all the fitting parameters like
        self.params.add('sig',value = 0, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = None)
        """
        self.params=Parameters()
        self.params.add('norm',value=self.norm,vary=0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('D', value=self.D, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('phi', value=self.phi, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('sbkg',value=self.sbkg,vary=0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('cbkg', value=self.cbkg, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('abkg', value=self.abkg, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('U', value=self.U, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        for key in self.__mpar__.keys():
            if key!='Material':
                for i in range(len(self.__mpar__[key])):
                    self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    def calc_rho(self,R=[1.0,0.0],material=['Au','H2O'], density=[19.3,1.0], sol_density=[1.0,1.0], Rmoles=[1.0,0.0], Energy=None, NrDep='True'):
        """
        Calculates the complex electron density of core-shell type multilayered particles in el/Angstroms^3

        R         :: list of Radii and subsequent shell thicknesses in Angstroms of the nanoparticle system
        material  :: list of material of all the shells starting from the core to outside
        density   :: list of density of all the materials in gm/cm^3 starting from the inner core to outside
        Rmoles    :: mole-fraction of the resonant element in the materials
        Energy    :: Energy in keV
        """
        self.output_params['scaler_parameters']={}
        if len(material) == len(density):
            Nl = len(material)
            rho = []
            adensity = []  # Density of anomalous element
            eirho = []  # Energy independent electron density
            r=0.0
            rhor=[]
            eirhor=[]
            adensityr=[]
            for i in range(Nl):
                mat=material[i].split(':')
                if len(mat)==2:
                    solute,solvent=mat

                    solute_formula=self.__cf__.parse(solute)
                    if self.relement in solute_formula.keys():
                        self.__cf__.formula_dict[self.relement] = Rmoles[i]
                    solute_elements=self.__cf__.elements()
                    solute_mw=self.__cf__.molecular_weight()
                    solute_mv=self.__cf__.molar_volume()
                    solute_mole_ratio=self.__cf__.element_mole_ratio()

                    solvent_formula=self.__cf__.parse(solvent)
                    solvent_elements=self.__cf__.elements()
                    solvent_mw=self.__cf__.molecular_weight()
                    solvent_mole_ratio=self.__cf__.element_mole_ratio()

                    solvent_moles=sol_density[i]*(1-solute_mv*density[i]/solute_mw) / solvent_mw
                    solute_moles=density[i]/solute_mw
                    total_moles=solvent_moles+solute_moles
                    solvent_mole_fraction=solvent_moles/total_moles
                    solute_mole_fraction=solute_moles/total_moles
                    comb_material=''
                    for ele in solute_mole_ratio.keys():
                        comb_material+='%s%.10f'%(ele,solute_mole_ratio[ele]*solute_mole_fraction)
                    for ele in solvent_mole_ratio.keys():
                        comb_material+='%s%.10f'%(ele,solvent_mole_ratio[ele]*solvent_mole_fraction)
                    tdensity=density[i]+sol_density[i]*(1-solute_mv*density[i]/solute_mw)
                    #self.output_params['scaler_parameters']['density[%s]' % material[i]]=tdensity
                else:
                    formula = self.__cf__.parse(material[i])
                    fac = 1.0
                    if self.relement in formula.keys():
                        self.__cf__.formula_dict[self.relement] = 0.0
                        t1 = self.__cf__.molar_mass()
                        self.__cf__.formula_dict[self.relement] = Rmoles[i]
                        t2 = self.__cf__.molar_mass()
                        if t1 > 0:
                            fac = t2 / t1
                            self.output_params['scaler_parameters']['density[%s]' % material[i]] = fac * density[i]
                    mole_ratio = self.__cf__.element_mole_ratio()
                    comb_material = ''
                    for ele in mole_ratio.keys():
                        comb_material += '%s%.10f' % (ele, mole_ratio[ele])
                    # comb_material=material[i]
                    tdensity = fac * density[i]
                    # self.output_params['scaler_parameters']['density[%s]' % material[i]] = tdensity
                formula = self.__cf__.parse(comb_material)
                molwt = self.__cf__.molecular_weight()
                elements = self.__cf__.elements()
                mole_ratio = self.__cf__.element_mole_ratio()
                # numbers=np.array(chemical_formula.get_element_numbers(material[i]))
                moles = [mole_ratio[ele] for ele in elements]
                nelectrons = 0.0
                felectrons = complex(0.0, 0.0)
                aden=0.0
                for j in range(len(elements)):
                    f0 = self.__cf__.xdb.f0(elements[j], 0.0)[0]
                    nelectrons = nelectrons + moles[j] * f0
                    if Energy is not None:
                        if elements[j]!=self.relement:
                            if NrDep:
                                f1 = self.__cf__.xdb.f1_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                                f2 = self.__cf__.xdb.f2_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                                felectrons = felectrons + moles[j] * complex(f1, f2)
                        else:
                            f1 = self.__cf__.xdb.f1_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                            f2 = self.__cf__.xdb.f2_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                            felectrons = felectrons + moles[j] * complex(f1, f2)
                    if elements[j]==self.relement:
                        aden+=0.6023 * moles[j]*tdensity/molwt
                adensity.append(aden)# * np.where(r > Radii[i - 1], 1.0, 0.0) * pl.where(r <= Radii[i], 1.0, 0.0) / molwt
                eirho.append(0.6023 * (nelectrons) * tdensity/molwt)# * np.where(r > Radii[i - 1], 1.0,0.0) * pl.where(r <= Radii[i], 1.0,0.0) / molwt
                rho.append(0.6023 * (nelectrons + felectrons) * tdensity/molwt)# * np.where(r > Radii[i - 1], 1.0,0.0) * pl.where(r <= Radii[i], 1.0, 0.0) / molwt
                # else:
                #     eirho.append(0.6023 * (nelectrons) * density[i]/molwt)# * np.where(r <= Radii[i], 1.0, 0.0) / molwt
                #     rho.append(0.6023 * (nelectrons + felectrons) * density[i]/molwt)# * np.where(r <= Radii[i], 1.0,0.0) / molwt
                #self.output_params['scaler_parameters']['rho[%s]' % material[i]]=rho[-1]
                #self.output_params['scaler_parameters']['eirho[%s]' % material[i]] = eirho[-1]
                #self.output_params['scaler_parameters']['adensity[%s]' % material[i]] = adensity[-1]
                rhor.append([r,np.real(rho[-1])])
                eirhor.append([r,np.real(eirho[-1])])
                adensityr.append([r,np.real(adensity[-1])])
                r=r+R[i]
                rhor.append([r, np.real(rho[-1])])
                eirhor.append([r, np.real(eirho[-1])])
                adensityr.append([r, np.real(adensity[-1])])
            rhor,eirhor,adensityr=np.array(rhor),np.array(eirhor),np.array(adensityr)
            rhor[-1,0]=rhor[-1,0]+R[-2]
            eirhor[-1, 0] = eirhor[-1, 0] + R[-2]
            adensityr[-1, 0] = adensityr[-1, 0] + R[-2]
            return rho, eirho, adensity, rhor, eirhor, adensityr

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

    def calc_mesh(self,R=[1.0],Rsig=[0.0],Np=100):
        """
        Computes a multi-dimensional meshgrid of radii (R) of interfaces with a finite widths (Rsig>0.001) of distribution
        :param R:
        :param Rsig:
        :return:
        """
        r1 = 'np.meshgrid('
        for (i, r) in enumerate(R):
            if Rsig[i] > 0.001:
                lgn = eval(self.dist+'.'+self.dist+'(x=0.001, pos=r, wid=Rsig[i])')
                rmin, rmax = find_minmax(lgn, r, Rsig[i])
                r1 = r1 + 'np.linspace(%.10f,%.10f,%d),' % (rmin, rmax, Np)
            else:
                r1 = r1 + '[%.10f],' % r
        r1 = r1[:-1] + ')'
        return (eval(r1))

    def sphere(self,q, R, dist, sdist, rho, eirho, adensity):
        form = np.zeros_like(R[0])
        eiform = np.zeros_like(R[0])
        aform = np.zeros_like(R[0])
        r1 = np.zeros_like(R[0])
        for i, r in enumerate(R):
            drho = rho[i] - rho[i + 1]
            deirho = eirho[i] - eirho[i+1]
            darho = adensity[i] - adensity[i+1]
            r1 += r
            fact=4* np.pi * 2.818e-5*1.0e-8*(np.sin(q * r1) - q * r1 * np.cos(q * r1)) / q ** 3
            form = form + drho * fact
            eiform = eiform +  deirho * fact
            aform = aform + darho * fact
        return  np.sum(np.abs(form) ** 2 * dist) / sdist, np.sum(np.abs(eiform) ** 2 * dist) / sdist, np.sum(np.abs(aform) ** 2 * dist) / sdist, np.sum(eiform*aform*dist) / sdist   #in cm^2

    def sphere_dict(self,q, R, dist, sdist, rho, eirho, adensity,key='SAXS-term'):
        form = np.zeros_like(R[0])
        eiform = np.zeros_like(R[0])
        aform = np.zeros_like(R[0])
        r1 = np.zeros_like(R[0])
        for i, r in enumerate(R):
            drho = rho[i] - rho[i + 1]
            deirho = eirho[i] - eirho[i+1]
            darho = adensity[i] - adensity[i+1]
            r1 += r
            fact=4* np.pi * 2.818e-5*1.0e-8*(np.sin(q * r1) - q * r1 * np.cos(q * r1)) / q ** 3
            eiform = eiform +  deirho*fact
            aform = aform + darho*fact
            form = form + drho * fact
        if key=='SAXS-term':
            return np.sum(np.abs(eiform) ** 2 * dist) / sdist # in cm^2
        elif key=='Resonant-term':
            return np.sum(np.abs(aform) ** 2 * dist) / sdist # in cm^2
        elif key=='Cross-term':
            return np.abs(np.sum(eiform * aform * dist) / sdist)  # in cm^2
        elif key=='Total':
            return np.sum(np.abs(form) ** 2 * dist) / sdist # in cm^2


    def update_params(self):
        self.norm=self.params['norm'].value
        self.sbkg=self.params['sbkg'].value
        self.cbkg = self.params['cbkg'].value
        self.abkg = self.params['abkg'].value
        self.D= self.params['D'].value
        self.phi = self.params['phi'].value
        self.U = self.params['U'].value
        key='Density'
        self.__density__=[self.params['__%s__%03d'%(key,i)].value for i in range(len(self.__mpar__[key]))]
        key='Sol_Density'
        self.__sol_density__=[self.params['__%s__%03d'%(key,i)].value for i in range(len(self.__mpar__[key]))]
        key='Rmoles'
        self.__Rmoles__=[self.params['__%s__%03d'%(key,i)].value for i in range(len(self.__mpar__[key]))]
        key='R'
        self.__R__=[self.params['__%s__%03d'%(key,i)].value for i in range(len(self.__mpar__[key]))]
        key='Rsig'
        self.__Rsig__=[self.params['__%s__%03d'%(key,i)].value for i in range(len(self.__mpar__[key]))]
        key='Material'
        self.__material__=[self.__mpar__[key][i] for i in range(len(self.__mpar__[key]))]

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params={}
        self.update_params()
        # for key in self.params.keys():
        #     print('%s: %f %f'%(key,self.params[key].min,self.params[key].max))
        rho,eirho,adensity,rhor,eirhor,adensityr=self.calc_rho(R=self.__R__,material=self.__material__, density=self.__density__, sol_density=self.__sol_density__,Energy=self.Energy, Rmoles= self.__Rmoles__, NrDep=self.NrDep)
        #rho.append(self.rhosol)
        #eirho.append(self.rhosol)
        #adensity.append(0.0)
        r=self.calc_mesh(R=self.__R__[:-1],Rsig=self.__Rsig__[:-1],Np=self.Np)
        adist = np.ones_like(r[0])
        for i in range(len(self.__R__)-1):
            if self.__Rsig__[i] > 0.001:
                if self.dist=='LogNormal':
                    adist *= np.exp(-(np.log(r[i]) - np.log(self.__R__[i])) ** 2 / 2 / self.__Rsig__[i] ** 2) / r[i] / 2.5066/self.__Rsig__[i]
                else:
                    adist *= np.exp(-(r[i]-self.__R__[i])**2/2/self.__Rsig__[i]**2)/2.5066/self.__Rsig__[i]
        sdist = np.sum(adist)
        if type(self.x)==dict:
            sqf={}
            for key in self.x.keys():
                sq=[]
                for q1 in self.x[key]:
                    sq.append(self.sphere_dict(q1, r, adist, sdist, rho, eirho, adensity,key=key))
                sqf[key] = self.norm * np.array(sq) * 6.022e20  # in cm^-1
                if self.SF is None:
                    struct = np.ones_like(self.x[key])#hard_sphere_sf(self.x[key], D = self.D, phi = 0.0)
                elif self.SF == 'Hard-Sphere':
                    struct = hard_sphere_sf(self.x[key], D=self.D, phi=self.phi)
                else:
                    struct = sticky_sphere_sf(self.x[key], D=self.D, phi=self.phi, U=self.U, delta=0.01)
                if key=='SAXS-term':
                    sqf[key]=sqf[key]*struct+self.sbkg
                if key=='Cross-term':
                    sqf[key]=sqf[key]*struct+self.cbkg
                if key=='Resonant-term':
                    sqf[key]=sqf[key]*struct+self.abkg
            key1='Total'
            sqt=[]
            for q1 in self.x[key]:
                 sqt.append(self.sphere_dict(q1, r, adist, sdist, rho, eirho, adensity, key=key1))
            total = self.norm * np.array(sqt) * 6.022e20*struct + self.sbkg # in cm^-1
            if not self.__fit__:
                self.output_params['Simulated_total_wo_err']={'x':self.x[key],'y':total}
                self.output_params['rho_r'] = {'x': rhor[:, 0], 'y': rhor[:, 1]}
                self.output_params['eirho_r'] = {'x': eirhor[:, 0], 'y': eirhor[:, 1]}
                self.output_params['adensity_r'] = {'x': adensityr[:, 0], 'y': adensityr[:, 1]}
                self.output_params['Structure_Factor']={'x':self.x,'y':struct}
            #sqf[key1]=total
            # sqerr = np.sqrt(self.flux * sqf[key] * 1e-5) / self.flux
            # sqwerr = sqf[key] * 1e-5 + 2 * (0.5 - np.random.rand(len(sqf[key]))) * sqerr
            # self.output_params['simulated_total_wo_err'] = {'x': self.x, 'y': sqf[key]}
            # self.output_params['simulated_total_w_err'] = {'x': self.x, 'y': sqwerr}
        else:
            sqf = []
            asqf = []
            eisqf = []
            csqf = []
            if self.SF is None:
                struct = np.ones_like(self.x)
            elif self.SF == 'Hard-Sphere':
                struct = hard_sphere_sf(self.x, D=self.D, phi=self.phi)
            else:
                struct = sticky_sphere_sf(self.x, D=self.D, phi=self.phi, U=self.U, delta=0.01)
            for q1 in self.x:
                tsq,eisq,asq,csq=self.sphere(q1, r, adist, sdist, rho,eirho,adensity)
                sqf.append(tsq)
                asqf.append(asq)
                eisqf.append(eisq)
                csqf.append(csq)
            sqf=self.norm*np.array(sqf) * 6.022e20 * struct + self.sbkg#in cm^-1
            if not self.__fit__: #Generate all the quantities below while not fitting
                asqf=self.norm*np.array(asqf) * 6.022e20 * struct + self.abkg#in cm^-1
                eisqf=self.norm*np.array(eisqf) * 6.022e20 * struct + self.sbkg#in cm^-1
                csqf = self.norm * np.array(csqf) * 6.022e20 * struct + self.cbkg # in cm^-1
                svol=0.2**2 * 1.5 * 1e-3 # scattering volume in cm^3
                sqerr=np.sqrt(self.flux*sqf*svol)
                sqwerr=(sqf * svol * self.flux + 2 * (0.5-np.random.rand(len(sqf))) * sqerr)
                self.output_params['simulated_total_w_err']={'x':self.x,'y':sqwerr,'yerr':sqerr}
                self.output_params['simulated_total_wo_err']={'x':self.x,'y':sqf*svol*self.flux}
                self.output_params['simulated_anomalous'] = {'x': self.x, 'y': asqf}
                self.output_params['simulated_saxs'] = {'x': self.x, 'y': eisqf}
                self.output_params['simulated_cross']={'x':self.x,'y':csqf}
                self.output_params['rho_r'] = {'x': rhor[:, 0], 'y': rhor[:, 1]}
                self.output_params['eirho_r'] = {'x': eirhor[:, 0], 'y': eirhor[:, 1]}
                self.output_params['adensity_r'] = {'x': adensityr[:, 0], 'y': adensityr[:, 1]}
                self.output_params['Structure_Factor'] = {'x': self.x, 'y': struct}
        return sqf


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Sphere_Uniform(x=x)
    print(fun.y())

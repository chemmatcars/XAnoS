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
from FormFactors.Sphere import Sphere
from ff_sphere import ff_sphere_ml
from Chemical_Formula import Chemical_Formula
from PeakFunctions import LogNormal, Gaussian
from Structure_Factors import hard_sphere_sf, sticky_sphere_sf
from utils import find_minmax
from functools import lru_cache
import time



class Oblate_Disc: #Please put the class name same as the function name
    def __init__(self, x=0, Np=10, flux=1e13, term='Total',dist='Gaussian', Energy=None, relement='Au',lnum=10, NrDep='True', norm=1.0, aspect=1.0, Rsig=0.0, sbkg=0.0, cbkg=0.0, abkg=0.0, D=1.0, phi=0.1, U=-1.0, SF='None', mpar={'Material':['Au','H2O'],'Density':[19.32,1.0],'Sol_Density':[1.0,1.0],'Rmoles':[1.0,0.0],'R':[1.0,0.0]}):
        """
        Documentation
        Calculates the Energy dependent form factor of multilayered oblate nanoparticles with different materials

        x           : Reciprocal wave-vector 'Q' inv-Angs in the form of a scalar or an array
        relement    : Resonant element of the nanoparticle. Default: 'Au'
        Energy      : Energy of X-rays in keV at which the form-factor is calculated. Default: None
        Np          : No. of points with which the size distribution will be computed. Default: 10
        NrDep       : Energy dependence of the non-resonant element. Default= 'True' (Energy Dependent), 'False' (Energy independent)
        dist        : The probablity distribution fucntion for the radii of different interfaces in the nanoparticles. Default: Gaussian
        aspect      : Ratio of thickness to the diameter of the disc in Angstroms
        norm        : The density of the nanoparticles in Molar (Moles/Liter)
        sbkg        : Constant incoherent background for SAXS-term
        cbkg        : Constant incoherent background for cross-term
        abkg        : Constant incoherent background for Resonant-term
        flux        : Total X-ray flux to calculate the errorbar to simulate the errorbar for the fitted data
        term        : 'SAXS-term' or 'Cross-term' or 'Resonant-term'
        D           : Hard Sphere Diameter
        phi         : Volume fraction of particles
        U           : The sticky-sphere interaction energy
        SF          : Type of structure factor. Default: 'None'
        Rsig        : Width of distribution of radii
        lnum        : Number of sublayers in which all the layers will be further divided
        mpar        : Multi-parameter which defines the following including the solvent/bulk medium which is the last one. Default: 'H2O'
                        Material ('Materials' using chemical formula),
                        Density ('Density' in gm/cubic-cms),
                        Density of solvent ('Sol_Density' in gm/cubic-cms) of the particular layer
                        Mole-fraction ('Rmoles') of resonant element in the material)
                        Radii ('R' in Angs), and
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.aspect=aspect
        self.norm=norm
        self.sbkg=sbkg
        self.cbkg=cbkg
        self.abkg=abkg
        self.dist=dist
        self.Np=Np
        self.Energy=Energy
        self.relement=relement
        self.NrDep=NrDep
        self.lnum=lnum
        #self.rhosol=rhosol
        self.flux=flux
        self.D=D
        self.phi=phi
        self.U=U
        self.Rsig=Rsig
        self.__mpar__=mpar #If there is any multivalued parameter
        self.SF=SF
        self.term=term
        self.choices={'dist':['Gaussian','LogNormal'],'NrDep':['True','False'],'SF':['None','Hard-Sphere', 'Sticky-Sphere'],
                      'term':['SAXS-term','Cross-term','Resonant-term','Total']} #If there are choices available for any fixed parameters
        self.init_params()
        self.__cf__=Chemical_Formula()
        self.__fit__=False
        self.output_params={}
        self.output_params={'scaler_parameters':{}}


    def init_params(self):
        """
        Define all the fitting parameters like
        self.params.add('sig',value = 0, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = None)
        """
        self.params=Parameters()
        self.params.add('aspect',value=self.aspect, vary=0, min=0, max=1, expr=None, brute_step=0.1)
        self.params.add('norm',value=self.norm,vary=0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('D', value=self.D, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('phi', value=self.phi, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('sbkg',value=self.sbkg,vary=0, min = -np.inf, max = np.inf, expr = None, brute_step = 0.1)
        self.params.add('cbkg', value=self.cbkg, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('abkg', value=self.abkg, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('U', value=self.U, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('Rsig', value=self.Rsig, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        for key in self.__mpar__.keys():
            if key!='Material':
                for i in range(len(self.__mpar__[key])):
                    self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)


    @lru_cache(maxsize=1)
    def calc_rho(self,R=(1.0,0.0),material=('Au','H2O'), relement='Au', density=(19.3,1.0), sol_density=(1.0,1.0), Rmoles=(1.0,0.0), Energy=None, NrDep='True'):
        """
        Calculates the complex electron density of core-shell type multilayered particles in el/Angstroms^3

        R         :: list of Radii and subsequent shell thicknesses in Angstroms of the nanoparticle system
        material  :: list of material of all the shells starting from the core to outside
        relement  :: Resonant element
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
                    element_adjust = None
                    if '*' in solute:
                        m = solute.split('*')[0]
                        f = self.__cf__.parse(m)
                        element_adjust = self.__cf__.elements()[-1]
                    solute_formula=self.__cf__.parse(solute)
                    if relement in solute_formula.keys():
                        if element_adjust is not None:
                            self.__cf__.formula_dict[relement] = 0.0
                            t1 = self.__cf__.molar_mass()
                            self.__cf__.formula_dict[element_adjust] = self.__cf__.element_mole_ratio()[element_adjust] - Rmoles[i]
                            self.__cf__.formula_dict[relement] = Rmoles[i]
                            t2 = self.__cf__.molar_mass()
                            if t1 > 0:
                                fac = t2 / t1
                    density[i]=fac*density[i]
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
                    element_adjust=None
                    if '*' in material[i]:
                        m=material[i].split('*')[0]
                        f=self.__cf__.parse(m)
                        element_adjust=self.__cf__.elements()[-1]
                    formula = self.__cf__.parse(material[i])
                    fac = 1.0
                    if relement in formula.keys():
                        self.__cf__.formula_dict[relement] = 0.0
                        t1 = self.__cf__.molar_mass()
                        if element_adjust is not None:
                            self.__cf__.formula_dict[element_adjust] = self.__cf__.element_mole_ratio()[
                                                                           element_adjust] - Rmoles[i]
                        self.__cf__.formula_dict[relement] = Rmoles[i]
                        t2 = self.__cf__.molar_mass()
                        if t1 > 0:
                            fac = t2 / t1
                    mole_ratio = self.__cf__.element_mole_ratio()
                    comb_material = ''
                    for ele in mole_ratio.keys():
                        comb_material += '%s%.10f' % (ele, mole_ratio[ele])
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
                        if elements[j]!=relement:
                            if NrDep:
                                f1 = self.__cf__.xdb.f1_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                                f2 = self.__cf__.xdb.f2_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                                felectrons = felectrons + moles[j] * complex(f1, f2)
                        else:
                            f1 = self.__cf__.xdb.f1_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                            f2 = self.__cf__.xdb.f2_chantler(element=elements[j], energy=Energy * 1e3, smoothing=0)
                            felectrons = felectrons + moles[j] * complex(f1, f2)
                    if elements[j]==relement:
                        aden+=0.6023 * moles[j]*tdensity/molwt
                adensity.append(aden)# * np.where(r > Radii[i - 1], 1.0, 0.0) * pl.where(r <= Radii[i], 1.0, 0.0) / molwt
                eirho.append(0.6023 * (nelectrons) * tdensity/molwt)# * np.where(r > Radii[i - 1], 1.0,0.0) * pl.where(r <= Radii[i], 1.0,0.0) / molwt
                rho.append(0.6023 * (nelectrons + felectrons) * tdensity/molwt)# * np.where(r > Radii[i - 1], 1.0,0.0) * pl.where(r <= Radii[i], 1.0, 0.0) / molwt
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

    @lru_cache(maxsize=2)
    def calc_Rdist(self, R, Rsig, dist, N):
        R=np.array(R)
        totalR = np.sum(R[:-1])
        if Rsig>0.001:
            fdist = eval(dist + '.' + dist + '(x=0.001, pos=totalR, wid=Rsig)')
            rmin, rmax = find_minmax(fdist, totalR, Rsig)
            dr = np.linspace(rmin, rmax, N)
            fdist.x = dr
            rdist = fdist.y()
            sumdist = np.sum(rdist)
            rdist = rdist / sumdist
            self.output_params['Distribution'] = {'x': dr, 'y': rdist}
            return dr, rdist, totalR
        else:
            self.output_params['Distribution'] = {'x': [totalR], 'y': [1.0]}
            return [totalR],[1.0], totalR

    @lru_cache(maxsize=2)
    def new_sphere(self,q,R,Rsig,rho,eirho,adensity,dist='Gaussian',Np=10):
        q=np.array(q)
        dr, rdist, totalR = self.calc_Rdist(R, Rsig, dist, Np)
        form = np.zeros_like(q)
        eiform = np.zeros_like(q)
        aform = np.zeros_like(q)
        cform = np.zeros_like(q)
        pfac=(4 * np.pi * 2.818e-5 * 1.0e-8)**2
        for i in range(len(dr)):
            r = np.array(R) * (1 + (dr[i] - totalR) / totalR)
            ff,mff=ff_sphere_ml(q, r, rho)
            form = form + rdist[i] * ff
            eiff,meiff=ff_sphere_ml(q, r, eirho)
            eiform = eiform + rdist[i] * eiff
            aff,maff=ff_sphere_ml(q, r, adensity)
            aform = aform + rdist[i] * aff
            cform = cform + rdist[i]*meiff*maff
        return pfac*form,pfac*eiform,pfac*aform,np.abs(pfac*cform) #in cm^2

    @lru_cache(maxsize=2)
    def new_sphere_dict(self,q,R,Rsig,rho,eirho,adensity,dist='Gaussian',Np=10,key='SAXS-term'):
        form, eiform,aform,cform=self.new_sphere(q,R,Rsig,rho,eirho,adensity,dist=dist,Np=Np)
        if key=='SAXS-term':
            return eiform
        elif key=='Resonant-term':
            return aform
        elif key=='Cross-term':
            return cform
        elif key=='Total':
            return form


    def update_params(self):
        key='Density'
        self.__density__=[self.params['__%s__%03d'%(key,i)].value for i in range(len(self.__mpar__[key]))]
        key='Sol_Density'
        self.__sol_density__=[self.params['__%s__%03d'%(key,i)].value for i in range(len(self.__mpar__[key]))]
        key='Rmoles'
        self.__Rmoles__=[self.params['__%s__%03d'%(key,i)].value for i in range(len(self.__mpar__[key]))]
        key='R'
        self.__R__=[self.params['__%s__%03d'%(key,i)].value for i in range(len(self.__mpar__[key]))]
        key='Material'
        self.__material__=[self.__mpar__[key][i] for i in range(len(self.__mpar__[key]))]


    @lru_cache(maxsize=2)
    def create_layers(self,R,material,density,sol_density,Rmoles, lnum=10):
        R=list(R)
        rt=[]
        mt=[]
        dt=[]
        sdt=[]
        rmols=[]
        R[-1]=R[-2]
        for i, r in enumerate(R):
            rt=rt+[r/lnum]*lnum
            mt=mt+[material[i]]*lnum
            dt=dt+[density[i]]*lnum
            sdt=sdt+[sol_density[i]]*lnum
            rmols=rmols+[Rmoles[i]]*lnum
        return tuple(rt), tuple(mt), tuple(dt), tuple(sdt), tuple(rmols)

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.update_params()
        rt, mt, dt, sdt, rmols = self.create_layers(tuple(self.__R__), tuple(self.__material__), tuple(self.__density__),
                                                    tuple(self.__sol_density__), tuple(self.__Rmoles__), lnum=self.lnum)
        trt=np.array(rt)
        r=np.cumsum(rt)
        Rtot=np.sum(self.__R__[:-1])
        thickness=Rtot*self.aspect
        self.output_params['scaler_parameters']['Thickness']=2*thickness
        self.output_params['scaler_parameters']['Diameter']=2*Rtot
        dt=np.where(((r-trt/2)>thickness)&((r-trt/2)<Rtot),2*(np.array(dt)-dt[-1])*
                    np.arcsin(thickness*np.sqrt((Rtot**2-(r-trt/2)**2)/(Rtot**2-thickness**2))/(r-trt/2))/np.pi+dt[-1],
                    np.array(dt))
        self.output_params['density']={'x':r,'y':dt}
        rho,eirho,adensity,rhor,eirhor,adensityr=self.calc_rho(R=rt,material=mt,relement=self.relement,
                                                               density=tuple(dt), sol_density=sdt,
                                                               Energy=self.Energy, Rmoles=tuple(rmols), NrDep=self.NrDep)
        if type(self.x)==dict:
            sqf={}
            for key in self.x.keys():
                sqf[key] = self.norm * 6.022e20 * self.new_sphere_dict(tuple(self.x[key]),rt,self.Rsig,
                                                                       tuple(rho), tuple(eirho), tuple(adensity),key=key,
                                                                       dist=self.dist,Np=self.Np)  # in cm^-1
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
            total = self.norm * 6.022e20*struct *self.new_sphere_dict(tuple(self.x[key]), rt,self.Rsig,
                                                                      tuple(rho), tuple(eirho), tuple(adensity), key=key1,
                                                                      dist=self.dist,Np=self.Np)+ self.sbkg # in cm^-1
            if not self.__fit__:
                self.output_params['Simulated_total_wo_err']={'x':self.x[key],'y':total}
                self.output_params['rho_r'] = {'x': rhor[:, 0], 'y': rhor[:, 1]}
                self.output_params['eirho_r'] = {'x': eirhor[:, 0], 'y': eirhor[:, 1]}
                self.output_params['adensity_r'] = {'x': adensityr[:, 0], 'y': adensityr[:, 1]}
                self.output_params['Structure_Factor']={'x':self.x,'y':struct}
        else:
            if self.SF is None:
                struct = np.ones_like(self.x)
            elif self.SF == 'Hard-Sphere':
                struct = hard_sphere_sf(self.x, D=self.D, phi=self.phi)
            else:
                struct = sticky_sphere_sf(self.x, D=self.D, phi=self.phi, U=self.U, delta=0.01)

            tsqf,eisqf,asqf,csqf=self.new_sphere(tuple(self.x), rt,self.Rsig, tuple(rho),tuple(eirho),
                                                 tuple(adensity),dist=self.dist,Np=self.Np)
            sqf=self.norm*np.array(tsqf) * 6.022e20 * struct + self.sbkg#in cm^-1
            # if not self.__fit__: #Generate all the quantities below while not fitting
            asqf=self.norm*np.array(asqf) * 6.022e20 * struct + self.abkg#in cm^-1
            eisqf=self.norm*np.array(eisqf) * 6.022e20 * struct + self.sbkg#in cm^-1
            csqf = self.norm * np.array(csqf) * 6.022e20 * struct + self.cbkg # in cm^-1
            svol=0.2**2 * 1.5 * 1e-3 # scattering volume in cm^3
            sqerr=np.sqrt(self.flux*tsqf*svol)
            sqwerr=(tsqf * svol * self.flux + 2 * (0.5-np.random.rand(len(tsqf))) * sqerr)
            self.output_params['simulated_total_w_err']={'x':self.x,'y':sqwerr,'yerr':sqerr}
            self.output_params['Total']={'x':self.x,'y':tsqf*svol*self.flux}
            self.output_params['Resonant-term'] = {'x': self.x, 'y': asqf}
            self.output_params['SAXS-term'] = {'x': self.x, 'y': eisqf}
            self.output_params['Cross-term']={'x':self.x,'y':csqf}
            self.output_params['rho_r'] = {'x': rhor[:, 0], 'y': rhor[:, 1]}
            self.output_params['eirho_r'] = {'x': eirhor[:, 0], 'y': eirhor[:, 1]}
            self.output_params['adensity_r'] = {'x': adensityr[:, 0], 'y': adensityr[:, 1]}
            self.output_params['Structure_Factor'] = {'x': self.x, 'y': struct}
            sqf=self.output_params[self.term]['y']
        return sqf


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=Oblate_Disc(x=x)
    print(fun.y())

####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
import sys
import os
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_routines'))
####Please do not remove lines above####

####Import your modules below if needed####
from ff_cylinder import ff_cylinder_ML



class CoreShellCylinder: #Please put the class name same as the function name
    def __init__(self,x=0, R=1.0, Rsig=0.0, rhoCore=1.0, shell=1.0, rhoShell=0.0, rhoSol=0.0, H=1.0, Hsig=0.0, Nsample=41, dist='Gaussian', norm=1.0,bkg=0.0, mpar={}):
        """
        Form factor of a poly-dispersed core-shell cylinder (still under development)
        x           : Independent variable in the form of a scalar or an array of Q-values
        R           : Radius of the cylindrical core in the same inverse unit as Q
        Rsig        : Width of the distribution in core radius R
        rhoCore     : The electron density of the core in el/Angs^3
        shell       : Thickness of the shell
        rhoShell    : Electron density of the shell in el/Angs^3
        rhoSol      : Electron density of the solvent in el/Angs^3
        H           : Length/Height of the cylindrical core in the same inverse unit as Q
        Hsig        : Width of the distribution in H
        Nsample     : No. of points for doing the averging
        dist        : The type of distribution: "Gaussian" or "LogNormal"
        norm        : Normalization constant
        bkg         : Additive constant background
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.R = R
        self.Rsig = Rsig
        self.rhoCore=rhoCore
        self.shell=shell
        self.rhoShell=rhoShell
        self.rhoSol=rhoSol
        self.H = H
        self.Hsig = Hsig
        self.dist = dist
        self.norm = norm
        self.bkg = bkg
        self.Nsample = Nsample
        self.__mpar__ = mpar #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.output_params={}
        self.init_params()
        self.__fit__=False

    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value = 0, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = None)
        """
        self.params=Parameters()
        self.params.add('R', value=self.R, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('Rsig', value=self.Rsig, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('rhoCore',value=self.rhoCore, vary= 0 , min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('shell', value=self.Rsig, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('rhoShell',value=self.rhoShell, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('rhoSol',value=self.rhoShell, vary=0,min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('H', value=self.H, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('Hsig', value=self.Hsig, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('R', value=self.R, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('norm', value=self.norm, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('bkg', value=self.bkg, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        for key in self.__mpar__.keys():
            if key!='type':
                for i in range(len(self.__mpar__[key])):
                        self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)

    def update_parameters(self):
        self.R = self.params['R'].value
        self.Rsig = self.params['Rsig'].value
        self.rhoCore = self.params['rhoCore'].value
        self.shell = self.params['shell'].value
        self.rhoShell = self.params['rhoShell'].value
        self.rhoSol = self.params['rhoSol'].value
        self.H = self.params['H'].value
        self.Hsig = self.params['Hsig'].value
        self.norm = self.params['norm'].value
        self.bkg = self.params['bkg'].value

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        q = self.x
        self.output_params={}
        if self.dist == 'Gaussian':
            if self.Rsig > 1e-3:
                rdist = Gaussian.Gaussian(x=0.0, pos=self.R, wid=self.Rsig)
                rmin, rmax = max(0.001, self.R - 5 * self.Rsig), self.R + 5 * self.Rsig
                r = np.linspace(rmin, rmax, self.Nsample)
                rdist.x = r
                distr = rdist.y()
                self.output_params['R_distribution'] = {'x': r, 'y': distr}
            else:
                r = np.array([self.R])
                distr = np.ones_like(r)
            if self.Hsig > 1e-3:
                hdist = Gaussian.Gaussian(x=0.0, pos=self.H, wid=self.Hsig)
                hmin, hmax = max(0.001, self.H - 5 * self.Hsig), self.H + 5 * self.Hsig
                h = np.linspace(hmin, hmax, self.Nsample)
                hdist.x = h
                disth = hdist.y()
                self.output_params['H_distribution'] = {'x': h, 'y': disth}
                if self.Rsig < 1e-3:
                    r = np.ones_like(h) * self.R
                    distr = np.ones_like(r)
            else:
                h = np.ones_like(r) * self.H
                disth = np.ones_like(h)
        elif self.dist == 'LogNormal':
            if self.Rsig > 1e-3:
                rdist = LogNormal.LogNormal(x=0.0, pos=self.R, wid=self.Rsig)
                rmin, rmax = max(0.001, self.R * (1 - np.exp(self.Rsig))), self.R * (1 + 2 * np.exp(self.Rsig))
                r = np.linspace(rmin, rmax, self.Nsample)
                rdist.x = r
                distr = rdist.y()
                self.output_params['R_distribution'] = {'x': r, 'y': distr}
            else:
                r = np.array([self.R])
                distr = np.ones_like(r)
            if self.Hsig > 1e-3:
                hdist = LogNormal.LogNormal(x=0.0, pos=self.H, wid=self.Hsig)
                hmin, hmax = max(0.001, self.H * (1 - np.exp(self.Hsig))), self.H * (1 + 2 * np.exp(self.Hsig))
                h = np.linspace(hmin, hmax, self.Nsample)
                hdist.x = h
                disth = hdist.y()
                self.output_params['H_distribution'] = {'x': h, 'y': disth}
                if self.Rsig < 1e-3:
                    r = np.ones_like(h) * self.R
                    distr = np.ones_like(r)
            else:
                h = np.ones_like(r) * self.H
                disth = np.ones_like(h)

        result = ff_cylinder_ML(q,r,distr,h,disth)
        return self.norm * result + self.bkg

if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=CoreShellCylinder(x=x)
    print(fun.y())

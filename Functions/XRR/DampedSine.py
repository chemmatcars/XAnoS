####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
import sys
import os
import math
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_routines/'))
from functools import lru_cache
####Please do not remove lines above####

####Import your modules below if needed####
from xr_ref import parratt


class DampedSine: #Please put the class name same as the function name
    def __init__(self, x=0.1, E=10.0, mpar={
        'Model': {'Layers': ['top', 'Bottom'], 'd': [0.0, 1.0], 'rho': [0.0, 0.333], 'beta': [0.0, 0.0],
                   'sig': [0.0, 3.0]}},
                 Minstep=0.5, rrf=True, fix_sig=False, qoff=0.0, yscale=1, amp=0.1, decay_len= 100, spacing= 10, z0=0, bkg=0.0):
        """
        Calculates X-ray reflectivity from a system of multiple layers using Parratt formalism

        x     	: array of wave-vector transfer along z-direction
        E     	: Energy of x-rays in invers units of x
        mpar  	: Dictionary of Phases where, Layers: Layer description, d: thickness of each layer, rho:Electron density of each layer, beta: Absorption coefficient of each layer, sig: roughness of interface separating each layer. The upper and lower thickness should be always  fixed. The roughness of the topmost layer should be always kept 0.
        Minstep 	: The thickness (Angstrom) of each layer for applying Parratt formalism
        rrf   	: True for Frensnel normalized refelctivity and False for just reflectivity
        qoff  	: q-offset to correct the zero q of the instrument
        yscale  : a scale factor for R or R/Rf
        amp     : the amplitude of the density oscillation at z=z0 as a fraction of subphase density
        decay_len : the decay length in unit of Angstrom
        spacing : the layer spacing in unit of Angstrom
        z0      : the starting position of the oscillation
        bkg     : In-coherrent background
        """
        if type(x) == list:
            self.x = np.array(x)
        else:
            self.x = x
        self.E = E
        self.__mpar__ = mpar
        self.Minstep = Minstep
        self.rrf = rrf
        self.fix_sig = fix_sig
        self.qoff = qoff
        self.yscale = yscale
        self.amp = amp
        self.decay_len = decay_len
        self.spacing = spacing
        self.z0= z0
        self.bkg = bkg
        self.choices = {'rrf': [True, False], 'fix_sig': [True, False]}
        self.__d__ = {}
        self.__rho__ = {}
        self.__beta__ = {}
        self.__sig__ = {}
        self.__fit__ = False
        self.__mkeys__=list(self.__mpar__.keys())
        self.init_params()

    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params = Parameters()
        self.params.add('qoff', self.qoff, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('yscale', self.yscale, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('amp', self.amp, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('decay_len', self.decay_len, vary=0, min=0.01, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('spacing', self.spacing, vary=0, min=0.01, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('z0', self.z0, vary=0, min=-np.inf, max=np.inf, expr=None, brute_step=0.1)
        self.params.add('bkg', self.bkg, vary=0, min=0, max=1, expr=None, brute_step=0.1)
        for mkey in self.__mkeys__:
            for key in self.__mpar__[mkey].keys():
                if key != 'Layers':
                    for i in range(len(self.__mpar__[mkey][key])):
                        self.params.add('__%s_%s_%03d' % (mkey, key, i), value=self.__mpar__[mkey][key][i], vary=0,
                                        min=0, max=np.inf, expr=None, brute_step=0.05)

    @lru_cache(maxsize=2)
    def calcProfile(self, d, rho, beta, sig, minstep, amp, decaylen, spacing, z0):
        """
        Calculates the electron and absorption density profiles
        """
        d = np.array(d)
        rho = np.array(rho)
        beta = np.array(beta)
        sig = np.array(sig)
        n = len(d)
        maxsig = max(np.abs(np.max(sig[1:])), 3)
        offset = np.sum(d[:-1])
        zmin = -offset - 5 * maxsig
        zmax = max(5 * maxsig, 8*decaylen)
        Nlayers = int((zmax - zmin) / minstep)
        __z__ = np.linspace(zmin, zmax, Nlayers + 1)

        __d__ = np.diff(__z__)
        __d__ = np.append(__d__, [__d__[-1]])
        __rho__ = self.sldCalFun(tuple(d), tuple(rho), tuple(sig), tuple(__z__), offset=offset)
        __beta__ = self.sldCalFun(tuple(d), tuple(beta), tuple(sig), tuple(__z__), offset=offset)

        # calculate the density profile for oscillation
        __rho2__ = amp*rho[-1]*np.exp(-(__z__-z0)/decaylen)*np.sin(2*np.pi*(__z__-z0)/spacing)*np.heaviside(__z__-z0,1)
        __beta2__ = amp * beta[-1] * np.exp(-(__z__ - z0) / decaylen) * np.sin( 2 * np.pi * (__z__ - z0) / spacing) * np.heaviside(__z__ - z0, 1)
        __rho__=list(np.array(__rho__)+__rho2__)
        __beta__ = list(np.array(__beta__) + __beta2__)
        return n, __z__, __d__, __rho__, __beta__

    @lru_cache(maxsize=10)
    def sldCalFun(self, d, y, sigma, x, offset=0.0):
        wholesld = []
        for j in range(len(x)):
            sld = 0
            for i in range(len(d) - 1):
                pos = np.sum(d[:i + 1])
                sld = sld + math.erf((x[j] - pos + offset) / sigma[i + 1] / math.sqrt(2)) * (y[i + 1] - y[i])
            wholesld.append(max((sld + y[0] + y[-1]) / 2, 0))
        return wholesld

    @lru_cache(maxsize=10)
    def py_parratt(self, x, lam, d, rho, beta):
        return parratt(np.array(x), lam, np.array(d), np.array(rho), np.array(beta))

    def update_parameters(self):
        for mkey in self.__mpar__.keys():
            # for key in self.__mpar__[mkey].keys():
            Nlayers = len(self.__mpar__[mkey]['d'])
            self.__d__[mkey] = tuple([self.params['__%s_%s_%03d' % (mkey, 'd', i)].value for i in range(Nlayers)])
            self.__rho__[mkey] = tuple([self.params['__%s_%s_%03d' % (mkey, 'rho', i)].value for i in range(Nlayers)])
            self.__beta__[mkey] = tuple([self.params['__%s_%s_%03d' % (mkey, 'beta', i)].value for i in range(Nlayers)])
            self.__sig__[mkey] = tuple([self.params['__%s_%s_%03d' % (mkey, 'sig', i)].value for i in range(Nlayers)])

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        self.output_params = {'scaler_parameters': {}}
        x = self.x + self.qoff
        lam = 6.62607004e-34 * 2.99792458e8 * 1e10 / self.E / 1e3 / 1.60217662e-19
        if not self.__fit__:
            for mkey in self.__mpar__.keys():
                Nlayers = len(self.__mpar__[mkey]['sig'])
                for i in range(2,Nlayers):
                    if self.fix_sig:
                        self.params['__%s_%s_%03d'%(mkey,'sig',i)].expr='__%s_%s_%03d'%(mkey,'sig',1)
                    else:
                        self.params['__%s_%s_%03d' % (mkey, 'sig', i)].expr = None
        self.update_parameters()
        mkey=list(self.__mpar__.keys())[0]
        n, z, d, rho, beta = self.calcProfile(self.__d__[mkey], self.__rho__[mkey],
                                                                                self.__beta__[mkey], self.__sig__[mkey], self.Minstep,
                                                                                self.amp, self.decay_len, self.spacing, self.z0)
        if not self.__fit__:
            self.output_params['%s_EDP' % self.__mkeys__[0]] = {'x': z, 'y': rho}
            self.output_params['%s_ADP' % self.__mkeys__[0]] = {'x': z, 'y': beta}
        refq, r2 = self.py_parratt(tuple(x), lam, tuple(d), tuple(rho), tuple(beta))
        if self.rrf:
            rhos = (self.params['__%s_rho_000'%(mkey)].value, self.params['__%s_rho_%03d' % (mkey,n - 1)].value)
            betas = (
            self.params['__%s_beta_000'%(mkey)].value, self.params['__%s_beta_%03d' % (mkey, n - 1)].value)
            ref, r2 = self.py_parratt(tuple(x - self.qoff), lam, (0.0, 1.0), rhos, betas)
            refq = refq / ref
        return refq * self.yscale+self.bkg


if __name__=='__main__':
    x=np.linspace(0.001,1.0,100)
    fun=DampedSine(x=x)
    print(fun.y())

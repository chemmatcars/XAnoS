####Please do not remove lines below####
from lmfit import Parameters
import numpy as np
import sys
import os
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./Functions'))
sys.path.append(os.path.abspath('./Fortran_routines/'))
####Please do not remove lines above####

####Import your modules below if needed####
from xr_ref import parratt


class SphereAtInterface: #Please put the class name same as the function name
    def __init__(self,x=0.1,lam=1.0,R=10,Rsig=0.0,rhoc=1.0,D=60.0, cov=100,Zo=20.0,decay=3.0,rho_up=0.333,rho_down=0.38,zmin=-50,zmax=100,Nlayers=151,Nc=20, roughness=3.0,rrf=1,mpar={},qoff=0):
        """
        Calculates X-ray reflectivity from a system of nanoparticle at an interface between two media
        x           : array of wave-vector transfer along z-direction
        lam         : wavelength of x-rays in invers units of x
        R           : Radius of nanoparticles in inverse units of x
        rhoc        : Electron density of the nanoparticles
        cov         : Coverate of the nanoparticles in %
        D           : The lattice constant of the two dimensional hcp structure formed by the particles
        Zo          : Average distance between the center of the nanoparticles and the interface
        decay       : Assuming exponential decay of the distribution of nanoparticles away from the interface
        rho_up      : Electron density of the upper medium
        rho_down    : Electron density of the lower medium
        zmin        : Minimum z value for the electron density profile
        zmin        : Maximum z value for the electron density profile
        Nlayers     : The total number of layers in which the electron density profile will be divided to appy Parratt Formalism
        Nc          : The number of points used for convolution of interfacial roughness with electron density profile
        roughness   : Roughness of the interface
        rrf         : 1 for Frensnel normalized refelctivity and 0 for just reflectivity
        qoff        : offset in the value of qz due to alignment errors
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.R=R
        self.lam=lam
        self.rhoc=rhoc
        self.Zo=Zo
        self.cov=cov
        self.D=D
        self.decay=decay
        self.rho_up=rho_up
        self.rho_down=rho_down
        self.zmin=zmin
        self.zmax=zmax
        self.Nlayers=Nlayers
        self.Nc=Nc
        self.roughness=roughness
        self.rrf=rrf
        self.qoff=qoff
        self.choices={}
        self.output_params={}
        self.__mpar__=mpar


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0)
        """
        self.params=Parameters()
        self.params.add('R',value=self.R,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('rhoc',value=self.rhoc,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('Zo',value=self.Zo,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('D',value=self.D,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('cov',value=self.cov,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('decay',value=self.decay,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('roughness',value=self.roughness,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        self.params.add('qoff',value=self.qoff,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        

    def decayNp(self,z,Rc=10,D=30.0,z0=0.0,xi=1.0,cov=100.0,rhoc=4.65,rhos=[0.334,0.38],sig=1.0,Nc=20):
        if sig<1e-3:
            z2=z
        else:
            Nmax=len(z)+Nc
            zmin=z[0]-(z[1]-z[0])*Nc/2
            zmax=z[-1]+(z[1]-z[0])*Nc/2
            z2=np.linspace(zmin,zmax,Nmax)
        intf=np.where(z2<=0,rhos[0],rhos[1])
        if z0<=0:
            z1=np.arange(-4*xi+z0,z0)
            dec=np.exp((z1-z0)/xi)/xi
        else:
            z1=np.arange(z0,z0+4*xi)
            dec=np.exp((z0-z1)/xi)/xi
        rhoz=np.zeros_like(z2)
        for i in range(len(z1)):
            rhoz=rhoz+self.rhoNPz(z2,z0=z1[i],rhoc=rhoc,Rc=Rc,D=D,rhos=rhos)*dec[i]/sum(dec)
        rhoz=cov*rhoz/100.0+(100-cov)*intf/100.0
        x=np.arange(-Nc/2,Nc/2+1)*(z[1]-z[0])
        if sig>1e-3:
            rough=np.exp(-x**2/2.0/sig**2)/np.sqrt(2*np.pi)/sig
            return np.convolve(rhoz,rough,mode='valid')
        else:
            return rhoz

    def rhoNPz(self,z,z0=0,rhoc=4.65,Rc=10.0,D=28.0,rhos=[0.334,0.38]):
        rhob=np.where(z>0,rhos[1],rhos[0])
        #D=D/2
        return np.where(np.abs(z-z0)<=Rc,(2*np.pi*(rhoc-rhob)*(Rc**2-(z-z0)**2)+1.732*rhob*D**2)/(1.732*D**2),rhob)


    def y(self):
        """
        Define the function in terms of x to return some value
        """
        Rc=self.params['R'].value
        D=self.params['D'].value
        Zo=self.params['Zo'].value
        cov=self.params['cov'].value
        sig=self.params['roughness'].value
        xi=self.params['decay'].value
        rhoc=self.params['rhoc'].value
        qoff=self.params['qoff'].value
        rhos=[self.rho_up,self.rho_down]
        lam=self.lam
        z=np.linspace(self.zmin,self.zmax,self.Nlayers)
        d=np.ones_like(z)
        edp=self.decayNp(z,Rc=Rc,z0=Zo,xi=xi,cov=cov,rhos=rhos,rhoc=rhoc,sig=sig,D=D,Nc=self.Nc)
        self.output_params['EDP']={'x':z,'y':edp}
        beta=np.zeros_like(z)
        rho=np.array(edp,dtype='float')
        refq,r2=parratt(self.x+qoff,lam,d,rho,beta)
        if self.rrf>0:
            ref,r2=parratt(self.x+qoff,lam,[0.0,1.0],rhos,[0.0,0.0])
            refq=refq/ref
        return refq


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=SphereAtInterface(x=x)
    print(fun.y())

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



class MultiPeaks: #Please put the class name same as the function name
    def __init__(self,x=0,power=1,N=0.0,c0=0.0,c1=0.0,c2=0.0,c3=0.0,cN=0.0,cexp=0.0,lexp=1.0,mpar={'type':['Gau'],'pos':[0.5],'wid':[0.1],'norm':[1.0]}):
        """
        Provides multipeak function with different background function

        x     	: independent variable in ter form of a scalar or an array
        power 	: 1 for c0+c1*x+c2x**2+c3*x**3+cN*x**N, -1 for c0+c1/x+c2/x**2+c3/x**3+cN/x**N
        N     	: exponent of arbitrary degree polynomial i.e x**N or 1/x**N
        c0    	: constant background
        c1    	: coeffcient of the linear(x) or inverse(1/x) background
        c2    	: coefficient of the quadratic(x**2) or inverse quadratic(1/x**2) background
        c3    	: coefficient of the cubic bacground
        cN    	: coefficient of the x**N or inverse 1/x**N background
        cexp  	: coefficient of the exponential background
        lexp  	: decay length of the exponential background
        mpar  	: The peak parameters where 'type': ('Gau': Gaussian, 'Lor': lorentzian, 'Ste': step)
        """
        if type(x)==list:
            self.x=np.array(x)
        else:
            self.x=x
        self.power=power
        self.N=N
        self.c0=c0
        self.c1=c1
        self.c2=c2
        self.c3=c3
        self.cN=cN
        self.cexp=cexp
        self.lexp=lexp
        self.__mpar__=mpar #If there is any multivalued parameter
        self.choices={} #If there are choices available for any fixed parameters
        self.init_params()
        self.output_params={'scaler_parameters':{}}


    def init_params(self):
        """
        Define all the fitting parameters like
        self.param.add('sig',value=0,vary=0,,min=-np.inf,max=np.inf,expr=None,brute_step=None)
        """
        self.params=Parameters()
        self.params.add('c0',value=self.c0,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('c1',value=self.c1,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('c2',value=self.c2,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('c3',value=self.c3,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('cN',value=self.cN,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('cexp',value=self.cexp,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        self.params.add('lexp',value=self.lexp,vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=0.1)
        for key in self.__mpar__.keys():
            if key!='type':
                for i in range(len(self.__mpar__[key])):
                        self.params.add('__%s__%03d'%(key,i),value=self.__mpar__[key][i],vary=0,min=-np.inf,max=np.inf,expr=None,brute_step=None)

    def gau(self,x,pos,wid,norm):
        """
        Gaussian function
        """
        return norm*np.exp(-4.0*np.log(2)*(x-pos)**2/wid**2)

    def lor(self,x,pos,wid,norm):
        """
        Lorentzian function
        """
        return norm*wid**2/4.0/((x-pos)**2+wid**2/4)

    def ste(self,x,pos,wid,norm):
        """
        Step function
        """
        return norm*(1.0+np.tanh((x-pos)/wid))/2.0

    def y(self):
        """
        Define the function in terms of x to return some value
        """
        func={'Gau':self.gau,'Lor':self.lor,'Ste':self.ste}
        res=np.zeros_like(self.x)
        for i in range(len(self.__mpar__['type'])):
            peak=self.__mpar__['type'][i]
            pos=self.params['__pos__%03d'%i].value
            wid=self.params['__wid__%03d'%i].value
            norm=self.params['__norm__%03d'%i].value
            fun=func[peak](self.x,pos,wid,norm)
            res=res+fun
            self.output_params['peak_%03d'%(i+1)]={'x':self.x,'y':fun}
        c=[self.params['c%d'%i].value for i in range(4)]
        cN=self.params['cN'].value
        bkg=c[0]+c[1]*self.x**self.power+c[2]*self.x**(self.power*2)+c[3]*self.x**(self.power*3)+cN*self.x**(self.power*self.N)+self.params['cexp'].value*np.exp(-self.x*self.params['lexp'].value)
        res=res+bkg
        self.output_params['bkg']={'x':self.x,'y':bkg}
        return res


if __name__=='__main__':
    x=np.arange(0.001,1.0,0.1)
    fun=MultiPeaks(x=x)
    print(fun.y())

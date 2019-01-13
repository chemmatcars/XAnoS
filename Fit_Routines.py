import numpy as np
from lmfit import fit_report, Minimizer
from PyQt5.QtCore import pyqtSignal, QObject

class Fit(QObject):
    functionCalled=pyqtSignal(dict,int,np.ndarray,str)
    def __init__(self,funClass,x,y=None,yerr=None,parent=None):
        QObject.__init__(self,parent)
        if yerr is None:
            yerr=np.ones_like(x)
        if y is None:
            y=np.zeros_like(x)
        self.x=x
        self.y=y
        self.imin=0
        self.imax=len(self.x)
        self.yerr=yerr
        self.func=funClass()
        self.func.x=self.x
        self.params=self.func.__dict__
        self.func.init_params()
        self.fit_params=self.func.params
        self.fitter=None
        self.result=None


    def sync_param(self):
        for key in self.fit_params.keys():
            self.fit_params[key].value=self.params[key]
        
    def evaluate(self):
        self.func.x=self.x[self.imin:self.imax+1]
        self.yfit=self.func.y()
        return self.yfit
    
    
    def residual(self,params,fit_scale):
        for key in self.fit_params.keys():
            self.params[key]=params[key].value
            self.fit_params[key].value=params[key].value
        yfit=self.evaluate()
        if fit_scale=='Log':
            return (np.log10(self.y[self.imin:self.imax+1])-np.log10(yfit))*self.y[self.imin:self.imax+1]/self.yerr[self.imin:self.imax+1]
        else:
            return (self.y[self.imin:self.imax+1]-yfit)/self.yerr[self.imin:self.imax+1]
        
    def callback(self,params,iterations,residual,fit_scale):
        """
        """
        self.functionCalled.emit(params,iterations,residual,fit_scale)
        if self.fit_abort:
            return True
    
    
    def perform_fit(self,xmin,xmax,fit_scale='Linear',fit_method='leastsq',maxiter=1):
        #self.sync_param()
        self.fit_abort=False
        self.imin,self.imax=np.where(self.x>=xmin)[0][0],np.where(self.x<=xmax)[0][-1]
        if fit_method=='leastsq':
            self.fitter=Minimizer(self.residual,self.fit_params,fcn_args=(fit_scale,),iter_cb=self.callback,nan_policy='omit',maxfev=maxiter)
        else:
            self.fitter=Minimizer(self.residual,self.fit_params,fcn_args=(fit_scale,),iter_cb=self.callback,nan_policy='omit', calc_covar=True)
        self.result=self.fitter.minimize(method=fit_method)        
        return fit_report(self.result),self.result.message
        
        
        
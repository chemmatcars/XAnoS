import numpy as np
from lmfit import fit_report, Minimizer, conf_interval, printfuncs
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QMessageBox
import traceback

class Fit(QObject):
    functionCalled=pyqtSignal(dict,int,np.ndarray,str)
    def __init__(self,funClass,x,y=None,yerr=None,parent=None):
        QObject.__init__(self,parent)

        self.set_x(x,y=y,yerr=yerr)
        self.func=funClass()
        self.func.x=self.x
        self.params=self.func.__dict__
        self.func.init_params()
        self.fit_params=self.func.params
        self.fitter=None
        self.result=None
        self.Niter=0


    def sync_param(self):
        for key in self.fit_params.keys():
            self.fit_params[key].value=self.params[key]

    def set_x(self,x,y=None,yerr=None):
        if type(x)==dict:
            self.x=x
            self.yerr={}
            self.y={}
            self.imin={}
            self.imax={}
            for key in self.x:
                if yerr is None:
                    self.yerr[key]=np.ones_like(self.x[key])
                else:
                    self.yerr[key]=yerr[key]
                if y is None:
                    self.y[key]=np.zeros_like(self.x[key])
                else:
                    self.y[key]=y[key]
                self.imin[key] = 0
                self.imax[key] = len(self.x[key])
        else:
            self.x=x
            if yerr is None:
                self.yerr=np.ones_like(x)
            else:
                self.yerr=yerr
            if y is None:
                self.y=np.zeros_like(x)
            else:
                self.y=y
            self.imin=0
            self.imax=len(self.x)

    def evaluate(self):
        self.func.__fit__=False
        if type(self.x) == dict:
            self.func.x = {}
            for key in self.x.keys():
                self.func.x[key] = self.x[key][self.imin[key]:self.imax[key] + 1]
        else:
            self.func.x = self.x[self.imin:self.imax + 1]
        self.yfit = self.func.y()
        return self.yfit
        
    def evaluate4fit(self):
        self.func.__fit__=True
        if type(self.x)==dict:
            self.func.x={}
            for key in self.x.keys():
                self.func.x[key]=self.x[key][self.imin[key]:self.imax[key]+1]
        else:
            self.func.x = self.x[self.imin:self.imax + 1]
        self.yfit=self.func.y()
        return self.yfit
    
    def residual(self,params,fit_scale):
        for key in self.fit_params.keys():
            self.params[key]=params[key].value
            self.fit_params[key].value=params[key].value
        yfit=self.evaluate4fit()
        if type(yfit)==dict:
            y=[]
            for key in yfit.keys():
                data=self.y[key][self.imin[key]:self.imax[key]+ 1]
                err=self.yerr[key][self.imin[key]:self.imax[key]+1]
                fit=yfit[key]
                maxd=np.max(data)
                data=data/maxd
                err=err/maxd
                fit=fit/maxd
                dnorm = data[0]
                fnorm = fit[0]
                if fit_scale=='Log':
                    y.append((np.log10(data)-np.log10(fit))*data/err)
                elif fit_scale=='Log w/o error':
                    y.append(np.log10(data) - np.log10(fit))
                elif fit_scale=='Linear w/o error':
                    y.append(data - fit)
                else:
                    y.append((data-fit)/err)
            y=np.concatenate(y)
            return y
        else:
            data=self.y[self.imin:self.imax+1]
            err=self.yerr[self.imin:self.imax+1]
            fit = yfit
            if fit_scale=='Log':
                return (np.log10(data)-np.log10(fit))*data/err
            elif fit_scale=='Log w/o error':
                return (np.log10(data)-np.log10(fit))
            elif fit_scale=='Linear w/o error':
                return (data-fit)
            else:
                return (data-fit)/err
        
    def callback(self,params,iterations,residual,fit_scale):
        """
        """
        #self.Niter += 1
        #print(self.Niter, ': I m here')
        self.functionCalled.emit(params,iterations,residual,fit_scale)
        if self.fit_abort:
            return True
        else:
            return None
    
    
    def perform_fit(self,xmin,xmax,fit_scale='Linear',fit_method='leastsq',maxiter=1):
        self.Niter=0
        #self.sync_param()
        self.fit_abort=False
        if type(self.x)==dict:
            self.imin = {}
            self.imax = {}
            for key in self.x.keys():
                self.imin[key],self.imax[key]=np.where(self.x[key]>=xmin)[0][0],np.where(self.x[key]<=xmax)[0][-1]
        else:
            self.imin, self.imax = np.where(self.x >= xmin)[0][0], np.where(self.x <= xmax)[0][-1]
        if fit_method=='leastsq':
            self.fitter=Minimizer(self.residual,self.fit_params,fcn_args=(fit_scale,),iter_cb=self.callback,nan_policy='omit',maxfev=maxiter)
        elif fit_method=='differential_evolution':
            self.fitter=Minimizer(self.residual,self.fit_params,fcn_args=(fit_scale,),iter_cb=self.callback,
                                  nan_policy='omit', calc_covar=True, maxiter=maxiter, popsize=300, updating='immediate')
        elif fit_method=='brute':
            self.fitter=Minimizer(self.residual,self.fit_params,fcn_args=(fit_scale,),iter_cb=self.callback,nan_policy='omit')
        elif fit_method=='emcee':
            self.fitter=Minimizer(self.residual,self.fit_params,fcn_args=(fit_scale,), iter_cb=self.callback, nan_policy='omit', burn=300, steps=1000, thin=20, is_weighted=True)
        else:
            self.fitter = Minimizer(self.residual, self.fit_params, fcn_args=(fit_scale,), iter_cb=self.callback,
                                    nan_policy='omit')
        self.result=self.fitter.minimize(method=fit_method)
        return fit_report(self.result),self.result.message



        
        
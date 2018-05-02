import numpy as np
from scipy.interpolate import interp1d
from numpy.linalg import inv

def calc_pr(q,Iq):
    """
    Calculates Moore's autocorrelation function
    """
    dq=np.mean(np.diff(q))
    rmax=2*np.pi/q[0]
    rmin=2*np.pi/q[-1]
    pr=[]
    for r in np.arange(0,rmax,1.0):
        pr.append([r,r*np.sum(q*Iq*np.sin(q*r))*dq/2/np.pi**2])
    return array(pr)

def Bint(n,s,d):
    """
    Calculates sine integrals
    """
    return np.pi*n*d*(-1)**(n+1)*np.sin(2*np.pi*d*s)/((np.pi*n)**2-(2*np.pi*d*s)**2)

def calc_prm(q1,Iq1,dIq1=None,Nr=101,dmax=100.0):
    """
    Calculates autocorrelation by Moore's method (J Appl. Cryst. 13, 168 (1980))
    """
    f1=interp1d(q1,Iq1)
    f2=interp1d(q1,dIq1)
    q=np.linspace(q1[0],q1[-1],len(q1))
    Iq=f1(q)
    dIq=f2(q)
    s=q/2.0/np.pi
    U=s*Iq
    nmin=int(2*s[0]*dmax)+1
    nmax=int(2*s[-1]*dmax)+1
    if dIq is None:
        dIq=np.ones_like(Iq)
    #Calculation of Matrix of product of sine Integrals
    Cmat=np.array([[np.sum(Bint(n,s,dmax)*Bint(m,s,dmax)/s**2/dIq**2) for n in range(nmin,nmax+1)] 
                   for m in range(nmin,nmax+1)])
    ymat=np.array([np.sum(Bint(n,s,dmax)*U/s**2/dIq**2) for n in range(nmin,nmax+1)])
    InvCmat=inv(Cmat)
    a=np.dot(ymat,InvCmat)/4.0
    r=np.linspace(0.001,dmax,Nr)
    pr=8*np.pi*r*np.array([np.sum(a*np.sin(np.pi*ri*np.array(range(nmin,nmax+1))/dmax)) for ri in r])
    N,M=np.meshgrid(np.arange(1,InvCmat.shape[0]+1),np.arange(1,InvCmat.shape[0]+1))
    dpr=2*np.pi*r*np.sqrt(np.array([np.sum(np.sin(np.pi*N*ri/dmax)*np.sin(np.pi*M*ri/dmax)*InvCmat) for ri in r]))
    Iqc=4*np.array([np.sum(a*Bint(np.array(range(nmin,nmax+1)),s1,dmax)) for s1 in s])/s
    #chi=np.sum((Iq-Iqc)**2/dIq**2)
    #chi_r=chi/(len(q)-len(a))
    return r,pr,dpr,q,Iqc

def find_minmax(fun,pos=1.0,wid=1.0,accuracy=1e-3):
    """
    Find the minimum and maximum values of x for which a peak like function 'fun(x,pos,wid)' has a relatve value compare to the peak value more than the 'accuracy'.
    fun           : Peak like function class 
    pos           : Peak position
    wid           : width of the peak
    """
    xmin=1e-10
    xmax=pos+5*wid
    N=int(1.0/accuracy)
    fun.x=np.linspace(xmin,xmax,N)
    fun.pos=pos
    fun.wid=wid
    fval=fun.y()
    frange=np.where(fval/np.max(fval)>accuracy)[0]
    while len(frange)>1 and np.abs(fun.x[frange[len(frange)-1]]-fun.x[-1])<1e-6:
        xmax=xmax*3
        fun.x=np.linspace(xmin,xmax,N*3)        
        fval=fun.y()
        frange=np.where(fval/np.max(fval)>accuracy)[0]
    return fun.x[frange[0]],fun.x[frange[-1]]

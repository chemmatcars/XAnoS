import numpy as np
import copy
from calc_cf import calc_cf
import os
import time
from scipy.interpolate import interp1d
import sys
import shutil
from calc_cf import calc_cf


def read1DSAXS(fname,data={},key=None,data_sort=True):
    """
    Reads 1D SAXS data from a data file 'fname' and append a dictonary to a master dictionary 'data' with a key name as 'fname' if the 'key' is None. The following keys will be added in the new dictinary as data columns:
        'x':Q-values
        'y':Intensity values
        'yerr':Intensity error values
    Other than above the dictionary will also include all the metadeta of the data file
    """
    if key is None:
        key=fname
    data[key]={}
    fh=open(fname,'r')
    lines=fh.readlines()
    for line in lines:
        if line[0]=='#' and '=' in line:
            header,val=line[1:].strip().split('=')[:2]
            try:
                data[key][header]=float(val.strip())
            except:
                data[key][header]=val.strip()
    dataval=np.loadtxt(fname,comments='#')
    data[key]['x']=[]
    data[key]['y']=[]
    data[key]['yerr']=[]
    for i in range(dataval.shape[0]):
        if dataval[i,1]>1e-20:
            data[key]['x'].append(dataval[i,0])
            data[key]['y'].append(dataval[i,1])
            try:
                data[key]['yerr'].append(dataval[i,2])
            except:
                data[key]['yerr'].append(np.ones_like(dataval[i,1]))
    data[key]['x']=np.array(data[key]['x'])
    data[key]['y']=np.array(data[key]['y'])
    data[key]['yraw']=copy.copy(data[key]['y'])
    data[key]['yerr']=np.array(data[key]['yerr'])
    #Sorting the data w.r.t x
    if data_sort:
        data[key]['y']=data[key]['y'][data[key]['x'].argsort()]
        data[key]['yerr']=data[key]['yerr'][data[key]['x'].argsort()]
        data[key]['yraw']=data[key]['yraw'][data[key]['x'].argsort()]
        data[key]['x']=data[key]['x'][data[key]['x'].argsort()]
    if 'Energy' not in data[key].keys():
        data[key]['Energy']=12.0
    if 'CF' not in data[key].keys():
        data[key]['CF']=1.0
    if 'qOff' not in data[key].keys():
        data[key]['qOff']=0.0
    if 'Thickness' not in data[key].keys():
        data[key]['Thickness']=1.0
    if 'xrf_bkg' not in data[key].keys():
        data[key]['xrf_bkg']=0.0
    return data

def reduce1DSAXS(fname=None,sam_nums=None,gc_num=None,air_num=None,sol_num=None,mt_num=None,Ntimes=1,xmin=0.0,xmax=1.0,Npt=1000,interpolation_type='linear', sample_thickness=0.148,bkg_fac=1.0):
    """
    Reduce a set of SAXS data with background subtraction and normalizing the data for absolute 
    scale using Glassy carbon
    
    fname             : Filename initials other than the numbers. for instance for 'sample01_0001.edf' the filename would be 'sample01' where '0001' acts as the text corresponding to image number 1.
    sam_nums          : a list of image numbers considered to be samples
    gc_num            : First image number corresponding to the image collected from Glassy Carbon
    air_num           : First image number corresponding to the image collected from Air
    sol_num           : First image number corresponding to the image collected from solvent (water in most of the cases)
    mt_num            : First image number corresponding to the image collected from Emtpy capillary
    Ntime             : First image number corresponding to how many times the measurements were repeated
    xmin, xmax        : Minimum, Maximum Q-values for getting CF by comparing experimental Glassy Carbon data from standard NIST data
    Npt               : Number of  points in which the data will be interpolated
    interpolation_type: Choose between 'linear' (default), 'quadratic' and 'cubic'
    sample_thickness  : Thickness of the samples in cm.'
    bkg_fac           : Background multiplication factor just to scale the background if needed. Default value is 1.0 for automatic scaling. 0.0 or no background subtraction
    """
    if fname is None: 
        return 'Please provide a filename'
    if sam_nums is None:
        return 'Please provide a list of image numbers of all the samples to be reduced'
    if gc_num is None:
        return 'Please provide the first image number corresponding to the glassy carbon'
    if air_num is None:
        return 'Please provide the first image number corresponding to Air background'
    if sol_num is None:
        return 'Please provide the first image number corresponding to solvent(water) background'
    if mt_num is None:
        return 'Please provide the first image number corresponding to emtpy capillary tube'
    Nfile=len(sam_nums)+4
    fulldata={}
    
    for times in range(Ntimes):
        fincr=Nfile*times
        gc_fname=fname+'_%04d.txt'%(gc_num+fincr)
        air_fname=fname+'_%04d.txt'%(air_num+fincr)
        sol_fname=fname+'_%04d.txt'%(sol_num+fincr)
        mt_fname=fname+'_%04d.txt'%(mt_num+fincr)
        data=read1DSAXS(gc_fname,data={})
        data=read1DSAXS(air_fname,data=data)
        
        #Interpolating the GC and air data
        data=interpolate_data(data,Npt=Npt,kind=interpolation_type)
        data[gc_fname]['x']=copy.copy(data[gc_fname]['xintp'])
        #Subtracting the air bkg from glassy carbon
        data[gc_fname]['y']=data[gc_fname]['yintp']-bkg_fac*data[air_fname]['yintp']
        data[gc_fname]['yerr']=np.sqrt(data[gc_fname]['yintperr']**2+bkg_fac**2*data[air_fname]['yintperr']**2)
        fdir=write1DSAXS(data)
        pfname=os.path.basename(gc_fname).split('.')[0]+'_bkg_sub_norm.txt'
        cfname=os.path.join(fdir,pfname)
        en,cf,x,y=calc_cf(cfname,xmin=xmin,xmax=xmax)
        print(cf)
        data=read1DSAXS(sol_fname,data=data)
        data=read1DSAXS(mt_fname,data=data)
        for num in sam_nums:
            tfname=fname+'_%04d.txt'%(num+fincr)
            data=read1DSAXS(tfname,data=data)
        #Interpolating all the data set again
        data=interpolate_data(data,Npt=Npt,kind=interpolation_type)
        #Normalizing all the data from onwards
        data[gc_fname]['x']=copy.copy(data[gc_fname]['xintp'])
        data[gc_fname]['y']=cf*data[gc_fname]['yintp']/0.1055
        data[gc_fname]['yerr']=cf*data[gc_fname]['yintperr']/0.1055
        for num in sam_nums:
            tfname=fname+'_%04d.txt'%(num+fincr)
            #Subtracting the solvent background
            data[tfname]['x']=copy.copy(data[tfname]['xintp'])
            data[tfname]['y']=cf*(data[tfname]['yintp']-bkg_fac*data[sol_fname]['yintp'])/sample_thickness
            data[tfname]['yerr']=cf*np.sqrt(data[tfname]['yintperr']**2+bkg_fac**2*data[sol_fname]['yintperr']**2)/sample_thickness
            
        data[sol_fname]['x']=copy.copy(data[sol_fname]['xintp'])
        data[sol_fname]['y']=cf*(data[sol_fname]['yintp']-bkg_fac*data[mt_fname]['yintp'])/sample_thickness
        data[sol_fname]['yerr']=cf*np.sqrt(data[sol_fname]['yintperr']**2+bkg_fac**2*data[mt_fname]['yintperr']**2)/sample_thickness
        data[mt_fname]['x']=copy.copy(data[mt_fname]['xintp'])
        data[mt_fname]['y']=cf*(data[mt_fname]['yintp']-bkg_fac*data[air_fname]['yintp'])/0.002 #Capillary thickness is 20 microns
        data[mt_fname]['yerr']=cf*np.sqrt(data[mt_fname]['yintperr']**2+bkg_fac**2*data[air_fname]['yintperr']**2)/0.002
        write1DSAXS(data)
        fulldata.update(data)
        
    #Performing means of all the data
    fulldata=interpolate_data(fulldata,Npt=Npt,kind=interpolation_type)
    gc_mean={}
    air_mean={}
    sol_mean={}
    mt_mean={}
    sam_mean={}
    for num in sam_nums:
        sam_mean[num]={}
    #Calculating the mean of all the signals
    for times in range(Ntimes):
        fincr=Nfile*times
        gc_fname=fname+'_%04d.txt'%(gc_num+fincr)
        air_fname=fname+'_%04d.txt'%(air_num+fincr)
        sol_fname=fname+'_%04d.txt'%(sol_num+fincr)
        mt_fname=fname+'_%04d.txt'%(mt_num+fincr)
        try:
            gc_mean['y']=gc_mean['y']+fulldata[gc_fname]['yintp']
        except:
            gc_mean['y']=fulldata[gc_fname]['yintp']
        try:
            air_mean['y']=air_mean['y']+fulldata[air_fname]['yintp']
        except:
            air_mean['y']=fulldata[air_fname]['yintp']
        try:
            sol_mean['y']=sol_mean['y']+fulldata[sol_fname]['yintp']
        except:
            sol_mean['y']=fulldata[sol_fname]['yintp']
        try:
            mt_mean['y']=mt_mean['y']+fulldata[mt_fname]['yintp']
        except:
            mt_mean['y']=fulldata[mt_fname]['yintp']
            
        for num in sam_nums:
            tfname=fname+'_%04d.txt'%(num+fincr)
            sam_mean[num]['x']=fulldata[tfname]['xintp']
            try:
                sam_mean[num]['y']=sam_mean[num]['y']+fulldata[tfname]['yintp']
            except:
                sam_mean[num]['y']=fulldata[tfname]['yintp']
    gc_mean['y']=gc_mean['y']/Ntimes
    air_mean['y']=air_mean['y']/Ntimes
    sol_mean['y']=sol_mean['y']/Ntimes
    mt_mean['y']=mt_mean['y']/Ntimes
    for num in sam_nums:
        sam_mean[num]['y']=sam_mean[num]['y']/Ntimes   
    
    #Calculating the errorbars
    for times in range(Ntimes):
        fincr=Nfile*times
        gc_fname=fname+'_%04d.txt'%(gc_num+fincr)
        air_fname=fname+'_%04d.txt'%(air_num+fincr)
        sol_fname=fname+'_%04d.txt'%(sol_num+fincr)
        mt_fname=fname+'_%04d.txt'%(mt_num+fincr)
        try:
            gc_mean['yerr']=gc_mean['yerr']+(gc_mean['y']-fulldata[gc_fname]['yintp'])**2
        except:
            gc_mean['yerr']=(gc_mean['y']-fulldata[gc_fname]['yintp'])**2
        try:
            air_mean['yerr']=air_mean['yerr']+(air_mean['y']-fulldata[air_fname]['yintp'])**2
        except:
            air_mean['yerr']=(air_mean['y']-fulldata[air_fname]['yintp'])**2
        try:
            sol_mean['yerr']=sol_mean['yerr']+(sol_mean['y']-fulldata[sol_fname]['yintp'])**2
        except:
            sol_mean['yerr']=(sol_mean['y']-fulldata[sol_fname]['yintp'])**2
        try:
            mt_mean['yerr']=mt_mean['yerr']+(mt_mean['y']-fulldata[mt_fname]['yintp'])**2
        except:
            mt_mean['yerr']=(mt_mean['y']-fulldata[mt_fname]['yintp'])**2
            
        for num in sam_nums:
            tfname=fname+'_%04d.txt'%(num+fincr)
            try:
                sam_mean[num]['yerr']=sam_mean[num]['yerr']+(sam_mean[num]['y']-fulldata[tfname]['yintp'])**2
            except:
                sam_mean[num]['yerr']=(sam_mean[num]['y']-fulldata[tfname]['yintp'])**2
    gc_mean['yerr']=np.sqrt(gc_mean['yerr']/Ntimes)
    air_mean['yerr']=np.sqrt(air_mean['yerr']/Ntimes)
    sol_mean['yerr']=np.sqrt(sol_mean['yerr']/Ntimes)
    mt_mean['yerr']=np.sqrt(mt_mean['yerr']/Ntimes)
    for num in sam_nums:
        sam_mean[num]['yerr']=np.sqrt(sam_mean[num]['yerr']/Ntimes)
    
    gc_mean['x']=fulldata[gc_fname]['xintp']
    air_mean['x']=fulldata[air_fname]['xintp']
    mt_mean['x']=fulldata[mt_fname]['xintp']
    sol_mean['x']=fulldata[sol_fname]['xintp']
    meandir=os.path.join(fdir,'Mean')
    if not os.path.exists(meandir):
        os.makedirs(meandir)
    np.savetxt(os.path.join(meandir,'gc_mean.txt'),np.vstack((gc_mean['x'],gc_mean['y'],gc_mean['yerr'])).T,comments='#',header='Energy=%.3f'%fulldata[gc_fname]['Energy'])
    np.savetxt(os.path.join(meandir,'air_mean.txt'),np.vstack((air_mean['x'],air_mean['y'],air_mean['yerr'])).T,comments='#',header='Energy=%.3f'%fulldata[gc_fname]['Energy'])
    np.savetxt(os.path.join(meandir,'mt_mean.txt'),np.vstack((mt_mean['x'],mt_mean['y'],mt_mean['yerr'])).T,comments='#',header='Energy=%.3f'%fulldata[gc_fname]['Energy'])
    np.savetxt(os.path.join(meandir,'sol_mean.txt'),np.vstack((sol_mean['x'],sol_mean['y'],sol_mean['yerr'])).T,comments='#',header='Energy=%.3f'%fulldata[gc_fname]['Energy'])
    for num in sam_nums:
        np.savetxt(os.path.join(meandir,'sam%04d_mean.txt'%num),np.vstack((sam_mean[num]['x'],sam_mean[num]['y'],sam_mean[num]['yerr'])).T,comments='#',header='Energy=%.3f'%fulldata[gc_fname]['Energy'])
        

def average1DSAXS(fname,num=None,ofname=None,delete_prev=False):
    """
    Averages over the 1D-SAXS patterns recorded in files with the names in the format like 'fname_0001.txt' where the last four numbers of the filename with path will be given as a list of numbers in 'num'.
    delete_prev=True will delete the directory containing output files if it exists
    """
    if num is not None:
        data={}
        fnames=[]
        for i in num:
            fnames.append(fname+'_%04d.txt'%i)
            data=read1DSAXS(fnames[-1],data=data)
        interpolate_data(data,Npt=len(data[fnames[0]]['x']),kind='linear')
        sumdata=[]
        monitor=0.0
        pDiode=0.0
        diode=0.0
        pDiodeCorr=0.0
        monitorCorr=0.0
        for fnam in fnames:
            sumdata.append(data[fnam]['yintp'])
            try:
                monitor=monitor+data[fnam]['Monitor']
                pDiode=pDiode+data[fnam]['BSDiode']
                diode=diode+data[fnam]['Diode']
                pDiodeCorr=pDiodeCorr+data[fnam]['BSDiode_corr']
                monitorCorr=monitorCorr+data[fnam]['Monitor_corr']
            except:
                monitor=1.0
                pDiode=1.0
                diode=1.0
                pDiodeCorr=1.0
                monitorCorr=1.0
        tlen=len(num)
        monitor=monitor/tlen
        pDiode=pDiode/tlen
        diode=diode/tlen
        pDiodeCorr=pDiodeCorr/tlen
        monitorCorr=monitorCorr/tlen
        sumdata=np.array(sumdata)
        meandata=np.mean(sumdata,axis=0)
        errordata=np.std(sumdata,axis=0)
        finaldata=np.vstack((data[fnames[0]]['xintp'],meandata,errordata)).T
        
        fdir=os.path.dirname(fnames[0])
        if os.path.exists(os.path.join(fdir,'Mean')) and delete_prev:
            shutil.rmtree(os.path.join(fdir,'Mean'))
        if not os.path.exists(os.path.join(fdir,'Mean')):
            os.makedirs(os.path.join(fdir,'Mean'))
        if ofname is None:
            ofname=os.path.join(fdir,'Mean',os.path.basename(fname)+'_mean.txt')
        else:
            ofname=os.path.join(fdir,'Mean',ofname)
            
        data[ofname]=copy.copy(data[fnames[0]])
        data[ofname]['x']=data[fnames[0]]['xintp']
        data[ofname]['y']=meandata
        data[ofname]['yerr']=errordata
        data[ofname]['Monitor']=monitor
        data[ofname]['Monitor_corr']=monitorCorr
        data[ofname]['BSDiode']=pDiode
        data[ofname]['BSDiode_corr']=pDiodeCorr
        header='Processed data obtained by taking Mean over the following files:\n'
        for fnam in fnames:
            header=header+fnam+'\n'
        for key in data[ofname].keys():
            if key!='x' and key!='y' and key!='yerr' and key!='xintp' and key!='yintp' and key!='yintperr':
                header=header+key+'='+str(data[ofname][key])+'\n'
        np.savetxt(ofname,finaldata,header=header,comments='#')
        print('Averaged data save in a file named %s'%ofname)
        return data,ofname
    
def bkgSub1DSAXS(sdata,sname,bdata,bname,ofname,cf=1.0,thickness=1.0,folder='Bkg_sub',norm=1.0):
    """
    Subtracting the Background data 'bdata' from the signal data 'sdata' where 'sname' and 'bname' are keys for the specific data to be subtracted
    'ofname' is the output file name
    """
    fdir=os.path.dirname(sname)
    data={}
    data[sname]=sdata[sname]
    data[bname]=bdata[bname]
    ofdir=os.path.join(fdir,folder)
    if not os.path.exists(ofdir):
        os.makedirs(ofdir)
    ofname=os.path.join(ofdir,ofname)
    interpolate_data(data,Npt=len(data[sname]['x']))
    data[ofname]=copy.copy(data[sname])
    data[ofname]['y']=data[sname]['yintp']-data[bname]['yintp']
    data[ofname]['yerr']=np.sqrt(data[sname]['yintperr']**2+data[bname]['yintperr']**2)
    data[ofname]['CF']=cf
    data[ofname]['Thickness']=thickness
    finaldata=np.vstack((data[ofname]['x'],norm*data[ofname]['y'],norm*data[ofname]['yerr'])).T
    header='Bkg subtracted data obtained from the following files:\n'
    header=header+'Signal file: '+sname+'\n'
    header=header+'Bkg file: '+bname+'\n'
    for key in data[ofname].keys():
        if key!='x' and key!='y' and key!='yerr' and key!='xintp' and key!='yintp' and key!='yintperr':
            header=header+key+'='+str(data[ofname][key])+'\n'
    np.savetxt(ofname,finaldata,header=header,comments='#')
    print('Subtracted filname data save in a file named %s'%ofname)
    return ofname
        
        
def interpolate_data(data,Npt=1000,kind='linear'):
    """
    Interpolates all the data with the common q values
    Npt     : No. of common q-values on which interpolated values will be calculated
    kind    :'linear','cubic'...please check the documentation of scipy.interpolate.interp1d for more options
    """
    qmin=0.0
    qmax=1e15
    
    #For getting the appropriate qmin and qmax of the interpolated data
    #for item in self.dataListWidget.selectedItems():
    for fname in data.keys():
        #dataname, fname=item.text().split(': ')
        tmin=np.min(data[fname]['x'])
        tmax=np.max(data[fname]['x'])
        if tmin>qmin:
            qmin=copy.copy(tmin)
        if tmax<qmax:
            qmax=copy.copy(tmax)
    qintp=np.linspace(qmin,qmax,Npt)                
    for fname in data.keys():
        data[fname]['xintp']=qintp
        fun=interp1d(data[fname]['x'],data[fname]['y'],kind=kind)
        funerr=interp1d(data[fname]['x'],data[fname]['yerr'],kind=kind)
        data[fname]['yintp']=fun(qintp)
        data[fname]['yintperr']=funerr(qintp)        
    return data
        
def write1DSAXS(data):
    """
    Writes the data dictionary in the filename provided with full path by 'fname'
    """
    fname=list(data.keys())[0]
    fdir=os.path.join(os.path.dirname(fname),'Bkg_sub_and_Norm')
    if not os.path.exists(fdir):
        os.makedirs(fdir)
    for fname in data.keys():
        pfname=os.path.join(fdir,os.path.basename(fname).split('.')[0]+'_bkg_sub_norm.txt')
        header='Processed data on %s\n'%time.asctime()
        #header='Original file=%s\n'%fname
        for key in data[fname].keys():
            if key!='x' and key!='y' and key!='yerr' and key!='xintp' and key!='yintp' and key!='yintperr' and key!='y-flb':
                header=header+'%s=%s\n'%(key,data[fname][key])
        header=header+'Q (A^-1)\tIntensity\tIntensity_error\n'
        np.savetxt(pfname,np.vstack((data[fname]['x'],data[fname]['y'],data[fname]['yerr'])).T,comments='#',header=header)
    return fdir
            
        
        
if __name__=='__main__':
#    fname='Np_11_85keV'
#    pfname='/home/epics/CARS5/Data/chemmat/Data/saxs/2017-08/Mar_CCD/'+fname+'/mar_ccd/extracted_diode_normalized/'+fname
#    offset=60
#    sam_nums=[offset+3,offset+4]#,offset+5,offset+6]
#    gc_num=offset+1
#    sol_num=offset+2
#    mt_num=offset+5
#    air_num=offset+6
#    reduce1DSAXS(pfname,sam_nums=sam_nums,gc_num=gc_num,sol_num=sol_num,mt_num=mt_num,air_num=air_num,Ntimes=10,xmin=0.08,xmax=0.12,bkg_fac=1.0)
    try:
        fname=sys.argv[1]
    except:
        print('Please provide the basefile name without numbers at the end.')
#    try:
#        start=int(sys.argv[2])
#    except:
#        print('Please provide starting file number.')
#    try:
#        end=int(sys.argv[3])
#    except:
#        print('Please provide starting file number.')
#    try:
#        ofname=sys.argv[4]
#    except:
#        ofname=None
#    num=range(start,end+1)
    try:
        start=int(sys.argv[2])
    except:
        start=0
    num=np.arange(1,31)+start
    gcdata,gcname=average1DSAXS(fname,num=num,ofname='GC_mean.txt',delete_prev=False)
    num=np.arange(31,61)+start
    watdata,watname=average1DSAXS(fname,num=num,ofname='Water_mean.txt')
    num=np.arange(61,91)+start
    SiOSr1data,SiOSr1name=average1DSAXS(fname,num=num,ofname='AuSiOc_mean.txt')
    num=np.arange(91,121)+start
    SiOSr2data,SiOSr2name=average1DSAXS(fname,num=num,ofname='AuNp_mean.txt')
    num=np.arange(121,151)+start
    Srdata,Srname=average1DSAXS(fname,num=num,ofname='AuSiOd_mean.txt')
    num=np.arange(151,181)+start
    MTdata,MTname=average1DSAXS(fname,num=num,ofname='MT_mean.txt')
    num=np.arange(181,211)+start
    Airdata,Airname=average1DSAXS(fname,num=num,ofname='Air_mean.txt')
    
    print('Performing background subtraction for GC')
    folder='Bkg_sub_wCF'
    thickness=0.1055
    norm=Airdata[Airname]['BSDiode_corr']/Airdata[Airname]['Monitor_corr']
    fname=bkgSub1DSAXS(gcdata,gcname,Airdata,Airname,'G11C_norm.txt',folder='Bkg_sub',norm=norm)
    energy,cf,qoff,x,istdf=calc_cf(fname,standard='GC',xmin=0.01,xmax=0.03,thickness=thickness)
    #cf=1.0
    fname=bkgSub1DSAXS(gcdata,gcname,Airdata,Airname,'GC_norm.txt',cf=cf,thickness=thickness,folder=folder,norm=norm)
    thickness=0.148
    print('Performing background subtraction for Water')
    bkgSub1DSAXS(watdata,watname,MTdata,MTname,'Water_norm.txt',cf=cf,thickness=thickness,folder=folder,norm=norm)
    #thickness=0.14
    print('Performing background subtraction for AuSiOc')
    bkgSub1DSAXS(SiOSr1data,SiOSr1name,watdata,watname,'AuSiOc_norm.txt',cf=cf,thickness=thickness,folder=folder,norm=norm)
    #thickness=0.143
    print('Performing background subtraction for AuNp')
    bkgSub1DSAXS(SiOSr2data,SiOSr2name,watdata,watname,'AuNp_norm.txt',cf=cf,thickness=thickness,folder=folder,norm=norm)
    #thickness=0.169
    print('Performing background subtraction for AuSiOd')
    bkgSub1DSAXS(Srdata,Srname,watdata,watname,'AuSiOd_norm.txt',cf=cf,thickness=thickness,folder=folder,norm=norm)
    #thickness=0.158
    print('Performing background subtraction for MT')
    bkgSub1DSAXS(MTdata,MTname,Airdata,Airname,'MT_norm.txt',cf=cf,thickness=thickness,folder=folder,norm=norm)
    
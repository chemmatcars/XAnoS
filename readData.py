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
    Reduce a set of SAXS data (kept in a same folder with a same name for data, backgrounds and standard sample) with background subtraction and normalizing the data for absolute 
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
        
def reduce1DSAXS2(fname=None,ftimes=1,gc_name=None,gc_times=1,air_name=None,air_times=1,sol_name=None,sol_times=1,mt_name=None,mt_times=1,xmin=0.0,xmax=1.0,Npt=1000,interpolation_type='linear',sample_thickness=0.148,bkg_fac=1.0,data={}):
    """
    Reduce a set of SAXS data (with data, backgrounds and standard samples kept in different folders) with background subtraction and normalizing the data for absolute 
    scale using Glassy carbon
    
    fname             : Filename initials other than the numbers. for instance for 'sample01_0001.edf' the filename would be 'sample01' where '0001' acts as the text corresponding to image number 1.
    ftimes            : Number of times the measurement repeated
    gc_name           : Filename initials other than the numbers for glassy carbon data
    gc_times          : Number of times the glassy carbon data were measured
    air_name          : Filename initials other than the numbers of air-data
    air_times         : Number of times the air data were measured
    sol_name          : Filename initials other than the numbers of solvent or background data
    sol_times         : Number of times the air data were measured
    mt_name           : Filename initials other than the numbers of empty capillary data
    mt_times          : Number of times the empty capillary data were measured
    xmin, xmax        : Minimum, Maximum Q-values for getting CF by comparing experimental Glassy Carbon data from standard NIST data
    Npt               : Number of  points in which the data will be interpolated
    interpolation_type: Choose between 'linear' (default), 'quadratic' and 'cubic'
    sample_thickness  : Thickness of the samples in cm.'
    bkg_fac           : Background multiplication factor just to scale the background if needed. Default value is 1.0 for automatic scaling. 0.0 or no background subtraction
    """
    if fname is None: 
        return 'File error:: Please provide a filename'
    if gc_name is None:
        return 'File error:: Please provide glassy carbon filename'
    if sol_name is None:
        return 'File error:: Please provide solvent/bacground filename'
    #if air_name is None:
    #    return 'Please provide Air filename'
    #if mt_name is None:
    #    return 'Please provide empty capillary filename'
    #Calculating average for all the files:
    file_exists=True
    num=1
    ofnames=[]
    while file_exists:
        try:
            fnum=range((num-1)*ftimes+1,num*ftimes+1)
            data,ofname=average1DSAXS(fname,num=fnum,ofname=fname+'_%04d_proc.txt'%((num-1)*ftimes+1),data=data)
            ofnames.append(ofname)
        except:
            del data[fname+'_%04d.txt'%((num-1)*ftimes+1)]
            print(fname+'_%04d.txt'%((num-1)*ftimes+1)+ ' doesnot exist')
            file_exists=False
        num+=1
    file_exists=True        
    num=1
    ogcnames=[]
    while file_exists:
        try:
            fnum=range((num-1)*gc_times+1,num*gc_times+1)
            data,ofname=average1DSAXS(gc_name,num=fnum,ofname=gc_name+'_%04d_proc.txt'%((num-1)*gc_times+1),data=data)
            ogcnames.append(ofname)
        except:
            del data[gc_name+'_%04d.txt'%((num-1)*gc_times+1)]
            print(gc_name+'_%04d.txt'%((num-1)*gc_times+1)+' doesnot exist')
            file_exists=False
        num+=1

    if len(ofnames)!=len(ogcnames):
        print("File number error: Number of data files not same as number of glassy carbon files")
        return 
    
    file_exists=True        
    num=1
    osolnames=[]
 
    while file_exists:
        try:
            fnum=range((num-1)*sol_times+1,num*sol_times+1)
            data,ofname=average1DSAXS(sol_name,num=fnum,ofname=sol_name+'_%04d_proc.txt'%((num-1)*sol_times+1),data=data)
            osolnames.append(ofname)
        except:
            del data[sol_name+'_%04d.txt'%((num-1)*sol_times+1)]
            print(sol_name+'_%04d.txt'%((num-1)*sol_times+1)+' doesnot exist')
            file_exists=False
        num+=1
        
    if len(ofnames)!=len(osolnames):
        print("File number error: Number of data files not same as number of solvent/background files")
        return 
           
    if air_name is not None:
        file_exists=True        
        num=1
        oairnames=[]
        while file_exists:
            try:
                fnum=range((num-1)*air_times+1,num*air_times+1)
                data,ofname=average1DSAXS(air_name,num=fnum,ofname=air_name+'_%04d_proc.txt'%((num-1)*air_times+1),data=data)
                oairnames.append(ofname)
            except:
                del data[air_name+'_%04d.txt'%((num-1)*air_times+1)]
                print(air_name+'_%04d.txt'%((num-1)*air_times+1)+' doesnot exist')
                file_exists=False
            num+=1
        if len(ofnames)!=len(oairnames):
            print("File number error: Number of data files not same as number of air background files")
            return 
    if mt_name is not None:
        file_exists=True        
        num=1
        omtnames=[]
        while file_exists:
            try:
                fnum=range((num-1)*mt_times+1,num*mt_times+1)
                data,ofname=average1DSAXS(mt_name,num=fnum,ofname=mt_name+'_%04d_proc.txt'%((num-1)*mt_times+1),data=data)
                omtnames.append(ofname)
            except:
                del data[mt_name+'_%04d.txt'%((num-1)*mt_times+1)]
                print(mt_name+'_%04d.txt'%((num-1)*mt_times+1)+' doesnot exist')
                file_exists=False
            num+=1
        if len(ofnames)!=len(ogcnames):
            print("File number error: Number of data files not same as number of empty capillary files")
            return 

    print("First stage completed: All files read successfully...")    
    #performing interpolation of all the data sets
    data=interpolate_data(data,Npt=Npt,kind=interpolation_type)
    print("2nd stage completed: All data interpolated...")    
    
    #Performing background subtractions of the averaged data
    for num in range(len(ofnames)):
        print("Performing backgroud subtraction and normalization: %d, and %d more to do..."%(num,len(ofnames)-num))
        data[ogcnames[num]]['x']=copy.copy(data[ogcnames[num]]['xintp'])
        if air_name is not None:
            data[ogcnames[num]]['y']=data[ogcnames[num]]['yintp']-data[oairnames[num]]['yintp']
            data[ogcnames[num]]['yerr']=np.sqrt(data[ogcnames[num]]['yintperr']**2+data[oairnames[num]]['yintperr']**2)
        else:
            data[ogcnames[num]]['y']=data[ogcnames[num]]['yintp']
            data[ogcnames[num]]['yerr']=data[ogcnames[num]]['yintperr']
        
        en,cf,x,y,z=calc_cf(ogcnames[num],xmin=xmin,xmax=xmax)
        data[ogcnames[num]]['CF']=cf     
        
        data[ofnames[num]]['x']=copy.copy(data[ofnames[num]]['xintp'])
        data[ofnames[num]]['y']=(data[ofnames[num]]['yintp']-data[osolnames[num]]['yintp'])
        data[ofnames[num]]['yerr']=np.sqrt(data[ofnames[num]]['yintperr']**2+data[osolnames[num]]['yintperr']**2)
        data[ofnames[num]]['CF']=cf
        
        
        data[osolnames[num]]['x']=copy.copy(data[osolnames[num]]['xintp'])
        if mt_name is not None:
            data[osolnames[num]]['y']=(data[osolnames[num]]['yintp']-data[omtnames[num]]['yintp'])
            data[osolnames[num]]['yerr']=np.sqrt(data[osolnames[num]]['yintperr']**2+data[omtnames[num]]['yintperr']**2)
        else:
            data[osolnames[num]]['y']=data[osolnames[num]]['yintp']
            data[osolnames[num]]['yerr']=data[osolnames[num]]['yintperr']
        data[osolnames[num]]['CF']=cf
             
        
        if mt_name is not None and air_name is not None:
            data[omtnames[num]]['x']=copy.copy(data[omtnames[num]]['xintp'])
            data[omtnames[num]]['y']=data[omtnames[num]]['yintp']-data[oairnames[num]]['yintp']
            data[omtnames[num]]['yerr']=np.sqrt(data[omtnames[num]]['yintperr']**2+data[oairnames[num]]['yintperr']**2)
            data[omtnames[num]]['CF']=cf
    print('Saving all the data now,,,')    
    write1DSAXS(data)
    print('Data processing completed successfully.')
    return data
        

def average1DSAXS(fname,num=None,ofname=None,delete_prev=False,data={}):
    """
    Averages over the 1D-SAXS patterns recorded in files with the names in the format like 'fname_0001.txt' where the last four numbers of the filename with path will be given as a list of numbers in 'num'.
    delete_prev=True will delete the directory containing output files if it exists
    ofname=Output filename
    """
    if num is not None:
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
        print('Averaged data saved in a file named %s'%ofname)
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
        tmin=np.min(data[fname]['x']    )
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
    try:
        fname=sys.argv[1]
        run=True
    except:
        print('Please provide the basefile name without numbers at the end as argument 2')
        run=False
    try:
        fnum=int(sys.argv[2])
        run=run and True
    except:
        print('Please provide the number of repeated measurements of data as argument 3')
        run= False
    try:
        sol_name=sys.argv[3]
    except:
        print('Please provide the solvent/background file name without numbers at the end as argument 4')
    try:
        sol_num=int(sys.argv[4])
    except:
        print('Please provide the number of repeated measurements of solvent/background data as argument 5')
    try:
        gc_name=sys.argv[5]
    except:
        print('Please provide Glassy Carbon file name without numbers at the end as argument 6')
    try:
        gc_num=int(sys.argv[6])
    except:
        print('Please provide the number of repeated measurements of Glassy carbon as argument 7')
    reduce1DSAXS2(fname=fname,ftimes=fnum,sol_name=sol_name,sol_times=sol_num,gc_name=gc_name,gc_times=gc_num,sample_thickness=0.15,xmin=0.04,xmax=0.07)

#if __name__=='__main__':
#    fname=sys.argv[1]
#    startnums=eval(sys.argv[2])
#    repeat=eval(sys.argv[3])
#    ofname=sys.argv[4]
#    
#    num=[]
#    for snum in startnums:
#        num=num+[snum+i for i in range(repeat)]
#    print(num)
#    average1DSAXS(fname,num=num,ofname=ofname,delete_prev=False,data={})
#    
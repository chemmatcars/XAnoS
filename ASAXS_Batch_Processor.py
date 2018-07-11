from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication,QWidget,QMessageBox,QFileDialog
import sys
from readData import average1DSAXS, interpolate_data
import copy
import numpy as np
from calc_cf import calc_cf
import os
import time

class ASAXS_Batch_Processor(QWidget):
    """
    """
    def __init__(self,parent=None):
        QWidget.__init__(self,parent=None)
        loadUi('UI_Forms/ASAXS_Batch_Processor.ui',self)
        self.sampleFname=None#self.sampleFnameLineEdit.text()
        self.bkgFname=None#self.bkgFnameLineEdit.text()
        self.standardFname=None#self.standardFnameLineEdit.text()
        self.containerFname=None#self.containerFnameLineEdit.text()
        self.airFname=None#self.airFnameLineEdit.text()
        self.sampleRepeat=self.sampleRepeatSpinBox.value()
        self.bkgRepeat=self.bkgRepeatSpinBox.value()
        self.standardRepeat=self.standardRepeatSpinBox.value()
        self.containerRepeat=self.containerRepeatSpinBox.value()
        self.airRepeat=self.airRepeatSpinBox.value()
        self.sampleThickness=float(self.sampleThicknessLineEdit.text())
        self.bkgThickness=float(self.bkgThicknessLineEdit.text())
        self.standardThickness=float(self.standardThicknessLineEdit.text())
        self.containerThickness=float(self.containerThicknessLineEdit.text())
        self.standard=self.standardComboBox.currentText()
        self.QRange=[float(x) for x in self.standardNormRangeLineEdit.text().split(':')]
        self.interpType=self.interpTypeComboBox.currentText()
        self.interpNpts=int(self.interpNptsLineEdit.text())
        self.bgFactor=float(self.bgFactorLineEdit.text())
        
        self.data=None
        self.ofnames=None
        
        self.init_signals()
        
        
    def init_signals(self):
        self.sampleFnamePushButton.clicked.connect(self.sampleFnameChanged)
        self.bkgFnamePushButton.clicked.connect(self.bkgFnameChanged)
        self.standardFnamePushButton.clicked.connect(self.standardFnameChanged)
        self.containerFnamePushButton.clicked.connect(self.containerFnameChanged)
        self.airFnamePushButton.clicked.connect(self.airFnameChanged)
        
        self.sampleRepeatSpinBox.valueChanged.connect(self.sampleRepeatChanged)
        self.bkgRepeatSpinBox.valueChanged.connect(self.bkgRepeatChanged)
        self.standardRepeatSpinBox.valueChanged.connect(self.standardRepeatChanged)
        self.containerRepeatSpinBox.valueChanged.connect(self.containerRepeatChanged)
        self.airRepeatSpinBox.valueChanged.connect(self.airRepeatChanged)
        
        self.sampleThicknessLineEdit.returnPressed.connect(self.sampleThicknessChanged)
        self.bkgThicknessLineEdit.returnPressed.connect(self.bkgThicknessChanged)
        self.standardThicknessLineEdit.returnPressed.connect(self.standardThicknessChanged)
        self.containerThicknessLineEdit.returnPressed.connect(self.containerThicknessChanged)
        
        self.standardComboBox.currentIndexChanged.connect(self.standardChanged)
        self.standardNormRangeLineEdit.returnPressed.connect(self.standardNormRangeChanged)
        self.interpTypeComboBox.currentIndexChanged.connect(self.interpTypeChanged)
        self.interpNptsLineEdit.returnPressed.connect(self.interpNptsChanged)
        self.bgFactorLineEdit.returnPressed.connect(self.bgFactorChanged)
        
        self.processPushButton.clicked.connect(self.process)
        
    def sampleFnameChanged(self):
        fname,_=QFileDialog.getOpenFileName(self,'Select the starting sample file',filter='Text files (*.txt)')
        if fname!='':
            self.sampleFname=fname[:-9]
            self.sampleFnameLineEdit.setText(self.sampleFname)
        else:
            self.sampleFname=None
            self.sampleFnameLineEdit.setText('None')
        
        
    def bkgFnameChanged(self):
        fname,_=QFileDialog.getOpenFileName(self,'Select the starting background file',filter='Text files (*.txt)')
        if fname!='':
            self.bkgFname=fname[:-9]
            self.bkgFnameLineEdit.setText(self.bkgFname)
        else:
            self.bkgFname=None
            self.bkgFnameLineEdit.setText('None')
        
    def standardFnameChanged(self):
        fname,_=QFileDialog.getOpenFileName(self,'Select the starting standard file',filter='Text files (*.txt)')
        if fname!='':
            self.standardFname=fname[:-9]
            self.standardFnameLineEdit.setText(self.standardFname)
        else:
            self.standardFname=None
            self.standardFnameLineEdit.setText('None')
        
    def containerFnameChanged(self):
        fname,_=QFileDialog.getOpenFileName(self,'Select the starting container file',filter='Text files (*.txt)')
        if fname!='':
            self.containerFname=fname[:-9]
            self.containerFnameLineEdit.setText(self.containerFname)
        else:
            self.containerFname=None
            self.containerFnameLineEdit.setText('None')
        
    def airFnameChanged(self):
        fname,_=QFileDialog.getOpenFileName(self,'Select the starting air file',filter='Text files (*.txt)')
        if fname!='':
            self.airFname=fname[:-9]
            self.airFnameLineEdit.setText(self.airFname)
        else:
            self.airFname=None
            self.airFnameLineEdit.setText('None')
        
    def sampleRepeatChanged(self):
        self.sampleRepeat=self.sampleRepeatSpinBox.value()
        
    def bkgRepeatChanged(self):
        self.bkgRepeat=self.bkgRepeatSpinBox.value()
        
    def standardRepeatChanged(self):
        self.standardRepeat=self.standardRepeatSpinBox.value()
        
    def containerRepeatChanged(self):
        self.containerRepeat=self.containerRepeatSpinBox.value()
        
    def airRepeatChanged(self):
        self.airRepeat=self.airRepeatSpinBox.value()
        
    def sampleThicknessChanged(self):
        try:
            self.sampleThickness=float(self.sampleThicknessLineEdit.text())
        except:
            self.sampleThicknessLineEdit.setText(str(self.sampleThickness))
            QMessageBox.warning(self,'Value Error','Please enter numbers only',QMessageBox.Ok)
            
    def bkgThicknessChanged(self):
        try:
            self.bkgThickness=float(self.bkgThicknessLineEdit.text())
        except:
            self.bkgThicknessLineEdit.setText(str(self.bkgThickness))
            QMessageBox.warning(self,'Value Error','Please enter numbers only',QMessageBox.Ok)
            
    def standardThicknessChanged(self):
        try:
            self.standardThickness=float(self.standardThicknessLineEdit.text())
        except:
            self.standardThicknessLineEdit.setText(self.standardThickness)
            QMessageBox.warning(self,'Value Error','Please enter numbers only',QMessageBox.Ok)
            
    def containerThicknessChanged(self):
        try:
            self.containerThickness=float(self.containerThicknessLineEdit.text())
        except:
            self.containerThicknessLineEdit.setText(str(self.containerThickness))
            
    def standardChanged(self):
        self.standard=self.standardComboBox.currentText()
            
    def standardNormRangeChanged(self):
        try:
            self.QRange=[float(x) for x in self.standardNormRangeLineEdit.text().split(':')]
        except:
            self.standardNormRangeLineEdit.setText('%.2f:%.2f'%(self.QRange[0],self.QRange[1]))
            QMessageBox.warning(self,'Value Error','Please enter numbers only',QMessageBox.Ok)
            
    def interpTypeChanged(self):
        self.interpType=self.interpTypeComboBox.currentText()
        
    def interpNptsChanged(self):
        try:
            self.interpNpts=int(self.interpNptsLineEdit.text())
        except:
            self.interpNptsLineEdit.setText(str(self.interpNpts))
            QMessageBox.warning(self,'Value Error','Please enter integer values only',QMessageBox.Ok)

    def bgFactorChanged(self):
        try:
            self.bgFactor=float(self.bgFactorLineEdit.text())
        except:
            self.bgFactorLineEdit.setText(str(self.bgFactor))
            QMessageBox.warning(self,'Value Error','Please enter floating values only',QMessageBox.Ok)


    def process(self):
        self.processMessageTextEdit.clear()
        self.sampleThicknessChanged()
        self.bkgThicknessChanged()
        self.standardThicknessChanged()
        self.containerThicknessChanged()
        self.data,self.ofnames=self.reduce1DSAXS(fname=self.sampleFname,ftimes=self.sampleRepeat,gc_name=self.standardFname,gc_times=self.standardRepeat,air_name=self.airFname,air_times=self.airRepeat,sol_name=self.bkgFname,sol_times=self.bkgRepeat,mt_name=self.containerFname,mt_times=self.containerRepeat,standard=self.standard,xmin=self.QRange[0],xmax=self.QRange[1],Npt=self.interpNpts,interpolation_type=self.interpType,sample_thickness=self.sampleThickness,sol_thickness=self.bkgThickness, mt_thickness=self.containerThickness, gc_thickness=self.standardThickness, bkg_fac=1.0,data={})
        
        
            
    def reduce1DSAXS(self, fname=None,ftimes=1,gc_name=None,gc_times=1,air_name=None,air_times=1,sol_name=None,sol_times=1,mt_name=None,mt_times=1,standard='GC', xmin=0.0,xmax=1.0,Npt=1000,interpolation_type='linear',sample_thickness=1.0,sol_thickness=1.0, mt_thickness=1e-4, gc_thickness=0.1055, bkg_fac=1.0,data={}):
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
        standard          : 'GC' or 'Water'
        xmin, xmax        : Minimum, Maximum Q-values for getting CF by comparing experimental Glassy Carbon data from standard NIST data
        Npt               : Number of  points in which the data will be interpolated
        interpolation_type: Choose between 'linear' (default), 'quadratic' and 'cubic'
        sample_thickness  : Thickness of the samples in cm.
        sol_thickness     : Thickness of the solvent in cm.
        gc_thickness      : Thickness of the standard sample in cm.
        mt_thickness      : Thickness of the container (1e-4 cm for empty capillary)
        bkg_fac           : Background multiplication factor just to scale the background if needed. Default value is 1.0 for automatic scaling. 0.0 or no background subtraction
        """
        if fname is None: 
            self.processMessageTextEdit.append('File error:: Please provide a filename')
            return None, None
        if gc_name is None:
            self.processMessageTextEdit.append('File error:: Please provide glassy carbon filename')
            return None, None
        #if sol_name is None:
        #    self.processMessageTextEdit.append('File error:: Please provide solvent/bacground filename')
        #    return None, None
        
        #Calculating average for all the files:
        file_exists=True
        num=1
        ofnames=[]
        while file_exists:
            try:
                fnum=range((num-1)*ftimes+1,num*ftimes+1)
                data,ofname=average1DSAXS(fname,num=fnum,ofname=fname+'_%04d_avg.txt'%((num-1)*ftimes+1),data=data)
                self.processMessageTextEdit.append('Averaged data saved in a file named %s'%ofname)
                ofnames.append(ofname)
            except:
                del data[fname+'_%04d.txt'%((num-1)*ftimes+1)]
                self.processMessageTextEdit.append(fname+'_%04d.txt'%((num-1)*ftimes+1)+ ' doesnot exist')
                file_exists=False
            num+=1
            QApplication.processEvents()
            
        file_exists=True        
        num=1
        ogcnames=[]
        while file_exists:
            try:
                fnum=range((num-1)*gc_times+1,num*gc_times+1)
                data,ofname=average1DSAXS(gc_name,num=fnum,ofname=gc_name+'_%04d_avg.txt'%((num-1)*gc_times+1),data=data)
                self.processMessageTextEdit.append('Averaged data saved in a file named %s'%ofname)
                ogcnames.append(ofname)
            except:
                del data[gc_name+'_%04d.txt'%((num-1)*gc_times+1)]
                self.processMessageTextEdit.append(gc_name+'_%04d.txt'%((num-1)*gc_times+1)+' doesnot exist')
                file_exists=False
            num+=1
            QApplication.processEvents()
            
        #if len(ofnames)!=len(ogcnames):
        #    self.processMessageTextEdit.append("File number error: Number of data files not same as number of glassy carbon files")
        #    return None, None
            

        if sol_name is not None:
            file_exists = True
            num = 1
            osolnames = []
            while file_exists:
                try:
                    fnum=range((num-1)*sol_times+1,num*sol_times+1)
                    data,ofname=average1DSAXS(sol_name,num=fnum,ofname=sol_name+'_%04d_avg.txt'%((num-1)*sol_times+1),data=data)
                    self.processMessageTextEdit.append('Averaged data saved in a file named %s'%ofname)
                    osolnames.append(ofname)
                except:
                    del data[sol_name+'_%04d.txt'%((num-1)*sol_times+1)]
                    self.processMessageTextEdit.append(sol_name+'_%04d.txt'%((num-1)*sol_times+1)+' doesnot exist')
                    file_exists=False
                num+=1
                QApplication.processEvents()
            
            if len(ofnames)!=len(osolnames):
                self.processMessageTextEdit.append("File number error: Number of data files not same as number of solvent/background files")
                return None, None
               
        if air_name is not None:
            file_exists=True        
            num=1
            oairnames=[]
            while file_exists:
                try:
                    fnum=range((num-1)*air_times+1,num*air_times+1)
                    data,ofname=average1DSAXS(air_name,num=fnum,ofname=air_name+'_%04d_avg.txt'%((num-1)*air_times+1),data=data)
                    self.processMessageTextEdit.append('Averaged data saved in a file named %s'%ofname)
                    oairnames.append(ofname)
                except:
                    del data[air_name+'_%04d.txt'%((num-1)*air_times+1)]
                    self.processMessageTextEdit.append(air_name+'_%04d.txt'%((num-1)*air_times+1)+' doesnot exist')
                    file_exists=False
                num+=1
                QApplication.processEvents()
            if len(ofnames)!=len(oairnames):
                self.processMessageTextEdit.append("File number error: Number of data files not same as number of air background files")
                return None, None
            
        if mt_name is not None:
            file_exists=True        
            num=1
            omtnames=[]
            while file_exists:
                try:
                    fnum=range((num-1)*mt_times+1,num*mt_times+1)
                    data,ofname=average1DSAXS(mt_name,num=fnum,ofname=mt_name+'_%04d_avg.txt'%((num-1)*mt_times+1),data=data)
                    self.processMessageTextEdit.append('Averaged data saved in a file named %s'%ofname)
                    omtnames.append(ofname)
                except:
                    del data[mt_name+'_%04d.txt'%((num-1)*mt_times+1)]
                    self.processMessageTextEdit.append(mt_name+'_%04d.txt'%((num-1)*mt_times+1)+' doesnot exist')
                    file_exists=False
                num+=1
                QApplication.processEvents()
                
            if len(ofnames)!=len(ogcnames):
                self.processMessageTextEdit.append("File number error: Number of data files not same as number of empty capillary files")
                return None, None 

    
        self.processMessageTextEdit.append("First stage completed: All files read successfully...")
        #performing interpolation of all the data sets
        data=interpolate_data(data,Npt=Npt,kind=interpolation_type)
        self.processMessageTextEdit.append("2nd stage completed: All data interpolated...")
        
        #Performing background subtractions of the averaged data
        fkeys=[]
        for num in range(len(ofnames)):
            self.processMessageTextEdit.append("Performing backgroud subtraction and normalization: %d, and %d more to do..."%(num,len(ofnames)-num))
            data[ogcnames[num]]['x']=copy.copy(data[ogcnames[num]]['xintp'])
            if air_name is not None:
                data[ogcnames[num]]['y']=data[ogcnames[num]]['yintp']-data[oairnames[num]]['yintp']
                data[ogcnames[num]]['yerr']=np.sqrt(data[ogcnames[num]]['yintperr']**2+data[oairnames[num]]['yintperr']**2)
            else:
                data[ogcnames[num]]['y']=data[ogcnames[num]]['yintp']
                data[ogcnames[num]]['yerr']=data[ogcnames[num]]['yintperr']
            
            en,cf,x,y=calc_cf(ogcnames[num],standard=standard,xmin=xmin,xmax=xmax,thickness=gc_thickness,interpolation_type=interpolation_type)
            data[ogcnames[num]]['CF']=cf    
            data[ogcnames[num]]['Thickness']=gc_thickness
            fkeys.append(ogcnames[num])


            data[ofnames[num]]['x']=copy.copy(data[ofnames[num]]['xintp'])
            if sol_name is not None:
                data[ofnames[num]]['y']=(data[ofnames[num]]['yintp']-self.bgFactor*data[osolnames[num]]['yintp'])
                data[ofnames[num]]['yerr']=np.sqrt(data[ofnames[num]]['yintperr']**2+self.bgFactor**2*data[osolnames[num]]['yintperr']**2)
            else:
                data[ofnames[num]]['y'] = data[ofnames[num]]['yintp']
                data[ofnames[num]]['yerr'] = data[ofnames[num]]['yintperr']
            data[ofnames[num]]['CF']=cf
            data[ofnames[num]]['Thickness']=sample_thickness
            fkeys.append(ofnames[num])
            
            
            if sol_name is not None:
                data[osolnames[num]]['x']=copy.copy(data[osolnames[num]]['xintp'])
                if mt_name is not None:
                    data[osolnames[num]]['y']=(data[osolnames[num]]['yintp']-data[omtnames[num]]['yintp'])
                    data[osolnames[num]]['yerr']=np.sqrt(data[osolnames[num]]['yintperr']**2+data[omtnames[num]]['yintperr']**2)
                else:
                    data[osolnames[num]]['y']=data[osolnames[num]]['yintp']
                    data[osolnames[num]]['yerr']=data[osolnames[num]]['yintperr']
                data[osolnames[num]]['CF']=cf
                data[osolnames[num]]['Thickness']=sol_thickness
                fkeys.append(osolnames[num])
                 
            
            if mt_name is not None and air_name is not None:
                data[omtnames[num]]['x']=copy.copy(data[omtnames[num]]['xintp'])
                data[omtnames[num]]['y']=data[omtnames[num]]['yintp']-data[oairnames[num]]['yintp']
                data[omtnames[num]]['yerr']=np.sqrt(data[omtnames[num]]['yintperr']**2+data[oairnames[num]]['yintperr']**2)
                data[omtnames[num]]['CF']=cf
                data[omtnames[num]]['Thickness']=mt_thickness
                fkeys.append(omtnames[num])
            QApplication.processEvents()
        self.processMessageTextEdit.append('Saving all the data now...')
        fkeys.sort()
        self.write1DSAXS(data,fnames=fkeys)
        self.processMessageTextEdit.append('Data processing completed successfully.')
        return data,fkeys
    
    
    def write1DSAXS(self,data,fnames=None):
        if fnames is None:
            fnames=data.keys()
        for fname in fnames:
            fdir=os.path.join(os.path.dirname(fname),'Bkg_sub_and_Norm')
            if not os.path.exists(fdir):
                os.makedirs(fdir)
            pfname=os.path.join(fdir,os.path.basename(fname).split('.')[0]+'_bkg_sub_norm.txt')
            header='Processed data on %s\n'%time.asctime()
            for key in data[fname].keys():
                if key!='x' and key!='y' and key!='yerr' and key!='xintp' and key!='yintp' and key!='yintperr' and key!='y-flb' and key!='yraw':
                    header=header+'%s=%s\n'%(key,data[fname][key])
            header=header+'col_name=["Q (A^-1)", "Int", "Int_err"]\n'
            header=header+'Q (A^-1)\tInt\tInt_err\n'
            np.savetxt(pfname,np.vstack((data[fname]['x'],data[fname]['y'],data[fname]['yerr'])).T,comments='#',header=header)
            self.processMessageTextEdit.append('Data saved in %s...'%pfname)
            QApplication.processEvents()
            
        
            
        
        
    
        
        


if __name__=='__main__':
    app=QApplication(sys.argv)
    w=ASAXS_Batch_Processor()
    w.setWindowTitle('ASAXS Batch Processor')
    w.resize(800,600)
    w.showMaximized()
    sys.exit(app.exec_())
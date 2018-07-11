import epics
from epics.utils import BYTES2STR
import sys
import pylab as pl

win=float(sys.argv[1])
start=float(sys.argv[2])
stop=float(sys.argv[3])
count_time=float(sys.argv[4])
steps=float(sys.argv[5])


llpv=epics.PV(BYTES2STR('15IDC:cyberAmp2k0ScaLL.VAL'))
llvpRBK=epics.PV(BYTES2STR('15IDC:cyberAmp2k0ScaLLRbv.VAL'))
ulpv=epics.PV(BYTES2STR('15IDC:cyberAmp2k0ScaUL.VAL'))
IDC15_scaler_start=epics.PV(BYTES2STR('15IDC:scaler1.CNT'))
IDC15_scaler_mode=epics.PV(BYTES2STR('15IDC:scaler1.CONT'))
IDC15_scaler_count_time=epics.PV(BYTES2STR('15IDC:scaler1.TP'))
IDC15_scaler_mode.put(0) # for one shot
yap_pv=epics.PV(BYTES2STR('15IDC:scaler1.S8'))

llpv_ip=llpv.value
ulpv_ip=ulpv.value
data=[]
positions=pl.linspace(start,stop,steps)
i=0
for pos in positions:
    llpv.put(str(pos),wait=True)
    llpv.put(str(pos)+win,wait=True)
    IDC15_scaler_start.put(1,wait=True)
    yap_counts=yap_pv.value
    data.append([i,float(llRBK.value),yap_counts])
    print(i,llpv.value,yap_counts)
    i+=1
data=pl.array(data)
pl.figure()
pl.plot(data[:,1],data[:,2],'r.-')
pl.show()

llpv.put(llpv_ip,wait=True)
ulpv.put(ulpv_ip,wait=True)
IDC15_scaler_mode.put(1)  # for autocount back again
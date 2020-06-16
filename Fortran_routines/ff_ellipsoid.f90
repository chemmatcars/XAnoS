subroutine ff_ellipsoid(q,Rx,RzRatio,Nalf,ff,aff,M)
    !***************************************************************************
    !Subroutine to calculate the form factor of an ellipsoid
    !q = Array of reciprocal wave-vectors at which the form-factor needs to be calculated
    !Rx = Major Radius of ellipsoid in Angstroms
    !RzRatio = Rz/Rx ratio for the minor axis of the ellipsoid
    !Nalf = Number of distict azimuthal angles for angular integration from 0 to pi/2
    !ff = azimuthally averaged form factor
    !aff= azimuthally averaged form factor amplitude
    !M = No. of reciprocal wave-vectors at which the form-factor needs to be calculated
    !***************************************************************************
    integer :: M, i, j, Nalf
    double precision :: q(0:M-1)
    double precision :: ff(0:M-1), aff(0:M-1)
    double precision :: Rx, RzRatio, Rx2, Rz2
    double precision :: rt, ft, alf, dalf, V
    dalf=3.14159/Nalf
    Rx2=Rx*Rx
    Rz2=Rx2*RzRatio*RzRatio
    V=4*3.14159*Rx**3*RzRatio/3
    do i = 0,M-1
        ff(i)=0.0d0
        aff(i)=0.0d0
        do j = 0, Nalf-1
            alf=float(j)*dalf
            rt=dsqrt(Rx2*dsin(alf)**2+Rz2*dcos(alf)**2)
            ft=(dsin(q(i)*rt)-q(i)*rt*dcos(q(i)*rt))/(q(i)*rt)**3
            aff(i)=aff(i)+ft*dsin(alf)
            ff(i)=ff(i)+ft*ft*dsin(alf)
        end do
        aff(i)=3*V*dalf*aff(i)
        ff(i)=(3*V)**2*ff(i)*dalf
    end do

end subroutine ff_ellipsoid

subroutine ff_ellipsoid_ml(q,Rx,RzRatio,rho,Nalf,ff,aff,M,Nlayers)
    !***************************************************************************
    !Subroutine to calculate the form factor of sphere with disctribution of radii
    !q = Array of reciprocal wave-vectors at which the form-factor needs to be calculated
    !R = Array of radius and shell thicknesses of sphere in Angstroms
    !rho = Array of electron densities  of core and the shells
    !Rdist = Probablity distribution of radii
    !Nlayers = Number of shells plus the core
    !aff = amplitude of form factor
    !ff = Form factor of sphere
    !M = No. of reciprocal wave-vectors at which the form-factor needs to be calculated
    !***************************************************************************
    integer :: M, i, j, k, Nalf, Nlayers
    double precision :: q(0:M-1)
    double precision :: ff(0:M-1), aff(0:M-1)
    double precision :: Rx(0:Nlayers-1), RzRatio(0:Nlayers-1), rho(0:Nlayers-1)
    double precision :: rt, ft, tRx, tRz, Rx2, Rz2, alf, dalf, V, taff
    dalf=3.14159/Nalf
    do i = 0,M-1
        ff(i)=0.0d0
        aff(i)=0.0d0
        tRx=0.0d0
        tRz=0.0d0
        do j = 0, Nalf-1
            alf=float(j)*dalf
            tRx=0.0d0
            tRz=0.0d0
            taff=0.0d0
            do k = 0, Nlayers-2
                tRx=tRx+Rx(k)
                tRz=tRz+Rx(k)*RzRatio(k)
                Rx2=tRx*tRx
                Rz2=tRz*tRz
                rt=dsqrt(Rx2*dsin(alf)**2+Rz2*dcos(alf)**2)
                ft=(rho(k)-rho(k+1))*(dsin(q(i)*rt)-q(i)*rt*dcos(q(i)*rt))/(q(i)*rt)**3
                taff=taff+ft
            end do
            aff(i)=aff(i)+taff*dsin(alf)
            ff(i)=ff(i)+taff*taff*dsin(alf)
        end do
        V=4*3.14159*tRz*tRx**2/3.0
        aff(i)=3*V*dalf*aff(i)
        ff(i)=(3*V)**2*ff(i)*dalf
    end do

end subroutine ff_ellipsoid_ml

subroutine ff_ellipsoid_ml_asaxs(q,Rx,RzRatio,rho,eirho,adensity,Nalf,fft,ffs,ffc,ffr,M,Nlayers)
    !***************************************************************************
    !Subroutine to calculate the form factor of sphere with disctribution of radii
    !q = Array of reciprocal wave-vectors at which the form-factor needs to be calculated
    !R = Array of radius and shell thicknesses of sphere in Angstroms
    !rho = Array of electron densities  of core and the shells
    !Rdist = Probablity distribution of radii
    !Nlayers = Number of shells plus the core
    !aff = amplitude of form factor
    !ff = Form factor of sphere
    !M = No. of reciprocal wave-vectors at which the form-factor needs to be calculated
    !***************************************************************************
    integer :: M, i, j, k, Nalf, Nlayers
    double precision :: q(0:M-1)
    double precision :: fft(0:M-1), ffs(0:M-1), ffc(0:M-1), ffr(0:M-1)
    double precision :: Rx(0:Nlayers-1), RzRatio(0:Nlayers-1)
    double complex :: rho(0:Nlayers-1)
    double precision :: eirho(0:Nlayers-1), adensity(0:Nlayers-1)
    double precision :: rt, fs, fc, fr, tRx, tRz, Rx2, Rz2, alf, dalf, V, fac
    double complex :: ft, tft
    double precision :: tfs, tfr
    dalf=3.14159/Nalf
    do i = 0,M-1
        fft(i)=0.0d0
        ffs(i)=0.0d0
        ffc(i)=0.0d0
        ffr(i)=0.0d0
        tRx=0.0d0
        tRz=0.0d0
        do j = 0, Nalf-1
            alf=float(j)*dalf
            tRx=0.0d0
            tRz=0.0d0
            tft=0.0d0
            tfs=0.0d0
            tfr=0.0d0
            do k = 0, Nlayers-2
                tRx=tRx+Rx(k)
                tRz=tRz+Rx(k)*RzRatio(k)
                Rx2=tRx*tRx
                Rz2=tRz*tRz
                rt=dsqrt(Rx2*dsin(alf)**2+Rz2*dcos(alf)**2)
                fac=(dsin(q(i)*rt)-q(i)*rt*dcos(q(i)*rt))/(q(i)*rt)**3
                ft=(rho(k)-rho(k+1))*fac
                fs=(eirho(k)-eirho(k+1))*fac
                fr=(adensity(k)-adensity(k+1))*fac
                fc=fs*fr
                tft=tft+ft
                tfs=tfs+fs
                tfr=tfr+fr
            end do
            fft(i)=fft(i)+cdabs(tft)**2*dsin(alf)
            ffs(i)=ffs(i)+tfs**2*dsin(alf)
            ffc(i)=ffc(i)+tfs*tfr*dsin(alf)
            ffr(i)=ffr(i)+tfr**2*dsin(alf)
        end do
        V=4*3.14159*tRz*tRx**2/3.0
        fft(i)=(3*V)**2*fft(i)*dalf
        ffs(i)=(3*V)**2*ffs(i)*dalf
        ffc(i)=(3*V)**2*ffc(i)*dalf
        ffr(i)=(3*V)**2*ffr(i)*dalf
    end do

end subroutine ff_ellipsoid_ml_asaxs
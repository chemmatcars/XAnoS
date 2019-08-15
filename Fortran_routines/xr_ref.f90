subroutine parratt_born(q,lambda,d,rho,beta,sigma,Rgen,Rgenr, M,N)
!***************************************************************************
!Subroutine to calculate Specular Reflectivity using Parrat Algorithm with
!Born Approximation for roughness
!M = No. of data points
!N = No. of slabs
!lambda = wavelength
!d = list of thicknesses of each slab
!rho=list of Electron densities of each slab
!beta=list of Absorption coefficient in each slab
!Rgen = generated reflectivtiy data
!Rgenr = generated reflectance data
!q = change in wave vector
!***************************************************************************
integer :: M,N
double precision :: q(0:M), Rgen(0:M)
double precision :: d(0:N+1), rho(0:N+1), beta(0:N+1), sigma(0:N+1), qc2(0:N+1)
double precision :: lambda
double complex :: X, fact1, fact2, r(0:N+1), k1, k2, fact, Rgenr(0:M)
double precision, parameter :: re=2.814e-5, pi=3.14157

do j=0,N+1
   qc2(j)=16.0d0*pi*re*(rho(j)-rho(0))
enddo

do i = 0,M
   r(N+1)=dcmplx(0.0d0,0.0d0)
   do j=N,0,-1
      k1=cdsqrt(dcmplx(q(i)**2-qc2(j),-32.0d0*beta(j)*pi**2/lambda**2))
      k2=cdsqrt(dcmplx(q(i)**2-qc2(j+1),-32.0d0*beta(j+1)*pi**2/lambda**2))
      X=(k1-k2)*cdexp(-k1*k2*sigma(j+1)**2/2)/(k1+k2)
      fact1=dcmplx(dcos(dble(k2)*d(j+1)),dsin(dble(k2)*d(j+1)))
      fact2=dexp(-aimag(k2)*d(j+1))
      fact=fact1*fact2
      r(j)=(X+r(j+1)*fact)/(1.0+X*r(j+1)*fact)
   enddo
   Rgenr(i)=r(0)
   Rgen(i)=cdabs(r(0))**2
enddo
end subroutine parratt_born


subroutine parratt(q,lambda,d,rho,beta,Rgen,Rgenr,M,N)
!***************************************************************************
!Calculation of reflectivity by Parratt Recursion Formula without any roughness
!
!M = No. of data points
!N = No. of slabs
!lambda = wavelength
!d = list of thicknesses of each slab
!rho=list of Electron densities of each slab
!beta=list of Absorption coefficient in each slab
!Rgen = generated reflectivtiy data
!Rgenr= generated reflectance data
!q = change in wave vector
!***************************************************************************
integer :: M,N
double precision :: q(0:M), Rgen(0:M)
double precision :: d(0:N+1), rho(0:N+1), beta(0:N+1), qc2(0:N+1)
double precision :: lambda
double complex :: X, fact1, fact2, r(0:N+1), k1, k2, fact,Rgenr(0:M)
double precision, parameter :: re=2.814e-5, pi=3.14157

do j=0,N+1
   qc2(j)=16.0d0*pi*re*(rho(j)-rho(0))
enddo

do i = 0,M
   r(N+1)=dcmplx(0.0d0,0.0d0)
   do j=N,0,-1
      k1=cdsqrt(dcmplx(q(i)**2-qc2(j),-32.0d0*beta(j)*pi**2/lambda**2))
      k2=cdsqrt(dcmplx(q(i)**2-qc2(j+1),-32.0d0*beta(j+1)*pi**2/lambda**2))
      X=(k1-k2)/(k1+k2)
      fact1=dcmplx(dcos(dble(k2)*d(j+1)),dsin(dble(k2)*d(j+1)))
      fact2=dexp(-aimag(k2)*d(j+1))
      fact=fact1*fact2
      r(j)=(X+r(j+1)*fact)/(1.0+X*r(j+1)*fact)
   enddo
   Rgenr(i)=r(0)
   Rgen(i)=cdabs(r(0))**2
enddo
end subroutine parratt


subroutine conv_parratt(q,delq,lambda,d,rho,beta,Rgen,M,N)
!***************************************************************************
!Calculation of convoluted reflectivity by Parratt Recursion Formula without
!any roughness

!M = No. of data points
!N = No. of slabs
!lambda = wavelength
!d = list of thicknesses of each slab
!rho=list of Electron densities of each slab
!beta=list of Absorption coefficient in each slab
!Rgen = generated reflectivtiy data
!q = change in wave vector
!delq=width of the resolution funciton
!***************************************************************************
integer :: M,N
double precision :: q(0:M), Rgen(0:M)
double precision :: d(0:N+1), rho(0:N+1), beta(0:N+1), qc2(0:N+1)
double precision :: lambda,delq
double complex :: X, fact1, fact2, r(0:N+1), k1, k2, fact
double precision, parameter :: re=2.814e-5, pi=3.14157
double precision :: refsum,q0
integer :: Nres
Nres=21

do j=0,N+1
   qc2(j)=16.0d0*pi*re*(rho(j)-rho(0))
enddo


do i = 0,M
  r(N+1)=dcmplx(0.0d0,0.0d0)
  refsum=0.0d0
  ressum=0.0d0
  do k = -(Nres-1)/2,(Nres-1)/2
    qo=q(i)+4*k*delq/(Nres-1)
      if (qo>=0.0d0) then
	do j=N,0,-1
	  k1=cdsqrt(dcmplx(qo**2-qc2(j),-32.0d0*beta(j)*pi**2/lambda**2))
	  k2=cdsqrt(dcmplx(qo**2-qc2(j+1),-32.0d0*beta(j+1)*pi**2/lambda**2))
	  X=(k1-k2)/(k1+k2)
	  fact1=dcmplx(dcos(dble(k2)*d(j+1)),dsin(dble(k2)*d(j+1)))
	  fact2=dexp(-aimag(k2)*d(j+1))
	  fact=fact1*fact2
	  r(j)=(X+r(j+1)*fact)/(1.0+X*r(j+1)*fact)
        enddo
	refsum=refsum+cdabs(r(0))**2*dexp(-k**2/2.0d0/(Nres-1)**2)
	ressum=ressum+dexp(-dfloat(k)**2/2.0d0/(dfloat(Nres)-1)**2)
      endif
    enddo
    rgen(i)=refsum/ressum
enddo

end subroutine conv_parratt


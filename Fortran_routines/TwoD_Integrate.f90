subroutine integrate_2d(img,img_err,solid_angle,rad,chi,rad_val,chi_val,integ,integ_err,M,N,rad_npt,chi_npt)
!**********************************************************************************
!Subroutine to perform cacking of a two dimensional SAXS/WAXS image
![M,N]=dimensions of the image
!img=image array
!img=image error array
!rad=array of radial values with similar dimensions as img
!chi=array of azimuthal values with similar dimensions as img!
!solid_angle= array of solid angle of the pixes of the detector
!rad_npt=Maximum number of points between which the radial part will be divided
!chi_npt=Maximum number of points between which the azimuthal part will be divided
!rad_val=Radial values
!chi_val=azimuthal values
!integ=integrated two dimensional caking data
!integ_err
!**********************************************************************************
implicit none
integer (8):: M,N,rad_npt,chi_npt
double precision, dimension(0:M-1,0:N-1):: img,img_err,solid_angle,rad,chi
double precision, dimension(0:rad_npt-1,0:chi_npt-1):: integ,integ_err,counts
double precision, dimension(0:rad_npt-1):: rad_val
double precision, dimension(0:chi_npt-1):: chi_val
double precision :: rad_step,chi_step
integer (8):: i,j,irad,ichi

integ(:,:)=0.0d0	
integ_err(:,:)=0.0d0
counts(:,:)=0.0d0

rad_step=dabs(rad_val(1)-rad_val(0))
chi_step=dabs(chi_val(1)-chi_val(0))


do i =0,M-1
	do j=0,N-1
		irad=idint((rad(i,j)-rad_val(0))/rad_step)
		ichi=idint((chi(i,j)-chi_val(0))/chi_step)
		if ((img(i,j)>0.0d0) .and. (irad>=0) .and. (ichi>=0) .and. (irad<=rad_npt-1) .and. (ichi<=chi_npt-1))  then
			integ(irad,ichi)=integ(irad,ichi)+img(i,j)/solid_angle(i,j)
			integ_err(irad,ichi)=integ_err(irad,ichi)+img_err(i,j)**2/solid_angle(i,j)**2
			counts(irad,ichi)=counts(irad,ichi)+1.0d0
		endif
	enddo
enddo

do i =0,rad_npt-1
	do j=0,chi_npt-1
		if (counts(i,j)>1.0d0) then
			integ(i,j)=integ(i,j)/counts(i,j)
			integ_err(i,j)=dsqrt(integ_err(i,j))/counts(i,j)
		else
			integ(i,j)=0.0d0
			integ_err(i,j)=0.0d0
		endif
	enddo
enddo

end subroutine integrate_2d

			
	


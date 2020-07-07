subroutine ff_sphere(q,R,ff,M)
    !***************************************************************************
    !Subroutine to calculate the form factor of sphere
    !q = Array of reciprocal wave-vectors at which the form-factor needs to be calculated
    !R = Radius of sphere in Angstroms
    !M = No. of reciprocal wave-vectors at which the form-factor needs to be calculated
    !***************************************************************************
    integer :: M, i
    double precision :: q(0:M-1)
    double precision :: ff(0:M-1)
    double precision :: R, fact

    do i = 0,M-1
        fact=(sin(q(i)*R)-q(i)*R*cos(q(i)*R))/q(i)**3
        ff(i)=fact*fact
    enddo

end subroutine ff_sphere

subroutine ff_sphere_ML(q,R,rho,ff,aff,M,Nlayers)
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
    integer :: M, Nlayers, i, j
    double precision :: q(0:M-1)
    double precision :: ff(0:M-1),aff(0:M-1)
    double precision :: R(0:Nlayers-1), rho(0:Nlayers-1)
    double precision :: fact,rt

    do i = 0,M-1
        fact=0.0d0
        rt=0.0d0
        do j=1,Nlayers-1
            rt=rt+R(j-1)
            fact=fact+(rho(j-1)-rho(j))*(dsin(q(i)*rt)-q(i)*rt*dcos(q(i)*rt))/q(i)**3
        end do
        aff(i)=fact
        ff(i) = fact*fact
    enddo
end subroutine ff_sphere_ML
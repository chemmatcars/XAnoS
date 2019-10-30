subroutine ff_cylinder(q,R,L,ff,M)
    !***************************************************************************
    !Subroutine to calculate the form factor of cylinder
    !q = Array of reciprocal wave-vectors at which the form-factor needs to be calculated
    !R = Radius of cylinder in Angstroms
    !L = Length of cylinder in Angstroms
    !M = No. of reciprocal wave-vectors at which the form-factor needs to be calculated
    !***************************************************************************
    integer :: M, i, j
    double precision :: q(0:M)
    double precision :: ff(0:M)
    double precision :: R, L, alpha, fact
    double precision, parameter :: pi=3.14157
    integer, parameter :: N=1000

    do i = 0,M
        do j=1,N
            alpha=pi*j/N/2.0
            fact=(sin(q(i)*L*cos(alpha)/2)/(q(i)*L*cos(alpha)/2) * bessel_j1(q(i)*R*sin(alpha))/(q(i)*R*sin(alpha)))**2
            ff(i) = ff(i) + fact * sin(alpha)
        enddo
        ff(i) = ff(i)*pi/N
    enddo

end subroutine ff_cylinder


subroutine ff_cylinder_dist(q,R,Rdist,L,Ldist,ff,M,N)
    !***************************************************************************
    !Subroutine to calculate the form factor of cylinder with disctribution of radius and length
    !q = Array of reciprocal wave-vectors at which the form-factor needs to be calculated
    !R = Array of radii of cylinder in Angstroms
    !Rdist = Probablity distribution of radii R
    !L = Array of Length of cylinder in Angstroms
    !Ldist = Probablity distribution of length L
    !N = No. of samples R and L
    !ff = Form factor of cylinder
    !M = No. of reciprocal wave-vectors at which the form-factor needs to be calculated
    !***************************************************************************
    integer :: M, N, i, j
    double precision :: q(0:M)
    double precision :: ff(0:M)
    double precision :: R(0:N), Rdist(0:N), L(0:N), Ldist(0:N), fact1, fact2, tsum
    double precision, parameter :: pi=3.14157
    integer, parameter :: Nangles=1000
    double precision :: alpha(0:Nangles)

    do j=1,Nangles
        alpha(j)=pi*j/Nangles/2.0
    end do

    do i = 0,M
        ff(i)=0.0d0
        do k=0,N
            tsum=0.0d0
            do j=1,Nangles
                fact1=sin(q(i)*L(k)*cos(alpha(j))/2.0d0)/(q(i)*L(k)*cos(alpha(j))/2.0d0)
                fact2=bessel_j1(q(i)*R(k)*sin(alpha(j)))/(q(i)*R(k)*sin(alpha(j)))
                tsum = tsum + fact1**2*fact2**2*sin(alpha(j))
            enddo
            ff(i) = ff(i)+tsum*Rdist(k)*Ldist(k)
        end do
        ff(i) = ff(i)*pi/sum(Rdist)/sum(Ldist)/Nangles
    enddo

end subroutine ff_cylinder_dist

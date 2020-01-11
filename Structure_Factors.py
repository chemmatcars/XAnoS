import numpy as np

def hard_sphere_sf(Q, D=1.0, phi=0.02):
    """
    Computes Hard-Sphere Structure Factor
    :param Q: Array of reciprocal space vectors in inv-Angstroms
    :param D: Hard-Sphere Diameter of particles in Angstroms
    :param phi: Volume Fraction of particles
    :return: Structure factor
    """
    if phi > 0.00001:
        lam1 = (1 + 2 * phi) ** 2 / (1 - phi) ** 4
        lam2 = -(1 + phi / 2) ** 2 / (1 - phi) ** 4
        q = Q * D
        t1 = (np.sin(q) - q * np.cos(q)) / q ** 3
        t2 = (q ** 2 * np.cos(q) - 2 * q * np.sin(q) - 2 * np.cos(q) + 2) / q ** 4
        t3 = (q ** 4 * np.cos(q) - 4 * q ** 3 * np.sin(q) - 12 * q ** 2 * np.cos(q) + 24 * q * np.sin(q)
              + 24 * np.cos(q) - 24) / q ** 6
        ncq = -24 * phi * (lam1 * t1 - 6 * phi * lam2 * t2 - phi * lam1 * t3 / 2)
        sq = 1 / (1 - ncq)
        return sq
    else:
        return np.ones_like(Q)

def sticky_sphere_sf(Q, D = 1.0, phi = 0.01, U = -1.0, delta = 0.01):
    """
    Computes Sticky-Sphere structure Factor
    :param Q: Array of reciprocal space vectors in inv-Angstroms
    :param D: Hard-Sphere Diameter of particles in Angstroms
    :param phi: Volume Fraction of particles
    :param U: Sticky sphere interaction energy
    :param delta: Width of the sticky sphere interactions
    :return: Structure factor
    """
    tau = np.exp(U) * (D+delta) / 12.0 / delta
    a = (1 + phi / 2) / (1 - phi)**2
    b = phi / (1-phi)
    c = phi / 12
    if (b+tau)**2 >= 4 * a * c:
        lam = (b + tau - np.sqrt((b+tau)**2 - 4 * a * c)) / 2 / c
    else:
        lam=0.0
        raise RuntimeWarning("Negative number obtained within  np.sqrt function")
    q = Q * D
    mu = lam * phi / (1 - phi)
    alf = (1 + 2 * phi - mu)/(1 - phi)**2
    bet = (-3 * phi + mu) / 2 / (1 - phi)**2

    A=1 + 12 * phi * (alf * (np.sin(q) - q * np.cos(q)) / q**3 +
                      bet * (1 - np.cos(q))/ q**2 -
                      lam * np.sin(q) / q / 12)
    B = 12 * phi * (alf * (1 / ( 2 * q) - np.sin(q) / q**2 + (1 - np.cos(q)) / q**3) +
                    bet * (1 / q - np.sin(q) / q**2) - lam*(1 - np.cos(q)) / 12 / q)
    return 1/(A**2+B**2)





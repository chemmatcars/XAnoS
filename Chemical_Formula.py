import re
from xraydb import XrayDB
import sys
import numpy as np
from mendeleev import get_table


class Chemical_Formula:
    def __init__(self, formula=None):
        self.formula = formula
        self.xdb = XrayDB()
        cols = ['symbol', 'covalent_radius_cordero']
        ptable = get_table('elements')
        x = ptable[cols]
        self.covalent_radius = x.set_index('symbol').T.to_dict('index')['covalent_radius_cordero']
        if formula is not None:
            self.parse(self.formula)

    def parse(self, formula):
        parsed = re.findall(r'([A-Z][a-z]*)([-+]?\d*\.*\d*)', formula)
        self.formula_dict = {}
        for a, b in parsed:
            if b != '':
                self.formula_dict[a] = float(b)
            else:
                self.formula_dict[a] = 1.0
        return self.formula_dict

    def elements(self):
        """
        Provides a list of all the elements in the formula
        :return:
        """
        return list(self.formula_dict.keys())

    def element_mole_ratio(self):
        """
        Provides a dictionary of mole ratio of all the elements in the formula
        :return:
        """
        return self.formula_dict

    def molar_mass(self):
        """
        Provides the total Molar-mass of the compound represented by the formula
        :return:
        """
        return np.sum([self.xdb.molar_mass(ele) * num for ele, num in self.formula_dict.items()])

    def molecular_weight(self):
        """
        Provides the Molecular-Weight of the compound represented by the formula
        :return:
        """
        return self.molar_mass()

    def molar_mass_ratio(self, element):
        """
        Provides the molecular-mass-ratio of the element in the chemical formula
        :param element: Symbol of the element
        :return:
        """
        if element in self.formula_dict.keys():
            tot = self.molar_mass()
            return self.xdb.molar_mass(element) * self.formula_dict[element] / tot
        else:
            return 0.0

    def molar_volume(self):
        """Returns molar volumes in cm^3 or ml"""
        volume=0.0
        for ele,moles in self.formula_dict.items():
            volume+=moles*4*np.pi*self.covalent_radius[ele]**3/3
        return 6.023e23*volume*1e-30



if __name__=='__main__':
    t=Chemical_Formula('NaCl')
    elements=t.elements
    element_mole_ratio=t.element_mole_ratio()
    molar_mass=t.molar_mass()
    molar_volume=t.molar_volume()
    print('Elements:',elements())
    print('Element moles:',element_mole_ratio)
    print('Molecular Weight (gms):',molar_mass)
    print('Molar Volume (ml):',molar_volume)
    density=(17.11*molar_mass/1000+(1-17.11*molar_volume/1000))
    print('Density of 17.11M NaCl (gms/ml):',density)



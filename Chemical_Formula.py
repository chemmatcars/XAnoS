import re
from xraydb import XrayDB
import sys
import numpy as np

class Chemical_Formula:
    def __init__(self,formula):
        self.formula=formula
        self.xdb=XrayDB()
        parsed=re.findall(r'([A-Z][a-z]*)([-+]?\d*\.*\d*)',self.formula)
        self.formula_dict={}
        for a,b in parsed:
            if b!='':
                self.formula_dict[a]=float(b)
            else:
                self.formula_dict[a]=1.0

    def elements(self):
        """
        Provides a list of all the elements in the formula
        :return:
        """
        return list(self.formula_dict.keys())

    def element_mole_ratio(self):
        """
        Provides a dictionary of mole ratio of all the elements in the forumula
        :return:
        """
        return self.formula_dict

    def molar_mass(self):
        """
        Provides the total Molar-mass of the compound represented by the formula
        :return:
        """
        return np.sum([self.xdb.molar_mass(ele)*num for ele,num in self.formula_dict.items()])

    def molecular_weight(self):
        """
        Provides the Molecular-Weight of the compound represented by the formula
        :return:
        """

        return self.molar_mass()

    def molar_mass_ratio(self,element):
        """
        Provides the molecular-mass-ratio of the element in the chemical formula
        :param element: Symbol of the element
        :return:
        """
        if element in self.formula_dict.keys():
            tot=self.molar_mass()
            return self.xdb.molar_mass(element)*self.formula_dict[element]/tot
        else:
            return 0.0


if __name__=='__main__':
    t=Chemical_Formula('H2SO4')
    print('Elements:',t.elements())
    print('Element moles:',t.element_mole_ratio())
    print('Molecular Weight (gms):',t.molar_mass())
    print('Mass Ratio of O(gms):',t.molar_mass_ratio('O'))


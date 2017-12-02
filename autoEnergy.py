'''
###############################################################################
#Module for Intensity optimization at a particular energy                     #
###############################################################################
Typically white beam enters a particular beamline optics where most of the 
times the beam gets monochromatized and then focused. In the undulator beamlines
the white beam is not exactly white as it peaks around the energy we chose by
selecting the selecting the gap between the magnets. There are 4 componets which
needs to be adjusted while changing energy in a beamline. 
1) Monochromator bragg angle: To accept a particular energy. This is a
one time change in the process of changing the energy
2) Undulator energy: We tweak the undulator little bit i.e typically 100-150 eV
above the monochromator energy.
3) 2nd Crystal of the monochromator: Tweek it through a DAC
4) Mirror after the monochromator: Tweak it through a DAC if needed.
'''



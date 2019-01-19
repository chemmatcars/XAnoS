.. _Introduction:

Introduction
============
    SAXS_Drive is a collection of widgets developed for the measurement, visualization, data reduction and analysis
    of Anomalous Small Angle X-ray Scattering data at `NSF's ChemMatCARS (Sector 15) <https://chemmatcars.uchicago.edu/>`_  at `Advanced Photon Source <https://www.aps.anl.gov/>`_ , USA.

    If you are using any components of SAXS_Drive for your research/work please do not forget to acknowledge (see :ref:`Acknowledgements`).

.. _Installation:

Installation
************
Follow the following instructions for installation:

1) Install Anaconda python (Python 3.6 and higher) for your operating system from: 'https://www.anaconda.com/download/'
2) Open a Anaconda terminal the run these two commands::

    $conda install pyqt pyqtgraph sqlalchemy scipy six matplotlib
    $pip install lmfit pyfai periodictable lmdifftools

3) Go to the website: https://github.com/scikit-beam/XrayDB

	i) Click the green button named "Clone or download"
	ii) Download the zip file
	iii) Extract the zip file into a folder
	iv) In the Anaconda terminal go the the extracted folder and type the following commands::

   		$cd "/home/mrinal/Download/XrayDB-master"
   		$cd python
   		$python setup.py install

4) Download SAXS_Drive from the Github page:
	i) Click the green button named "Clone or download"
	ii) Download the zip file
   	iii) Extract the zip file into a folder
   	iv) In the Anaconda terminal go the the extracted folder::

   	    $cd "/home/mrinal/Download/SAXS_Drive-master"

5) Run the following commands to run different packages:
    i) Data Collection package (Do not run this when not in the beamline!)::

        $python Data_Collector.py

    ii) Data Reduction package::

        $python Data_Reducer.py

    iii) Data viewer and analysis package::

            $python ASAXS_Widget.py

    iv) Data fitting package::

        $python Fit_Widget.py


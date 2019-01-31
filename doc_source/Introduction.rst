.. _Introduction:

Introduction
============
    **XAnoS** stands for **X**\-ray **Ano**\malous **S**\cattering and the package provides a collection of widgets developed for the measurement, visualization, data reduction and analysis
    of Anomalous Small Angle X-ray Scattering data at `NSF's ChemMatCARS (Sector 15) <https://chemmatcars.uchicago.edu/>`_  at `Advanced Photon Source <https://www.aps.anl.gov/>`_ , USA.

    If you are using any components of XAnoS for your research/work please do not forget to acknowledge (see :ref:`Acknowledgements`).

.. _Installation:

Installation
************
Follow the following instructions for installation:

1) Install Anaconda python (Python 3.6 and higher) for your operating system from: 'https://www.anaconda.com/download/'
2) Open a Anaconda terminal the run these two commands::

    conda install pyqt pyqtgraph sqlalchemy scipy six matplotlib
    pip install lmfit pyfai periodictable lmdifftools

3) Go to the website: https://github.com/scikit-beam/XrayDB

	i) Click the green button named "Clone or download"
	ii) Download the zip file
	iii) Extract the zip file into a folder
	iv) In the Anaconda terminal go the the extracted folder and type the following commands with your own folder path::

   		cd /home/mrinal/Download/XrayDB-master
   		cd python
   		python setup.py install

4) The installation can be done in two different ways:
    a) Universal way which does not need GIT installation:
	    i) Open a web browser and go to the webpage : https://github.com/nayanbera/XAnoS
	    ii) Click the green button named "Clone or download"
	    iii) Download the zip file
   	    iv) Extract the zip file into a folder
   	    v) In the Anaconda terminal go the the extracted folder::

   	            cd /home/mrinal/Download/XAnoS-master

    b) Easier way with `GIT <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_ already installed, run the following commands in a terminal with your own folder path::

        cd /home/mrinal/Download/
        git clone https://github.com/nayanbera/XAnoS.git

    The second method will create **XAnoS** folder with all updated packages in installation folder (i.e. /home/mrinal/Download). The advantage of the second method is that it is easy to upgrade the package when there is any update available. Go to the folder named **XAnoS** and run the following command to upgrade it::

            git pull

5) Run the following commands to run different packages:
    i) Data Collection package (**Do not run this when not in the beamline!**)::

         python Data_Collector_Server.py

    ii) Data Reduction package::

         python Data_Reducer.py

    iii) Data viewer and analysis package::

             python ASAXS_Widget.py

    iv) Data fitting package::

         python Fit_Widget.py


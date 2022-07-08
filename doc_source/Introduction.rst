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

    conda install git pyqt pyqtgraph sqlalchemy scipy six matplotlib pandas
    pip install lmfit pyfai pylint periodictable mendeleev corner emcee tabulate

3) The installation can be done by running the following commands in a terminal (linux/MacOS) or Anaconda Terminal (windows) in a folder where you wish the software to be installed::

        git clone https://github.com/nayanbera/XAnoS.git

   The command create a folder named XAnoS. In order to upgrade the software at any time just go to the folder named **XAnoS** and run the following command in the terminal::

            git pull

4)  Run the following commands to run different packages:
    i) Data Collection package (**Do not run this when not in the beamline!**)::

         python XAnoS_Collector.py

    ii) Data Reduction package::

         python XAnoS_Reducer.py

    iii) Data viewer and analysis package::

            python XAnoS_Components.py


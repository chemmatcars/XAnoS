.. _Fit_Widget:

Fit Widget
==========

.. contents:: Table of Contents
   :depth: 2

Fit_Widget_ provides a platform to simulate and fit a model to 1D data. It uses `LMFIT <https://lmfit.github.io/lmfit-py/>`_ python library for fitting.
Some of the commonly used functions are provided under different categories and the users can develop their own
categories and fitting functions by using an easy to use template within a Function_Editor_


.. figure:: ./Figures/Fit_Widget_in_Action.png
    :figwidth: 100%

    **Fit Widget** in action in which a Small Angle X-ray Scattering data is fitted with poly-dispersed **Sphere** model with **Log-Normal** distribution.


    **Features**

    1. Read and fit multiple data sets
    2. Functions are categorized under different types and experimental techniques
    3. Easy to add new categories and new functions within the categories
    4. Once the function is defined properly all the free and fitting parameters will be available within the GUI as tables.
    5. An in-built Function_Editor_ is provided with a easy to use template.
    6. A Data_Dialog_ is provided for importing and manipulating data files.
    7. Another cool feature of Fit_Widget_ is the ability to view and save other functions/parameters generated during the calculation/evaluation of a user supplied functions.


    **Usage**

    Fit_Widget_ can be used as stand-alone python fitting package by running this in terminal::

        python Fit_Widget.py

    The widget can be used as a widget with any other python application.

.. _Brief_Tutorial:

Brief Tutorial
**************
This tutorial is focused on showing a beginner how to use the Fit_Widget_ to:

1. Simulate an already available function
2. Import and fit a data with a simulated model or function
3. Write your own model/function using the Function_Editor_

Simulate an already available function
--------------------------------------
The available functions can be simulated by following these steps:

1. In the Fit_Widget_ window go to a **Function** tab
2. Select a categories among the **Function Categories** which will populate the **Functions** lists with functions/models available for that category.
3. Click on one of the functions which will create a plot the simulated curve in the **Data and Fit** tab and also it will populates the parameter tables in **Parameters** tab with the parameter values required for the functions.
4. The values of **X-axis** of the simulated curve can be changed by changing the **x** parameter located at the to of the **Parameters** tab.
5. All the parameters can be changed and on change of each of the parameters the function/model will be re-calculated and the plot will be updated.

Data Importing and Fitting
--------------------------
The main objective of Fit_Widget_ is to provide a user to fit a model/function to a data. Please follow these to perform a data fitting using Fit_Widget_:

1. Click the **Data** tab.
2. Import data file(s) by clicking the **Add Files** button which will prompt for selecting the data files.
3. Once imported the data files with their path will be listed in the **Data files** list below the **Add Files** button
4. Select the data file in the list which you would like to fit.
5. Go to **Functions** tab and select the necessary Category from the **Function Category** list and then select the necessary function from the **Functions** list.
6. Now you will have both data and simulated curve/function plotted as symbols and lines, respectively.
7. At this point play with the parameters value in the **Parameters** tab to make the simulated curve/function close to the data.
8. Once the simulated curve looks very close to the data you can select the parameters available in the **Single fitting parameters** and **Multiple fitting parameters** as fitting parameters by checking out the checkbox (☑) available in box carrying the parameter values.
9. Constraints on the **Single fitting parameters** can be implemented by adding values to the cell corresponding to **Min/Max** columns which are kept by default as **-inf/inf**, respectively, for no limits.
10. Constraints on the **Multiple fitting parameters** can be implemented by **double-clicking** the cell displaying the value of parameter of interest. This will open a dialog to chose for the **Min/Max** values for the parameters which are also kept as **-inf/inf**, respectively, for no constraints.
11. Go back to the **Data** tab and provide the **X-range** of the data in this format **Xmin:Xmax** to perform the fit. By default, the values of **Xmin:Xmax** is taken from the **Xmin** and **Xmax** of the data.
12. Select the **Fit Scale**  between the **Linear|Log** option. By default the **Linear** option is selected. **Fit Scale** determines how the **Chi-Square** (:math:`\chi^2`) will be calculated i.e.:

    * For **Fit Scale=Log**: :math:`\chi^2` is calculated using :math:`\log{(DataY)}-\log{(SimulatedY)}`
    * For **Fit Scale=Linear**: :math:`\chi^2` is calculated using :math:`DataY-SimulatedY`
13. Click the **Fit** button to start fitting the data which will open up a Fit_Progress_ dialog showing the number of iterations and the :math:`\chi^2` corresponding to the current iterations. The plot of the simulated data will also be updated with the parameters, corresponding to the iteration, as the fit progresses.
14. The iterations will continue until either the minimum :math:`\chi^2` is obtained or **maximum number of iterations (default=1000)**  are reached.
15. Once the fitting concluded a Fit_Results_ dialog will appear showing all the necessary details about the fitting.
16. At this point the user has freedom to either **Accept/Reject** the fitting results.

    * **Accepting** will update all the fitting parameters with the :math:`\chi^2`-minimized parameters
    * **Rejecting** will keep the parameters unaltered with the values before starting the fit.


.. _Fit_Progress:

.. figure:: ./Figures/Fit_Progress.png
    :figwidth: 30%

    Fit Progress Dialog

.. _Fit_Results:

.. figure:: ./Figures/Fit_Results.png
    :figwidth: 70%

    Fit Results Dialog


Categories and Functions
************************
Fit_Widget_ provides some of the useful functions/models which are categorized into several categories. Users can add their own categories and functions as per their requirements. The categories and functions/models are provided for the users to either use directly in their data analysis or learn from them to create their own.

* Backgrounds_
    1. PowerLaw_
* DLS_
    1. FirstCumulant_
* FormFactors_
    1. ContinuousSphere_
    2. CoreShellSphere_
    3. Ellipsoid_
    4. Formol_
    5. Sphere_
    6. SphericalShell_expDecay_
* GISAXS_
    1. Rod_Sphere_
* PeakFunctions_
    1. Gaussian_
    2. LogNormal_
    3. MultiPeaks_
* XRR_
    1. MultiSphereAtInterface_
    2. Parratt_
    3. SphereAtInterface_


.. _Backgrounds:

Backgrounds
-----------
This category includes smooth functions which are generally used as background models/functions for other functions.

.. _PowerLaw:

PowerLaw
++++++++
The power law function is :math:`y=Ax^n` .

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x		    Independent variable in ter form of a scalar or an array
    A		    Amplitude
    n           Exponent
    ==========  ========================================================================================================


.. _DLS:

DLS
---
This category includes functions related to analyze Dynamic Light Scattering data.

.. _FirstCumulant:

FirstCumulant
+++++++++++++
Calculates auto-correlation function for DLS measurements in water as a solvent

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x			Independent variable in the form of scalar or array of time intervals in microseconds
    tfac		factor to change from time units of from data to seconds
    lam         Wavelength of light in Angstroms
    n           Refractive index of solvent
    theta       Angle of the detector in degrees with respect to the beam direction
    T			Temperature of the solvent in kelvin scale
    D			Hydrodynamic diameter in Angstroms
    ==========  ========================================================================================================


.. _FormFactors:

FormFactors
-----------
This category includes Form Factors for Small Angle X-ray Scattering (SAXS) data.

.. _ContinuousSphere:

ContinuousSphere
++++++++++++++++
This calculates the form factor of a sphere with continuous electron density gradient along the radial direction

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable as a single or array of q-values in the reciprocal unit as R
    R           An array of radial locations
    rho         Electron density at the locations R
    Rsig        Width of the distribution of all the radial locations
    N           No. of points on which the distribution will be calculated
    dist        'Gaussian' or 'LogNormal'
    norm        Normalization constant
    bkg         Constant Bkg
    ==========  ========================================================================================================

.. _CoreShellSphere:

CoreShellSphere
+++++++++++++++
This calculates the form factor of a spherical core-shell structure with size and shell thickness distribution

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable as single or Array of q-values in the reciprocal unit as R and Rsig
    R           Mean radius of the solid spheres
    Rsig        Width of the distribution of solid spheres
    rhoc        Electron density of the core
    sh          Shell thickness
    shsig       Width of distribution of shell thicknesses
    rhosh       Electron density of the shell
    dist        Gaussian or LogNormal
    N           No. of points on which the distribution will be calculated
    rhosol      Electron density of the surrounding solvent/media
    ==========  ========================================================================================================

.. _Ellipsoid:

Ellipsoid
+++++++++
Calculates the form factor of an ellipsoid

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable as single or Array of q-values in the reciprocal unit as R1 and R2
    R1          Semi-minor of the ellipsoid
    R2          Semi-major axis of the ellipsoid
    rhoc        Electron density of the ellipsoid
    rhosol      Electron density of the surrounding media/solvent
    norm        Normalization constant
    bkg         Constant Bkg
    ==========  ========================================================================================================

.. _Formol:

Formol
++++++
This calculates the form factor for two different kinds of  molecules in cm^-1 for which the XYZ coordinates of the all the atoms composing the molecules are known

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable scalar or array of reciprocal wave vectors
    E           Energy of the X-rays at which the scattering pattern is measured
    fname1      Name with path of the .xyz file containing X, Y, Z coordinates of all the atoms of the molecule of type 1
    eta1        Fraction of molecule type 1
    fname2      Name with path of the .xyz file containing X, Y, Z coordinates of all the atoms of the moleucule of type 2
    eta2        Fraction of molecule type 2
    rmin        Minimum radial distance for calculating electron density
    rmax        Maximum radial distance for calculating electron density
    Nr          Number of points at which electron density will be calculated
    qoff        Q-offset may be required due to uncertainity in Q-calibration
    sol         No of electrons in solvent molecule (Ex: H2O has 18 electrons)
    sig         Debye-waller factor
    norm        Normalization constant which can be the molar concentration of the particles
    bkg         Background
    ==========  ========================================================================================================

.. _Sphere:

Sphere
++++++
Calculates the form factor of a solid sphere with size distribution

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable as array of q-values in the same reciprocal unit as R and Rsig
    R           Mean radius of the solid spheres
    Rsig        Width of the distribution of solid spheres
    dist        Gaussian or LogNormal
    N           No. of points on which the distribution will be calculated
    rhoc        Electron density of the particle
    rhosol      Electron density of the solvent or surrounding environment
    ==========  ========================================================================================================

.. _SphericalShell_expDecay:

SphericalShell_expDecay
+++++++++++++++++++++++
Calculates the form factor of exponentially decaying ion distribution around a spherical particle

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable in the form of a scalar or an array
    Rc          Radial distance in Angstroms after which the solvent contribution starts
    strho       Concentration of the ions of interest in the stern layer in Molar
    tst         Thickness of stern layer in Angstroms
    lrho        The maximum concentration of the diffuse layer in Molars
    lexp        The decay length of the diffuse layer assuming exponential decay
    rhosol      The surrounding bulk density
    norm        Density of particles in Moles/Liter
    bkg         Constant background
    ==========  ========================================================================================================

.. _GISAXS:

GISAXS
------
This category includes functions which deals with X-ray scattering patterns in Grazing incidence university.

.. _Rod_Sphere:

Rod_Sphere
++++++++++
This Provides rod scan from spherical objects dispersed on a substrate

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable as array of Qz values of rod scan
    R           Mean radius of spheres in inverse units of Qz
    Rsig        Width of distribution of spheres in inverse units of Qz
    dist        'Gaussian' or 'LogNormal'
    qc          Critical wave-vector for the substrate on which sphere are aranged
    qpar        In-plane wave-vector at which the rod was measured
    qparsig:    The width of the peak at which the rod was measured
    norm        Normalization constant
    bkg:        Constant background
    ==========  ========================================================================================================


.. _PeakFunctions:

PeakFunctions
-------------
This category includes peak related functions

.. _Gaussian:

Gaussian
++++++++
Provides Gaussian function`

    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable as scalar or array of values
    pos         Peak position
    wid         Width of the peak
    norm        Normalization constant
    bkg         Constant background
    ==========  ========================================================================================================

.. _LogNormal:

LogNormal
+++++++++
Provides log-normal function :math:`y=norm\exp{\left[\frac{-(\log{x}-\log{pos})^2}{2wid^2}\right]/\sqrt{2\pi}}/wid/x+bkg`
    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable as scalar or array of values
    pos         Peak position of the Gaussian part of the distribution
    wid         Width of the Gaussian part of the distribution
    norm        Normalization constant
    bkg         Constant background
    ==========  ========================================================================================================

.. _MultiPeaks:

MultiPeaks
++++++++++
Provides multipeak function with different background function
    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           independent variable in ter form of a scalar or an array
    power       1 for :math:`c_0+c_1 x+c_2 x^2+c_3 x^3+c_N x^N`, -1 for :math:`c0+c1/x+c2/x^2+c3/x^3+c_N/x^N`
    N           exponent of arbitrary degree polynomial i.e :math:`x^N` or :math:`1/x^N`
    c0          constant background
    c1          coefficient of the linear(x) or inverse(1/x) background
    c2          coefficient of the quadratic(:math:`x^2`) or inverse quadratic (:math:`1/x^2`) background
    c3          coefficient of the cubic bacground
    cN          coefficient of the :math:`x^N` or inverse :math:`1/x^N` background
    cexp        coefficient of the exponential background
    lexp        decay length of the exponential background
    mpar        The peak parameters where 'type': (0: Gaussian, 1: Lorenzian, 2: Step)
    ==========  ========================================================================================================


.. _XRR:

XRR
---
This category includes X-ray Reflectivity (XRR) related functions

.. _MultiSphereAtInterface:

MultiSphereAtInterface
++++++++++++++++++++++
Calculates X-ray reflectivity from multilayers of core-shell spherical nanoparticles assembled near an interface
    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable as array of wave-vector transfer along z-direction
    E           Energy of x-rays in inverse units of x
    Rc          Radius of the core of the nanoparticles
    rhoc        Electron density of the core
    Tsh         Thickness of the outer shell
    rhosh       Electron Density of the outer shell. If 0, the electron density the shell region will be assumed to be filled by the bulk phases depending upon the position of the nanoparticles
    rhoup       Electron density of the upper bulk phase
    rhodown     Electron density of the lower bulk phase
    sig         Roughness of the interface
    mpar        The layer parameters where, **Z0** : position of the layer, **cov** : coverage of the nanoparticles in the layer, **Z0sig** : Width of distribution of the nanoparticles in the layer
    rrf         1 for Fresnel normalized reflectivity and 0 for just reflectivity
    qoff        q-offset to correct the zero q of the instrument
    zmin        Minimum depth for electron density calculation
    zmax        Maximum depth for electron density calculation
    dz          Minimum slab thickness
    ==========  ========================================================================================================

.. _Parratt:

Parratt
+++++++
Calculates X-ray reflectivity from a system of multiple layers using Parratt formalism
    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Indpendendent variable as array of wave-vector transfer along z-direction
    E           Energy of x-rays in invers units of x
    mpar        The layer parameters where, d: thickness of each layer, rho:Electron ensity of each layer, beta: Absorption coefficient of each layer, sig: roughness of interface separating each layer. The upper and lower thickness should be always  fixed. The roughness of the topmost layer should be always kept 0.
    Nlayers     The number of layers in which the layers will be subdivided for applying Parratt formalism
    rrf         1 for Frensnel normalized refelctivity and 0 for just reflectivity
    qoff        q-offset to correct the zero q of the instrument
    ==========  ========================================================================================================

.. _SphereAtInterface:

SphereAtInterface
+++++++++++++++++
Calculates X-ray reflectivity from a system of nanoparticle at an interface between two media
    ==========  ========================================================================================================
    Parameters  Description
    ==========  ========================================================================================================
    x           Independent variable as array of wave-vector transfer along z-direction
    lam         Wavelength of x-rays in invers units of x
    Rc          Radius of nanoparticles in inverse units of x
    rhoc        Electron density of the nanoparticles
    cov         Coverate of the nanoparticles in %
    D           The lattice constant of the two dimensional hcp structure formed by the particles
    Zo          Average distance between the center of the nanoparticles and the interface
    decay       Assuming exponential decay of the distribution of nanoparticles away from the interface
    rho_up      Electron density of the upper medium
    rho_down    Electron density of the lower medium
    zmin        Minimum z value for the electron density profile
    zmin        Maximum z value for the electron density profile
    dz          Minimum slab thickness
    roughness   Roughness of the interface
    rrf         1 for Frensnel normalized refelctivity and 0 for just reflectivity
    qoff        Offset in the value of qz due to alignment errors
    ==========  ========================================================================================================


.. _Data_Dialog:

Data Dialog
***********
The dialog provides an interface to import and manipulate data for the Fit_Widget_.

.. figure:: ./Figures/Data_Dialog.png
    :figwidth: 70%

    Data Dialog in action as a stand-alone data viewer where a file **trial.txt** is imported.

    **Features**

    Data Dialog has several cool features:

    1. It can import any ascii file with tabulated data with the file extensions (**.txt**, **.dat**).
    2. It can show both the meta-data and the data present in the file provided that the data file is written in this particular format as mentioned in Data_File_Format_.
    3. After loading the file, both meta-data and the data can be added or removed or modified.
    4. New rows and columns can be added or removed for the data.
    5. Mathematical calculations can be done on the existing columns of the data which will be added as new columns. For data manipulations please follow the instructions in Data_Manipulation_.
    6. Provides 1D plots of all/some of the columns of the data. See Plotting_With_Data_Dialog_
    7. If the **☐Auto Update** is checked, any change in the data file will update the data automatically in the Data_Dialog_ along with **Plots**.
    8. Using the **☐Auto Update** feature a datafile can be visualized dynamically on change in the data within the file.

    **Usage**

    The dialog can be used as a dialog to import data in any other widgets like the Fit_Widget_. For example, within the Fit_Widget_ the Data_Dialog_ is used to manipulate the data by opening the dialog using the following function::

        from Data_Dialog import Data_Dialog

        def openDataDialog(self,item):
            fnum,fname=item.text().split('<>')
            data_dlg=Data_Dialog(data=self.dlg_data[fname],parent=self,plotIndex=self.plotColIndex[fname])
            data_dlg.dataFileLineEdit.setText(fname)
            if data_dlg.exec_():
                newFname=data_dlg.dataFileLineEdit.text()
                if fname==newFname:
                    self.plotColIndex[fname]=data_dlg.plotColIndex
                    self.dlg_data[fname]=copy.copy(data_dlg.data)
                    self.data[fname]=copy.copy(data_dlg.externalData)
                    self.plotWidget.add_data(self.data[fname]['x'],self.data[fname]['y'],yerr=self.data[fname]['yerr'],name=fnum)
                    self.update_plot()
                else:
                    item.setText('%s<>%s'%(fnum,newFname))
                    self.data[newFname]=self.data.pop(fname)
                    self.dlg_data[newFname]=self.dlg_data.pop(fname)
                    self.dlg_data[newFname]=copy.copy(data_dlg.data)
                    self.data[newFname]=copy.copy(data_dlg.externalData)
                    self.plotColIndex[newFname]=data_dlg.plotColIndex
                    self.plotWidget.add_data(self.data[newFname]['x'], self.data[newFname]['y'], yerr=self.data[newFname][
                        'yerr'],name=fnum)
                    self.update_plot()


    The dialog can also be used stand-alone to visualize, manipulate a data file with data and meta-data (see Data_File_Format_) by running this command in terminal::

            python Data_Dialog.py [filename]

    where [filename] is an optional argument to provide a file with full path.




.. _Data_File_Format:

Data File Format
----------------
The data file must be written in the format as shown below::

    #Any text about explaining the data
    #parameter1_name=parameter1_value
    #parameter2_name=parameter2_value
    #col_names=['col1','col2','col3']
    1   1   1
    2   4   8
    3   9   27

The first few lines with '#' can be used for stating the details of the file. Any meta-data needs to be saved should
follow the syntax as shown above as '#parameter1_name=parameter1_value'. When the above file is saved as **data_file.txt** and opened in Data_Dialog_, the data looks like this:

.. figure:: ./Figures/Data_Dialog_w_Data_File.png
    :figwidth: 70%

    Data Dialog in action in which it is loaded with **data_fle.txt**



.. _Data_Manipulation:

Data Manipulation
-----------------
In the Data_Dialog_ both the meta-data and data can be added/removed and edited with the following conditions:

1. If a file is imported with **col_names** as one of the meta-data, you can edit the values of the **col_names** but cannot remove it.
2. If the columns are already set for plotting in the **Plot Setup** tab you cannot remove the last two tabs.
3. When the Data_Dialog_ is not used within any other widgets, all the data columns can be removed.
4. When the Data_Dialog_ is used within any other widgets, one can delete all the columns except the remaining two.

Add New Data Column
+++++++++++++++++++
You can add new columns by clicking **Add Column** which will open up a Data_Column_Dialog_i_. Then the column values can be either:

1. An expression of **i** which can take integer values from a minimum value (default=0) to a maximum value (default=100). The expression can be any numpy expression like::

    i**2
    np.sin(i)+np.cos(i)
    np.exp(i*2)

 Here **np** is the imported **numpy** module. Please see Data_Column_Dialog_i_.

2. A numpy expression involving the data columns (col_A and col_B in this case) like::

    col.col_A+col.col_B
    np.sin(col.col_A)+np.cos(col.col_B)
    np.exp(col.col_A)

 Here a particular column is used as **col.Column_Name**. Please see Data_Column_Dialog_Columns_.

.. _Data_Column_Dialog_i:

.. figure:: ./Figures/Data_Column_Dialog_with_i.png
    :figwidth: 70%

    Data Column Dialog with numpy expression involving i

.. _Data_Column_Dialog_Columns:

.. figure:: ./Figures/Data_Column_Dialog_with_columns.png
    :figwidth: 70%

    Data Column Dialog with numpy expression involving columns

Remove Data Columns
+++++++++++++++++++
The columns can be removed by:

1. Selecting the entire column either by:

   * Selecting the first row of the column and select the last row with **SHIFT** button pressed.
   * Clicking the **Left-Mouse-Button** of the mouse over the first row of the column and keeping the **Left-Mouse-Button** pressed drag all the way to the last column.
   * All the columns can be selected by be clicking on a single data cell and press **CTRL-A**

2. Click the **Remove Column** button.

Add New Data Rows
+++++++++++++++++
A new row can be added by selecting a row where you want to add a row and click **Add Row**

Remove Data Rows
++++++++++++++++
Multiple rows can be removed by selecting multiple rows and click **Remove Rows**

Change Data Column Names
++++++++++++++++++++++++
The column names of the Data can be changed by changing the meta-data **col_names**.


.. _Plotting_With_Data_Dialog:

Plotting with Data Dialog
-------------------------
Data_Dialog_ can also be used for visualizing (within the Data Dialog) and selecting the data (for other widgets) to create 1D plots with errorbars. In order to plot the data needs to be at least a two column data. Once a two-column data is opened, in order to to visualize/select the data for plotting one needs to do the following:

    1) Click to the **Plot Setup** tab. See Data_Dialog_Plot_Setup_.
    2) Click **Add** button which will automatically add a row in the table.
    3) By default the row will be loaded with with *Data_0* as label, first and second column of the data as *X* and *Y* column, respectively.
    4) By default the *Yerr* column is selected as *None*.
    5) Many rows can be added in this way to visualize the data in Data_Dialog_ whereas when the Data_Dialog_ is used within other widgets only one row will be added by default.
    6) The data rows can be removed from the **Plot Setup** by selecting entire row (by clicking the row numbers at the extreme left) and clicking the **Remove** button.
    7) When using the Data_Dialog_ with any other widget, you cannot add or remove plots set for plotting. Though you can change the columns to plot.
    8) All the columns of the data will be available as drop down menu in each of the cells for selecting them as *X*, *Y*, and *Yerr* columns to plot.
    9) After adding the column, go to **Plots** tab within the Data_Dialog_ to visualize the data. See Data_Dialog_Plot_tab_.
    10) Both the X- and Y-axis labels will be updated with the column names selected in the **Plot Setup**.
    11) In order to switch between the log/linear scales of both the axes check/uncheck the **☐LogX** and **☐LogY** checkboxes.
    12) Line-width and the Symbol sizes can be tweaked by changing the **Line width** and **Point size** options.
    13) By default, the errorbars are not plotted and can be plotted by checking the **☐Errorbar** checkbox, provided that a column is already selected in *Yerr* column of the **Plot Setup**.

.. _Data_Dialog_Plot_Setup:
.. figure:: ./Figures/Data_Dialog_Plot_Setup.png
    :figwidth: 70%

    Plot Setup of Data Dialog

.. _Data_Dialog_Plot_tab:
.. figure:: ./Figures/Data_Dialog_Plot_tab.png
    :figwidth: 70%

    Plot tab of Data Dialog

.. _Function_Editor:

Function Editor
***************
The editor provides an interface to write new functions to be included
in the Fit_Widget_. The editor is enabled with python syntax highlighting.

.. figure:: ./Figures/Function_Editor.png
    :figwidth: 100%

    Function Editor

The editor starts with a template to write new functions. The template looks like this::

    ####Please do not remove lines below####
    from lmfit import Parameters
    import numpy as np
    import sys
    import os
    sys.path.append(os.path.abspath('.'))
    sys.path.append(os.path.abspath('./Functions'))
    sys.path.append(os.path.abspath('./Fortran_rountines'))
    ####Please do not remove lines above####

    ####Import your modules below if needed####



    class <*>: #Please put the class name same as the function name
        def __init__(self,x=0,mpar={}):
            """
            Documentation
            x           : independent variable in ter form of a scalar or an array
            """
            if type(x)==list:
                self.x=np.array(x)
            else:
                self.x=x
            self.__mpar__=mpar #If there is any multivalued parameter
            self.choices={} #If there are choices available for any fixed parameters
            self.init_params()

        def init_params(self):
            """
            Define all the fitting parameters like
            self.param.add('sig',value = 0, vary = 0, min = -np.inf, max = np.inf, expr = None, brute_step = None)
            """
            self.params=Parameters()

        def y(self):
            """
            Define the function in terms of x to return some value
            """
            self.output_params={}
            return self.x

A new function is basically as a python **class**. The *class name* determines the name of the function. As per the template there are three essential functions needs to be defined within the **class**:

1. **__init__** function
    . With this function we initialize all the parameters necessary for the class. The function atleast needs a value of an independent parameter **x** which by default takes scaler value **0**. **x** can take a scaler or array of values. **mfit** is a python dictionary to define multiple fitting parameters. In order to learn how to use **mfit** please look at the functions like: MultiSphereAtInterface_, Parratt_, and MultiPeaks_.

2. **init_params** function
    . With this function we define among all the parameters which one will be treated as our fitting parameters.

3. **y** function
    . This function actually returns the actual values of the function to be calculated by the **class**
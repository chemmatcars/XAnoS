.. _Fit_Widget:

Fit Widget
==========
This widget provides a data fitting platform which uses `LMFIT <https://lmfit.github.io/lmfit-py/>`_ python library.
Some of the commonly used functions are provided under different categories and the users can develop their own
categories and fitting functions by using an easy to use template within a Function_Editor_

.. figure:: ./Figures/Fit_Widget.png
    :figwidth: 100%

    Fit Widget in action


    **Features**

    1. Read and fit multiple data sets
    2. Functions are categorized under different types and experimental techniques
    3. Easy to add new categories and new functions within the categories
    4. Once the function is defined properly all the free and fitting parameters will be available within the GUI as tables.
    5. An in-built Function_Editor_ is provided with a easy to use template.
    6. A Data_Dialog_ is provided for importing and manipulating data files


    **Usage**

    Fit_Widget_ can be used as stand-alone python fitting package by running this in terminal::

        $python Fit_widget.py

    The widget can be used as a widget with any other python application.


.. _Data_Dialog:

Data Dialog
***********
The dialog provides an interface to import and manipulate data for the Fit_Widget_.

.. figure:: ./Figures/Data_Dialog.png
    :figwidth: 100%

    Data Dialog

The dialog can also be used stand-alone to visualize, manipulate a data file provided  running this command in terminal::

    $python Data_Dialog.py [filename]

where [filename] is an optional argument to provide a file with full path.

Data Dialog has several cool features:

Data Manipulation
-----------------






.. _Function_Editor:

Function Editor
***************
The editor provides an interface to write new functions to be included
in the Fit_Widget_. The is enabled with python syntax highlighting.

.. figure:: ./Figures/Function_Editor.png
    :figwidth: 100%

    Function Editor


      

.. _XAnoS_Batch_Processor:

XAnoS_Batch_Processor
=====================

.. contents:: Table of Contents
   :depth: 2

ASAXS data collection involves measurements of SAXS data at several energies below the energy edge of the element of interest from the sample, background, standard samples (Glassy Carbon (GC), Water etc). Sometimes SAXS data are also collected from empty container holding the sample and air background. After the data collection one needs to perform necessary background subtractions and absolute intensity normalizations for all the data. For this purpose, depending upon the sequence of data collection two batch processing widgets are developed:

1. :ref:`XAnoS_Batch_Processor_1`
2. :ref:`XAnoS_Batch_Processor_2`

.. _XAnoS_Batch_Processor_1:

XAnoS_Batch_Processor_1
***********************
This batch processor is designed to process (background subtraction and absolute intensity normalization) the SAXS data is collected **Serial mode** from the system of interest, the background, the intensity standard (GC or Water), the empty container and the air background. **Serial mode** means SAXS data will be collected at all the energies of interest for a sample before moving to the next sample. Visually the data is collected in the fashion shown below.

.. figure:: ./Figures/Serial_mode.png
    :figwidth: 50%

    **Serial mode** of ASAXS data collection. The dashed lines with arrows indicates the steps for measuring **Empty** ad **Air**  are optional.

**Usage**

:ref:`XAnoS_Batch_Processor_1` can be used stand-alone widget by running the command in terminal::

    python XAnoS_Batch_Processor_1.py


.. figure:: ./Figures/ASAXS_Batch_Processor_1.png
    :figwidth: 100%

    **ASAXS Batch Processor 1** in action.


.. _XAnoS_Batch_Processor_2:

XAnoS_Batch_Processor_2
***********************
This batch processor is designed to process (background subtraction and absolute intensity normalization) the SAXS data is collected **Parallel mode** from the system of interest, the background, the intensity standard (GC or Water), the empty container and the air background. **Parallel mode** means SAXS data will be collected for all the samples at a same energy and then change to different energies. Visually the data is collected in the fashion shown below.

.. figure:: ./Figures/Parallel_mode.png
    :figwidth: 50%

    **Parallel mode** of ASAXS data collection. The collection of data from **Empty** and **Air** are optional.


**Usage**

:ref:`XAnoS_Batch_Processor_2` can be used stand-alone widget by running the command in terminal::

    python XAnoS_Batch_Processor_2.py

.. figure:: ./Figures/ASAXS_Batch_Processor_2.png
    :figwidth: 100%

    **XAnoS_Batch_Processor_2** in action.

In **Parallel mode**, generally the data are collected within a same folder with same filename and different filenumber such as **filename_0001.txt**, **filename_0002.txt**,...etc, for all the samples, backgrounds, ... etc. In order to process the data with :ref:`XAnoS_Batch_Processor_2` please follow these simples steps:

1. Click **Select** button Open the first filename of the whole ASAXS data series. This will add the *Filename* with the full *FilePath* (no file filenumbers) to the **First Sample Name** of the widget.
2. Provide file numbers for data files corresponding to the first sample, background and standard sample data in the **First Sample Nums** (Default=1), **First Bkg Num** (Default=2), and **First Std Num** (Default=3), respectively.
3. Provide the thicknesses (in *centimeters*) of the  sample, background, and standard sample in the **Sample Thickness (cm)**, **Background Thickness (cm)**, and **Standard Thickness (cm)**.
4. Provide the numbers of Energy points done for each of the sample as **Energy Npts** (Default=20).
5. Provide how many times a data is taken per sample per energy in **Repeat** (Default=1)
6. Provide which standard sample to use between **GC** and **Water** in **Standard Sample** (Default=GC).
7. Provide the **Q-range** in **Xmin:Xmax** (Default=0.1:0.25) in Å\ :sup:`-1` at which the standard sample data will be compared with the absolute intensity values obtained from `NIST <https://www-s.nist.gov/srmors/view_detail.cfm?srm=3600>`_ to get the ASAXS data in absolute intensity scale.
8. Select the interpolation method between **linear|quadratic|cubic** for interpolating the data as needed to do the batch processing.
9. Click **Process** button to start processing.
10. After the processing is done the processed ASAXS data from the system of interest will be plotted in plot.
11. The processed data will be saved within a new subfolder named **bkgsub**.
12. Within the **bkgsub** subfolder two kinds of files will be created in the following format:

    * *filename_filenumber_bsub.txt* : These are background subtracted files of the system of interest
    * *filename_filenumber_bsub_proc.txt* : These are background subtracted and absolute scale normalized data obtained after the processing. These files will be used further for ASAXS analysis using :ref:`XAnoS_Components`.


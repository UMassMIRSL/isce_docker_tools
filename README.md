[![Language](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/)

# ISCE Docker Tools
https://github.com/sgk0/isce_docker_tools

https://github.com/UMassMIRSL/isce_docker_tools

We plan to release a few workflows that utilize an ISCE image of docker that should be able to run with minimal user inputs and need for accessing/modifying the ISCE image.

We provide
  1. A docker image of ISCE (version 2.3.1), which may consist of a few new python scripts plus some minor modifications of ISCE, as needed to complete the workflows. This docker image should be able to run any of the other ISCE workflows correctly, as we tried to make minimal changes to existing ISCE modules. 
  2. Python workflows, controlled via run_ctrl.py script and several other python scripts that are launched sequentially. Users may modify them as needed.
  - A workflow for co-registration and radiometric terrain correction of UAVSAR MLC time series data ("uavsar_rtc_mlc").
  - A workflow for finding and downloading UAVSAR HDF5 data and annotation files (no need for ISCE). This is a Jupyter Notebook ("0_download_hf5slc.ipynb") located in "hdf5_download_and_mlc_production"
  - A workflow that reads the SLC data contained in the UAVSAR/NISAR hdf5 formatted file and produces UAVSAR MLC .zip files ("hdf5_download_and_mlc_production"). that can be directly used as inputs to  the uavsar_rtc_mlc workflow. The tools have been tested with the 'CX' and dithered 'CD', 'CG' products at the 129 (20 + 5 MHz) and 138 (40 + 5 MHz) modes.
  


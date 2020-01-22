# ISCE Docker Tools

We plan to release a few workflows that utilize an ISCE image of docker that should be able to run with minimal user inputs and need for accessing/modifying the ISCE image.

We provide
  1. A docker image of ISCE (version 2.3.1), which may consist of a few new python scripts plus some minor modifications of ISCE, as needed to complete the workflows. This docker image should be able to run any of the other ISCE workflows correctly, as we tried to make minimal changes to existing ISCE modules. 
  2. Python workflows, controlled via run_ctrl.py script and several other python scripts that are launched sequentially. Users may modify them as needed. Currently, we only have a workflow for co-registration and radiometric terrain correction of UAVSAR MLC imagery. This is in the uavsar_rtc_mlc folder. We're also planning to make a similar workflow but using Sentinel-1 SLC data as input sometime in the future.


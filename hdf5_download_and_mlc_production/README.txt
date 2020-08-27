ISCE Docker Tools for converting NISAR/UAVSAR hdf5 data to MLCs

0_download_hdf5slc.ipynb UAVSAR .h5 search and download tool

This tool is a Jupyter notebook that does not require ISCE, and should at be run cell by cell each time download of a new dataset is attempted.
This is because the references to the available file versions may often be wrong and require 'manual' updates. See the cell titled 
"### We may need to repair some data references". The tool will also obtain annotation files for UAVSAR, because they have the information needed to import
UAVSAR data into ISCE. Eventually, one probably could instead get that information from the hdf5, but this is not addressed as the annotation files are readily available.

After the directory structure was created and files finished downloading ("0_download_hdf5slc.ipynb"), update the UAVSAR flightline and product information in run_ctrl according to selected values in "0_download_hdf5slc.ipynb". Then you can launch the docker container to obtain the mlc zipped files from the .5h. Please note that although the data may be CX, CG or CD and different products, the mlcs had been renamed to conform with other UAVSAR standard and readily work with the RTC processing tool. 

For subsequent RTC processing and geocoding, swap the set of RTC realted .py scripts (including run_ctrl.py) with the used in this tool. Then launch docker again.

PS: 
By default, the intermediate data for producing the mlcs is kept, to assist in troubleshooting. 
I recommend to delete the folders after each set of MLCs are produced, to save on storage.

Docker command line example
e.g. if the run control script is in /data1/uavsar/uavsar_h5slc2mlc_rev/docker_new_runs run:

docker run -it --rm -v /data1/uavsar/uavsar_h5slc2mlc_rev:/work/uavsar_mlcproc 667c090f09b5

Becuase ISCE runs as root, on linux all outputs are set to user and group root. 

You can fix it by 
sudo chown <user> *.zip
sudp chown <group> *.zip




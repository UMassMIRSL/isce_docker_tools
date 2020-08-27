# ISCE Docker Tool (IDT) Workflow for converting NISAR/UAVSAR hdf5 data to zipped MLCs just as provided by JPL

## 1 Set up the correct folder structure for the IDT
See https://github.com/sgk0/isce_docker_tools/tree/master/uavsar_rtc_mlc

## 2 0_download_hdf5slc.ipynb, the UAVSAR .h5 search and download tool

This tool is a Jupyter notebook that does not require ISCE, and should at be run cell by cell each time download of a new dataset is attempted.
This is because the references to the available file versions may often be wrong and require 'manual' updates. See the cell titled 
"### We may need to repair some data references". The tool will also obtain annotation files for UAVSAR, because they have the information needed to import
UAVSAR data into ISCE. Eventually, one probably could instead get that information from the hdf5, but this is not addressed as the annotation files are readily available.

After the directory structure was created and files finished downloading ("0_download_hdf5slc.ipynb"), it is important to update the UAVSAR flightline and product information in run_ctrl according to selected values in "0_download_hdf5slc.ipynb". 

## 3 h5tomlc.py 

You may now launch the docker container for processing the hdf5 data to zipped MLCs. Please note that although the data may be CX, CG or CD and different products, the mlcs had been renamed to conform with other UAVSAR products so that it readily works with the RTC processing scripts in "uavsar_rtc_mlc". 

Please note, you may continue data processing in the same docker_new_runs folder, but will need to swap the set of RTC relted .py scripts (including run_ctrl.py) with the ones used in this tool. Then launch docker again.

Docker command line example
e.g. if the run control script is in /data1/uavsar/uavsar_h5slc2mlc_rev/docker_new_runs run:

docker run -it --rm -v /data1/uavsar/uavsar_h5slc2mlc_rev:/work/uavsar_mlcproc 667c090f09b5
where /data1/uavsar/uavsar_h5slc2mlc_rev needs to be replaced to match the path to the /docker_new_runs folder
where 67c090f09b5 needs to be replaced with whichever number corresponds to the IDT image installed on local system

PS: By default, the intermediate data for producing the mlcs is kept, to assist in troubleshooting, but I recommend to delete the folders after each set of MLCs are produced after you have the zipped MLCs

PS2: Because ISCE runs as root, on linux all outputs are set to user and group root. 

You can fix it by 
sudo chown <user> *.zip
sudo chown <group> *.zip

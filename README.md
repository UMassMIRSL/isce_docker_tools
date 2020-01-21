MIRSL UAVSAR MLC STACK RTC processor
====================================

This workflow uses two or more UAVSAR MLC datasets as input to generate a co-registered stack of images that had been corrected for viewing geometry and terrain effects (gamma0).
The workflow is to be used in conjunction with a Docker container that has a slightly modified version of ISCE installed on it, to facilitate MLC processing. The container is available at [website](). More details on ISCE is available at [website](https://github.com/isce-framework/isce2).

Pre-requisites
- an EARTHDATA account at [website](https://urs.earthdata.nasa.gov/), used to download the digital elevation model files
- Docker. To install Docker on your system, follow directions at [website](https://docs.docker.com/)

(A) Install the docker image of ISCE (modified for RTC)
(1) download the Docker_Install folder from Box
(2) unzip folder, cd into "Docker_Install" and run "docker build -t uavsar_mlc_rtc ." from command line
This will install a Docker image on your system. 
(3) "docker image ls", and note the IMAGE ID value (copy/paste)

(B) Set-up of the processor on your system
(1) Pick a directory on the local machine where work is to be done (<localdir>). e.g.  $HOME/work and do the following:
    (a) create a folder named "docker_new_runs". This is because the docker image was built using WORKDIR $HOME/uavsar_mlcproc/docker_new_runs. 
        This can be overridden by (i) rebuilding the Docker image with different value for WORKDIR; (ii) override on the command line with the option -w="$HOME/uavsar_mlcproc/XXX" (XXX is dir name)
    (b) copy the workflow .py scripts (in workflow_scripts dir on box) into "docker_new_runs" (i.e. 0_ann_dem.py, 1_iscestack.py, 2_resamp_pol.py, 3_uavsar_pp_mlc.py, run_ctrl.py)
    (c) You will need to create a file named .netrc in "docker_new_runs"
        "machine urs.earthdata.nasa.gov login <login> password <password>"
        -Windows doesn't easily let you make filenames starting with '.' but the below line works (run from a cmd window)
        "echo machine urs.earthdata.nasa.gov login <login> password <password> > .netrc
         (More information at [website](https://lpdaac.usgs.gov/resources/e-learning/how-access-lp-daac-data-command-line/))
    (d) Place the MLC UAVSAR zip files (don't unzip them) in "docker_new_runs", e.g. from https://uavsar.jpl.nasa.gov/cgi-bin/data.pl

(2) Data processing (skip b, because you will build the image from scratch using the data on the Box folder; if running on linux, please note comment d)
    (a) launch Docker
    (b) if image not on local system
      b.1 install it using "docker pull skraatz00/mirsl_isce_rtc_v0"
      b.2 if building from docker file "docker build -t imgname ." where imgname is a custom name
    type docker image ls and note the IMAGE ID for skraatz00/mirsl_isce_rtc_v0]
    (c) in a terminal, type
    "docker run -it --rm -v <localdir>:/work/uavsar_mlcproc <IMAGE ID>"
    
    (d) If you are running this on linux: you will get a permission error. This is because docker the container is running as a different user (i.e. it is root) and creates new directories and files
     which will be locked if users don't match. A workaround is to create the directory structure that will be used ahead of time; or to let step (c) fail and then chmod the directory 
     <localdir>/flightName and its subdirectories to the correct permissions. It is not ideal that the container runs as root but it is in line with how they are set up for cloud processing. 
     In addition to the python scripts, we provide the dockerfile with the ancillary updated ISCE data required to run the MLC processor so that users may build the container to suit their needs.

Note: If you want to use another DEM, an example for using OpenTopography is included in the 0_ann_dem.py script in the elif clause starting line 291


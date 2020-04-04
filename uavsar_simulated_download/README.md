# Tool for downloading simulated NISAR data as input to isce_docker_tools

This tool downloads the files specified as per the links provided in wget.txt. 
  1. Go to https://uavsar.jpl.nasa.gov/cgi-bin/data.pl
  2. Check the box 'Simulated NISAR' and search
  3. Select the dataset of interest (view)
  4. Scroll to 'wget commands to download data' and copy the links to the .ann and .mlc files (minus 'wget ') and paste into wget.txt
  5. 'python dl_uavsar_sim_wget.py'

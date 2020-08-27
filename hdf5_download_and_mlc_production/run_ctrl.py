#This script will look through the file_repository_new_runs folder for UAVSAR MLC zip files; create a new project structure for each;
#and copy the python scripts and move the .mlc.zip files to the appropriate subfolders. Then it will run each script in sequence.

import os, shutil, subprocess, time
import numpy as np
from h5tomlc import makemlc

#-----USER DEFINED SETTINGS
CAMPAIGN='NISARP' #or 'NISARA' for AM and 'NISARP' for PM
SITE='25006'
PROD='129' #129 = global 20 & 5 MHz, 138 = US Ag 40 & 5 MHz
PROD2='CG' #CX = normal, CG = dithered-gaps, CD = dithered-no-gaps
channels='B' #A is (HH,HV) and has higher frequency compared to B (20 or 40 MHz vs 5 or 20 MHz); whereas B is (VH,VV). PROD='143' has both channels at 20 MHz
symmetrize = 1 #use UAVSAR's approach for symmetrizing HV and VH
#symmetrization: based on the principle of reciprocity HV should give the same result of VH. But due to instrument limitations (e.g. thermal noise/channel imbalance/cable lengths)
#vh and hv will not match in practice. The symmetrization is a statistical approach for reducing the imbalance, where the entire image statistics are used as inputs
#to determine correction factors for magnitude and phase for this imbalance. As result, the HV and VH channels will become much more similar on the whole; but there may still be some clear
#differences at the level of individual pixels.
#-----------------

#step0
cwd = os.getcwd()
zerodir = os.path.join(cwd, SITE, PROD, PROD2) #'0_make_ann_dem'
projects = sorted([f for f in os.listdir(zerodir) if f.endswith('.h5')])
maindir, thisdir = os.path.split(cwd)

for num, val in enumerate(projects):
    t0 = time.time()
    print('Processing %s' % (val))
    makemlc(CAMPAIGN, SITE, PROD, PROD2, channels, symmetrize, num)
    t1 = time.time()
    print('Processing took %s seconds' %(np.round(t1-t0,3)))

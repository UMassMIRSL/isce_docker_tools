#!/usr/bin/env python3
#this file should be placed inside the project root directory, in the folder 1_do_coreg_only_on_HHHH
#purpose 1 is to assign radar to lat/lon only once, for the masterSlc ('HHHH'), 
#purpose 2 is to iterate over all of the slaveSlc files (only 'HHHH' values, but for different date) to get offset values for each date
#in the next step, 2_resampdir, every slaveSlc will be resampled to the coordinates of the masterSlc

import os, subprocess
#--------------Set params-----
cwd = os.getcwd()
prjdir, step1dir = os.path.split(cwd)
zerodir = os.path.join(prjdir, '0_make_ann_dem')
isceprocdir = os.path.join(prjdir, 'SLC')
offsetsdir = os.path.join(prjdir, 'offsets')
mSlcl = sorted([f for f in os.listdir(zerodir) if f.endswith('_mlc.zip')])
mct = mSlcl[0].split('_')[7]
masterSlc = mSlcl[0][:-14]+'HHHH_CX_'+mct+'.slc'
runtopo = 1 #0 means don't need to run it, because this had been done already

if os.path.exists(os.path.join(prjdir,'merged', 'geom_master', 'hgt.rdr')):
    print('=====Skipping topo.py, it already ran=====')
    runtopo = 0
#-------------------------------

demn = [f for f in os.listdir(zerodir) if f.endswith('dem.wgs84')]
masterdate = '20'+masterSlc.split('_')[4]
flightName = masterSlc.split('_')[0]

if runtopo == 1:
    print('=======topo.py=======')
    subprocess.call(['topo.py', '--master', os.path.join(isceprocdir,masterSlc[:-4]), '--dem', os.path.join(zerodir,demn[0]), '--output', os.path.join(prjdir,'merged','geom_master'), '--native'])
        #topo.py is the forward geometry mapping of the master stack, from radar to lat/lon coordinates

#---------------------------------------LOOP START (over each slave and pol)-----------------------#
if os.path.exists(offsetsdir):
    existing_slc = [f for f in os.listdir(offsetsdir) if f.startswith(flightName)]
    newslavelist = sorted([f for f in os.listdir(isceprocdir) if f.startswith(flightName) and masterdate[2:] not in f])
    slavelist = list(set(newslavelist) - set(existing_slc))
else:
    slavelist = sorted([f for f in os.listdir(isceprocdir) if f.startswith(flightName) and masterdate[2:] not in f])

if len(slavelist)==0:
    print('=====Skipping geo2rdr.py, no new slc images=====')
else:
    print('=====Adding new slc images to stack, %s' %(slavelist))

for num, val in enumerate(list(slavelist)):
    print('=======geo2rdr.py=======')
    subprocess.call(['geo2rdr.py', '--master', os.path.join(isceprocdir,masterSlc[:-4]), '--slave', os.path.join(isceprocdir,val), '--geom', os.path.join(prjdir,'merged','geom_master'), '--outdir', os.path.join(prjdir, 'offsets', val), '--native'])
        #geo2rdr.py is the reverse geometry mapping, maps slave onto the master. 
        #it also finds/reports the offsets between the images

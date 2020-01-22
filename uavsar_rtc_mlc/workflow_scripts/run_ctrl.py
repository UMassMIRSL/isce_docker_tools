#This script will look through the file_repository_new_runs folder for UAVSAR MLC zip files; create a new project structure for each;
#and copy the python scripts and move the .mlc.zip files to the appropriate subfolders. Then it will run each script in sequence.

import os, shutil, subprocess, time
import numpy as np
#---user specific input---#
shpname = 'stoneville_west_ag' #the shapefile dir placed into new_runs containing shapefile with matching EPSG to the geotiffs (UTM zones) containing shapefiles named shpname.shp shpname.dbf etc
#---end user specify input---#

#step0
zerodir = '0_make_ann_dem'
zerofn = '0_ann_dem.py'
#zerofn = '0_make_ann_dem_move_v2.py'

#step1
coregdir = '1_do_coreg_only_on_HHHH'
coregfn = '1_isce_stack.py'

#step2
resampdir = '2_resampdir'
resampfn = '2_resamp_pol.py'
#resampfn = '2_resamp_pol_v1.py'

#step 3
postprocdir = '3_postprocess_stacks'
postprocfn = '3_uavsar_pp_mlc_v2.py'

cwd = os.getcwd()
os.chdir(cwd)
shutil.copy(os.path.join(cwd, '.netrc'), '/work/.netrc')

maindir, thisdir = os.path.split(cwd)

mlczip = [f for f in os.listdir() if f.endswith('_mlc.zip')]

#group the mlc.zip by project...those that start with the same two parameters
prjlst = []
for numd, vald in enumerate(mlczip):
    prj = vald.split('_')[0]+'_'+vald.split('_')[1]
    prjlst.append(prj)

projects = list(set(prjlst))
print('There are %s projects (%s)' % (len(projects), projects))

for num, val in enumerate(projects):
    prjfiles = [f for f in os.listdir() if f.startswith(val)]
    print('Project %s consists of %s flightlines' % (projects[num], len(prjfiles)))
    prjdir = os.path.join(maindir, projects[num])
    
    if not os.path.exists(prjdir):
        os.mkdir(prjdir)
        os.mkdir(os.path.join(prjdir,zerodir))
        shutil.copy(os.path.join(cwd, zerofn), os.path.join(prjdir, zerodir, zerofn))
        os.mkdir(os.path.join(prjdir,coregdir))
        shutil.copy(os.path.join(cwd, coregfn), os.path.join(prjdir, coregdir, coregfn))
        os.mkdir(os.path.join(prjdir,resampdir))
        shutil.copy(os.path.join(cwd, resampfn), os.path.join(prjdir, resampdir, resampfn))
        os.mkdir(os.path.join(prjdir,postprocdir))
        shutil.copy(os.path.join(cwd, postprocfn), os.path.join(prjdir, postprocdir, postprocfn))
    
    
    for numd, vald in enumerate(prjfiles):
        shutil.move(os.path.join(cwd, vald), os.path.join(prjdir, zerodir, vald))
    
    t0 = time.time()
    print('Running %s for project %s' % (zerofn, val))
    os.chdir(os.path.join(prjdir, zerodir))
    aa = os.getcwd()
    subprocess.call([os.path.join(aa,zerofn)])
    t1 = time.time()
    print('Running %s for project %s' % (coregfn, val))
    os.chdir(os.path.join(prjdir, coregdir))
    aa = os.getcwd()
    subprocess.call([os.path.join(aa, coregfn)])
    t2 = time.time()
    print('Running %s for project %s' % (resampfn, val))
    os.chdir(os.path.join(prjdir, resampdir))
    aa = os.getcwd()
    subprocess.call([os.path.join(aa,resampfn)])
    t3 = time.time()
    print('Running %s for project %s' % (postprocfn, val))
    os.chdir(os.path.join(prjdir, postprocdir))
    aa = os.getcwd()
    subprocess.call([os.path.join(aa, postprocfn)])
    t4 = time.time()
    
    print('0_make_ann_dem took %s seconds' %(np.round(t1-t0,3)))
    print('1_coreg took %s seconds' %(np.round(t2-t1,3)))
    print('2_resampdir took %s seconds' %(np.round(t3-t2,3)))
    print('3_postprocess took %s seconds' %(np.round(t4-t3,3)))
    print('Processing took %s seconds' %(np.round(t4-t0,3)))
    os.chdir(cwd)


#!/usr/bin/env python3
import isce, shelve, os, subprocess, shutil
#--------------Set params-----
cwd = os.getcwd()
resampdir = cwd
prjdir, xxx = os.path.split(cwd)
zerodir = os.path.join(prjdir, '0_make_ann_dem')
isceprocdir = os.path.join(prjdir, 'SLC')
offsetsdir = os.path.join(prjdir, 'offsets')
writexmldir = os.path.join(resampdir, 'writexml')
postprocdir = os.path.join(prjdir, '3_postprocess_stacks')
mSlcl = sorted([f for f in os.listdir(zerodir) if f.endswith('_mlc.zip')])
mct = mSlcl[0].split('_')[7]
masterSlc = mSlcl[0][:-14]+'HHHH_CX_'+mct+'.slc'
#-------------------------------

flightName = masterSlc.split('_')[0]
p2res = [f for f in os.listdir(resampdir) if f.startswith(flightName)]

#read the masterslc data to get its length and width 
shelvefile = os.path.join(isceprocdir,masterSlc[:-4],'data')
with shelve.open(shelvefile, flag = 'r') as db:
    frame = db['frame']
length = frame.numberOfLines
width = frame.numberOfSamples
db.close()

if not os.path.exists(writexmldir):
    os.mkdir(writexmldir)
if not os.path.exists(postprocdir):
    os.mkdir(postprocdir)

if len(p2res)==0:
    print('=====Skipping resampleSlc.py, no new slc images=====')

for num, val in enumerate(p2res):
    print('=======resampleSlc.py for: ' +val+'=======')
    crosstalk = val.split('_')[7]
    subprocess.call(['resampleSlc.py', '--master', os.path.join(isceprocdir,masterSlc[:-4]), '--slave', os.path.join(resampdir,val), '--coreg', os.path.join(resampdir,'coreg',val), '--offsets', os.path.join(offsetsdir,val[:-10]+'HHHH_CX_'+crosstalk), '--noflat'])

for num, val in enumerate(p2res):
    shutil.move(os.path.join(resampdir, 'coreg', val, val+'.slc'), os.path.join(resampdir, writexmldir, val+'.slc'))
    shutil.copy(os.path.join(resampdir, val, val+'.ann'), os.path.join(writexmldir, val+'.ann'))
    shutil.rmtree(os.path.join(resampdir,val))

#the following is to update the dimensions of the slave .ann files so that they match the dims of the master
os.chdir(writexmldir)
annl = [f for f in os.listdir('.') if f.endswith('.ann')]
for num, val in enumerate(annl):
    with open(val,'r') as ins:
        linelist = []
        for line in ins:
            if 'mlc_pwr.set_rows (pixels) = ' in line:
                line = 'mlc_pwr.set_rows (pixels) = '+str(length)+'\n'
            if 'mlc_pwr.set_cols (pixels) = ' in line:
                line = 'mlc_pwr.set_cols (pixels) = '+str(width)+'\n'
            if 'slc_1_1x1_mag.set_rows (pixels) = ' in line:
                line = 'slc_1_1x1_mag.set_rows (pixels) = '+str(length)+'\n'
            if 'slc_1_1x1_mag.set_cols (pixels) = ' in line:
                line = 'slc_1_1x1_mag.set_cols (pixels) = '+str(width)+'\n'
            linelist.append(line)
    
    with open(val, 'w') as f:
        for item in linelist:
            f.write("%s" %item)

subprocess.call(['writexml_sk.py', '-i', '.', '-o', postprocdir, '-p', '1', '-m', '0'])
    #this moves all the files into the postprocessing directory, -p 1 means to put all of them into common folder

if os.path.exists(os.path.join(cwd,'coreg')):
    shutil.rmtree(os.path.join(cwd,'coreg'))

#!/usr/bin/env python3
import os, subprocess, shutil, csv, zipfile
import pandas as pd
import numpy as np
import datetime as dt
from osgeo import gdal

####------Set Params--------####
cwd = os.getcwd()
prjdir, step1dir = os.path.split(cwd)
zerodir = os.path.join(prjdir, '0_make_ann_dem')
mSlcl = sorted([f for f in os.listdir(zerodir) if f.endswith('_mlc.zip')])
masterSlc = mSlcl[0][:-14]+'HHHH_CX_01.slc'
postprocdir = os.path.join(prjdir, '3_postprocess_stacks')
flightName = masterSlc.split('_')[0]

####------go through each dir move geo.tif--------####
dirlst = ['HHHH', 'HVHV', 'VVVV']

for numd, vald in enumerate(dirlst):
    if not os.path.exists(os.path.join(cwd,vald)):
        os.mkdir(os.path.join(cwd,vald))

dirnm = [f for f in os.listdir(postprocdir) if os.path.isdir(os.path.join(postprocdir, f)) and f.startswith(flightName)]
for num, val in enumerate(dirnm):
    obsdir = os.path.join(postprocdir,val)
    os.chdir(obsdir)
    
    tiffnames = [f for f in os.listdir(obsdir) if f.endswith('_geo.tif')]
    
    for numd, vald in enumerate(dirlst):
        dn = [f for f in tiffnames if vald in f]
            #dn[0] is the file to be moved
        
        if len(dn) > 0:
            mvd = os.path.join(cwd, vald)
            shutil.move(os.path.join(obsdir,dn[0]), os.path.join(mvd, dn[0]))

        #rmn = [f for f in os.listdir() if f.endswith(sw)]
        #for numd2, vald2 in enumerate(rmn):
        #    os.remove(vald2)

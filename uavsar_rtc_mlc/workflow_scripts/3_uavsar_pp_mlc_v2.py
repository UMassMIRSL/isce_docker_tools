#!/usr/bin/env python3
import os, subprocess, shutil, csv, zipfile, utm
import pandas as pd
import numpy as np
import datetime as dt
from osgeo import gdal

####------User Set Params--------####
complexmag = 0  #compute magnitude of complex valued data
geocode = 1     #geocode real valued images
xyres_out = '10,10'   #resolution in meters
intmethod = 'bilinear'#interpolation method; e.g. 'near' or bilinear

####------Set Params--------####
cwd = os.getcwd()
postprocdir = cwd
prjdir, step1dir = os.path.split(cwd)
zerodir = os.path.join(prjdir, '0_make_ann_dem')
geomdir = os.path.join(prjdir, 'merged', 'geom_master')
mSlcl = sorted([f for f in os.listdir(zerodir) if f.endswith('_mlc.zip')])
mct = mSlcl[0].split('_')[7]
masterSlc = mSlcl[0][:-14]+'HHHH_CX_'+mct+'.slc'
flightName = masterSlc.split('_')[0]

dirnm = [f for f in os.listdir(postprocdir) if os.path.isdir(f) and f.startswith(flightName)]
sw = ['HHHH', 'HVHV', 'VVVV']
sw2 = ['HHHV', 'HHVV', 'HVVV']

#######----------Calculate Magnitudes--------------#####
for num, val in enumerate(dirnm):
    nd = os.path.join(postprocdir, val)
    os.chdir(nd)
    mlcnm = [f for f in os.listdir(nd) if f.endswith('.mlc')]
    if len(mlcnm) < 3:
        convertl = [f for f in os.listdir('.') if any(x in f for x in sw) and f.endswith('.slc')]
        for numd, vald in enumerate(convertl):
            print('-----------Calculating Image Magnitude '+vald+'--------------')
            eq = '--e=sqrt(a*conj(a))'
            ps1 = '--a='+vald
            subprocess.call(['imageMath.py', eq, ps1, '-o', vald[:-3]+'mlc', '-t','FLOAT', '-s', 'BIL']) #BIL BIP
            os.remove(vald)
            os.remove(vald+'.xml')
            os.remove(vald+'.vrt')

if complexmag == 1:
    for num, val in enumerate(dirnm):
        nd = os.path.join(postprocdir, val)
        os.chdir(nd)
        mlcnm = [f for f in os.listdir(nd) if f.endswith('.mag')]
        if len(mlcnm) == 0:
            convertl = [f for f in os.listdir('.') if any(x in f for x in sw2) and f.endswith('.slc')]
            for numd, vald in enumerate(convertl):
                print('-----------Calculating Image Magnitude '+vald+'--------------')
                eq = '--e=sqrt(a*conj(a))'
                ps1 = '--a='+vald
                subprocess.call(['imageMath.py', eq, ps1, '-o', vald[:-3]+'mag', '-t','FLOAT', '-s', 'BIL']) #BIL BIP
                #os.remove(vald) 
                #os.remove(vald+'.vrt')
                #os.remove(vald+'.xml')
                    #commented to keep complex valued file, it will have the intermediate name of .slc (but it is equivalent UAVSAR .mlc)

os.chdir(postprocdir)

def setdtype(fni):
    if any(x in vald for x in sw):
        datatype = 'FLOAT'
        intlv = 'BIL'
    elif any(x in vald for x in sw2) and '.mag' in fni:
        datatype = 'FLOAT'
        intlv = 'BIL'
    else:
        datatype = 'CFLOAT'
        intlv = 'BIP'
    return datatype, intlv

##note now we have 3 slc files ; 3 mag files, 3 mlc files
######----------RTC Processing steps--------------#####
for num, val in enumerate(dirnm):
    nd = os.path.join(postprocdir, val)
    os.chdir(nd)
    slcnm = [f for f in os.listdir(nd) if f.endswith('.mlc') or f.endswith('.mag')]
    sscn = [f for f in os.listdir(nd) if f.endswith('.slc')] #as long as there are files named .slc in dir, it still needs to be processed

    if len(sscn) > 0:
        sscn.extend(slcnm)
        for numd, vald in enumerate(sscn):
            datatype, intlv = setdtype(vald)
            if vald.endswith('.mag'):
                imgoutname = vald[:-4]+'_mag'
            else:
                imgoutname = vald[:-4]
            
            print('-----------Calculate GAMMA0--------------')
            eq = '--e=(a/cos(f_0*PI/180.))*(tan(b_1*PI/180.)/tan(f_0*PI/180.))*(c==0)'
                ##different eqs are valid, should give same result...e.g. bring uavsar data to beta by dividing by sin(f_0*PI/180.) then multiply by tan(b_1*PI/180.)
                ##here I just change sigma0->gamma0 then apply the SCF for gamma (ratio of these tan fns)
            #1/cos(f_0) to convert sigma0 to gamma0
            #the ratio of tan(b_1) and tan(f_0) to obtain the Slope Correction Factor for gamma e.g. NORMLIM in Small 2011 e.g. eq 5, with f_0 ellipsoid, b_1 local incidance angle shadowmasked
            #the shadowmask c to avoid correcting in shadowed area
            #---optional--
            ###eq with view angle dep correction ... eq = '--e=(a/cos(f_0*PI/180.)/cos(b_1*PI/180.))*(tan(b_1*PI/180.)/tan(f_0*PI/180.))*(c==0)'
            ###but I removed it because it's better to let user do this kind of correction. Over harvard forest, result looks much better using the correction with n=1 (greatly reduces the obvious look angle dependence on backscatter)
            ###since the UAVSAR roi's are near center of swath ~40 degree look angle, backscatter is not extemely high or low for scene. Also, fewer non-essential modifications make it easier to make comparisons.
            ###look angle correction term: 1/cos(b_1), here rough estimate n=1 for scattering law correction, as backscatter power varies by surface & view angle e.g. Ulaby & Dobson Radar Scattering Statistics for Terrain 1989 Fig 2-11 pg 27. 
            ###also: i think the above could/should be 1/cos(f_0) or perhaps 1/cos(b_0) ....because b_1 is now the projection angle in ISCE ....although labelled local incidence angle modified by DEM
            #---end optional--
            ps1 = '--a='+vald
            ps2 = '--b='+geomdir+'/incLocal.rdr'
            ps3 = '--c='+geomdir+'/shadowMask.rdr'
            ps4 = '--f='+geomdir+'/los.rdr'
            subprocess.call(['imageMath.py', eq, ps1, ps2, ps3, ps4, '-o', imgoutname+'_out', '-t',datatype, '-s', intlv])

           
            if os.path.exists(vald[:-3]+'ann'):
                os.remove(vald[:-3]+'ann')
                os.remove(vald) 
                os.remove(vald+'.vrt') 
                os.remove(vald+'.xml') 
            
            if vald.endswith('.mag'):
                os.remove(vald) 
                os.remove(vald+'.vrt') 
                os.remove(vald+'.xml') 

        dbfn = [f for f in os.listdir(nd) if f.startswith('data.')]
        if len(dbfn) > 0:
            os.remove(dbfn[0])
    os.chdir(postprocdir)
    os.chdir(cwd)

######----------Cleanup--------------#####
for num, val in enumerate(dirnm):
    nd = os.path.join(postprocdir, val)
    os.chdir(nd)
    outnm = [f for f in os.listdir(nd) if f.endswith('_out')]
    crosstalk = outnm[0].split('_')[7]
    if len(outnm) >= 6:
        aa = gdal.Open(val+'HHHH_CX_'+crosstalk+'_out.vrt')
        ncols = str(aa.RasterXSize)
        nrows = str(aa.RasterYSize)
        
        #replace my barebone .ann with the original one, but add in the new nrow ncol values
        zip_filepath = os.path.join(zerodir,val+'_CX_'+crosstalk+'_mlc.zip')
        annfile = val+'_CX_'+crosstalk+'.ann'
        
        with zipfile.ZipFile(zip_filepath) as z:
            with z.open(annfile) as zf, open(nd+'/'+annfile, 'wb') as f:
                shutil.copyfileobj(zf, f)

        with open(annfile, 'a') as ins:
            ins.write('; isce processing parameters\n')
            ins.write('iscemlc_pwr.set_rows (pixels) = '+nrows+'\n')
            ins.write('iscemlc_pwr.set_cols (pixels) = '+ncols+'\n')

        for numd, vald in enumerate(outnm):
            os.rename(vald, vald[:-4]+'.mlc')

#        #print('Compressing .mlc files')
#        #addtozip = [f for f in os.listdir() if f.endswith('.mlc') or f.endswith('.ann')]
#        #zf = zipfile.ZipFile(annfile[:-4]+'_rtc.zip', 'w')
#        #
#        #for numd, vald in enumerate(addtozip):
#        #    zf.write(vald)
#        #zf.close()

        delfiles = [f for f in os.listdir('.') if not f.endswith('.mlc') and not f.endswith('.ann')]
        for numd, vald in enumerate(delfiles):
            os.remove(vald)

######----------Geocode--------------#####

def genvrt(fni, cl, rw):
    if any(x in fni for x in sw) or fni.endswith('_mag.mlc'):
        tmp = """<VRTDataset rasterXSize='{cl}' rasterYSize='{rw}'>
    <VRTRasterBand band="1" dataType="Float32" subClass="VRTRawRasterBand">
        <SourceFilename relativeToVRT="1">{fni}</SourceFilename>
        <ByteOrder>LSB</ByteOrder>
        <ImageOffset>0</ImageOffset>
        <PixelOffset>4</PixelOffset>
        <LineOffset>13200</LineOffset>
    </VRTRasterBand>
</VRTDataset>"""
    elif any(x in fni for x in sw2):
        tmp = """<VRTDataset rasterXSize='{cl}' rasterYSize='{rw}'>
    <VRTRasterBand band="1" dataType="CFloat32" subClass="VRTRawRasterBand">
        <SourceFilename relativeToVRT="1">{fni}</SourceFilename>
        <ByteOrder>LSB</ByteOrder>
        <ImageOffset>0</ImageOffset>
        <PixelOffset>8</PixelOffset>
        <LineOffset>26400</LineOffset>
    </VRTRasterBand>
</VRTDataset>"""

    context = {"cl":cl, "rw":rw, "fni":fni}
    with open(fni+'.vrt', 'w') as f:
        f.write(tmp.format(**context))

if geocode == 1:
    for num, val in enumerate(dirnm):
        nd = os.path.join(postprocdir, val)
        os.chdir(nd)
        tiffiles = sorted([f for f in os.listdir(nd) if f.startswith(flightName) and f.endswith('.tif')])
        outfiles = sorted([f for f in os.listdir(nd) if f.startswith(flightName) and f.endswith('.mlc')])# and not f.endswith('_mag.mlc')])
        crosstalk = outfiles[0].split('_')[7][:-4]
        #estimate utm zone of flight from peg lon lat
        annfile = val+'_CX_'+crosstalk+'.ann'
        swx = ('Peg Latitude', 'Peg Longitude')
        with open(annfile, 'r') as ins:
            linelist = []
            for line in ins:
                if line.startswith('Peg Latitude'):
                    lat = float(line.split('=')[1].strip())
                if line.startswith('Peg Longitude'):
                    lon = float(line.split('=')[1].strip())
        utmz = utm.from_latlon(lat,lon)

        #if letter less equal than M == 77  means south; N or greater North

        if ord(utmz[3]) <= 77: #south
            northsouth = 7
        elif ord(utmz[3]) > 77: #north
            northsouth = 6
        zonenum = utmz[2]
        epsgproj_out = 'EPSG:32'+str(northsouth)+str(zonenum)
        
        #get cols, rows from ann it is different from the original. I wrote into the last two lines of the .ann
        cols = 3300
        with open(annfile, 'r') as ins:
            info = ins.read().splitlines()
        aa = info[-2].split(' ')
        rows = aa[-1]
        
        if len(tiffiles) == 0:
            print('-----------Additional processing: Geocoding (only real)--------------')
            for numd, vald in enumerate(outfiles):
                if not any(x in vald for x in sw2):
                    genvrt(vald, cols, rows)
                    print("-----------Geocoding: " + vald+"------------")
                    subprocess.call(['geocode_sk.py', '-i', vald+'.vrt', '-l', os.path.join(geomdir,'lat.rdr.vrt'), '-L', os.path.join(geomdir,'lon.rdr.vrt'),'-o', os.path.join(nd,vald[:-4]+'_geo.tif'), '-c', epsgproj_out, '-s', xyres_out, '-m', intmethod])
                if vald.endswith('_mag.mlc'):
                    genvrt(vald, cols, rows)
                    print("-----------Geocoding: " + vald+"------------")
                    subprocess.call(['geocode_sk.py', '-i', vald+'.vrt', '-l', os.path.join(geomdir,'lat.rdr.vrt'), '-L', os.path.join(geomdir,'lon.rdr.vrt'),'-o', os.path.join(nd,vald[:-4]+'_geo.tif'), '-c', epsgproj_out, '-s', xyres_out, '-m', intmethod])

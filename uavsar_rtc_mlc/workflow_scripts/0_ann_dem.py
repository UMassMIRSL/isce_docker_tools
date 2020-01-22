#!/usr/bin/env python3
import os, subprocess, shutil, csv
import pandas as pd
import numpy as np
import datetime as dt
from osgeo import gdal

####------User Set Params--------####
dembuf = 0.1 #buffer DEM extent. Can be increased if ISCE indicates extent is too small.
ftguess = 360   #Guess of UAVSAR flight time in seconds. Usually it is 6-10 minutes. Used if 'Stop Time of Acquisition' not provided in .ann in MLC .ann
vel = '250'     #Airplane velocity in (m/s). UAVSAR usually between 200-250 m/s. Average speed may be noted as comment in .ann, but no guarantee for MLC .ann
                #ftguess and vel are important in case ISCE throws a time mismatch error regarding orbital calculation
####------Set Params--------####
cwd = os.getcwd()
prjdir, zerodir = os.path.split(cwd)
coregdir = os.path.join(prjdir, '1_do_coreg_only_on_HHHH')
resampdir = os.path.join(prjdir, '2_resampdir')
postprocdir = os.path.join(prjdir, '3_postprocess_stacks')
isceprocdir = os.path.join(prjdir, 'SLC') 
mkdl = [coregdir, resampdir, postprocdir, isceprocdir]
for numd, vald in enumerate(mkdl):
    if os.path.exists(vald) == False:
        os.mkdir(vald)

mSlcl = sorted([f for f in os.listdir('.') if f.endswith('_mlc.zip')])
mSlcp = [] 
masterSlczip = mSlcl[0]

if os.path.exists(os.path.join(cwd,'processed.txt')):
    with open('processed.txt', 'r') as f:
        mSlcp = f.read().splitlines()
    bb = set(mSlcp)
else:
    bb=set()

aa = set(mSlcl)
new2proc = list(aa-bb)
mSlcp.extend(new2proc)

lmin = '25'     #UAVSAR minimum look angle in (deg)
lmax = '65'     #UAVSAR maximum look angle in (deg)
antlen = '1.5'  #Antenna Length in (m)
pols = ['HHHH', 'VVVV', 'HVHV', 'HHHV', 'HHVV', 'HVVV']

#####----------iterate over new zip files in cwd-------------#####
cwd = os.getcwd()

if len(new2proc)==0:
    print('No new files to process')
else:
    print('New files to process: %s' %(new2proc))

for num, val in enumerate(new2proc):
    os.chdir(cwd)
    pz = os.path.join(cwd, val)
    po = os.path.join(cwd)
    unzip = ['unzip', '-o', pz, '-d', po]
    subprocess.call(unzip)

    for num2, pol in enumerate(pols):
        print('-----------STEP (1/8) REWRITING .ANN for MLC for pol: '+pol+'--------------')
        
        annin =val[:-8]+'.ann'
        crosstalk = val.split('_')[7]
        slcn = val[:-14]+pol+'_CX_'+crosstalk+'.slc' 
        annout = slcn[:-3]+'ann'    
        sw = ('Peg', 'Center Wavelength', 'Global Average Altitude', 'Global Average Terrain', 'Pulse Length', 'Average Pulse Repetition Interval',
        'Bandwidth', 'Approximate', 'mlc_pwr.set_rows', 'mlc_pwr.set_cols',
        'mlc_pwr.row_addr', 'mlc_pwr.col_addr', 'mlc_pwr.row_mult',
        'mlc_pwr.col_mult', 'Date of Acquisition', 'Stop Time of Acquisition', 'Look Direction')

        with open(annin, 'r') as ins:
            linelist = []
            for line in ins:
                if line.startswith(sw):
                    line = line.split(';', 1)[0]
                    line = line.replace('=',' ')
                    line = ' '.join(line.split())
                    line = line.replace('(', ';(')
                    line = line.replace(')', ');')
                    linelist.append(line)

        with open('xx.csv', 'w') as f:
            for item in linelist:
                f.write("%s\n" %item)

        xx = pd.read_csv('xx.csv', index_col = None, header = None, names =
             ['Name','Unit','Value'], sep=';',
             encoding='latin1')

        xx = xx.applymap(str)
        xx = xx.apply(lambda x: x.str.strip())

        #Read values
        ullat = xx.loc[xx['Name'] == 'Approximate Upper Left Latitude']['Value'].tolist()
        ullon = xx.loc[xx['Name'] == 'Approximate Upper Left Longitude']['Value'].tolist()
        urlat = xx.loc[xx['Name'] == 'Approximate Upper Right Latitude']['Value'].tolist()
        urlon = xx.loc[xx['Name'] == 'Approximate Upper Right Longitude']['Value'].tolist()
        bllat = xx.loc[xx['Name'] == 'Approximate Lower Left Latitude']['Value'].tolist()
        bllon = xx.loc[xx['Name'] == 'Approximate Lower Left Longitude']['Value'].tolist()
        brlat = xx.loc[xx['Name'] == 'Approximate Lower Right Latitude']['Value'].tolist()
        brlon = xx.loc[xx['Name'] == 'Approximate Lower Right Longitude']['Value'].tolist()
        S1C1 = bllat[0]+', '+bllon[0]
        S1C2 = ullat[0]+', '+ullon[0]
        S1C3 = brlat[0]+', '+brlon[0]
        S1C4 = urlat[0]+', '+urlon[0]
        
        nmost = max(float(ullat[0]), float(urlat[0]))
        smost = min(float(bllat[0]), float(brlat[0]))
        wmost = min(float(ullon[0]),float(bllon[0]))
        emost = max(float(urlon[0]), float(brlon[0]))
        
        if nmost < 60.0:
           nmost = int(np.ceil(nmost+1.0))
           smost = int(np.floor(smost-1.0))
           wmost = int(np.floor(wmost-1.0))
           emost = int(np.ceil(emost+1.0))
        elif nmost >= 60.0: 
           nmost = nmost + 0.15
           smost = smost - 0.15
           wmost = wmost - 0.15
           emost = emost + 0.15
        #at latitude > 60 N/S, dem comes from different source

        mpsr = xx.loc[xx['Name'] == 'mlc_pwr.set_rows']['Value'].tolist()
        mpsc = xx.loc[xx['Name'] == 'mlc_pwr.set_cols']['Value'].tolist()
        mpra = xx.loc[xx['Name'] == 'mlc_pwr.row_addr']['Value'].tolist()
        mpca = xx.loc[xx['Name'] == 'mlc_pwr.col_addr']['Value'].tolist()
        mprm = xx.loc[xx['Name'] == 'mlc_pwr.row_mult']['Value'].tolist()
        mpcm = xx.loc[xx['Name'] == 'mlc_pwr.col_mult']['Value'].tolist()
        doac = xx.loc[xx['Name'] == 'Date of Acquisition']['Value'].tolist()
        dost = xx.loc[xx['Name'] == 'Stop Time of Acquisition']['Value'].tolist()
        pri = xx.loc[xx['Name'] == 'Average Pulse Repetition Interval']['Value'].tolist()
        pri = np.float(pri[0])*12

        #Start/Stop time
        aa = pd.to_datetime(doac[0])
        tstart = aa
        if len(dost)>0:
            tstop = pd.to_datetime(dost[0])
        else:
            tstop = aa + dt.timedelta(0,ftguess)
        tstart = tstart.strftime("%d-%b-%Y %H:%M:%S UTC")
        tstop = tstop.strftime("%d-%b-%Y %H:%M:%S UTC")

        xx = xx.append({'Name': 'Polarization','Unit': '(&)','Value': pol}, ignore_index=True)
        xx = xx.append({'Name': 'Average Pulse Repetition Interval','Unit': '(ms)','Value': pri}, ignore_index=True)
        xx = xx.append({'Name': 'slc_1_1x1','Unit':
            '(&)','Value': slcn}, ignore_index=True)
        xx = xx.append({'Name': 'slc_1_1x1_mag.set_rows','Unit':
            '(pixels)','Value': mpsr[0]}, ignore_index=True)
        xx = xx.append({'Name': 'slc_1_1x1_mag.set_cols','Unit':
            '(pixels)','Value': mpsc[0]}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Starting Azimuth','Unit':
            '(m)','Value': mpra[0]}, ignore_index=True)
        xx = xx.append({'Name': 'Image Starting Slant Range','Unit':
            '(m)','Value': mpca[0]}, ignore_index=True)
        xx = xx.append({'Name': 'slc_1_1x1_mag.col_addr','Unit':
            '(m)','Value': mpca[0]}, ignore_index=True)
        xx = xx.append({'Name': '1x1 SLC Azimuth Pixel Spacing','Unit':
            '(m/pixel)','Value': mprm[0]}, ignore_index=True)
        xx = xx.append({'Name': '1x1 SLC Range Pixel Spacing','Unit':
            '(m/pixel)','Value': mpcm[0]}, ignore_index=True)
        xx = xx.append({'Name': 'Average Along Track Velocity','Unit':
            '(m/s)','Value': vel}, ignore_index=True)
        xx = xx.append({'Name': 'Minimum Look Angle','Unit':
            '(deg)','Value': lmin}, ignore_index=True)
        xx = xx.append({'Name': 'Maximum Look Angle','Unit':
            '(deg)','Value': lmax}, ignore_index=True)
        xx = xx.append({'Name': 'Antenna Length','Unit':
            '(m)','Value': antlen}, ignore_index=True)
        xx = xx.append({'Name': 'Start Time of Acquisition','Unit':
            '(&)','Value': tstart}, ignore_index=True)
        xx = xx.append({'Name': 'Stop Time of Acquisition','Unit':
            '(&)','Value': tstop}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Approximate Corner 1','Unit':
            '(&)','Value': S1C1}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Approximate Corner 2','Unit':
            '(&)','Value': S1C2}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Approximate Corner 3','Unit':
            '(&)','Value': S1C3}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Approximate Corner 4','Unit':
            '(&)','Value': S1C4}, ignore_index=True)
        xx['es'] = '='

        xx = xx[['Name', 'Unit', 'es', 'Value']]
        np.savetxt(annout, xx.values, fmt='%s')

        if pol in ('HHHV', 'HHVV', 'HVVV'):
            os.rename(slcn[:-3]+'mlc',slcn)

    subprocess.call(['writexml_sk.py', '-i', cwd, '-o', cwd, '-p', '1', '-m', '1'])
    os.chdir(os.path.join(cwd, annout[:-14]))
    
    #Although there are 3 real valued UAVSAR data, need to change them to complex
    #That is because one of the ISCE tools we need to run was only built to work with complex interpolation (SINC)
    mlcfiles = [f for f in os.listdir('.') if f.endswith('.mlc')]
    for numd, vald in enumerate(mlcfiles):
        eq = '--e=a'
        ps1 = '--a='+vald
        print('making complex')
        subprocess.call(['imageMath.py', eq, ps1, '-o', os.path.join(cwd, vald[:-3]+'slc'), '-t', 'CFLOAT', '-s', 'BIP']) #BIL BIL

    annf = [f for f in os.listdir('.') if f.endswith('.ann')]
    for numd, vald in enumerate(annf):
        shutil.move(os.path.join(cwd, annout[:-14], vald), os.path.join(cwd, vald))
    
    os.chdir(cwd)
    shutil.rmtree(os.path.join(cwd, annout[:-14]))

    #Move files to appropriate dirs for ISCE stack processing
    if not os.path.exists(os.path.join(cwd, 'move')):
            os.mkdir(os.path.join(cwd, 'move'))

    fns = [f for f in os.listdir(cwd) if 'HHHH' in f and f.endswith('.slc')]
    for numd, vald in enumerate(fns):
        shutil.copy(os.path.join(cwd, vald), os.path.join(cwd, 'move', vald))
        shutil.copy(os.path.join(cwd, vald[:-3]+'ann'), os.path.join(cwd, 'move', vald[:-3]+'ann'))
    
    if val == masterSlczip:
        subprocess.call(['writexml_sk.py', '-i', '.', '-o', postprocdir, '-p', '1', '-m', '0'])
    else:
        subprocess.call(['writexml_sk.py', '-i', '.', '-o', resampdir, '-p', '0', '-m', '0'])
    
    os.chdir(os.path.join(cwd, 'move'))
    subprocess.call(['writexml_sk.py', '-i', '.', '-o', isceprocdir, '-p', '0', '-m', '0'])
    os.chdir(cwd)

    print('-----------STEP (2/8) Downloading DEM--------------')

    demstr = 'demLat_'
    if smost > 0:
        if abs(smost) < 10:
            demstr = demstr+'N0'+str(abs(smost))
        if abs(smost) > 10:
            demstr = demstr+'N'+str(abs(smost))
    elif smost < 0:
        if abs(smost) < 10:
            demstr = demstr+'S0'+str(abs(smost))
        if abs(smost) > 10:
            demstr = demstr+'S'+str(abs(smost))

    if nmost > 0:
        if abs(nmost) < 10:
            demstr = demstr+'_N0'+str(abs(nmost))
        if abs(nmost) > 10:
            demstr = demstr+'_N'+str(abs(nmost))
    elif nmost < 0:
        if abs(nmost) < 10:
            demstr = demstr+'_S0'+str(abs(nmost))
        if abs(nmost) > 10:
            demstr = demstr+'_S'+str(abs(nmost))

    if wmost > 0:
        if abs(wmost) < 10:
            demstr = demstr+'_Lon_E00'+str(abs(wmost))
        if abs(wmost) > 10 and abs(wmost) < 100:
            demstr = demstr+'_Lon_E0'+str(abs(wmost))
        if abs(wmost) > 100:
            demstr = demstr+'_Lon_E'+str(abs(wmost))
    elif wmost < 0:
        if abs(wmost) < 10:
            demstr = demstr+'_Lon_W00'+str(abs(wmost))
        if abs(wmost) > 10 and abs(wmost) < 100:
            demstr = demstr+'_Lon_W0'+str(abs(wmost))
        if abs(wmost) > 100:
            demstr = demstr+'_Lon_W'+str(abs(wmost))
    if emost > 0:
        if abs(emost) < 10:
            demstr = demstr+'_E00'+str(abs(emost))
        if abs(emost) > 10 and abs(emost) < 100:
            demstr = demstr+'_E0'+str(abs(emost))
        if abs(emost) > 100:
            demstr = demstr+'_E'+str(abs(emost))
    elif emost < 0:
        if abs(emost) < 10:
            demstr = demstr+'_W00'+str(abs(emost))
        if abs(emost) > 10 and abs(emost) < 100:
            demstr = demstr+'_W0'+str(abs(emost))
        if abs(emost) > 100:
            demstr = demstr+'_W'+str(abs(emost))

    print(demstr)
    demf = [f for f in os.listdir('.') if f.startswith(demstr) or f.startswith('dem.wgs84')]

    if len(demf)==0 and nmost < 60:
        print('Downloading SRTM1 DEM for SNWE box %s %s %s %s' %(smost, nmost, wmost, emost))
        #subprocess.call(['dem.py','-a', 'stitch', '-b', str(smost), str(nmost), str(wmost), str(emost), '-r', '-s', '1', '-c', '-n', 'uname', '-w', 'pass', '-u', 'https://aria-alt-dav.jpl.nasa.gov/repository/products/SRTM1_v3/'])
        #curl -k -f -u 'user:pass' -O http://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/N32W114.SRTMGL1.hgt.zip
        subprocess.call(['dem.py','-a', 'stitch', '-b', str(smost), str(nmost), str(wmost), str(emost), '-r', '-s', '1', '-c'])
            #This is the ISCE tools for downloading and stitching SRTM1 DEM, and works within
    elif len(demf)==0 and nmost >= 60:
        print('Downloading high latitude DEM for SNWE box %s %s %s %s' %(smost-dembuf, nmost+dembuf, wmost-dembuf, emost+dembuf))
        subprocess.call(['wget', '-O', 'dem.tif', 'http://ot-data1.sdsc.edu:9090/otr/getdem?north='+str(nmost+dembuf)+'&south='+str(smost-dembuf)+'&east='+str(emost+dembuf)+'&west='+str(wmost-dembuf)+'&demtype=AW3D30_E&outputFormat=GTiff'])
        print('Filling nodata values')
        subprocess.call(['gdal_fillnodata.py', 'dem.tif'])
        print('Translating to flat ENVI format')
        subprocess.call(['gdal_translate', '-of', 'ENVI', '-ot', 'Int16', 'dem.tif', 'dem.wgs84'])
        print('Making it an ISCE dem')
        subprocess.call(['gdal2isce_xml.py', '-i', 'dem.wgs84'])
        os.remove('dem.tif')
            #for high latitude sites, downloading from opentopographyi
            #Note: if there is an issue with with the ISCE outputs, check DEM first. Located in merged/geom_master/hgt.rdr
    else:
        print('DEM found, skipping download')

#write log of processed files
if len(new2proc)>0:
    with open('processed.txt', 'w') as f:
        for item in mSlcp:
            f.write("%s\n" %item)

#remove dem and other files that aren't used
rmfiles = ('.dem.vrt', '.dem.xml', '.dem', 'x.csv', '_L090_CX_'+crosstalk+'.ann', 'sce.log', '.slc.vrt', '.slc.xml')
demn = [f for f in os.listdir('.') if f.endswith(rmfiles)]
for numd, vald in enumerate(demn):
    os.remove(vald)

#update the xml for absolute pathname
demn = [f for f in os.listdir('.') if f.endswith('dem.wgs84')]
print('Fixing Image XML')
subprocess.call(['fixImageXml.py', '-f', '-i', demn[0]])

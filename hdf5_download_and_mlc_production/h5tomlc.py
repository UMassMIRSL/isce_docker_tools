#!/usr/bin/env python3

import os, h5py, shutil
import zipfile
import numpy as np
import subprocess as sp
import pandas as pd

#indicate flightline details
filenum=5 #there are 6 total, use numbers 0 through 5
CAMPAIGN='NISARP' #or 'NISARA' for AM and 'NISARP' for PM
SITE='25006'
PROD='129' #129 = global 20 & 5 MHz, 138 = US Ag 40 & 5 MHz
PROD2='CD' #CX = normal, CG = dithered-gaps, CD = dithered-no-gaps
channels='B' #A is (HH,HV) and has higher frequency compared to B (20 or 40 MHz vs 5 or 20 MHz); whereas B is (VH,VV). PROD='143' has both channels at 20 MHz
symmetrize = 1 #use UAVSAR's approach for symmetrizing HV and VH
#symmetrization: based on the principle of reciprocity HV should give the same result of VH. But due to instrument limitations (e.g. thermal noise/channel imbalance/cable lengths)
#vh and hv will not match in practice. The symmetrization is a statistical approach for reducing the imbalance, where the entire image statistics are used as inputs
#to determine correction factors for magnitude and phase for this imbalance. As result, the HV and VH channels will become much more similar on the whole; but there may still be some clear
#differences at the level of individual pixels.

def makemlc(CAMPAIGN=CAMPAIGN, SITE=SITE, PROD=PROD, PROD2=PROD2, channels=channels, symmetrize=symmetrize, filenum=filenum):
    basedir= os.getcwd()
    workingdir=os.path.join(basedir, SITE, PROD, PROD2)
    fnr = sorted([f for f in os.listdir(workingdir) if f.endswith('.h5')])[filenum] #work on one file for now
    aa = fnr.replace('h5', 'ann')
    aa = aa.replace(PROD2,'CX')
    annin = aa.replace(PROD,PROD+channels)
    fnr = os.path.join(workingdir, fnr)

    #print(fnr)
    #print(annin)

    n_HH = 'science/LSAR/SLC/swaths/frequency'+channels+'/HH'
    n_HV = 'science/LSAR/SLC/swaths/frequency'+channels+'/HV'
    n_VH = 'science/LSAR/SLC/swaths/frequency'+channels+'/VH'
    n_VV = 'science/LSAR/SLC/swaths/frequency'+channels+'/VV'

    with h5py.File(fnr, 'r') as f:  
        dat_HH = f[n_HH][()]
        print(dat_HH.shape)
        
        tmp_dat_HV = f[n_HV][()]
        print(tmp_dat_HV.shape)
        
        tmp_dat_VH = f[n_VH][()]
        print(tmp_dat_VH.shape)

        dat_VV = f[n_VV][()]
        print(dat_VV.shape)

    #added 8-26, UAVSAR approach for symmetrizing HV and VH data

    if symmetrize == 1:
        
        phase_sum = np.sum(tmp_dat_HV*np.conj(tmp_dat_VH))
        phase_sum_mag = np.sqrt(phase_sum*np.conj(phase_sum)) 
        phase_adj = phase_sum/phase_sum_mag
        
        sum_pwr_HV = np.sum(tmp_dat_HV*np.conj(tmp_dat_HV))
        sum_pwr_VH = np.sum(tmp_dat_VH*np.conj(tmp_dat_VH))
        mag_adj = np.sqrt(sum_pwr_HV/sum_pwr_VH)
        
        dat_VH = tmp_dat_VH*phase_adj*mag_adj
        dat_HV = (tmp_dat_HV+dat_VH)*0.5
        
        #to check if symmetrizing improved things take the difference between HV and VH between before and after, and sum over array. The value after correction should be much smaller
        diff_no_corr = np.sum(tmp_dat_HV-tmp_dat_VH)
        diff_after_corr = np.sum(dat_HV-dat_VH)
        print('SUM(HV-VH) from before symmetrizing: %s versus after symmetrizing %s' %(diff_no_corr, diff_after_corr))

    vel = '200'
    ftguess = 450
    lmin = '25'
    lmax = '65'
    antlen = '1.5'

    annsplit = annin.split('L090')
    annin = os.path.join(workingdir, annin)
    slcdir = os.path.join(workingdir, os.path.split(annin)[1][:-4])

    if os.path.exists(slcdir):
        shutil.rmtree(slcdir)
    #print(annin)
    #print(slcdir)
    #print(fno)

    aa = os.path.split(fnr)[1].split('_'+PROD2)
    basen_s = aa[0]
    basen_e = aa[1]
    #print(aa)

    #now write these cross products to a file ending in .slc
    pols = ['HH', 'HV', 'VH', 'VV']
    datfiles = [dat_HH, dat_HV, dat_VH, dat_VV]

    for num, val in enumerate(pols):
        annout = annsplit[0]+'L090'+val+annsplit[1]
        slcn = annout[:-3]+'slc'    
        os.makedirs(slcdir, exist_ok='True')

        #write the slc array data
        aa = os.path.split(fnr)[1].split('_'+PROD2)
        basen_s = aa[0]
        basen_e = aa[1]
        fno = basen_s + val +'_CX'+basen_e[:-2]+'slc'
        fno = fno.replace('_'+PROD, '_'+PROD+channels)
        datfiles[num].tofile(os.path.join(slcdir,fno))

        sw = ('Peg', 'Center Wavelength', 'Global Average Altitude', 'Global Average Terrain', 'Pulse Length', 'Average Pulse Repetition Interval',
    'Bandwidth', 'Approximate', 'slc_mag.set_rows', 'slc_mag.set_cols',
    'slc_mag.row_addr', 'slc_mag.col_addr', 'slc_mag.row_mult',
    'slc_mag.col_mult', 'Date of Acquisition', 'Stop Time of Acquisition', 'Look Direction')

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

        xx = pd.read_csv('xx.csv', index_col = None, header = None, names = ['Name','Unit','Value'], sep=';', encoding='latin1')
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

        mpsr = xx.loc[xx['Name'] == 'slc_mag.set_rows']['Value'].tolist()
        mpsc = xx.loc[xx['Name'] == 'slc_mag.set_cols']['Value'].tolist()
        mpra = xx.loc[xx['Name'] == 'slc_mag.row_addr']['Value'].tolist()
        mpca = xx.loc[xx['Name'] == 'slc_mag.col_addr']['Value'].tolist()
        mprm = xx.loc[xx['Name'] == 'slc_mag.row_mult']['Value'].tolist()
        mpcm = xx.loc[xx['Name'] == 'slc_mag.col_mult']['Value'].tolist()
        doac = xx.loc[xx['Name'] == 'Date of Acquisition']['Value'].tolist()
        dost = xx.loc[xx['Name'] == 'Stop Time of Acquisition']['Value'].tolist()

        pri = xx.loc[xx['Name'] == 'Average Pulse Repetition Interval']['Value'].tolist()
        pri = np.float(pri[0])

        #smrm = xx.loc[xx['Name'] == 'slc_mag.row_mult']['Value'].tolist()
        #mmrm = xx.loc[xx['Name'] == 'mlc_mag.row_mult']['Value'].tolist()
        #mfact = np.int(np.float(mmrm[0])/np.float(smrm[0]))
        #pri = np.float(pri[0])*mfact

        #Start/Stop time
        aa = pd.to_datetime(doac[0])
        tstart = aa
        if len(dost)>0:
            tstop = pd.to_datetime(dost[0])
        else:
            tstop = aa + dt.timedelta(0,ftguess)
        tstart = tstart.strftime("%d-%b-%Y %H:%M:%S UTC")
        tstop = tstop.strftime("%d-%b-%Y %H:%M:%S UTC")

        xx = xx.append({'Name': 'Polarization','Unit': '(&)','Value': val}, ignore_index=True)
        xx = xx.append({'Name': 'Average Pulse Repetition Interval','Unit': '(ms)','Value': pri}, ignore_index=True)
        xx = xx.append({'Name': 'slc_1_1x1','Unit':'(&)','Value': slcn}, ignore_index=True)
        xx = xx.append({'Name': 'slc_1_1x1_mag.set_rows','Unit':'(pixels)','Value': mpsr[0]}, ignore_index=True)
        xx = xx.append({'Name': 'slc_1_1x1_mag.set_cols','Unit':'(pixels)','Value': mpsc[0]}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Starting Azimuth','Unit':'(m)','Value': mpra[0]}, ignore_index=True)
        xx = xx.append({'Name': 'Image Starting Slant Range','Unit':'(m)','Value': mpca[0]}, ignore_index=True)
        xx = xx.append({'Name': 'slc_1_1x1_mag.col_addr','Unit':'(m)','Value': mpca[0]}, ignore_index=True)
        xx = xx.append({'Name': '1x1 SLC Azimuth Pixel Spacing','Unit':'(m/pixel)','Value': mprm[0]}, ignore_index=True)
        xx = xx.append({'Name': '1x1 SLC Range Pixel Spacing','Unit':'(m/pixel)','Value': mpcm[0]}, ignore_index=True)
        xx = xx.append({'Name': 'Average Along Track Velocity','Unit':'(m/s)','Value': vel}, ignore_index=True)
        xx = xx.append({'Name': 'Minimum Look Angle','Unit':'(deg)','Value': lmin}, ignore_index=True)
        xx = xx.append({'Name': 'Maximum Look Angle','Unit':'(deg)','Value': lmax}, ignore_index=True)
        xx = xx.append({'Name': 'Antenna Length','Unit':'(m)','Value': antlen}, ignore_index=True)
        xx = xx.append({'Name': 'Start Time of Acquisition','Unit':'(&)','Value': tstart}, ignore_index=True)
        xx = xx.append({'Name': 'Stop Time of Acquisition','Unit':'(&)','Value': tstop}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Approximate Corner 1','Unit':'(&)','Value': S1C1}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Approximate Corner 2','Unit':'(&)','Value': S1C2}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Approximate Corner 3','Unit':'(&)','Value': S1C3}, ignore_index=True)
        xx = xx.append({'Name': 'Segment 1 Data Approximate Corner 4','Unit':'(&)','Value': S1C4}, ignore_index=True)
        xx['es'] = '='

        xx = xx[['Name', 'Unit', 'es', 'Value']]
        np.savetxt(os.path.join(slcdir,annout), xx.values, fmt='%s')

        sp.call(['writexml_sk.py', '-i', slcdir, '-o', slcdir, '-p', '0', '-m', '0'])
         
    #move the SLC files out of the directories into a common one
    outputfn = os.path.split(slcdir)[1]
    mvdir = sorted([f for f in os.listdir(slcdir) if os.path.isdir(os.path.join(slcdir,f))])

    for numd, vald in enumerate(mvdir):
        mvl = [f for f in os.listdir(os.path.join(slcdir, vald)) if '.slc' in f]
        for numd2, vald2 in enumerate(mvl):
            shutil.move(os.path.join(slcdir, vald, vald2), os.path.join(slcdir, vald2))

    #take cross products
    os.chdir(slcdir)
    pcl = [f for f in os.listdir('.') if f.endswith('.slc')]

    for numd, vald in enumerate(pcl):
        if '_L090HH_' in vald:
            #create HHHH
            outname = vald.replace('HH', 'HHHH')
            eq = '--e=a*conj(b)'
            ps1 = '--a='+vald
            ps2 = '--b='+vald
            sp.call(['imageMath.py', eq , ps1, ps2, '-o', outname, '-t', 'FLOAT', '-s', 'BIL'])
            #create HHHV
            outname = vald.replace('HH', 'HHHV')
            eq = '--e=a*conj(b)'
            ps1 = '--a='+vald
            ps2 = '--b='+vald.replace('HH','HV')
            sp.call(['imageMath.py', eq , ps1, ps2, '-o', outname, '-t', 'CFLOAT', '-s', 'BIP'])
            #create HHVV
            outname = vald.replace('HH', 'HHVV')
            eq = '--e=a*conj(b)'
            ps1 = '--a='+vald
            ps2 = '--b='+vald.replace('HH','VV')
            sp.call(['imageMath.py', eq , ps1, ps2, '-o', outname, '-t', 'CFLOAT', '-s', 'BIP'])
        if '_L090HV_' in vald:
            #create HVHV
            outname = vald.replace('HV', 'HVHV')
            eq = '--e=a*conj(b)'
            ps1 = '--a='+vald
            ps2 = '--b='+vald
            sp.call(['imageMath.py', eq , ps1, ps2, '-o', outname, '-t', 'FLOAT', '-s', 'BIL'])
            #create HVVV
            outname = vald.replace('HV', 'HVVV')
            eq = '--e=a*conj(b)'
            ps1 = '--a='+vald
            ps2 = '--b='+vald.replace('HV','VV')
            sp.call(['imageMath.py', eq , ps1, ps2, '-o', outname, '-t', 'CFLOAT', '-s', 'BIP'])
        if '_L090VV_' in vald:
            #create VVVV
            outname = vald.replace('VV', 'VVVV')
            eq = '--e=a*conj(b)'
            ps1 = '--a='+vald
            ps2 = '--b='+vald
            sp.call(['imageMath.py', eq , ps1, ps2, '-o', outname, '-t', 'FLOAT', '-s', 'BIL'])
            
    os.chdir(workingdir)      

    #please note, because image math looks at the vrt, which only has the relative path to the slc file, all files are moved to the same directory ahead of processing
    #note: the xml that was written out does have the full path to where the file was originally put 
    # #cmd line is: imageMath.py '--e=a*conj(b)' --a=NISARP_25006_19040_009_190621_L090HH_CX_129A_03.slc --b=NISARP_25006_19040_009_190621_L090HH_CX_129A_03.slc -o ../ptst.slc -t FLOAT -s BIL

    #multi-look according to mlc data provided in the UAVSAR annotation files

    #take cross products
    if PROD == '138':
        rlk = '2'
    else:
        rlk = '1'
    os.chdir(slcdir)
    sw = ('_L090HHHH_', '_L090HHHV_', '_L090HHVV_', '_L090HVHV_', '_L090HVVV_', '_L090VVVV_')
    pcl = [f for f in os.listdir('.') if any(s in f for s in sw) and f.endswith('.slc')]

    for numd, vald in enumerate(pcl):
        outname = vald.replace('.slc', '.mlc')
        sp.call(['looks.py', '-i', vald, '-o', outname, '-r',rlk, '-a', '2'])
            
    os.chdir(workingdir)      

    #compress to zip

    shutil.copy(os.path.join(workingdir, annin), os.path.join(slcdir, os.path.split(annin)[1]))

    os.chdir(slcdir)
    pcl = sorted([f for f in os.listdir('.') if f.endswith('.mlc')])
    pca = [f for f in os.listdir('.') if f.endswith('.ann')]
    pz = pcl+pca

    zn = pca[0].replace('_'+PROD+channels+'_', '_')
    zn = zn[:-4]+'_mlc.zip'

    zf = zipfile.ZipFile(zn, 'w')
    for numd, vald in enumerate(pz):
        on = vald.replace('_'+PROD+channels+'_', '_')
        zf.write(vald, on)
    zf.close()

    shutil.move(zn, os.path.join(basedir,zn))
    os.chdir(basedir)

#def main(CAMPAIGN=CAMPAIGN, SITE=SITE, PROD=PROD, PROD2 = PROD2, channels=channels, symmetrize=symmetrize):

if __name__== "__main__":
    makemlc(CAMPAIGN, SITE, PROD, PROD2, channels, symmetrize, filenum)

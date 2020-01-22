#!/usr/bin/env python3

import os
import glob
import argparse

import isce
import isceobj
import shelve 
from isceobj.Util.decorators import use_api

def createParser():
    '''
    Create command line parser.
    '''

    parser = argparse.ArgumentParser(description='Unzip Alos zip files.')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True,
            help='directory which has all dates as directories. Inside each date, zip files are expected.')
    parser.add_argument('-d', '--dop_file', dest='dopFile', type=str, required=False,
            help='Doppler file for the stack.')
    parser.add_argument('-o', '--output', dest='output', type=str, required=True,
            help='output directory which will be used for unpacking.')
    parser.add_argument('-t', '--text_cmd', dest='text_cmd', type=str, default='source ~/.bash_profile;'
       , help='text command to be added to the beginning of each line of the run files. Example : source ~/.bash_profile;')

    return parser


def cmdLineParse(iargs=None):
    '''
    Command line parser.
    '''

    parser = createParser()
    return parser.parse_args(args = iargs)

def write_xml(shelveFile, slcFile):
    with shelve.open(shelveFile,flag='r') as db:
        frame = db['frame']

    length = frame.numberOfLines 
    width = frame.numberOfSamples
    print ('width, length:',width,length)
    print('slc.filename is:', slcFile)
    slc = isceobj.createSlcImage()
    slc.setWidth(width)
    slc.setLength(length)
    slc.filename = slcFile
    slc.setAccessMode('write')
    slc.renderHdr()
    slc.renderVRT()


def get_Date(file):

    yyyymmdd='20'+file.split('_')[4]
    return yyyymmdd

def main(iargs=None):
    '''
    The main driver.
    '''

    inps = cmdLineParse(iargs)
    
    outputDir = os.path.abspath(inps.output)
    run_unPack = 'run_unPackAlos'

    #######################################
    #mlc_files = glob.glob(os.path.join(inps.input, '*.mlc'))

    cwd = os.getcwd()
    os.chdir(os.path.join(cwd,inps.input))

    mlc_files = [f for f in os.listdir() if f.endswith('.mlc')]
    for numd, vald in enumerate(mlc_files):
        os.rename(vald, vald.replace('HHHH',''))

    mlc_files = sorted([f for f in os.listdir() if f.endswith('.mlc')])
    anf = sorted([f for f in os.listdir() if f.endswith('.ann')])
    for numd, vald in enumerate(mlc_files):
        print(vald)
        os.rename(vald, get_Date(vald)+'.slc')
        os.rename(anf[numd], get_Date(vald)+'.ann')
        #os.rename(anf[numd], os.path.join(inps.input, get_Date(vald)+'.ann'))

    mlc_files = [f for f in os.listdir() if f.endswith('.slc')]

   #val should be same as file in slcFile is download/NISARP_32039_19040_007_190621_L090_s5_1x1.slc
   #imgDate should be 20190621
   #shelvefile should be /Users/mirsl1-mac/postdoc_kraatz/data/uavsar/tst_slc_stack/SLC/20190621/data
   #slcFile should be /Users/mirsl1-mac/postdoc_kraatz/data/uavsar/tst_slc_stack/SLC/20190621/NISARP_32039_19040_007_190621_L090_s5_1x1.slc
   ###but for susbsequent proc need rename files to date strings
    for num, val in enumerate(mlc_files):
        imgDate = val[:-4]#get_Date(val)
        annFile = val[:-3]+'ann'
        print('file', val)
        print('date', imgDate)
        print('ann', annFile)
        imgDir = os.path.join(outputDir,imgDate)
        if not os.path.exists(imgDir):
           os.makedirs(imgDir)
        cmd = 'unpackFrame_UAVSAR_MLC.py -i ' + annFile + ' -o ' + imgDir
        print (cmd)
        os.system(cmd)

        cmd = 'mv ' + val + ' ' + imgDir
        print(cmd)
        os.system(cmd)

        cmd = 'mv ' + annFile + ' ' + imgDir
        print(cmd)
        os.system(cmd)

        shelveFile = os.path.join(imgDir, 'data')
        slcFile = os.path.join(imgDir, os.path.basename(val))
        print(shelveFile, slcFile)
        write_xml(shelveFile, slcFile)

if __name__ == '__main__':

    main()



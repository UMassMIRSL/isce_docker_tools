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
    parser.add_argument('-p', '--polflag', dest='polflag', type=str, required=True,
            help='0: make folder for each pol; else: put multiple pols into one date folder')
    parser.add_argument('-m', '--mlcflag', dest='mlcflag', type=str, required=True,
            help='0: files end with .slc, 1: files end with .mlc')

    return parser
def cmdLineParse(iargs=None):
    '''
    Command line parser.
    '''

    parser = createParser()
    return parser.parse_args(args = iargs)

def write_xml(shelveFile, slcFile, mlcflag):
    with shelve.open(shelveFile,flag='r') as db:
        frame = db['frame']

    length = frame.numberOfLines
    width = frame.numberOfSamples
    pol = frame.polarization

    sw = ('HHHH', 'HVHV', 'VVVV')
    if pol in sw and mlcflag == '1':
        slc = isceobj.createMlcImage()
    else:
        slc = isceobj.createSlcImage()
    
    slc.setWidth(width)
    slc.setLength(length)
    slc.filename = slcFile
    slc.polarization = pol #apparently that doesnt get saved
    slc.setAccessMode('write')
    slc.renderHdr()
    slc.renderVRT()
    
def main(iargs=None):
    '''
    The main driver.
    '''

    inps = cmdLineParse(iargs)

    outputDir = os.path.abspath(inps.output)
    run_unPack = 'run_unPackAlos'

    #######################################
    if inps.mlcflag == '1':
        slc_files = glob.glob(os.path.join(inps.input, '*.mlc'))
    else:
        slc_files = glob.glob(os.path.join(inps.input, '*.slc'))
    
    for file in slc_files:
        
        if inps.mlcflag == '1':
            annFile = file.replace('.mlc','')+'.ann'
        else:
            annFile = file.replace('.slc','')+'.ann'
        
        if inps.polflag == '0':
            imgDir = os.path.join(outputDir,annFile[:-4])
            if not os.path.exists(imgDir):
                os.makedirs(imgDir)
        else:
            imgDir = os.path.join(outputDir,annFile[:-14])
            if not os.path.exists(imgDir):
                os.makedirs(imgDir)

        cmd = 'unpackFrame_UAVSAR_MLC.py -i ' + annFile + ' -o ' + imgDir
        print (cmd)
        os.system(cmd)

        cmd = 'mv ' + file + ' ' + imgDir
        print(cmd)
        os.system(cmd)

        cmd = 'mv ' + annFile + ' ' + imgDir
        print(cmd)
        os.system(cmd)

        shelveFile = os.path.join(imgDir, 'data')
        slcFile = os.path.join(imgDir, os.path.basename(file))
        write_xml(shelveFile, slcFile, inps.mlcflag)

if __name__ == '__main__':

    main()

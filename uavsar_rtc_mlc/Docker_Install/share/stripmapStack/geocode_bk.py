#!/usr/bin/env python3
# coding: utf-8
import argparse
from osgeo import gdal, ogr, osr

def cmdLineParse():
    '''
    Command line parser.
    '''

    parser = argparse.ArgumentParser( description='Geocode an image using GDAL')
    parser.add_argument('-i', '--input', dest='infile', type=str, required=True,
                        help='Input file to be geocoded')
    parser.add_argument('-l', '--lat', dest='latFile', type=str, required=True,
                        help='latitude file in radar coordinate')
    parser.add_argument('-L', '--lon', dest='lonFile', type=str, required=True,
                        help='longitude file in radar coordinate')
    parser.add_argument('-o', '--output', dest='outfile', type=str, required=True,
                        help = 'Output file name')
    return parser.parse_args()



def geocodeUsingGdalWarp(infile, latfile, lonfile, outfile,
                         insrs=4326, outsrs=None,
                         spacing=None, fmt='GTiff', bounds=None,
                         method='near'):
    '''
    Geocode a swath file using corresponding lat, lon files
    '''
    sourcexmltmpl = '''    <SimpleSource>
      <SourceFilename>{0}</SourceFilename>
      <SourceBand>{1}</SourceBand>
    </SimpleSource>'''
    
    driver = gdal.GetDriverByName('VRT')
    tempvrtname = 'geocode.vrt'

    inds = gdal.OpenShared(infile, gdal.GA_ReadOnly)
    tempds = driver.Create(tempvrtname, inds.RasterXSize, inds.RasterYSize, 0)

    for ii in range(inds.RasterCount):
        band = inds.GetRasterBand(1)
        tempds.AddBand(band.DataType)
        tempds.GetRasterBand(ii+1).SetMetadata({'source_0': sourcexmltmpl.format(infile, ii+1)}, 'vrt_sources')
  
    sref = osr.SpatialReference()
    sref.ImportFromEPSG(insrs)
    srswkt = sref.ExportToWkt()

    tempds.SetMetadata({'SRS' : srswkt,
                        'X_DATASET': lonfile,
                        'X_BAND' : '1',
                        'Y_DATASET': latfile,
                        'Y_BAND' : '1',
                        'PIXEL_OFFSET' : '0',
                        'LINE_OFFSET' : '0',
                        'PIXEL_STEP' : '1',
                        'LINE_STEP' : '1'}, 'GEOLOCATION')
    
    band = None
    tempds = None 
    inds = None
    
    if spacing is None:
        spacing = [None, None]
    
    warpOptions = gdal.WarpOptions(format=fmt,
                                   xRes=spacing[0], yRes=spacing[0],
                                   dstSRS=outsrs, outputBounds = bounds, 
                                   resampleAlg=method, geoloc=True)
    gdal.Warp(outfile, tempvrtname, options=warpOptions)

if __name__ == '__main__':

    #####Parse command line
    inps = cmdLineParse()
    geocodeUsingGdalWarp(inps.infile, inps.latFile, inps.lonFile, inps.outfile)

#cmd = "imageMath.py --e='a*cos(b_0*PI/180.)/cos(b_1*PI/180.) * (c==0)' --a={beta} --b={inc} --c={mask} -o {out} -t FLOAT -s BIL"
#cmdrun = cmmd.format(inc = incname,beta = betaname,out = outpolname,mask = maskname)
#status = os.system(cmdrun)
#if status:
#    raise Exception('{0} Failed.'.format(cmdrun))

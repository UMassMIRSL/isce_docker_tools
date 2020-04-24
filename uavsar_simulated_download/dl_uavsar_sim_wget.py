#this will download the uavsar simulated data (or others) as per links provided in wget.txt
#this will rename the files to be consistent with regular UAVSAR data so that it can be easily input to the ISCE Docker Tool
#make sure when running this code, only the wget.txt and dl_uavsar_sim_wget.py are in the dir, move the zip files elsewhere

import requests, os, zipfile
from lxml import html
from clint.textui import progress

unm = ''
pwd = ''

##########headers
uavdl = 'UA_NISARP_09702' #the flightlines to search for
checknewfn = 1

if os.path.exists('wget.txt'):
    checknewfn = 0

###########functions
def download_file(url):
    local_filename = url.split('/')[-1]
    with requests.Session() as session:
        session.auth = (unm, pwd)
        r1 = session.request('get', url)
        r = session.get(r1.url, auth=(unm, pwd), stream = True)
        if r.ok:
            with open(local_filename, 'wb') as f:
                total_length = int(r.headers.get('content-length'))
                for chunk in progress.bar(r.iter_content(chunk_size=8192), expected_size=(total_length/8192) + 1): 
                    if chunk:
                        f.write(chunk)
                        f.flush()
###########MAIN
if checknewfn == 1:
    print('Checking for new uavsar data ...')
    r = requests.get(p1)
    wp = html.fromstring(r.content)
    ll = wp.xpath('//a/@href')

    with open('filelist.txt', 'r') as f:
        ll2 = f.read().splitlines()

    aa = set(ll)
    bb = set(ll2)
    cc = aa-bb
    
    if len(cc)>0:
        print('There is new uavsar data %s' %(cc))
        
        with open('filelist.txt', 'w') as f:
            for item in ll:
                f.write("%s\n" % item)
    elif len(cc) ==0:
        print('No new uavsar data')

elif checknewfn == 0:
    with open('wget.txt', 'r') as f:
        ll = f.read().splitlines()
    
    dll = [f for f in ll if f.startswith('http')]
    
    if len(dll) == 0:
        print('No new files to download')
    elif len(dll) > 0:
        print('%s new files will be downloaded, they are %s' %(len(dll), dll))
        for num, val in enumerate(dll):
            print('Downloading file %s' %(val))
            download_file(val)

#note i rename the filenames to make the more like the standard mlc.zip so that the ISCE Docker Tool can read it
annl = [f for f in os.listdir('.') if f.endswith('.ann')]

if len(annl) > 0:
    for num, val in enumerate(annl):
        aa = val.split('_')
        bb = aa[0]+'_'+aa[1]+'_'+aa[2]+'_'+aa[3]+'_'+aa[4]
        zfnl = [f for f in os.listdir('.') if f.startswith(bb)]
        znx = val.split('_')
        zn = znx[0]+'_'+znx[1]+'_'+znx[2]+'_'+znx[3]+'_'+znx[4]+'_'+znx[5]+'_'+znx[6]+'_'+znx[8].split('.')[0]+'_mlc.zip'
        
        with zipfile.ZipFile(zn, 'w') as zp:
            for num2, val2 in enumerate(zfnl):
                znx2 = val2.split('_')
                zn2 = znx2[0]+'_'+znx2[1]+'_'+znx2[2]+'_'+znx2[3]+'_'+znx2[4]+'_'+znx2[5]+'_'+znx2[6]+'_'+znx2[8]
                zp.write(val2, arcname=zn2)

sw = ('.zip', '.py', '.txt')
delfn = [f for f in os.listdir('.') if not os.path.isdir(f) and not f.endswith(sw)]

for num, val in enumerate(delfn):
    os.remove(val)

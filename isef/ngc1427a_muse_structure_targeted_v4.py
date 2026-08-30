#!/usr/bin/env python3
import json,subprocess,time
from pathlib import Path
URL='https://dataportal.eso.org/dataPortal/file/ADP.2026-06-24T16:04:14.194'
OUT=Path('results/ngc1427a_muse_structure_targeted_v4.json');OUT.parent.mkdir(exist_ok=True)
BLOCK=2880
# Known from v3 header-only walk: primary header 20160 bytes; DATA header 5760 bytes;
# DATA payload padded 6693275520 bytes. Therefore the next HDU header begins here.
OFF_DATA=20160; OFF_NEXT=20160+5760+6693275520

def rng(a,b):
 last=None
 for k in range(5):
  p=subprocess.run(['curl','-L','--fail','--silent','--show-error','--max-time','90','--range',f'{a}-{b}',URL],capture_output=True,timeout=100)
  if p.returncode==0 and len(p.stdout)==b-a+1:return p.stdout
  last=(p.returncode,p.stderr.decode('utf-8','replace')[:300],len(p.stdout));time.sleep(2**k)
 raise RuntimeError(str(last))
def header(off,maxblocks=8):
 cards=[]
 for j in range(maxblocks):
  raw=rng(off+j*BLOCK,off+(j+1)*BLOCK-1)
  for i in range(0,BLOCK,80):
   c=raw[i:i+80].decode('ascii','replace');cards.append(c)
   if c.startswith('END '):
    d={}
    for z in cards:
     if len(z)>=10 and z[8:10]=='= ':
      key=z[:8].strip(); val=z[10:].split('/')[0].strip()
      d[key]=val
    return d,j+1
 raise RuntimeError('END not found')
keep={'XTENSION','EXTNAME','BITPIX','NAXIS','NAXIS1','NAXIS2','NAXIS3','PCOUNT','GCOUNT','BUNIT','CRPIX1','CRPIX2','CRPIX3','CRVAL1','CRVAL2','CRVAL3','CDELT1','CDELT2','CDELT3','CD1_1','CD1_2','CD1_3','CD2_1','CD2_2','CD2_3','CD3_1','CD3_2','CD3_3','CTYPE1','CTYPE2','CTYPE3','CUNIT1','CUNIT2','CUNIT3'}
o={'status':'TARGETED_HEADERS_ONLY_V4','science_data_bytes_requested':False,'success':False,'known_next_header_offset':OFF_NEXT}
try:
 dh,db=header(OFF_DATA);nh,nb=header(OFF_NEXT)
 o['data_header_blocks']=db;o['data_selected']={k:dh[k] for k in keep if k in dh}
 o['next_header_blocks']=nb;o['next_selected']={k:nh[k] for k in keep if k in nh}
 o['success']=True
except Exception as e:o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))

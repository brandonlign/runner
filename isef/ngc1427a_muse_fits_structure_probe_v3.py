#!/usr/bin/env python3
"""Header-only FITS HDU walker for the public NGC1427A deep MUSE cube.

The walker requests FITS header blocks (2880 bytes) one at a time. Once a
header is complete, it computes the byte size of that HDU's data array from
BITPIX/NAXIS/PCOUNT/GCOUNT and jumps directly to the next header. It never
requests any byte range belonging to an HDU data array.
"""
import json, math, subprocess
from pathlib import Path
URL='https://dataportal.eso.org/dataPortal/file/ADP.2026-06-24T16:04:14.194'
OUT=Path('results/ngc1427a_muse_fits_structure_probe_v3.json'); OUT.parent.mkdir(exist_ok=True)
BLOCK=2880

def get_block(off):
    end=off+BLOCK-1
    p=subprocess.run(['curl','-L','--fail','--silent','--show-error','--max-time','90','--range',f'{off}-{end}',URL],capture_output=True,timeout=100)
    if p.returncode!=0: raise RuntimeError(p.stderr.decode('utf-8','replace')[:400])
    if len(p.stdout)!=BLOCK: raise RuntimeError(f'expected {BLOCK} bytes at {off}, got {len(p.stdout)}')
    return p.stdout

def parse_value(s):
    x=s.split('/')[0].strip()
    if x.startswith("'") and x.endswith("'"): return x[1:-1].strip()
    if x=='T': return True
    if x=='F': return False
    try:
        return int(x)
    except Exception: pass
    try:
        return float(x.replace('D','E'))
    except Exception: return x

def read_header(off):
    cards=[]; blocks=0
    while True:
        raw=get_block(off+blocks*BLOCK); blocks+=1
        for i in range(0,BLOCK,80):
            c=raw[i:i+80].decode('ascii','replace'); cards.append(c)
            if c.startswith('END '):
                hdr={}
                for z in cards:
                    if len(z)>=10 and z[8:10]=='= ':
                        hdr[z[:8].strip()]=parse_value(z[10:])
                return hdr,blocks
        if blocks>100: raise RuntimeError('header exceeds 100 FITS blocks')

def data_padded_bytes(h):
    bitpix=abs(int(h.get('BITPIX',8))); naxis=int(h.get('NAXIS',0))
    n=1 if naxis>0 else 0
    for i in range(1,naxis+1): n*=int(h.get(f'NAXIS{i}',0))
    pcount=int(h.get('PCOUNT',0)); gcount=int(h.get('GCOUNT',1))
    # FITS standard data size in bytes, rounded to a 2880-byte record.
    raw=((bitpix*n)//8 + pcount)*gcount if n or pcount else 0
    return int(math.ceil(raw/BLOCK)*BLOCK) if raw else 0

keep={'XTENSION','EXTNAME','BITPIX','NAXIS','NAXIS1','NAXIS2','NAXIS3','PCOUNT','GCOUNT','BUNIT','WCSAXES','CRPIX1','CRPIX2','CRPIX3','CRVAL1','CRVAL2','CRVAL3','CDELT1','CDELT2','CDELT3','CD1_1','CD1_2','CD2_1','CD2_2','CTYPE1','CTYPE2','CTYPE3','CUNIT1','CUNIT2','CUNIT3','OBJECT','INSTRUME','PRODCATG','DATAMIN','DATAMAX'}
o={'status':'FITS_HEADERS_ONLY_V3','science_data_bytes_requested':False,'url':URL,'success':False,'hdus':[]}
try:
    off=0
    for idx in range(8):
        h,b=read_header(off); dbytes=data_padded_bytes(h)
        o['hdus'].append({'index':idx,'header_offset':off,'header_blocks':b,'header_bytes':b*BLOCK,'data_padded_bytes_skipped':dbytes,'selected':{k:h[k] for k in keep if k in h}})
        off += b*BLOCK + dbytes
        # Stop when no extension is expected or after common MUSE DATA/STAT products.
        if idx==0 and not bool(h.get('EXTEND',False)): break
        if idx>=1 and str(h.get('EXTNAME','')).upper() in {'STAT','VAR','VARIANCE'}: break
    o['success']=True
except Exception as e:
    o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))

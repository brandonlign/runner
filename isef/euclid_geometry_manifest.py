#!/usr/bin/env python3
"""Map actual Q2 Field-1 dither geometry from one VIS SCI quadrant.

Reads only the primary + first SCI extension header from exposure 0, then the
same extension header from all 15 remaining exposures concurrently. Emits WCS
center/corner coordinates and relative shifts. No pixel data are downloaded.
"""
from __future__ import annotations
import json, math, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

BASE='https://irsa.ipac.caltech.edu/data/Euclid/q2/data'
FILES=[
'EUC_VIS_SWL-DET-067070-00-1__20250621T020155.487037Z_sci.fits','EUC_VIS_SWL-DET-067070-01-1__20250621T020156.049078Z_sci.fits','EUC_VIS_SWL-DET-067070-02-1__20250621T020157.327960Z_sci.fits','EUC_VIS_SWL-DET-067070-03-1__20250621T020200.784839Z_sci.fits','EUC_VIS_SWL-DET-067070-04-1__20250621T020159.310075Z_sci.fits','EUC_VIS_SWL-DET-067070-05-1__20250621T020148.061975Z_sci.fits','EUC_VIS_SWL-DET-067070-06-1__20250621T020208.198375Z_sci.fits','EUC_VIS_SWL-DET-067070-07-1__20250621T020158.860635Z_sci.fits','EUC_VIS_SWL-DET-067070-08-1__20250621T020202.737416Z_sci.fits','EUC_VIS_SWL-DET-067070-09-1__20250621T020203.034854Z_sci.fits','EUC_VIS_SWL-DET-067070-10-1__20250621T020153.520357Z_sci.fits','EUC_VIS_SWL-DET-067070-11-1__20250621T020206.950527Z_sci.fits','EUC_VIS_SWL-DET-067070-12-1__20250621T020154.990859Z_sci.fits','EUC_VIS_SWL-DET-067070-13-1__20250621T020149.508409Z_sci.fits','EUC_VIS_SWL-DET-067070-14-1__20250621T020202.468375Z_sci.fits','EUC_VIS_SWL-DET-067070-15-1__20250621T020200.444396Z_sci.fits']
URLS=[f'{BASE}/{x}' for x in FILES]
OUT=Path('results/euclid_geometry_manifest.json')
BLOCK=2880;CARD=80;HMAX=32*BLOCK

def rr(url,a,b,timeout=40):
    n=b-a+1;req=urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}','User-Agent':'isef-euclid-geometry/1.0'})
    with urllib.request.urlopen(req,timeout=timeout) as r:data=r.read(n+1);s=r.status
    if s!=206 or len(data)!=n:raise RuntimeError(f'HTTP/range failure status={s} got={len(data)} want={n}')
    return data

def val(raw):
    raw=raw.strip();q=False;cut=len(raw)
    for i,ch in enumerate(raw):
        if ch=="'":q=not q
        elif ch=='/' and not q:cut=i;break
    s=raw[:cut].strip()
    if not s:return None
    if s.startswith("'"):
        m=re.match(r"'((?:''|[^'])*)'",s);return m.group(1).replace("''","'").strip() if m else s.strip("'").strip()
    if s=='T':return True
    if s=='F':return False
    try:return float(s.replace('D','E')) if any(c in s for c in '.EDed') else int(s)
    except:return s

def hdr(url,off):
    b=rr(url,off,off+HMAX-1);d={};cards=[]
    for i in range(0,len(b),CARD):
        c=b[i:i+CARD].decode('ascii',errors='replace');cards.append(c);k=c[:8].strip()
        if k=='END':return d,cards,math.ceil((i+CARD)/BLOCK)*BLOCK
        if len(c)>=10 and c[8:10]=='= ':d[k]=val(c[10:])
    raise RuntimeError('no END')

def one(i,off):
    h,c,hb=hdr(URLS[i],off);w=WCS(fits.Header.fromstring(''.join(c),sep=''),relax=True);nx=int(h['NAXIS1']);ny=int(h['NAXIS2']);ra,de=w.pixel_to_world_values(nx/2,ny/2)
    corners=[]
    for x,y in [(0,0),(nx-1,0),(0,ny-1),(nx-1,ny-1)]:
        r,d=w.pixel_to_world_values(x,y);corners.append([float(r),float(d)])
    return {'index':i,'file':FILES[i],'extname':str(h.get('EXTNAME','')),'nx':nx,'ny':ny,'header_bytes':int(hb),'center_ra':float(ra),'center_dec':float(de),'corners':corners,'crval1':float(h.get('CRVAL1',np.nan)),'crval2':float(h.get('CRVAL2',np.nan))}

def main():
    t=time.time();res={'success':False}
    try:
        _,_,phb=hdr(URLS[0],0);first=one(0,phb);off=phb
        rows=[None]*16;rows[0]=first
        with ThreadPoolExecutor(max_workers=15) as ex:
            fs={ex.submit(one,i,off):i for i in range(1,16)}
            for f in as_completed(fs):rows[fs[f]]=f.result()
        ra0=rows[0]['center_ra'];de0=rows[0]['center_dec'];cosd=math.cos(math.radians(de0))
        for r in rows:
            r['dra_arcsec']=float((r['center_ra']-ra0)*cosd*3600);r['ddec_arcsec']=float((r['center_dec']-de0)*3600);r['shift_arcsec']=float(math.hypot(r['dra_arcsec'],r['ddec_arcsec']))
        # Purely empirical grouping of nearly identical pointing centers (<3 arcsec).
        groups=[]
        for r in rows:
            placed=False
            for g in groups:
                q=rows[g[0]]
                if math.hypot(r['dra_arcsec']-q['dra_arcsec'],r['ddec_arcsec']-q['ddec_arcsec'])<3:
                    g.append(r['index']);placed=True;break
            if not placed:groups.append([r['index']])
        res={'success':True,'extension_offset':int(off),'extension':first['extname'],'rows':rows,'empirical_groups_lt3arcsec':groups}
    except Exception as e:res['error']=f'{type(e).__name__}: {e}';raise
    finally:
        res['elapsed_seconds']=round(time.time()-t,2);OUT.parent.mkdir(parents=True,exist_ok=True);txt=json.dumps(res,indent=2,sort_keys=True);OUT.write_text(txt+'\n');print(txt,flush=True)
if __name__=='__main__':main()

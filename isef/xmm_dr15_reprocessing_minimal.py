#!/usr/bin/env python3
"""Minimal blinded 5XMM old-era vs 4XMM-DR14 presence/absence gate.
Transfers only RA/Dec from HEASARC for speed; outputs aggregate counts only.
"""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz';P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz')
OUT=Path('results/xmm_dr15_reprocessing_minimal.json');OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='sum_flag < 3 AND extent = 0 AND end_time <= 60309.99999 AND ep_det_ml >= 15'
def save(x):OUT.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');print(json.dumps(x,indent=2,sort_keys=True))
def tap():
 b=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':f'SELECT TOP 500000 ra,dec FROM xmmssc WHERE {BASE}'}).encode();req=urllib.request.Request(EP,data=b,headers={'User-Agent':'ISEF-XMM-minimal/1.0','Content-Type':'application/x-www-form-urlencoded'})
 with urllib.request.urlopen(req,timeout=150) as r:raw=r.read()
 txt=raw.decode('utf-8','replace')
 if 'QUERY_STATUS' in txt[:8000] and 'value="ERROR"' in txt[:8000]:raise RuntimeError(txt[:4000])
 return Table.read(io.BytesIO(raw),format='votable')
def dl4():
 reqh=urllib.request.Request(U4,method='HEAD',headers={'User-Agent':'ISEF-XMM-minimal/1.0'});total=int(urllib.request.urlopen(reqh,timeout=30).headers['Content-Length'])
 if P4.exists() and P4.stat().st_size==total:return
 req=urllib.request.Request(U4,headers={'User-Agent':'ISEF-XMM-minimal/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r,P4.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b:break
   f.write(b)
def main():
 try:
  t=tap();dl4();ra5=np.asarray(t['ra'],float);de5=np.asarray(t['dec'],float);ok5=np.isfinite(ra5)&np.isfinite(de5);ra5=ra5[ok5];de5=de5[ok5]
  with fits.open(P4,memmap=True) as h:
   tabs=[z for z in h if isinstance(z,(fits.BinTableHDU,fits.TableHDU)) and z.data is not None];d=max(tabs,key=lambda z:len(z.data)).data;n={x.upper():x for x in d.names};ra4=np.asarray(d[n['SC_RA']],float);de4=np.asarray(d[n['SC_DEC']],float);ok=np.isfinite(ra4)&np.isfinite(de4);ra4=ra4[ok];de4=de4[ok]
  _,sep,_=SkyCoord(ra5*u.deg,de5*u.deg).match_to_catalog_sky(SkyCoord(ra4*u.deg,de4*u.deg));s=sep.arcsec
  out={'success':True,'five_parent_rows':int(len(ra5)),'four_rows':int(len(ra4)),'unmatched_counts_by_radius_arcsec':{str(r):int(np.sum(s>r)) for r in (2,3,5,7,10,15,20,30)},'nearest_sep_arcsec_summary':{'median':float(np.median(s)),'q90':float(np.quantile(s,.9)),'q95':float(np.quantile(s,.95)),'q99':float(np.quantile(s,.99))},'note':'No identities or coordinates emitted. Old-era proxy only; exact ObsIDs needed before reprocessing-only claim.'};save(out)
 except Exception as e:save({'success':False,'error':f'{type(e).__name__}: {e}'})
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Blinded exact-ObsID gate for the 5XMM reprocessing-recovery hypothesis.

No source names/coordinates are emitted. We ask whether clean 5XMM sources from the
DR14 time era that are positionally absent from 4XMM nevertheless carry an XMM
ObsID already represented in the official 4XMM-DR14 source catalogue. If yes,
that is direct evidence the observation existed before DR15 and the source was
recovered by changed catalogue processing rather than simply newer observing time.
"""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz')
OUT=Path('results/xmm_dr15_obsid_reprocessing_gate.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='sum_flag < 3 AND extent = 0 AND end_time <= 60309.99999 AND ep_det_ml >= 15'
def save(x): OUT.write_text(json.dumps(x,indent=2,sort_keys=True,default=str)+'\n'); print(json.dumps(x,indent=2,sort_keys=True,default=str))
def tap():
 q=f'SELECT TOP 100000 ra,dec,obs_id,end_time FROM xmmssc WHERE {BASE}'
 b=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}).encode()
 req=urllib.request.Request(EP,data=b,headers={'User-Agent':'ISEF-XMM-obsid-gate/1.0','Content-Type':'application/x-www-form-urlencoded'})
 with urllib.request.urlopen(req,timeout=180) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl4():
 reqh=urllib.request.Request(U4,method='HEAD',headers={'User-Agent':'ISEF-XMM-obsid-gate/1.0'}); total=int(urllib.request.urlopen(reqh,timeout=30).headers['Content-Length'])
 if P4.exists() and P4.stat().st_size==total:return total
 req=urllib.request.Request(U4,headers={'User-Agent':'ISEF-XMM-obsid-gate/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,P4.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b:break
   f.write(b)
 return total
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def main():
 try:
  t=tap(); size=dl4(); ra5=np.asarray(t['ra'],float); de5=np.asarray(t['dec'],float); obs5=np.asarray([norm(x) for x in t['obs_id']])
  with fits.open(P4,memmap=True) as h:
   tabs=[z for z in h if isinstance(z,(fits.BinTableHDU,fits.TableHDU)) and z.data is not None]; d=max(tabs,key=lambda z:len(z.data)).data; names={n.upper():n for n in d.names}
   ra4=np.asarray(d[names['SC_RA']],float); de4=np.asarray(d[names['SC_DEC']],float)
   obscol=names.get('OBS_ID') or names.get('OBSID')
   obs4=set(norm(x) for x in d[obscol]) if obscol else set()
  ok=np.isfinite(ra4)&np.isfinite(de4); c4=SkyCoord(ra4[ok]*u.deg,de4[ok]*u.deg); c5=SkyCoord(ra5*u.deg,de5*u.deg); _,sep,_=c5.match_to_catalog_sky(c4); s=sep.arcsec
  out={'success':True,'five_rows':len(t),'four_rows':len(ra4),'four_catalog_bytes':size,'four_obsid_column':obscol,
       'five_nonblank_obsid':int(np.sum(obs5!='')),'four_unique_nonblank_obsids':int(sum(bool(x) for x in obs4)),
       'unmatched_counts':{str(r):int(np.sum(s>r)) for r in (5,10,15,20,30)}}
  for r in (10,15,20,30):
   m=s>r; o=obs5[m]; non=o!=''; present=np.array([x in obs4 for x in o]) if len(o) else np.array([],bool)
   out[f'r{r}']={'n_unmatched':int(m.sum()),'nonblank_obsid':int(non.sum()),'obsid_present_in_4xmm':int((non&present).sum()),
                 'fraction_present_given_nonblank':float((non&present).sum()/non.sum()) if non.sum() else None}
  out['interpretation']='If a substantial conservative-unmatched cohort has a nonblank 5XMM ObsID already present in 4XMM-DR14, the reprocessing-recovery aperture is real. No identities emitted.'
  save(out)
 except Exception as e: save({'success':False,'error':f'{type(e).__name__}: {e}'})
if __name__=='__main__': main()

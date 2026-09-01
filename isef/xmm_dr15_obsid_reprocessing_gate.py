#!/usr/bin/env python3
"""Blinded exact-ObsID gate for the 5XMM reprocessing-recovery hypothesis.

No source names/coordinates are emitted. The frozen source sample is reconstructed
with SRCID added, and its positional-count fingerprint must reproduce the already
opened blind gate exactly before any ObsID result is accepted. Detection/observation
rows in 5XMM are then joined by SRCID and compared to the official 4XMM-DR14
observation list. No source identities are written.
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
U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz')
P4OBS=Path('/tmp/4xmmdr14_obslist.fits')
OUT=Path('results/xmm_dr15_obsid_reprocessing_gate.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='sum_flag < 3 AND extent = 0 AND ep_det_ml >= 15'
FINGERPRINT={'5':3301,'10':1944,'15':1640,'20':1420,'30':1081}

def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()

def save(x):
 OUT.write_text(json.dumps(x,indent=2,sort_keys=True,default=str)+'\n')
 print(json.dumps(x,indent=2,sort_keys=True,default=str))

def tap_table(query,timeout=180):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':query})
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-obsid-gate/1.2'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')

def download(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-obsid-gate/1.2'})
 with urllib.request.urlopen(req,timeout=180) as r,path.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
 return path.stat().st_size

def old_positions():
 if not P4.exists(): download(U4,P4)
 with fits.open(P4,memmap=True) as h:
  tabs=[z for z in h if isinstance(z,(fits.BinTableHDU,fits.TableHDU)) and z.data is not None]
  d=max(tabs,key=lambda z:len(z.data)).data; names={n.upper():n for n in d.names}
  return np.asarray(d[names['SC_RA']],float),np.asarray(d[names['SC_DEC']],float),len(d)

def old_obsids():
 if not P4OBS.exists(): download(U4OBS,P4OBS)
 with fits.open(P4OBS,memmap=True) as h:
  tabs=[z for z in h if isinstance(z,(fits.BinTableHDU,fits.TableHDU)) and z.data is not None]
  d=max(tabs,key=lambda z:len(z.data)).data; names={n.upper():n for n in d.names}
  c=names.get('OBS_ID') or names.get('OBSID') or names.get('OBSERVATION_ID')
  if not c: raise RuntimeError('Official DR14 obslist has no recognized ObsID column: '+','.join(d.names))
  vals={norm(x) for x in d[c] if norm(x)}
  return vals,len(d),c

def detection_obsids(srcids):
 # Query only the frozen unmatched identities, in small batches. Results are
 # aggregated immediately to per-source ObsID sets; no names/coordinates emitted.
 out={s:set() for s in srcids}
 ids=list(srcids)
 for i in range(0,len(ids),80):
  batch=ids[i:i+80]
  quoted=','.join("'"+s.replace("'","''")+"'" for s in batch)
  q=f'SELECT srcid,obsid FROM xmmstack WHERE srcid IN ({quoted})'
  t=tap_table(q,240)
  if 'srcid' not in t.colnames or 'obsid' not in t.colnames: raise RuntimeError('xmmstack query missing srcid/obsid')
  for sid,obs in zip(t['srcid'],t['obsid']):
   s=norm(sid); o=norm(obs)
   if s in out and o: out[s].add(o)
 return out

def main():
 try:
  # Adding SRCID must not change the frozen TOP-100000 sample. Reproduce its exact
  # positional fingerprint before using any detection-layer information.
  t=tap_table(f'SELECT TOP 100000 srcid,ra,dec FROM xmmssc WHERE {BASE}',240)
  src=np.asarray([norm(x) for x in t['srcid']]); ra5=np.asarray(t['ra'],float); de5=np.asarray(t['dec'],float)
  ra4,de4,n4=old_positions(); ok=np.isfinite(ra4)&np.isfinite(de4)
  c4=SkyCoord(ra4[ok]*u.deg,de4[ok]*u.deg); c5=SkyCoord(ra5*u.deg,de5*u.deg)
  _,sep,_=c5.match_to_catalog_sky(c4); s=sep.arcsec
  fp={str(r):int(np.sum(s>r)) for r in (5,10,15,20,30)}
  fingerprint_ok=(fp==FINGERPRINT)
  if not fingerprint_ok:
   save({'success':False,'science_status':'INVALID_SAMPLE_RECONSTRUCTION','observed_fingerprint':fp,'frozen_fingerprint':FINGERPRINT})
   return
  m20=s>20; unmatched=list(dict.fromkeys(src[m20].tolist()))
  if len(unmatched)!=FINGERPRINT['20']:
   save({'success':False,'science_status':'INVALID_DUPLICATE_SRCID_STRUCTURE','n_unmatched_rows':int(m20.sum()),'n_unique_unmatched_srcids':len(unmatched)})
   return
  oldset,nobs,obscol=old_obsids()
  det=detection_obsids(unmatched)
  with_nonblank=[sid for sid in unmatched if len(det.get(sid,set()))>0]
  oldhit=[sid for sid in with_nonblank if any(o in oldset for o in det[sid])]
  frac=(len(oldhit)/len(with_nonblank)) if with_nonblank else None
  gate1=len(unmatched)>=1000; gate2=len(oldhit)>=250; gate3=(frac is not None and frac>=0.25)
  out={'success':True,'science_status':'PASS' if gate1 and gate2 and gate3 else 'FAIL',
       'source_sample_rows':len(t),'positional_fingerprint':fp,'frozen_fingerprint_reproduced':True,
       'four_unique_source_rows':n4,'official_dr14_obslist_rows':nobs,'official_dr14_obsid_column':obscol,
       'official_dr14_unique_obsids':len(oldset),'n_unmatched_20arcsec':len(unmatched),
       'n_unmatched_with_detection_obsid':len(with_nonblank),'n_unmatched_with_any_dr14_obsid':len(oldhit),
       'fraction_dr14_given_nonblank':frac,
       'frozen_gates':{'g1_n_unmatched_ge_1000':gate1,'g2_old_obsid_hits_ge_250':gate2,'g3_old_fraction_ge_0p25':gate3},
       'privacy':'No source names, coordinates, SRCIDs, or individual ObsIDs emitted.'}
  save(out)
 except Exception as e:
  save({'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'})

if __name__=='__main__': main()

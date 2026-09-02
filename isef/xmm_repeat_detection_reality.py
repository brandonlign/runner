#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4OBS=Path('/tmp/4xmmdr14_obslist.fits'); OUT=Path('results/xmm_repeat_detection_reality.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 3 AND s.extent=0 AND s.ep_det_ml>=15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-repeat-reality/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-repeat-reality/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
def refs():
 if not P4.exists(): dl(U4,P4)
 if not P4OBS.exists(): dl(U4OBS,P4OBS)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float).copy(); de=np.asarray(d[nm['SC_DEC']],float).copy()
 with fits.open(P4OBS,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
 ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def qbin(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,d.obsid AS dobsid,d.pps_srcnum AS pps FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'cap {lo}-{hi}')
  mid=(lo+hi)/2; return qbin(lo,mid,depth+1)+qbin(mid,hi,depth+1)
 return [t]
def hemi(c4,old,a,b):
 counts=[]; total=0
 for lo in range(a,b,5):
  tabs=qbin(float(lo),float(lo+5)); t=vstack(tabs,metadata_conflicts='silent') if len(tabs)>1 else tabs[0]; by={}; obs=defaultdict(set)
  for sid,ra,de,ob in zip(t['sid'],t['sra'],t['sdec'],t['dobsid']):
   s=norm(sid)
   if s not in by: by[s]=(float(ra),float(de))
   o=norm(ob)
   if o in old: obs[s].add(o)
  ids=list(by)
  if not ids: continue
  c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4)
  cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and len(obs[ids[i]])>=1]; total+=len(cases); counts.extend(len(obs[s]) for s in cases)
 a2=sum(x>=2 for x in counts); a3=sum(x>=3 for x in counts)
 return {'recoveries':total,'ge2_distinct_old_obsid_detections':a2,'ge2_fraction':a2/total if total else None,'ge3_distinct_old_obsid_detections':a3,'ge3_fraction':a3/total if total else None,'max_distinct_old_obsid_detections':max(counts) if counts else 0}
def main():
 try:
  c4,old=refs(); d=hemi(c4,old,0,180); v=hemi(c4,old,180,360); passed=all(r['ge2_distinct_old_obsid_detections']>=50 and r['ge2_fraction']>=0.10 for r in (d,v)); out={'success':True,'development':d,'validation':v,'frozen_robustness_pass':passed,'privacy':'Aggregate counts only; no identities or coordinates emitted.'}
 except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

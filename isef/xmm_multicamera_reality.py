#!/usr/bin/env python3
"""Frozen aggregate multi-camera support test for strict 5XMM reprocessing recoveries."""
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
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4OBS=Path('/tmp/4xmmdr14_obslist.fits'); OUT=Path('results/xmm_multicamera_reality.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent = 0 AND s.ep_det_ml >= 15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def f(x):
 try:
  v=float(x); return v if np.isfinite(v) else np.nan
 except: return np.nan
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-multicamera-reality/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-multicamera-reality/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as z:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   z.write(b)
def refs():
 if not P4.exists(): dl(U4,P4)
 if not P4OBS.exists(): dl(U4OBS,P4OBS)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float).copy(); de=np.asarray(d[nm['SC_DEC']],float).copy()
 with fits.open(P4OBS,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
 ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def q(lo,hi,depth=0):
 s=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,d.obsid AS obsid,d.pps_srcnum AS pps,d.pn_det_ml AS pn,d.m1_det_ml AS m1,d.m2_det_ml AS m2 FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid WHERE {BASE} AND s.ra >= {lo:.8f} AND s.ra < {hi:.8f} AND d.pps_srcnum IS NOT NULL'''; t=tap(s)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'cap persists {lo}-{hi}')
  m=(lo+hi)/2; return q(lo,m,depth+1)+q(m,hi,depth+1)
 return [t]
def cat(ts): return vstack(ts,metadata_conflicts='silent') if len(ts)>1 else ts[0]
def hemi(lo,hi,c4,old):
 by={}; obs=defaultdict(set); cams=defaultdict(lambda:[-np.inf,-np.inf,-np.inf])
 for b in range(int(lo),int(hi),5):
  t=cat(q(float(b),float(min(b+5,hi))))
  for sid,ra,de,ob,pn,m1,m2 in zip(t['sid'],t['sra'],t['sdec'],t['obsid'],t['pn'],t['m1'],t['m2']):
   s=norm(sid); o=norm(ob)
   if s not in by: by[s]=(float(ra),float(de))
   if o in old:
    obs[s].add(o)
    for j,x in enumerate((pn,m1,m2)):
     v=f(x)
     if np.isfinite(v): cams[s][j]=max(cams[s][j],v)
 ids=list(by); c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4)
 cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and bool(obs[ids[i]])]
 hist={str(k):0 for k in range(4)}; ge2_6=0; ge2_10=0; any6=0
 for s in cases:
  a=np.array(cams[s]); n6=int(np.sum(a>=6)); n10=int(np.sum(a>=10)); hist[str(n6)]+=1; any6+=int(n6>=1); ge2_6+=int(n6>=2); ge2_10+=int(n10>=2)
 frac=ge2_6/len(cases) if cases else None
 return {'recoveries':len(cases),'camera_support_hist_ge6':hist,'at_least_one_camera_ge6':any6,'at_least_two_cameras_ge6':ge2_6,'fraction_ge2_cameras_ge6':frac,'at_least_two_cameras_ge10':ge2_10,'gate_count_ge150':ge2_6>=150,'gate_fraction_ge0p25':frac is not None and frac>=.25}
def main():
 try:
  c4,old=refs(); dev=hemi(0,180,c4,old); val=hemi(180,360,c4,old); passed=dev['gate_count_ge150'] and dev['gate_fraction_ge0p25'] and val['gate_count_ge150'] and val['gate_fraction_ge0p25']; out={'success':True,'science_status':'PASS' if passed else 'FAIL','development':dev,'validation':val,'camera_threshold_ml':6,'descriptive_second_threshold_ml':10,'privacy':'Aggregate counts only; no identities or coordinates emitted.'}
 except Exception as e: out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

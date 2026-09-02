#!/usr/bin/env python3
"""Prepared aggregate-only counter for preregistered development outlier aperture.
DO NOT RUN unless the separately frozen multi-camera project gate has passed."""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz';U4O='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits';P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz');P4O=Path('/tmp/4xmmdr14_obslist.fits');OUT=Path('results/xmm_high_reality_outlier_candidate_count.json');OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent=0 AND s.ep_det_ml>=15'
def n(x):
 if isinstance(x,(bytes,np.bytes_)):x=x.decode('utf-8','replace')
 return str(x).strip()
def f(x):
 try:
  v=float(x);return v if np.isfinite(v) else np.nan
 except:return np.nan
def valid(x):
 z=n(x);return bool(z and z not in ('--','None','nan','null'))
def tap(q):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q});req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-outlier-count/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r:return Table.read(io.BytesIO(r.read()),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-outlier-count/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as g:
  while 1:
   b=r.read(8388608)
   if not b:break
   g.write(b)
def refs():
 if not P4.exists():dl(U4,P4)
 if not P4O.exists():dl(U4O,P4O)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};ra=np.asarray(d[nm['SC_RA']],float);de=np.asarray(d[nm['SC_DEC']],float)
 with fits.open(P4O,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};old={n(x) for x in d[nm['OBS_ID']] if n(x)}
 ok=np.isfinite(ra)&np.isfinite(de);return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def qb(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,s.classx_outlier outlier,s.gaiadr3_source_id gid,s.gaia_match_prob gp,s.wise_name wn,s.wise_match_prob wp,s.classopt_class oc,d.obsid obsid,d.pn_det_ml pn,d.m1_det_ml m1,d.m2_det_ml m2 FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL''';t=tap(q)
 if len(t)>=CAP:
  if depth>=8:raise RuntimeError('cap')
  m=(lo+hi)/2;return qb(lo,m,depth+1)+qb(m,hi,depth+1)
 return [t]
def main():
 try:
  c4,old=refs();p={};obs=defaultdict(set);cams=defaultdict(lambda:[-np.inf]*3)
  for lo in range(0,180,5):
   ts=qb(lo,lo+5);t=vstack(ts,metadata_conflicts='silent') if len(ts)>1 else ts[0]
   for r in t:
    s=n(r['sid']);p.setdefault(s,{'ra':f(r['sra']),'dec':f(r['sdec']),'outlier':f(r['outlier']),'gaia':valid(r['gid']) and f(r['gp'])>=.8,'wise':valid(r['wn']) and f(r['wp'])>=.8,'opt':valid(r['oc'])});o=n(r['obsid'])
    if o in old:
     obs[s].add(o)
     for j,k in enumerate(('pn','m1','m2')):
      v=f(r[k]);cams[s][j]=max(cams[s][j],v) if np.isfinite(v) else cams[s][j]
  ids=list(p);c=SkyCoord([p[s]['ra'] for s in ids]*u.deg,[p[s]['dec'] for s in ids]*u.deg);_,sep,_=c.match_to_catalog_sky(c4);rec=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and obs[ids[i]]];multi=[s for s in rec if sum(np.array(cams[s])>=6)>=2];outl=[s for s in multi if np.isfinite(p[s]['outlier']) and p[s]['outlier']>5];blank=[s for s in outl if not p[s]['gaia'] and not p[s]['wise'] and not p[s]['opt']];out={'success':True,'development_strict_recoveries':len(rec),'multicamera_ge2':len(multi),'multicamera_and_outlier_gt5':len(outl),'final_preregistered_candidate_pool_count':len(blank),'aggregate_feasibility_gate_ge10':len(blank)>=10,'privacy':'No identities or coordinates emitted.'}
 except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()

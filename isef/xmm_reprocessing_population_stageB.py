#!/usr/bin/env python3
"""Frozen Stage B census for the 5XMM reprocessing-recovery project.
Validation hemisphere only: 180 <= RA < 360 deg. No identities/coordinates emitted.
"""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'
U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4OBS=Path('/tmp/4xmmdr14_obslist.fits')
OUT=Path('results/xmm_reprocessing_population_stageB.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 3 AND s.extent = 0 AND s.ep_det_ml >= 15'; CAP=100000
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q})
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-population-stageB/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def download(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-population-stageB/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,path.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
def old_positions():
 if not P4.exists(): download(U4,P4)
 with fits.open(P4,memmap=True) as h:
  tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]
  d=max(tabs,key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}
  return np.asarray(d[nm['SC_RA']],float).copy(),np.asarray(d[nm['SC_DEC']],float).copy(),len(d)
def old_obsids():
 if not P4OBS.exists(): download(U4OBS,P4OBS)
 with fits.open(P4OBS,memmap=True) as h:
  tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]
  d=max(tabs,key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; c=nm['OBS_ID']
  return {norm(x) for x in d[c] if norm(x)},len(d)
def query_interval(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,d.obsid AS dobsid
FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid
WHERE {BASE} AND s.ra >= {lo:.8f} AND s.ra < {hi:.8f}'''
 t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'row cap persists at {lo}-{hi}')
  mid=(lo+hi)/2; a,la=query_interval(lo,mid,depth+1); b,lb=query_interval(mid,hi,depth+1)
  return (a,b),la+lb
 return t,[{'ra_lo':lo,'ra_hi':hi,'join_rows':len(t),'depth':depth}]
def flatten(x):
 if isinstance(x,tuple):
  for z in x: yield from flatten(z)
 else: yield x
def score_table(t,c4,oldset):
 by={}; obs=defaultdict(set)
 for sid,ra,de,ob in zip(t['sid'],t['sra'],t['sdec'],t['dobsid']):
  s=norm(sid)
  if s not in by: by[s]=(float(ra),float(de))
  o=norm(ob)
  if o and o not in ('--','None','nan'): obs[s].add(o)
 if not by: return {'eligible':0,'positionally_unmatched':0,'reprocessing_recovered':0,'with_nonblank_obsid':0}
 ids=list(by); ra=np.array([by[s][0] for s in ids]); de=np.array([by[s][1] for s in ids])
 _,sep,_=SkyCoord(ra*u.deg,de*u.deg).match_to_catalog_sky(c4); un=[ids[i] for i in np.flatnonzero(sep.arcsec>20)]
 rep=[s for s in un if any(o in oldset for o in obs.get(s,set()))]
 return {'eligible':len(ids),'positionally_unmatched':len(un),'reprocessing_recovered':len(rep),'with_nonblank_obsid':sum(bool(obs.get(s)) for s in ids)}
def main():
 try:
  ra4,de4,n4=old_positions(); ok=np.isfinite(ra4)&np.isfinite(de4); c4=SkyCoord(ra4[ok]*u.deg,de4[ok]*u.deg); oldset,nobs=old_obsids()
  bins=[]; leaves=[]
  for lo in range(180,360,5):
   tree,meta=query_interval(float(lo),float(lo+5)); leaves.extend(meta); agg={'eligible':0,'positionally_unmatched':0,'reprocessing_recovered':0,'with_nonblank_obsid':0}
   for t in flatten(tree):
    s=score_table(t,c4,oldset)
    for k in agg: agg[k]+=s[k]
   bins.append({'ra_lo':lo,'ra_hi':lo+5,**agg}); print(json.dumps({'progress_bin':f'{lo}-{lo+5}',**agg}),flush=True)
  total={k:sum(b[k] for b in bins) for k in ('eligible','positionally_unmatched','reprocessing_recovered','with_nonblank_obsid')}; prev=total['reprocessing_recovered']/total['eligible'] if total['eligible'] else None
  g1=total['reprocessing_recovered']>=500; g2=prev is not None and prev>=0.001
  out={'success':True,'science_status':'PASS' if g1 and g2 else 'FAIL','hemisphere':'validation','ra_range_deg':[180,360],'four_unique_source_rows':n4,'official_dr14_obslist_rows':nobs,'official_dr14_unique_obsids':len(oldset),'totals':total,'reprocessing_prevalence':prev,'frozen_gates':{'g1_reprocessing_recovered_ge_500':g1,'g2_prevalence_ge_0p001':g2},'bins':bins,'query_leaves':leaves,'privacy':'Only aggregate/bin counts emitted; no source identities or coordinates.'}
 except Exception as e: out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

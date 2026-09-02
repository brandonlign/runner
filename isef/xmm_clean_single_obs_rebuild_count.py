#!/usr/bin/env python3
"""Frozen Stage R1: count prior-catalogue-clean single-observation 5XMM recoveries.
Aggregate-only output; no source identities or coordinates emitted."""
from pathlib import Path
from collections import defaultdict
import gzip,shutil,io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4O='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
U4S='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s.fits.gz'
P4=Path('/tmp/4main.fits.gz'); P4O=Path('/tmp/4main_obs.fits'); P4SG=Path('/tmp/4stack.fits.gz'); P4S=Path('/tmp/4stack.fits')
OUT=Path('results/xmm_clean_single_obs_rebuild_count.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent=0 AND s.ep_det_ml>=15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-clean-single-R1/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:return Table.read(io.BytesIO(r.read()),format='votable')
def dl(url,p,timeout=1200):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-clean-single-R1/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r,p.open('wb') as f:
  while True:
   b=r.read(16*1024*1024)
   if not b: break
   f.write(b)
def coords_from(path):
 with fits.open(path,memmap=True) as h:
  tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]; d=max(tabs,key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}
  for a,b in [('SC_RA','SC_DEC'),('RA','DEC'),('SRC_RA','SRC_DEC'),('SOURCE_RA','SOURCE_DEC')]:
   if a in nm and b in nm:
    ra=np.asarray(d[nm[a]],float).copy(); de=np.asarray(d[nm[b]],float).copy(); ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),int(np.sum(ok))
 raise RuntimeError('no coordinates')
def obsids(path):
 with fits.open(path,memmap=False) as h:
  tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]; d=max(tabs,key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; c=nm.get('OBS_ID') or nm.get('OBSID'); return {norm(x) for x in d[c] if norm(x)}
def refs():
 if not P4.exists(): dl(U4,P4,300)
 if not P4O.exists(): dl(U4O,P4O,300)
 if not P4SG.exists(): dl(U4S,P4SG,1200)
 if not P4S.exists():
  with gzip.open(P4SG,'rb') as src,P4S.open('wb') as dst: shutil.copyfileobj(src,dst,length=32*1024*1024)
 return coords_from(P4)[0],coords_from(P4S)[0],obsids(P4O)
def qb(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,s.n_contrib ncontrib,d.obsid obsid FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'cap {lo}-{hi}')
  m=(lo+hi)/2; return qb(lo,m,depth+1)+qb(m,hi,depth+1)
 return [t]
def hemi(lo,hi,cmain,cstack,oldmain):
 by={}; obs=defaultdict(set); nc={}
 for b in range(lo,hi,5):
  ts=qb(float(b),float(b+5)); t=vstack(ts,metadata_conflicts='silent') if len(ts)>1 else ts[0]
  for sid,ra,de,ncon,ob in zip(t['sid'],t['sra'],t['sdec'],t['ncontrib'],t['obsid']):
   s=norm(sid); by.setdefault(s,(float(ra),float(de)))
   try: nc.setdefault(s,int(ncon))
   except: pass
   o=norm(ob)
   if o in oldmain: obs[s].add(o)
 ids=[s for s in by if obs[s]]
 c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg); _,sm,_=c.match_to_catalog_sky(cmain)
 mainclean=[ids[i] for i in range(len(ids)) if sm.arcsec[i]>20]
 cc=SkyCoord([by[s][0] for s in mainclean]*u.deg,[by[s][1] for s in mainclean]*u.deg); _,ss,_=cc.match_to_catalog_sky(cstack)
 clean=[mainclean[i] for i in range(len(mainclean)) if ss.arcsec[i]>20]
 single=sum(nc.get(s)==1 for s in clean)
 return {'strict_main_only':len(mainclean),'prior_catalogue_clean':len(clean),'clean_n_contrib_eq_1':single,'clean_single_fraction':single/len(clean) if clean else None,'gate_count_ge_100':single>=100}
def main():
 try:
  cm,cs,old=refs(); dev=hemi(0,180,cm,cs,old); val=hemi(180,360,cm,cs,old); out={'success':True,'science_status':'PASS' if dev['gate_count_ge_100'] and val['gate_count_ge_100'] else 'FAIL','development':dev,'validation':val,'frozen_gate':'clean_n_contrib_eq_1 >= 100 in each hemisphere','privacy':'Aggregate counts only; no identities or coordinates emitted.'}
 except Exception as e: out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

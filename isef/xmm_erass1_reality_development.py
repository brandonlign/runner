#!/usr/bin/env python3
"""Frozen development eRASS1 external-reality test for 5XMM reprocessing recoveries.
No source identities or coordinates are emitted."""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from scipy.stats import fisher_exact
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'
U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4OBS=Path('/tmp/4xmmdr14_obslist.fits')
OUT=Path('results/xmm_erass1_reality_development.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 3 AND s.extent = 0 AND s.ep_det_ml >= 15'; CAP=100000; RADIUS=15.0; PAD=0.01

def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-eRASS1-reality/1.1'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-eRASS1-reality/1.1'})
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
def q5(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,d.obsid AS dobsid,d.pps_srcnum AS pps FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid WHERE {BASE} AND s.ra >= {lo:.8f} AND s.ra < {hi:.8f} AND d.pps_srcnum IS NOT NULL'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'5XMM row cap persists {lo}-{hi}')
  mid=(lo+hi)/2; return q5(lo,mid,depth+1)+q5(mid,hi,depth+1)
 return [t]
def qe_plain(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} ra,dec FROM erass1main WHERE ra >= {lo:.8f} AND ra < {hi:.8f}'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'eRASS1 row cap persists {lo}-{hi}')
  mid=(lo+hi)/2; return qe_plain(lo,mid,depth+1)+qe_plain(mid,hi,depth+1)
 return [t]
def qe_wrapped(lo,hi):
 tabs=[]
 if lo<0:
  tabs.extend(qe_plain(360.0+lo,360.0)); lo=0.0
 if hi>360:
  tabs.extend(qe_plain(0.0,hi-360.0)); hi=360.0
 if hi>lo: tabs.extend(qe_plain(lo,hi))
 return tabs
def cat(tabs):
 if not tabs: return Table()
 return vstack(tabs,metadata_conflicts='silent') if len(tabs)>1 else tabs[0]
def main():
 try:
  c4,old=refs(); totals={'cases':0,'real_matches':0,'shift_matches':0,'both':0,'real_only':0,'shift_only':0,'neither':0}; bins=[]
  for lo in range(0,180,5):
   t=cat(q5(float(lo),float(lo+5))); by={}; obs=defaultdict(set)
   for sid,ra,de,ob in zip(t['sid'],t['sra'],t['sdec'],t['dobsid']):
    s=norm(sid)
    if s not in by: by[s]=(float(ra),float(de))
    o=norm(ob)
    if o and o not in ('--','None','nan'): obs[s].add(o)
   ids=list(by)
   if not ids: continue
   c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4)
   cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and any(o in old for o in obs[ids[i]])]
   et=cat(qe_wrapped(float(lo)-PAD,float(lo+6)+PAD)); ec=SkyCoord(np.asarray(et['ra'],float)*u.deg,np.asarray(et['dec'],float)*u.deg) if len(et) else None
   br={'cases':len(cases),'real_matches':0,'shift_matches':0,'both':0,'real_only':0,'shift_only':0,'neither':0}
   for s in cases:
    ra,de=by[s]; real=False; shifted=False
    if ec is not None:
     _,sr,_=SkyCoord(ra*u.deg,de*u.deg).match_to_catalog_sky(ec); real=bool(sr.arcsec<=RADIUS)
     _,ss,_=SkyCoord(((ra+1.0)%360)*u.deg,de*u.deg).match_to_catalog_sky(ec); shifted=bool(ss.arcsec<=RADIUS)
    br['real_matches']+=int(real); br['shift_matches']+=int(shifted)
    if real and shifted: br['both']+=1
    elif real: br['real_only']+=1
    elif shifted: br['shift_only']+=1
    else: br['neither']+=1
   for k in totals: totals[k]+=br[k]
   bins.append({'ra_lo':lo,'ra_hi':lo+5,**br}); print(json.dumps({'bin':f'{lo}-{lo+5}',**br}),flush=True)
  n=totals['cases']; rm=totals['real_matches']; sm=totals['shift_matches']; odds,p=fisher_exact([[rm,n-rm],[sm,n-sm]],alternative='greater'); ratio=(rm/sm) if sm else None
  gates={'g1_real_matches_ge_25':rm>=25,'g2_real_to_shift_ratio_ge_5':(sm==0 or rm>=5*sm),'g3_fisher_p_le_0p001':p<=0.001}
  out={'success':True,'hemisphere':'development','match_radius_arcsec':RADIUS,'shift_ra_deg':1.0,'query_padding_deg':PAD,'totals':totals,'real_match_fraction':rm/n if n else None,'shift_match_fraction':sm/n if n else None,'real_to_shift_ratio':ratio,'fisher_odds_ratio':float(odds),'fisher_one_sided_p':float(p),'frozen_gates':gates,'science_status':'PASS' if all(gates.values()) else 'FAIL','bins':bins,'privacy':'Aggregate counts only; no source identities or coordinates emitted.'}
 except Exception as e: out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

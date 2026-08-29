#!/usr/bin/env python3
"""Development-only positional gate for the frozen 5XMM reprocessing study.

Uses even 30-degree RA sectors only. Reads identifiers, positions, positional errors,
quality/extent and detection likelihood needed for the frozen cohort. It does NOT read
spectral, flux, hardness, variability, source-name, classification, or counterpart fields.
No candidate identities/coordinates are emitted; only aggregate statistics.
"""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
OUT=Path('results/xmm_development_positional_gate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';T5='xmmstack'
EP4='https://sky.esa.int/esasky-tap/tap/sync';T4='catalogues.mv_xsa_epic_stack_cat_fdw'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz';U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
SECTORS=(0,2,4,6,8,10); RADII=(5.,7.,10.,15.); MARGIN=.02

def cv(x):
 if np.ma.is_masked(x):return None
 if isinstance(x,(bytes,np.bytes_)):return x.decode('utf-8','replace').strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x

def tap(ep,q,timeout=300):
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode(); req=urllib.request.Request(ep,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-positional-gate/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:cv(rr[n]) for n in t.colnames} for rr in t]

def load_stacks(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-positional-gate/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,path.open('wb') as f:
  while True:
   b=r.read(1<<20)
   if not b:break
   f.write(b)
 with fits.open(path,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names];d=max(tabs,key=lambda z:len(z.data)).data
  stacks=defaultdict(set);rev=defaultdict(set)
  for row in d:
   s=str(cv(row['STACK_ID']));o=str(cv(row['OBS_ID']));stacks[s].add(o);rev[o].add(s)
  return dict(stacks),dict(rev)

def exact_pairs():
 s4,r4=load_stacks(U4,Path('/tmp/p4.gz'));s5,r5=load_stacks(U5,Path('/tmp/p5.gz'))
 bad4={s for o,v in r4.items() if len(v)>1 for s in v};bad5={s for o,v in r5.items() if len(v)>1 for s in v}
 by5=defaultdict(list)
 for s,obs in s5.items():by5[frozenset(obs)].append(s)
 pairs=[]
 for a,obs in s4.items():
  for b in by5.get(frozenset(obs),[]):
   if a not in bad4 and b not in bad5:pairs.append((a,b))
 p4={a:b for a,b in pairs};p5={b:a for a,b in pairs}
 e4={o:next(iter(v)) for o,v in r4.items() if len(v)==1 and next(iter(v)) in p4}
 e5={o:next(iter(v)) for o,v in r5.items() if len(v)==1 and next(iter(v)) in p5}
 return p4,p5,e4,e5

def ra_clause(lo,hi,margin=0):
 a=lo-margin;b=hi+margin
 if a<0:return f'(ra >= {360+a:.8f} OR ra < {b:.8f})'
 if b>=360:return f'(ra >= {a:.8f} OR ra < {b-360:.8f})'
 return f'(ra >= {a:.8f} AND ra < {b:.8f})'

def parent(srcid,emap):
 s=str(srcid)
 if len(s)!=16 or not s.startswith('3') or not s.isdigit():return None
 return emap.get(s[1:11])

def qtile(x,qs=(.5,.9,.95,.99)):
 a=np.asarray(x,float);a=a[np.isfinite(a)]
 return {str(q):float(np.quantile(a,q)) for q in qs} if len(a) else {}

def group5(rows,e5):
 g=defaultdict(list)
 for r in rows:
  b=parent(r['srcid'],e5)
  if b:g[b].append(r)
 return g

def nearest_stats(d5,d4,map5to4,e5,e4):
 g4=defaultdict(list)
 for r in d4:
  a=parent(r['srcid'],e4)
  if a:g4[a].append(r)
 seps=[];errscaled=[];shift_seps=[];tested=0;empty_parent=0
 for b,rows in group5(d5,e5).items():
  a_pair=map5to4.get(b); old=g4.get(a_pair,[])
  if not old:
   empty_parent+=len(rows);continue
  c4=SkyCoord([float(r['ra']) for r in old]*u.deg,[float(r['dec']) for r in old]*u.deg)
  c5=SkyCoord([float(r['ra']) for r in rows]*u.deg,[float(r['dec']) for r in rows]*u.deg)
  idx,sep,_=c5.match_to_catalog_sky(c4); ss=sep.arcsec
  seps.extend(ss.tolist());tested+=len(rows)
  for r,i,s in zip(rows,idx,ss):
   e5v=float(r['error_radius']) if r.get('error_radius') is not None else np.nan
   e4v=float(old[int(i)]['radec_err']) if old[int(i)].get('radec_err') is not None else np.nan
   den=max(1.0,(e5v if np.isfinite(e5v) else 0)+(e4v if np.isfinite(e4v) else 0))
   errscaled.append(float(s)/den)
  ras=np.array([float(r['ra']) for r in rows]);decs=np.array([float(r['dec']) for r in rows])
  dra=(60./3600.)/np.maximum(np.cos(np.deg2rad(decs)),.0872)
  shifted=SkyCoord(((ras+dra)%360)*u.deg,decs*u.deg)
  _,sep_shift,_=shifted.match_to_catalog_sky(c4);shift_seps.extend(sep_shift.arcsec.tolist())
 arr=np.asarray(seps)
 denom=tested+empty_parent
 return {'tested':tested,'parents_without_dr14_sources':empty_parent,'nearest_arcsec_quantiles':qtile(seps),'error_scaled_quantiles':qtile(errscaled),'random_shift_nearest_arcsec_quantiles':qtile(shift_seps),'counts_no_dr14_within_arcsec':{str(r):int(np.sum(arr>r))+empty_parent for r in RADII},'fractions_no_dr14_within_arcsec':{str(r):(int(np.sum(arr>r))+empty_parent)/denom if denom else None for r in RADII},'random_shift_fractions_within_arcsec':{str(r):float(np.mean(np.asarray(shift_seps)<=r)) if shift_seps else None for r in RADII}}

def main():
 try:
  map4to5,map5to4,e4,e5=exact_pairs();sector_results={};all5=[];all4=[]
  for sec in SECTORS:
   lo=sec*30.;hi=lo+30.;cl5=ra_clause(lo,hi,0);cl4=ra_clause(lo,hi,MARGIN)
   q5=f"SELECT TOP 200000 srcid,ra,dec,error_radius,extent,sum_flag,stack_det_ml,n_obs FROM {T5} WHERE n_obs IS NOT NULL AND {cl5} AND sum_flag=0 AND extent=0 AND stack_det_ml>=10"
   q4=f"SELECT TOP 200000 srcid,ra,dec,radec_err,n_obs FROM {T4} WHERE n_obs IS NOT NULL AND {cl4}"
   r5=tap(EP5,q5);r4=tap(EP4,q4)
   k5=[r for r in r5 if parent(r['srcid'],e5) in map5to4]
   k4=[r for r in r4 if parent(r['srcid'],e4) in map4to5]
   st=nearest_stats(k5,k4,map5to4,e5,e4)
   st.update({'sector':sec,'ra_range':[lo,hi],'queried_dr15_clean':len(r5),'eligible_dr15_exact_input':len(k5),'queried_dr14s_all':len(r4),'eligible_dr14s_exact_input':len(k4)})
   sector_results[str(sec)]=st;all5.extend(k5);all4.extend(k4)
  pooled=nearest_stats(all5,all4,map5to4,e5,e4)
  out={'success':True,'status':'DEVELOPMENT_ONLY','holdout_opened':False,'exact_pairs':len(map4to5),'selection':'DR15 summary SUM_FLAG=0, EXTENT=0, STACK_DET_ML>=10, even 30-degree RA sectors only; DR14s positional reference uses all summary sources in paired stacks','sector_results':sector_results,'pooled':pooled,'decision':'POSITIONAL_COHORT_VIABLE' if pooled['tested']>=1000 and pooled['counts_no_dr14_within_arcsec']['15.0']>=50 else 'POSITIONAL_COHORT_WEAK','note':'No flux/spectral/hardness/variability/name/classification/counterpart fields were read or emitted.'}
 except Exception as e:out={'success':False,'status':'DEVELOPMENT_ONLY','holdout_opened':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

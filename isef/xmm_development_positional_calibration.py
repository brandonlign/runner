#!/usr/bin/env python3
"""Development-only multi-offset astrometric calibration for 5XMM vs 4XMM-DR14s.

Uses only even 30-degree RA sectors and the exact-input stack cohort. Scientific
outcome fields (flux, spectrum, hardness, variability, names, classifications,
counterparts) are intentionally not queried. Outputs aggregates only.
"""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
OUT=Path('results/xmm_development_positional_calibration.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';T5='xmmstack'
EP4='https://sky.esa.int/esasky-tap/tap/sync';T4='catalogues.mv_xsa_epic_stack_cat_fdw'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz';U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
SECTORS=(0,2,4,6,8,10); RADII=np.array([2.,3.,4.,5.,6.,7.,8.,10.,12.,15.])
# deterministic sky offsets in arcsec; all selected before outcome inspection
OFFSETS=((60,0),(-60,0),(0,60),(0,-60),(120,0),(-120,0),(0,120),(0,-120))
MARGIN=.04

def cv(x):
 if np.ma.is_masked(x):return None
 if isinstance(x,(bytes,np.bytes_)):return x.decode('utf-8','replace').strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x

def tap(ep,q,timeout=360):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-pos-cal/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:cv(rr[n]) for n in t.colnames} for rr in t]

def load(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-pos-cal/1.0'})
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

def maps():
 s4,r4=load(U4,Path('/tmp/c4.gz'));s5,r5=load(U5,Path('/tmp/c5.gz'))
 bad4={s for _,v in r4.items() if len(v)>1 for s in v};bad5={s for _,v in r5.items() if len(v)>1 for s in v}
 by5=defaultdict(list)
 for s,o in s5.items():by5[frozenset(o)].append(s)
 pairs=[(a,b) for a,o in s4.items() for b in by5.get(frozenset(o),[]) if a not in bad4 and b not in bad5]
 m45=dict(pairs);m54={b:a for a,b in pairs}
 e4={o:next(iter(v)) for o,v in r4.items() if len(v)==1 and next(iter(v)) in m45}
 e5={o:next(iter(v)) for o,v in r5.items() if len(v)==1 and next(iter(v)) in m54}
 return m45,m54,e4,e5

def par(s,e):
 x=str(s);return e.get(x[1:11]) if len(x)==16 and x.startswith('3') and x.isdigit() else None

def clause(lo,hi,margin=0):
 a=lo-margin;b=hi+margin
 if a<0:return f'(ra>={360+a:.8f} OR ra<{b:.8f})'
 if b>=360:return f'(ra>={a:.8f} OR ra<{b-360:.8f})'
 return f'(ra>={a:.8f} AND ra<{b:.8f})'

def shifted(ra,dec,dx,dy):
 # dx,dy are tangent-plane arcsec; adequate at these tiny offsets
 d2=np.clip(dec+dy/3600.,-89.999,89.999)
 dra=(dx/3600.)/np.maximum(np.cos(np.deg2rad(d2)),0.01745)
 return (ra+dra)%360.,d2

def compute(r5,r4,m54,e5,e4):
 g4=defaultdict(list);g5=defaultdict(list)
 for r in r4:
  a=par(r['srcid'],e4)
  if a:g4[a].append(r)
 for r in r5:
  b=par(r['srcid'],e5)
  if b:g5[b].append(r)
 real=[];null=[[] for _ in OFFSETS];err5=[];err4=[]
 for b,rows in g5.items():
  old=g4.get(m54.get(b),[])
  if not old:continue
  c4=SkyCoord(np.array([float(x['ra']) for x in old])*u.deg,np.array([float(x['dec']) for x in old])*u.deg)
  ra=np.array([float(x['ra']) for x in rows]);dec=np.array([float(x['dec']) for x in rows])
  c5=SkyCoord(ra*u.deg,dec*u.deg);idx,sep,_=c5.match_to_catalog_sky(c4);real.extend(sep.arcsec.tolist())
  err5.extend([float(x['error_radius']) if x.get('error_radius') is not None else np.nan for x in rows])
  err4.extend([float(old[int(i)]['radec_err']) if old[int(i)].get('radec_err') is not None else np.nan for i in idx])
  for j,(dx,dy) in enumerate(OFFSETS):
   rr,dd=shifted(ra,dec,dx,dy);cs=SkyCoord(rr*u.deg,dd*u.deg);_,sp,_=cs.match_to_catalog_sky(c4);null[j].extend(sp.arcsec.tolist())
 real=np.asarray(real); nulls=[np.asarray(x) for x in null];n=len(real)
 curves=[]
 for rad in RADII:
  observed=float(np.mean(real<=rad)) if n else np.nan
  nfs=[float(np.mean(x<=rad)) for x in nulls]
  chance=float(np.mean(nfs));chance_sd=float(np.std(nfs,ddof=1))
  fdr=chance/observed if observed>0 else None
  unmatched=1-observed
  curves.append({'radius_arcsec':float(rad),'observed_match_fraction':observed,'unmatched_fraction':unmatched,'null_match_fraction_mean':chance,'null_match_fraction_sd':chance_sd,'estimated_match_fdr_ratio':fdr,'null_by_offset':nfs})
 core=real[real<=5]
 # empirical normalized separation only for 5-arcsec core; report error scaling for matched core separately
 e5a=np.asarray(err5);e4a=np.asarray(err4);den=np.sqrt(np.nan_to_num(e5a)**2+np.nan_to_num(e4a)**2);den=np.maximum(den,.25)
 scaled=real/den;mask=real<=5
 return {'n':n,'curves':curves,'real_sep_quantiles':{str(q):float(np.quantile(real,q)) for q in (.5,.8,.85,.9,.95,.99)},'core_le5_sep_quantiles':{str(q):float(np.quantile(core,q)) for q in (.5,.9,.95,.99)},'core_le5_error_scaled_quantiles':{str(q):float(np.quantile(scaled[mask],q)) for q in (.5,.9,.95,.99)}}

def main():
 try:
  m45,m54,e4,e5=maps();all4=[];r5_by_threshold={10:[],15:[]};counts={}
  for sec in SECTORS:
   lo=sec*30.;hi=lo+30.
   r4=tap(EP4,f"SELECT TOP 200000 srcid,ra,dec,radec_err,n_obs FROM {T4} WHERE n_obs IS NOT NULL AND {clause(lo,hi,MARGIN)}")
   base=tap(EP5,f"SELECT TOP 200000 srcid,ra,dec,error_radius,extent,sum_flag,stack_det_ml,n_obs FROM {T5} WHERE n_obs IS NOT NULL AND {clause(lo,hi)} AND sum_flag=0 AND extent=0 AND stack_det_ml>=10")
   k4=[r for r in r4 if par(r['srcid'],e4) in m45];k10=[r for r in base if par(r['srcid'],e5) in m54];k15=[r for r in k10 if float(r['stack_det_ml'])>=15]
   all4.extend(k4);r5_by_threshold[10].extend(k10);r5_by_threshold[15].extend(k15)
   counts[str(sec)]={'raw_dr14':len(r4),'raw_dr15_ml10':len(base),'eligible_dr14':len(k4),'eligible_dr15_ml10':len(k10),'eligible_dr15_ml15':len(k15),'top_truncated':len(r4)>=200000 or len(base)>=200000}
  res10=compute(r5_by_threshold[10],all4,m54,e5,e4);res15=compute(r5_by_threshold[15],all4,m54,e5,e4)
  # freeze recommendation by objective development rule: smallest radius >=3 arcsec with >=99% of 5-arcsec core retained and estimated match FDR <=1%.
  core5=res10['curves'][3]['observed_match_fraction']
  eligible=[]
  for z in res10['curves']:
   retention=z['observed_match_fraction']/core5 if core5 else 0
   if z['radius_arcsec']>=3 and retention>=.99 and (z['estimated_match_fdr_ratio'] or 1)<=.01:eligible.append(z['radius_arcsec'])
  rec=min(eligible) if eligible else None
  out={'success':True,'status':'DEVELOPMENT_ONLY','holdout_opened':False,'exact_pairs':len(m45),'offsets_arcsec':[list(x) for x in OFFSETS],'sector_query_counts':counts,'ml10':res10,'ml15_sensitivity':res15,'objective_rule':'Choose smallest radius >=3 arcsec retaining >=99% of matches found by 5 arcsec while estimated null/observed match ratio <=1%.','recommended_primary_radius_arcsec':rec,'decision':'CALIBRATION_PASS' if rec is not None and res15['n']>=1000 else 'CALIBRATION_NEEDS_WORK','note':'No flux/spectral/hardness/variability/name/classification/counterpart fields queried or emitted.'}
 except Exception as e:out={'success':False,'status':'DEVELOPMENT_ONLY','holdout_opened':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

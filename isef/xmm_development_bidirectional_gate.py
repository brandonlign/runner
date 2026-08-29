#!/usr/bin/env python3
"""Development-only bidirectional 4XMM-DR14s <-> 5XMM positional comparison.

Aggregate counts only; no flux, spectrum, variability, identity or counterpart fields.
Even RA sectors only. Exact-input stack pairs only.
"""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
OUT=Path('results/xmm_development_bidirectional_gate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
E5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';T5='xmmstack';E4='https://sky.esa.int/esasky-tap/tap/sync';T4='catalogues.mv_xsa_epic_stack_cat_fdw'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz';U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
SECS=(0,2,4,6,8,10);RADS=(5.,7.,10.,15.);M=.04

def cv(x):
 if np.ma.is_masked(x):return None
 if isinstance(x,(bytes,np.bytes_)):return x.decode().strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x

def tap(ep,q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-bidir/1.0'})
 with urllib.request.urlopen(req,timeout=360) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:cv(rr[n]) for n in t.colnames} for rr in t]
def stack(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-bidir/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while True:
   b=r.read(1<<20)
   if not b:break
   f.write(b)
 with fits.open(p,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names];d=max(tabs,key=lambda z:len(z.data)).data
  s=defaultdict(set);rev=defaultdict(set)
  for x in d:
   a=str(cv(x['STACK_ID']));o=str(cv(x['OBS_ID']));s[a].add(o);rev[o].add(a)
  return dict(s),dict(rev)
def maps():
 s4,r4=stack(U4,Path('/tmp/b4.gz'));s5,r5=stack(U5,Path('/tmp/b5.gz'));bad4={a for v in r4.values() if len(v)>1 for a in v};bad5={a for v in r5.values() if len(v)>1 for a in v};by5=defaultdict(list)
 for a,o in s5.items():by5[frozenset(o)].append(a)
 ps=[(a,b) for a,o in s4.items() for b in by5.get(frozenset(o),[]) if a not in bad4 and b not in bad5];m45=dict(ps);m54={b:a for a,b in ps};e4={o:next(iter(v)) for o,v in r4.items() if len(v)==1 and next(iter(v)) in m45};e5={o:next(iter(v)) for o,v in r5.items() if len(v)==1 and next(iter(v)) in m54};return m45,m54,e4,e5
def par(x,e):
 s=str(x);return e.get(s[1:11]) if len(s)==16 and s.startswith('3') and s.isdigit() else None
def clause(lo,hi,m=0):
 a=lo-m;b=hi+m
 if a<0:return f'(ra>={360+a} OR ra<{b})'
 if b>=360:return f'(ra>={a} OR ra<{b-360})'
 return f'(ra>={a} AND ra<{b})'
def nearest(src,tgt,srcemap,tgtemap,pairmap):
 gt=defaultdict(list)
 for r in tgt:
  p=par(r['srcid'],tgtemap)
  if p:gt[p].append(r)
 ss=[]
 for r in src:
  p=par(r['srcid'],srcemap);q=pairmap.get(p);old=gt.get(q,[])
  if not old:continue
  c=SkyCoord(float(r['ra'])*u.deg,float(r['dec'])*u.deg);t=SkyCoord([float(x['ra']) for x in old]*u.deg,[float(x['dec']) for x in old]*u.deg);_,sp,_=c.match_to_catalog_sky(t);ss.append(float(np.asarray(sp.arcsec).reshape(-1)[0]))
 a=np.asarray(ss);return {'n':len(a),'sep_quantiles':{str(q):float(np.quantile(a,q)) for q in (.5,.9,.95,.99)} if len(a) else {},'unmatched':{str(r):int(np.sum(a>r)) for r in RADS},'unmatched_fraction':{str(r):float(np.mean(a>r)) for r in RADS} if len(a) else {}}
def main():
 try:
  m45,m54,e4,e5=maps();all4=[];all5=[];sector={}
  for sec in SECS:
   lo=sec*30;hi=lo+30
   q4=f"SELECT TOP 200000 srcid,ra,dec,stack_flag,extent,ep_det_ml,n_obs FROM {T4} WHERE n_obs IS NOT NULL AND {clause(lo,hi)} AND stack_flag<=1 AND extent=0 AND ep_det_ml>=10"
   q5=f"SELECT TOP 200000 srcid,ra,dec,sum_flag,extent,stack_det_ml,n_obs FROM {T5} WHERE n_obs IS NOT NULL AND {clause(lo,hi,M)} AND sum_flag=0 AND extent=0 AND stack_det_ml>=10"
   r4=tap(E4,q4);r5=tap(E5,q5);k4=[r for r in r4 if par(r['srcid'],e4) in m45];k5=[r for r in r5 if par(r['srcid'],e5) in m54];all4.extend(k4);all5.extend(k5);sector[str(sec)]={'clean_dr14':len(k4),'clean_dr15':len(k5),'top_truncated':len(r4)>=200000 or len(r5)>=200000}
  a=nearest(all5,all4,e5,e4,m54);b=nearest(all4,all5,e4,e5,m45)
  out={'success':True,'status':'DEVELOPMENT_ONLY','holdout_opened':False,'exact_pairs':len(m45),'sector_counts':sector,'dr15_to_dr14':a,'dr14_to_dr15':b,'net_clean_count_difference':len(all5)-len(all4),'clean_dr15':len(all5),'clean_dr14':len(all4),'decision':'BIDIRECTIONAL_GATE_COMPLETE','note':'DR14 primary diagnostic uses STACK_FLAG<=1, EXTENT=0, EP_DET_ML>=10. DR15 uses SUM_FLAG=0, EXTENT=0, STACK_DET_ML>=10. Numeric likelihoods are not assumed to be identical statistical tests; this is a sensitivity comparison. No scientific outcome/identity fields read.'}
 except Exception as e:out={'success':False,'status':'DEVELOPMENT_ONLY','holdout_opened':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

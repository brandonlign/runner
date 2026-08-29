#!/usr/bin/env python3
"""Structural source->parent-stack validation for 4XMM-DR14s and 5XMM-DR15.

No flux, spectral, classification, variability, source name, or candidate outcome fields
are read. Parent candidates are official stacks whose full ObsID set contains every
source child ObsID and whose stack size equals the source-summary N_OBS.
"""
from pathlib import Path
from collections import defaultdict,Counter
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table
OUT=Path('results/xmm_parent_stack_subset_validation.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; T5='xmmstack'
EP4='https://sky.esa.int/esasky-tap/tap/sync'; T4='catalogues.mv_xsa_epic_stack_cat_fdw'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz'
U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
def cv(x):
 if np.ma.is_masked(x): return None
 if isinstance(x,(bytes,np.bytes_)): return x.decode('utf-8','replace').strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x
def tap(ep,q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-parent-subset/1.0'})
 with urllib.request.urlopen(req,timeout=240) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:cv(rr[n]) for n in t.colnames} for rr in t]
def stacks(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-parent-subset/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,path.open('wb') as f:
  while True:
   b=r.read(1<<20)
   if not b:break
   f.write(b)
 with fits.open(path,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names];d=max(tabs,key=lambda z:len(z.data)).data
  groups=defaultdict(set); nobs={}
  for row in d:
   sid=str(cv(row['STACK_ID'])); oid=str(cv(row['OBS_ID'])); groups[sid].add(oid); nobs[sid]=int(cv(row['N_OBSERVATIONS']))
  return {sid:obs for sid,obs in groups.items() if len(obs)==nobs[sid]}
def rows(ep,tab,obscol,limit):
 # A contiguous deterministic prefix is sufficient for structural validation and avoids per-source queries.
 return tap(ep,f'SELECT TOP {limit} srcid,{obscol},n_obs FROM {tab} ORDER BY srcid')
def validate(rs,obscol,ss,max_sources=5000):
 g=defaultdict(lambda:{'n_obs':None,'child':set()})
 for r in rs:
  sid=str(r['srcid']); no=r.get('n_obs'); oid=r.get(obscol)
  if no is not None:g[sid]['n_obs']=int(no)
  if oid not in (None,''):g[sid]['child'].add(str(oid))
 # only complete source groups safely inside row prefix: drop final srcid; require summary row and >=1 child.
 keys=sorted(g)[:-1]
 keys=[k for k in keys if g[k]['n_obs'] is not None and g[k]['child']][:max_sources]
 idx=defaultdict(set)
 for stackid,obs in ss.items():
  for o in obs:idx[(len(obs),o)].add(stackid)
 hist=Counter(); unique=[]; none=[]; amb=[]; encoded_in_child=0
 for sid in keys:
  z=g[sid]; n=z['n_obs']; child=z['child']; encoded=sid[1:11] if len(sid)==16 and sid.startswith('3') else None
  if encoded in child:encoded_in_child+=1
  cand=None
  for o in child:
   hit=idx.get((n,o),set())
   cand=set(hit) if cand is None else cand & hit
  cand=cand or set()
  cand={x for x in cand if child <= ss[x]}
  hist[len(cand)]+=1
  if len(cand)==1:unique.append((sid,next(iter(cand))))
  elif len(cand)==0:none.append(sid)
  else:amb.append((sid,sorted(cand)))
 return {'tested_sources':len(keys),'unique_parent':len(unique),'no_parent':len(none),'ambiguous_parent':len(amb),'unique_fraction':len(unique)/len(keys) if keys else 0,'candidate_count_histogram':dict(sorted(hist.items())),'encoded_min_obsid_in_child_fraction':encoded_in_child/len(keys) if keys else 0,'sample_unique':unique[:20],'sample_no_parent':none[:20],'sample_ambiguous':amb[:10]}
def main():
 try:
  s4=stacks(U4,Path('/tmp/s4.fits.gz'));s5=stacks(U5,Path('/tmp/s5.fits.gz'))
  r4=rows(EP4,T4,'obs_id',120000);r5=rows(EP5,T5,'obsid',120000)
  v4=validate(r4,'obs_id',s4);v5=validate(r5,'obsid',s5)
  out={'success':True,'dr14s':v4,'dr15':v5,'official_stack_counts':{'dr14s':len(s4),'dr15':len(s5)},'decision':'PARENT_MAPPING_VALID' if v4['unique_fraction']>=.99 and v5['unique_fraction']>=.99 and v4['ambiguous_parent']==0 and v5['ambiguous_parent']==0 else 'PARENT_MAPPING_NEEDS_WORK','note':'Structural fields only; no scientific outcome fields read.'}
 except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Validate source parent-stack mapping using the 10-digit ObsID encoded in SRCID.
Structural validation only: no flux, spectral, variability, names, or classifications.
"""
from pathlib import Path
from collections import defaultdict,Counter
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table
OUT=Path('results/xmm_embedded_obsid_parent_validation.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';T5='xmmstack'
EP4='https://sky.esa.int/esasky-tap/tap/sync';T4='catalogues.mv_xsa_epic_stack_cat_fdw'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz'
U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
def cv(x):
 if np.ma.is_masked(x):return None
 if isinstance(x,(bytes,np.bytes_)):return x.decode('utf-8','replace').strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x
def tap(ep,q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-embedded-parent/1.0'})
 with urllib.request.urlopen(req,timeout=240) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:cv(rr[n]) for n in t.colnames} for rr in t]
def stack_index(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-embedded-parent/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,path.open('wb') as f:
  while True:
   b=r.read(1<<20)
   if not b:break
   f.write(b)
 with fits.open(path,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names];d=max(tabs,key=lambda z:len(z.data)).data
  idx=defaultdict(set);stacks=defaultdict(set)
  for row in d:
   sid=str(cv(row['STACK_ID'])); oid=str(cv(row['OBS_ID'])); idx[oid].add(sid);stacks[sid].add(oid)
  return idx,stacks
def validate(ep,tab,idx,limit=50000):
 rs=tap(ep,f'SELECT TOP {limit} srcid,n_obs,n_contrib FROM {tab} WHERE n_obs IS NOT NULL ORDER BY srcid')
 hist=Counter();bad_format=[];unmapped=[];amb=[];mapped=[]
 for r in rs:
  sid=str(r['srcid'])
  if len(sid)!=16 or not sid.startswith('3') or not sid.isdigit():bad_format.append(sid);continue
  oid=sid[1:11];cand=idx.get(oid,set());hist[len(cand)]+=1
  if len(cand)==1:mapped.append((sid,oid,next(iter(cand))))
  elif not cand:unmapped.append((sid,oid))
  else:amb.append((sid,oid,sorted(cand)))
 n=len(rs);return {'tested_summary_sources':n,'valid_format':n-len(bad_format),'unique_parent':len(mapped),'unmapped':len(unmapped),'ambiguous':len(amb),'unique_fraction':len(mapped)/n if n else 0,'candidate_count_histogram':dict(sorted(hist.items())),'sample_mapped':mapped[:20],'sample_unmapped':unmapped[:20],'sample_ambiguous':amb[:10]}
def main():
 try:
  i4,s4=stack_index(U4,Path('/tmp/s4.gz'));i5,s5=stack_index(U5,Path('/tmp/s5.gz'))
  dup4={o:sorted(v) for o,v in i4.items() if len(v)!=1};dup5={o:sorted(v) for o,v in i5.items() if len(v)!=1}
  v4=validate(EP4,T4,i4);v5=validate(EP5,T5,i5)
  out={'success':True,'official_obsid_uniqueness':{'dr14s_obsids':len(i4),'dr14s_nonunique':len(dup4),'dr15_obsids':len(i5),'dr15_nonunique':len(dup5)},'dr14s':v4,'dr15':v5,'decision':'EMBEDDED_OBSID_PARENT_VALID' if not dup4 and not dup5 and v4['unique_fraction']>=.999 and v5['unique_fraction']>=.999 else 'EMBEDDED_OBSID_PARENT_NEEDS_WORK','note':'Structural identifiers only; no scientific outcomes read.'}
 except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

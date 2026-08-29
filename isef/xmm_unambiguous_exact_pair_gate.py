#!/usr/bin/env python3
"""Construct exact DR14s/DR15 stack pairs after conservatively removing any
stack that contains an ObsID assigned to more than one stack in either release.
Structural fields only; no source outcomes are inspected.
"""
from pathlib import Path
from collections import defaultdict
import json,urllib.request
import numpy as np
from astropy.io import fits
OUT=Path('results/xmm_unambiguous_exact_pair_gate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz'
def cv(x):
 if isinstance(x,(bytes,np.bytes_)):return x.decode().strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x
def load(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-unambiguous-pairs/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,path.open('wb') as f:
  while True:
   b=r.read(1<<20)
   if not b:break
   f.write(b)
 with fits.open(path,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names];d=max(tabs,key=lambda z:len(z.data)).data
  stacks=defaultdict(set);rev=defaultdict(set);meta={}
  for row in d:
   s=str(cv(row['STACK_ID']));o=str(cv(row['OBS_ID']));stacks[s].add(o);rev[o].add(s)
   m={}
   for k in ('REF_RA','REF_DEC'):
    if k in d.names:
     try:m[k.lower()]=float(cv(row[k]))
     except:pass
   if m:meta[s]=m
  return dict(stacks),dict(rev),meta
def main():
 s4,r4,m4=load(U4,Path('/tmp/4.gz'));s5,r5,m5=load(U5,Path('/tmp/5.gz'))
 d4={o:sorted(v) for o,v in r4.items() if len(v)>1};d5={o:sorted(v) for o,v in r5.items() if len(v)>1}
 bad4={s for o in d4 for s in d4[o]};bad5={s for o in d5 for s in d5[o]}
 byset5=defaultdict(list)
 for s,obs in s5.items():byset5[frozenset(obs)].append(s)
 raw=[]
 for a,obs in s4.items():
  for b in byset5.get(frozenset(obs),[]):raw.append((a,b,obs))
 clean=[(a,b,obs) for a,b,obs in raw if a not in bad4 and b not in bad5]
 pairs=[]
 for a,b,obs in clean:
  pairs.append({'dr14s_stack':a,'dr15_stack':b,'n_obsids':len(obs),'min_obsid':min(obs),'max_obsid':max(obs),'ref_ra_dr14s':m4.get(a,{}).get('ref_ra'),'ref_dec_dr14s':m4.get(a,{}).get('ref_dec'),'ref_ra_dr15':m5.get(b,{}).get('ref_ra'),'ref_dec_dr15':m5.get(b,{}).get('ref_dec')})
 out={'success':True,'dr14s':{'stacks':len(s4),'obsids':len(r4),'duplicate_obsids':d4,'affected_stacks':sorted(bad4)},'dr15':{'stacks':len(s5),'obsids':len(r5),'duplicate_obsids':d5,'affected_stacks':sorted(bad5)},'raw_exact_pairs':len(raw),'unambiguous_exact_pairs':len(clean),'removed_exact_pairs':len(raw)-len(clean),'pairs':pairs,'decision':'UNAMBIGUOUS_EXACT_COHORT_PASS' if len(clean)>=1000 else 'UNAMBIGUOUS_EXACT_COHORT_FAIL','note':'No source-level science fields read.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='pairs'}|{'pair_sample':pairs[:20]},indent=2,sort_keys=True))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Feasibility gate: exact input-observation matches between 4XMM-DR14s and 5XMM-DR15.

Uses only the official small observation/stack-list FITS files. No source catalogue
rows, source identities, or spectral outcomes are inspected. The goal is to learn
whether enough *identical ObsID sets* exist to support a clean generation-to-
generation source-detection comparison.
"""
from __future__ import annotations
from pathlib import Path
import json, urllib.request, hashlib
from collections import defaultdict, Counter
from astropy.io import fits
import numpy as np

U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
U5_CANDIDATES=[
 'https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz',
]
P4=Path('/tmp/4xmmdr14s_obslist.fits.gz');P5=Path('/tmp/5xmmdr15_stacklist.fits.gz')
OUT=Path('results/xmm_matched_stack_gate.json');OUT.parent.mkdir(parents=True,exist_ok=True)

def dl(urls,path):
 if isinstance(urls,str):urls=[urls]
 errs=[]
 for url in urls:
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-matched-stack-gate/1.1'})
   with urllib.request.urlopen(req,timeout=120) as r,path.open('wb') as f:
    while True:
     b=r.read(1024*1024)
     if not b:break
     f.write(b)
   if path.stat().st_size<1000:raise RuntimeError('download too small')
   return url
  except Exception as e:errs.append(f'{url}: {type(e).__name__}: {e}')
 raise RuntimeError('; '.join(errs))

def norm(x):
 if isinstance(x,(bytes,np.bytes_)):return x.decode('utf-8','replace').strip()
 return str(x).strip()

def inspect(path):
 out=[]
 with fits.open(path,memmap=False) as h:
  for i,z in enumerate(h):
   if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names:
    names=list(z.data.names);out.append({'hdu':i,'name':z.name,'rows':len(z.data),'columns':names})
 return out

def table(path):
 with fits.open(path,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names]
  return max(tabs,key=lambda z:len(z.data)).data.copy()

def findcol(names,needles):
 for exact in needles:
  for n in names:
   if n.upper()==exact.upper():return n
 for n in names:
  u=n.upper()
  if any(x.upper() in u for x in needles):return n
 return None

def stack_sets(d):
 names=list(d.names)
 sc=findcol(names,['STACK_ID','STACKID','STACK'])
 ob=findcol(names,['OBS_ID','OBSID'])
 if not sc or not ob:raise RuntimeError(f'cannot resolve stack/obs columns from {names}')
 g=defaultdict(set)
 for r in d:
  s=norm(r[sc]);o=norm(r[ob])
  if s and o:g[s].add(o)
 return g,{'stack_col':sc,'obs_col':ob}

def digest_obs(s):return hashlib.sha256('\n'.join(sorted(s)).encode()).hexdigest()[:20]

def main():
 try:
  u4=dl(U4,P4);u5=dl(U5_CANDIDATES,P5)
  info4=inspect(P4);info5=inspect(P5);d4=table(P4);d5=table(P5)
  g4,c4=stack_sets(d4);g5,c5=stack_sets(d5)
  byset4=defaultdict(list);byset5=defaultdict(list)
  for sid,s in g4.items():byset4[frozenset(s)].append(sid)
  for sid,s in g5.items():byset5[frozenset(s)].append(sid)
  exact_sets=set(byset4)&set(byset5)
  exact4=sum(len(byset4[s]) for s in exact_sets);exact5=sum(len(byset5[s]) for s in exact_sets)
  obs_exact=sum(len(s) for s in exact_sets)
  set4=list(byset4);obs_to_4=defaultdict(set)
  for j,s in enumerate(set4):
   for o in s:obs_to_4[o].add(j)
  contained=0;extra_hist=[]
  for s5 in byset5:
   possible=set()
   for o in s5:possible |= obs_to_4.get(o,set())
   hits=[set4[j] for j in possible if set4[j].issubset(s5)]
   if hits:
    contained+=1;best=max(hits,key=len);extra_hist.append(len(s5)-len(best))
  sizes4=Counter(map(len,g4.values()));sizes5=Counter(map(len,g5.values()))
  examples=[{'obs_set_hash':digest_obs(s),'n_obs':len(s)} for s in sorted(exact_sets,key=lambda x:(len(x),sorted(x)))[:25]]
  out={'success':True,'four_url':u4,'five_url':u5,'four_file_bytes':P4.stat().st_size,'five_file_bytes':P5.stat().st_size,
       'four_hdus':info4,'five_hdus':info5,'four_columns_resolved':c4,'five_columns_resolved':c5,
       'four_stack_count':len(g4),'five_stack_count':len(g5),'four_unique_obsids':len(set().union(*g4.values())) if g4 else 0,
       'five_unique_obsids':len(set().union(*g5.values())) if g5 else 0,
       'four_stack_size_histogram':dict(sorted(sizes4.items())),'five_stack_size_histogram':dict(sorted(sizes5.items())),
       'exact_observation_set_count':len(exact_sets),'four_stacks_on_exact_sets':exact4,'five_stacks_on_exact_sets':exact5,
       'observation_memberships_across_exact_sets':obs_exact,'five_sets_containing_a_four_set':contained,
       'extra_observation_histogram_for_containment':dict(sorted(Counter(extra_hist).items())),
       'exact_examples_anonymous':examples,
       'decision':'MATCHED_STACK_EXPERIMENT_FEASIBLE' if len(exact_sets)>=100 else 'MATCHED_STACK_EXPERIMENT_TOO_SMALL',
       'note':'Only stack/observation membership was inspected; no source catalogue rows, identities, or spectral outcomes were read.'}
  OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
 except Exception as e:
  out={'success':False,'error':f'{type(e).__name__}: {e}'};OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()

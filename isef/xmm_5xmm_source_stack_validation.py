#!/usr/bin/env python3
"""Validate how 5XMM source rows map to official stack ObsID sets.

Structural-only: queries source IDs, observation IDs, and N_OBS/N_CONTRIB for a
fixed first sample. No coordinates, source names, fluxes, spectra, classifications,
or variability values are read or emitted.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict,Counter
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table

TAP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
STACKURL='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz'
OUT=Path('results/xmm_5xmm_source_stack_validation.json');OUT.parent.mkdir(parents=True,exist_ok=True)
SF=Path('/tmp/5xmmdr15_stacklist.fits.gz')

def q(adql):
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':adql}).encode()
 req=urllib.request.Request(TAP,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-source-stack-validation/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:raw=r.read()
 txt=raw.decode('utf-8','replace')
 if 'QUERY_STATUS' in txt[:10000] and ('value="ERROR"' in txt[:10000] or '>ERROR<' in txt[:10000]):raise RuntimeError(txt[:10000])
 t=Table.read(io.BytesIO(raw),format='votable');rows=[]
 for rr in t:
  z={}
  for n in t.colnames:
   x=rr[n]
   if np.ma.is_masked(x):z[n]=None
   elif isinstance(x,bytes):z[n]=x.decode('utf-8','replace').strip()
   elif hasattr(x,'item'):
    try:z[n]=x.item()
    except:z[n]=str(x)
   else:z[n]=x
  rows.append(z)
 return rows

def dl():
 req=urllib.request.Request(STACKURL,headers={'User-Agent':'ISEF-XMM-source-stack-validation/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r,SF.open('wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b:break
   f.write(b)

def norm(x):
 if isinstance(x,(bytes,np.bytes_)):return x.decode('utf-8','replace').strip()
 return str(x).strip()

def official_sets():
 dl()
 with fits.open(SF,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names]
  d=max(tabs,key=lambda z:len(z.data)).data
  names=list(d.names);sc=next(n for n in names if n.upper()=='STACK_ID');ob=next(n for n in names if n.upper() in ('OBS_ID','OBSID'))
  g=defaultdict(set)
  for r in d:g[norm(r[sc])].add(norm(r[ob]))
 return g

def main():
 out={'success':True,'tap':TAP,'stacklist':STACKURL}
 try:
  stacks=official_sets();byset=defaultdict(list)
  for sid,s in stacks.items():byset[frozenset(s)].append(sid)
  # Select a deterministic structural sample of source summaries. n_obs is NULL on child rows.
  sums=q('SELECT TOP 500 srcid,n_obs,n_contrib FROM xmmstack WHERE n_obs IS NOT NULL ORDER BY srcid')
  srcids=[str(r['srcid']) for r in sums if r.get('srcid') is not None]
  if not srcids:raise RuntimeError('no source-summary rows returned')
  # Fetch children in chunks to avoid query-length limits.
  children=[]
  for i in range(0,len(srcids),50):
   vals=','.join("'"+s.replace("'","''")+"'" for s in srcids[i:i+50])
   children += q(f'SELECT srcid,obsid FROM xmmstack WHERE srcid IN ({vals}) AND obsid IS NOT NULL')
  gs=defaultdict(set)
  for r in children:
   if r.get('srcid') is not None and r.get('obsid') not in (None,''):gs[str(r['srcid'])].add(str(r['obsid']).strip())
  unique=0;none=0;multiple=0;nobs_agree=0;prefix_matches=0;mapped_sizes=Counter();child_counts=[]
  for r in sums:
   sid=str(r['srcid']);s=frozenset(gs.get(sid,set()));hits=byset.get(s,[]) if s else []
   child_counts.append(len(s))
   try:nobs=int(r['n_obs'])
   except:nobs=-1
   if nobs==len(s):nobs_agree+=1
   if len(hits)==1:
    unique+=1;mapped_sizes[len(s)]+=1
    stackid=str(hits[0])
    # Test only as a structural diagnostic; do not emit IDs.
    if sid.startswith(stackid):prefix_matches+=1
   elif len(hits)==0:none+=1
   else:multiple+=1
  out.update({'official_stack_count':len(stacks),'source_summary_sample':len(sums),'child_rows':len(children),
              'sources_with_unique_exact_obsset_stack':unique,'sources_with_no_exact_obsset_stack':none,
              'sources_with_multiple_stack_matches':multiple,'n_obs_equals_child_obsid_count':nobs_agree,
              'srcid_prefix_matches_mapped_stack':prefix_matches,
              'mapped_stack_size_histogram':dict(sorted(mapped_sizes.items())),
              'child_obsid_count_histogram':dict(sorted(Counter(child_counts).items())),
              'unique_mapping_fraction':unique/len(sums) if sums else 0,
              'decision':'SOURCE_STACK_MAPPING_VALID' if unique>=0.95*len(sums) else 'SOURCE_STACK_MAPPING_NEEDS_WORK',
              'note':'Only structural IDs and ObsID membership were inspected. No source names, coordinates, fluxes, spectra, classifications, or variability were read.'})
 except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

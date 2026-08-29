#!/usr/bin/env python3
"""Structural validation of stacked-catalog SRCID -> STACK_ID encoding.

Uses deterministic source-summary samples plus official stack-list IDs. No source
names, coordinates, fluxes, spectra, classifications, or variability values are
read. This tests whether the parent stack can be recovered from SRCID alone.
"""
from pathlib import Path
from collections import Counter
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table
OUT=Path('results/xmm_stackid_prefix_validation.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
EP4='https://sky.esa.int/esasky-tap/tap/sync'
TAB4='catalogues.mv_xsa_epic_stack_cat_fdw'
U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz'

def tap(ep,q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-stackid-prefix/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:raw=r.read()
 txt=raw.decode('utf-8','replace')
 if 'QUERY_STATUS' in txt[:10000] and ('value="ERROR"' in txt[:10000] or '>ERROR<' in txt[:10000]):raise RuntimeError(txt[:10000])
 t=Table.read(io.BytesIO(raw),format='votable');out=[]
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
  out.append(z)
 return out

def dl_ids(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-stackid-prefix/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r,path.open('wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b:break
   f.write(b)
 with fits.open(path,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names];d=max(tabs,key=lambda z:len(z.data)).data
  sc=next(n for n in d.names if n.upper()=='STACK_ID')
  return sorted({(x.decode('utf-8','replace') if isinstance(x,(bytes,np.bytes_)) else str(x)).strip() for x in d[sc]})

def validate(srcids,stackids):
 bylen=Counter(map(len,stackids));sets={L:set(s for s in stackids if len(s)==L) for L in bylen};lens=sorted(sets,reverse=True)
 unique=zero=multi=0;matched_len=Counter();amb=[]
 for raw in srcids:
  s=str(raw).strip();hits=[]
  for L in lens:
   p=s[:L]
   if p in sets[L]:hits.append(p)
  hits=list(dict.fromkeys(hits))
  if len(hits)==1:unique+=1;matched_len[len(hits[0])]+=1
  elif not hits:zero+=1
  else:multi+=1;amb.append(len(hits))
 return {'sample':len(srcids),'unique_prefix_match':unique,'no_prefix_match':zero,'multiple_prefix_matches':multi,'unique_fraction':unique/len(srcids) if srcids else 0,'stack_id_length_histogram':dict(sorted(bylen.items())),'matched_prefix_length_histogram':dict(sorted(matched_len.items())),'ambiguous_hit_count_histogram':dict(sorted(Counter(amb).items()))}

def main():
 try:
  ids4=dl_ids(U4,Path('/tmp/dr14s_ids.fits.gz'));ids5=dl_ids(U5,Path('/tmp/dr15_ids.fits.gz'))
  # Summary rows only. In both generations N_OBS is populated on the source-summary row.
  r5=tap(EP5,'SELECT TOP 2000 srcid,n_obs FROM xmmstack WHERE n_obs IS NOT NULL ORDER BY srcid')
  r4=tap(EP4,f'SELECT TOP 2000 srcid,n_obs FROM {TAB4} WHERE n_obs IS NOT NULL ORDER BY srcid')
  s5=[r['srcid'] for r in r5 if r.get('srcid') is not None];s4=[r['srcid'] for r in r4 if r.get('srcid') is not None]
  out={'success':True,'dr15':validate(s5,ids5),'dr14s':validate(s4,ids4),'dr15_official_stack_ids':len(ids5),'dr14s_official_stack_ids':len(ids4),
       'decision':'ENCODING_VALID' if validate(s5,ids5)['unique_fraction']>=.99 and validate(s4,ids4)['unique_fraction']>=.99 else 'ENCODING_NOT_YET_VALID',
       'note':'Structural IDs only; no source identity or science outcome fields were queried.'}
 except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

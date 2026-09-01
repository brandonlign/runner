#!/usr/bin/env python3
"""Freeze a metadata-only pseudo-period null panel for Stage-5 TESS development."""
from __future__ import annotations
import json, math, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from tess_asteroids import MovingTPF
HERE=Path(__file__).resolve().parent
OUT=HERE/'results'/'tess_binary_stage5_null_manifest'; OUT.mkdir(parents=True,exist_ok=True)
POOL_FILE=HERE/'tess_binary_stage4_validation_controls.txt'
URLS=['https://www.johnstonsarchive.net/astro/asteroidmoons.html','https://www.johnstonsarchive.net/astro/asteroidmoonsq.html','https://www.johnstonsarchive.net/astro/contactbinast.html']
ANY_NUM_RE=re.compile(r'\(([0-9]{1,7})\)')
PILOT=[
 {'number':20325,'period':0.9808,'sectors':[42,43]}, {'number':2171,'period':0.9567,'sectors':[43,44]},
 {'number':761,'period':2.3783,'sectors':[44,45,46]}, {'number':2680,'period':2.2170,'sectors':[44,45,46]},
 {'number':2486,'period':7.1920,'sectors':[71,73,91]}, {'number':2280,'period':0.89496,'sectors':[71,72,91]},
 {'number':854,'period':1.5720,'sectors':[34,70,71]}, {'number':2080,'period':1.0762,'sectors':[71,72,92]},
 {'number':7393,'period':1.6426,'sectors':[42,43,44]}, {'number':2019,'period':0.74925,'sectors':[55,71,72,91]},
 {'number':809,'period':0.6424,'sectors':[72,91]}, {'number':4528,'period':1.4592,'sectors':[30,45,46]}]
N_PER=4; UNION=sorted({s for p in PILOT for s in p['sectors']})
def mentions(url):
 r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-stage5-null-manifest/1.0'}); r.raise_for_status()
 return {int(x) for x in ANY_NUM_RE.findall(BeautifulSoup(r.text,'html.parser').get_text(' ',strip=True))}
def all_visibility(number):
 out={}
 for s in UNION:
  try:
   mt=MovingTPF.from_name(str(number),sector=s); n=int(len(mt.ephem))
   if n: out[s]={'sector':s,'ephemeris_rows':n,'camera':int(mt.camera),'ccd':int(mt.ccd)}
  except Exception: pass
 return number,out
def subset(v,sectors): return [v[s] for s in sectors if s in v]
def sig(h): return len(h),sum(x['ephemeris_rows'] for x in h)
def cost(ph,ch):
 pn,pr=sig(ph); cn,cr=sig(ch); return abs(cn-pn),abs(math.log((cr+1)/(pr+1)))
def main():
 pool=[int(x) for x in POOL_FILE.read_text().split()]
 binaryish=set().union(*(mentions(u) for u in URLS))|{p['number'] for p in PILOT}; pool=[n for n in pool if n not in binaryish]
 objects=pool+[p['number'] for p in PILOT]; vis={}
 with ThreadPoolExecutor(max_workers=16) as ex:
  futs={ex.submit(all_visibility,n):n for n in objects}
  for i,f in enumerate(as_completed(futs),1):
   n,v=f.result(); vis[n]=v
   if i%20==0: print('metadata',i,'/',len(objects),flush=True)
 used=set(); rows=[]
 for p in PILOT:
  ph=subset(vis[p['number']],p['sectors'])
  if not ph: raise RuntimeError(f"pilot positive {p['number']} has no metadata visibility")
  cand=[]
  for n in pool:
   if n in used: continue
   ch=subset(vis[n],p['sectors'])
   if ch: cand.append((cost(ph,ch),n,ch))
  cand.sort(key=lambda x:(x[0][0],x[0][1],x[1])); chosen=cand[:N_PER]
  if len(chosen)!=N_PER: raise RuntimeError(f"only {len(chosen)} controls for {p['number']}")
  for c,n,ch in chosen:
   used.add(n); rows.append({'source_positive':p['number'],'control':n,'pseudo_period_days':p['period'],'tested_sectors':[h['sector'] for h in ch],'positive_visibility':ph,'control_visibility':ch,'metadata_cost':[float(c[0]),float(c[1])]})
  print(p['number'],[(n,[h['sector'] for h in ch]) for _,n,ch in chosen],flush=True)
 if len(rows)!=48 or len({r['control'] for r in rows})!=48: raise RuntimeError('cardinality/uniqueness failure')
 report={'role':'Stage-5 development pseudo-period null panel; metadata-only selection','science_pixels_opened_during_selection':False,'control_source':'already-consumed Stage-4 control identities','binaryish_exclusions':URLS,'matching':'same pilot sector opportunities; minimize visible-sector-count difference then log ephemeris-row difference; deterministic number tie-break','controls_per_positive':N_PER,'n_controls':48,'rows':rows}
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps({'n_controls':48,'controls':[r['control'] for r in rows]},indent=2))
if __name__=='__main__': main()

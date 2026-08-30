#!/usr/bin/env python3
"""Exploratory post-failure diagnostic for spatial heterogeneity in DR14s->5XMM loss.
NOT confirmatory. Uses already-opened outcome space and emits aggregates only.
"""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
OUT=Path('results/xmm_postfailure_environment_diagnostic.json');OUT.parent.mkdir(parents=True,exist_ok=True)
E5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';T5='xmmstack';E4='https://sky.esa.int/esasky-tap/tap/sync';T4='catalogues.mv_xsa_epic_stack_cat_fdw'
U5='https://xmmssc.aip.de/files/dr15/5xmmdr15_stacklist.fits.gz';U4='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
SECS=(0,1,10,11);MARGIN=.04

def cv(x):
 if np.ma.is_masked(x):return None
 if isinstance(x,(bytes,np.bytes_)):return x.decode().strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x
def tap(ep,q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-postfail/1.0'})
 with urllib.request.urlopen(req,timeout=420) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:cv(rr[n]) for n in t.colnames} for rr in t]
def stacks(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-postfail/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:p.write_bytes(r.read())
 with fits.open(p,memmap=False) as h:
  tabs=[z for z in h if getattr(z,'data',None) is not None and hasattr(z.data,'names') and z.data.names];d=max(tabs,key=lambda z:len(z.data)).data;s=defaultdict(set);rev=defaultdict(set)
  for x in d:a=str(cv(x['STACK_ID']));o=str(cv(x['OBS_ID']));s[a].add(o);rev[o].add(a)
 return dict(s),dict(rev)
def maps():
 s4,r4=stacks(U4,Path('/tmp/d4.gz'));s5,r5=stacks(U5,Path('/tmp/d5.gz'));bad4={a for v in r4.values() if len(v)>1 for a in v};bad5={a for v in r5.values() if len(v)>1 for a in v};by5=defaultdict(list)
 for a,o in s5.items():by5[frozenset(o)].append(a)
 ps=[(a,b) for a,o in s4.items() for b in by5.get(frozenset(o),[]) if a not in bad4 and b not in bad5];m45=dict(ps);m54={b:a for a,b in ps};e4={o:next(iter(v)) for o,v in r4.items() if len(v)==1 and next(iter(v)) in m45};e5={o:next(iter(v)) for o,v in r5.items() if len(v)==1 and next(iter(v)) in m54};return m45,m54,e4,e5
def par(x,e):
 s=str(x);return e.get(s[1:11]) if len(s)==16 and s.startswith('3') and s.isdigit() else None
def clause(lo,hi,m=0):
 a=lo-m;b=hi+m
 if a<0:return f'(ra>={360+a:.8f} OR ra<{b:.8f})'
 if b>=360:return f'(ra>={a:.8f} OR ra<{b-360:.8f})'
 return f'(ra>={a:.8f} AND ra<{b:.8f})'
def loss(r,new,m45):
 pool=new.get(m45[r['parent']],[])
 if not pool:return 1
 c=SkyCoord(r['ra']*u.deg,r['dec']*u.deg);t=SkyCoord([x[0] for x in pool]*u.deg,[x[1] for x in pool]*u.deg);_,sp,_=c.match_to_catalog_sky(t);return int(float(np.asarray(sp.arcsec).reshape(-1)[0])>5)
def agg(rows):
 if not rows:return {'n':0}
 n=len(rows);lost=sum(r['lost'] for r in rows);strong=[r for r in rows if r['strong']];weak=[r for r in rows if not r['strong']]
 def lf(z):return sum(r['lost'] for r in z)/len(z) if z else None
 return {'n':n,'lost':lost,'loss_fraction':lost/n,'strong_n':len(strong),'strong_loss_fraction':lf(strong),'weak_n':len(weak),'weak_loss_fraction':lf(weak),'median_abs_gal_b_deg':float(np.median([r['ab'] for r in rows])),'median_nn_arcsec':float(np.median([r['nn'] for r in rows if np.isfinite(r['nn'])])) if any(np.isfinite(r['nn']) for r in rows) else None,'median_parent_sources':float(np.median([r['psz'] for r in rows]))}
def main():
 try:
  m45,m54,e4,e5=maps();old=[];new=defaultdict(list);counts={}
  for sec in SECS:
   lo=sec*30;hi=lo+30;q4=f"SELECT TOP 200000 srcid,ra,dec,ep_det_ml,n_contrib,fratio,stack_flag,extent FROM {T4} WHERE n_obs IS NOT NULL AND {clause(lo,hi)} AND stack_flag<=1 AND extent=0 AND ep_det_ml>=10 AND n_contrib>=2 AND fratio IS NOT NULL";q5=f"SELECT TOP 200000 srcid,ra,dec,n_obs FROM {T5} WHERE n_obs IS NOT NULL AND {clause(lo,hi,MARGIN)}"
   a=tap(E4,q4);b=tap(E5,q5);ka=[]
   for r in a:
    p=par(r['srcid'],e4)
    try:fr=float(r['fratio'])
    except:continue
    if p not in m45 or not np.isfinite(fr) or fr<=0:continue
    ka.append({'parent':p,'ra':float(r['ra']),'dec':float(r['dec']),'strong':fr>=5,'sector':sec})
   for r in b:
    p=par(r['srcid'],e5)
    if p in m54:new[p].append((float(r['ra']),float(r['dec'])))
   old.extend(ka);counts[str(sec)]={'old':len(ka),'new_raw':len(b),'truncated':len(a)>=200000 or len(b)>=200000}
  byp=defaultdict(list)
  for i,r in enumerate(old):byp[r['parent']].append(i)
  for p,ii in byp.items():
   co=SkyCoord([old[i]['ra'] for i in ii]*u.deg,[old[i]['dec'] for i in ii]*u.deg);psz=len(ii)
   if psz>1:_,sep,_=co.match_to_catalog_sky(co,nthneighbor=2);nn=np.asarray(sep.arcsec)
   else:nn=np.array([np.inf])
   for j,i in enumerate(ii):old[i]['nn']=float(nn[j]);old[i]['psz']=psz
  co=SkyCoord([r['ra'] for r in old]*u.deg,[r['dec'] for r in old]*u.deg,frame='icrs');ab=np.abs(np.asarray(co.galactic.b.deg))
  for i,r in enumerate(old):r['ab']=float(ab[i]);r['lost']=loss(r,new,m45)
  bcuts=[(0,5),(5,15),(15,30),(30,90.1)];ncuts=[(0,10),(10,30),(30,60),(60,1e99)]
  out={'success':True,'status':'POSTFAILURE_EXPLORATORY_ONLY','confirmatory_reuse_forbidden':True,'exact_pairs':len(m45),'query_counts':counts,'sector':{str(s):agg([r for r in old if r['sector']==s]) for s in SECS},'abs_gal_b_bins':{f'{a}-{b}':agg([r for r in old if a<=r['ab']<b]) for a,b in bcuts},'nearest_neighbor_bins_arcsec':{f'{a}-{b}':agg([r for r in old if a<=r['nn']<b]) for a,b in ncuts},'sector_by_abs_gal_b':{str(s):{f'{a}-{b}':agg([r for r in old if r['sector']==s and a<=r['ab']<b]) for a,b in bcuts} for s in SECS},'note':'Exploratory diagnosis after frozen holdout failure. Aggregates only; cannot rescue or validate the failed mechanism.'}
 except Exception as e:out={'success':False,'status':'POSTFAILURE_EXPLORATORY_ONLY','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

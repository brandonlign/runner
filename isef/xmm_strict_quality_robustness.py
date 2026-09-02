#!/usr/bin/env python3
"""Frozen strict-quality robustness for the 5XMM reprocessing-recovery result.
Aggregate outputs only; no identities or coordinates emitted."""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request,hashlib
import numpy as np
from scipy.stats import mannwhitneyu
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4OBS=Path('/tmp/4xmmdr14_obslist.fits'); OUT=Path('results/xmm_strict_quality_robustness.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
ORIG={'development':571,'validation':638}
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def fnum(x):
 try:
  v=float(x); return v if np.isfinite(v) else np.nan
 except: return np.nan
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-strict-quality/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-strict-quality/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
def refs():
 if not P4.exists(): dl(U4,P4)
 if not P4OBS.exists(): dl(U4OBS,P4OBS)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float).copy(); de=np.asarray(d[nm['SC_DEC']],float).copy()
 with fits.open(P4OBS,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
 ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def qbin(lo,hi,cut,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,s.ep_flux AS flux,s.ep_det_ml AS detml,d.obsid AS dobsid,d.pps_srcnum AS pps
FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid
WHERE {cut} AND s.extent=0 AND s.ep_det_ml>=15 AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL'''
 t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'row cap {cut} {lo}-{hi}')
  mid=(lo+hi)/2; return qbin(lo,mid,cut,depth+1)+qbin(mid,hi,cut,depth+1)
 return [t]
def one(c4,old,hemi,cut):
 a,b=(0,180) if hemi=='development' else (180,360); eligible_total=0; recoveries=0; cases_all={}; controls_all={}; used=set(); excluded=0
 for lo in range(a,b,5):
  tabs=qbin(float(lo),float(lo+5),cut); t=vstack(tabs,metadata_conflicts='silent') if len(tabs)>1 else tabs[0]
  props={}; obs=defaultdict(set)
  for row in t:
   sid=norm(row['sid'])
   if sid not in props: props[sid]={'ra':fnum(row['sra']),'dec':fnum(row['sdec']),'flux':fnum(row['flux']),'detml':fnum(row['detml'])}
   o=norm(row['dobsid']);
   if o and o not in ('--','None','nan'): obs[sid].add(o)
  ids=list(props); eligible_total+=len(ids)
  if not ids: continue
  c=SkyCoord([props[s]['ra'] for s in ids]*u.deg,[props[s]['dec'] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4)
  caseids=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and any(o in old for o in obs[ids[i]])]; recoveries+=len(caseids)
  ctrlids=[ids[i] for i in range(len(ids)) if sep.arcsec[i]<=20 and any(o in old for o in obs[ids[i]])]
  om=defaultdict(list)
  for s in ctrlids:
   for o in obs[s]&old: om[o].append(s)
  for s in sorted(caseids,key=lambda x:hashlib.sha256(x.encode()).hexdigest()):
   cand=set()
   for o in obs[s]&old: cand.update(om.get(o,[]))
   avail=[x for x in cand if x not in used]; avail.sort(key=lambda x:hashlib.sha256((s+'|'+x).encode()).hexdigest()); chosen=avail[:3]
   if not chosen: excluded+=1; continue
   cases_all[s]=props[s]
   for x in chosen: controls_all[x]=props[x]; used.add(x)
 tests={}
 if recoveries>=200:
  for name,field in [('brightness','flux'),('detection_strength','detml')]:
   ca=np.array([p[field] for p in cases_all.values()],float); co=np.array([p[field] for p in controls_all.values()],float); ca=ca[np.isfinite(ca)&(ca>0)]; co=co[np.isfinite(co)&(co>0)]; ca=np.log10(ca); co=np.log10(co)
   p=float(mannwhitneyu(ca,co,alternative='two-sided').pvalue) if len(ca) and len(co) else None
   tests[name]={'case_n':len(ca),'control_n':len(co),'case_median_log10':float(np.median(ca)) if len(ca) else None,'control_median_log10':float(np.median(co)) if len(co) else None,'median_difference':float(np.median(ca)-np.median(co)) if len(ca) and len(co) else None,'raw_p':p}
 return {'eligible':eligible_total,'recoveries':recoveries,'prevalence':recoveries/eligible_total if eligible_total else None,'retained_fraction_of_original':recoveries/ORIG[hemi],'matched_cases':len(cases_all),'unique_controls':len(controls_all),'excluded_no_control':excluded,'tests':tests}
def main():
 try:
  c4,old=refs(); cuts={'strict':'s.sum_flag < 2','very_strict':'s.sum_flag = 0'}; out={'success':True,'results':{}}
  for cname,cut in cuts.items():
   out['results'][cname]={}
   for hemi in ('development','validation'):
    r=one(c4,old,hemi,cut); out['results'][cname][hemi]=r; print(json.dumps({'cut':cname,'hemisphere':hemi,'recoveries':r['recoveries'],'prevalence':r['prevalence']}),flush=True)
  s=out['results']['strict']; ps=[]; dirs=[]
  enough=all(s[h]['recoveries']>=200 for h in ('development','validation'))
  if enough:
   for h in ('development','validation'):
    for k in ('brightness','detection_strength'):
     ps.append(s[h]['tests'][k]['raw_p']); dirs.append(s[h]['tests'][k]['median_difference']<0)
  out['strict_quality_robust']=bool(enough and all(dirs) and all(p*4<=0.01 for p in ps)); out['bonferroni_four_tests']=[min(1.0,p*4) for p in ps]; out['privacy']='Aggregate statistics only; no identities or coordinates emitted.'
 except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request,hashlib
import numpy as np
from scipy.stats import mannwhitneyu
from astropy.table import Table
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4OBS=Path('/tmp/4xmmdr14_obslist.fits'); OUT=Path('results/xmm_reprocessing_dev_properties.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 3 AND s.extent = 0 AND s.ep_det_ml >= 15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def fnum(x):
 try:
  v=float(x); return v if np.isfinite(v) else np.nan
 except: return np.nan
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-dev-properties/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-dev-properties/1.0'})
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
def qbin(lo,hi):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,s.ep_flux AS flux,s.ep_hr2 AS hr2,s.ep_hr3 AS hr3,s.ep_det_ml AS detml,s.n_contrib AS ncontrib,s.n_obs AS nobs,s.approx_source_var AS svar,d.obsid AS dobsid FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid WHERE {BASE} AND s.ra >= {lo} AND s.ra < {hi}'''
 t=tap(q)
 if len(t)>=CAP: raise RuntimeError(f'cap hit {lo}-{hi}; frozen 5deg property query requires subdivision implementation before interpretation')
 return t
def summarize(v):
 a=np.asarray(v,float); a=a[np.isfinite(a)]
 if not len(a): return {'n':0,'median':None,'q25':None,'q75':None}
 return {'n':int(len(a)),'median':float(np.median(a)),'q25':float(np.quantile(a,.25)),'q75':float(np.quantile(a,.75))}
def holm(raw):
 items=sorted(raw.items(),key=lambda z:z[1]); out={}; prev=0.0; m=len(items)
 for i,(k,p) in enumerate(items):
  a=min(1.0,(m-i)*p); a=max(a,prev); out[k]=a; prev=a
 return out
def main():
 try:
  c4,old=refs(); all_case={}; all_ctrl={}; pairs=[]; excluded=0
  for lo in range(0,180,5):
   t=qbin(lo,lo+5); props={}; obs=defaultdict(set)
   for row in t:
    sid=norm(row['sid']);
    if sid not in props: props[sid]={'ra':fnum(row['sra']),'dec':fnum(row['sdec']),'flux':fnum(row['flux']),'hr2':fnum(row['hr2']),'hr3':fnum(row['hr3']),'detml':fnum(row['detml']),'ncontrib':fnum(row['ncontrib']),'nobs':fnum(row['nobs']),'svar':fnum(row['svar'])}
    o=norm(row['dobsid']);
    if o and o not in ('--','None','nan'): obs[sid].add(o)
   ids=list(props); c=SkyCoord([props[s]['ra'] for s in ids]*u.deg,[props[s]['dec'] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4)
   cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and any(o in old for o in obs[ids[i]])]
   ctrls=[ids[i] for i in range(len(ids)) if sep.arcsec[i]<=20 and any(o in old for o in obs[ids[i]])]
   om=defaultdict(list)
   for s in ctrls:
    for o in obs[s]&old: om[o].append(s)
   used=set()
   for s in sorted(cases,key=lambda x:hashlib.sha256(x.encode()).hexdigest()):
    cand=set()
    for o in obs[s]&old: cand.update(om.get(o,[]))
    avail=[x for x in cand if x not in used]
    avail.sort(key=lambda x:hashlib.sha256((s+'|'+x).encode()).hexdigest())
    chosen=avail[:3]
    if not chosen: excluded+=1; continue
    all_case[s]=props[s]
    for x in chosen: all_ctrl[x]=props[x]; used.add(x)
    pairs.append(len(chosen))
   print(json.dumps({'bin':f'{lo}-{lo+5}','cases':len(cases),'controls_pool':len(ctrls),'matched_cases_cumulative':len(all_case)}),flush=True)
  variables={'brightness':('flux',True),'hr2':('hr2',False),'hr3':('hr3',False),'detection_strength':('detml',True),'ncontrib':('ncontrib',False),'variability':('svar',True)}; tests={}
  for name,(field,logit) in variables.items():
   a=np.array([p[field] for p in all_case.values()],float); b=np.array([p[field] for p in all_ctrl.values()],float)
   if logit: a=np.where(a>0,np.log10(a),np.nan); b=np.where(b>0,np.log10(b),np.nan)
   a=a[np.isfinite(a)]; b=b[np.isfinite(b)]
   p=float(mannwhitneyu(a,b,alternative='two-sided').pvalue) if len(a) and len(b) else None
   tests[name]={'case':summarize(a),'control':summarize(b),'raw_p':p,'median_difference_case_minus_control':float(np.median(a)-np.median(b)) if len(a) and len(b) else None}
  fam={'brightness':tests['brightness']['raw_p'],'spectral_shape':min(1.0,2*min(tests['hr2']['raw_p'],tests['hr3']['raw_p'])) if tests['hr2']['raw_p'] is not None and tests['hr3']['raw_p'] is not None else 1.0,'detection_strength':tests['detection_strength']['raw_p'],'ncontrib':tests['ncontrib']['raw_p'],'variability':tests['variability']['raw_p']}
  adj=holm({k:(1.0 if v is None else v) for k,v in fam.items()})
  reality=sum(1 for p in all_case.values() if np.isfinite(p['ncontrib']) and p['ncontrib']>=2)/len(all_case) if all_case else None
  out={'success':True,'hemisphere':'development','matched_cases':len(all_case),'unique_controls':len(all_ctrl),'cases_excluded_no_exact_obsid_control':excluded,'controls_per_matched_case_mean':float(np.mean(pairs)) if pairs else None,'tests':tests,'family_raw_p':fam,'holm_adjusted_p':adj,'repeat_xmm_fraction_ncontrib_ge_2':reality,'privacy':'Aggregate statistics only; no identities or coordinates emitted.'}
 except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

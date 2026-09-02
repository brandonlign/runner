#!/usr/bin/env python3
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
P4=Path('/tmp/4x.fits.gz'); PO=Path('/tmp/4obs.fits'); OUT=Path('results/xmm_strict_quality_robustness.json'); OUT.parent.mkdir(parents=True,exist_ok=True); ORIG={'development':571,'validation':638}
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def fnum(x):
 try:
  v=float(x); return v if np.isfinite(v) else np.nan
 except: return np.nan
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-strict-quality/2.1'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-strict-quality/2.1'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
def refs():
 if not P4.exists(): dl(U4,P4)
 if not PO.exists(): dl(U4OBS,PO)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float).copy(); de=np.asarray(d[nm['SC_DEC']],float).copy()
 with fits.open(PO,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
 ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def qbin(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,s.sum_flag AS sf,s.ep_flux AS flux,s.ep_det_ml AS detml,d.obsid AS dobsid,d.pps_srcnum AS pps FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid WHERE s.sum_flag<2 AND s.extent=0 AND s.ep_det_ml>=15 AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'cap {lo}-{hi}')
  m=(lo+hi)/2; return qbin(lo,m,depth+1)+qbin(m,hi,depth+1)
 return [t]
def analyze(c4,old,t,hemi,flag0):
 props={}; obs=defaultdict(set)
 for row in t:
  if flag0 and int(row['sf'])!=0: continue
  sid=norm(row['sid'])
  if sid not in props: props[sid]={'ra':fnum(row['sra']),'dec':fnum(row['sdec']),'flux':fnum(row['flux']),'detml':fnum(row['detml'])}
  o=norm(row['dobsid']);
  if o and o not in ('--','None','nan'): obs[sid].add(o)
 ids=list(props); c=SkyCoord([props[s]['ra'] for s in ids]*u.deg,[props[s]['dec'] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4)
 cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and any(o in old for o in obs[ids[i]])]; pool=[ids[i] for i in range(len(ids)) if sep.arcsec[i]<=20 and any(o in old for o in obs[ids[i]])]
 om=defaultdict(list)
 for s in pool:
  for o in obs[s]&old: om[o].append(s)
 used=set(); mc={}; cc={}; ex=0
 for s in sorted(cases,key=lambda x:hashlib.sha256(x.encode()).hexdigest()):
  cand=set()
  for o in obs[s]&old: cand.update(om.get(o,[]))
  av=[x for x in cand if x not in used]; av.sort(key=lambda x:hashlib.sha256((s+'|'+x).encode()).hexdigest()); ch=av[:3]
  if not ch: ex+=1; continue
  mc[s]=props[s]
  for x in ch: cc[x]=props[x]; used.add(x)
 tests={}
 if len(cases)>=200:
  for name,f in [('brightness','flux'),('detection_strength','detml')]:
   a=np.array([p[f] for p in mc.values()]); b=np.array([p[f] for p in cc.values()]); a=np.log10(a[np.isfinite(a)&(a>0)]); b=np.log10(b[np.isfinite(b)&(b>0)]); pv=float(mannwhitneyu(a,b,alternative='two-sided').pvalue)
   tests[name]={'case_n':len(a),'control_n':len(b),'case_median_log10':float(np.median(a)),'control_median_log10':float(np.median(b)),'median_difference':float(np.median(a)-np.median(b)),'raw_p':pv}
 n=len(ids); r=len(cases)
 return {'eligible':n,'recoveries':r,'prevalence':r/n if n else None,'retained_fraction_of_original':r/ORIG[hemi],'matched_cases':len(mc),'unique_controls':len(cc),'excluded_no_control':ex,'tests':tests}
def main():
 try:
  c4,old=refs(); raw={'development':[],'validation':[]}
  for lo in range(0,360,10):
   raw['development' if lo<180 else 'validation'] += qbin(float(lo),float(lo+10)); print(json.dumps({'progress':f'{lo}-{lo+10}'}),flush=True)
  out={'success':True,'results':{'strict':{},'very_strict':{}}}
  for h in ('development','validation'):
   t=vstack(raw[h],metadata_conflicts='silent'); out['results']['strict'][h]=analyze(c4,old,t,h,False); out['results']['very_strict'][h]=analyze(c4,old,t,h,True)
  s=out['results']['strict']; enough=all(s[h]['recoveries']>=200 for h in ('development','validation')); ps=[]; dirs=[]
  if enough:
   for h in ('development','validation'):
    for k in ('brightness','detection_strength'): ps.append(s[h]['tests'][k]['raw_p']); dirs.append(s[h]['tests'][k]['median_difference']<0)
  out['bonferroni_four_tests']=[min(1.0,p*4) for p in ps]; out['strict_quality_robust']=bool(enough and all(dirs) and all(p*4<=0.01 for p in ps)); out['privacy']='Aggregate statistics only; no identities or coordinates emitted.'
 except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

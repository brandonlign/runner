#!/usr/bin/env python3
"""Frozen aggregate nearest-4XMM separation robustness test."""
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
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'; P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4O=Path('/tmp/4xmmdr14_obslist.fits'); OUT=Path('results/xmm_separation_robustness.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent = 0 AND s.ep_det_ml >= 15'; BASE_COUNTS={'development':528,'validation':587}; THR=(30.,60.)
def norm(x):
 if isinstance(x,(bytes,np.bytes_)):x=x.decode('utf-8','replace')
 return str(x).strip()
def num(x):
 try:
  v=float(x); return v if np.isfinite(v) else np.nan
 except:return np.nan
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-separation-robustness/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-separation-robustness/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b:break
   f.write(b)
def refs():
 if not P4.exists():dl(U4,P4)
 if not P4O.exists():dl(U4OBS,P4O)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float); de=np.asarray(d[nm['SC_DEC']],float)
 with fits.open(P4O,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
 ok=np.isfinite(ra)&np.isfinite(de);return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def qb(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,s.ep_flux flux,s.ep_det_ml detml,d.obsid obsid FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL''';t=tap(q)
 if len(t)>=CAP:
  if depth>=8:raise RuntimeError(f'cap {lo}-{hi}')
  m=(lo+hi)/2;return qb(lo,m,depth+1)+qb(m,hi,depth+1)
 return [t]
def load(lo,hi):
 props={};obs=defaultdict(set)
 for b in range(int(lo),int(hi),5):
  ts=qb(float(b),float(min(b+5,hi)));t=vstack(ts,metadata_conflicts='silent') if len(ts)>1 else ts[0]
  for row in t:
   s=norm(row['sid']);props.setdefault(s,{'ra':num(row['sra']),'dec':num(row['sdec']),'flux':num(row['flux']),'detml':num(row['detml'])});o=norm(row['obsid'])
   if o and o not in ('--','None','nan'):obs[s].add(o)
 return props,obs
def matched(props,obs,seps,ids,old,threshold):
 cases=[ids[i] for i in range(len(ids)) if seps[i]>threshold and any(o in old for o in obs[ids[i]])]; ctrls=[ids[i] for i in range(len(ids)) if seps[i]<=20 and any(o in old for o in obs[ids[i]])]; om=defaultdict(list)
 for x in ctrls:
  for o in obs[x]&old:om[o].append(x)
 used=set();ca=[];co=[]
 for s in sorted(cases,key=lambda x:hashlib.sha256(x.encode()).hexdigest()):
  cand=set()
  for o in obs[s]&old:cand.update(om.get(o,[]))
  a=[x for x in cand if x not in used];a.sort(key=lambda x:hashlib.sha256((s+'|'+x).encode()).hexdigest());ch=a[:3]
  if not ch:continue
  ca.append(s);co.extend(ch);used.update(ch)
 def tst(field):
  a=np.array([props[x][field] for x in ca],float);b=np.array([props[x][field] for x in co],float);a=a[np.isfinite(a)&(a>0)];b=b[np.isfinite(b)&(b>0)];a=np.log10(a);b=np.log10(b);p=float(mannwhitneyu(a,b,alternative='two-sided').pvalue);return {'median_diff':float(np.median(a)-np.median(b)),'raw_p':p,'n_case':len(a),'n_control':len(b)}
 return {'recoveries':len(cases),'matched_cases':len(ca),'unique_controls':len(co),'flux':tst('flux'),'detml':tst('detml')}
def main():
 try:
  c4,old=refs();out={'success':True,'thresholds_arcsec':list(THR),'hemispheres':{}};raw=[]
  for name,lo,hi in [('development',0,180),('validation',180,360)]:
   props,obs=load(lo,hi);ids=list(props);c=SkyCoord([props[s]['ra'] for s in ids]*u.deg,[props[s]['dec'] for s in ids]*u.deg);_,sep,_=c.match_to_catalog_sky(c4);seps=sep.arcsec;hr={}
   for th in THR:
    z=matched(props,obs,seps,ids,old,th);z['retained_fraction_vs_20arcsec_strict']=z['recoveries']/BASE_COUNTS[name];hr[str(int(th))]=z;raw += [z['flux']['raw_p'],z['detml']['raw_p']]
   out['hemispheres'][name]=hr
  corr=[min(1.,p*8) for p in raw];j=0;criteria=[]
  for name in ('development','validation'):
   for th in THR:
    z=out['hemispheres'][name][str(int(th))];z['flux']['bonferroni_p']=corr[j];j+=1;z['detml']['bonferroni_p']=corr[j];j+=1;need=.70 if th==30 else .40;criteria.append(z['retained_fraction_vs_20arcsec_strict']>=need and z['flux']['median_diff']<0 and z['detml']['median_diff']<0 and z['flux']['bonferroni_p']<=.01 and z['detml']['bonferroni_p']<=.01)
  out['science_status']='PASS' if all(criteria) else 'FAIL';out['privacy']='Aggregate results only.'
 except Exception as e:out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()

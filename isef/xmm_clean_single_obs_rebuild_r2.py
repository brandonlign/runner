#!/usr/bin/env python3
"""Frozen Stage R2 for the clean single-observation 5XMM rebuild.
Do not execute unless Stage R1 passed in both hemispheres. Aggregate output only."""
from pathlib import Path
from collections import defaultdict
import gzip,shutil,io,json,urllib.parse,urllib.request,hashlib
import numpy as np
from scipy.stats import mannwhitneyu
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4O='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'; U4S='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s.fits.gz'
P4=Path('/tmp/4main.fits.gz'); P4O=Path('/tmp/4main_obs.fits'); P4SG=Path('/tmp/4stack.fits.gz'); P4S=Path('/tmp/4stack.fits'); OUT=Path('results/xmm_clean_single_obs_rebuild_r2.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent=0 AND s.ep_det_ml>=15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def num(x):
 try:
  v=float(x); return v if np.isfinite(v) else np.nan
 except:return np.nan
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-clean-R2/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:return Table.read(io.BytesIO(r.read()),format='votable')
def dl(url,p,timeout=1200):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-clean-R2/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r,p.open('wb') as f:
  while True:
   b=r.read(16*1024*1024)
   if not b:break
   f.write(b)
def coords(path):
 with fits.open(path,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}
  for a,b in [('SC_RA','SC_DEC'),('RA','DEC'),('SRC_RA','SRC_DEC'),('SOURCE_RA','SOURCE_DEC')]:
   if a in nm and b in nm:
    ra=np.asarray(d[nm[a]],float).copy(); de=np.asarray(d[nm[b]],float).copy(); ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg)
 raise RuntimeError('no coordinate columns')
def obsids(path):
 with fits.open(path,memmap=False) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; c=nm.get('OBS_ID') or nm.get('OBSID'); return {norm(x) for x in d[c] if norm(x)}
def refs():
 if not P4.exists():dl(U4,P4,300)
 if not P4O.exists():dl(U4O,P4O,300)
 if not P4SG.exists():dl(U4S,P4SG,1200)
 if not P4S.exists():
  with gzip.open(P4SG,'rb') as src,P4S.open('wb') as dst:shutil.copyfileobj(src,dst,length=32*1024*1024)
 return coords(P4),coords(P4S),obsids(P4O)
def qb(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,s.ep_flux flux,s.ep_det_ml detml,s.stack_det_ml stackml,s.n_contrib nc,d.obsid obsid FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8:raise RuntimeError(f'cap {lo}-{hi}')
  m=(lo+hi)/2;return qb(lo,m,depth+1)+qb(m,hi,depth+1)
 return [t]
def hemi(lo,hi,cmain,cstack,old):
 p={}; obs=defaultdict(set)
 for b in range(lo,hi,5):
  ts=qb(float(b),float(b+5));t=vstack(ts,metadata_conflicts='silent') if len(ts)>1 else ts[0]
  for r in t:
   s=norm(r['sid']);p.setdefault(s,{'ra':num(r['sra']),'dec':num(r['sdec']),'flux':num(r['flux']),'detml':num(r['detml']),'stackml':num(r['stackml']),'nc':num(r['nc'])});o=norm(r['obsid'])
   if o in old:obs[s].add(o)
 ids=[s for s in p if obs[s]]; c=SkyCoord([p[s]['ra'] for s in ids]*u.deg,[p[s]['dec'] for s in ids]*u.deg);_,sm,_=c.match_to_catalog_sky(cmain)
 mainclean=[ids[i] for i in range(len(ids)) if sm.arcsec[i]>20]; cc=SkyCoord([p[s]['ra'] for s in mainclean]*u.deg,[p[s]['dec'] for s in mainclean]*u.deg);_,ss,_=cc.match_to_catalog_sky(cstack)
 cases=[mainclean[i] for i in range(len(mainclean)) if ss.arcsec[i]>20 and p[mainclean[i]]['nc']==1]
 # Controls are retained 4XMM sources, N_CONTRIB=1, sharing an exact old ObsID. No outcome enters selection.
 ctrl=[ids[i] for i in range(len(ids)) if sm.arcsec[i]<=20 and p[ids[i]]['nc']==1]; om=defaultdict(list)
 for x in ctrl:
  for o in obs[x]&old:om[o].append(x)
 used=set(); ca=[]; co=[]
 for s in sorted(cases,key=lambda x:hashlib.sha256(x.encode()).hexdigest()):
  cand=set()
  for o in obs[s]&old:cand.update(om.get(o,[]))
  avail=[x for x in cand if x not in used];avail.sort(key=lambda x:hashlib.sha256((s+'|'+x).encode()).hexdigest());ch=avail[:3]
  if not ch:continue
  ca.append(s);co.extend(ch);used.update(ch)
 def test(k):
  a=np.array([p[s][k] for s in ca],float);b=np.array([p[s][k] for s in co],float);a=a[np.isfinite(a)&(a>0)];b=b[np.isfinite(b)&(b>0)];a=np.log10(a);b=np.log10(b);return {'median_case':float(np.median(a)),'median_control':float(np.median(b)),'median_diff':float(np.median(a)-np.median(b)),'raw_p':float(mannwhitneyu(a,b,alternative='two-sided').pvalue),'n_case':int(len(a)),'n_control':int(len(b))}
 high=sum(np.isfinite(p[s]['stackml']) and p[s]['stackml']>=20 for s in cases)
 return {'clean_single_recoveries':len(cases),'matched_cases':len(ca),'unique_controls':len(co),'stack_det_ml_ge20':high,'stack_det_ml_ge20_fraction':high/len(cases) if cases else None,'flux':test('flux'),'detml':test('detml')}
def main():
 try:
  cm,cs,old=refs();d=hemi(0,180,cm,cs,old);v=hemi(180,360,cm,cs,old);tests=[d['flux'],d['detml'],v['flux'],v['detml']]
  for z in tests:z['bonferroni_p']=min(1.0,z['raw_p']*4.0)
  def gate(z):return z['flux']['median_diff']<0 and z['detml']['median_diff']<0 and z['flux']['bonferroni_p']<=.01 and z['detml']['bonferroni_p']<=.01
  out={'success':True,'science_status':'PASS' if gate(d) and gate(v) else 'FAIL','development':d,'validation':v,'frozen_rule':'Both median differences negative in each hemisphere; all four Bonferroni p <= 0.01','privacy':'Aggregate only; no source identities or coordinates emitted.'}
 except Exception as e:out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()

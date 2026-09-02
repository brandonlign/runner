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
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz';U4O='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits';P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz');P4O=Path('/tmp/4xmmdr14_obslist.fits');OUT=Path('results/xmm_single_contrib_mechanism.json');OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent=0 AND s.ep_det_ml>=15'
def n(x):
 if isinstance(x,(bytes,np.bytes_)):x=x.decode('utf-8','replace')
 return str(x).strip()
def f(x):
 try:
  v=float(x);return v if np.isfinite(v) else np.nan
 except:return np.nan
def tap(q):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q});req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-single-contrib/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r:return Table.read(io.BytesIO(r.read()),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-single-contrib/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as g:
  while 1:
   b=r.read(8388608)
   if not b:break
   g.write(b)
def refs():
 if not P4.exists():dl(U4,P4)
 if not P4O.exists():dl(U4O,P4O)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};ra=np.asarray(d[nm['SC_RA']],float);de=np.asarray(d[nm['SC_DEC']],float)
 with fits.open(P4O,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};old={n(x) for x in d[nm['OBS_ID']] if n(x)}
 ok=np.isfinite(ra)&np.isfinite(de);return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def qb(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,s.ep_flux flux,s.ep_det_ml detml,s.n_contrib nc,d.obsid obsid FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL''';t=tap(q)
 if len(t)>=CAP:
  if depth>=8:raise RuntimeError('cap')
  m=(lo+hi)/2;return qb(lo,m,depth+1)+qb(m,hi,depth+1)
 return [t]
def hemi(lo,hi,c4,old):
 p={};obs=defaultdict(set)
 for b in range(lo,hi,5):
  ts=qb(b,b+5);t=vstack(ts,metadata_conflicts='silent') if len(ts)>1 else ts[0]
  for r in t:
   s=n(r['sid']);p.setdefault(s,{'ra':f(r['sra']),'dec':f(r['sdec']),'flux':f(r['flux']),'detml':f(r['detml']),'nc':f(r['nc'])});o=n(r['obsid'])
   if o in old:obs[s].add(o)
 ids=list(p);c=SkyCoord([p[s]['ra'] for s in ids]*u.deg,[p[s]['dec'] for s in ids]*u.deg);_,sep,_=c.match_to_catalog_sky(c4);rec=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and obs[ids[i]]];cases=[s for s in rec if p[s]['nc']==1];ctrl=[ids[i] for i in range(len(ids)) if sep.arcsec[i]<=20 and obs[ids[i]] and p[ids[i]]['nc']==1];om=defaultdict(list)
 for x in ctrl:
  for o in obs[x]&old:om[o].append(x)
 used=set();ca=[];co=[]
 for s in sorted(cases,key=lambda x:hashlib.sha256(x.encode()).hexdigest()):
  q=set()
  for o in obs[s]&old:q.update(om.get(o,[]))
  a=[x for x in q if x not in used];a.sort(key=lambda x:hashlib.sha256((s+'|'+x).encode()).hexdigest());ch=a[:3]
  if not ch:continue
  ca.append(s);co+=ch;used.update(ch)
 def test(k):
  a=np.array([p[s][k] for s in ca]);b=np.array([p[s][k] for s in co]);a=a[np.isfinite(a)&(a>0)];b=b[np.isfinite(b)&(b>0)];a=np.log10(a);b=np.log10(b);return {'median_diff':float(np.median(a)-np.median(b)),'raw_p':float(mannwhitneyu(a,b,alternative='two-sided').pvalue),'n_case':len(a),'n_control':len(b)}
 return {'strict_recoveries':len(rec),'single_contrib_recoveries':len(cases),'single_fraction':len(cases)/len(rec) if rec else None,'matched_single_cases':len(ca),'unique_controls':len(co),'flux':test('flux'),'detml':test('detml')}
def main():
 try:
  c4,old=refs();d=hemi(0,180,c4,old);v=hemi(180,360,c4,old);ps=[d['flux']['raw_p'],d['detml']['raw_p'],v['flux']['raw_p'],v['detml']['raw_p']];adj=[min(1,x*4) for x in ps];d['flux']['bonferroni_p'],d['detml']['bonferroni_p'],v['flux']['bonferroni_p'],v['detml']['bonferroni_p']=adj
  def gate(z):return z['single_contrib_recoveries']>=100 and z['single_fraction']>=.2 and z['flux']['median_diff']<0 and z['detml']['median_diff']<0 and z['flux']['bonferroni_p']<=.01 and z['detml']['bonferroni_p']<=.01
  out={'success':True,'science_status':'PASS' if gate(d) and gate(v) else 'FAIL','development':d,'validation':v,'privacy':'Aggregate only.'}
 except Exception as e:out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()

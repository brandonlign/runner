#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'; P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4O=Path('/tmp/4xmmdr14_obslist.fits'); OUT=Path('results/xmm_high_stack_likelihood.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent=0 AND s.ep_det_ml>=15'
def n(x):
 if isinstance(x,(bytes,np.bytes_)):x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q});req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-high-stack/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r:return Table.read(io.BytesIO(r.read()),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-high-stack/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while 1:
   b=r.read(8388608)
   if not b:break
   f.write(b)
def refs():
 if not P4.exists():dl(U4,P4)
 if not P4O.exists():dl(U4OBS,P4O)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};ra=np.asarray(d[nm['SC_RA']],float);de=np.asarray(d[nm['SC_DEC']],float)
 with fits.open(P4O,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};old={n(x) for x in d[nm['OBS_ID']] if n(x)}
 ok=np.isfinite(ra)&np.isfinite(de);return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def qb(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,s.stack_det_ml sml,d.obsid obsid FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL''';t=tap(q)
 if len(t)>=CAP:
  if depth>=8:raise RuntimeError('cap')
  m=(lo+hi)/2;return qb(lo,m,depth+1)+qb(m,hi,depth+1)
 return [t]
def hemi(lo,hi,c4,old):
 by={};obs=defaultdict(set);ml={}
 for b in range(lo,hi,5):
  ts=qb(float(b),float(b+5));t=vstack(ts,metadata_conflicts='silent') if len(ts)>1 else ts[0]
  for sid,ra,de,sml,ob in zip(t['sid'],t['sra'],t['sdec'],t['sml'],t['obsid']):
   s=n(sid);by.setdefault(s,(float(ra),float(de)));o=n(ob)
   if o in old:obs[s].add(o)
   try:v=float(sml);ml[s]=max(ml.get(s,-np.inf),v) if np.isfinite(v) else ml.get(s,-np.inf)
   except:pass
 ids=list(by);c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg);_,sep,_=c.match_to_catalog_sky(c4);cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and obs[ids[i]]];a20=sum(ml.get(s,-np.inf)>=20 for s in cases);a30=sum(ml.get(s,-np.inf)>=30 for s in cases);fr=a20/len(cases) if cases else None;return {'strict_recoveries':len(cases),'stack_ml_ge20':a20,'fraction_ge20':fr,'stack_ml_ge30':a30,'gate_count_ge100':a20>=100,'gate_fraction_ge0p20':fr is not None and fr>=.2}
def main():
 try:
  c4,old=refs();d=hemi(0,180,c4,old);v=hemi(180,360,c4,old);p=d['gate_count_ge100'] and d['gate_fraction_ge0p20'] and v['gate_count_ge100'] and v['gate_fraction_ge0p20'];out={'success':True,'science_status':'PASS' if p else 'FAIL','development':d,'validation':v,'primary_threshold':20,'descriptive_threshold':30,'privacy':'Aggregate only.'}
 except Exception as e:out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()

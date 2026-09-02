#!/usr/bin/env python3
"""Aggregate coverage diagnostic explicitly allowed by prior-stacked exclusion prereg."""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz';U4O='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits';U4SO='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
P4=Path('/tmp/4main.fits.gz');P4O=Path('/tmp/4mainobs.fits');PSO=Path('/tmp/4stackobs.fits.gz');OUT=Path('results/xmm_prior_stack_coverage_diagnostic.json');OUT.parent.mkdir(parents=True,exist_ok=True);BASE='s.sum_flag<2 AND s.extent=0 AND s.ep_det_ml>=15'
def n(x):
 if isinstance(x,(bytes,np.bytes_)):x=x.decode('utf-8','replace')
 return str(x).strip()
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-stack-coverage/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r,p.open('wb') as g:
  while 1:
   b=r.read(8388608)
   if not b:break
   g.write(b)
def obs(path):
 with fits.open(path,memmap=False) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};c=nm.get('OBS_ID') or nm.get('OBSID');return {n(x) for x in d[c] if n(x)}
def refs():
 if not P4.exists():dl(U4,P4)
 if not P4O.exists():dl(U4O,P4O)
 if not PSO.exists():dl(U4SO,PSO)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};ra=np.asarray(d[nm['SC_RA']],float);de=np.asarray(d[nm['SC_DEC']],float);ok=np.isfinite(ra)&np.isfinite(de);c=SkyCoord(ra[ok]*u.deg,de[ok]*u.deg)
 return c,obs(P4O),obs(PSO)
def tap(q):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q});req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-stack-coverage/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r:return Table.read(io.BytesIO(r.read()),format='votable')
def qb(lo,hi,dep=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,d.obsid obsid FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo} AND s.ra<{hi} AND d.pps_srcnum IS NOT NULL''';t=tap(q)
 if len(t)>=CAP:
  if dep>=8:raise RuntimeError('cap')
  m=(lo+hi)/2;return qb(lo,m,dep+1)+qb(m,hi,dep+1)
 return [t]
def hemi(lo,hi,c4,old,so):
 by={};oo=defaultdict(set)
 for b in range(lo,hi,5):
  ts=qb(b,b+5);t=vstack(ts,metadata_conflicts='silent') if len(ts)>1 else ts[0]
  for sid,ra,de,ob in zip(t['sid'],t['sra'],t['sdec'],t['obsid']):
   s=n(sid);by.setdefault(s,(float(ra),float(de)));o=n(ob)
   if o in old:oo[s].add(o)
 ids=list(by);c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg);_,sep,_=c.match_to_catalog_sky(c4);rec=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and oo[ids[i]]];covered=sum(bool(oo[s]&so) for s in rec);return {'strict_main_only_recoveries':len(rec),'with_at_least_one_genuine_old_obsid_in_4xmmdr14s':covered,'coverage_fraction':covered/len(rec) if rec else None,'without_any_4xmmdr14s_obsid':len(rec)-covered}
def main():
 try:
  c,o,s=refs();out={'success':True,'development':hemi(0,180,c,o,s),'validation':hemi(180,360,c,o,s),'old_stacked_unique_obsids':len(s),'privacy':'Aggregate only; diagnostic does not inspect 4XMM-DR14s source matches.'}
 except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()

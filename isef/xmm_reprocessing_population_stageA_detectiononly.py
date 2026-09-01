#!/usr/bin/env python3
"""Corrected frozen Stage A: old-ObsID membership requires an actual 5XMM detection row (non-null PPS_SRCNUM), not an upper-limit row."""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4OBS=Path('/tmp/4xmmdr14_obslist.fits'); OUT=Path('results/xmm_reprocessing_population_stageA_detectiononly.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 3 AND s.extent = 0 AND s.ep_det_ml >= 15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-stageA-detectiononly/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-stageA-detectiononly/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
def refs():
 if not P4.exists(): dl(U4,P4)
 if not P4OBS.exists(): dl(U4OBS,P4OBS)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float).copy(); de=np.asarray(d[nm['SC_DEC']],float).copy(); n4=len(d)
 with fits.open(P4OBS,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}; no=len(d)
 ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old,n4,no
def qbin(lo,hi):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,d.obsid AS dobsid FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid WHERE {BASE} AND d.pps_srcnum IS NOT NULL AND s.ra >= {lo} AND s.ra < {hi}'''
 t=tap(q)
 if len(t)>=CAP: raise RuntimeError(f'row cap hit {lo}-{hi}; subdivide before interpretation')
 return t
def main():
 try:
  c4,old,n4,no=refs(); bins=[]
  for lo in range(0,180,5):
   t=qbin(lo,lo+5); by={}; obs=defaultdict(set)
   for sid,ra,de,o in zip(t['sid'],t['sra'],t['sdec'],t['dobsid']):
    s=norm(sid); by.setdefault(s,(float(ra),float(de))); z=norm(o)
    if z and z not in ('--','None','nan'): obs[s].add(z)
   ids=list(by); c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4); un=[ids[i] for i in np.flatnonzero(sep.arcsec>20)]; rep=[s for s in un if any(o in old for o in obs[s])]
   b={'ra_lo':lo,'ra_hi':lo+5,'eligible':len(ids),'positionally_unmatched':len(un),'reprocessing_recovered':len(rep),'detection_join_rows':len(t)}; bins.append(b); print(json.dumps(b),flush=True)
  tot={k:sum(b[k] for b in bins) for k in ('eligible','positionally_unmatched','reprocessing_recovered')}; prev=tot['reprocessing_recovered']/tot['eligible']; g1=tot['reprocessing_recovered']>=500; g2=prev>=0.001
  out={'success':True,'science_status':'PASS' if g1 and g2 else 'FAIL','implementation':'detection-only via non-null XMMSTACK.PPS_SRCNUM','hemisphere':'development','ra_range_deg':[0,180],'four_unique_source_rows':n4,'official_dr14_obslist_rows':no,'totals':tot,'reprocessing_prevalence':prev,'frozen_gates':{'g1_reprocessing_recovered_ge_500':g1,'g2_prevalence_ge_0p001':g2},'bins':bins,'privacy':'Aggregate counts only.'}
 except Exception as e: out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

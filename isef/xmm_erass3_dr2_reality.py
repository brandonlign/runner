#!/usr/bin/env python3
"""Frozen eROSITA DR2/eRASS:3 cross-mission reality test using catalogue UID_5XMM.
Aggregate output only."""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
UER='https://erosita.mpe.mpg.de/dr2/AllSkySurveyData_dr2/Catalogues_dr2/RamosM_DR2/eRASS3_Main_v1.3.fits'
P4=Path('/tmp/4x.fits.gz'); PO=Path('/tmp/4obs.fits'); PE=Path('/tmp/erass3.fits'); OUT=Path('results/xmm_erass3_dr2_reality.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-eRASS3-DR2/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p,timeout=1200):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-eRASS3-DR2/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r,p.open('wb') as f:
  while True:
   b=r.read(16*1024*1024)
   if not b: break
   f.write(b)
def refs():
 if not P4.exists(): dl(U4,P4,180)
 if not PO.exists(): dl(U4OBS,PO,180)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float).copy(); de=np.asarray(d[nm['SC_DEC']],float).copy()
 with fits.open(PO,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
 ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def qbin(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,s.sum_flag AS sf,d.obsid AS dobsid,d.pps_srcnum AS pps FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid WHERE s.sum_flag<3 AND s.extent=0 AND s.ep_det_ml>=15 AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'cap {lo}-{hi}')
  m=(lo+hi)/2; return qbin(lo,m,depth+1)+qbin(m,hi,depth+1)
 return [t]
def get_erass_ids():
 if not PE.exists(): dl(UER,PE)
 with fits.open(PE,memmap=True) as h:
  tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]; d=max(tabs,key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}
  c=nm.get('UID_5XMM')
  if c is None: raise RuntimeError('UID_5XMM column absent')
  a=np.asarray(d[c],dtype=np.int64).copy()
 pos=set(map(int,a[a>0])); neg=set(map(int,-a[a<-1])); return pos,neg,len(a)
def hemisphere(c4,old,pos,neg,a,b,strict=False):
 idsall=set(); coords={}; obs=defaultdict(set); flags={}
 for lo in range(a,b,5):
  tabs=qbin(float(lo),float(lo+5)); t=vstack(tabs,metadata_conflicts='silent') if len(tabs)>1 else tabs[0]
  for sid,ra,de,sf,ob in zip(t['sid'],t['sra'],t['sdec'],t['sf'],t['dobsid']):
   s=norm(sid); f=int(sf)
   if strict and f>=2: continue
   idsall.add(s); flags[s]=f
   if s not in coords: coords[s]=(float(ra),float(de))
   o=norm(ob)
   if o in old: obs[s].add(o)
 ids=list(idsall)
 if not ids: return {}
 c=SkyCoord([coords[s][0] for s in ids]*u.deg,[coords[s][1] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4)
 cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and obs[ids[i]]]
 numeric=[]
 for s in cases:
  try: numeric.append(int(s))
  except: pass
 strong=sum(x in pos for x in numeric); weak=sum((x not in pos) and (x in neg) for x in numeric); n=len(cases)
 return {'recoveries':n,'numeric_srcids':len(numeric),'strong_erass3_associations':strong,'weak_only_associations':weak,'strong_fraction_all_recoveries':strong/n if n else None,'support_ge50_and_ge15pct':bool(strong>=50 and strong/n>=0.15 if n else False)}
def main():
 try:
  c4,old=refs(); pos,neg,ner=get_erass_ids(); out={'success':True,'erass3_rows':ner,'strong_uid5xmm_unique':len(pos),'weak_uid5xmm_unique':len(neg),'original':{},'strict_sumflag_lt2':{}}
  for name,a,b in [('development',0,180),('validation',180,360)]: out['original'][name]=hemisphere(c4,old,pos,neg,a,b,False); out['strict_sumflag_lt2'][name]=hemisphere(c4,old,pos,neg,a,b,True)
  out['original_frozen_support_pass']=all(out['original'][h]['support_ge50_and_ge15pct'] for h in ('development','validation')); out['privacy']='Aggregate counts only; no identities or coordinates emitted.'
 except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()

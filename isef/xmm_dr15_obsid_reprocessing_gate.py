#!/usr/bin/env python3
"""Blinded exact-ObsID gate for the 5XMM reprocessing-recovery hypothesis.

The frozen 100k source sample is always reconstructed with the *exact original*
column projection (ra,dec,obsid) that produced the preregistered positional
fingerprint. SRCIDs are attached only afterward from a separately retrieved,
RA-partitioned all-sky index. This avoids HEASARC TOP-row ordering changing when
an extra selected column is added. No source identities are emitted.
"""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u

EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'
U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz')
P4OBS=Path('/tmp/4xmmdr14_obslist.fits')
OUT=Path('results/xmm_dr15_obsid_reprocessing_gate.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='sum_flag < 3 AND extent = 0 AND ep_det_ml >= 15'
FINGERPRINT={'5':3301,'10':1944,'15':1640,'20':1420,'30':1081}

def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()

def save(x):
 OUT.write_text(json.dumps(x,indent=2,sort_keys=True,default=str)+'\n')
 print(json.dumps(x,indent=2,sort_keys=True,default=str))

def tap_table(query,timeout=240):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':query})
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-obsid-gate/1.3'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')

def download(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-obsid-gate/1.3'})
 with urllib.request.urlopen(req,timeout=180) as r,path.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
 return path.stat().st_size

def old_positions():
 if not P4.exists(): download(U4,P4)
 with fits.open(P4,memmap=True) as h:
  tabs=[z for z in h if isinstance(z,(fits.BinTableHDU,fits.TableHDU)) and z.data is not None]
  d=max(tabs,key=lambda z:len(z.data)).data; names={n.upper():n for n in d.names}
  ra=np.asarray(d[names['SC_RA']],float).copy(); de=np.asarray(d[names['SC_DEC']],float).copy(); n=len(d)
 return ra,de,n

def old_obsids():
 if not P4OBS.exists(): download(U4OBS,P4OBS)
 with fits.open(P4OBS,memmap=True) as h:
  tabs=[z for z in h if isinstance(z,(fits.BinTableHDU,fits.TableHDU)) and z.data is not None]
  d=max(tabs,key=lambda z:len(z.data)).data; names={n.upper():n for n in d.names}
  c=names.get('OBS_ID') or names.get('OBSID') or names.get('OBSERVATION_ID')
  if not c: raise RuntimeError('Official DR14 obslist has no recognized ObsID column: '+','.join(d.names))
  vals={norm(x) for x in d[c] if norm(x)}; n=len(d)
 return vals,n,c

def source_index():
 # 30-degree bins keep each result well below HEASARC's 100k query cap. Ordering
 # inside bins is irrelevant because this is only an attachment index.
 ss=[]; rr=[]; dd=[]; counts=[]
 for lo in range(0,360,30):
  hi=lo+30
  q=f'SELECT TOP 100000 srcid,ra,dec FROM xmmssc WHERE {BASE} AND ra >= {lo} AND ra < {hi}'
  t=tap_table(q,300); counts.append(len(t))
  if len(t)>=100000: raise RuntimeError(f'RA bin {lo}-{hi} hit 100k cap')
  ss.extend(norm(x) for x in t['srcid']); rr.extend(float(x) for x in t['ra']); dd.extend(float(x) for x in t['dec'])
 return np.asarray(ss),np.asarray(rr,float),np.asarray(dd,float),counts

def attach_srcids(ra,de):
 src,rr,dd,counts=source_index()
 cidx=SkyCoord(rr*u.deg,dd*u.deg); c=SkyCoord(ra*u.deg,de*u.deg)
 idx,sep,_=c.match_to_catalog_sky(cidx); asec=sep.arcsec
 if np.max(asec)>0.05:
  raise RuntimeError(f'Frozen sample to source-index max match separation {np.max(asec):.6f} arcsec > 0.05')
 matched=src[idx]
 if len(set(matched.tolist())) != len(matched):
  raise RuntimeError('Frozen 100k sample did not attach one-to-one to unique SRCIDs')
 return matched,counts,float(np.max(asec)),float(np.median(asec))

def detection_obsids(srcids):
 out={s:set() for s in srcids}; ids=list(srcids)
 for i in range(0,len(ids),80):
  batch=ids[i:i+80]
  quoted=','.join("'"+s.replace("'","''")+"'" for s in batch)
  t=tap_table(f'SELECT srcid,obsid FROM xmmstack WHERE srcid IN ({quoted})',300)
  if 'srcid' not in t.colnames or 'obsid' not in t.colnames: raise RuntimeError('xmmstack query missing srcid/obsid')
  for sid,obs in zip(t['srcid'],t['obsid']):
   s=norm(sid); o=norm(obs)
   if s in out and o: out[s].add(o)
 return out

def main():
 try:
  # EXACT original projection: do not add fields here.
  t=tap_table(f'SELECT TOP 100000 ra,dec,obsid FROM xmmssc WHERE {BASE}',300)
  ra5=np.asarray(t['ra'],float); de5=np.asarray(t['dec'],float)
  ra4,de4,n4=old_positions(); ok=np.isfinite(ra4)&np.isfinite(de4)
  c4=SkyCoord(ra4[ok]*u.deg,de4[ok]*u.deg); c5=SkyCoord(ra5*u.deg,de5*u.deg)
  _,sep,_=c5.match_to_catalog_sky(c4); s=sep.arcsec
  fp={str(r):int(np.sum(s>r)) for r in (5,10,15,20,30)}
  if fp!=FINGERPRINT:
   save({'success':False,'science_status':'INVALID_SAMPLE_RECONSTRUCTION','observed_fingerprint':fp,'frozen_fingerprint':FINGERPRINT}); return
  src,index_counts,max_attach,median_attach=attach_srcids(ra5,de5)
  m20=s>20; unmatched=src[m20].tolist()
  if len(unmatched)!=FINGERPRINT['20'] or len(set(unmatched))!=len(unmatched):
   save({'success':False,'science_status':'INVALID_DUPLICATE_SRCID_STRUCTURE','n_unmatched_rows':int(m20.sum()),'n_unique_unmatched_srcids':len(set(unmatched))}); return
  oldset,nobs,obscol=old_obsids(); det=detection_obsids(unmatched)
  with_nonblank=[sid for sid in unmatched if det.get(sid)]
  oldhit=[sid for sid in with_nonblank if any(o in oldset for o in det[sid])]
  frac=(len(oldhit)/len(with_nonblank)) if with_nonblank else None
  gate1=len(unmatched)>=1000; gate2=len(oldhit)>=250; gate3=(frac is not None and frac>=0.25)
  save({'success':True,'science_status':'PASS' if gate1 and gate2 and gate3 else 'FAIL',
        'source_sample_rows':len(t),'positional_fingerprint':fp,'frozen_fingerprint_reproduced':True,
        'source_index_ra_bin_counts':index_counts,'source_index_rows':int(sum(index_counts)),
        'source_attachment_max_arcsec':max_attach,'source_attachment_median_arcsec':median_attach,
        'four_unique_source_rows':n4,'official_dr14_obslist_rows':nobs,'official_dr14_obsid_column':obscol,
        'official_dr14_unique_obsids':len(oldset),'n_unmatched_20arcsec':len(unmatched),
        'n_unmatched_with_detection_obsid':len(with_nonblank),'n_unmatched_with_any_dr14_obsid':len(oldhit),
        'fraction_dr14_given_nonblank':frac,
        'frozen_gates':{'g1_n_unmatched_ge_1000':gate1,'g2_old_obsid_hits_ge_250':gate2,'g3_old_fraction_ge_0p25':gate3},
        'privacy':'No source names, coordinates, SRCIDs, or individual ObsIDs emitted.'})
 except Exception as e:
  save({'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'})

if __name__=='__main__': main()

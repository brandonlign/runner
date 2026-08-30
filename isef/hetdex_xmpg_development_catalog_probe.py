#!/usr/bin/env python3
"""Development-only HETDEX XMPG catalog feasibility probe.
Uses HPSC1 only and externally published O3ELG coordinates. No HPSC2-new identities.
"""
from pathlib import Path
from collections import defaultdict
import json, urllib.request, math
import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
OUT=Path('results/hetdex_xmpg_development_catalog_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='https://web.corral.tacc.utexas.edu/hetdex/HETDEX/catalogs/hetdex_source_catalog_1/'
FILES={'source':BASE+'hetdex_sc1_v3.2.fits','det':BASE+'hetdex_sc1_detinfo_v3.2.fits'}
# Published Indahl+ 2021 Table 1 coordinates; labels are known positive-control objects.
CONTROLS=[
('O3ELG1',31.0511,-0.2286,0.0780),('O3ELG2',8.2826,-0.1793,0.0780),('O3ELG3',6.0817,-0.0720,0.0840),
('O3ELG4a',9.8204,-0.0121,0.0820),('O3ELG5',9.7674,0.0360,0.0830),('O3ELG6',13.4199,0.0403,0.0700),
('O3ELG7',32.9842,0.0585,0.0960),('O3ELG8',31.8456,0.1995,0.0630),('O3ELG9',203.8739,51.0155,0.0620),
('O3ELG10',197.6288,51.0607,0.0330),('O3ELG11',176.0732,51.1047,0.0840),('O3ELG12a',200.1701,51.1910,0.0730),
('O3ELG13',None,None,None),('O3ELG14',None,None,0.0904),('O3ELG15',None,None,0.0267),('O3ELG16',None,None,0.0706)]
# Only coordinates visible in the externally retrieved Table 1 are used; controls without coordinates remain unqueried.
REST={'oii':3727.0,'hgamma':4340.47,'oiii4363':4363.21,'hbeta':4861.33,'oiii4959':4958.91,'oiii5007':5006.84}
def dl(url,p):
 if p.exists() and p.stat().st_size>100000:return
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-HETDEX-XMPG-dev/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r, open(p,'wb') as f:
  while True:
   b=r.read(4<<20)
   if not b:break
   f.write(b)
def val(x):
 if np.ma.is_masked(x):return None
 if isinstance(x,(bytes,np.bytes_)):return x.decode(errors='replace').strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x
def nearest_line(rows,z,rest,tol=8.0):
 want=rest*(1+z);best=None
 for r in rows:
  try:w=float(r['wave'])
  except:continue
  d=abs(w-want)
  if d<=tol and (best is None or d<best['delta_A']):
   best={'delta_A':d,'wave':w,'line_id':val(r['line_id']) if 'line_id' in r.array.names else None,
         'sn':float(r['sn']) if 'sn' in r.array.names and np.isfinite(r['sn']) else None,
         'flux':float(r['flux']) if 'flux' in r.array.names and np.isfinite(r['flux']) else None,
         'chi2':float(r['chi2']) if 'chi2' in r.array.names and np.isfinite(r['chi2']) else None}
 return best
def main():
 out={'status':'DEVELOPMENT_ONLY','hpsc2_new_opened':False,'success':False,'controls':[]}
 try:
  ps=Path('/tmp/hpsc1_source.fits');pd=Path('/tmp/hpsc1_det.fits');dl(FILES['source'],ps);dl(FILES['det'],pd)
  with fits.open(ps,memmap=True) as h:
   tab=max([x for x in h if getattr(x,'data',None) is not None and hasattr(x.data,'names')],key=lambda x:len(x.data)).data
   names=list(tab.names);ra=np.asarray(tab['RA'],float);dec=np.asarray(tab['DEC'],float);z=np.asarray(tab['z_hetdex'],float);stype=np.asarray(tab['source_type']).astype(str)
   good=np.isfinite(z)&(z>=0.005)&(z<=0.085)
   out['source_columns']=names
   out['hpsc1_source_rows']=int(len(tab));out['hpsc1_lowz_005_0085_rows']=int(good.sum())
   out['hpsc1_lowz_source_types']={str(k):int(v) for k,v in zip(*np.unique(stype[good],return_counts=True))}
   coords=SkyCoord(ra*u.deg,dec*u.deg)
   matches=[]
   for lab,cra,cdec,cz in CONTROLS:
    if cra is None:out['controls'].append({'label':lab,'queryable':False,'reason':'coordinate_not_imported_from_external_table'});continue
    c=SkyCoord(cra*u.deg,cdec*u.deg);idx,sep,_=c.match_to_catalog_sky(coords);sep=float(sep.arcsec)
    rec={'label':lab,'queryable':True,'nearest_sep_arcsec':sep,'matched':sep<=3.0,'published_z':cz}
    if sep<=3.0:
     rec.update({'catalog_z':float(z[idx]),'source_type':str(stype[idx]),'source_id':int(tab['source_id'][idx]),'shotid':int(tab['shotid'][idx])})
    out['controls'].append(rec)
  with fits.open(pd,memmap=True) as h:
   d=max([x for x in h if getattr(x,'data',None) is not None and hasattr(x.data,'names')],key=lambda x:len(x.data)).data
   out['det_columns']=list(d.names);out['hpsc1_detection_rows']=int(len(d));by=defaultdict(list)
   for i,r in enumerate(out['controls']):
    if r.get('matched'):by[r['source_id']]=r
   if by:
    ids=np.asarray(d['source_id'])
    for sid,rec in by.items():
     rr=d[ids==sid];rec['n_detection_rows']=int(len(rr));zz=rec['catalog_z'];rec['expected_line_matches']={k:nearest_line(rr,zz,v) for k,v in REST.items()}
   # Anonymous feasibility counts: low-z detection groups with high-S/N 5007-like line and coherent 4959/3727 windows.
   # Group only source_ids already classified at z<=0.085 in source table; no unknown IDs emitted.
   # Reopen compact source mapping from controls not enough, so use detection table z/source_type directly.
   zdet=np.asarray(d['z_hetdex'],float);typ=np.asarray(d['source_type']).astype(str);wave=np.asarray(d['wave'],float);sn=np.asarray(d['sn'],float) if 'sn' in d.names else np.full(len(d),np.nan)
   low=np.isfinite(zdet)&(zdet>=0.005)&(zdet<=0.085)&np.isfinite(wave)
   target=np.abs(wave-REST['oiii5007']*(1+zdet))<=8.0
   strong=low&target&np.isfinite(sn)&(sn>=10)
   out['anonymous_highsn_5007_detection_rows']=int(strong.sum())
   out['anonymous_highsn_5007_unique_sources']=int(len(np.unique(np.asarray(d['source_id'])[strong])))
  out['matched_queryable_controls']=int(sum(1 for r in out['controls'] if r.get('matched')))
  out['success']=True
 except Exception as e:out['error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

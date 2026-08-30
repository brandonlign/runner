#!/usr/bin/env python3
"""Development-only HETDEX XMPG control probe via VizieR HPSC1 mirror.
Queries only externally published Indahl+2021 control coordinates. Never queries HPSC2.
"""
from pathlib import Path
import json
import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier
OUT=Path('results/hetdex_xmpg_vizier_control_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
CONTROLS=[
('O3ELG1',31.0511,-0.2286,0.0780),('O3ELG2',8.2826,-0.1793,0.0780),('O3ELG3',6.0817,-0.0720,0.0840),
('O3ELG4a',9.8204,-0.0121,0.0820),('O3ELG5',9.7674,0.0360,0.0830),('O3ELG6',13.4199,0.0403,0.0700),
('O3ELG7',32.9842,0.0585,0.0960),('O3ELG8',31.8456,0.1995,0.0630),('O3ELG9',203.8739,51.0155,0.0620),
('O3ELG10',197.6288,51.0607,0.0330),('O3ELG11',176.0732,51.1047,0.0840),('O3ELG12a',200.1701,51.1910,0.0730),
('O3ELG12b',200.1696,51.1921,0.0730),('O3ELG13',172.8717,51.2003,0.0650),('O3ELG14',176.4366,51.2577,0.0900),
('O3ELG15',212.7970,51.2664,0.0270),('O3ELG16',168.1299,51.8901,0.0710)]
REST={'oii':3727.0,'hgamma':4340.47,'oiii4363':4363.21,'hbeta':4861.33,'oiii4959':4958.91,'oiii5007':5006.84}
def py(x):
 if np.ma.is_masked(x):return None
 if isinstance(x,(bytes,np.bytes_)):return x.decode(errors='replace').strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:pass
 return str(x)
def findcol(cols,*keys):
 lo={c.lower().replace('_','').replace('-',''):c for c in cols}
 for k in keys:
  kk=k.lower().replace('_','').replace('-','')
  if kk in lo:return lo[kk]
 for c in cols:
  cc=c.lower().replace('_','').replace('-','')
  if any(k.lower().replace('_','').replace('-','') in cc for k in keys):return c
 return None
def main():
 out={'success':False,'status':'DEVELOPMENT_ONLY','hpsc2_new_opened':False,'controls':[],'catalogs':['J/ApJ/943/177/sources','J/ApJ/943/177/detinfo']}
 try:
  V=Vizier(columns=['**'],row_limit=-1,timeout=120)
  for lab,ra,dec,zpub in CONTROLS:
   c=SkyCoord(ra*u.deg,dec*u.deg);rec={'label':lab,'published_z':zpub,'inside_primary_z':0.005<=zpub<=0.085}
   src=V.query_region(c,radius=3*u.arcsec,catalog='J/ApJ/943/177/sources')
   det=V.query_region(c,radius=3*u.arcsec,catalog='J/ApJ/943/177/detinfo')
   rec['source_rows']=sum(len(t) for t in src);rec['det_rows']=sum(len(t) for t in det)
   rec['source_columns']=list(src[0].colnames) if len(src) else []
   rec['det_columns']=list(det[0].colnames) if len(det) else []
   if len(src):
    t=src[0];cz=findcol(t.colnames,'z_hetdex','zHETDEX','z');sid=findcol(t.colnames,'source_id','SourceID');st=findcol(t.colnames,'source_type','Type')
    if len(t):
     rec['catalog_z']=float(t[cz][0]) if cz and np.isfinite(t[cz][0]) else None
     rec['source_id']=py(t[sid][0]) if sid else None;rec['source_type']=py(t[st][0]) if st else None
   lines=[]
   if len(det):
    for t in det:
     wc=findcol(t.colnames,'wave','wavelength');snc=findcol(t.colnames,'sn','SNR');fc=findcol(t.colnames,'flux');lc=findcol(t.colnames,'line_id','lineID')
     for r in t:
      w=float(r[wc]) if wc and not np.ma.is_masked(r[wc]) else np.nan
      if not np.isfinite(w):continue
      lines.append({'wave':w,'sn':float(r[snc]) if snc and not np.ma.is_masked(r[snc]) else None,'flux':float(r[fc]) if fc and not np.ma.is_masked(r[fc]) else None,'line_id':py(r[lc]) if lc else None})
   rec['expected_lines']={}
   zuse=rec.get('catalog_z') if rec.get('catalog_z') is not None else zpub
   for name,rw in REST.items():
    want=rw*(1+zuse);cand=[x for x in lines if abs(x['wave']-want)<=8]
    rec['expected_lines'][name]=min(cand,key=lambda x:abs(x['wave']-want)) if cand else None
   out['controls'].append(rec)
  out['n_controls_with_source_rows']=sum(r['source_rows']>0 for r in out['controls'])
  out['n_controls_with_any_det_rows']=sum(r['det_rows']>0 for r in out['controls'])
  out['n_controls_with_catalog_4363_detection']=sum(r['expected_lines']['oiii4363'] is not None for r in out['controls'])
  out['n_primary_domain_controls_with_catalog_4363_detection']=sum(r['inside_primary_z'] and r['expected_lines']['oiii4363'] is not None for r in out['controls'])
  out['note']='Catalog detection rows are only a sensitivity precheck; formal control gate still requires spectrum-level fitting. No HPSC2 queried.'
  out['success']=True
 except Exception as e:out['error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Metadata-only eROSITA-new-ULX -> XMM archival coverage kill test.

STRICT INFORMATION BARRIER: catalog + XMM observation/exposure metadata only.
No XMM event photons, source light curves, arrival times, or timing outcomes.
"""
from __future__ import annotations
import io, json
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u

OUT=Path('results/erosita_ulx_xmm_coverage'); OUT.mkdir(parents=True,exist_ok=True)
EROSITA_FITS='https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/WeberP_DR1/ulx_erass1_main.fits'
XSA_SYNC='https://nxsa.esac.esa.int/tap-server/tap/sync'
PRIOR_FLAGS=['f_walton','f_bernadich','f_kovlakas','f_tranin_ulx','f_tranin_hlx']

def tap(q,timeout=300):
 r=requests.post(XSA_SYNC,data={'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q},timeout=timeout)
 if not r.ok: raise RuntimeError(f'XSA HTTP {r.status_code} for ADQL: {q}\n{r.text[:2500]}')
 t=r.text
 try:return pd.read_csv(io.StringIO(t))
 except Exception as e: raise RuntimeError(t[:2500]) from e

def df_fits(b):
 with fits.open(io.BytesIO(b),memmap=False) as h:
  x=next(z for z in h if isinstance(z,(fits.BinTableHDU,fits.TableHDU))).data
  d={}
  for c in x.names:
   vals=[]
   for v in x[c]:
    if isinstance(v,(bytes,bytearray)): v=v.decode('utf8','replace').strip()
    elif isinstance(v,np.generic): v=v.item()
    vals.append(v)
   d[c]=vals
 return pd.DataFrame(d)

def col(df,*names):
 m={str(c).lower():c for c in df.columns}
 for n in names:
  if n.lower() in m:return m[n.lower()]
 raise KeyError((names,list(df.columns)))

def flag_false(v):
 if pd.isna(v):return True
 if isinstance(v,(bool,np.bool_)):return not bool(v)
 return str(v).strip().lower() in {'0','0.0','false','f','n','no','none','nan',''}

def schema(table):
 return tap("SELECT column_name,datatype,description,unit FROM TAP_SCHEMA.columns WHERE table_name='"+table+"' ORDER BY column_index")

def pick(s,names,required=False):
 a={str(x).lower():str(x) for x in s.column_name.tolist()} if len(s) else {}
 for n in names:
  if n.lower() in a:return a[n.lower()]
 if required:raise KeyError((names,sorted(a)))
 return None

def sep_arcmin(ra,dec,oras,odecs):
 a=SkyCoord(float(ra)*u.deg,float(dec)*u.deg); b=SkyCoord(np.asarray(oras,float)*u.deg,np.asarray(odecs,float)*u.deg); return a.separation(b).arcmin

def norm_obsid(v):
 """XMM observation IDs are fixed-width 10-character identifiers.

 CSV parsing may coerce an all-digit identifier to integer/float and strip the
 leading zero, so restore it mechanically before any exposure-table join.
 """
 if pd.isna(v): return ''
 if isinstance(v,(int,np.integer)): s=str(int(v))
 elif isinstance(v,(float,np.floating)) and float(v).is_integer(): s=str(int(v))
 else:
  s=str(v).strip()
  if s.endswith('.0') and s[:-2].isdigit(): s=s[:-2]
 return s.zfill(10) if s.isdigit() else s

def main():
 report={'information_barrier':'eROSITA catalog + XMM metadata only; no event photons or timing outcomes'}
 r=requests.get(EROSITA_FITS,timeout=120); r.raise_for_status(); cat=df_fits(r.content)
 report['main_rows']=len(cat)
 if len(cat)!=90:raise RuntimeError(f'expected 90 rows, got {len(cat)}')
 iau=col(cat,'IAUNAME'); ra=col(cat,'RAJ2000','RA'); dec=col(cat,'DEJ2000','DEC')
 lm={str(c).lower():c for c in cat.columns}; missing=[f for f in PRIOR_FLAGS if f not in lm]
 if missing: raise RuntimeError(f'missing flags {missing}; cols={list(cat.columns)}')
 mask=pd.Series(True,index=cat.index)
 for f in PRIOR_FLAGS: mask &= cat[lm[f]].map(flag_false)
 new=cat[mask].copy(); report['new_rows']=len(new)
 if len(new)!=53: raise RuntimeError(f'expected 53 new rows, got {len(new)}')
 new[[iau,ra,dec]+[lm[f] for f in PRIOR_FLAGS]].to_csv(OUT/'new_sources.csv',index=False)

 tabs=tap("SELECT table_name,description FROM TAP_SCHEMA.tables WHERE table_name LIKE '%observation%' OR table_name LIKE '%exposure%'")
 tabs.to_csv(OUT/'tables.csv',index=False); names={str(x).lower():str(x) for x in tabs.table_name}
 obs=next((names[x] for x in ['xsa.v_public_observations','v_public_observations','xsa.v_all_observations','v_all_observations'] if x in names),None)
 exp=next((names[x] for x in ['xsa.v_exposure','v_exposure','xsa.v_exposures','v_exposures'] if x in names),None)
 report['obs_table']=obs; report['exp_table']=exp
 if not obs: raise RuntimeError(f'no observation table: {list(names.values())}')
 os=schema(obs); os.to_csv(OUT/'obs_schema.csv',index=False)
 es=schema(exp) if exp else pd.DataFrame();
 if exp: es.to_csv(OUT/'exp_schema.csv',index=False)
 oid=pick(os,['observation_id','obs_id','obsid'],True); ora=pick(os,['ra'],True); odec=pick(os,['dec'],True); dur=pick(os,['duration','observation_duration'],True)
 target=pick(os,['target','target_name']); start=pick(os,['start_utc','start_time'])
 cols=[oid,ora,odec,dur]+[x for x in [target,start] if x]
 q='SELECT '+','.join(cols)+' FROM '+obs
 ob=tap(q); ob['_obsid_norm']=ob[oid].map(norm_obsid); report['public_obs_rows']=len(ob)
 matches=[]
 for _,s in new.iterrows():
  seps=sep_arcmin(s[ra],s[dec],ob[ora],ob[odec]); idx=np.where(seps<=13)[0]
  for j in idx:
   x=ob.iloc[j]; z={'iauname':str(s[iau]),'ra':float(s[ra]),'dec':float(s[dec]),'observation_id':str(x['_obsid_norm']),'offaxis_arcmin':float(seps[j]),'observation_duration_s':float(x[dur])}
   if target:z['target']=str(x[target])
   if start:z['start']=str(x[start])
   matches.append(z)
 m=pd.DataFrame(matches); m.to_csv(OUT/'obs_matches.csv',index=False)
 long=m[m.observation_duration_s>=10000] if len(m) else m
 report['sources_any_xmm_13arcmin']=int(m.iauname.nunique()) if len(m) else 0
 report['sources_obs_ge10ks']=int(long.iauname.nunique()) if len(long) else 0
 report['obs_matches_ge10ks']=len(long)

 if exp and len(long):
  eo=pick(es,['observation_id','obs_id','obsid'],True); inst=pick(es,['instrument','instrument_name','instrument_id']); ed=pick(es,['duration','exposure_duration','scheduled_duration','performed_duration']); eid=pick(es,['exposure_id','exp_id']); mode=pick(es,['mode_friendly_name','mode','instrument_mode','exposure_mode']); filt=pick(es,['filter','filter_name'])
  report['exposure_columns']={'obsid':eo,'instrument':inst,'duration':ed,'exposure_id':eid,'mode':mode,'filter':filt}
  if inst and ed:
   ids=sorted(set(long.observation_id.map(norm_obsid))); chunks=[]; ecols=[x for x in [eo,eid,inst,ed,mode,filt] if x]
   report['matched_obsids_for_exposure_query']=ids
   for k in range(0,len(ids),40):
    il=','.join("'"+x.replace("'","''")+"'" for x in ids[k:k+40]); chunks.append(tap(f"SELECT {','.join(ecols)} FROM {exp} WHERE {eo} IN ({il})"))
   ee=pd.concat(chunks,ignore_index=True); ee['_obsid_norm']=ee[eo].map(norm_obsid); ee.to_csv(OUT/'exposures.csv',index=False)
   ii=ee[inst].astype(str).str.lower(); pn=ee[ii.str.contains('pn',regex=False)|ii.str.contains('epn',regex=False)].copy(); report['pn_rows']=len(pn); report['exposure_instruments']=sorted(set(ee[inst].astype(str)))
   if len(pn):
    pn['pn_duration_s']=pd.to_numeric(pn[ed],errors='coerce'); agg=pn.groupby('_obsid_norm',as_index=False).pn_duration_s.sum(min_count=1); mm=long.merge(agg,left_on='observation_id',right_on='_obsid_norm',how='left'); mm.to_csv(OUT/'pn_matches.csv',index=False); gp=mm[mm.pn_duration_s>=10000]; report['sources_pn_ge10ks']=int(gp.iauname.nunique()); report['pn_matches_ge10ks']=len(gp)
   else: report['sources_pn_ge10ks']=0
  else: report['pn_schema_unresolved']=True
 else: report['pn_metadata_not_run']=True
 report['count_screen']='NOT_RUN_BY_DESIGN'
 (OUT/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+'\n'); print(json.dumps(report,indent=2,sort_keys=True,default=str))

if __name__=='__main__': main()

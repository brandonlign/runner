#!/usr/bin/env python3
"""Infrastructure-only exact-link probe for 4XMM-DR14 and 5XMM-DR15.

No candidate identities are selected or emitted. Establishes whether public TAP
services expose (1) the exact DR14 observation set and (2) 5XMM source-to-ObsID
links needed for a defensible reprocessing-only cohort.
"""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
OUT=Path('results/xmm_exact_link_schema.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP4='https://xcatdb.unistra.fr/xtapdb/sync'
EP5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'

def query(ep,adql):
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':adql}).encode()
 req=urllib.request.Request(ep,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-exact-link/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:raw=r.read()
 txt=raw.decode('utf-8','replace')
 if 'QUERY_STATUS' in txt[:10000] and ('value="ERROR"' in txt[:10000] or '>ERROR<' in txt[:10000]):raise RuntimeError(txt[:10000])
 t=Table.read(io.BytesIO(raw),format='votable');rows=[]
 for rr in t:
  z={}
  for n in t.colnames:
   x=rr[n]
   if np.ma.is_masked(x):z[n]=None
   elif isinstance(x,bytes):z[n]=x.decode('utf-8','replace')
   elif hasattr(x,'item'):
    try:z[n]=x.item()
    except:z[n]=str(x)
   else:z[n]=x
  rows.append(z)
 return rows

def compact_cols(rows):
 return [r for r in rows if any(k in str(r.get('column_name','')).lower() for k in ('obs','src','ra','dec','mjd','flag','extent','det_ml','contrib','upper','stack'))]

def main():
 out={'success':True,'dr14_endpoint':EP4,'dr15_endpoint':EP5}
 tests={
  'dr14_obscore_columns':(EP4,"SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='obscore'"),
  'dr14_obscore_sample':(EP4,'SELECT TOP 3 * FROM obscore'),
  'dr14_obscore_count':(EP4,'SELECT COUNT(*) AS n FROM obscore'),
  'dr15_xmmstack_sample':(EP5,'SELECT TOP 8 srcid,ra,dec,n_obs,n_contrib,n_detections,n_upper_lims,obsid,mjd_first,mjd_last,ep_det_ml,stack_det_ml,sum_flag,extent FROM xmmstack'),
  'dr15_xmmstack_count':(EP5,'SELECT COUNT(*) AS n FROM xmmstack'),
 }
 for k,(ep,q) in tests.items():
  try:
   z=query(ep,q)
   if k.endswith('_columns'):z=compact_cols(z)
   out[k]=z
  except Exception as e:out[k+'_error']=f'{type(e).__name__}: {e}'
 # Try likely ObsID spellings only if the obscore schema is accessible.
 cols=[str(r.get('column_name','')) for r in out.get('dr14_obscore_columns',[])]
 for c in cols:
  if c.lower() in ('obs_id','obsid','obs_publisher_did','obs_collection'):
   try:out[f'dr14_distinct_{c}']=query(EP4,f'SELECT DISTINCT {c} FROM obscore')[:20000]
   except Exception as e:out[f'dr14_distinct_{c}_error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()

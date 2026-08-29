#!/usr/bin/env python3
"""Probe XSA candidate legacy/source tables for exact ObsID access.

Infrastructure-only. Queries schema plus a compact anonymous sample of structural
columns; no 5XMM candidate cohort is selected.
"""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
EP='https://nxsa.esac.esa.int/tap-server/tap/sync'
OUT=Path('results/xmm_xsa_legacy_tables_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
TABLES=['xsa.v_epic_source','xsa.small_epic_source_cat']

def query(q):
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode()
 req=urllib.request.Request(EP,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XSA-legacy-probe/1.0'})
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

def main():
 out={'success':True,'endpoint':EP}
 for tab in TABLES:
  key=tab.replace('.','_')
  try:
   cols=query(f"SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='{tab}'")
   rel=[r for r in cols if any(s in str(r.get('column_name','')).lower() for s in ('obs','src','det','ra','dec','mjd','time','flag','extent','catalog','version','rev'))]
   out[key+'_relevant_columns']=rel
   out[key+'_column_count']=len(cols)
   out[key+'_count']=query(f'SELECT COUNT(*) AS n FROM {tab}')
   names=[str(r.get('column_name')) for r in cols]
   wanted=[]
   for cand in ('obs_id','obsid','observation_id','source_id','srcid','detid','det_id','ra','dec','mjd_start','mjd_end','start_time','end_time','sum_flag','extent'):
    hit=next((n for n in names if n.lower()==cand),None)
    if hit and hit not in wanted:wanted.append(hit)
   if wanted:
    out[key+'_structural_sample']=query(f"SELECT TOP 5 {','.join(wanted)} FROM {tab}")
  except Exception as e:out[key+'_error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()

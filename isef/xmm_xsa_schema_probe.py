#!/usr/bin/env python3
"""Probe ESA XSA TAP for 4XMM-DR14 catalogue and observation linkage.
Infrastructure only; no 5XMM candidate identities are requested.
"""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
EP='https://nxsa.esac.esa.int/tap-server/tap/sync'
OUT=Path('results/xmm_xsa_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)

def query(q):
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode()
 req=urllib.request.Request(EP,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XSA-schema/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:raw=r.read()
 txt=raw.decode('utf-8','replace')
 if 'QUERY_STATUS' in txt[:10000] and ('value="ERROR"' in txt[:10000] or '>ERROR<' in txt[:10000]):raise RuntimeError(txt[:10000])
 t=Table.read(io.BytesIO(raw),format='votable');out=[]
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
  out.append(z)
 return out

def main():
 out={'success':True,'endpoint':EP}
 try:
  tabs=query("SELECT table_name,description FROM TAP_SCHEMA.tables")
  out['xmm_candidate_tables']=[r for r in tabs if any(s in str(r.get('table_name','')).lower() for s in ('epic','4xmm','xmm','stack'))][:200]
 except Exception as e:out['tables_error']=f'{type(e).__name__}: {e}'
 # Known historical table first; current XSA maps this view to current 4XMM release.
 for tab in ('xsa.v_epic_source_cat','xsa.v_epic_xmm_stack_cat'):
  key=tab.replace('.','_')
  try:
   cols=query(f"SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='{tab}'")
   out[key+'_relevant_columns']=[r for r in cols if any(s in str(r.get('column_name','')).lower() for s in ('obs','src','ra','dec','mjd','flag','det_ml','extent'))]
   out[key+'_sample']=query(f'SELECT TOP 2 * FROM {tab}')
   out[key+'_count']=query(f'SELECT COUNT(*) AS n FROM {tab}')
  except Exception as e:out[key+'_error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()

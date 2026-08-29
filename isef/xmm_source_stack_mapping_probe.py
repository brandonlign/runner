#!/usr/bin/env python3
"""Infrastructure-only probe of 5XMM source/stack identifiers.
No spectral outcomes or source identities are emitted."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';OUT=Path('results/xmm_source_stack_mapping_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)

def q(adql):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':adql}).encode();req=urllib.request.Request(EP,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-stack-map/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:raw=r.read()
 txt=raw.decode('utf-8','replace')
 if 'QUERY_STATUS' in txt[:8000] and ('value="ERROR"' in txt[:8000] or '>ERROR<' in txt[:8000]):raise RuntimeError(txt[:8000])
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
 for tab in ('xmmstack','xmmstackob'):
  try:
   cols=q(f"SELECT column_name,datatype,description FROM TAP_SCHEMA.columns WHERE table_name='{tab}'")
   out[tab+'_mapping_columns']=[r for r in cols if any(s in str(r.get('column_name','')).lower() for s in ('src','stack','obs','row','summary','n_obs','n_contrib'))]
  except Exception as e:out[tab+'_columns_error']=f'{type(e).__name__}: {e}'
 # Try structural samples with progressively safer column sets.
 tests={
  'xmmstack_structural':"SELECT TOP 20 srcid,obs_id,n_obs,n_contrib FROM xmmstack",
  'xmmstackob_structural':"SELECT TOP 20 stack_id,obsid FROM xmmstackob",
 }
 for k,s in tests.items():
  try:out[k]=q(s)
  except Exception as e:out[k+'_error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()

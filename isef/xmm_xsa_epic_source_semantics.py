#!/usr/bin/env python3
"""Inspect XSA v_epic_source structural columns for catalogue-membership metadata.
No science candidate selection."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table
EP='https://nxsa.esac.esa.int/tap-server/tap/sync';OUT=Path('results/xmm_xsa_epic_source_semantics.json');OUT.parent.mkdir(parents=True,exist_ok=True)

def q(s):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':s}).encode();req=urllib.request.Request(EP,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XSA-epic-source-semantics/1.0'})
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
 try:out['columns']=q("SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='xsa.v_epic_source'")
 except Exception as e:out['columns_error']=f'{type(e).__name__}: {e}'
 # Probe counts by any plausible quality/catalogue membership fields discovered.
 names=[str(r.get('column_name','')) for r in out.get('columns',[])]
 for n in names:
  if any(s in n.lower() for s in ('catalog','cat_', 'quality','flag','public','process','version','date','time','observation')):
   try:out['distinct_'+n]=q(f'SELECT {n},COUNT(*) AS n FROM xsa.v_epic_source GROUP BY {n}')[:200]
   except Exception as e:out['distinct_'+n+'_error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()

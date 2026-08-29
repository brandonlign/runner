#!/usr/bin/env python3
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
OUT=Path('results/xmm_dr14_variability_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://sky.esa.int/esasky-tap/tap/sync';TAB='catalogues.mv_xsa_epic_stack_cat_fdw'
def tap(q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(EP,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-var-schema/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');out=[]
 for rr in t:
  row={}
  for n in t.colnames:
   x=rr[n]
   if hasattr(x,'item'):
    try:x=x.item()
    except:pass
   row[n]=x.decode().strip() if isinstance(x,bytes) else str(x) if not isinstance(x,(int,float,bool,type(None))) else x
  out.append(row)
 return out
def main():
 rows=tap(f"SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='{TAB}' ORDER BY column_name")
 keys=('fratio','var','chi','contrib','n_obs','det_ml','radec_err','flux')
 rel=[r for r in rows if any(k in str(r['column_name']).lower() for k in keys)]
 out={'success':True,'table':TAB,'relevant_columns':rel,'note':'Schema metadata only; no source values queried.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

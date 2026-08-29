#!/usr/bin/env python3
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
OUT=Path('results/xmm_dr15_position_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
def tap(q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(EP,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-pos-schema/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:(rr[n].item() if hasattr(rr[n],'item') else str(rr[n])) for n in t.colnames} for rr in t]
def main():
 rows=tap("SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='xmmstack' ORDER BY column_name")
 keys=('err','pos','ra','dec','extent','sum_flag','stack_det_ml')
 rel=[r for r in rows if any(k in str(r['column_name']).lower() for k in keys)]
 out={'success':True,'relevant_columns':rel}
 OUT.write_text(json.dumps(out,indent=2,default=str,sort_keys=True)+'\n');print(json.dumps(out,indent=2,default=str,sort_keys=True))
if __name__=='__main__':main()

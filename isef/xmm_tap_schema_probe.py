#!/usr/bin/env python3
"""Infrastructure-only probe for XMM catalogue table/version access.
No candidate source rows are requested."""
import io,json,urllib.parse,urllib.request
from pathlib import Path
import numpy as np
from astropy.table import Table
TAP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
OUT=Path('results/xmm_tap_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)

def q(adql):
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':adql}).encode();req=urllib.request.Request(TAP,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-XMM-schema/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:raw=r.read()
 txt=raw.decode('utf-8','replace')
 if 'value="ERROR"' in txt[:6000]: raise RuntimeError(txt[:6000])
 t=Table.read(io.BytesIO(raw),format='votable');return [{str(n):('' if np.ma.is_masked(r[n]) else str(r[n])) for n in t.colnames} for r in t]

def main():
 out={'success':True}
 for key,adql in {
  'tables':"SELECT table_name,description FROM TAP_SCHEMA.tables WHERE table_name LIKE '%xmm%'",
  'xmmssc_columns':"SELECT column_name,datatype,description FROM TAP_SCHEMA.columns WHERE table_name='xmmssc'",
  'xmmstack_columns':"SELECT column_name,datatype,description FROM TAP_SCHEMA.columns WHERE table_name='xmmstack'",
 }.items():
  try:out[key]=q(adql)
  except Exception as e:out[key+'_error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

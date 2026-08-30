#!/usr/bin/env python3
"""Schema-only probe for the new HEASARC AMS02RATES table. Reads no science rows."""
import io,json,urllib.parse,urllib.request
from pathlib import Path
from astropy.table import Table
OUT=Path('results/ams02_rates_schema_probe.json'); OUT.parent.mkdir(exist_ok=True)
TAP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
o={'status':'SCHEMA_ONLY','science_rows_accessed':False,'success':False}
try:
 q="SELECT column_name,datatype,unit,description FROM TAP_SCHEMA.columns WHERE table_name='ams02rates' ORDER BY column_index"
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}).encode()
 req=urllib.request.Request(TAP,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-AMS02-Schema/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r: raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable')
 o['columns']=[{str(n):str(row[n]) for n in t.colnames} for row in t]
 o['column_count']=len(t); o['success']=True; o['decision']='AMS02RATES_SCHEMA_ACCESSIBLE'
except Exception as e:
 o['error']=type(e).__name__+': '+str(e); o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENCE_DECISION'
OUT.write_text(json.dumps(o,indent=2)+'\n'); print(json.dumps(o,indent=2))

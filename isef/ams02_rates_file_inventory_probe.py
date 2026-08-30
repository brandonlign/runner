#!/usr/bin/env python3
"""Metadata-only AMS02RATES inventory. No rate_mean/min/max and no FITS science rows."""
import io,json,urllib.parse,urllib.request
from pathlib import Path
from astropy.table import Table
OUT=Path('results/ams02_rates_file_inventory_probe.json'); OUT.parent.mkdir(exist_ok=True)
TAP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
o={'status':'FILE_METADATA_ONLY','one_second_science_rows_accessed':False,'daily_rate_summaries_accessed':False,'success':False}
def q(adql):
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':adql}).encode()
 req=urllib.request.Request(TAP,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-AMS02-Inventory/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
try:
 a=q('SELECT COUNT(*) AS n, MIN("time") AS tmin, MAX(end_time) AS tmax FROM ams02rates')
 b=q('SELECT TOP 3 record_id,"time",end_time,exposure,data_file FROM ams02rates ORDER BY "time" ASC')
 c=q('SELECT TOP 3 record_id,"time",end_time,exposure,data_file FROM ams02rates ORDER BY "time" DESC')
 def rows(t): return [{str(n):str(r[n]) for n in t.colnames} for r in t]
 o['coverage_summary']=rows(a); o['earliest_files']=rows(b); o['latest_files']=rows(c); o['success']=True; o['decision']='AMS02_FILE_INVENTORY_ACCESSIBLE'
except Exception as e:
 o['error']=type(e).__name__+': '+str(e); o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENCE_DECISION'
OUT.write_text(json.dumps(o,indent=2)+'\n'); print(json.dumps(o,indent=2))

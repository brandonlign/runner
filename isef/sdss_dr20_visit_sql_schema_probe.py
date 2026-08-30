#!/usr/bin/env python3
"""Schema-only probe for a SQL fallback to DR20 visit-level data.
Does not query source rows or identities.
"""
from pathlib import Path
import json, urllib.parse, urllib.request
OUT=Path('results/sdss_dr20_visit_sql_schema_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'
queries=[
    "SELECT TOP 200 name FROM sys.tables WHERE name LIKE '%visit%' ORDER BY name",
    "SELECT TOP 200 table_name,column_name FROM information_schema.columns WHERE column_name IN ('sdss_id','xcsao_v_rad','xcsao_e_v_rad','telescope','zwarning_flags') ORDER BY table_name,column_name"
]
out={'success':False,'status':'SCHEMA_ONLY','source_rows_accessed':False,'queries':[]}
try:
    for q in queries:
        url=BASE+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'})
        req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-SQL-SchemaProbe/1.0'})
        with urllib.request.urlopen(req,timeout=120) as r:
            raw=r.read().decode('utf-8','replace')
        out['queries'].append({'query':q,'response_prefix':raw[:20000]})
    out['success']=True; out['decision']='SQL_SCHEMA_PROBE_COMPLETE'
except Exception as e:
    out['error_type']=type(e).__name__; out['error']=str(e)[:1000]
OUT.write_text(json.dumps(out,indent=2,sort_keys=True))
print(OUT.read_text())

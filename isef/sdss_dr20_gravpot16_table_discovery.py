#!/usr/bin/env python3
"""Schema-only discovery of DR20 GravPot16-like SkyServer tables; no source rows."""
from pathlib import Path
import json, urllib.parse, urllib.request
OUT=Path('results/sdss_dr20_gravpot16_table_discovery.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'
queries=[
 "SELECT TOP 100 name FROM sys.tables WHERE LOWER(name) LIKE '%gravpot%' ORDER BY name",
 "SELECT TOP 200 table_name FROM information_schema.tables WHERE LOWER(table_name) LIKE '%gravpot%' ORDER BY table_name"
]
out={'success':False,'status':'SCHEMA_ONLY','source_rows_accessed':False,'responses':[]}
try:
 for q in queries:
  url=BASE+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-GravPot16-Discovery/1.0'})
  with urllib.request.urlopen(req,timeout=120) as r: obj=json.loads(r.read().decode('utf-8','replace'))
  out['responses'].append({'query':q,'response':obj})
 names=[]
 for block in out['responses']:
  for t in block['response']:
   if isinstance(t,dict) and t.get('TableName')=='Table1':
    for row in t.get('Rows',[]): names.extend([str(v) for v in row.values() if v is not None])
 out['discovered_names']=sorted(set(names)); out['success']=True; out['decision']='GRAVPOT16_TABLE_NAMES_DISCOVERED'
except Exception as e:
 out['error_type']=type(e).__name__; out['error']=str(e)[:1000]
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)); print(OUT.read_text())

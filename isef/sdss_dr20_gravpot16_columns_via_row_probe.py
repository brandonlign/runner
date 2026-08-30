#!/usr/bin/env python3
"""Discover GravPot16 columns via one arbitrary table row, emitting names only.
This is not a candidate query: no values, IDs, coordinates, or row contents are retained/emitted.
"""
from pathlib import Path
import json, urllib.parse, urllib.request
OUT=Path('results/sdss_dr20_gravpot16_columns_via_row_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'
q='SELECT TOP 1 * FROM GravPot16'
out={'success':False,'status':'COLUMN_NAMES_ONLY','candidate_rows_accessed':False,'arbitrary_schema_row_accessed':False}
try:
 url=BASE+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-GravPot16-Columns/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r: obj=json.loads(r.read().decode('utf-8','replace'))
 cols=[]; had=False
 for t in obj:
  if isinstance(t,dict) and t.get('TableName')=='Table1':
   rows=t.get('Rows',[])
   if rows:
    had=True; cols=sorted(str(k) for k in rows[0].keys())
 out['arbitrary_schema_row_accessed']=had; out['columns']=cols
 low=' '.join(cols).lower(); keys=['energy','etot','e_tot','escape','unbound','bound','jacobi','ecc','apo','peri','lz','v_tot','velocity','prob']
 out['collision_keywords_present']={k:(k in low) for k in keys}; out['success']=True; out['decision']='GRAVPOT16_COLUMNS_RECOVERED' if cols else 'GRAVPOT16_ROW_QUERY_RETURNED_NO_COLUMNS'
except Exception as e:
 out['error_type']=type(e).__name__; out['error']=str(e)[:500]
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)); print(OUT.read_text())

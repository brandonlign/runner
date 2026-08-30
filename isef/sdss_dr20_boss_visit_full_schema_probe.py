#!/usr/bin/env python3
"""Schema-only DR20 probe for fields needed in identity-open spectral validation.
No source rows or candidate identities are queried.
"""
from pathlib import Path
import json, urllib.parse, urllib.request
OUT=Path('results/sdss_dr20_boss_visit_full_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
SQL='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'
out={'success':False,'status':'SCHEMA_ONLY','source_rows_accessed':False}
try:
    qs={
      'visit':"SELECT column_name,data_type FROM information_schema.columns WHERE table_name='mwm_boss_allvisit' ORDER BY ordinal_position",
      'star':"SELECT column_name,data_type FROM information_schema.columns WHERE table_name='mwm_boss_allstar' ORDER BY ordinal_position",
      'lite':"SELECT column_name,data_type FROM information_schema.columns WHERE table_name='lite_all_star' ORDER BY ordinal_position"}
    result={}
    for k,q in qs.items():
        url=SQL+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'})
        req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-BOSS-Schema/1.0'})
        with urllib.request.urlopen(req,timeout=120) as r: obj=json.loads(r.read().decode('utf-8','replace'))
        tables=[x for x in obj if isinstance(x,dict) and x.get('TableName')=='Table1']
        rows=tables[0].get('Rows',[]) if tables else []
        result[k]=[str(x.get('column_name',x.get('COLUMN_NAME',''))) for x in rows]
    out['columns']=result;out['success']=True;out['decision']='POSTSURVIVOR_BOSS_SCHEMA_READY'
except Exception as e:
    out['error_type']=type(e).__name__;out['error']=str(e)[:1000];out['decision']='SCHEMA_INFRASTRUCTURE_FAILURE'
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(OUT.read_text())

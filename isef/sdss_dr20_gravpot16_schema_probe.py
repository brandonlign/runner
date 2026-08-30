#!/usr/bin/env python3
"""Schema-only audit of the DR20 GravPot16 VAC; no source rows."""
from pathlib import Path
import json, urllib.parse, urllib.request
OUT=Path('results/sdss_dr20_gravpot16_schema_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'
q="SELECT ordinal_position,column_name,data_type FROM information_schema.columns WHERE table_name='GravPot16' ORDER BY ordinal_position"
out={'success':False,'source_rows_accessed':False,'status':'SCHEMA_ONLY'}
try:
    url=BASE+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-GravPot16-Schema/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r: raw=r.read().decode('utf-8','replace')
    obj=json.loads(raw); out['response']=obj
    names=[]
    for t in obj:
        if isinstance(t,dict) and t.get('TableName')=='Table1': names=[str(x.get('column_name','')) for x in t.get('Rows',[])]
    out['columns']=names
    low=' '.join(names).lower(); keys=['energy','e_tot','escape','unbound','bound','apo','peri','ecc','jacobi','lz','v_tot','velocity','prob']
    out['collision_keywords_present']={k:(k in low) for k in keys}; out['success']=True; out['decision']='GRAVPOT16_SCHEMA_AUDITED'
except Exception as e:
    out['error_type']=type(e).__name__; out['error']=str(e)[:1000]
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)); print(OUT.read_text())

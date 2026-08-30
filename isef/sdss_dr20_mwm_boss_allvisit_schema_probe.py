#!/usr/bin/env python3
"""Schema-only probe of DR20 SkyServer mwm_boss_allvisit.
No source rows or identities are queried.
"""
from pathlib import Path
import json, urllib.parse, urllib.request
OUT=Path('results/sdss_dr20_mwm_boss_allvisit_schema_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'
q="SELECT ordinal_position,column_name,data_type FROM information_schema.columns WHERE table_name='mwm_boss_allvisit' ORDER BY ordinal_position"
out={'success':False,'status':'SCHEMA_ONLY','source_rows_accessed':False}
try:
    url=BASE+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'})
    req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-MWMBossVisit-Schema/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r: raw=r.read().decode('utf-8','replace')
    out['response']=json.loads(raw)
    text=raw.lower()
    wanted=['sdss_id','telescope','xcsao_v_rad','xcsao_e_v_rad','snr','zwarning_flags']
    out['wanted_present']={x:(x in text) for x in wanted}
    out['all_wanted_present']=all(out['wanted_present'].values())
    out['success']=True
    out['decision']='MWM_BOSS_ALLVISIT_SCHEMA_READY' if out['all_wanted_present'] else 'MWM_BOSS_ALLVISIT_SCHEMA_INCOMPLETE'
except Exception as e:
    out['error_type']=type(e).__name__; out['error']=str(e)[:1000]
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)); print(OUT.read_text())

#!/usr/bin/env python3
"""Schema-only HTTP probe of the official GravPot16 SAS directory/data model."""
from pathlib import Path
import json,re,urllib.request
OUT=Path('results/sdss_dr20_gravpot16_sas_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
urls=['https://data.sdss.org/sas/dr20/vac/mwm/orbits/','https://data.sdss.org/datamodel/files/MWM_ORBITS/','https://data.sdss.org/datamodel/files/MWM_ORBITS']
out={'success':False,'status':'SCHEMA_ONLY','source_rows_accessed':False,'pages':[]}
for url in urls:
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-GravPot16-SAS-Schema/1.0'})
  with urllib.request.urlopen(req,timeout=120) as r:raw=r.read().decode('utf-8','replace');final=r.geturl();status=r.status
  text=re.sub(r'<[^>]+>',' ',raw);text=' '.join(text.split())
  hrefs=re.findall(r'href=["\']([^"\']+)',raw,re.I)
  out['pages'].append({'url':url,'final':final,'status':status,'text_prefix':text[:30000],'hrefs':hrefs[:500]})
 except Exception as e:out['pages'].append({'url':url,'error':f'{type(e).__name__}: {e}'})
out['success']=any(p.get('status')==200 for p in out['pages']);out['decision']='GRAVPOT16_SAS_SCHEMA_PROBED'
OUT.write_text(json.dumps(out,indent=2,sort_keys=True));print(OUT.read_text())

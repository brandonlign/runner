#!/usr/bin/env python3
from pathlib import Path
import urllib.request,re,urllib.parse,json
OUT=Path('results/sdss_dr20_mwm_datamodel_path_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
ROOT='https://data.sdss.org/datamodel/files/MWM_ASTRA/V_ASTRA/'
def fetch(u):
 req=urllib.request.Request(u,headers={'User-Agent':'ISEF-SDSS-HVS/1.3'})
 with urllib.request.urlopen(req,timeout=60) as r:return r.status,r.geturl(),r.read(1000000).decode('utf-8','replace')
out={'success':True,'status':'SCHEMA_ONLY','levels':[]}
try:
 todo=[ROOT];seen=set()
 for depth in range(3):
  nxt=[]
  for u in todo:
   if u in seen:continue
   seen.add(u)
   try:
    st,f,s=fetch(u);ls=sorted(set(urllib.parse.urljoin(f,x) for x in re.findall(r'href=["\']([^"\']+)',s,re.I)))
    out['levels'].append({'url':u,'status':st,'links':[x for x in ls if 'MWM_ASTRA' in x][:300]})
    for x in ls:
     if 'MWM_ASTRA' in x and (x.endswith('/') or any(k in x.lower() for k in ['allvisit','targets','bossnet'])):nxt.append(x)
   except Exception as e:out['levels'].append({'url':u,'error':f'{type(e).__name__}: {e}'})
  todo=nxt
except Exception as e:out={'success':False,'status':'SCHEMA_ONLY','error':f'{type(e).__name__}: {e}'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))

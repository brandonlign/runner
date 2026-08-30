#!/usr/bin/env python3
from pathlib import Path
import urllib.request,re,urllib.parse,html,json
OUT=Path('results/sdss_dr20_mwm_summary_datamodel_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
ROOT='https://data.sdss.org/datamodel/files/MWM_ASTRA/V_ASTRA/summary/'
def get(u):
 req=urllib.request.Request(u,headers={'User-Agent':'ISEF-SDSS-HVS/1.4'})
 with urllib.request.urlopen(req,timeout=60) as r:return r.status,r.geturl(),r.read(2_000_000).decode('utf-8','replace')
out={'success':True,'status':'SCHEMA_ONLY','pages':[]}
try:
 st,f,s=get(ROOT);links=sorted(set(urllib.parse.urljoin(f,x) for x in re.findall(r'href=["\']([^"\']+)',s,re.I)));out['pages'].append({'url':ROOT,'links':links[:500]})
 for x in links:
  if any(k in x.lower() for k in ['mwmallvisit','mwmtargets','mwmallstar']):
   try:
    st,f,t=get(x);clean=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',t))).strip();out['pages'].append({'url':x,'status':st,'text':clean[:150000]})
   except Exception as e:out['pages'].append({'url':x,'error':f'{type(e).__name__}: {e}'})
except Exception as e:out={'success':False,'status':'SCHEMA_ONLY','error':f'{type(e).__name__}: {e}'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))

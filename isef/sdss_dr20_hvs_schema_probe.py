#!/usr/bin/env python3
"""Schema/access-only probe for an SDSS DR20 robust-unbound-star feasibility test.
Does not read catalog rows or source identities.
"""
from pathlib import Path
import json,re,urllib.request,urllib.parse
OUT=Path('results/sdss_dr20_hvs_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='https://data.sdss.org/sas/dr20/vac/mwm/orbits/'
DM='https://data.sdss.org/datamodel/files/MWM_ORBITS/'
URLS=[BASE,DM]
def get(url,n=2_000_000):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-SDSS-HVS-schema/1.0'})
 with urllib.request.urlopen(req,timeout=90) as r:return {'status':r.status,'final':r.geturl(),'type':r.headers.get('Content-Type'),'text':r.read(n).decode('utf-8','replace')}
def main():
 out={'success':True,'status':'SCHEMA_ONLY','pages':[],'links':[],'note':'No catalog rows or source identities inspected.'}
 try:
  links=[]
  for u in URLS:
   try:
    g=get(u);ls=sorted(set(urllib.parse.urljoin(g['final'],x) for x in re.findall(r'href=["\']([^"\']+)',g['text'],re.I)))
    out['pages'].append({'url':u,'status':g['status'],'final':g['final'],'content_type':g['type'],'excerpt':re.sub(r'\s+',' ',g['text'][:30000])})
    links+=ls
   except Exception as e:out['pages'].append({'url':u,'error':f'{type(e).__name__}: {e}'})
  out['links']=sorted(set(x for x in links if any(k in x.lower() for k in ['fits','parquet','csv','datamodel','orbit','gravpot','readme'])))[:300]
 except Exception as e:out={'success':False,'status':'SCHEMA_ONLY','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

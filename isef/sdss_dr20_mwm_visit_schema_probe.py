#!/usr/bin/env python3
"""Schema/access-only probe for DR20 MWM visit-level RV products. No rows."""
from pathlib import Path
import urllib.request,re,html,json,urllib.parse
OUT=Path('results/sdss_dr20_mwm_visit_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
PAGES=[
 'https://data.sdss.org/datamodel/files/MWM_ASTRA/mwmAllVisit.html',
 'https://data.sdss.org/datamodel/files/MWM_ASTRA/mwmTargets.html',
 'https://data.sdss.org/datamodel/files/ASTRA_ALL_VISIT_BOSS_NET/astraAllVisitBossNet.html',
 'https://data.sdss.org/datamodel/files/MWM_ASTRA/',
 'https://dr20.sdss.org/sas/dr20/spectro/astra/0.8.1/summary/'
]
def fetch(u):
 req=urllib.request.Request(u,headers={'User-Agent':'ISEF-SDSS-HVS-RV-schema/1.0'})
 with urllib.request.urlopen(req,timeout=60) as r:return r.status,r.geturl(),r.read(2_000_000).decode('utf-8','replace')
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()
def main():
 out={'success':True,'status':'SCHEMA_ONLY','pages':[],'product_links':[],'note':'Documentation and directory names only; no rows/source identities.'};links=[]
 for u in PAGES:
  try:
   st,final,s=fetch(u);href=sorted(set(urllib.parse.urljoin(final,x) for x in re.findall(r'href=["\']([^"\']+)',s,re.I)));links+=href
   out['pages'].append({'url':u,'status':st,'final':final,'text':clean(s)[:120000]})
  except Exception as e:out['pages'].append({'url':u,'error':f'{type(e).__name__}: {e}'})
 out['product_links']=sorted(set(x for x in links if any(k in x.lower() for k in ['allvisit','mwm','bossnet','fits','summary'])))[:500]
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

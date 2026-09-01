#!/usr/bin/env python3
"""Locate official 4XMM-DR14 observation-summary resources without inspecting sources."""
from pathlib import Path
import json,re,urllib.request
OUT=Path('results/xmm_dr14_obslist_locator.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
urls=[
 'https://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4XMM_DR14.html',
 'http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4XMM_DR14.html',
 'https://www.cosmos.esa.int/web/xmm-newton/xsa',
]
out={}
for u in urls:
 try:
  req=urllib.request.Request(u,headers={'User-Agent':'ISEF-XMM-resource-locator/1.0'})
  with urllib.request.urlopen(req,timeout=60) as r:
   raw=r.read(3_000_000); final=r.geturl(); status=r.status
  txt=raw.decode('utf-8','replace')
  hrefs=re.findall(r'''(?:href|src)=["']([^"']+)["']''',txt,re.I)
  hits=[x for x in hrefs if any(k in x.lower() for k in ('obs','4xmm','fits','csv'))]
  out[u]={'status':status,'final_url':final,'bytes':len(raw),'hits':hits[:300]}
 except Exception as e: out[u]={'error':f'{type(e).__name__}: {e}'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))

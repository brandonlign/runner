#!/usr/bin/env python3
import json,urllib.request
from pathlib import Path
U={
 '5src':'https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/5XMM_DR15cat_source_v1.0.fits.gz',
 '4full':'https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_v1.0.fits.gz'}
out={}
for k,u in U.items():
 try:
  req=urllib.request.Request(u,method='HEAD',headers={'User-Agent':'ISEF-size-probe/1.0'})
  with urllib.request.urlopen(req,timeout=30) as r:out[k]={'status':r.status,'headers':dict(r.headers)}
 except Exception as e:out[k]={'error':f'{type(e).__name__}: {e}'}
p=Path('results/xmm_catalog_file_probe.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))

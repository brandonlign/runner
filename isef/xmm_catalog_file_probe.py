#!/usr/bin/env python3
import json,urllib.request
from pathlib import Path
B='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/'
U={
 '5src':B+'5XMM_DR15cat_source_v1.0.fits.gz',
 '4full':B+'4XMM_DR14cat_v1.0.fits.gz',
 '4slim_guess1':B+'4XMM_slim_DR14cat_v1.0.fits.gz',
 '4slim_guess2':B+'4XMM_DR14cat_slim_v1.0.fits.gz',
 '4slim_guess3':B+'4XMM_DR14slim_v1.0.fits.gz'}
out={}
for k,u in U.items():
 try:
  req=urllib.request.Request(u,method='HEAD',headers={'User-Agent':'ISEF-size-probe/1.1'})
  with urllib.request.urlopen(req,timeout=30) as r:out[k]={'status':r.status,'content_length':r.headers.get('Content-Length'),'last_modified':r.headers.get('Last-Modified')}
 except Exception as e:out[k]={'error':f'{type(e).__name__}: {e}'}
p=Path('results/xmm_catalog_file_probe.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))

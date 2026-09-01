#!/usr/bin/env python3
from pathlib import Path
import json,urllib.request
O=Path('results/xmm_5xmm_slim_locator.json'); O.parent.mkdir(parents=True,exist_ok=True)
urls=[
 'https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/5XMM_DR15cat_slim_v1.0.fits.gz',
 'https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/5XMM_DR15cat_v1.0.fits.gz',
]
out={}
for u in urls:
 try:
  r=urllib.request.urlopen(urllib.request.Request(u,method='HEAD',headers={'User-Agent':'ISEF-XMM-slim-locator/1.0'}),timeout=30)
  out[u]={'status':r.status,'content_length':r.headers.get('Content-Length'),'content_type':r.headers.get('Content-Type')}
 except Exception as e: out[u]={'error':f'{type(e).__name__}: {e}'}
O.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))

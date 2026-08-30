#!/usr/bin/env python3
import json,urllib.request,concurrent.futures
from pathlib import Path
field='112053'; fn='spec-112053-60334-63050396111356292.fits'
root='https://dr20.sdss.org/sas/dr20/spectro/boss/redux/v6_2_1/spectra/daily'
# Probe documented DR20 full/lite branches; identity is already authorized open.
urls=[f'{root}/{x}/{field}/{fn}' for x in ['full','lite']]+[f'{root}/{field}/{fn}']
def one(u):
 try:
  req=urllib.request.Request(u,method='HEAD',headers={'User-Agent':'ISEF-DR20-SpecPath/1.0'})
  with urllib.request.urlopen(req,timeout=30) as r:return u,{'ok':True,'status':r.status,'length':r.headers.get('Content-Length'),'final':r.geturl()}
 except Exception as e:return u,{'ok':False,'error':type(e).__name__+': '+str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:o=dict(ex.map(one,urls.items() if False else urls))
p=Path('results/sdss_dr20_spec_url_probe.json');p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))

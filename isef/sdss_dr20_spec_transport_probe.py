#!/usr/bin/env python3
import json, subprocess, urllib.request
from pathlib import Path
fn='spec-112053-60334-63050396111356292.fits'; field='112053'
rel=f'spectro/boss/redux/v6_2_1/spectra/daily/full/{field}/{fn}'
urls=[f'https://dr20.sdss.org/sas/dr20/{rel}',f'https://data.sdss.org/sas/dr20/{rel}',f'https://data.sdss.org/sas/dr20/{rel}.gz']
o={'http':{},'rsync':{}}
for u in urls:
 try:
  req=urllib.request.Request(u,headers={'User-Agent':'ISEF-DR20-TransportProbe/1.0','Range':'bytes=0-1023'})
  with urllib.request.urlopen(req,timeout=30) as r:
   b=r.read(1024);o['http'][u]={'ok':True,'status':r.status,'length':r.headers.get('Content-Length'),'content_range':r.headers.get('Content-Range'),'magic':b[:16].hex(),'final':r.geturl()}
 except Exception as e:o['http'][u]={'ok':False,'error':type(e).__name__+': '+str(e)}
for target in [f'rsync://dtn.sdss.org/dr20/{rel}',f'rsync://dtn.sdss.org/dr20/spectro/boss/redux/v6_2_1/spectra/daily/full/{field}/']:
 try:
  p=subprocess.run(['rsync','--dry-run','-lv',target],capture_output=True,text=True,timeout=40);o['rsync'][target]={'returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-2000:]}
 except Exception as e:o['rsync'][target]={'error':type(e).__name__+': '+str(e)}
p=Path('results/sdss_dr20_spec_transport_probe.json');p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))

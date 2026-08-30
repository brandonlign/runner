#!/usr/bin/env python3
import json, subprocess, urllib.request
from pathlib import Path
fn='spec-112053-60334-63050396111356292.fits'; field='112053'
base='spectro/boss/redux/v6_2_1/spectra/daily/full'
o={'listings':{},'direct_checks':{}}
def rs(target,args=None):
 try:
  cmd=['rsync','--no-motd','-lv']+(args or [])+[target]
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=60);return {'returncode':p.returncode,'stdout':p.stdout[-12000:],'stderr':p.stderr[-3000:]}
 except Exception as e:return {'error':type(e).__name__+': '+str(e)}
for suffix in ['', '/', '/112XXX/', '/112/', '/1120/', '/11205/']:
 t=f'rsync://dtn.sdss.org/dr20/{base}{suffix}';o['listings'][t]=rs(t)
# Also list root and keep only names containing 112 for compactness.
root=f'rsync://dtn.sdss.org/dr20/{base}/'
r=rs(root); lines=(r.get('stdout') or '').splitlines();r['matching_112']=[x for x in lines if '112' in x][-500:];r['stdout_tail']=r.pop('stdout','')[-3000:];o['root_filtered']=r
# Try likely direct paths only after hierarchy listing.
variants=[f'{base}/{field}/{fn}',f'{base}/112XXX/{field}/{fn}',f'{base}/112XXX/{fn}']
for rel in variants:o['direct_checks'][rel]=rs(f'rsync://dtn.sdss.org/dr20/{rel}', ['--dry-run'])
p=Path('results/sdss_dr20_spec_transport_probe.json');p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))

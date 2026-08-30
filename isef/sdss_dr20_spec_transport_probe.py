#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
base='spectro/boss/redux/v6_2_1/spectra/daily/full/112XXX/112053'
def rs(target):
 try:
  p=subprocess.run(['rsync','--no-motd','-lv',target],capture_output=True,text=True,timeout=60);return {'returncode':p.returncode,'stdout':p.stdout[-60000:],'stderr':p.stderr[-3000:]}
 except Exception as e:return {'error':type(e).__name__+': '+str(e)}
o={}
for mjd in ['60334','60660','60665']:
 t=f'rsync://dtn.sdss.org/dr20/{base}/{mjd}/'; r=rs(t); lines=(r.get('stdout') or '').splitlines();
 # keep all listing metadata plus exact/nearby catalog-ID matches
 r['candidate_like']=[x for x in lines if '630503961' in x or 'spec-112053' in x][-300:];r['stdout_tail']=r.pop('stdout','')[-5000:];o[mjd]=r
p=Path('results/sdss_dr20_spec_transport_probe.json');p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))

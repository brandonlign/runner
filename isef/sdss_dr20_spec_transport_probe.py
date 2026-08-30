#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
field='112053'; base='spectro/boss/redux/v6_2_1/spectra/daily/full/112XXX/112053/'
def rs(target):
 try:
  p=subprocess.run(['rsync','--no-motd','-lv',target],capture_output=True,text=True,timeout=60)
  return {'returncode':p.returncode,'stdout':p.stdout[-30000:],'stderr':p.stderr[-3000:]}
 except Exception as e:return {'error':type(e).__name__+': '+str(e)}
target=f'rsync://dtn.sdss.org/dr20/{base}'
o={'target':target,'listing':rs(target)}
# isolate candidate MJDs and likely catalog-id prefix for readability
lines=(o['listing'].get('stdout') or '').splitlines()
o['candidate_lines']=[x for x in lines if any(m in x for m in ['60334','60660','60665','63050396111356292'])]
p=Path('results/sdss_dr20_spec_transport_probe.json');p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))

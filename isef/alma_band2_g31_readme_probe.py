#!/usr/bin/env python3
import json, urllib.request, re
from pathlib import Path
BASE='https://almascience.nrao.edu/almadata/sciver/G31.41Band2'
SETS={
 'X3e':f'{BASE}/X3e_spectralscan_67-75GHz/G31_MOUS_X3e_README',
 'X42':f'{BASE}/X42_spectralscan_75-84GHz/G31_MOUS_X42_README',
 'X46':f'{BASE}/X46_spectralscan_84-92GHz/G31_MOUS_X46_README',
}
OUT=Path('results/alma_band2_g31_readme_probe.json');OUT.parent.mkdir(exist_ok=True)
def get(u):
 req=urllib.request.Request(u,headers={'User-Agent':'ISEF-ALMA-B2-README/1.0'})
 with urllib.request.urlopen(req,timeout=90) as r:return r.read().decode('utf-8','replace')
o={'status':'README_ONLY','science_data_read':False,'sets':{}}
for k,u in SETS.items():
 try:
  txt=get(u)
  # README is public documentation; preserve full text plus machine-extracted likely filenames and spectral-window facts.
  filenames=sorted(set(re.findall(r'[^\s"\'<>]+\.(?:fits|image|pb|mask|model|residual|psf|tt0|tt1|txt|csv|tar|tgz)[^\s"\'<>]*',txt,re.I)))
  lines=txt.splitlines()
  interesting=[x for x in lines if re.search(r'(spw|spectral|frequency|GHz|MHz|channel|image|cube|product|fits|reference|continuum|rms|beam|baseline|sidelobe|flag|line-free|velocity|LSRK|LSR)',x,re.I)]
  o['sets'][k]={'url':u,'chars':len(txt),'full_text':txt,'filenames':filenames[:500],'interesting_lines':interesting[:500]}
 except Exception as e:o['sets'][k]={'url':u,'error':type(e).__name__+': '+str(e)}
o['success']=all('error' not in v for v in o['sets'].values())
OUT.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))

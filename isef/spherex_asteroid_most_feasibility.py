#!/usr/bin/env python3
"""Exploratory fallback feasibility probe: SPHEREx moving-object coverage.
No discovery claim; tests whether repeated spectral-image coverage is actually accessible."""
from pathlib import Path
import json
from astroquery.ipac.irsa.most import Most
OUT=Path('results/spherex_asteroid_most_feasibility.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
objects={
 'Vesta':'20000004',
 'Ceres':'20000001',
 'Pallas':'20000002',
 'Hygiea':'20000010',
}
out={'success':True,'queries':{}}
try:
 for name,obj in objects.items():
  q=Most.query_object(output_mode='Regular',obj_name=obj,obs_begin='2025-08-01',obs_end='2025-08-31',catalog='spherex')
  r=q['results']; m=q['metadata']
  rec={'n_images':len(r),'result_columns':list(r.colnames),'metadata_columns':list(m.colnames)}
  # Aggregate temporal/spectral-like metadata only; do not download images yet.
  for col in ['mjd','mjd_obs','obsdate','date_obs','wavelength','lambda','band','detector','image_url']:
   if col in r.colnames:
    vals=[str(x) for x in r[col]]
    rec[col+'_n_unique']=len(set(vals))
  out['queries'][name]=rec
except Exception as e:
 out={'success':False,'error':f'{type(e).__name__}: {e}','partial':out.get('queries',{})}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))

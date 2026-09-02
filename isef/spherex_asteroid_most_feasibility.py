#!/usr/bin/env python3
"""Exploratory fallback feasibility probe: SPHEREx moving-object coverage.
No discovery claim; tests whether repeated spectral-image coverage is actually accessible."""
from pathlib import Path
import json
from astroquery.ipac.irsa.most import Most
OUT=Path('results/spherex_asteroid_most_feasibility.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
# Try both numbered-object packed identifiers and names; MOST accepts object names/IDs but coverage can vary.
objects={
 'Vesta':['20000004','4 Vesta','Vesta'],
 'Ceres':['20000001','1 Ceres','Ceres'],
 'Pallas':['20000002','2 Pallas','Pallas'],
 'Hygiea':['20000010','10 Hygiea','Hygiea'],
}
out={'success':True,'queries':{}}
for name,aliases in objects.items():
 rec=None; errors=[]
 for obj in aliases:
  try:
   q=Most.query_object(output_mode='Regular',obj_name=obj,obs_begin='2025-08-01',obs_end='2025-08-31',catalog='spherex')
   if q is None or q.get('results') is None:
    errors.append(f'{obj}: no result payload'); continue
   r=q['results']; m=q.get('metadata')
   rec={'query_alias':obj,'n_images':len(r),'result_columns':list(r.colnames),'metadata_columns':list(m.colnames) if m is not None else []}
   for col in ['mjd','mjd_obs','obsdate','date_obs','wavelength','lambda','band','detector','image_url']:
    if col in r.colnames:
     vals=[str(x) for x in r[col]]
     rec[col+'_n_unique']=len(set(vals))
   break
  except Exception as e:
   errors.append(f'{obj}: {type(e).__name__}: {e}')
 if rec is None:
  rec={'n_images':0,'errors':errors}
  out['success']=False
 elif errors:
  rec['prior_alias_errors']=errors
 out['queries'][name]=rec
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))

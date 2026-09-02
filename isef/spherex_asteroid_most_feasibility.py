#!/usr/bin/env python3
"""Exploratory fallback feasibility probe: SPHEREx moving-object coverage.
No discovery claim; tests whether repeated spectral-image coverage is actually accessible."""
from pathlib import Path
import json
from astroquery.ipac.irsa.most import Most
OUT=Path('results/spherex_asteroid_most_feasibility.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
objects={
 'Vesta':['20000004','4 Vesta','Vesta'],
 'Ceres':['20000001','1 Ceres','Ceres'],
 'Pallas':['20000002','2 Pallas','Pallas'],
 'Hygiea':['20000010','10 Hygiea','Hygiea'],
}
# Probe month-by-month across the public mission interval; a single giant MOST request can be brittle.
months=[('2025-05-01','2025-05-31'),('2025-06-01','2025-06-30'),('2025-07-01','2025-07-31'),('2025-08-01','2025-08-31'),('2025-09-01','2025-09-30'),('2025-10-01','2025-10-31'),('2025-11-01','2025-11-30'),('2025-12-01','2025-12-31'),('2026-01-01','2026-01-31'),('2026-02-01','2026-02-28'),('2026-03-01','2026-03-31'),('2026-04-01','2026-04-30'),('2026-05-01','2026-05-31'),('2026-06-01','2026-06-30'),('2026-07-01','2026-07-31'),('2026-08-01','2026-08-31')]
out={'success':True,'queries':{}}
for name,aliases in objects.items():
 rec={'months_with_images':0,'total_images':0,'unique_mjd':set(),'unique_urls':set(),'successful_alias':None,'month_counts':{},'errors':[]}
 alias=aliases[0]
 for begin,end in months:
  q=None
  for obj in ([alias] if rec['successful_alias'] else aliases):
   try:
    qq=Most.query_object(output_mode='Regular',obj_name=obj,obs_begin=begin,obs_end=end,catalog='spherex')
    if qq is not None and qq.get('results') is not None:
     q=qq; rec['successful_alias']=obj; alias=obj; break
   except Exception as e:
    rec['errors'].append(f'{begin}:{obj}:{type(e).__name__}:{e}')
  if q is None: continue
  r=q['results']; n=len(r); rec['month_counts'][begin[:7]]=n
  if n:
   rec['months_with_images']+=1; rec['total_images']+=n
   if 'mjd_obs' in r.colnames: rec['unique_mjd'].update(str(x) for x in r['mjd_obs'])
   if 'image_url' in r.colnames: rec['unique_urls'].update(str(x) for x in r['image_url'])
 rec['unique_mjd_count']=len(rec['unique_mjd']); rec['unique_image_url_count']=len(rec['unique_urls'])
 rec['unique_mjd']=sorted(rec['unique_mjd']); rec['unique_urls']=sorted(rec['unique_urls'])[:3]
 out['queries'][name]=rec
 if rec['total_images']==0: out['success']=False
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))

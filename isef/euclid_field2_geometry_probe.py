#!/usr/bin/env python3
"""Metadata/WCS-only verification of the frozen Field-2 validation geometry.

No science pixel arrays are read.  The script activates Q2 Field 2, parses FITS
headers through the existing exact-WCS router, and selects five development-style
validation centers using the same fixed offset list and >=120 arcsec separation.
The resulting centers are candidates for the later validation run and may be
frozen before Field-2 variability is inspected.
"""
import json,math
from pathlib import Path
import euclid_field_runtime as fr
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp
OUT=Path('results/euclid_field2_geometry_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
FIELD=2;CENTER=fr.FIELD_CENTERS[FIELD]

def target_from_offset(dra_as,ddec_as):
 ra,de=CENTER;return ra+dra_as/(3600*math.cos(math.radians(de))),de+ddec_as/3600

def sep_as(a,b):return math.hypot((a[0]-b[0])*math.cos(math.radians((a[1]+b[1])/2))*3600,(a[1]-b[1])*3600)
def main():
 runtime=fr.activate_field(FIELD);gm=er.map_groups();chosen=[];rejected=[]
 for off in mp.CANDIDATE_OFFSETS:
  target=target_from_offset(*off)
  if any(sep_as(target,x['target'])<mp.MIN_SEP_AS for x in chosen):continue
  try:
   routes,diag=er.route_target(gm,target);chosen.append({'offset_arcsec':list(off),'target':target,'routes':{str(k):int(v) for k,v in routes.items()},'route_diagnostics':diag})
   if len(chosen)>=5:break
  except Exception as e:rejected.append({'offset_arcsec':list(off),'error':f'{type(e).__name__}: {e}'})
 out={'success':len(chosen)==5,'field':FIELD,'center':CENTER,'metadata_only':True,'files':runtime['files'],'selected_centers':chosen,'routing_rejections':rejected,'note':'No science pixel array or variability yield was read.'};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()

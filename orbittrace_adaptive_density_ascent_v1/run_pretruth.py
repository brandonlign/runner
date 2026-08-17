#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import sklearn

from adaptive_density_ascent_v1 import DIMENSION,H_LOGV,H_RAD,H_SOL,MAX_BASIN_FRACTION,MIN_SUPPORT,fit_ranked

YEARS=(2013,2014); BLIND=(20.0,55.0)
EXPECTED_RUNTIME={"numpy":"2.3.5","scipy":"1.17.0","sklearn":"1.8.0"}

def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p:Path,o:Any)->str:
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+"\n").encode(); p.write_bytes(raw); return hashlib.sha256(raw).hexdigest()

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--rows-2013',type=Path,required=True); ap.add_argument('--rows-2014',type=Path,required=True)
    ap.add_argument('--scientific-source',type=Path,required=True); ap.add_argument('--protocol',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    runtime={"numpy":np.__version__,"scipy":scipy.__version__,"sklearn":sklearn.__version__}; require(runtime==EXPECTED_RUNTIME,f"runtime drift {runtime}")
    allowed=("id","sol","sun_lon","ecl_lat","vg"); shas={}; summaries={}
    for year,path in ((2013,a.rows_2013),(2014,a.rows_2014)):
        rows=json.loads(path.read_text()); require(isinstance(rows,list) and rows,f"empty rows {year}")
        require(len({str(r['id']) for r in rows})==len(rows),f"duplicate IDs {year}"); require(all(int(r['year'])==year for r in rows),f"year drift {year}")
        require(all(not(BLIND[0]<=float(r['sol'])<=BLIND[1]) for r in rows),'protected row entered candidate')
        require(all('truth' not in r and 'shower' not in r for r in rows),'truth field entered candidate')
        view=[{k:r[k] for k in allowed} for r in rows]
        fams,summary=fit_ranked(view); require([int(f['rank']) for f in fams]==list(range(1,len(fams)+1)),'rank discontinuity')
        payload={"schema":"ORBITTRACE_ADAPTIVE_DENSITY_ASCENT_V1_PRETRUTH","method":"OrbitTrace Adaptive Density Ascent v1","year":year,"event_count":len(view),"family_count":len(fams),"families":fams,"structural_summary":summary,
          "configuration":{"h_sol":H_SOL,"h_rad":H_RAD,"h_logv":H_LOGV,"dimension":DIMENSION,"k_rule":"ceil(log2(n))","density":"-6*log(r_k)","parent_rule":"first_kNN_neighbor_with_higher_density","min_support":MIN_SUPPORT,"max_basin_fraction":MAX_BASIN_FRACTION,"ranking":"root_log_density+log_nearest_higher_root_distance"},
          "runtime":runtime,"scientific_source_sha256":sha(a.scientific_source),"protocol_sha256":sha(a.protocol),"detector_input_fields":list(allowed),"blind_exclusion":list(BLIND),"truth_accessed":False,"target_information_access":False,"target_region_events_accessed":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"post_result_parameter_search":False}
        shas[str(year)]=dump(a.output/f'candidate_{year}.json',payload); summaries[str(year)]=summary
    manifest={"method":"OrbitTrace Adaptive Density Ascent v1","candidate_sha256":shas,"scientific_source_sha256":sha(a.scientific_source),"protocol_sha256":sha(a.protocol),"runtime":runtime,"truth_accessed":False,"target_information_access":False,"target_region_events_accessed":False}
    msh=dump(a.output/'candidate_source_manifest.json',manifest)
    print(json.dumps({"verdict":"PASS_ADAPTIVE_DENSITY_ASCENT_V1_PRETRUTH","candidate_sha256":shas,"manifest_sha256":msh,"summaries":summaries},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())

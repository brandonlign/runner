#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import networkx as nx
import numpy as np
import scipy
import sklearn
from reciprocal_rank_community_v1 import H_SOL,H_RAD,H_LOGV,RESOLUTION,LOUVAIN_THRESHOLD,SEED,MIN_SUPPORT,fit_ranked

YEARS=(2013,2014); BLIND=(20.0,55.0)
EXPECTED_RUNTIME={"numpy":"2.3.5","scipy":"1.17.0","sklearn":"1.8.0","networkx":"3.6.1"}
def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,o):
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+"\n").encode(); Path(p).write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--rows-2013",type=Path,required=True); ap.add_argument("--rows-2014",type=Path,required=True)
    ap.add_argument("--scientific-source",type=Path,required=True); ap.add_argument("--protocol",type=Path,required=True); ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    rt={"numpy":np.__version__,"scipy":scipy.__version__,"sklearn":sklearn.__version__,"networkx":nx.__version__}; req(rt==EXPECTED_RUNTIME,f"runtime drift {rt}")
    allowed=("id","sol","sun_lon","ecl_lat","vg"); outputs={}
    for year,path in ((2013,a.rows_2013),(2014,a.rows_2014)):
        rows=json.loads(path.read_text()); req(isinstance(rows,list) and rows,f"empty {year}"); req(len({str(r['id']) for r in rows})==len(rows),f"dupe {year}")
        req(all(int(r['year'])==year for r in rows),f"year drift {year}"); req(all(not(BLIND[0]<=float(r['sol'])<=BLIND[1]) for r in rows),"protected row")
        req(all('truth' not in r and 'shower' not in r for r in rows),"truth field"); view=[{k:r[k] for k in allowed} for r in rows]
        fams,summary=fit_ranked(view); req([f['rank'] for f in fams]==list(range(1,len(fams)+1)),"rank discontinuity")
        req(summary['mutual_edge_count']>len(view),"sparse graph"); req(summary['community_count']>1 and summary['weighted_modularity']>0,"bad partition")
        payload={"schema":"ORBITTRACE_RECIPROCAL_RANK_COMMUNITY_V1_PRETRUTH","method":"OrbitTrace Reciprocal Rank Communities v1","year":year,"event_count":len(view),
            "family_count":len(fams),"families":fams,"structural_summary":summary,
            "configuration":{"h_sol":H_SOL,"h_rad":H_RAD,"h_logv":H_LOGV,"k_rule":"ceil(log2(n))","edge_admission":"mutual_kNN","edge_weight":"1/sqrt(r_ij*r_ji)","resolution":RESOLUTION,"louvain_threshold":LOUVAIN_THRESHOLD,"seed":SEED,"min_support":MIN_SUPPORT},
            "runtime":rt,"scientific_source_sha256":sha(a.scientific_source),"protocol_sha256":sha(a.protocol),"detector_input_fields":list(allowed),"blind_exclusion":list(BLIND),
            "truth_accessed":False,"target_information_access":False,"target_region_events_accessed":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"post_result_parameter_search":False}
        outputs[str(year)]=dump(a.output/f"candidate_{year}.json",payload)
    manifest={"method":"OrbitTrace Reciprocal Rank Communities v1","candidate_sha256":outputs,"scientific_source_sha256":sha(a.scientific_source),"protocol_sha256":sha(a.protocol),"runtime":rt,"truth_accessed":False,"target_information_access":False,"target_region_events_accessed":False}
    msh=dump(a.output/"candidate_source_manifest.json",manifest); print(json.dumps({"verdict":"PASS_RECIPROCAL_RANK_COMMUNITY_V1_PRETRUTH","candidates":outputs,"manifest_sha256":msh},indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())

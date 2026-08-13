#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,tempfile
from pathlib import Path
import numpy as np
import active_scan,raw_uncertainty
MIN_COMPLETE=0.95
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
def req(x,m):
    if not x: raise RuntimeError(m)
def pc(v,p): return None if not v else float(np.percentile(np.asarray(v,float),p,method='linear'))
def main():
    p=argparse.ArgumentParser()
    for n in ('quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'): p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); req(hashlib.sha256(a.quality_source.read_bytes()).hexdigest()==QUALITY_SHA,'quality source drift')
    scan=active_scan.load(a)
    with tempfile.TemporaryDirectory(prefix='orbittrace_unc_schema_') as td: raw,sources,counts=raw_uncertainty.load(Path(td))
    stats={}; gates=[]
    for y in raw_uncertainty.YEARS:
        total=len(scan[y]); joined=complete=pos3=0; vals=[[],[],[]]
        for row in scan[y]:
            sig=raw.get((y,str(row['id'])))
            if sig is None: continue
            joined+=1
            if all(v is not None and v>=0 for v in sig):
                complete+=1; pos3+=int(all(v>0 for v in sig))
                for i,v in enumerate(sig): vals[i].append(float(v))
        frac=complete/total if total else 0.0; gate=frac>=MIN_COMPLETE; gates.append(gate)
        stats[str(y)]={'active_scan_events':total,'raw_id_joined':joined,'complete_nonnegative_uncertainty':complete,'complete_fraction':frac,'complete_gate_at_least_0_95':gate,'all_three_positive_fraction_of_complete':pos3/complete if complete else 0.0,'diagnostic':{k:{'median':pc(v,50),'p90':pc(v,90),'p99':pc(v,99),'positive_fraction':sum(x>0 for x in v)/len(v) if v else 0.0} for k,v in zip(('ra_sigma','dec_sigma','vg_sigma'),vals)}}
    verdict='PASS_GMN_V31_MEASUREMENT_UNCERTAINTY_SCHEMA_V1' if len(sources)==24 and all(gates) else 'FAIL_GMN_V31_MEASUREMENT_UNCERTAINTY_SCHEMA_V1'
    out={'verdict':verdict,'scientific_role':'TARGET_EXCLUDED_TRUTH_FREE_FEASIBILITY_ONLY','years':[2022,2023],'blind_exclusion':[20.0,55.0],'minimum_complete_fraction':MIN_COMPLETE,'year_stats':stats,'raw_counts':counts,'monthly_sources':sources,'protected_uncertainty_fields_indexed':False,'labels_interpreted':False,'scientific_ranking_computed':False,'candidate_membership_changed':False,'strictly_positive_metrics_are_diagnostic_only':True,'continuation_threshold_search':False,'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_scientific_values_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    (a.output/'GMN_V31_MEASUREMENT_UNCERTAINTY_SCHEMA_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':verdict,'year_stats':stats},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())

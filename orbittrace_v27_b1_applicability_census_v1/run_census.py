#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from typing import Any

import b1_runtime as b1
from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base,require
from orbittrace_v27_background_odds_evidence_oof_ranker_v1 import augment_pretruth as v27

YEARS=(2013,2014)

def classify(msg:str)->str:
    if 'source year' in msg and 'has <4 original seeds' in msg: return 'LT4_SOURCE_SEEDS'
    if 'source year' in msg and 'has <4 screened local-field events' in msg: return 'LT4_SCREENED_LOCAL_FIELD'
    if 'target year' in msg and 'has no fixed expanded members' in msg: return 'NO_FIXED_TARGET_MEMBERS'
    if 'non-finite SonotaCo orbit' in msg: return 'NONFINITE_ORBIT'
    if 'non-finite B1 fixed-member log odds' in msg: return 'NONFINITE_LOG_ODDS'
    return 'OTHER_RUNTIME_ERROR'

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True); p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True); p.add_argument('--v22-root',type=Path,required=True); p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    meta=json.loads((a.v22_root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); membership=json.loads((a.v22_root/'family_memberships.json').read_text()); ids=list(map(str,meta['family_ids'])); expanded=membership['families']; require([str(f['family_id']) for f in expanded]==ids,'membership alignment changed'); require(meta['truth_accessed'] is False and membership['truth_accessed'] is False,'truth-bearing input')
    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
    for y in YEARS:
        require(all(not (forbidden & {str(k).lower() for k in r}) for r in raw[y]),'truth-bearing row'); require(all(not (20<=float(r['sol'])%360<=55) for r in raw[y]),'protected interval row'); require(all(all(k in r for k in v27.REQUIRED_ORBIT_FIELDS) for r in raw[y]),'missing orbit field')
    canonical=v15_application.validate_pair(YEARS,raw); runtime,support,base,_=load_support_base(p19_module=type('Shim',(),{'mult':v17.MULT})(),support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts); generators.configure_pair(YEARS,support=support,mult=v17.MULT,v6=v17.v6,v8=v17.v8,p19=p19,p20=p20); require(float(support.BLIND_LOW)==20 and float(support.BLIND_HIGH)==55,'firewall changed'); support.CORPUS=p19.CORPUS
    hard=v17.build_hard_with_v15_order(scan_by_year=canonical,support=support,base=base,runtime=runtime); s19,_=generators.build_p19_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p19=p19); s20=generators.build_p20_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p20=p20)['soft_families']; originals=hard['hard_families']+s19+s20; orig={str(f['family_id']):f for f in originals}; require(set(orig)==set(ids),'candidate universe changed')
    event_lookup={y:{str(r['id']):r for r in raw[y]} for y in YEARS}; orbit_lookup={y:{str(r['id']):v27.orbit_tuple(r) for r in raw[y]} for y in YEARS}; byexp={str(f['family_id']):f for f in expanded}
    rows=[]; counts=Counter(); family_any=0; family_all=0
    for n,fid in enumerate(ids,1):
        f=orig[fid]; eids=list(map(str,byexp[fid]['event_ids'])); oids=set(map(str,f['event_ids'])); annual=[]
        for y in YEARS:
            try:
                val,diag=v27.annual_b1_mean_log_odds(target_year=y,family=f,expanded_ids=eids,original_ids=oids,rows=raw,event_lookup=event_lookup,orbit_lookup=orbit_lookup); status='PASS'; err=None; annual.append({'year':y,'status':status,'mean_log_odds':val,**diag})
            except RuntimeError as exc:
                err=str(exc); status=classify(err); annual.append({'year':y,'status':status,'error':err})
            counts[status]+=1
        npass=sum(r['status']=='PASS' for r in annual); family_any+=int(npass>=1); family_all+=int(npass==2); rows.append({'family_id':fid,'source':byexp[fid].get('source'),'annual':annual,'pass_years':npass})
        if n%25==0 or n==len(ids): print(f'CENSUS_PROGRESS {a.comparator} {n}/{len(ids)}',flush=True)
    result={'stage':'V27_EXACT_B1_TRUTH_FREE_APPLICABILITY_CENSUS','comparator':a.comparator,'families':len(ids),'family_all_years_applicable':family_all,'family_any_year_applicable':family_any,'family_all_years_fraction':family_all/len(ids),'family_any_year_fraction':family_any/len(ids),'annual_status_counts':dict(sorted(counts.items())),'annual_total':2*len(ids),'rows':rows,'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'scientific_performance_evaluated':False}
    (a.output/f'V27_B1_APPLICABILITY_CENSUS_{a.comparator.upper()}.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())

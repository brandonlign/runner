#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

P2_SOURCE_SHA256='f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb'
P3_EVALUATOR_COMPAT_SOURCE_SHA256='f6c4c5a76b8b3f35d434aed4f1fb15035be05c40d0e0531c343ff620f3ba8185'
DSH_SOURCE_SHA256='85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a'
P13_TRANSPORT_SOURCE_SHA256='f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'
YEARS=(2023,2025)


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument('--panel',required=True,choices=('hdbscan','sugar')); p.add_argument('--core-input',required=True,type=Path); p.add_argument('--halo-pretruth',required=True,type=Path); p.add_argument('--output',required=True,type=Path); return p.parse_args()


def main()->int:
    a=parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    core=json.loads(gzip.decompress(a.core_input.read_bytes()).decode())
    halo=pickle.loads(a.halo_pretruth.read_bytes())
    require(core['panel']==a.panel and halo['panel']==a.panel,'panel mismatch')
    require(core['years']==list(YEARS) and halo['years']==list(YEARS),'year mismatch')
    require(core['blind_exclusion']==[20.0,55.0] and halo['blind_exclusion']==[20.0,55.0],'blind interval mismatch')
    require(core['competitor_cluster_values_accessed'] is False and halo['competitor_cluster_values_accessed'] is False,'comparator values entered pretruth')
    require(core['known_shower_truth_accessed'] is False and halo['known_shower_truth_accessed'] is False,'truth entered pretruth')
    require(halo.get('target_accessed') is False,'target entered P12 halo pretruth transport')
    core_families=halo['core_families']; core_order=list(map(str,halo['core_multiplicity_order']))
    require(core_order==list(map(str,core['multiplicity_order'])),'core order changed during halo transport')
    require({str(f['family_id']) for f in core_families}==set(core_order),'core family universe changed during halo transport')
    require(halo['core_pretruth_sha256']==core['core_pretruth_sha256'],'core identity hash changed during halo transport')
    compat_crossfit={'fold_count':5,'seed_floor_min_strict':0.5,'negative_tail_max':0.10,'no_known_shower_truth_used':True,'role':'generic evaluator compatibility metadata only; primary candidate is P13 immutable core'}
    compat_model={'role':'P13 primary core benchmark uses no membership model in primary discovery scoring','halo_model_pretruth_sha256':halo['model_pretruth_sha256']}
    compat_decisions={'role':'P13 primary evaluator receives immutable cores only','core_pretruth_sha256':halo['core_pretruth_sha256'],'halo_membership_pretruth_sha256':halo['halo_membership_pretruth_sha256']}
    candidate_families=json.loads(json.dumps(core_families))
    cp={
        'classification':'P3 matched-literature pretruth panel checkpoint',
        'panel':a.panel,'years':list(YEARS),'blind_exclusion':[20.0,55.0],
        'competitor_cluster_values_accessed':False,'known_shower_truth_accessed':False,
        'p2_source_sha256':P2_SOURCE_SHA256,'p3_development_source_sha256':P3_EVALUATOR_COMPAT_SOURCE_SHA256,'dsh_source_sha256':DSH_SOURCE_SHA256,
        'parameter_search':False,'new_members_can_seed_growth':False,'crossfit_model_decisions_membership_and_rank_frozen_before_truth':True,
        'exact_event_rows':{str(y):len(core['scan_by_year'][str(y)]) for y in YEARS},
        'v8_multiplicity_order':core_order,
        'v8_order_pretruth_sha256':hashlib.sha256(json.dumps(core_order,separators=(',',':')).encode()).hexdigest(),
        'p3_crossfit_pretruth':compat_crossfit,'p3_crossfit_pretruth_sha256':canonical_sha(compat_crossfit),
        'p3_model_pretruth':compat_model,'p3_model_pretruth_sha256':canonical_sha(compat_model),
        'p3_decisions_pretruth':compat_decisions,'p3_decisions_pretruth_sha256':canonical_sha(compat_decisions),
        'p3_expanded_families':candidate_families,'p3_membership_pretruth_sha256':canonical_sha(candidate_families),
        'p3_diagnostics':{
            'compatibility_role':'dormant P3 evaluator matching math applied to exact P13 immutable cores',
            'p13_core_pretruth_sha256':halo['core_pretruth_sha256'],
            'p13_halo_membership_pretruth_sha256':halo['halo_membership_pretruth_sha256'],
            'p13_drift_pretruth_sha256':halo['drift_pretruth_sha256'],
            'p13_density_pretruth_sha256':halo['density_pretruth_sha256'],
            'p13_decisions_pretruth_sha256':halo['decisions_pretruth_sha256'],
            'p13_halo_family_count':len(halo['halo_families']),
            'p13_halo_assigned_nonseed_events':halo['assigned_nonseed_events'],
            'p13_halo_proposal_events':halo['proposal_events'],
            'p13_halo_conflicted_proposal_events':halo['conflicted_proposal_events'],
            'primary_candidate_is_core_only':True,
            'halo_can_affect_primary_evaluation':False,
        },
        'p13_halo_families':halo['halo_families'],
        'p13_halo_membership_pretruth_sha256':halo['halo_membership_pretruth_sha256'],
        'p13_core_pretruth_sha256':halo['core_pretruth_sha256'],
        'p13_transport_source_sha256':P13_TRANSPORT_SOURCE_SHA256,
        'p13_primary_core_only':True,
        'p13_halo_secondary_only':True,
    }
    raw=pickle.dumps(cp,protocol=pickle.HIGHEST_PROTOCOL); a.output.write_bytes(raw); a.output.with_suffix(a.output.suffix+'.sha256').write_text(hashlib.sha256(raw).hexdigest()+'\n')
    print('P13_MATCHED_PRETRUTH_CHECKPOINT_FROZEN',a.panel,json.dumps({'core_families':len(candidate_families),'core_sha':cp['p13_core_pretruth_sha256'],'halo_sha':cp['p13_halo_membership_pretruth_sha256'],'transport_source_sha256':P13_TRANSPORT_SOURCE_SHA256,'rows':cp['exact_event_rows']},sort_keys=True),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())

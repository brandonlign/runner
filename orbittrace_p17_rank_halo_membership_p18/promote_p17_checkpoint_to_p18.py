#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

P15_RULE='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
P17_RULE='P17_FAIL_CLOSED_RECIPROCAL_SUPPORT_CLOSURE'
P18_RULE='P18_P17_RANK_LABEL_FREE_HALO_MEMBERSHIP'
P15_MATCHED_SOURCE='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P17_MATCHED_SOURCE='c0c39d1bd660efbe5e5353b5a33185428a6f60f4a3759be3acd16a15a063012a'
P16_ADAPTER_BLOB='a143d59be30a03091ae9a46ce169ff9b12280c99'


def require(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def clone(value:Any)->Any:
    return json.loads(json.dumps(value))


def p17_snapshot(cp:dict[str,Any])->dict[str,Any]:
    return {
        'architecture':cp['p17_architecture'],
        'bidirectional_reliability_threshold_changed':cp['p17_bidirectional_reliability_threshold_changed'],
        'missing_reciprocal_creates_positive_evidence':cp['p17_missing_reciprocal_creates_positive_evidence'],
        'closures':clone(cp['p17_reciprocal_closures']),
        'closure_count':cp['p17_reciprocal_closure_count'],
        'closure_sha256':cp['p17_reciprocal_closure_sha256'],
        'closure_frozen_before_truth':cp['p17_reciprocal_closure_frozen_before_truth'],
        'diagnostic_closure_count':cp['p3_diagnostics']['p17_reciprocal_closure_count'],
        'diagnostic_closure_sha256':cp['p3_diagnostics']['p17_reciprocal_closure_sha256'],
        'diagnostic_fail_closed_no_proposals':cp['p3_diagnostics']['p17_fail_closed_no_proposals'],
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()

    raw=a.input.read_bytes(); side=a.input.with_suffix(a.input.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==hashlib.sha256(raw).hexdigest(),'P18 input checkpoint sidecar mismatch')
    cp=pickle.loads(raw)
    require(cp['classification']=='P3 matched-literature pretruth panel checkpoint','P18 input checkpoint class changed')
    require(cp['panel'] in {'hdbscan','sugar'} and cp['years']==[2023,2025] and cp['blind_exclusion']==[20.0,55.0],'P18 input universe changed')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,'P18 input is not pretruth')

    require(cp.get('p14_architecture')=='P14_SUPPORT_SAFE_MULTIPLICITY_RANK','P18 primary architecture changed')
    require(cp.get('p14_rank_frozen_before_truth') is True and cp.get('p14_no_fabricated_score') is True and cp.get('p14_episode_size_128_unchanged') is True,'P18 primary rank semantics changed')
    require(cp.get('p15_architecture')==P15_RULE,'P18 input lacks exact P15 availability architecture')
    require(cp.get('p15_generated_matched_source_sha256')==P15_MATCHED_SOURCE,'P18 P15 matched source changed')
    require(cp.get('p15_min_direction_negatives_unchanged')==128 and cp.get('p15_no_padding_resampling_or_relaxation') is True,'P18 P15 support rule changed')
    require(cp.get('p15_secondary_characterization_only') is True and cp.get('p15_halo_availability_frozen_before_truth') is True,'P18 P15 halo not safely frozen')

    require(cp.get('p17_architecture')==P17_RULE,'P18 input lacks exact P17 closure architecture')
    require(cp.get('p17_bidirectional_reliability_threshold_changed') is False,'P18 input P17 threshold changed')
    require(cp.get('p17_missing_reciprocal_creates_positive_evidence') is False,'P18 input P17 created positive reciprocal evidence')
    require(cp.get('p17_reciprocal_closure_frozen_before_truth') is True,'P18 P17 closure not frozen pretruth')
    closures=cp.get('p17_reciprocal_closures')
    require(isinstance(closures,list) and cp.get('p17_reciprocal_closure_count')==len(closures),'P18 P17 closure ledger/count changed')
    require(cp.get('p17_reciprocal_closure_sha256')==canonical_sha(closures),'P18 P17 closure hash changed')
    for x in closures:
        require(x['reciprocal_reliability_available'] is False and x['reciprocal_direction_unavailable'] is True,'P18 P17 closure status invalid')
        require(x['p17_reciprocal_fail_closed'] is True and x['p9_reliable'] is False and int(x['proposal_count'])==0,'P18 P17 closure contributed evidence')
    p17_before=p17_snapshot(cp); p17_before_sha=canonical_sha(p17_before)

    core=clone(cp['p3_expanded_families'])
    halo=clone(cp['p13_halo_families'])
    require(len(core)==len(halo)>0,'P18 empty or unequal core/halo family counts')
    core_by={str(f['family_id']):f for f in core}; halo_by={str(f['family_id']):f for f in halo}
    require(len(core_by)==len(core) and len(halo_by)==len(halo),'P18 duplicate stable family ID')
    require(set(core_by)==set(halo_by),'P18 core/halo family universe differs')

    order=list(map(str,cp['v8_multiplicity_order']))
    require(set(order)==set(core_by) and len(order)==len(core_by),'P18 rank/family universe differs')
    original_order_sha=cp['v8_order_pretruth_sha256']
    require(hashlib.sha256(json.dumps(order,separators=(',',':')).encode()).hexdigest()==original_order_sha,'P18 primary order hash changed before transform')

    evaluator=[]; correspondence=[]; total_added=0
    for fid in order:
        c=core_by[fid]; h=halo_by[fid]
        cids=set(map(str,c['event_ids'])); hids=set(map(str,h['event_ids']))
        require(cids and cids<=hids,f'P18 core not subset of halo {fid}')
        added=sorted(hids-cids)
        stored=set(map(str,h.get('p2_added_event_ids',[])))
        require(stored==set(added),f'P18 stored halo additions differ from halo-core set difference {fid}')
        require(int(h.get('p2_added_event_count',len(stored)))==len(stored),f'P18 stored halo added count changed {fid}')
        row=clone(h)
        row['event_ids']=sorted(hids); row['event_count']=len(hids)
        row['p3_added_event_ids']=added; row['p3_added_event_count']=len(added)
        evaluator.append(row); total_added+=len(added)
        correspondence.append({
            'family_id':fid,
            'core_event_count':len(cids),
            'halo_event_count':len(hids),
            'added_event_count':len(added),
            'core_event_ids_sha256':canonical_sha(sorted(cids)),
            'halo_event_ids_sha256':canonical_sha(sorted(hids)),
            'added_event_ids_sha256':canonical_sha(added),
        })

    cp['p3_expanded_families']=evaluator
    cp['p3_membership_pretruth_sha256']=canonical_sha(evaluator)
    cp['p3_model_pretruth']={
        'role':'P18 compatibility metadata only: P17/P14 core controls existence/rank; evaluator-facing membership is exact frozen P17/P15/P12 halo',
        'inherited_p17_closure_sha256':p17_before['closure_sha256'],
        'p16_semantic_adapter_blob':P16_ADAPTER_BLOB,
    }
    cp['p3_model_pretruth_sha256']=canonical_sha(cp['p3_model_pretruth'])
    cp['p3_decisions_pretruth']={
        'role':'P18 output architecture only; no new member decision is computed',
        'core_pretruth_sha256':cp['p13_core_pretruth_sha256'],
        'halo_membership_pretruth_sha256':cp['p13_halo_membership_pretruth_sha256'],
        'reported_membership_pretruth_sha256':cp['p3_membership_pretruth_sha256'],
        'p17_closure_snapshot_sha256':p17_before_sha,
    }
    cp['p3_decisions_pretruth_sha256']=canonical_sha(cp['p3_decisions_pretruth'])
    cp['p3_diagnostics']['primary_candidate_is_core_only']=False
    cp['p3_diagnostics']['halo_can_affect_primary_evaluation']=True
    cp['p3_diagnostics']['family_existence_and_rank_core_only']=True
    cp['p3_diagnostics']['reported_membership_is_exact_label_free_halo']=True
    cp['p3_diagnostics']['p18_no_new_member_proposal']=True
    cp['p3_diagnostics']['p18_total_already_frozen_halo_additions']=total_added
    cp['p3_diagnostics']['p18_core_halo_correspondence_sha256']=canonical_sha(correspondence)

    cp['p18_architecture']=P18_RULE
    cp['p18_primary_candidate_for_matched_verdict']=True
    cp['p18_p17_core_only_is_diagnostic_ablation']=True
    cp['p18_family_existence_source']='immutable P17/P14 recurrent core'
    cp['p18_rank_source']='immutable P14 support-safe multiplicity total order carried through P17'
    cp['p18_reported_membership_source']='exact frozen P17/P15/P12 label-free halo'
    cp['p18_p17_matched_source_sha256']=P17_MATCHED_SOURCE
    cp['p18_p16_semantic_adapter_blob']=P16_ADAPTER_BLOB
    cp['p18_no_new_detector_score_distance_threshold_family_proposal_growth_merge_or_rank']=True
    cp['p18_new_members_can_seed_growth']=False
    cp['p18_core_order_unchanged']=True
    cp['p18_core_order_pretruth_sha256']=original_order_sha
    cp['p18_reported_membership_pretruth_sha256']=cp['p3_membership_pretruth_sha256']
    cp['p18_core_halo_correspondence']=correspondence
    cp['p18_core_halo_correspondence_sha256']=canonical_sha(correspondence)
    cp['p18_total_already_frozen_halo_additions']=total_added
    cp['p18_p17_closure_snapshot_sha256']=p17_before_sha
    cp['p18_membership_frozen_before_truth']=True
    cp['crossfit_model_decisions_membership_and_rank_frozen_before_truth']=True
    cp['new_members_can_seed_growth']=False
    cp['parameter_search']=False

    require(list(map(str,cp['v8_multiplicity_order']))==order and cp['v8_order_pretruth_sha256']==original_order_sha,'P18 changed primary rank')
    require(canonical_sha(p17_snapshot(cp))==p17_before_sha,'P18 changed P17 closure provenance')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,'P18 transform accessed comparator/truth')

    out=pickle.dumps(cp,protocol=pickle.HIGHEST_PROTOCOL)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(out)
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(hashlib.sha256(out).hexdigest()+'\n')
    print('P18_PRETRUTH_CHECKPOINT_FROZEN',cp['panel'],json.dumps({
        'families':len(order),
        'already_frozen_halo_additions':total_added,
        'core_order_sha256':original_order_sha,
        'reported_membership_sha256':cp['p18_reported_membership_pretruth_sha256'],
        'correspondence_sha256':cp['p18_core_halo_correspondence_sha256'],
        'p17_closure_count':cp['p17_reciprocal_closure_count'],
        'p17_closure_sha256':cp['p17_reciprocal_closure_sha256'],
        'p17_closure_snapshot_sha256':p17_before_sha,
    },sort_keys=True),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())

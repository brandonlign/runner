#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

P15_RULE='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
P15_SOURCE='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P16_RULE='P16_CORE_RANK_LABEL_FREE_HALO_MEMBERSHIP'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def clone(value:Any)->Any:
    return json.loads(json.dumps(value))


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()

    raw=a.input.read_bytes(); side=a.input.with_suffix(a.input.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==hashlib.sha256(raw).hexdigest(),'P16 input checkpoint sidecar mismatch')
    cp=pickle.loads(raw)
    require(cp['classification']=='P3 matched-literature pretruth panel checkpoint','P16 input checkpoint class changed')
    require(cp['panel'] in {'hdbscan','sugar'} and cp['years']==[2023,2025] and cp['blind_exclusion']==[20.0,55.0],'P16 input universe changed')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,'P16 input not pretruth')
    require(cp.get('p14_architecture')=='P14_SUPPORT_SAFE_MULTIPLICITY_RANK','P16 primary P14 architecture changed')
    require(cp.get('p14_rank_frozen_before_truth') is True and cp.get('p14_no_fabricated_score') is True and cp.get('p14_episode_size_128_unchanged') is True,'P16 primary rank semantics changed')
    require(cp.get('p15_architecture')==P15_RULE,'P16 input lacks exact P15 halo availability architecture')
    require(cp.get('p15_generated_matched_source_sha256')==P15_SOURCE,'P16 input P15 source changed')
    require(cp.get('p15_min_direction_negatives_unchanged')==128 and cp.get('p15_no_padding_resampling_or_relaxation') is True,'P16 input P15 support rule changed')
    require(cp.get('p15_secondary_characterization_only') is True and cp.get('p15_halo_availability_frozen_before_truth') is True,'P16 input P15 halo not safely frozen')

    core=clone(cp['p3_expanded_families'])
    halo=clone(cp['p13_halo_families'])
    require(len(core)==len(halo)>0,'P16 empty or unequal core/halo family counts')
    core_by={str(f['family_id']):f for f in core}; halo_by={str(f['family_id']):f for f in halo}
    require(len(core_by)==len(core) and len(halo_by)==len(halo),'P16 duplicate stable family ID')
    require(set(core_by)==set(halo_by),'P16 core/halo family universe differs')
    order=list(map(str,cp['v8_multiplicity_order']))
    require(set(order)==set(core_by) and len(order)==len(core_by),'P16 primary order/family universe differs')
    original_order_sha=cp['v8_order_pretruth_sha256']
    require(hashlib.sha256(json.dumps(order,separators=(',',':')).encode()).hexdigest()==original_order_sha,'P16 primary order hash changed before transform')

    evaluator=[]; correspondence=[]; total_added=0
    for fid in order:
        c=core_by[fid]; h=halo_by[fid]
        cids=set(map(str,c['event_ids'])); hids=set(map(str,h['event_ids']))
        require(cids and cids<=hids,f'P16 core not subset of halo {fid}')
        added=sorted(hids-cids)
        stored=set(map(str,h.get('p2_added_event_ids',[])))
        require(stored==set(added),f'P16 stored halo additions differ from halo-core set difference {fid}')
        require(int(h.get('p2_added_event_count',len(stored)))==len(stored),f'P16 stored halo added count changed {fid}')
        row=clone(h)
        row['event_ids']=sorted(hids)
        row['event_count']=len(hids)
        row['p3_added_event_ids']=added
        row['p3_added_event_count']=len(added)
        evaluator.append(row)
        total_added += len(added)
        correspondence.append({
            'family_id':fid,
            'core_event_count':len(cids),
            'halo_event_count':len(hids),
            'added_event_count':len(added),
            'core_event_ids_sha256':canonical_sha(sorted(cids)),
            'halo_event_ids_sha256':canonical_sha(sorted(hids)),
            'added_event_ids_sha256':canonical_sha(added),
        })

    # Preserve the primary order byte-for-byte. Only evaluator-facing membership
    # and compatibility metadata are changed.
    cp['p3_expanded_families']=evaluator
    cp['p3_membership_pretruth_sha256']=canonical_sha(evaluator)
    cp['p3_model_pretruth']={
        'role':'P16 compatibility metadata: family existence/rank remain P14 core-only; evaluator-facing membership is exact frozen P15/P12 label-free halo',
        'inherited_p15_halo_model_pretruth_sha256':cp['p3_diagnostics'].get('p13_halo_membership_pretruth_sha256'),
    }
    cp['p3_model_pretruth_sha256']=canonical_sha(cp['p3_model_pretruth'])
    cp['p3_decisions_pretruth']={
        'role':'P16 output architecture only; no new member decision is computed',
        'core_pretruth_sha256':cp['p13_core_pretruth_sha256'],
        'halo_membership_pretruth_sha256':cp['p13_halo_membership_pretruth_sha256'],
        'reported_membership_pretruth_sha256':cp['p3_membership_pretruth_sha256'],
    }
    cp['p3_decisions_pretruth_sha256']=canonical_sha(cp['p3_decisions_pretruth'])
    cp['p3_diagnostics']['primary_candidate_is_core_only']=False
    cp['p3_diagnostics']['halo_can_affect_primary_evaluation']=True
    cp['p3_diagnostics']['family_existence_and_rank_core_only']=True
    cp['p3_diagnostics']['reported_membership_is_exact_label_free_halo']=True
    cp['p3_diagnostics']['p16_no_new_member_proposal']=True
    cp['p3_diagnostics']['p16_total_already_frozen_halo_additions']=total_added
    cp['p3_diagnostics']['p16_core_halo_correspondence_sha256']=canonical_sha(correspondence)

    cp['p16_architecture']=P16_RULE
    cp['p16_family_existence_source']='immutable P14/P15 recurrent core'
    cp['p16_rank_source']='immutable P14 support-safe multiplicity total order'
    cp['p16_reported_membership_source']='exact frozen P15/P12 label-free halo'
    cp['p16_no_new_detector_score_threshold_or_proposal']=True
    cp['p16_new_members_can_seed_growth']=False
    cp['p16_core_order_unchanged']=True
    cp['p16_core_order_pretruth_sha256']=original_order_sha
    cp['p16_reported_membership_pretruth_sha256']=cp['p3_membership_pretruth_sha256']
    cp['p16_core_halo_correspondence']=correspondence
    cp['p16_core_halo_correspondence_sha256']=canonical_sha(correspondence)
    cp['p16_total_already_frozen_halo_additions']=total_added
    cp['p16_membership_frozen_before_truth']=True
    cp['crossfit_model_decisions_membership_and_rank_frozen_before_truth']=True
    cp['new_members_can_seed_growth']=False
    cp['parameter_search']=False

    require(list(map(str,cp['v8_multiplicity_order']))==order,'P16 changed primary order')
    require(cp['v8_order_pretruth_sha256']==original_order_sha,'P16 changed primary order hash')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,'P16 transform accessed truth/comparator')

    out=pickle.dumps(cp,protocol=pickle.HIGHEST_PROTOCOL)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(out)
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(hashlib.sha256(out).hexdigest()+'\n')
    print('P16_PRETRUTH_CHECKPOINT_FROZEN',cp['panel'],json.dumps({
        'families':len(order),
        'already_frozen_halo_additions':total_added,
        'core_order_sha256':original_order_sha,
        'reported_membership_sha256':cp['p16_reported_membership_pretruth_sha256'],
        'correspondence_sha256':cp['p16_core_halo_correspondence_sha256'],
        'p15_unavailable_directions':cp['p15_unavailable_direction_count'],
    },sort_keys=True),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())

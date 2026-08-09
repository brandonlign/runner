#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

P18_RULE='P18_P17_RANK_LABEL_FREE_HALO_MEMBERSHIP'
P17_RULE='P17_FAIL_CLOSED_RECIPROCAL_SUPPORT_CLOSURE'


def require(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def canonical_sha(v)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def checkpoint(path:Path,panel:str)->dict:
    raw=path.read_bytes(); side=path.with_suffix(path.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==hashlib.sha256(raw).hexdigest(),f'P18 checkpoint hash changed {panel}')
    cp=pickle.loads(raw)
    require(cp['panel']==panel and cp['years']==[2023,2025] and cp['blind_exclusion']==[20.0,55.0],f'P18 checkpoint universe changed {panel}')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,f'P18 checkpoint was not pretruth {panel}')
    require(cp.get('p18_architecture')==P18_RULE,f'P18 architecture missing {panel}')
    require(cp.get('p18_primary_candidate_for_matched_verdict') is True and cp.get('p18_p17_core_only_is_diagnostic_ablation') is True,f'P18 primary/ablation semantics changed {panel}')
    require(cp.get('p18_no_new_detector_score_distance_threshold_family_proposal_growth_merge_or_rank') is True,f'P18 added scientific operation {panel}')
    require(cp.get('p18_new_members_can_seed_growth') is False and cp.get('p18_core_order_unchanged') is True and cp.get('p18_membership_frozen_before_truth') is True,f'P18 freeze semantics changed {panel}')
    require(cp.get('p18_core_order_pretruth_sha256')==cp.get('v8_order_pretruth_sha256'),f'P18 primary order hash changed {panel}')
    require(cp.get('p18_reported_membership_pretruth_sha256')==cp.get('p3_membership_pretruth_sha256'),f'P18 reported membership hash changed {panel}')
    require(cp.get('p17_architecture')==P17_RULE and cp.get('p17_reciprocal_closure_frozen_before_truth') is True,f'P18 lost P17 closure {panel}')
    require(cp.get('p17_missing_reciprocal_creates_positive_evidence') is False,f'P18 P17 closure created positive evidence {panel}')
    require(cp['p3_diagnostics'].get('family_existence_and_rank_core_only') is True,f'P18 family/rank source changed {panel}')
    require(cp['p3_diagnostics'].get('reported_membership_is_exact_label_free_halo') is True,f'P18 reported membership source changed {panel}')
    require(cp['p3_diagnostics'].get('p18_no_new_member_proposal') is True,f'P18 introduced member proposal {panel}')
    require(canonical_sha(cp['p18_core_halo_correspondence'])==cp['p18_core_halo_correspondence_sha256'],f'P18 correspondence hash changed {panel}')
    return cp


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--base-p14-transport-finalizer',required=True,type=Path)
    p.add_argument('--base-p14-finalizer',required=True,type=Path)
    p.add_argument('--p13-result',required=True,type=Path)
    p.add_argument('--hdbscan-checkpoint',required=True,type=Path)
    p.add_argument('--sugar-checkpoint',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()

    subprocess.run([
        sys.executable,str(a.base_p14_transport_finalizer),
        '--base-p14-finalizer',str(a.base_p14_finalizer),
        '--p13-result',str(a.p13_result),
        '--hdbscan-checkpoint',str(a.hdbscan_checkpoint),
        '--sugar-checkpoint',str(a.sugar_checkpoint),
        '--output',str(a.output),
    ],check=True)
    out=json.loads(a.output.read_text())
    require(out['verdict'] in {'PASS_P14_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P14_MATCHED_SPARSE_SUPERIORITY_NO_GO'},'P18 inherited matched verdict changed')
    passed=out['verdict'].startswith('PASS_')
    require(bool(out['external_validation_authorized'])==passed,'P18 inherited external flag mismatch')
    require(out['target_access_authorized'] is False,'P18 matched stage authorized target')
    require(out['sparse_superiority_required_against_both_comparators_in_both_years'] is True,'P18 sparse standard changed')
    require(out['pairwise_only_no_cross_denominator_comparison'] is True and out['broad_only_does_not_authorize_external'] is True,'P18 fairness changed')

    cps={'hdbscan':checkpoint(a.hdbscan_checkpoint,'hdbscan'),'sugar':checkpoint(a.sugar_checkpoint,'sugar')}
    out['verdict']='PASS_P18_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS' if passed else 'FAIL_P18_MATCHED_SPARSE_SUPERIORITY_NO_GO'
    out['architecture']=P18_RULE
    out['primary_discovery_output']='immutable P17/P14 recurrent-core family universe and support-safe multiplicity order'
    out['reported_membership_output']='exact frozen P17/P15/P12 label-free halo for each already-discovered family'
    out['p18_primary_candidate_for_matched_verdict']=True
    out['p18_p17_core_only_is_diagnostic_ablation']=True
    out['p18_no_new_detector_score_distance_threshold_family_proposal_growth_merge_or_rank']=True
    out['p18_family_existence_and_rank_core_only']=True
    out['p18_reported_membership_exact_label_free_halo']=True
    out['p18_pretruth']={panel:{
        'core_order_sha256':cps[panel]['p18_core_order_pretruth_sha256'],
        'reported_membership_sha256':cps[panel]['p18_reported_membership_pretruth_sha256'],
        'core_halo_correspondence_sha256':cps[panel]['p18_core_halo_correspondence_sha256'],
        'already_frozen_halo_additions':cps[panel]['p18_total_already_frozen_halo_additions'],
        'p17_closure_count':cps[panel]['p17_reciprocal_closure_count'],
        'p17_closure_sha256':cps[panel]['p17_reciprocal_closure_sha256'],
        'p15_unavailable_directions':cps[panel]['p15_unavailable_direction_count'],
    } for panel in ('hdbscan','sugar')}
    for panel in ('hdbscan','sugar'):
        q=out['panels'][panel]
        if q.get('status')=='ELIGIBLE_EVALUATED':
            if 'p13_core_annual' in q:
                q['p18_reported_membership_annual']=q['p13_core_annual']
            if 'core_false_positive_burden' in q:
                q['p18_reported_membership_false_positive_burden']=q['core_false_positive_burden']
    out['external_validation_authorized']=passed
    out['target_access_authorized']=False
    out['claim_boundary']='Matched SonotaCo 2023/2025 exact-row comparison only. P18 changes only evaluator-facing reported membership from immutable P17/P14 core to immutable label-free P17 halo for the same families; family existence/rank and all inherited sparse-superiority gates are unchanged. Matched PASS authorizes only the separately frozen no-retuning external test, never target access.'
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('ORBITTRACE_P18_MATCHED_RESULT_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('ORBITTRACE_P18_MATCHED_RESULT_END')
    return 0


if __name__=='__main__':
    raise SystemExit(main())

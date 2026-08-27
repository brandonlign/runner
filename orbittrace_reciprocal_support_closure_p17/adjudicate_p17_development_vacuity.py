#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

P15_DEV_SHA='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
P13_CORE_SHA='12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c'
P12_HALO_SHA='f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(v)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--p15-artifact-only-result',required=True,type=Path); p.add_argument('--p17-patcher',required=True,type=Path); p.add_argument('--output',required=True,type=Path); a=p.parse_args()
    r=json.loads(a.p15_artifact_only_result.read_text()); s=a.p17_patcher.read_text()
    require(r['verdict']=='PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT','P17 parent artifact-only development did not pass')
    require(r['adjudication_mode']=='artifact_only_from_immutable_canonical_P12_P13','P17 parent development mode changed')
    require(r['p15_development_source_sha256']==P15_DEV_SHA,'P17 parent P15 source changed')
    require(r['fixed_min_direction_negatives']==128,'P17 parent threshold changed')
    require(r['canonical_direction_count']==452 and r['canonical_minimum_negative_count']==2197,'P17 canonical support universe changed')
    require(r['p15_unavailable_direction_count']==0 and r['p15_unavailable_directions']==[],'P17 new branch not vacuous on canonical development')
    require(r['p15_fallback_vacuous_on_development'] is True,'P17 P15 fallback not vacuous')
    require(r['p15_no_padding_resampling_or_relaxation'] is True and r['p15_secondary_characterization_only'] is True,'P17 parent science changed')
    require(r['canonical_p13_core_pretruth_sha256']==P13_CORE_SHA,'P17 canonical core changed')
    require(r['canonical_p12_membership_pretruth_sha256']==P12_HALO_SHA and r['canonical_p13_halo_pretruth_sha256']==P12_HALO_SHA,'P17 canonical halo changed')
    require(r['new_truth_query'] is False and r['matched_truth_access'] is False and r['external_data_access'] is False and r['target_information_access'] is False,'P17 parent firewall changed')

    required=(
        "P15_DEV_SHA='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'",
        'p17_unavailable_count = sum(1 for item in p15_unavailable_directions',
        'p17_reciprocal_unavailable = any(',
        'p17_reciprocal_p3_reliable = False',
        'p9_reliable = bool(direction_reliable and p17_reciprocal_p3_reliable)',
        'missing reciprocal reliability without support-unavailable proof',
        'p17_missing_reciprocal_creates_positive_evidence',
        "if 'p17_reciprocal_p3_reliable = True' in text:",
        "raise RuntimeError('P17 fabricates reciprocal positive reliability')",
    )
    for x in required: require(x in s,f'P17 patcher source invariant missing: {x}')
    # Reject an actual generated-code assignment while allowing the patcher's own
    # defensive string check that explicitly rejects such an assignment.
    require('\n            p17_reciprocal_p3_reliable = True\n' not in s,'P17 patcher contains a positive reciprocal assignment')

    out={
        'verdict':'PASS_P17_RECIPROCAL_SUPPORT_CLOSURE_DEVELOPMENT_VACUITY',
        'classification':'ARTIFACT_ONLY_UNREACHABLE_BRANCH_NONREGRESSION',
        'parent_p15_development_source_sha256':P15_DEV_SHA,
        'canonical_direction_count':452,
        'canonical_minimum_negative_count':2197,
        'canonical_unavailable_direction_count':0,
        'p17_reciprocal_closure_branch_vacuous_on_development':True,
        'p17_changes_p9_threshold':False,
        'p17_missing_reciprocal_creates_positive_evidence':False,
        'canonical_p13_core_pretruth_sha256':P13_CORE_SHA,
        'canonical_p12_halo_pretruth_sha256':P12_HALO_SHA,
        'fresh_development_rerun_used':False,
        'post_result_numeric_tolerance_used':False,
        'matched_comparator_access':False,
        'external_data_access':False,
        'target_information_access':False,
    }
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('P17_DEVELOPMENT_VACUITY_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('P17_DEVELOPMENT_VACUITY_END')
    return 0


if __name__=='__main__': raise SystemExit(main())

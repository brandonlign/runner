#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

PANELS=('hdbscan','sugar')
YEARS=(2023,2025)
P13_TRANSPORT_SOURCE_SHA256='f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'
ASSIGNMENT_SHA256={
    'hdbscan':{2023:'35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761',2025:'8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'},
    'sugar':{2023:'2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389',2025:'77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e'},
}
EXPECTED_COUNTS={'hdbscan':{2023:26460,2025:19658},'sugar':{2023:30414,2025:23200}}


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def canonical_sha(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def load_checkpoint(path:Path,panel:str)->dict[str,Any]:
    raw=path.read_bytes(); side=path.with_suffix(path.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==hashlib.sha256(raw).hexdigest(),f'P13 checkpoint hash mismatch {panel}')
    cp=pickle.loads(raw)
    require(cp['classification']=='P3 matched-literature pretruth panel checkpoint',f'wrong evaluator checkpoint class {panel}')
    require(cp['panel']==panel and cp['years']==list(YEARS) and cp['blind_exclusion']==[20.0,55.0],f'checkpoint universe changed {panel}')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,f'pretruth firewall failed {panel}')
    require(cp['p13_primary_core_only'] is True and cp['p13_halo_secondary_only'] is True,f'P13 core/halo role changed {panel}')
    require(cp['p3_diagnostics']['primary_candidate_is_core_only'] is True and cp['p3_diagnostics']['halo_can_affect_primary_evaluation'] is False,f'generic evaluator compatibility role changed {panel}')
    require(len(cp['p13_core_pretruth_sha256'])==64 and len(cp['p13_halo_membership_pretruth_sha256'])==64,f'P13 pretruth hashes missing {panel}')
    require(cp['p3_membership_pretruth_sha256']==canonical_sha(cp['p3_expanded_families']),f'core candidate hash changed {panel}')
    require(cp['p13_transport_source_sha256']==P13_TRANSPORT_SOURCE_SHA256,f'P12 panel transport source changed {panel}')
    return cp


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--p3-result',required=True,type=Path); p.add_argument('--hdbscan-checkpoint',required=True,type=Path); p.add_argument('--sugar-checkpoint',required=True,type=Path); p.add_argument('--output',required=True,type=Path); a=p.parse_args()
    r=json.loads(a.p3_result.read_text()); cps={'hdbscan':load_checkpoint(a.hdbscan_checkpoint,'hdbscan'),'sugar':load_checkpoint(a.sugar_checkpoint,'sugar')}
    require(r['years']==list(YEARS) and r['blind_exclusion']==[20.0,55.0],'P3 evaluator universe changed')
    require(r['pairwise_only_no_cross_denominator_comparison'] is True,'denominator mixing permitted')
    require(r['sparse_stream_superiority_required_for_promotion'] is True and r['broad_only_does_not_authorize_external'] is True,'promotion semantics changed')
    require(set(r['panels'])==set(PANELS),'P3 evaluator panel universe changed')
    panels={}; all_sparse=True
    for panel in PANELS:
        q=r['panels'][panel]; cp=cps[panel]
        eligible=q['status']=='ELIGIBLE_EVALUATED'
        if not eligible:
            all_sparse=False
            panels[panel]={'status':q['status'],'sparse_pairwise_pass':False,'broad_pairwise_pass':False,'core_pretruth_sha256':cp['p13_core_pretruth_sha256'],'halo_membership_pretruth_sha256':cp['p13_halo_membership_pretruth_sha256'],'assignment_source_sha256':ASSIGNMENT_SHA256[panel],'assignment_counts':EXPECTED_COUNTS[panel]}
            continue
        require(q['exact_event_rows']==cp['exact_event_rows'],f'exact row counts differ from checkpoint {panel}')
        require(q['p3_membership_pretruth_sha256']==cp['p3_membership_pretruth_sha256'],f'evaluated candidate differs from frozen P13 core {panel}')
        require(q['p3_diagnostics']['primary_candidate_is_core_only'] is True and q['p3_diagnostics']['halo_can_affect_primary_evaluation'] is False,f'halo entered primary evaluator {panel}')
        year_sparse={}; year_broad={}
        for year in YEARS:
            g=q['pairwise_gates'][str(year)]
            require(set(g['sparse_gates'])=={'four_to_nine_gain_ge_0_10','four_to_twentyfour_gain_ge_0_10','macro_f1_not_more_than_0_10_lower','retain_at_least_80pct_f1_gt_0_5_count'},f'sparse gate set changed {panel} {year}')
            year_sparse[str(year)]=bool(g['sparse_pass'] and all(g['sparse_gates'].values()))
            year_broad[str(year)]=bool(g['broad_pass'] and all(g['broad_gates'].values()))
        sparse=bool(q['sparse_pairwise_pass'] and all(year_sparse.values()))
        broad=bool(q['broad_pairwise_pass'] and all(year_broad.values()))
        all_sparse &= sparse
        panels[panel]={
            'status':'ELIGIBLE_EVALUATED','sparse_pairwise_pass':sparse,'broad_pairwise_pass':broad,
            'year_sparse_pass':year_sparse,'year_broad_pass':year_broad,'pairwise_gates':q['pairwise_gates'],
            'p13_core_annual':q['p3_annual'],'competitor_annual':q['competitor_annual'],
            'core_false_positive_burden':q['p3_false_positive_burden'],'competitor_false_positive_burden':q['competitor_false_positive_burden'],
            'core_pretruth_sha256':cp['p13_core_pretruth_sha256'],'halo_membership_pretruth_sha256':cp['p13_halo_membership_pretruth_sha256'],
            'halo_family_count':cp['p3_diagnostics']['p13_halo_family_count'],'halo_assigned_nonseed_events':cp['p3_diagnostics']['p13_halo_assigned_nonseed_events'],
            'assignment_source_sha256':ASSIGNMENT_SHA256[panel],'assignment_counts':EXPECTED_COUNTS[panel],
        }
    verdict='PASS_P13_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS' if all_sparse else 'FAIL_P13_MATCHED_SPARSE_SUPERIORITY_NO_GO'
    out={
        'verdict':verdict,'classification':'SPARSE_STREAM_SUPERIORITY' if all_sparse else 'NO_LITERATURE_SUPERIORITY',
        'years':list(YEARS),'blind_exclusion':[20.0,55.0],
        'primary_discovery_output':'immutable P13 recurrent core only','secondary_characterization_output':'exact transported P12 halo; cannot affect superiority',
        'sparse_superiority_required_against_both_comparators_in_both_years':True,'pairwise_only_no_cross_denominator_comparison':True,
        'broad_only_does_not_authorize_external':True,'p3_evaluator_classification':r['classification'],'p3_evaluator_sparse_stream_superiority':r['sparse_stream_superiority'],
        'panels':panels,'target_access_authorized':False,'external_validation_authorized':bool(all_sparse),
        'claim_boundary':'Matched SonotaCo 2023/2025 exact-row comparison only. P13 advances only if sparse superiority passes independently against both HDBSCAN and Sugar in both years. Halo is characterization-only. No target authorization.',
    }
    require(bool(r['sparse_stream_superiority'])==all_sparse,'P3 evaluator/P13 sparse verdict mismatch')
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('ORBITTRACE_P13_MATCHED_RESULT_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('ORBITTRACE_P13_MATCHED_RESULT_END')
    return 0


if __name__=='__main__': raise SystemExit(main())

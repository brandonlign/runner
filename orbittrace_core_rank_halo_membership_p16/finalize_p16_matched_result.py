#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

P16_RULE='P16_CORE_RANK_LABEL_FREE_HALO_MEMBERSHIP'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(v)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def checkpoint(path:Path,panel:str)->dict:
    raw=path.read_bytes(); side=path.with_suffix(path.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==hashlib.sha256(raw).hexdigest(),f'P16 checkpoint hash changed {panel}')
    cp=pickle.loads(raw)
    require(cp['panel']==panel and cp['years']==[2023,2025] and cp['blind_exclusion']==[20.0,55.0],f'P16 checkpoint universe changed {panel}')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,f'P16 checkpoint was not pretruth {panel}')
    require(cp.get('p16_architecture')==P16_RULE,f'P16 architecture missing {panel}')
    require(cp.get('p16_core_order_unchanged') is True and cp.get('p16_membership_frozen_before_truth') is True,f'P16 freeze semantics changed {panel}')
    require(cp.get('p16_no_new_detector_score_threshold_or_proposal') is True and cp.get('p16_new_members_can_seed_growth') is False,f'P16 added scientific growth {panel}')
    require(cp.get('p16_core_order_pretruth_sha256')==cp.get('v8_order_pretruth_sha256'),f'P16 primary order hash changed {panel}')
    require(cp.get('p16_reported_membership_pretruth_sha256')==cp.get('p3_membership_pretruth_sha256'),f'P16 reported membership hash changed {panel}')
    require(cp['p3_diagnostics'].get('family_existence_and_rank_core_only') is True,f'P16 family/rank source changed {panel}')
    require(cp['p3_diagnostics'].get('reported_membership_is_exact_label_free_halo') is True,f'P16 reported membership source changed {panel}')
    require(cp['p3_diagnostics'].get('p16_no_new_member_proposal') is True,f'P16 introduced member proposal {panel}')
    require(canonical_sha(cp['p16_core_halo_correspondence'])==cp['p16_core_halo_correspondence_sha256'],f'P16 correspondence hash changed {panel}')
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
    require(out['verdict'] in {'PASS_P14_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P14_MATCHED_SPARSE_SUPERIORITY_NO_GO'},'P16 inherited matched verdict changed')
    passed=out['verdict'].startswith('PASS_')
    require(bool(out['external_validation_authorized'])==passed,'P16 inherited external flag mismatch')
    require(out['target_access_authorized'] is False,'P16 matched stage authorized target')
    require(out['sparse_superiority_required_against_both_comparators_in_both_years'] is True,'P16 sparse standard changed')
    require(out['pairwise_only_no_cross_denominator_comparison'] is True and out['broad_only_does_not_authorize_external'] is True,'P16 fairness changed')
    cps={'hdbscan':checkpoint(a.hdbscan_checkpoint,'hdbscan'),'sugar':checkpoint(a.sugar_checkpoint,'sugar')}
    out['verdict']='PASS_P16_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS' if passed else 'FAIL_P16_MATCHED_SPARSE_SUPERIORITY_NO_GO'
    out['architecture']=P16_RULE
    out['primary_discovery_output']='immutable P14/P15 recurrent-core family universe and support-safe multiplicity order'
    out['reported_membership_output']='exact frozen P15/P12 label-free halo for each already-discovered family'
    out['p16_no_new_detector_score_threshold_or_member_proposal']=True
    out['p16_family_existence_and_rank_core_only']=True
    out['p16_reported_membership_exact_label_free_halo']=True
    out['p16_pretruth']={panel:{
        'core_order_sha256':cps[panel]['p16_core_order_pretruth_sha256'],
        'reported_membership_sha256':cps[panel]['p16_reported_membership_pretruth_sha256'],
        'core_halo_correspondence_sha256':cps[panel]['p16_core_halo_correspondence_sha256'],
        'already_frozen_halo_additions':cps[panel]['p16_total_already_frozen_halo_additions'],
        'p15_unavailable_directions':cps[panel]['p15_unavailable_direction_count'],
    } for panel in ('hdbscan','sugar')}
    out['external_validation_authorized']=passed
    out['target_access_authorized']=False
    out['claim_boundary']='Matched SonotaCo 2023/2025 exact-row comparison only. P16 changes only reported membership from immutable core to immutable label-free halo; family existence/rank and all inherited sparse-superiority gates are unchanged. Matched PASS authorizes only a separately frozen external test, never target access.'
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('ORBITTRACE_P16_MATCHED_RESULT_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('ORBITTRACE_P16_MATCHED_RESULT_END')
    return 0


if __name__=='__main__': raise SystemExit(main())

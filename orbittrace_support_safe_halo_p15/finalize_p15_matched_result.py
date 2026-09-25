#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

P15_SOURCE='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P15_RULE='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
PANELS=('hdbscan','sugar')


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def load_checkpoint(path:Path,panel:str)->dict:
    raw=path.read_bytes(); side=path.with_suffix(path.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==hashlib.sha256(raw).hexdigest(),f'P15 checkpoint hash mismatch {panel}')
    cp=pickle.loads(raw)
    require(cp['panel']==panel and cp['years']==[2023,2025] and cp['blind_exclusion']==[20.0,55.0],f'P15 checkpoint universe changed {panel}')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,f'P15 checkpoint was not pretruth {panel}')
    require(cp.get('p15_architecture')==P15_RULE,f'P15 architecture missing {panel}')
    require(cp.get('p15_generated_matched_source_sha256')==P15_SOURCE,f'P15 source changed {panel}')
    require(cp.get('p15_min_direction_negatives_unchanged')==128,f'P15 minimum changed {panel}')
    require(cp.get('p15_no_padding_resampling_or_relaxation') is True,f'P15 support relaxation enabled {panel}')
    require(cp.get('p15_secondary_characterization_only') is True,f'P15 halo became primary {panel}')
    require(cp.get('p15_halo_availability_frozen_before_truth') is True,f'P15 availability was not frozen before truth {panel}')
    unavailable=cp.get('p15_unavailable_directions')
    require(isinstance(unavailable,list) and cp.get('p15_unavailable_direction_count')==len(unavailable),f'P15 availability ledger changed {panel}')
    require(cp.get('p15_availability_sha256')==canonical_sha(unavailable),f'P15 availability hash changed {panel}')
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
    require(out['verdict'] in {'PASS_P14_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P14_MATCHED_SPARSE_SUPERIORITY_NO_GO'},'unexpected inherited P14 matched verdict')
    passed=out['verdict'].startswith('PASS_')
    require(bool(out['external_validation_authorized'])==passed,'P15 inherited external authorization mismatch')
    require(out['target_access_authorized'] is False,'P15 matched stage authorized target')
    require(out['sparse_superiority_required_against_both_comparators_in_both_years'] is True,'P15 sparse standard changed')
    require(out['pairwise_only_no_cross_denominator_comparison'] is True and out['broad_only_does_not_authorize_external'] is True,'P15 fairness changed')
    cps={
        'hdbscan':load_checkpoint(a.hdbscan_checkpoint,'hdbscan'),
        'sugar':load_checkpoint(a.sugar_checkpoint,'sugar'),
    }
    out['verdict']='PASS_P15_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS' if passed else 'FAIL_P15_MATCHED_SPARSE_SUPERIORITY_NO_GO'
    out['architecture']='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY_OVER_P14_PRIMARY'
    out['primary_discovery_output']='promoted P14 support-safe multiplicity-ranked recurrent core; unchanged by P15'
    out['secondary_characterization_output']='exact P12 halo where direction support >=128; exact support-poor directions unavailable and contribute zero proposals'
    out['p15_generated_matched_source_sha256']=P15_SOURCE
    out['p15_min_direction_negatives_unchanged']=128
    out['p15_no_padding_resampling_or_relaxation']=True
    out['p15_secondary_characterization_only']=True
    out['p15_pretruth_availability']={panel:{
        'unavailable_direction_count':cps[panel]['p15_unavailable_direction_count'],
        'availability_sha256':cps[panel]['p15_availability_sha256'],
        'unavailable_directions':cps[panel]['p15_unavailable_directions'],
    } for panel in PANELS}
    out['external_validation_authorized']=passed
    out['target_access_authorized']=False
    out['claim_boundary']='Matched SonotaCo 2023/2025 exact-row comparison only. P15 changes secondary halo availability only; primary P14 core/rank and all sparse-superiority gates are inherited unchanged. Matched PASS authorizes only the separately preregistered MAARSY 2020/2021 external test, never target access.'
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('ORBITTRACE_P15_MATCHED_RESULT_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('ORBITTRACE_P15_MATCHED_RESULT_END')
    return 0


if __name__=='__main__': raise SystemExit(main())

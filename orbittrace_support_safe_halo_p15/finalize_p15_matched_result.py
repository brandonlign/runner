#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

P15_MATCHED_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P15_DEV_PASS='PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--base-p14-finalizer',required=True,type=Path)
    p.add_argument('--p15-validator',required=True,type=Path)
    p.add_argument('--p13-result',required=True,type=Path)
    p.add_argument('--hdbscan-checkpoint',required=True,type=Path)
    p.add_argument('--sugar-checkpoint',required=True,type=Path)
    p.add_argument('--p15-development-verdict',required=True)
    p.add_argument('--p15-development-run',required=True,type=int)
    p.add_argument('--p15-development-artifact-id',required=True,type=int)
    p.add_argument('--p15-development-artifact-digest',required=True)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()

    require(a.p15_development_verdict==P15_DEV_PASS,'P15 matched evaluator activated without exact development PASS')
    require(a.p15_development_run>0 and a.p15_development_artifact_id>0,'P15 development provenance missing')
    require(a.p15_development_artifact_digest.startswith('sha256:') and len(a.p15_development_artifact_digest)==71,'P15 development artifact digest malformed')

    subprocess.run([sys.executable,str(a.p15_validator),'--hdbscan',str(a.hdbscan_checkpoint),'--sugar',str(a.sugar_checkpoint)],check=True)
    subprocess.run([
        sys.executable,str(a.base_p14_finalizer),
        '--p13-result',str(a.p13_result),
        '--hdbscan-checkpoint',str(a.hdbscan_checkpoint),
        '--sugar-checkpoint',str(a.sugar_checkpoint),
        '--output',str(a.output),
    ],check=True)

    out=json.loads(a.output.read_text())
    require(out['verdict'] in {'PASS_P14_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P14_MATCHED_SPARSE_SUPERIORITY_NO_GO'},'unexpected inherited P14 matched verdict')
    matched_pass=out['verdict'].startswith('PASS_')
    require(bool(out['external_validation_authorized'])==matched_pass,'P15 inherited external flag mismatch')
    require(out['target_access_authorized'] is False,'P15 matched stage authorized target')
    require(out['sparse_superiority_required_against_both_comparators_in_both_years'] is True,'P15 sparse standard changed')
    require(out['pairwise_only_no_cross_denominator_comparison'] is True and out['broad_only_does_not_authorize_external'] is True,'P15 matched fairness changed')

    cps={}
    for panel,path in (('hdbscan',a.hdbscan_checkpoint),('sugar',a.sugar_checkpoint)):
        cp=pickle.loads(path.read_bytes())
        require(cp.get('p15_generated_matched_source_sha256')==P15_MATCHED_SHA,f'P15 matched source changed {panel}')
        require(cp.get('p15_halo_availability_frozen_before_truth') is True,f'P15 halo availability not pretruth-frozen {panel}')
        require(cp.get('p15_secondary_characterization_only') is True,f'P15 halo became primary {panel}')
        cps[panel]={
            'availability_sha256':cp['p15_availability_sha256'],
            'unavailable_direction_count':cp['p15_unavailable_direction_count'],
            'unavailable_directions':cp['p15_unavailable_directions'],
        }

    out['verdict']='PASS_P15_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS' if matched_pass else 'FAIL_P15_MATCHED_SPARSE_SUPERIORITY_NO_GO'
    out['architecture']='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
    out['primary_discovery_output']='exact promoted P14 recurrent core/rank; P15 changes secondary halo availability only'
    out['secondary_characterization']='exact P12 on eligible directions; <128-negative directions add zero nonseed proposals and remain pretruth-recorded unavailable'
    out['p15_matched_halo_source_sha256']=P15_MATCHED_SHA
    out['p15_development_verdict']=a.p15_development_verdict
    out['p15_development_run']=a.p15_development_run
    out['p15_development_artifact_id']=a.p15_development_artifact_id
    out['p15_development_artifact_digest']=a.p15_development_artifact_digest
    out['p15_halo_availability_pretruth']=cps
    out['external_validation_authorized']=matched_pass
    out['target_access_authorized']=False
    out['claim_boundary']='Matched SonotaCo 2023/2025 exact-row comparison only. Sparse superiority must pass separately against both HDBSCAN and Sugar in both years. P15 halo availability is frozen pretruth and cannot alter primary core/rank or truth denominators. Matched PASS authorizes only the preregistered external validation, never target access.'
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('ORBITTRACE_P15_MATCHED_RESULT_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('ORBITTRACE_P15_MATCHED_RESULT_END')
    return 0

if __name__=='__main__': raise SystemExit(main())

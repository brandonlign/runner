#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path

P15_RULE='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
P15_PARENT='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
P15_SOURCE='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P14_COMMIT='213310dc72f691b1558171e8094002ec6b9a7b07'
P14_BLOB='dfb58023ce26583a532ea5342cde051ff288d44c'
P14_PARENT='f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'
REPAIR_AUDIT_RUN=31326543587


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate(path:Path,panel:str)->dict:
    raw=path.read_bytes(); side=path.with_suffix(path.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==hashlib.sha256(raw).hexdigest(),f'checkpoint sidecar mismatch {panel}')
    cp=pickle.loads(raw)
    require(cp['classification']=='P3 matched-literature pretruth panel checkpoint',f'checkpoint class changed {panel}')
    require(cp['panel']==panel and cp['years']==[2023,2025] and cp['blind_exclusion']==[20.0,55.0],f'checkpoint universe changed {panel}')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,f'pretruth firewall failed {panel}')
    require(cp.get('p14_architecture')=='P14_SUPPORT_SAFE_MULTIPLICITY_RANK',f'P14 primary architecture changed {panel}')
    require(cp.get('p14_source_commit')==P14_COMMIT and cp.get('p14_support_blob')==P14_BLOB,f'P14 primary source changed {panel}')
    require(cp.get('p14_rank_frozen_before_truth') is True and cp.get('p14_no_fabricated_score') is True and cp.get('p14_episode_size_128_unchanged') is True,f'P14 rank semantics changed {panel}')
    require(canonical_sha(cp['p14_support_safe_rank'])==cp['p14_support_safe_rank_sha256'],f'P14 rank hash changed {panel}')
    require(cp.get('p13_transport_parent_source_sha256')==P14_PARENT,f'P14 transport parent changed {panel}')
    require(cp.get('p13_transport_source_sha256')==P15_PARENT,f'P14 technical transport changed {panel}')
    require(cp.get('p14_p12_snm_id_transport_repair_audit_run')==REPAIR_AUDIT_RUN,f'P14 transport audit changed {panel}')
    require(cp.get('p14_p12_snm_id_transport_scientific_delta') is False,f'P14 transport became scientific {panel}')

    require(cp.get('p15_architecture')==P15_RULE,f'P15 architecture missing {panel}')
    require(cp.get('p15_parent_source_sha256')==P15_PARENT,f'P15 parent source changed {panel}')
    require(cp.get('p15_generated_matched_source_sha256')==P15_SOURCE,f'P15 matched source changed {panel}')
    require(cp.get('p15_min_direction_negatives_unchanged')==128,f'P15 negative minimum changed {panel}')
    require(cp.get('p15_no_padding_resampling_or_relaxation') is True,f'P15 support relaxation enabled {panel}')
    require(cp.get('p15_secondary_characterization_only') is True,f'P15 halo became primary {panel}')
    require(cp.get('p15_halo_availability_frozen_before_truth') is True,f'P15 availability not pretruth frozen {panel}')
    unavailable=cp.get('p15_unavailable_directions')
    require(isinstance(unavailable,list),f'P15 availability ledger missing {panel}')
    require(cp.get('p15_unavailable_direction_count')==len(unavailable),f'P15 unavailable count mismatch {panel}')
    require(cp.get('p15_availability_sha256')==canonical_sha(unavailable),f'P15 availability hash mismatch {panel}')
    for item in unavailable:
        require(set(item)=={'family_id','source_year','target_year','observed_negative_count','required_negative_count','status'},f'P15 availability schema changed {panel}')
        require(int(item['required_negative_count'])==128 and int(item['observed_negative_count'])<128,f'P15 availability support semantics changed {panel}')
        require(item['status']=='CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES',f'P15 availability status changed {panel}')
    require(cp['p3_diagnostics'].get('p15_unavailable_direction_count')==len(unavailable),f'P15 diagnostics count mismatch {panel}')
    require(cp['p3_diagnostics'].get('p15_availability_sha256')==canonical_sha(unavailable),f'P15 diagnostics hash mismatch {panel}')
    require(cp['p3_diagnostics'].get('p15_secondary_characterization_only') is True,f'P15 diagnostic role changed {panel}')
    return cp


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--hdbscan',required=True,type=Path); p.add_argument('--sugar',required=True,type=Path); a=p.parse_args()
    for panel,path in (('hdbscan',a.hdbscan),('sugar',a.sugar)):
        cp=validate(path,panel)
        print('P15_PRETRUTH_VALID',panel,'checkpoint_sha',hashlib.sha256(path.read_bytes()).hexdigest(),'unavailable_directions',cp['p15_unavailable_direction_count'],'availability_sha',cp['p15_availability_sha256'])
    print('PASS_P15_BOTH_PRETRUTH_CHECKPOINTS_VALIDATED_BEFORE_TRUTH')
    return 0


if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

P15_RULE='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
P15_PARENT_SHA='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
P15_SOURCE_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def canonical_sha(value:object)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--base-p14-transport-finalizer',required=True,type=Path)
    p.add_argument('--base-p14-finalizer',required=True,type=Path)
    p.add_argument('--base-finalizer',required=True,type=Path)
    p.add_argument('--panel',required=True,choices=('hdbscan','sugar'))
    p.add_argument('--core-input',required=True,type=Path)
    p.add_argument('--halo-pretruth',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    subprocess.run([
        sys.executable,str(a.base_p14_transport_finalizer),
        '--base-p14-finalizer',str(a.base_p14_finalizer),
        '--base-finalizer',str(a.base_finalizer),
        '--panel',a.panel,
        '--core-input',str(a.core_input),
        '--halo-pretruth',str(a.halo_pretruth),
        '--output',str(a.output),
    ],check=True)

    halo=pickle.loads(a.halo_pretruth.read_bytes())
    require(halo['panel']==a.panel,'P15 halo panel mismatch')
    require(halo['competitor_cluster_values_accessed'] is False and halo['known_shower_truth_accessed'] is False,'P15 halo firewall changed')
    require(halo.get('target_accessed') is False,'P15 halo target access')
    require(halo.get('p15_architecture')==P15_RULE,'P15 halo architecture missing')
    require(halo.get('p15_parent_source_sha256')==P15_PARENT_SHA,'P15 halo parent source changed')
    require(halo.get('p15_min_direction_negatives_unchanged')==128,'P15 128-negative requirement changed')
    require(halo.get('p15_no_padding_resampling_or_relaxation') is True,'P15 support relaxation permitted')
    require(halo.get('p15_secondary_characterization_only') is True,'P15 halo role changed')
    unavailable=halo.get('p15_unavailable_directions')
    require(isinstance(unavailable,list),'P15 availability ledger missing')
    require(int(halo.get('p15_unavailable_direction_count',-1))==len(unavailable),'P15 availability count mismatch')
    require(halo.get('p15_availability_sha256')==canonical_sha(unavailable),'P15 availability hash mismatch')
    for x in unavailable:
        require(set(x)=={'family_id','source_year','target_year','observed_negative_count','required_negative_count','status'},'P15 availability ledger schema changed')
        require(int(x['required_negative_count'])==128 and int(x['observed_negative_count'])<128,'P15 unavailable support semantics changed')
        require(x['status']=='CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES','P15 availability status changed')

    raw=a.output.read_bytes(); cp=pickle.loads(raw)
    require(cp['panel']==a.panel,'P15 checkpoint panel mismatch')
    require(cp.get('p14_architecture')=='P14_SUPPORT_SAFE_MULTIPLICITY_RANK','P15 altered primary architecture')
    require(cp.get('p14_rank_frozen_before_truth') is True,'P15 primary rank not frozen')
    require(cp.get('competitor_cluster_values_accessed') is False and cp.get('known_shower_truth_accessed') is False,'P15 checkpoint firewall changed')
    cp['p15_architecture']=P15_RULE
    cp['p15_parent_source_sha256']=P15_PARENT_SHA
    cp['p15_generated_matched_source_sha256']=P15_SOURCE_SHA
    cp['p15_min_direction_negatives_unchanged']=128
    cp['p15_unavailable_directions']=unavailable
    cp['p15_unavailable_direction_count']=len(unavailable)
    cp['p15_availability_sha256']=canonical_sha(unavailable)
    cp['p15_no_padding_resampling_or_relaxation']=True
    cp['p15_secondary_characterization_only']=True
    cp['p15_halo_availability_frozen_before_truth']=True
    cp['p3_diagnostics']['p15_unavailable_direction_count']=len(unavailable)
    cp['p3_diagnostics']['p15_availability_sha256']=cp['p15_availability_sha256']
    cp['p3_diagnostics']['p15_secondary_characterization_only']=True
    out=pickle.dumps(cp,protocol=pickle.HIGHEST_PROTOCOL)
    a.output.write_bytes(out)
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(hashlib.sha256(out).hexdigest()+'\n')
    print('P15_MATCHED_PRETRUTH_CHECKPOINT_FROZEN',a.panel,json.dumps({'unavailable_directions':len(unavailable),'availability_sha':cp['p15_availability_sha256'],'core_sha':cp['p13_core_pretruth_sha256'],'halo_sha':cp['p13_halo_membership_pretruth_sha256']},sort_keys=True),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())

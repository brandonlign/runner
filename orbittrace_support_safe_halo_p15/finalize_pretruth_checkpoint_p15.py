#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

P15_PARENT_SHA='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
P15_MATCHED_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P15_ARCH='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--base-transport-finalizer',required=True,type=Path)
    p.add_argument('--base-p14-finalizer',required=True,type=Path)
    p.add_argument('--base-finalizer',required=True,type=Path)
    p.add_argument('--panel',required=True,choices=('hdbscan','sugar'))
    p.add_argument('--core-input',required=True,type=Path)
    p.add_argument('--halo-pretruth',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()

    subprocess.run([
        sys.executable,str(a.base_transport_finalizer),
        '--base-p14-finalizer',str(a.base_p14_finalizer),
        '--base-finalizer',str(a.base_finalizer),
        '--panel',a.panel,
        '--core-input',str(a.core_input),
        '--halo-pretruth',str(a.halo_pretruth),
        '--output',str(a.output),
    ],check=True)

    halo=pickle.loads(a.halo_pretruth.read_bytes())
    require(halo['classification']=='P13 exact-P12 matched-panel pretruth halo transport','P15 halo checkpoint class changed')
    require(halo['panel']==a.panel,'P15 halo panel changed')
    require(halo.get('p15_architecture')==P15_ARCH,'P15 architecture missing from halo')
    require(halo.get('p15_parent_source_sha256')==P15_PARENT_SHA,'P15 matched parent source changed')
    require(halo.get('p15_min_direction_negatives_unchanged')==128,'P15 128-negative rule changed')
    require(halo.get('p15_no_padding_resampling_or_relaxation') is True,'P15 relaxation enabled')
    require(halo.get('p15_secondary_characterization_only') is True,'P15 halo became primary')
    ledger=halo.get('p15_unavailable_directions')
    require(isinstance(ledger,list),'P15 availability ledger missing')
    require(halo.get('p15_unavailable_direction_count')==len(ledger),'P15 availability count mismatch')
    require(halo.get('p15_availability_sha256')==canonical_sha(ledger),'P15 availability hash mismatch')
    for row in ledger:
        require(row.get('status')=='CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES','P15 availability status changed')
        require(int(row.get('required_negative_count'))==128,'P15 availability required count changed')
        require(int(row.get('observed_negative_count'))<128,'P15 unavailable direction is actually eligible')

    raw=a.output.read_bytes(); cp=pickle.loads(raw)
    require(cp['panel']==a.panel,'P15 final checkpoint panel mismatch')
    require(cp.get('p13_transport_source_sha256')==P15_PARENT_SHA,'P15 parent transport checkpoint provenance changed')
    require(cp.get('p14_p12_snm_id_transport_scientific_delta') is False,'P14 technical transport became scientific')
    require(cp.get('p14_rank_frozen_before_truth') is True,'P14/P15 core rank not pretruth frozen')
    require(cp.get('competitor_cluster_values_accessed') is False,'competitor values entered P15 finalizer')
    require(cp.get('known_shower_truth_accessed') is False,'truth entered P15 finalizer')

    cp['p15_architecture']=P15_ARCH
    cp['p15_parent_source_sha256']=P15_PARENT_SHA
    cp['p15_halo_source_sha256']=P15_MATCHED_SHA
    cp['p15_min_direction_negatives_unchanged']=128
    cp['p15_unavailable_directions']=ledger
    cp['p15_unavailable_direction_count']=len(ledger)
    cp['p15_availability_sha256']=canonical_sha(ledger)
    cp['p15_no_padding_resampling_or_relaxation']=True
    cp['p15_secondary_characterization_only']=True
    cp['p15_matched_pretruth_frozen_before_truth']=True
    cp['p15_scientific_scope']='secondary halo availability only; unavailable <128-negative directions add zero nonseed proposals; primary P14 core/rank unchanged'

    out=pickle.dumps(cp,protocol=pickle.HIGHEST_PROTOCOL)
    a.output.write_bytes(out)
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(hashlib.sha256(out).hexdigest()+'\n')
    print('P15_MATCHED_PRETRUTH_CHECKPOINT_FROZEN',a.panel,hashlib.sha256(out).hexdigest(),'unavailable',len(ledger),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())

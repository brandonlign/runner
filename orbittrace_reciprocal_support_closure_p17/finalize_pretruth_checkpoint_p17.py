#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

P17_RULE='P17_FAIL_CLOSED_RECIPROCAL_SUPPORT_CLOSURE'
P15_SOURCE='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(v)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--base-p15-finalizer',required=True,type=Path)
    p.add_argument('--base-p14-transport-finalizer',required=True,type=Path)
    p.add_argument('--base-p14-finalizer',required=True,type=Path)
    p.add_argument('--base-finalizer',required=True,type=Path)
    p.add_argument('--panel',required=True,choices=('hdbscan','sugar'))
    p.add_argument('--core-input',required=True,type=Path)
    p.add_argument('--halo-pretruth',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()

    subprocess.run([
        sys.executable,str(a.base_p15_finalizer),
        '--base-p14-transport-finalizer',str(a.base_p14_transport_finalizer),
        '--base-p14-finalizer',str(a.base_p14_finalizer),
        '--base-finalizer',str(a.base_finalizer),
        '--panel',a.panel,'--core-input',str(a.core_input),
        '--halo-pretruth',str(a.halo_pretruth),'--output',str(a.output),
    ],check=True)

    halo=pickle.loads(a.halo_pretruth.read_bytes())
    require(halo['panel']==a.panel,'P17 halo panel mismatch')
    require(halo.get('p15_architecture')=='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY','P17 lost P15 availability base')
    require(halo.get('p17_architecture')==P17_RULE,'P17 halo architecture missing')
    require(halo.get('p17_bidirectional_reliability_threshold_changed') is False,'P17 changed P9 threshold')
    require(halo.get('p17_missing_reciprocal_creates_positive_evidence') is False,'P17 creates positive reciprocal evidence')
    closures=halo.get('p17_reciprocal_closures')
    require(isinstance(closures,list),'P17 closure ledger missing')
    require(halo.get('p17_reciprocal_closure_count')==len(closures),'P17 closure count mismatch')
    require(halo.get('p17_reciprocal_closure_sha256')==canonical_sha(closures),'P17 closure hash mismatch')
    for x in closures:
        require(x['reciprocal_reliability_available'] is False,'P17 closure has reciprocal reliability')
        require(x['reciprocal_direction_unavailable'] is True,'P17 closure missing unavailable proof')
        require(x['p9_reliable'] is False and int(x['proposal_count'])==0,'P17 closure contributed proposal')

    cp=pickle.loads(a.output.read_bytes())
    require(cp['panel']==a.panel,'P17 checkpoint panel mismatch')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,'P17 checkpoint firewall changed')
    cp['p17_architecture']=P17_RULE
    cp['p17_parent_p15_matched_source_sha256']=P15_SOURCE
    cp['p17_bidirectional_reliability_threshold_changed']=False
    cp['p17_missing_reciprocal_creates_positive_evidence']=False
    cp['p17_reciprocal_closures']=closures
    cp['p17_reciprocal_closure_count']=len(closures)
    cp['p17_reciprocal_closure_sha256']=canonical_sha(closures)
    cp['p17_reciprocal_closure_frozen_before_truth']=True
    cp['p3_diagnostics']['p17_reciprocal_closure_count']=len(closures)
    cp['p3_diagnostics']['p17_reciprocal_closure_sha256']=cp['p17_reciprocal_closure_sha256']
    cp['p3_diagnostics']['p17_fail_closed_no_proposals']=True
    out=pickle.dumps(cp,protocol=pickle.HIGHEST_PROTOCOL)
    a.output.write_bytes(out)
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(hashlib.sha256(out).hexdigest()+'\n')
    print('P17_PRETRUTH_CHECKPOINT_FROZEN',a.panel,json.dumps({'closures':len(closures),'closure_sha':cp['p17_reciprocal_closure_sha256'],'core_sha':cp['p13_core_pretruth_sha256'],'halo_sha':cp['p13_halo_membership_pretruth_sha256']},sort_keys=True))
    return 0


if __name__=='__main__': raise SystemExit(main())

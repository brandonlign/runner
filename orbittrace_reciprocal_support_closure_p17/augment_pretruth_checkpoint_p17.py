#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path

RULE='P17_FAIL_CLOSED_RECIPROCAL_SUPPORT_CLOSURE'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(v)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--checkpoint',required=True,type=Path); p.add_argument('--halo-pretruth',required=True,type=Path); a=p.parse_args()
    raw=a.checkpoint.read_bytes(); side=a.checkpoint.with_suffix(a.checkpoint.suffix+'.sha256')
    require(side.exists() and side.read_text().strip()==hashlib.sha256(raw).hexdigest(),'P17 parent checkpoint hash mismatch')
    cp=pickle.loads(raw); halo=pickle.loads(a.halo_pretruth.read_bytes())
    require(cp['panel']==halo['panel'],'P17 panel mismatch')
    require(cp['years']==[2023,2025] and cp['blind_exclusion']==[20.0,55.0],'P17 universe changed')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,'P17 checkpoint not pretruth')
    require(cp.get('p15_architecture')=='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY','P17 parent checkpoint lacks P15')
    require(halo.get('p17_architecture')==RULE,'P17 halo architecture missing')
    require(halo.get('p17_bidirectional_reliability_threshold_changed') is False,'P17 changed P9 threshold')
    require(halo.get('p17_missing_reciprocal_creates_positive_evidence') is False,'P17 created reciprocal evidence')
    closures=halo.get('p17_reciprocal_closures'); require(isinstance(closures,list),'P17 closure ledger missing')
    require(halo.get('p17_reciprocal_closure_count')==len(closures),'P17 closure count mismatch')
    require(halo.get('p17_reciprocal_closure_sha256')==canonical_sha(closures),'P17 closure hash mismatch')
    for x in closures:
        require(x['reciprocal_reliability_available'] is False and x['reciprocal_direction_unavailable'] is True,'P17 closure status invalid')
        require(x['p9_reliable'] is False and int(x['proposal_count'])==0,'P17 closure contributed proposal')
    cp['p17_architecture']=RULE
    cp['p17_bidirectional_reliability_threshold_changed']=False
    cp['p17_missing_reciprocal_creates_positive_evidence']=False
    cp['p17_reciprocal_closures']=closures
    cp['p17_reciprocal_closure_count']=len(closures)
    cp['p17_reciprocal_closure_sha256']=canonical_sha(closures)
    cp['p17_reciprocal_closure_frozen_before_truth']=True
    cp['p3_diagnostics']['p17_reciprocal_closure_count']=len(closures)
    cp['p3_diagnostics']['p17_reciprocal_closure_sha256']=cp['p17_reciprocal_closure_sha256']
    cp['p3_diagnostics']['p17_fail_closed_no_proposals']=True
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,'P17 augmentation changed firewall')
    out=pickle.dumps(cp,protocol=pickle.HIGHEST_PROTOCOL); a.checkpoint.write_bytes(out); side.write_text(hashlib.sha256(out).hexdigest()+'\n')
    print('P17_CHECKPOINT_AUGMENTED',cp['panel'],json.dumps({'closures':len(closures),'closure_sha':cp['p17_reciprocal_closure_sha256'],'checkpoint_sha':hashlib.sha256(out).hexdigest()},sort_keys=True))
    return 0


if __name__=='__main__': raise SystemExit(main())

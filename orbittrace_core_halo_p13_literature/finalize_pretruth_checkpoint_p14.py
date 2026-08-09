#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path
from typing import Any

P14_COMMIT='213310dc72f691b1558171e8094002ec6b9a7b07'
P14_SUPPORT_BLOB='dfb58023ce26583a532ea5342cde051ff288d44c'
P14_DEV_ARTIFACT=9041190744
P14_DEV_DIGEST='sha256:cf0ae11a664a01d274c3b64dc1062789bc84016c00a7958fb470e564fff09f93'


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--base-finalizer',required=True,type=Path)
    p.add_argument('--panel',required=True,choices=('hdbscan','sugar'))
    p.add_argument('--core-input',required=True,type=Path)
    p.add_argument('--halo-pretruth',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    subprocess.run([sys.executable,str(a.base_finalizer),'--panel',a.panel,'--core-input',str(a.core_input),'--halo-pretruth',str(a.halo_pretruth),'--output',str(a.output)],check=True)
    core=json.loads(gzip.decompress(a.core_input.read_bytes()).decode())
    raw=a.output.read_bytes(); cp=pickle.loads(raw)
    require(core.get('architecture')=='P14_SUPPORT_SAFE_MULTIPLICITY_RANK','P14 checkpoint core architecture missing')
    require(core.get('p14_source_commit')==P14_COMMIT and core.get('p14_support_blob')==P14_SUPPORT_BLOB,'P14 checkpoint source identity changed')
    rank=core.get('p14_support_safe_rank'); require(isinstance(rank,dict),'P14 rank audit missing')
    require(int(rank['episode_size'])==128,'P14 checkpoint episode size changed')
    require(int(rank['families_scored'])+int(rank['families_unscorable'])==int(rank['families_requested']),'P14 checkpoint rank accounting incomplete')
    require(rank['fabricated_scores'] is False and rank['episode_size_relaxed'] is False,'P14 checkpoint fail-closed rule changed')
    unscorable=list(rank['unscorable_families']); require([str(x['family_id']) for x in unscorable]==sorted(str(x['family_id']) for x in unscorable),'P14 checkpoint unscorable order changed')
    cp['p14_architecture']='P14_SUPPORT_SAFE_MULTIPLICITY_RANK'
    cp['p14_source_commit']=P14_COMMIT
    cp['p14_support_blob']=P14_SUPPORT_BLOB
    cp['p14_development_artifact_id']=P14_DEV_ARTIFACT
    cp['p14_development_artifact_digest']=P14_DEV_DIGEST
    cp['p14_support_safe_rank']=rank
    cp['p14_support_safe_rank_sha256']=canonical_sha(rank)
    cp['p14_unscorable_family_count']=int(rank['families_unscorable'])
    cp['p14_scored_family_count']=int(rank['families_scored'])
    cp['p14_rank_frozen_before_truth']=True
    cp['p14_no_fabricated_score']=True
    cp['p14_episode_size_128_unchanged']=True
    cp['p3_diagnostics']['p14_support_safe_rank_sha256']=cp['p14_support_safe_rank_sha256']
    cp['p3_diagnostics']['p14_unscorable_family_count']=cp['p14_unscorable_family_count']
    cp['p3_diagnostics']['p14_primary_candidate_is_core_only']=True
    out=pickle.dumps(cp,protocol=pickle.HIGHEST_PROTOCOL); a.output.write_bytes(out); a.output.with_suffix(a.output.suffix+'.sha256').write_text(hashlib.sha256(out).hexdigest()+'\n')
    print('P14_MATCHED_PRETRUTH_CHECKPOINT_FROZEN',a.panel,json.dumps({'core_families':len(cp['p3_expanded_families']),'scored':cp['p14_scored_family_count'],'unscorable':cp['p14_unscorable_family_count'],'rank_sha':cp['p14_support_safe_rank_sha256'],'core_sha':cp['p13_core_pretruth_sha256'],'halo_sha':cp['p13_halo_membership_pretruth_sha256']},sort_keys=True),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())

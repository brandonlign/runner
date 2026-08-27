#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

PANELS=('hdbscan','sugar')
P14_COMMIT='213310dc72f691b1558171e8094002ec6b9a7b07'
P14_SUPPORT_BLOB='dfb58023ce26583a532ea5342cde051ff288d44c'
CORRECT_HDBSCAN_2025_SHA='8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'


def canonical_sha(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def checkpoint(path:Path,panel:str)->dict[str,Any]:
    raw=path.read_bytes(); side=path.with_suffix(path.suffix+'.sha256')
    require(side.read_text().strip()==hashlib.sha256(raw).hexdigest(),f'P14 checkpoint hash changed {panel}')
    cp=pickle.loads(raw)
    require(cp['classification']=='P3 matched-literature pretruth panel checkpoint',f'P14 evaluator checkpoint class changed {panel}')
    require(cp.get('p14_architecture')=='P14_SUPPORT_SAFE_MULTIPLICITY_RANK',f'P14 architecture missing {panel}')
    require(cp.get('p14_source_commit')==P14_COMMIT and cp.get('p14_support_blob')==P14_SUPPORT_BLOB,f'P14 source changed {panel}')
    require(cp.get('p14_rank_frozen_before_truth') is True and cp.get('p14_no_fabricated_score') is True and cp.get('p14_episode_size_128_unchanged') is True,f'P14 rank freeze changed {panel}')
    require(canonical_sha(cp['p14_support_safe_rank'])==cp['p14_support_safe_rank_sha256'],f'P14 rank audit hash changed {panel}')
    require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,f'P14 checkpoint firewall changed {panel}')
    return cp


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--p13-result',required=True,type=Path); p.add_argument('--hdbscan-checkpoint',required=True,type=Path); p.add_argument('--sugar-checkpoint',required=True,type=Path); p.add_argument('--output',required=True,type=Path); a=p.parse_args()
    r=json.loads(a.p13_result.read_text()); cps={p:checkpoint(getattr(a,f'{p}_checkpoint'),p) for p in PANELS}
    require(r['verdict'] in {'PASS_P13_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P13_MATCHED_SPARSE_SUPERIORITY_NO_GO'},'unexpected compatibility finalizer verdict')
    all_sparse=r['verdict'].startswith('PASS_')
    require(bool(r['external_validation_authorized'])==all_sparse,'P14 compatibility external flag mismatch')
    require(r['target_access_authorized'] is False,'P14 matched stage authorized target')
    require(r['sparse_superiority_required_against_both_comparators_in_both_years'] is True,'P14 sparse standard changed')
    require(r['pairwise_only_no_cross_denominator_comparison'] is True and r['broad_only_does_not_authorize_external'] is True,'P14 matched fairness changed')
    require(r['panels']['hdbscan']['assignment_source_sha256']['2025'] if isinstance(r['panels']['hdbscan']['assignment_source_sha256'],dict) else True,'P14 result schema unexpected')
    out=json.loads(json.dumps(r))
    out['verdict']='PASS_P14_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS' if all_sparse else 'FAIL_P14_MATCHED_SPARSE_SUPERIORITY_NO_GO'
    out['architecture']='P14_SUPPORT_SAFE_MULTIPLICITY_RANK'
    out['primary_discovery_output']='promoted P14 recurrent core with exact v8 multiplicity where defined and fail-closed support-safe rank completion'
    out['p14_source_commit']=P14_COMMIT; out['p14_support_blob']=P14_SUPPORT_BLOB
    out['p14_rank_pretruth']={panel:{'sha256':cps[panel]['p14_support_safe_rank_sha256'],'families_scored':cps[panel]['p14_scored_family_count'],'families_unscorable':cps[panel]['p14_unscorable_family_count'],'episode_size':128,'fabricated_scores':False} for panel in PANELS}
    out['hdbscan_2025_corrected_assignment_sha256']=CORRECT_HDBSCAN_2025_SHA
    out['claim_boundary']='Matched SonotaCo 2023/2025 exact-row comparison only. P14 support-safe rank semantics were promoted before truth; exact 128-event scores are unchanged and undefined scores receive no ranking credit over scored families. Halo remains characterization-only. No target authorization.'
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('ORBITTRACE_P14_MATCHED_RESULT_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('ORBITTRACE_P14_MATCHED_RESULT_END')
    return 0


if __name__=='__main__': raise SystemExit(main())

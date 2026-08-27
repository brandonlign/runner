#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PARENT='f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'
TECH='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
REPAIR_AUDIT_RUN=31326543587


def canonical_sha(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--base-p14-finalizer',required=True,type=Path)
    p.add_argument('--p13-result',required=True,type=Path)
    p.add_argument('--hdbscan-checkpoint',required=True,type=Path)
    p.add_argument('--sugar-checkpoint',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    subprocess.run([
        sys.executable,str(a.base_p14_finalizer),
        '--p13-result',str(a.p13_result),
        '--hdbscan-checkpoint',str(a.hdbscan_checkpoint),
        '--sugar-checkpoint',str(a.sugar_checkpoint),
        '--output',str(a.output),
    ],check=True)
    out=json.loads(a.output.read_text())
    require(out['verdict'] in {'PASS_P14_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P14_MATCHED_SPARSE_SUPERIORITY_NO_GO'},'unexpected P14 matched verdict')
    require(out['target_access_authorized'] is False,'matched result authorized target')
    require(bool(out['external_validation_authorized'])==out['verdict'].startswith('PASS_'),'external authorization mismatch')
    require(out['sparse_superiority_required_against_both_comparators_in_both_years'] is True,'sparse standard changed')
    require(out['pairwise_only_no_cross_denominator_comparison'] is True and out['broad_only_does_not_authorize_external'] is True,'matched fairness changed')
    out['p14_p12_snm_id_transport_parent_sha256']=PARENT
    out['p14_p12_snm_id_transport_sha256']=TECH
    out['p14_p12_snm_id_transport_repair_audit_run']=REPAIR_AUDIT_RUN
    out['p14_p12_snm_id_transport_scientific_delta']=False
    out['target_access_authorized']=False
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('ORBITTRACE_P14_MATCHED_TRANSPORT_V3_RESULT_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('ORBITTRACE_P14_MATCHED_TRANSPORT_V3_RESULT_END')
    return 0


if __name__=='__main__':
    raise SystemExit(main())

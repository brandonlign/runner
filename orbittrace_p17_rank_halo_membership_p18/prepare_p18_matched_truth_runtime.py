#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

STAGE_START="progress 'STAGE EXACT POSTFREEZE SOURCES — VALUES STILL UNINDEXED'\n"
TRUTH_START="progress 'OPEN MATCHED TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE'\n"
PARENT_PREP="""python orbittrace_support_safe_rank_p14/prepare_transport_compatible_p13_finalizer.py \\
  orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py /tmp/finalize_p13_transport.py
python -m py_compile /tmp/finalize_p13_transport.py
"""
P18_PREP="""python orbittrace_p17_rank_halo_membership_p18/prepare_p18_compatible_p13_finalizer.py \\
  orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py /tmp/finalize_p18_p13.py
python -m py_compile /tmp/finalize_p18_p13.py
"""
P13_FINALIZE_START='python /tmp/finalize_p13_transport.py \\\n'


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--parent',required=True,type=Path)
    ap.add_argument('--stage-output',required=True,type=Path)
    ap.add_argument('--evaluator-output',required=True,type=Path)
    args=ap.parse_args()
    text=args.parent.read_text()
    require(text.count(STAGE_START)==1 and text.count(TRUTH_START)==1,'parent stage/truth anchors changed')
    s=text.index(STAGE_START)+len(STAGE_START)
    t=text.index(TRUTH_START)
    require(s<t,'parent stage/truth order changed')
    stage=text[s:t]
    require(stage.count(PARENT_PREP)==1,'parent P13 prep surface changed')
    stage_p18=stage.replace(PARENT_PREP,P18_PREP,1)
    restored=stage_p18.replace(P18_PREP,PARENT_PREP,1)
    require(restored==stage,'P18 staging differs outside one preregistered finalizer-prep substitution')
    stage_lines=stage_p18.splitlines()
    require(not any(line.lstrip().startswith(('python -u input/evaluator/evaluate_frozen_blindsafe.py','python input/evaluator/evaluate_frozen_blindsafe.py')) for line in stage_lines),'truth evaluator invocation leaked into staging')
    require('OrbitTrace-April' not in stage_p18 and 'target_coordinate' not in stage_p18,'target token leaked into staging')

    e0=t+len(TRUTH_START)
    require(text.count(P13_FINALIZE_START)==1,'parent P13 finalization anchor changed')
    e1=text.index(P13_FINALIZE_START,e0)
    evaluator=text[e0:e1]
    require(evaluator.count('python -u input/evaluator/evaluate_frozen_blindsafe.py')==1,'blind-safe evaluator invocation count changed')
    require('finalize_' not in evaluator,'finalizer leaked into one-time evaluator block')
    require('OrbitTrace-April' not in evaluator and 'target_coordinate' not in evaluator,'target token leaked into evaluator')
    require('--hdbscan-pretruth pretruth/checkpoints/hdbscan.pkl' in evaluator,'HDBSCAN checkpoint input changed')
    require('--sugar-pretruth pretruth/checkpoints/sugar.pkl' in evaluator,'Sugar checkpoint input changed')
    require('--output output/p3_evaluator_result.json' in evaluator,'raw evaluator output changed')

    args.stage_output.write_text(stage_p18)
    args.evaluator_output.write_text(evaluator)
    print('P18_INHERITED_STAGE_SHA256='+sha256_bytes(stage_p18.encode()))
    print('P18_ONE_TIME_EVALUATOR_BLOCK_SHA256='+sha256_bytes(evaluator.encode()))
    print('PASS_P18_MATCHED_RUNTIME_EXACT_PARENT_EXTRACTION')
    return 0


if __name__=='__main__':
    raise SystemExit(main())

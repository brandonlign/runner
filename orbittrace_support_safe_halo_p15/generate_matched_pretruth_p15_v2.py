#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
V1=HERE/'generate_matched_pretruth_p15.py'

OLD_CHILD_GUARD='''progress 'P14 PRETRUTH CHILD / PROMOTED METHOD GUARDS'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t launcher_files < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#launcher_files[@]}" -eq 1
test "${launcher_files[0]}" = 'orbittrace_support_safe_rank_p14/LAUNCH_PRETRUTH.md'
launch_marker="$(git show "$HEAD_SHA":orbittrace_support_safe_rank_p14/LAUNCH_PRETRUTH.md)"
test "$(printf '%s\\n' "$launch_marker" | sed -n '1p')" = 'LAUNCH_P14_MATCHED_PRETRUTH_DIRECT_V1'
test "$(printf '%s\\n' "$launch_marker" | sed -n '2p')" = '691'
test "$(printf '%s\\n' "$launch_marker" | sed -n '3p')" = '31325324850'
test "$(printf '%s\\n' "$launch_marker" | wc -l)" -eq 3
'''
NEW_CHILD_GUARD='''progress 'P15 OUTER ACTIVATION ALREADY GATED / PROMOTED METHOD GUARDS'
test "$(git rev-parse HEAD)" = "$BASE_SHA"
test ! -e orbittrace_support_safe_halo_p15/MATCHED_PRETRUTH_RUN.md
echo PASS_P15_OUTER_ONE_FILE_ACTIVATION_ALREADY_VERIFIED
'''


def once(text:str,old:str,new:str,label:str)->str:
    n=text.count(old)
    if n!=1: raise RuntimeError(f'P15 v2 technical guard repair anchor {label} count={n}')
    return text.replace(old,new,1)


def main()->int:
    if len(sys.argv)!=3: raise SystemExit('usage: generate_matched_pretruth_p15_v2.py EXACT_P13_V3 OUTPUT')
    source,output=map(Path,sys.argv[1:])
    subprocess.run([sys.executable,str(V1),str(source),str(output)],check=True)
    original=output.read_text()
    text=once(original,OLD_CHILD_GUARD,NEW_CHILD_GUARD,'inherited P14 child marker')

    if text.replace(NEW_CHILD_GUARD,OLD_CHILD_GUARD,1)!=original:
        raise RuntimeError('P15 v2 guard repair changed generated shell outside the stale child guard')
    required=(
        'PASS_P15_OUTER_ONE_FILE_ACTIVATION_ALREADY_VERIFIED',
        'PASS_P14_DIRECT_AUTHORITATIVE_DEVELOPMENT',
        'PASS_P15_MATCHED_SUPPORT_SAFE_HALO_SOURCE_ACTIVE',
        'PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES',
        'p15_halo_availability_frozen_before_truth',
        '23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6',
        'exit 0',
    )
    for token in required:
        if token not in text: raise RuntimeError(f'P15 v2 generated invariant missing: {token}')
    forbidden=(
        "orbittrace_support_safe_rank_p14/LAUNCH_PRETRUTH.md",
        "LAUNCH_P14_MATCHED_PRETRUTH_DIRECT_V1",
        'OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE',
        'evaluate_frozen_blindsafe.py','finalize_p3_evaluator_result.py',
        'OrbitTrace-April','target_coordinate',
    )
    for token in forbidden:
        if token in text: raise RuntimeError(f'P15 v2 stale/posttruth/target token survived: {token}')
    output.write_text(text)
    print('PASS_P15_MATCHED_PRETRUTH_V2_STALE_P14_CHILD_GUARD_REMOVED_ONLY')
    return 0


if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent.parent
P15_GEN=HERE/'orbittrace_support_safe_halo_p15'/'generate_matched_pretruth_p15_v2.py'
P17_PATCH=HERE/'orbittrace_reciprocal_support_closure_p17'/'apply_p17_reciprocal_support_closure.py'
P15_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'


def main()->int:
    if len(sys.argv)!=3: raise SystemExit('usage: generate_matched_pretruth_p17.py EXACT_P13_V3 OUTPUT')
    source,output=map(Path,sys.argv[1:])
    subprocess.run([sys.executable,str(P15_GEN),str(source),str(output)],check=True)
    original=output.read_text()
    lines=original.splitlines(keepends=True)

    run_hits=[i for i,l in enumerate(lines) if 'orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py' in l and l.rstrip().endswith('/tmp/p12_panel.py')]
    if len(run_hits)!=1: raise RuntimeError(f'P17 P15 runtime anchor count={len(run_hits)}')
    i=run_hits[0]
    old_run=lines[i]
    m=re.match(r'^(?P<prefix>\s*python\s+orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15\.py\s+)(?P<src>\S+)(?P<out>\s+/tmp/p12_panel\.py\s*)$',old_run.rstrip('\n'))
    if not m: raise RuntimeError('P17 cannot parse P15 runtime line')
    src=m.group('src')
    lines[i]=(m.group('prefix')+src+' /tmp/p12_panel_p15.py\n')

    sha_hits=[j for j,l in enumerate(lines) if P15_SHA in l and '/tmp/p12_panel.py' in l and 'sha256sum -c' in l]
    if len(sha_hits)!=1: raise RuntimeError(f'P17 P15 source-hash anchor count={len(sha_hits)}')
    j=sha_hits[0]
    lines[j]=(
        f"echo '{P15_SHA}  /tmp/p12_panel_p15.py' | sha256sum -c -\n"
        "python orbittrace_reciprocal_support_closure_p17/apply_p17_reciprocal_support_closure.py /tmp/p12_panel_p15.py /tmp/p12_panel.py | tee /tmp/p17_source_build.txt\n"
        "python -m py_compile /tmp/p12_panel.py\n"
        "grep -F 'P17_SCOPE=represent P15-unavailable reciprocal explicitly; missing reciprocal reliability is fail-closed false; no P12 threshold/model/geometry/rank change' /tmp/p17_source_build.txt\n"
        "echo PASS_P17_MATCHED_SOURCE_ACTIVE\n"
    )
    text=''.join(lines)

    # Reversibility proof: replace the exact P17 insertion with the original P15
    # runtime+hash lines and recover the generated P15-v2 shell byte-for-byte.
    restored=text
    new_run=m.group('prefix')+src+' /tmp/p12_panel_p15.py\n'
    new_hash=(
        f"echo '{P15_SHA}  /tmp/p12_panel_p15.py' | sha256sum -c -\n"
        "python orbittrace_reciprocal_support_closure_p17/apply_p17_reciprocal_support_closure.py /tmp/p12_panel_p15.py /tmp/p12_panel.py | tee /tmp/p17_source_build.txt\n"
        "python -m py_compile /tmp/p12_panel.py\n"
        "grep -F 'P17_SCOPE=represent P15-unavailable reciprocal explicitly; missing reciprocal reliability is fail-closed false; no P12 threshold/model/geometry/rank change' /tmp/p17_source_build.txt\n"
        "echo PASS_P17_MATCHED_SOURCE_ACTIVE\n"
    )
    restored=restored.replace(new_run,old_run,1).replace(new_hash,original.splitlines(keepends=True)[j],1)
    if restored!=original: raise RuntimeError('P17 generated shell changed outside the exact P15->P17 source insertion')

    required=(
        'PASS_P15_OUTER_ONE_FILE_ACTIVATION_ALREADY_VERIFIED',
        'PASS_P15_MATCHED_SUPPORT_SAFE_HALO_SOURCE_ACTIVE',
        'PASS_P17_MATCHED_SOURCE_ACTIVE',
        'PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES',
        'p15_halo_availability_frozen_before_truth',
        'exit 0',
    )
    for token in required:
        if token not in text: raise RuntimeError(f'P17 generated invariant missing: {token}')
    for token in ('OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE','evaluate_frozen_blindsafe.py','finalize_p3_evaluator_result.py','OrbitTrace-April','target_coordinate'):
        if token in text: raise RuntimeError(f'P17 forbidden posttruth/target token survived: {token}')
    output.write_text(text)
    print('PASS_P17_PRETRUTH_SHELL_GENERATED_FROM_EXACT_P15_V2')
    return 0


if __name__=='__main__': raise SystemExit(main())

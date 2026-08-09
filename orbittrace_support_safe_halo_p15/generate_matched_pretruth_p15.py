#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
P14=HERE.parent/'orbittrace_support_safe_rank_p14'/'generate_matched_pretruth_direct_v3.py'
P14_PARENT='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
P15_MATCHED='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
FORBIDDEN=('OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE','evaluate_frozen_blindsafe.py','finalize_p3_evaluator_result.py','OrbitTrace-April','target_coordinate')


def once(text:str,old:str,new:str,label:str)->str:
    n=text.count(old)
    if n!=1: raise RuntimeError(f'P15 matched pretruth anchor {label} count={n}')
    return text.replace(old,new,1)


def clean(text:str,label:str)->None:
    for token in FORBIDDEN:
        if token in text:
            raise RuntimeError(f'P15 forbidden posttruth/target token after {label}: {token}')


def main()->int:
    if len(sys.argv)!=3: raise SystemExit('usage: generate_matched_pretruth_p15.py EXACT_V3 OUTPUT')
    source,output=map(Path,sys.argv[1:])
    subprocess.run([sys.executable,str(P14),str(source),str(output)],check=True)
    text=output.read_text(encoding='utf-8')
    clean(text,'P14 base generation')

    transport_old=(
        "python orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py /tmp/p12_panel_v2.py /tmp/p12_panel.py\n"
        f"echo '{P14_PARENT}  /tmp/p12_panel.py' | sha256sum -c -\n"
        "echo PASS_P14_DIRECT_AUDITED_SNM_ID_TRANSPORT_ACTIVE\n"
    )
    transport_new=(
        "python orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py /tmp/p12_panel_v2.py /tmp/p12_panel_v3.py\n"
        f"echo '{P14_PARENT}  /tmp/p12_panel_v3.py' | sha256sum -c -\n"
        "python orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py /tmp/p12_panel_v3.py /tmp/p12_panel.py\n"
        f"echo '{P15_MATCHED}  /tmp/p12_panel.py' | sha256sum -c -\n"
        "echo PASS_P15_MATCHED_SUPPORT_SAFE_HALO_SOURCE_ACTIVE\n"
    )
    text=once(text,transport_old,transport_new,'P15 matched halo source'); clean(text,'halo source transform')

    stage_old=(
        "cp orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py /tmp/finalize_p14_checkpoint.py\n"
        "python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py\n"
    )
    stage_new=(
        "cp orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py /tmp/finalize_p14_checkpoint.py\n"
        "cp orbittrace_support_safe_halo_p15/finalize_pretruth_checkpoint_p15.py /tmp/finalize_p15_checkpoint.py\n"
        "python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py /tmp/finalize_p15_checkpoint.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py\n"
    )
    text=once(text,stage_old,stage_new,'P15 finalizer staging'); clean(text,'finalizer staging')

    # Use explicit backslash-newline bytes. A triple-quoted literal with a source
    # line ending in '\\' can be parsed as a Python line continuation and can
    # accidentally consume the following generated-shell text. This is a pure
    # launcher repair; the finalizer arguments and checkpoint science are unchanged.
    finalizer_old=(
        "  python /tmp/finalize_p14_checkpoint.py \\\n"
        "    --base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py \\\n"
        "    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\\n"
    )
    finalizer_new=(
        "  python /tmp/finalize_p15_checkpoint.py \\\n"
        "    --base-transport-finalizer /tmp/finalize_p14_checkpoint.py \\\n"
        "    --base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py \\\n"
        "    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\\n"
    )
    text=once(text,finalizer_old,finalizer_new,'P15 finalizer call'); clean(text,'finalizer call')

    barrier_old=(
        "    assert c['p14_p12_snm_id_transport_repair_audit_run']==31326543587\n"
        "    assert c['p14_p12_snm_id_transport_scientific_delta'] is False\n"
        "    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False\n"
    )
    barrier_new=(
        "    assert c['p14_p12_snm_id_transport_repair_audit_run']==31326543587\n"
        "    assert c['p14_p12_snm_id_transport_scientific_delta'] is False\n"
        "    assert c['p15_architecture']=='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'\n"
        f"    assert c['p15_parent_source_sha256']=='{P14_PARENT}'\n"
        f"    assert c['p15_generated_matched_source_sha256']=='{P15_MATCHED}'\n"
        "    assert c['p15_min_direction_negatives_unchanged']==128\n"
        "    assert c['p15_no_padding_resampling_or_relaxation'] is True\n"
        "    assert c['p15_secondary_characterization_only'] is True\n"
        "    assert c['p15_halo_availability_frozen_before_truth'] is True\n"
        "    ledger=c['p15_unavailable_directions']; assert isinstance(ledger,list)\n"
        "    assert c['p15_unavailable_direction_count']==len(ledger)\n"
        "    import hashlib as _h,json as _j\n"
        "    assert c['p15_availability_sha256']==_h.sha256(_j.dumps(ledger,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()\n"
        "    assert all(r['status']=='CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES' and int(r['required_negative_count'])==128 and int(r['observed_negative_count'])<128 for r in ledger)\n"
        "    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False\n"
    )
    text=once(text,barrier_old,barrier_new,'P15 hard pretruth barrier'); clean(text,'hard pretruth barrier')

    source_old='sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/p12_panel.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py > pretruth/p14_source_sha256.txt\n'
    source_new='sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/p12_panel.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py /tmp/finalize_p15_checkpoint.py orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py > pretruth/p15_source_sha256.txt\n'
    text=once(text,source_old,source_new,'P15 source ledger'); clean(text,'source ledger')

    text=once(text,'PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES','PASS_P15_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES','P15 barrier label')
    clean(text,'final P15 transform')

    required=(P14_PARENT,P15_MATCHED,'PASS_P15_MATCHED_SUPPORT_SAFE_HALO_SOURCE_ACTIVE','apply_support_safe_halo_p15.py','/tmp/finalize_p15_checkpoint.py','CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES','PASS_P15_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES')
    for token in required:
        if token not in text: raise RuntimeError(f'P15 generated invariant missing {token}')
    output.write_text(text,encoding='utf-8')
    print('PASS_P15_MATCHED_PRETRUTH_GENERATOR_SOURCE_FREEZE')
    return 0


if __name__=='__main__': raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE / 'generate_matched_pretruth_direct_v2.py'
PARENT_SHA = 'f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'
TECH_SHA = '55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
REPAIR_AUDIT_RUN = '31326543587'


def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f'P14 direct v3 integration anchor {label} count={n}')
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit('usage: generate_matched_pretruth_direct_v3.py EXACT_V3 OUTPUT')
    source, output = map(Path, sys.argv[1:])
    subprocess.run([sys.executable, str(V2), str(source), str(output)], check=True)
    text = output.read_text(encoding='utf-8')

    transport_old = '''python orbittrace_core_halo_p13_literature/apply_p12_matched_transport_patch_v2.py /tmp/p12.py /tmp/p12_panel.py
echo "$P12_TRANSPORT_SHA  /tmp/p12_panel.py" | sha256sum -c -
'''
    transport_new = f'''python orbittrace_core_halo_p13_literature/apply_p12_matched_transport_patch_v2.py /tmp/p12.py /tmp/p12_panel_v2.py
echo '{PARENT_SHA}  /tmp/p12_panel_v2.py' | sha256sum -c -
python orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py /tmp/p12_panel_v2.py /tmp/p12_panel.py
echo '{TECH_SHA}  /tmp/p12_panel.py' | sha256sum -c -
echo PASS_P14_DIRECT_AUDITED_SNM_ID_TRANSPORT_ACTIVE
'''
    text = once(text, transport_old, transport_new, 'runtime transport')

    stage_old = '''cp orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint_p14.py /tmp/finalize_p14_checkpoint.py
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint.py
'''
    stage_new = '''cp orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint_p14.py /tmp/finalize_p14_checkpoint_base.py
cp orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py /tmp/finalize_p14_checkpoint.py
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py
'''
    text = once(text, stage_old, stage_new, 'transport finalizer staging')

    finalizer_old = '''  python /tmp/finalize_p14_checkpoint.py \\
    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\
'''
    finalizer_new = '''  python /tmp/finalize_p14_checkpoint.py \\
    --base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py \\
    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\
'''
    text = once(text, finalizer_old, finalizer_new, 'transport-aware checkpoint finalizer')

    barrier_old = """    assert c['p14_rank_frozen_before_truth'] is True and c['p14_no_fabricated_score'] is True and c['p14_episode_size_128_unchanged'] is True
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
"""
    barrier_new = f"""    assert c['p14_rank_frozen_before_truth'] is True and c['p14_no_fabricated_score'] is True and c['p14_episode_size_128_unchanged'] is True
    assert c['p13_transport_parent_source_sha256']=='{PARENT_SHA}'
    assert c['p13_transport_source_sha256']=='{TECH_SHA}'
    assert c['p14_p12_snm_id_transport_repair_audit_run']=={REPAIR_AUDIT_RUN}
    assert c['p14_p12_snm_id_transport_scientific_delta'] is False
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
"""
    text = once(text, barrier_old, barrier_new, 'pretruth transport provenance barrier')

    source_hash_old = 'sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/finalize_p14_checkpoint.py > pretruth/p14_source_sha256.txt\n'
    source_hash_new = 'sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/p12_panel.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py > pretruth/p14_source_sha256.txt\n'
    text = once(text, source_hash_old, source_hash_new, 'source hash ledger')

    required = (
        'PASS_P14_DIRECT_AUDITED_SNM_ID_TRANSPORT_ACTIVE',
        PARENT_SHA,
        TECH_SHA,
        'apply_p12_snm_id_transport_from_v2.py',
        '--base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py',
        "p14_p12_snm_id_transport_scientific_delta'] is False",
        'PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES',
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f'P14 direct v3 generated invariant missing: {token}')
    for token in ('OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE', 'evaluate_frozen_blindsafe.py', 'finalize_p3_evaluator_result.py', 'OrbitTrace-April', 'target_coordinate'):
        if token in text:
            raise RuntimeError(f'P14 direct v3 forbidden posttruth/target token survived: {token}')

    output.write_text(text, encoding='utf-8')
    print('PASS_P14_DIRECT_V3_AUDITED_TRANSPORT_GENERATED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

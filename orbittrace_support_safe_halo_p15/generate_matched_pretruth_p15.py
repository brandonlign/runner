#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
P14_GEN=HERE.parent/'orbittrace_support_safe_rank_p14'/'generate_matched_pretruth_direct_v3.py'
P14_TECH_SHA='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
P15_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P15_DEV_AUDIT_RUN='31327637103'


def once(text:str,old:str,new:str,label:str)->str:
    n=text.count(old)
    if n!=1: raise RuntimeError(f'P15 matched integration anchor {label} count={n}')
    return text.replace(old,new,1)


def main()->int:
    if len(sys.argv)!=3: raise SystemExit('usage: generate_matched_pretruth_p15.py EXACT_P13_V3 OUTPUT')
    source,output=map(Path,sys.argv[1:])
    subprocess.run([sys.executable,str(P14_GEN),str(source),str(output)],check=True)
    text=output.read_text()

    runtime_old=f'''python orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py /tmp/p12_panel_v2.py /tmp/p12_panel.py
echo '{P14_TECH_SHA}  /tmp/p12_panel.py' | sha256sum -c -
echo PASS_P14_DIRECT_AUDITED_SNM_ID_TRANSPORT_ACTIVE
'''
    runtime_new=f'''python orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py /tmp/p12_panel_v2.py /tmp/p12_panel_v3.py
echo '{P14_TECH_SHA}  /tmp/p12_panel_v3.py' | sha256sum -c -
echo PASS_P14_DIRECT_AUDITED_SNM_ID_TRANSPORT_ACTIVE
python orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py /tmp/p12_panel_v3.py /tmp/p12_panel.py
echo '{P15_SHA}  /tmp/p12_panel.py' | sha256sum -c -
echo PASS_P15_MATCHED_SUPPORT_SAFE_HALO_SOURCE_ACTIVE
'''
    text=once(text,runtime_old,runtime_new,'P15 matched runtime')

    stage_old='''cp orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint_p14.py /tmp/finalize_p14_checkpoint_base.py
cp orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py /tmp/finalize_p14_checkpoint.py
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py
'''
    stage_new='''cp orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint_p14.py /tmp/finalize_p14_checkpoint_base.py
cp orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py /tmp/finalize_p14_transport_checkpoint.py
cp orbittrace_support_safe_halo_p15/finalize_pretruth_checkpoint_p15.py /tmp/finalize_p15_checkpoint.py
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_transport_checkpoint.py /tmp/finalize_p15_checkpoint.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py
'''
    text=once(text,stage_old,stage_new,'P15 checkpoint finalizer staging')

    call_old='''  python /tmp/finalize_p14_checkpoint.py \\
    --base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py \\
    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\
'''
    call_new='''  python /tmp/finalize_p15_checkpoint.py \\
    --base-p14-transport-finalizer /tmp/finalize_p14_transport_checkpoint.py \\
    --base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py \\
    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\
'''
    text=once(text,call_old,call_new,'P15 checkpoint finalizer call')

    barrier_old=f'''    assert c['p13_transport_parent_source_sha256']=='f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'
    assert c['p13_transport_source_sha256']=='{P14_TECH_SHA}'
    assert c['p14_p12_snm_id_transport_repair_audit_run']==31326543587
    assert c['p14_p12_snm_id_transport_scientific_delta'] is False
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
'''
    barrier_new=barrier_old.replace("    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False\n",f'''    assert c['p15_architecture']=='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
    assert c['p15_parent_source_sha256']=='{P14_TECH_SHA}'
    assert c['p15_generated_matched_source_sha256']=='{P15_SHA}'
    assert c['p15_min_direction_negatives_unchanged']==128
    assert c['p15_no_padding_resampling_or_relaxation'] is True
    assert c['p15_secondary_characterization_only'] is True
    assert c['p15_halo_availability_frozen_before_truth'] is True
    assert c['p15_unavailable_direction_count']==len(c['p15_unavailable_directions'])
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
''')
    text=once(text,barrier_old,barrier_new,'P15 pretruth barrier')

    source_old='sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/p12_panel.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py > pretruth/p14_source_sha256.txt\n'
    source_new='sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/p12_panel_v3.py /tmp/p12_panel.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_transport_checkpoint.py /tmp/finalize_p15_checkpoint.py > pretruth/p15_source_sha256.txt\n'
    text=once(text,source_old,source_new,'P15 source hash ledger')

    required=('PASS_P15_MATCHED_SUPPORT_SAFE_HALO_SOURCE_ACTIVE',P15_SHA,'apply_support_safe_halo_p15.py','/tmp/finalize_p15_checkpoint.py',"p15_halo_availability_frozen_before_truth'] is True",'PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES','exit 0')
    for token in required:
        if token not in text: raise RuntimeError(f'P15 matched generated invariant missing: {token}')
    forbidden=('OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE','evaluate_frozen_blindsafe.py','finalize_p3_evaluator_result.py','OrbitTrace-April','target_coordinate')
    for token in forbidden:
        if token in text: raise RuntimeError(f'P15 matched forbidden posttruth/target token survived: {token}')
    if text.count('apply_support_safe_halo_p15.py /tmp/p12_panel_v3.py /tmp/p12_panel.py')!=1:
        raise RuntimeError('P15 matched runtime application not unique')
    output.write_text(text)
    print(f'P15_MATCHED_PREREGISTERED_DEVELOPMENT_AUDIT_RUN={P15_DEV_AUDIT_RUN}')
    print('PASS_P15_MATCHED_PRETRUTH_GENERATOR_PREREGISTERED')
    return 0


if __name__=='__main__': raise SystemExit(main())

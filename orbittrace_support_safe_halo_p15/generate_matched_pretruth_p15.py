#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
P14=HERE.parent/'orbittrace_support_safe_rank_p14'/'generate_matched_pretruth_direct_v3.py'
P14_TRANSPORT='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
P15_MATCHED='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'


def once(text:str,old:str,new:str,label:str)->str:
    n=text.count(old)
    if n!=1: raise RuntimeError(f'P15 matched pretruth anchor {label} count={n}')
    return text.replace(old,new,1)


def main()->int:
    if len(sys.argv)!=3:
        raise SystemExit('usage: generate_matched_pretruth_p15.py EXACT_V3 OUTPUT')
    source,output=map(Path,sys.argv[1:])
    subprocess.run([sys.executable,str(P14),str(source),str(output)],check=True)
    text=output.read_text(encoding='utf-8')

    transport_old=f'''python orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py /tmp/p12_panel_v2.py /tmp/p12_panel.py
echo '{P14_TRANSPORT}  /tmp/p12_panel.py' | sha256sum -c -
echo PASS_P14_DIRECT_AUDITED_SNM_ID_TRANSPORT_ACTIVE
'''
    transport_new=f'''python orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py /tmp/p12_panel_v2.py /tmp/p12_panel_v3.py
echo '{P14_TRANSPORT}  /tmp/p12_panel_v3.py' | sha256sum -c -
python orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py /tmp/p12_panel_v3.py /tmp/p12_panel.py
echo '{P15_MATCHED}  /tmp/p12_panel.py' | sha256sum -c -
echo PASS_P15_SUPPORT_SAFE_HALO_MATCHED_SOURCE_ACTIVE
'''
    text=once(text,transport_old,transport_new,'P15 matched halo source')

    stage_old='''cp orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py /tmp/finalize_p14_checkpoint.py
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py
'''
    stage_new='''cp orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py /tmp/finalize_p14_checkpoint.py
cp orbittrace_support_safe_halo_p15/finalize_pretruth_checkpoint_p15.py /tmp/finalize_p15_checkpoint.py
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py /tmp/finalize_p15_checkpoint.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py
'''
    text=once(text,stage_old,stage_new,'P15 finalizer staging')

    finalizer_old='''  python /tmp/finalize_p14_checkpoint.py \\
    --base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py \\
    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\
'''
    finalizer_new='''  python /tmp/finalize_p15_checkpoint.py \\
    --base-transport-finalizer /tmp/finalize_p14_checkpoint.py \\
    --base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py \\
    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\
'''
    text=once(text,finalizer_old,finalizer_new,'P15 finalizer call')

    barrier_old=f'''    assert c['p14_p12_snm_id_transport_repair_audit_run']==31326543587
    assert c['p14_p12_snm_id_transport_scientific_delta'] is False
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
'''
    barrier_new=f'''    assert c['p14_p12_snm_id_transport_repair_audit_run']==31326543587
    assert c['p14_p12_snm_id_transport_scientific_delta'] is False
    assert c['p15_architecture']=='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
    assert c['p15_parent_source_sha256']=='{P14_TRANSPORT}'
    assert c['p15_halo_source_sha256']=='{P15_MATCHED}'
    assert c['p15_min_direction_negatives_unchanged']==128
    assert c['p15_no_padding_resampling_or_relaxation'] is True
    assert c['p15_secondary_characterization_only'] is True
    assert c['p15_matched_pretruth_frozen_before_truth'] is True
    ledger=c['p15_unavailable_directions']; assert isinstance(ledger,list)
    assert c['p15_unavailable_direction_count']==len(ledger)
    import hashlib as _h,json as _j
    assert c['p15_availability_sha256']==_h.sha256(_j.dumps(ledger,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert all(r['status']=='CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES' and int(r['required_negative_count'])==128 and int(r['observed_negative_count'])<128 for r in ledger)
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
'''
    text=once(text,barrier_old,barrier_new,'P15 hard pretruth barrier')

    source_old='sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/p12_panel.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py > pretruth/p14_source_sha256.txt\n'
    source_new='sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/p12_panel.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py /tmp/finalize_p15_checkpoint.py orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py > pretruth/p15_source_sha256.txt\n'
    text=once(text,source_old,source_new,'P15 source ledger')

    text=once(text,'PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES','PASS_P15_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES','P15 barrier label')

    required=(
        P14_TRANSPORT,P15_MATCHED,'PASS_P15_SUPPORT_SAFE_HALO_MATCHED_SOURCE_ACTIVE',
        'apply_support_safe_halo_p15.py','/tmp/finalize_p15_checkpoint.py',
        'CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES',
        'PASS_P15_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES',
    )
    for token in required:
        if token not in text: raise RuntimeError(f'P15 generated invariant missing {token}')
    for token in ('OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE','evaluate_frozen_blindsafe.py','finalize_p3_evaluator_result.py','OrbitTrace-April','target_coordinate'):
        if token in text: raise RuntimeError(f'P15 forbidden posttruth/target token survived: {token}')
    output.write_text(text,encoding='utf-8')
    print('PASS_P15_MATCHED_PRETRUTH_GENERATOR_SOURCE_FREEZE')
    return 0


if __name__=='__main__':
    raise SystemExit(main())

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
    if n!=1: raise RuntimeError(f'{label} count={n}')
    return text.replace(old,new,1)


def report(label:str,text:str)->None:
    hits=[x for x in FORBIDDEN if x in text]
    print(label,'len',len(text),'forbidden',hits)
    for x in hits:
        i=text.index(x)
        print('CONTEXT',x,repr(text[max(0,i-240):i+240]))


def main()->int:
    if len(sys.argv)!=2: raise SystemExit('usage: audit_generate_matched_pretruth_p15_transform.py EXACT_V3')
    source=Path(sys.argv[1]); tmp=Path('/tmp/p14_base_pretruth.sh')
    subprocess.run([sys.executable,str(P14),str(source),str(tmp)],check=True)
    text=tmp.read_text(); report('P14_BASE',text)
    if any(x in text for x in FORBIDDEN): raise RuntimeError('P14 base already contains forbidden token')

    transport_old=f'''python orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py /tmp/p12_panel_v2.py /tmp/p12_panel.py
echo '{P14_PARENT}  /tmp/p12_panel.py' | sha256sum -c -
echo PASS_P14_DIRECT_AUDITED_SNM_ID_TRANSPORT_ACTIVE
'''
    transport_new=f'''python orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py /tmp/p12_panel_v2.py /tmp/p12_panel_v3.py
echo '{P14_PARENT}  /tmp/p12_panel_v3.py' | sha256sum -c -
python orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py /tmp/p12_panel_v3.py /tmp/p12_panel.py
echo '{P15_MATCHED}  /tmp/p12_panel.py' | sha256sum -c -
echo PASS_P15_MATCHED_SUPPORT_SAFE_HALO_SOURCE_ACTIVE
'''
    text=once(text,transport_old,transport_new,'transport'); report('AFTER_TRANSPORT',text)

    stage_old='''cp orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py /tmp/finalize_p14_checkpoint.py
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py
'''
    stage_new='''cp orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py /tmp/finalize_p14_checkpoint.py
cp orbittrace_support_safe_halo_p15/finalize_pretruth_checkpoint_p15.py /tmp/finalize_p15_checkpoint.py
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py /tmp/finalize_p15_checkpoint.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py
'''
    text=once(text,stage_old,stage_new,'stage'); report('AFTER_STAGE',text)

    finalizer_old='''  python /tmp/finalize_p14_checkpoint.py \\
    --base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py \\
    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\
'''
    finalizer_new='''  python /tmp/finalize_p15_checkpoint.py \\
    --base-transport-finalizer /tmp/finalize_p14_checkpoint.py \\
    --base-p14-finalizer /tmp/finalize_p14_checkpoint_base.py \\
    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\
'''
    text=once(text,finalizer_old,finalizer_new,'finalizer'); report('AFTER_FINALIZER',text)

    barrier_old='''    assert c['p14_p12_snm_id_transport_repair_audit_run']==31326543587
    assert c['p14_p12_snm_id_transport_scientific_delta'] is False
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
'''
    barrier_new=f'''    assert c['p14_p12_snm_id_transport_repair_audit_run']==31326543587
    assert c['p14_p12_snm_id_transport_scientific_delta'] is False
    assert c['p15_architecture']=='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
    assert c['p15_parent_source_sha256']=='{P14_PARENT}'
    assert c['p15_generated_matched_source_sha256']=='{P15_MATCHED}'
    assert c['p15_min_direction_negatives_unchanged']==128
    assert c['p15_no_padding_resampling_or_relaxation'] is True
    assert c['p15_secondary_characterization_only'] is True
    assert c['p15_halo_availability_frozen_before_truth'] is True
    ledger=c['p15_unavailable_directions']; assert isinstance(ledger,list)
    assert c['p15_unavailable_direction_count']==len(ledger)
    import hashlib as _h,json as _j
    assert c['p15_availability_sha256']==_h.sha256(_j.dumps(ledger,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert all(r['status']=='CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES' and int(r['required_negative_count'])==128 and int(r['observed_negative_count'])<128 for r in ledger)
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
'''
    text=once(text,barrier_old,barrier_new,'barrier'); report('AFTER_BARRIER',text)

    source_old='sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/p12_panel.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py > pretruth/p14_source_sha256.txt\n'
    source_new='sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/p12_panel.py /tmp/finalize_p14_checkpoint_base.py /tmp/finalize_p14_checkpoint.py /tmp/finalize_p15_checkpoint.py orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py > pretruth/p15_source_sha256.txt\n'
    text=once(text,source_old,source_new,'source'); report('AFTER_SOURCE',text)

    text=once(text,'PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES','PASS_P15_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES','label'); report('AFTER_LABEL',text)
    if any(x in text for x in FORBIDDEN): raise RuntimeError('P15 transform introduced forbidden token')
    print('PASS_P15_TRANSFORM_STAGE_DIAGNOSTIC_NO_FORBIDDEN_TOKEN')
    return 0


if __name__=='__main__': raise SystemExit(main())

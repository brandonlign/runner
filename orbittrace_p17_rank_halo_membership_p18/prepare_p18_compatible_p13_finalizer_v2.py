#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PARENT_TRANSPORT="P13_TRANSPORT_SOURCE_SHA256='f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'\n"
TECH_TRANSPORT="P13_TRANSPORT_SOURCE_SHA256='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'\n"
OLD_CP="    require(cp['p3_diagnostics']['primary_candidate_is_core_only'] is True and cp['p3_diagnostics']['halo_can_affect_primary_evaluation'] is False,f'generic evaluator compatibility role changed {panel}')\n"
NEW_CP="    require(cp['p3_diagnostics']['primary_candidate_is_core_only'] is False and cp['p3_diagnostics']['halo_can_affect_primary_evaluation'] is True and cp['p3_diagnostics']['family_existence_and_rank_core_only'] is True and cp['p3_diagnostics']['reported_membership_is_exact_label_free_halo'] is True and cp['p3_diagnostics']['p18_no_new_member_proposal'] is True,f'P18 checkpoint output semantics changed {panel}')\n"
OLD_Q="        require(q['p3_diagnostics']['primary_candidate_is_core_only'] is True and q['p3_diagnostics']['halo_can_affect_primary_evaluation'] is False,f'halo entered primary evaluator {panel}')\n"
NEW_Q="        require(q['p3_diagnostics']['primary_candidate_is_core_only'] is False and q['p3_diagnostics']['halo_can_affect_primary_evaluation'] is True and q['p3_diagnostics']['family_existence_and_rank_core_only'] is True and q['p3_diagnostics']['reported_membership_is_exact_label_free_halo'] is True and q['p3_diagnostics']['p18_no_new_member_proposal'] is True,f'P18 output semantics changed {panel}')\n"


def once(text:str,old:str,new:str,label:str)->str:
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f'P18 finalizer v2 compatibility anchor {label} count={n}')
    return text.replace(old,new,1)


def main()->int:
    if len(sys.argv)!=3:
        raise SystemExit('usage: prepare_p18_compatible_p13_finalizer_v2.py BASE OUTPUT')
    src,out=map(Path,sys.argv[1:])
    original=src.read_text()
    text=once(original,PARENT_TRANSPORT,TECH_TRANSPORT,'transport provenance')
    text=once(text,OLD_CP,NEW_CP,'checkpoint output role')
    text=once(text,OLD_Q,NEW_Q,'evaluator output role')
    restored=text.replace(NEW_Q,OLD_Q,1).replace(NEW_CP,OLD_CP,1).replace(TECH_TRANSPORT,PARENT_TRANSPORT,1)
    if restored!=original:
        raise RuntimeError('P18 finalizer v2 differs outside three exact compatibility surfaces')
    gates=(
        'four_to_nine_gain_ge_0_10','four_to_twentyfour_gain_ge_0_10',
        'macro_f1_not_more_than_0_10_lower','retain_at_least_80pct_f1_gt_0_5_count',
        'PASS_P13_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS',
        'FAIL_P13_MATCHED_SPARSE_SUPERIORITY_NO_GO',
    )
    for token in gates:
        if text.count(token)!=original.count(token) or token not in text:
            raise RuntimeError(f'P18 inherited benchmark gate changed: {token}')
    for token in ('OrbitTrace-April','target_coordinate'):
        if token in text:
            raise RuntimeError(f'forbidden target token present: {token}')
    out.write_text(text)
    print('PASS_P18_P13_FINALIZER_EXACT_THREE_SURFACE_POSTTRUTH_COMPATIBILITY_REPAIR')
    return 0


if __name__=='__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SIGNAL_SHA256 = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
FRONTIER_SHA256 = '5ca5cab6f6a47c05d013237190ad21b247a13e22fa06988ee36dc0832a37fc02'
FRONTIER_CANONICAL_SHA256 = '8373f4946e7f84c7c3ee0ac51167881722d4f8b78c34383400f1967824df6798'
COMPONENT_SHA256 = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
V31_ORDER_SHA256 = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'
V46_ORDER_SHA256 = '80965d6e32ae772a3ebe405bd147095e00f2c9c4688160e189d9ce69f3deaf89'
EXPECTED_FREEZE_CANONICAL_SHA256 = '706916d7d101903b982d481df8807d54d59af0ea7905aadb305205193aa3013d'
EXPECTED_FREEZE_FILE_SHA256 = '39534c85d2fca765451c0766452c4e4106dacccbb27c064c6f4a87be8cdd7949'
RECOVERY_F1 = 0.5
PANEL_BUDGETS = ((2013, 11), (2014, 9))


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256((json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256('\n'.join(map(str, order)).encode()).hexdigest()


def freeze_mode(signal_file: Path, frontier_file: Path, component_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(sha(signal_file) == SIGNAL_SHA256, '#1098 signal identity changed')
    require(sha(frontier_file) == FRONTIER_SHA256, '#1126 frontier identity changed')
    require(sha(component_file) == COMPONENT_SHA256, 'component identity changed')

    signal = json.loads(signal_file.read_text())
    frontier = json.loads(frontier_file.read_text())
    components = json.loads(component_file.read_text())

    require(signal['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', '#1098 signal verdict changed')
    require(signal['scientific_role'] == 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION', '#1098 role changed')
    require(int(signal['family_count']) == 229 and len(signal['families']) == 229, '#1098 family universe changed')
    require(signal['target_information_access'] is False and signal['target_region_events_accessed'] is False, '#1098 target firewall changed')
    require(signal['maarsy_scientific_access'] is False and signal['dms_scientific_access'] is False, '#1098 survey firewall changed')
    require(signal['blind_exclusion'] == [20.0, 55.0], '#1098 blind exclusion changed')

    require(frontier['verdict'] == 'PASS_V31_JOINT_COMPONENT_PARETO_FRONTIER_VECTOR_FREEZE', '#1126 vector verdict changed')
    require(frontier['scientific_role'] == 'FIXED_60_JOINT_FAMILY_PARETO_FRONTIER_FROZEN_BEFORE_OUTCOME_TRUTH_OR_1113_AUTHORIZATION', '#1126 role changed')
    require(frontier['canonical_sha256_without_self_field'] == FRONTIER_CANONICAL_SHA256, '#1126 canonical identity changed')
    require(int(frontier['family_count']) == 229 and int(frontier['joint_family_count']) == 60 and int(frontier['frontier_family_count']) == 2, '#1126 family counts changed')
    require(frontier['literature_budget_used'] is False, '#1126 frontier used literature budget')
    require(frontier['target_information_access'] is False and frontier['target_region_events_accessed'] is False, '#1126 target firewall changed')
    require(frontier['maarsy_scientific_access'] is False and frontier['dms_scientific_access'] is False, '#1126 survey firewall changed')
    require(frontier['blind_exclusion'] == [20.0, 55.0], '#1126 blind exclusion changed')

    require(components['truth_accessed'] is False and int(components['component_count']) == 196, 'invalid pretruth components')
    require(components['target_information_access'] is False and components['target_region_events_accessed'] is False, 'component target firewall changed')
    require(components['maarsy_scientific_access'] is False and components['dms_scientific_access'] is False, 'component survey firewall changed')
    require(components['blind_exclusion'] == [20.0, 55.0], 'component blind exclusion changed')

    rows = {str(r['family_id']): r for r in signal['families']}
    require(len(rows) == 229, 'duplicate #1098 family identity')
    v31_order = sorted(rows, key=lambda fid: (int(rows[fid]['v31_rank']), fid))
    require(order_sha(v31_order) == V31_ORDER_SHA256, 'exact v31 HDB order changed')

    frontier_ids = {
        str(r['family_id'])
        for r in frontier['families']
        if bool(r['pareto_frontier_record'])
    }
    require(len(frontier_ids) == 2, 'frontier cardinality changed')
    for fid in frontier_ids:
        require(fid in rows and bool(rows[fid]['joint_signal']), 'frontier escaped fixed joint gate')

    def placement_key(fid: str) -> float:
        r = rows[fid]
        return float(r['component_best_v31_percentile']) if fid in frontier_ids else float(r['v31_percentile'])

    v46_order = sorted(
        rows,
        key=lambda fid: (placement_key(fid), float(rows[fid]['v31_percentile']), fid),
    )
    require(order_sha(v46_order) == V46_ORDER_SHA256, 'binding v46 HDB order changed')

    component_by_id = {str(c['component_id']): c for c in components['components']}
    panels = []
    for year, budget in PANEL_BUDGETS:
        v31_set = set(v31_order[:budget])
        v46_set = set(v46_order[:budget])
        incoming = sorted(v46_set - v31_set)
        outgoing = sorted(v31_set - v46_set)
        require(len(incoming) == 1 and len(outgoing) == 1, f'boundary cardinality changed for {year}')

        in_rows = []
        for fid in incoming:
            r = rows[fid]
            cid = str(r['component_id'])
            require(cid in component_by_id, f'missing component for {fid}')
            gap = float(r['v31_percentile']) - float(r['component_best_v31_percentile'])
            require(int(r['v31_rank']) > budget, f'incoming family was already inside v31 budget {year}')
            require(gap > 0.0, f'incoming family lacks inherited component advantage {year}')
            in_rows.append({
                'family_id': fid,
                'v31_rank': int(r['v31_rank']),
                'v31_percentile': float(r['v31_percentile']),
                'component_id': cid,
                'component_best_v31_percentile': float(r['component_best_v31_percentile']),
                'inherited_evidence_gap': gap,
                'component_member_count': int(r['component_member_count']),
            })

        out_rows = []
        for fid in outgoing:
            r = rows[fid]
            out_rows.append({
                'family_id': fid,
                'v31_rank': int(r['v31_rank']),
                'v31_percentile': float(r['v31_percentile']),
                'component_id': str(r['component_id']),
                'component_best_v31_percentile': float(r['component_best_v31_percentile']),
            })

        panels.append({
            'year': year,
            'budget': budget,
            'incoming_family_ids': incoming,
            'outgoing_family_ids': outgoing,
            'intersection_count': len(v31_set & v46_set),
            'incoming': in_rows,
            'outgoing': out_rows,
        })

    payload: dict[str, Any] = {
        'verdict': 'PASS_V46_BOUNDARY_INHERITANCE_FREEZE',
        'scientific_role': 'FIXED_V31_V46_HDB_BOUNDARY_SUBSTITUTIONS_FROZEN_BEFORE_OUTCOME_TRUTH',
        'source_1098_signal_sha256': SIGNAL_SHA256,
        'source_1126_frontier_sha256': FRONTIER_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'v31_order_sha256': V31_ORDER_SHA256,
        'v46_order_sha256': V46_ORDER_SHA256,
        'frontier_family_count': len(frontier_ids),
        'fixed_hdb_literature_panels': panels,
        'boundary_rule': 'exact set difference top-B(v46) versus top-B(v31) at pre-existing HDB literature budgets B=11 for 2013 and B=9 for 2014',
        'truth_accessed': False,
        'new_rank_or_score_evaluated': False,
        'selector_evaluated': False,
        'successor_selected': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'alternate_budget_evaluated': False,
        'oracle_identity_hardcoded': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    payload['canonical_sha256_without_self_field'] = canonical_sha(payload)
    require(payload['canonical_sha256_without_self_field'] == EXPECTED_FREEZE_CANONICAL_SHA256, 'boundary freeze canonical identity changed')
    out = output / 'V46_BOUNDARY_INHERITANCE_FREEZE.json'
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n')
    require(sha(out) == EXPECTED_FREEZE_FILE_SHA256, 'boundary freeze file identity changed')
    print(json.dumps({'verdict': payload['verdict'], 'canonical_sha256': payload['canonical_sha256_without_self_field'], 'panels': panels}, indent=2, sort_keys=True))
    return 0


def diagnose_mode(freeze_file: Path, hdbscan_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(sha(freeze_file) == EXPECTED_FREEZE_FILE_SHA256, 'frozen boundary identity changed before truth diagnostic')
    freeze = json.loads(freeze_file.read_text())
    require(freeze['verdict'] == 'PASS_V46_BOUNDARY_INHERITANCE_FREEZE', 'boundary freeze verdict changed')
    require(freeze['scientific_role'] == 'FIXED_V31_V46_HDB_BOUNDARY_SUBSTITUTIONS_FROZEN_BEFORE_OUTCOME_TRUTH', 'boundary freeze role changed')
    require(freeze['truth_accessed'] is False, 'boundary identities were not frozen pretruth')

    from orbittrace_v40_component_best_evidence_representative_v1 import train_evaluate as v40

    memberships = json.loads((hdbscan_root / 'family_memberships.json').read_text())
    require(memberships['truth_accessed'] is False, '#950 HDB memberships unexpectedly truth-aware')
    require(memberships['target_information_access'] is False, '#950 target firewall changed')
    require(memberships['maarsy_scientific_access'] is False and memberships['dms_scientific_access'] is False, '#950 survey firewall changed')
    fam_by_id = {str(f['family_id']): f for f in memberships['families']}
    require(len(fam_by_id) == 229, '#950 HDB family universe changed')

    by_year = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year, _ in PANEL_BUDGETS}
    eligible = v40.v22.eligible_from_year_truth(by_year)
    hidden: dict[str, str] = {}
    for year, _ in PANEL_BUDGETS:
        hidden.update(by_year[year])

    needed_ids = set()
    for panel in freeze['fixed_hdb_literature_panels']:
        needed_ids.update(map(str, panel['incoming_family_ids']))
        needed_ids.update(map(str, panel['outgoing_family_ids']))
    require(needed_ids <= set(fam_by_id), 'frozen boundary family missing from #950')

    annual_cache: dict[str, dict[str, Any]] = {}
    for fid in sorted(needed_ids):
        fam = fam_by_id[fid]
        truth = v40.v22.family_truth(fam, hidden, eligible)
        label = truth['best_label']
        if truth['positive'] and label is not None:
            f13, f14 = map(float, v40.v24.annual_f1_for_fixed_label(fam, str(label), by_year))
            diagnostic_group = 'SHOWER/' + str(label)
        else:
            f13 = f14 = 0.0
            diagnostic_group = 'NEG/' + fid
        annual_cache[fid] = {
            'family_id': fid,
            'diagnostic_group': diagnostic_group,
            'positive': bool(truth['positive']),
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY_F1),
            'recoverable_2014': bool(f14 > RECOVERY_F1),
        }

    panel_results = []
    direction = []
    for panel in freeze['fixed_hdb_literature_panels']:
        year = int(panel['year'])
        incoming = str(panel['incoming_family_ids'][0])
        outgoing = str(panel['outgoing_family_ids'][0])
        ik = f'annual_f1_{year}'
        rk = f'recoverable_{year}'
        in_f1 = float(annual_cache[incoming][ik])
        out_f1 = float(annual_cache[outgoing][ik])
        pair_harm = bool(in_f1 < out_f1)
        direction.append(pair_harm)
        panel_results.append({
            'year': year,
            'budget': int(panel['budget']),
            'incoming_family_id': incoming,
            'outgoing_family_id': outgoing,
            'incoming_v31_rank': int(panel['incoming'][0]['v31_rank']),
            'incoming_component_best_v31_percentile': float(panel['incoming'][0]['component_best_v31_percentile']),
            'incoming_inherited_evidence_gap': float(panel['incoming'][0]['inherited_evidence_gap']),
            'incoming_annual_f1': in_f1,
            'outgoing_annual_f1': out_f1,
            'incoming_less_than_outgoing': pair_harm,
            'incoming_recoverable_f1_gt_0_5': bool(annual_cache[incoming][rk]),
            'outgoing_recoverable_f1_gt_0_5': bool(annual_cache[outgoing][rk]),
            'recoverability_category_harm': bool((not annual_cache[incoming][rk]) and annual_cache[outgoing][rk]),
            'incoming_diagnostic_group': annual_cache[incoming]['diagnostic_group'],
            'outgoing_diagnostic_group': annual_cache[outgoing]['diagnostic_group'],
        })

    passed = bool(all(direction))
    result = {
        'verdict': 'PASS_V46_BOUNDARY_INHERITED_EVIDENCE_SUBSTITUTION_HARM_DIAGNOSTIC' if passed else 'FAIL_V46_BOUNDARY_INHERITED_EVIDENCE_SUBSTITUTION_HARM_DIAGNOSTIC',
        'scientific_role': 'POST_V46_MECHANISM_DIAGNOSTIC_ONLY_NO_SUCCESSOR_OR_ORDER_EVALUATED',
        'mechanism_question': 'did each fixed v46 HDB budget-boundary entrant have worse own-family annual F1 than the exact v31 family it displaced despite strictly better inherited component evidence than its own v31 placement',
        'boundary_substitution_harm_supported_both_years': passed,
        'boundary_freeze_sha256': EXPECTED_FREEZE_FILE_SHA256,
        'boundary_freeze_canonical_sha256': EXPECTED_FREEZE_CANONICAL_SHA256,
        'recovery_f1_threshold_descriptive_only': RECOVERY_F1,
        'panels': panel_results,
        'truth_rows_for_fixed_boundary_families': [annual_cache[fid] for fid in sorted(needed_ids)],
        'new_rank_or_score_evaluated': False,
        'counterfactual_order_evaluated': False,
        'replacement_rule_evaluated': False,
        'selector_evaluated': False,
        'successor_selected': False,
        'threshold_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'alternate_budget_search': False,
        'component_gap_threshold_search': False,
        'component_size_rule_search': False,
        'frontier_redefinition': False,
        'second_pareto_layer_evaluated': False,
        'relaxed_dominance_evaluated': False,
        'epsilon_dominance_evaluated': False,
        'identity_rescue_list_created': False,
        'oracle_identity_used_for_ranking': False,
        'truth_aware_group_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = output / 'V46_BOUNDARY_INHERITED_EVIDENCE_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panels': panel_results}, indent=2, sort_keys=True))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)

    f = sub.add_parser('freeze')
    f.add_argument('--signal-file', type=Path, required=True)
    f.add_argument('--frontier-file', type=Path, required=True)
    f.add_argument('--component-file', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)

    d = sub.add_parser('diagnose')
    d.add_argument('--freeze-file', type=Path, required=True)
    d.add_argument('--hdbscan-root', type=Path, required=True)
    d.add_argument('--truth-root', type=Path, required=True)
    d.add_argument('--output', type=Path, required=True)

    a = p.parse_args()
    if a.mode == 'freeze':
        return freeze_mode(a.signal_file, a.frontier_file, a.component_file, a.output)
    return diagnose_mode(a.freeze_file, a.hdbscan_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

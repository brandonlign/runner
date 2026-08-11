#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24

SOURCE_RUN = 31457923695
SOURCE_ARTIFACT = 9088724826
SOURCE_SIGNAL_SHA = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
AUTH_RUN = 31458734952
AUTH_ARTIFACT = 9088994714
AUTH_RESULT_SHA = '939f4288a5f0d2de84ef566bb93713da664230deb65777c422795c93fba10c6d'
GRAPH_SHA = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
HDB_N = 229
JOINT_N = 60
RECOVERY = 0.5


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def canonical_sha(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n'
    return hashlib.sha256(payload.encode()).hexdigest()


def validate_source(path: Path) -> dict[str, Any]:
    require(sha(path) == SOURCE_SIGNAL_SHA, '#1098 signal identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', '#1098 signal verdict changed')
    require(r['scientific_role'] == 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION', '#1098 signal role changed')
    require(int(r['family_count']) == HDB_N and len(r['families']) == HDB_N, '#1098 HDB universe changed')
    require(sum(bool(x['joint_signal']) for x in r['families']) == JOINT_N, '#1098 joint count changed')
    require(r['graph_sha256'] == GRAPH_SHA and r['component_sha256'] == COMPONENT_SHA, '#1098 geometry identity changed')
    for k in ('threshold_selected','top_k_selected','rank_window_selected','alternate_boolean_rule_evaluated','oracle_identity_hardcoded','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(r[k] is False, f'#1098 forbidden flag changed: {k}')
    require(r['blind_exclusion'] == [20.0, 55.0], '#1098 blind exclusion changed')
    ids: set[str] = set()
    ranks: set[int] = set()
    for x in r['families']:
        fid = str(x['family_id'])
        vr = int(x['v31_rank'])
        vp = float(x['v31_percentile'])
        cp = float(x['component_best_v31_percentile'])
        require(fid not in ids, 'duplicate #1098 family')
        require(vr not in ranks and 1 <= vr <= HDB_N, 'invalid/duplicate #1098 v31 rank')
        require(abs(vp - ((vr - 1) / (HDB_N - 1))) < 1e-15, '#1098 v31 percentile changed')
        require(0.0 <= cp <= 1.0, '#1098 component percentile invalid')
        require(bool(x['joint_signal']) == bool(x['positive_quality_suppression'] and x['component_closure_opportunity']), '#1098 Boolean changed')
        ids.add(fid); ranks.add(vr)
    return r


def validate_authorization(path: Path) -> dict[str, Any]:
    require(sha(path) == AUTH_RESULT_SHA, '#1113 result identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC', '#1113 verdict changed')
    require(r['scientific_role'] == 'POST_V42_DIAGNOSTIC_ONLY_CONDITIONAL_COMPONENT_PLACEMENT_NO_SUCCESSOR_EVALUATED', '#1113 role changed')
    require(int(r['joint_family_count']) == JOINT_N, '#1113 joint family count changed')
    require(r['source_1098_run'] == SOURCE_RUN and r['source_1098_artifact'] == SOURCE_ARTIFACT, '#1113 source provenance changed')
    require(r['source_signal_sha256'] == SOURCE_SIGNAL_SHA, '#1113 source signal changed')
    for k in ('new_rank_or_score_evaluated','selector_evaluated','replacement_rule_evaluated','successor_selected','quality_rank_placement_retry','threshold_search','top_k_search','rank_window_search','component_size_statistic_search','q_calibration_search','alternate_component_aggregation_search','suppression_magnitude_search','promotion_gain_search','route_specific_rule','year_specific_rule','budget_specific_rule','graph_or_component_redefinition','feature_search','model_search','k_search','scaling_search','diversity_search','fusion_search','source_quota_selected','oracle_identity_hardcoded','truth_aware_group_identity_used_for_ranking','post_result_second_search','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(r[k] is False, f'#1113 forbidden flag changed: {k}')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and r['blind_exclusion'] == [20.0,55.0], '#1113 firewall changed')
    return r


def freeze_mode(source_signal: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    source = validate_source(source_signal)
    joint = [x for x in source['families'] if bool(x['joint_signal'])]
    require(len(joint) == JOINT_N, 'joint set changed')
    ordered = sorted(joint, key=lambda x: (int(x['v31_rank']), str(x['family_id'])))

    best_so_far: float | None = None
    rows: list[dict[str, Any]] = []
    frontier_count = 0
    for x in ordered:
        cp = float(x['component_best_v31_percentile'])
        frontier = bool(best_so_far is None or cp < best_so_far)
        if frontier:
            frontier_count += 1
            best_so_far = cp
        rows.append({
            'family_id': str(x['family_id']),
            'v31_rank': int(x['v31_rank']),
            'v31_percentile': float(x['v31_percentile']),
            'component_best_v31_percentile': cp,
            'pareto_frontier_record': frontier,
            'frontier_record_index': frontier_count if frontier else None,
        })

    # Audit equivalence to direct Pareto nondominance in the two frozen coordinates.
    for i in rows:
        dominated = False
        for j in rows:
            if i['family_id'] == j['family_id']:
                continue
            xj, yj = float(j['v31_percentile']), float(j['component_best_v31_percentile'])
            xi, yi = float(i['v31_percentile']), float(i['component_best_v31_percentile'])
            if xj <= xi and yj <= yi and (xj < xi or yj < yi):
                dominated = True
                break
        require(bool(i['pareto_frontier_record']) == (not dominated), f"record/Pareto mismatch {i['family_id']}")

    payload = {
        'verdict': 'PASS_V31_JOINT_COMPONENT_PARETO_FRONTIER_VECTOR_FREEZE',
        'scientific_role': 'FIXED_60_JOINT_FAMILY_PARETO_FRONTIER_FROZEN_BEFORE_OUTCOME_TRUTH_OR_1113_AUTHORIZATION',
        'source_run': SOURCE_RUN,
        'source_artifact': SOURCE_ARTIFACT,
        'source_signal_sha256': SOURCE_SIGNAL_SHA,
        'family_count': HDB_N,
        'joint_family_count': JOINT_N,
        'frontier_family_count': frontier_count,
        'dominated_family_count': JOINT_N - frontier_count,
        'frontier_definition': 'Pareto nondominance minimizing (exact_v31_percentile, component_best_v31_percentile) within fixed #1098 joint-positive HDB families; equivalently strict new component-best record scanning exact-v31 rank ascending',
        'families': rows,
        'threshold_selected': False,
        'quantile_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'literature_budget_used': False,
        'second_pareto_layer_evaluated': False,
        'relaxed_dominance_evaluated': False,
        'epsilon_dominance_evaluated': False,
        'weighted_score_evaluated': False,
        'candidate_total_order_evaluated': False,
        'promotion_position_evaluated': False,
        'oracle_identity_hardcoded': False,
        'truth_aware_group_identity_used_for_frontier': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0,55.0],
    }
    csha = canonical_sha(payload)
    payload['canonical_sha256_without_self_field'] = csha
    (output / 'V31_JOINT_COMPONENT_PARETO_FRONTIER_VECTOR.json').write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': payload['verdict'], 'frontier_family_count': frontier_count, 'dominated_family_count': JOINT_N-frontier_count, 'canonical_sha256': csha}, indent=2, sort_keys=True))
    return 0


def safe_compare(frontier: list[dict[str, Any]], dominated: list[dict[str, Any]]) -> dict[str, Any]:
    if not frontier or not dominated:
        return {
            'comparison_defined': False,
            'frontier_count': len(frontier),
            'dominated_count': len(dominated),
            'frontier_recoverable_count': sum(bool(r['recoverable']) for r in frontier),
            'dominated_recoverable_count': sum(bool(r['recoverable']) for r in dominated),
            'frontier_recoverable_fraction': None if not frontier else float(sum(bool(r['recoverable']) for r in frontier)/len(frontier)),
            'dominated_recoverable_fraction': None if not dominated else float(sum(bool(r['recoverable']) for r in dominated)/len(dominated)),
            'direction_pass': False,
        }
    fr = sum(bool(r['recoverable']) for r in frontier)
    dr = sum(bool(r['recoverable']) for r in dominated)
    pf = float(fr/len(frontier)); pd = float(dr/len(dominated))
    return {
        'comparison_defined': True,
        'frontier_count': len(frontier),
        'dominated_count': len(dominated),
        'frontier_recoverable_count': fr,
        'dominated_recoverable_count': dr,
        'frontier_recoverable_fraction': pf,
        'dominated_recoverable_fraction': pd,
        'frontier_minus_dominated_fraction': float(pf-pd),
        'direction_pass': bool(pf > pd),
    }


def audit_mode(vector: Path, authorization: Path, hdb_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    v = json.loads(vector.read_text())
    require(v['verdict'] == 'PASS_V31_JOINT_COMPONENT_PARETO_FRONTIER_VECTOR_FREEZE', 'frontier vector verdict changed')
    require(v['scientific_role'] == 'FIXED_60_JOINT_FAMILY_PARETO_FRONTIER_FROZEN_BEFORE_OUTCOME_TRUTH_OR_1113_AUTHORIZATION', 'frontier vector role changed')
    require(int(v['family_count']) == HDB_N and int(v['joint_family_count']) == JOINT_N and len(v['families']) == JOINT_N, 'frontier vector universe changed')
    frontier_count = int(v['frontier_family_count']); dominated_count = int(v['dominated_family_count'])
    require(frontier_count + dominated_count == JOINT_N, 'frontier partition changed')
    require(1 <= frontier_count <= JOINT_N, 'frontier count invalid')
    validate_authorization(authorization)

    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((hdb_root / 'family_memberships.json').read_text())
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, 'HDB payload not pretruth')
    ids = list(map(str, meta['family_ids']))
    fams = list(fp['families'])
    require(len(ids) == HDB_N and [str(x['family_id']) for x in fams] == ids, 'HDB family identity changed')
    require(meta['target_information_access'] is False and meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, 'HDB firewall changed')

    by = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013,2014)}
    eligible = v22.eligible_from_year_truth(by)
    hidden: dict[str, Any] = {}
    hidden.update(by[2013]); hidden.update(by[2014])
    flag = {str(r['family_id']): bool(r['pareto_frontier_record']) for r in v['families']}
    require(set(flag).issubset(set(ids)) and len(flag) == JOINT_N, 'frontier family ids mismatch HDB payload')

    truth_rows: list[dict[str, Any]] = []
    for fid, fam in zip(ids, fams):
        if fid not in flag:
            continue
        t = v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v24.annual_f1_for_fixed_label(fam, str(label), by))
            group = 'SHOWER/' + str(label)
        else:
            f13 = f14 = 0.0
            group = 'NEG/' + fid
        truth_rows.append({
            'family_id': fid,
            'diagnostic_group': group,
            'frontier': flag[fid],
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
        })
    require(len(truth_rows) == JOINT_N, 'truth rows changed joint population')

    annual: dict[str, Any] = {}
    gates: list[bool] = []
    for year in (2013,2014):
        rk = f'recoverable_{year}'
        fr = [{'recoverable': bool(r[rk])} for r in truth_rows if r['frontier']]
        dr = [{'recoverable': bool(r[rk])} for r in truth_rows if not r['frontier']]
        famcmp = safe_compare(fr, dr)

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in truth_rows:
            grouped[str(r['diagnostic_group'])].append(r)
        fg: list[dict[str, Any]] = []
        dg: list[dict[str, Any]] = []
        for group, rows in sorted(grouped.items()):
            frontier_members = [r for r in rows if r['frontier']]
            dominated_members = [r for r in rows if not r['frontier']]
            if frontier_members:
                fg.append({'diagnostic_group': group, 'recoverable': bool(any(bool(r[rk]) for r in frontier_members)), 'selected_family_count': len(frontier_members)})
            else:
                require(dominated_members, 'empty joint-positive group')
                dg.append({'diagnostic_group': group, 'recoverable': bool(any(bool(r[rk]) for r in dominated_members)), 'selected_family_count': len(dominated_members)})
        grpcmp = safe_compare(fg, dg)
        gate = bool(famcmp['direction_pass'] and grpcmp['direction_pass'])
        gates.append(gate)
        annual[str(year)] = {
            'family_level': famcmp,
            'diagnostic_group_level': grpcmp,
            'interpretation_gate_pass': gate,
        }

    breadth = bool(1 <= frontier_count < JOINT_N)
    passed = bool(breadth and all(gates))
    result = {
        'verdict': 'PASS_V31_JOINT_COMPONENT_PARETO_FRONTIER_DIAGNOSTIC' if passed else 'FAIL_V31_JOINT_COMPONENT_PARETO_FRONTIER_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_THRESHOLD_FREE_PRIORITY_STRUCTURE_DIAGNOSTIC_NO_ORDER_OR_SUCCESSOR_EVALUATED',
        'source_run': SOURCE_RUN,
        'source_artifact': SOURCE_ARTIFACT,
        'source_signal_sha256': SOURCE_SIGNAL_SHA,
        'authorization_run': AUTH_RUN,
        'authorization_artifact': AUTH_ARTIFACT,
        'authorization_result_sha256': AUTH_RESULT_SHA,
        'family_count': HDB_N,
        'joint_family_count': JOINT_N,
        'frontier_family_count': frontier_count,
        'dominated_family_count': dominated_count,
        'strict_nonempty_frontier_subset': breadth,
        'frontier_priority_supported_both_years_both_levels': passed,
        'annual_diagnostics': annual,
        'new_rank_or_score_evaluated': False,
        'candidate_total_order_evaluated': False,
        'selector_order_evaluated': False,
        'promotion_position_evaluated': False,
        'replacement_rule_evaluated': False,
        'literature_panel_evaluated': False,
        'successor_selected': False,
        'threshold_search': False,
        'quantile_search': False,
        'effect_size_threshold_selected': False,
        'top_k_search': False,
        'rank_window_search': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'second_pareto_layer_evaluated': False,
        'relaxed_dominance_evaluated': False,
        'epsilon_dominance_evaluated': False,
        'weighted_score_evaluated': False,
        'alternate_component_statistic_search': False,
        'component_size_search': False,
        'q_calibration_search': False,
        'graph_or_component_redefinition': False,
        'feature_search': False,
        'model_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'oracle_identity_hardcoded': False,
        'truth_aware_group_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0,55.0],
    }
    (output / 'V31_JOINT_COMPONENT_PARETO_FRONTIER_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    f = sub.add_parser('freeze')
    f.add_argument('--source-signal', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('audit')
    a.add_argument('--vector', type=Path, required=True)
    a.add_argument('--authorization', type=Path, required=True)
    a.add_argument('--hdb-root', type=Path, required=True)
    a.add_argument('--truth-root', type=Path, required=True)
    a.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.mode == 'freeze':
        return freeze_mode(args.source_signal, args.output)
    return audit_mode(args.vector, args.authorization, args.hdb_root, args.truth_root, args.output)


if __name__ == '__main__':
    raise SystemExit(main())

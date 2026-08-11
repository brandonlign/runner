#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from orbittrace_v42_quality_component_gated_rescue_v1 import train_evaluate as v42

v40 = v42.v40

VARIANT = 'adjacent_consensus_dominance_correction_v1'
PROTOCOL_BLOB = 'cf98ab87f54b79d25c2f57f8df324928ca43ca79'
SIGNAL_SHA = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
AUTH1139_SHA = 'c372b4aac0547198cb6ac4239d604fddc12fdd0f11a930ab39a1e46d01f5e461'
V48_FREEZE_SHA = '295d2392838d841c441ce164351e426b3efbbe7be487877b4cf3f914a64c7351'
V31_HDB_SHA = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'
V49_HDB_SHA = '6344a7a4abd67698cd32d17d3183c482b7e8954f6923e0c255a04f7d231af819'
HDB_N = 229
SUGAR_N = 267
JOINT_N = 60
EXPECTED_SWAPS = 35
EXPECTED_MOVED = 50
EXPECTED_UP = 20
EXPECTED_DOWN = 30
EXPECTED_MAX_UP = 6
EXPECTED_MAX_DOWN = 3

_ORIG_BUILD = v42.build_v42_order
_V49_ORDER: list[str] = []
_V31_ORDER: list[str] = []
_SIGNAL_ROWS: dict[str, dict[str, Any]] = {}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256('\n'.join(map(str, order)).encode()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256((json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()


def load_signal(path: Path) -> dict[str, Any]:
    require(sha(path) == SIGNAL_SHA, '#1098 signal identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', '#1098 verdict changed')
    require(r['scientific_role'] == 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION', '#1098 role changed')
    require(int(r['family_count']) == HDB_N and len(r['families']) == HDB_N, '#1098 HDB universe changed')
    require(sum(bool(x['joint_signal']) for x in r['families']) == JOINT_N, '#1098 joint population changed')
    require(r['graph_sha256'] == v40.GRAPH_SHA256 and r['component_sha256'] == v40.COMPONENT_SHA256, '#1098 geometry changed')
    for k in ('threshold_selected', 'top_k_selected', 'rank_window_selected', 'alternate_boolean_rule_evaluated', 'oracle_identity_hardcoded', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(r[k] is False, f'#1098 forbidden flag set: {k}')
    require(r['blind_exclusion'] == [20.0, 55.0], '#1098 blind exclusion changed')
    return r


def validate_1139(path: Path) -> None:
    require(sha(path) == AUTH1139_SHA, '#1139 result identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V46_JOINT_INHERITANCE_GAP_DIAGNOSTIC', '#1139 verdict changed')
    require(r['scientific_role'] == 'POST_V46_DIAGNOSTIC_ONLY_JOINT_INHERITANCE_GAP_NO_SUCCESSOR_EVALUATED', '#1139 role changed')
    require(r['joint_family_count'] == JOINT_N and r['direction_supported_both_years'] is True, '#1139 mechanism direction changed')
    for y in ('2013', '2014'):
        a = r['annual_diagnostics'][y]
        require(a['direction_pass'] is True, f'#1139 {y} direction changed')
        require(float(a['recoverable']['median_inheritance_gap']) < float(a['nonrecoverable']['median_inheritance_gap']), f'#1139 {y} median direction changed')
    for k in ('new_rank_or_score_evaluated', 'selector_evaluated', 'replacement_rule_evaluated', 'successor_selected', 'threshold_search', 'quantile_search', 'top_k_search', 'rank_window_search', 'alternate_statistic_search', 'alternate_direction_test', 'pairwise_dominance_evaluated', 'boundary_identity_used', 'boundary_rescue_list_created', 'post_result_second_search', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(r[k] is False, f'#1139 forbidden flag set: {k}')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and r['blind_exclusion'] == [20.0, 55.0], '#1139 firewall changed')


def validate_v48_pretruth_freeze(path: Path) -> None:
    require(sha(path) == V48_FREEZE_SHA, 'v48 pretruth order-freeze identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V48_SELF_SUPPORTED_ORDER_FREEZE', 'v48 freeze verdict changed')
    require(r['scientific_role'] == 'V48_COMPLETE_HDB_ORDER_FROZEN_BEFORE_OUTCOME_TRUTH', 'v48 freeze role changed')
    require(r['truth_accessed'] is False and r['literature_budget_used'] is False, 'v48 structural authorizer not pretruth')
    require(r['hdb_family_count'] == HDB_N and r['joint_positive_candidate_count'] == JOINT_N and r['self_supported_candidate_count'] == 35, 'v48 frozen counts changed')
    require(r['moved_candidate_count'] == 225, 'v48 frozen cascade count changed')
    require(r['v31_hdb_order_sha256'] == V31_HDB_SHA, 'v48 parent order identity changed')
    require(r['v48_hdb_order_sha256'] == '62041ea9f6e094471a7decf02c71491fc553e93af86a655e21bf1035d0904db6', 'v48 order identity changed')
    for k in ('threshold_selected', 'top_k_selected', 'rank_window_selected', 'coefficient_selected', 'oracle_identity_used_for_ranking', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(r[k] is False, f'v48 freeze forbidden flag set: {k}')
    require(r['blind_exclusion'] == [20.0, 55.0], 'v48 freeze firewall changed')


def derive_v49(signal: dict[str, Any]) -> tuple[list[str], list[str], list[dict[str, Any]], dict[str, Any]]:
    rows = {str(x['family_id']): x for x in signal['families']}
    require(len(rows) == HDB_N, 'duplicate #1098 family identity')
    base = [str(x['family_id']) for x in sorted(signal['families'], key=lambda x: (int(x['v31_rank']), str(x['family_id'])))]
    require([int(rows[f]['v31_rank']) for f in base] == list(range(1, HDB_N + 1)), 'exact v31 ranks not a permutation')
    require(order_sha(base) == V31_HDB_SHA, 'exact v31 order identity changed')

    order = list(base)
    swaps: list[dict[str, Any]] = []
    i = 1
    while i < len(order):
        aid = str(order[i])
        bid = str(order[i - 1])
        a = rows[aid]
        b = rows[bid]
        qa = float(a['quality_percentile'])
        qb = float(b['quality_percentile'])
        ca = float(a['component_best_v31_percentile'])
        cb = float(b['component_best_v31_percentile'])
        allow = bool(
            bool(a['joint_signal'])
            and qa <= qb
            and ca <= cb
            and (qa < qb or ca < cb)
        )
        if allow:
            swaps.append({
                'mover_family_id': aid,
                'crossed_family_id': bid,
                'mover_quality_percentile': qa,
                'crossed_quality_percentile': qb,
                'mover_component_best_v31_percentile': ca,
                'crossed_component_best_v31_percentile': cb,
            })
            order[i - 1], order[i] = order[i], order[i - 1]
            i = max(1, i - 1)
        else:
            i += 1

    require(order_sha(order) == V49_HDB_SHA, 'v49 truth-blind order identity changed')
    old = {f: i + 1 for i, f in enumerate(base)}
    new = {f: i + 1 for i, f in enumerate(order)}
    moved = [f for f in base if old[f] != new[f]]
    up = [f for f in moved if new[f] < old[f]]
    down = [f for f in moved if new[f] > old[f]]
    stats = {
        'adjacent_swap_count': len(swaps),
        'moved_candidate_count': len(moved),
        'moved_up_count': len(up),
        'moved_down_count': len(down),
        'unchanged_count': HDB_N - len(moved),
        'maximum_upward_displacement': max((old[f] - new[f] for f in up), default=0),
        'maximum_downward_displacement': max((new[f] - old[f] for f in down), default=0),
    }
    require(stats['adjacent_swap_count'] == EXPECTED_SWAPS, 'v49 swap count changed')
    require(stats['moved_candidate_count'] == EXPECTED_MOVED, 'v49 moved count changed')
    require(stats['moved_up_count'] == EXPECTED_UP and stats['moved_down_count'] == EXPECTED_DOWN, 'v49 movement direction counts changed')
    require(stats['maximum_upward_displacement'] == EXPECTED_MAX_UP and stats['maximum_downward_displacement'] == EXPECTED_MAX_DOWN, 'v49 displacement extrema changed')

    candidate_rows = []
    for fid in base:
        r = rows[fid]
        candidate_rows.append({
            'family_id': fid,
            'v31_rank': old[fid],
            'v49_rank': new[fid],
            'v49_rank_delta': old[fid] - new[fid],
            'joint_signal': bool(r['joint_signal']),
            'quality_rank': int(r['quality_rank']),
            'quality_percentile': float(r['quality_percentile']),
            'component_best_v31_percentile': float(r['component_best_v31_percentile']),
            'v31_percentile': float(r['v31_percentile']),
        })
    return base, order, swaps, {'stats': stats, 'candidate_rows': candidate_rows}


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    return v42.pretruth_mode(sugar_root, hdbscan_root, output)


def freeze_order_mode(signal_file: Path, author1139: Path, v48_freeze: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    signal = load_signal(signal_file)
    validate_1139(author1139)
    validate_v48_pretruth_freeze(v48_freeze)
    base, order, swaps, d = derive_v49(signal)
    payload: dict[str, Any] = {
        'verdict': 'PASS_V49_ADJACENT_CONSENSUS_DOMINANCE_ORDER_FREEZE',
        'scientific_role': 'COMPLETE_V49_HDB_ORDER_FROZEN_BEFORE_CURRENT_OUTCOME_TRUTH',
        'source_1098_run': 31457923695,
        'source_1098_artifact': 9088724826,
        'source_1098_signal_sha256': SIGNAL_SHA,
        'authorizing_1139_run': 31488131546,
        'authorizing_1139_artifact': 9099927842,
        'authorizing_1139_result_sha256': AUTH1139_SHA,
        'structural_v48_freeze_artifact': 9100509632,
        'structural_v48_freeze_sha256': V48_FREEZE_SHA,
        'hdb_family_count': HDB_N,
        'joint_positive_candidate_count': JOINT_N,
        'pairwise_rule': 'current lower family A swaps upward one adjacent position across B iff A is #1098 joint-positive, A.quality_percentile <= B.quality_percentile, A.component_best_v31_percentile <= B.component_best_v31_percentile, and at least one inequality is strict; after swap scan pointer steps back one',
        'v31_hdb_order': base,
        'v31_hdb_order_sha256': V31_HDB_SHA,
        'v49_hdb_order': order,
        'v49_hdb_order_sha256': V49_HDB_SHA,
        'adjacent_swaps': swaps,
        **d['stats'],
        'candidate_rows': d['candidate_rows'],
        'truth_accessed': False,
        'literature_budget_used': False,
        'absolute_auxiliary_rank_used': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'swap_distance_cap_selected': False,
        'alternate_pairwise_rule_evaluated': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    payload['canonical_sha256_without_self_field'] = canonical_sha(payload)
    p = output / 'V49_ADJACENT_CONSENSUS_DOMINANCE_ORDER_FREEZE.json'
    p.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': payload['verdict'], 'v49_hdb_order_sha256': V49_HDB_SHA, **d['stats'], 'file_sha256': sha(p), 'canonical_sha256_without_self_field': payload['canonical_sha256_without_self_field']}, indent=2, sort_keys=True))
    return 0


def build_v49_order(route: str, base_order: list[str], components: list[dict[str, Any]], rank_maps: dict[str, dict[str, int]]):
    order, rows = _ORIG_BUILD(route, base_order, components, rank_maps)
    if route == 'sugar':
        return order, rows
    require(list(map(str, base_order)) == _V31_ORDER, 'runtime v31 order differs from pretruth v49 freeze')
    by = {str(r['family_id']): r for r in rows}
    require(set(by) == set(_SIGNAL_ROWS) == set(_V31_ORDER), 'runtime v49 family universe changed')
    for fid in _V31_ORDER:
        a = by[fid]
        b = _SIGNAL_ROWS[fid]
        require(bool(a['joint_gate']) == bool(b['joint_signal']), f'joint gate changed for {fid}')
        require(int(a['quality_rank']) == int(b['quality_rank']), f'quality rank changed for {fid}')
        require(abs(float(a['v31_percentile']) - float(b['v31_percentile'])) < 1e-15, f'v31 percentile changed for {fid}')
        require(abs(float(a['component_best_v31_percentile']) - float(b['component_best_v31_percentile'])) < 1e-15, f'component-best percentile changed for {fid}')
    nr = {fid: i + 1 for i, fid in enumerate(_V49_ORDER)}
    for r in rows:
        fid = str(r['family_id'])
        r['v42_rank'] = nr[fid]
        r['v49_rank'] = nr[fid]
        r['v49_rank_delta'] = int(r['v31_rank']) - nr[fid]
    return list(_V49_ORDER), rows


def evaluate_mode(sugar_root: Path, hdbscan_root: Path, truth_root: Path, ranker_source: Path, graph_file: Path, component_file: Path, author1091: Path, signal_file: Path, author1139: Path, v48_freeze: Path, frozen_order: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    signal = load_signal(signal_file)
    validate_1139(author1139)
    validate_v48_pretruth_freeze(v48_freeze)
    f = json.loads(frozen_order.read_text())
    require(f['verdict'] == 'PASS_V49_ADJACENT_CONSENSUS_DOMINANCE_ORDER_FREEZE', 'v49 order-freeze verdict changed')
    require(f['scientific_role'] == 'COMPLETE_V49_HDB_ORDER_FROZEN_BEFORE_CURRENT_OUTCOME_TRUTH', 'v49 order-freeze role changed')
    require(f['source_1098_signal_sha256'] == SIGNAL_SHA and f['authorizing_1139_result_sha256'] == AUTH1139_SHA and f['structural_v48_freeze_sha256'] == V48_FREEZE_SHA, 'v49 order-freeze provenance changed')
    require(f['v31_hdb_order_sha256'] == V31_HDB_SHA and f['v49_hdb_order_sha256'] == V49_HDB_SHA, 'v49 order-freeze identity changed')
    require(order_sha(list(map(str, f['v31_hdb_order']))) == V31_HDB_SHA and order_sha(list(map(str, f['v49_hdb_order']))) == V49_HDB_SHA, 'v49 serialized order hash changed')
    require(f['adjacent_swap_count'] == EXPECTED_SWAPS and f['moved_candidate_count'] == EXPECTED_MOVED and f['moved_up_count'] == EXPECTED_UP and f['moved_down_count'] == EXPECTED_DOWN, 'v49 structural counts changed')
    require(f['maximum_upward_displacement'] == EXPECTED_MAX_UP and f['maximum_downward_displacement'] == EXPECTED_MAX_DOWN, 'v49 displacement extrema changed')
    require(f['truth_accessed'] is False and f['literature_budget_used'] is False and f['absolute_auxiliary_rank_used'] is False, 'v49 order freeze not outcome-independent')

    global _V31_ORDER, _V49_ORDER, _SIGNAL_ROWS
    _V31_ORDER = list(map(str, f['v31_hdb_order']))
    _V49_ORDER = list(map(str, f['v49_hdb_order']))
    _SIGNAL_ROWS = {str(x['family_id']): x for x in signal['families']}

    engine = output / '_frozen_v42_engine'
    original_builder = v42.build_v42_order
    original_variant = v42.VARIANT
    v42.build_v42_order = build_v49_order
    v42.VARIANT = VARIANT
    try:
        rc = v42.evaluate_mode(sugar_root, hdbscan_root, truth_root, ranker_source, graph_file, component_file, author1091, engine)
    finally:
        v42.build_v42_order = original_builder
        v42.VARIANT = original_variant
    require(rc == 0, 'frozen v42/v31 evaluation engine failed')

    rp = engine / 'V42_QUALITY_COMPONENT_GATED_RESCUE_RESULT.json'
    require(rp.is_file(), 'v49 engine result missing')
    raw = json.loads(rp.read_text())
    require(raw['parent_v31_reproduction_pass'] is True and len(raw['parent_v31_controls']) == 4, 'exact v31 controls failed')
    require(raw['pretruth_graph_sha256'] == v40.GRAPH_SHA256 and raw['pretruth_component_sha256'] == v40.COMPONENT_SHA256, 'v49 geometry changed')
    require(raw['order_diagnostics']['sugar']['exact_v31_unchanged'] is True, 'Sugar changed')
    require(raw['order_diagnostics']['hdbscan']['v31_order_sha256'] == V31_HDB_SHA, 'runtime parent HDB order changed')
    require(raw['order_diagnostics']['hdbscan']['v42_total_order_sha256'] == V49_HDB_SHA, 'runtime v49 HDB order differs from pretruth freeze')
    require(int(raw['joint_positive_candidate_count']) == JOINT_N, 'runtime joint population changed')

    panels = list(raw['panels'])
    wins = sum(bool(x['superiority_pair_pass']) for x in panels)
    require(wins == int(raw['panel_wins']), 'panel win count mismatch')
    passed = wins == 4

    freeze: dict[str, Any] = {'verdict': 'NOT_FROZEN_V49_ADJACENT_CONSENSUS_DOMINANCE_FAIL', 'reference_sha256': None}
    engine_ref = engine / 'v42_quality_component_gated_rescue_reference.npz'
    if passed:
        require(engine_ref.is_file(), 'passing reference missing')
        dst = output / 'v49_adjacent_consensus_dominance_reference.npz'
        shutil.copyfile(engine_ref, dst)
        freeze = {
            'verdict': 'PASS_V49_FULL_EXPOSED_ADJACENT_CONSENSUS_DOMINANCE_REFERENCE_FREEZE',
            'reference_sha256': v40.v22.sha(dst),
            'pretruth_graph_sha256': v40.GRAPH_SHA256,
            'pretruth_component_sha256': v40.COMPONENT_SHA256,
            'v31_hdb_order_sha256': V31_HDB_SHA,
            'v49_hdb_order_sha256': V49_HDB_SHA,
            'pairwise_rule': f['pairwise_rule'],
            'sugar_rule': 'exact v31 unchanged',
            'in_sample_reference_score_used_for_promotion': False,
        }
    (output / 'V49_ADJACENT_CONSENSUS_DOMINANCE_MODEL_FREEZE.json').write_text(json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n')

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V49_ADJACENT_CONSENSUS_DOMINANCE_V1',
        'verdict': 'PASS_V49_ADJACENT_CONSENSUS_DOMINANCE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V49_ADJACENT_CONSENSUS_DOMINANCE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'starting from exact v31 HDB order, permit only adjacent upward swaps initiated by exact #1098 joint-positive families that Pareto-dominate the immediate predecessor in both immutable quality and component-best percentiles; Sugar exact v31 unchanged',
        'pre_result_frozen_protocol_blob': PROTOCOL_BLOB,
        'source_1098_signal_sha256': SIGNAL_SHA,
        'authorizing_1091_run': 31456963941,
        'authorizing_1091_artifact': 9088402091,
        'authorizing_1139_run': 31488131546,
        'authorizing_1139_artifact': 9099927842,
        'authorizing_1139_result_sha256': AUTH1139_SHA,
        'structural_v48_freeze_artifact': 9100509632,
        'structural_v48_freeze_sha256': V48_FREEZE_SHA,
        'pretruth_graph_sha256': v40.GRAPH_SHA256,
        'pretruth_component_sha256': v40.COMPONENT_SHA256,
        'v31_hdb_order_sha256': V31_HDB_SHA,
        'v49_hdb_order_sha256': V49_HDB_SHA,
        'joint_positive_candidate_count': JOINT_N,
        'adjacent_swap_count': EXPECTED_SWAPS,
        'moved_candidate_count': EXPECTED_MOVED,
        'moved_up_count': EXPECTED_UP,
        'moved_down_count': EXPECTED_DOWN,
        'maximum_upward_displacement': EXPECTED_MAX_UP,
        'maximum_downward_displacement': EXPECTED_MAX_DOWN,
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': raw['parent_v31_controls'],
        'feature_dimension': raw['feature_dimension'],
        'recovery_f1_threshold': raw['recovery_f1_threshold'],
        'nearest_k': raw['nearest_k'],
        'v31_distance': raw['v31_distance'],
        'v31_annual_margin': raw['v31_annual_margin'],
        'v31_annual_combiner': raw['v31_annual_combiner'],
        'sugar_rule': 'exact v31 unchanged',
        'hdb_pairwise_rule': f['pairwise_rule'],
        'panel_wins': wins,
        'panels': panels,
        'fold_diagnostics': raw['fold_diagnostics'],
        'hdb_candidate_rows': raw['hdb_candidate_rows'],
        'full_model_freeze': freeze,
        'absolute_quality_rank_placement': False,
        'absolute_component_placement': False,
        'inheritance_gap_placement': False,
        'threshold_search': False,
        'quantile_search': False,
        'epsilon_search': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'swap_distance_cap_selected': False,
        'alternate_scan_order_search': False,
        'alternate_dominance_dimensions_search': False,
        'one_signal_swap_evaluated': False,
        'or_rule_evaluated': False,
        'coefficient_search': False,
        'interpolation_search': False,
        'bonus_or_cap_search': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'sugar_modified': False,
        'radius_search': False,
        'metric_search': False,
        'graph_pruning': False,
        'graph_expansion': False,
        'component_definition_search': False,
        'candidate_generation_changed': False,
        'candidate_membership_changed': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
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
    (output / 'V49_ADJACENT_CONSENSUS_DOMINANCE_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    shutil.rmtree(engine)
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels, 'v49_hdb_order_sha256': V49_HDB_SHA, 'full_model_freeze': freeze}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('pretruth')
    a.add_argument('--sugar-root', type=Path, required=True)
    a.add_argument('--hdbscan-root', type=Path, required=True)
    a.add_argument('--output', type=Path, required=True)
    f = sub.add_parser('freeze-order')
    f.add_argument('--signal-file', type=Path, required=True)
    f.add_argument('--authorizing-1139', type=Path, required=True)
    f.add_argument('--v48-freeze', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    e = sub.add_parser('evaluate')
    e.add_argument('--sugar-root', type=Path, required=True)
    e.add_argument('--hdbscan-root', type=Path, required=True)
    e.add_argument('--truth-root', type=Path, required=True)
    e.add_argument('--ranker-source', type=Path, required=True)
    e.add_argument('--graph-file', type=Path, required=True)
    e.add_argument('--component-file', type=Path, required=True)
    e.add_argument('--authorizing-1091', type=Path, required=True)
    e.add_argument('--signal-file', type=Path, required=True)
    e.add_argument('--authorizing-1139', type=Path, required=True)
    e.add_argument('--v48-freeze', type=Path, required=True)
    e.add_argument('--frozen-order', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    x = p.parse_args()
    if x.mode == 'pretruth':
        return pretruth_mode(x.sugar_root, x.hdbscan_root, x.output)
    if x.mode == 'freeze-order':
        return freeze_order_mode(x.signal_file, x.authorizing_1139, x.v48_freeze, x.output)
    return evaluate_mode(x.sugar_root, x.hdbscan_root, x.truth_root, x.ranker_source, x.graph_file, x.component_file, x.authorizing_1091, x.signal_file, x.authorizing_1139, x.v48_freeze, x.frozen_order, x.output)


if __name__ == '__main__':
    raise SystemExit(main())

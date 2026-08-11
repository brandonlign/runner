#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v42_quality_component_gated_rescue_v1 import train_evaluate as v42

VARIANT = 'joint_gated_component_best_placement_v1'
PLACEMENT_RUN = 31458734952
PLACEMENT_ARTIFACT = 9088994714
PLACEMENT_DIGEST = 'sha256:5bddfbe4abda60006757561d4c6477102317e02f5fb9555330e0b62eaf3353df'
PLACEMENT_RESULT_SHA = '939f4288a5f0d2de84ef566bb93713da664230deb65777c422795c93fba10c6d'
HDB_N = 229
SUGAR_N = 267


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def validate_placement_authorizer(path: Path) -> None:
    require(v42.v40.v22.sha(path) == PLACEMENT_RESULT_SHA, '#1113 placement result identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC', '#1113 verdict changed')
    require(r['scientific_role'] == 'POST_V42_DIAGNOSTIC_ONLY_CONDITIONAL_COMPONENT_PLACEMENT_NO_SUCCESSOR_EVALUATED', '#1113 role changed')
    require(r['joint_family_count'] == 60, '#1113 joint population changed')
    require(r['placement_statistic'] == 'component_best_v31_percentile from frozen #1098 signal; lower is better', '#1113 placement statistic changed')
    require(r['placement_direction_supported_both_years_both_levels'] is True, '#1113 placement direction not supported')
    require(r['source_signal_sha256'] == 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07', '#1113 source joint signal changed')
    for year in ('2013', '2014'):
        require(r['annual_diagnostics'][year]['family_level']['direction_pass'] is True, f'#1113 family direction failed {year}')
        require(r['annual_diagnostics'][year]['diagnostic_group_level']['direction_pass'] is True, f'#1113 group direction failed {year}')
    for k in (
        'new_rank_or_score_evaluated', 'selector_evaluated', 'replacement_rule_evaluated', 'successor_selected',
        'quality_rank_placement_retry', 'threshold_search', 'top_k_search', 'rank_window_search',
        'component_size_statistic_search', 'q_calibration_search', 'alternate_component_aggregation_search',
        'suppression_magnitude_search', 'promotion_gain_search', 'route_specific_rule', 'year_specific_rule',
        'budget_specific_rule', 'graph_or_component_redefinition', 'feature_search', 'model_search', 'k_search',
        'scaling_search', 'diversity_search', 'fusion_search', 'source_quota_selected', 'oracle_identity_hardcoded',
        'truth_aware_group_identity_used_for_ranking', 'post_result_second_search', 'target_information_access',
        'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access',
    ):
        require(r[k] is False, f'#1113 forbidden flag changed: {k}')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and r['blind_exclusion'] == [20.0, 55.0], '#1113 firewall changed')


def build_v44_order(
    route: str,
    base_order: list[str],
    components: list[dict[str, Any]],
    rank_maps: dict[str, dict[str, int]],
) -> tuple[list[str], list[dict[str, Any]]]:
    require(route in ('sugar', 'hdbscan'), 'invalid route')
    if route == 'sugar':
        rows = [
            {
                'representative_family_id': str(fid),
                'family_id': str(fid),
                'v31_rank': i + 1,
                'v31_percentile': float(i / (SUGAR_N - 1)),
                'joint_gate': False,
                'sugar_unchanged': True,
                'v44_key': float(i / (SUGAR_N - 1)),
            }
            for i, fid in enumerate(base_order)
        ]
        return list(map(str, base_order)), rows

    require(len(base_order) == HDB_N, 'HDB family count changed')
    require(len(v42._QUALITY_RANK) == HDB_N and set(base_order) == set(v42._QUALITY_RANK), 'immutable quality-rank map unavailable')
    vrank = rank_maps['hdbscan']
    component_best = v42.component_best_percentiles(components, rank_maps)
    hdb_component: dict[str, str] = {}
    for c in components:
        cid = str(c['component_id'])
        for fid in map(str, c['hdbscan_family_ids']):
            require(fid not in hdb_component, 'HDB family occurs in multiple components')
            hdb_component[fid] = cid
    require(set(hdb_component) == set(base_order), 'HDB component assignment incomplete')

    rows: list[dict[str, Any]] = []
    for fid0 in base_order:
        fid = str(fid0)
        rv = int(vrank[fid])
        rq = int(v42._QUALITY_RANK[fid])
        ph = float((rv - 1) / (HDB_N - 1))
        cid = hdb_component[fid]
        pc = float(component_best[cid])
        require(np.isfinite(ph) and np.isfinite(pc), 'nonfinite v44 percentile')
        quality_suppressed = bool(rq < rv)
        component_opportunity = bool(pc < ph)
        joint = bool(quality_suppressed and component_opportunity)
        key = float(pc if joint else ph)
        rows.append({
            'representative_family_id': fid,
            'family_id': fid,
            'component_id': cid,
            'v31_rank': rv,
            'quality_rank': rq,
            'v31_percentile': ph,
            'component_best_v31_percentile': pc,
            'quality_suppressed': quality_suppressed,
            'component_opportunity': component_opportunity,
            'joint_gate': joint,
            'v44_key': key,
            # compatibility-only field for the frozen v42 wrapper; value is the v44 key, not v42 quality rank.
            'v42_key': key,
        })

    by_id = {str(r['family_id']): r for r in rows}
    order = sorted(
        map(str, base_order),
        key=lambda fid: (
            float(by_id[fid]['v44_key']),
            float(by_id[fid]['v31_percentile']),
            fid,
        ),
    )
    require(len(order) == HDB_N and set(order) == set(base_order), 'invalid v44 HDB total order')
    new_rank = {fid: i + 1 for i, fid in enumerate(order)}
    for r in rows:
        fid = str(r['family_id'])
        r['v42_rank'] = int(new_rank[fid])  # frozen v42 wrapper compatibility only
        r['v44_rank'] = int(new_rank[fid])
        r['promotion_rank_gain'] = int(r['v31_rank'] - r['v44_rank']) if bool(r['joint_gate']) else 0
    return order, rows


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    return v42.pretruth_mode(sugar_root, hdbscan_root, output)


def evaluate_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    component_file: Path,
    joint_authorizer: Path,
    placement_authorizer: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    validate_placement_authorizer(placement_authorizer)
    require(v42.v40.v22.sha(graph_file) == v42.v40.GRAPH_SHA256, 'pretruth graph identity changed')
    require(v42.v40.v22.sha(component_file) == v42.v40.COMPONENT_SHA256, 'pretruth component identity changed')

    engine = output / '_frozen_v42_engine'
    engine.mkdir(parents=True, exist_ok=True)
    original_builder = v42.build_v42_order
    original_variant = v42.VARIANT
    v42.build_v42_order = build_v44_order
    v42.VARIANT = VARIANT
    try:
        rc = v42.evaluate_mode(
            sugar_root,
            hdbscan_root,
            truth_root,
            ranker_source,
            graph_file,
            component_file,
            joint_authorizer,
            engine,
        )
    finally:
        v42.build_v42_order = original_builder
        v42.VARIANT = original_variant
    require(rc == 0, 'frozen v42 execution wrapper failed')

    raw_path = engine / 'V42_QUALITY_COMPONENT_GATED_RESCUE_RESULT.json'
    require(raw_path.is_file(), 'wrapped evaluator result missing')
    raw = json.loads(raw_path.read_text())
    require(raw['parent_v31_reproduction_pass'] is True and len(raw['parent_v31_controls']) == 4, 'exact v31 controls failed')
    require(raw['pretruth_graph_sha256'] == v42.v40.GRAPH_SHA256 and raw['pretruth_component_sha256'] == v42.v40.COMPONENT_SHA256, 'frozen geometry changed')
    require(int(raw['joint_positive_candidate_count']) == 60, 'v44 joint-positive count changed from frozen gate')
    require(raw['sugar_modified'] is False and raw['sugar_rule'] == 'exact v31 unchanged', 'Sugar changed')

    hdb_rows = list(raw['hdb_candidate_rows'])
    require(len(hdb_rows) == HDB_N, 'v44 HDB row count changed')
    require(sum(bool(r['joint_gate']) for r in hdb_rows) == 60, 'v44 joint row count changed')
    require(all('v44_key' in r and 'v44_rank' in r for r in hdb_rows), 'v44 candidate rows missing placement fields')
    for r in hdb_rows:
        expected = float(r['component_best_v31_percentile'] if r['joint_gate'] else r['v31_percentile'])
        require(abs(float(r['v44_key']) - expected) <= 1e-15, 'v44 placement key changed')

    panels = list(raw['panels'])
    wins = int(sum(bool(r['superiority_pair_pass']) for r in panels))
    require(wins == int(raw['panel_wins']), 'panel win count mismatch')
    passed = bool(wins == 4)

    sugar_diag = raw['order_diagnostics']['sugar']
    hdb_diag = raw['order_diagnostics']['hdbscan']
    freeze: dict[str, Any] = {'verdict': 'NOT_FROZEN_V44_JOINT_COMPONENT_BEST_PLACEMENT_FAIL', 'reference_sha256': None}
    engine_ref = engine / 'v42_quality_component_gated_rescue_reference.npz'
    if passed:
        require(engine_ref.is_file(), 'passing wrapped reference missing')
        dst = output / 'v44_joint_component_best_placement_reference.npz'
        shutil.copyfile(engine_ref, dst)
        freeze = {
            'verdict': 'PASS_V44_FULL_EXPOSED_JOINT_COMPONENT_BEST_PLACEMENT_REFERENCE_FREEZE',
            'reference_sha256': v42.v40.v22.sha(dst),
            'pretruth_graph_sha256': v42.v40.GRAPH_SHA256,
            'pretruth_component_sha256': v42.v40.COMPONENT_SHA256,
            'joint_gate': '(quality_rank < exact_v31_rank) AND (component_best_v31_percentile < own_hdb_v31_percentile)',
            'placement_key': 'component_best_v31_percentile if joint gate else own exact-v31 percentile',
            'sugar_rule': 'exact v31 unchanged',
            'in_sample_reference_score_used_for_promotion': False,
        }
    (output / 'V44_JOINT_COMPONENT_BEST_PLACEMENT_MODEL_FREEZE.json').write_text(json.dumps(freeze, indent=2, sort_keys=True) + '\n')

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V44_JOINT_COMPONENT_BEST_PLACEMENT_V1',
        'verdict': 'PASS_V44_JOINT_COMPONENT_BEST_PLACEMENT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V44_JOINT_COMPONENT_BEST_PLACEMENT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'preserve the exact 60-family quality-suppression AND component-opportunity gate, but place joint-positive HDB candidates by frozen component-best exact-v31 percentile instead of v42 quality rank; Sugar exact v31 unchanged',
        'gate_authorizing_diagnostic': '#1091 PASS_V31_QUALITY_COMPONENT_JOINT_SIGNAL_DIAGNOSTIC',
        'gate_authorizing_run': v42.AUTHOR_RUN,
        'gate_authorizing_artifact': v42.AUTHOR_ARTIFACT,
        'gate_authorizing_sha256': v42.AUTHOR_RESULT_SHA,
        'placement_authorizing_diagnostic': '#1113 PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC',
        'placement_authorizing_run': PLACEMENT_RUN,
        'placement_authorizing_artifact': PLACEMENT_ARTIFACT,
        'placement_authorizing_digest': PLACEMENT_DIGEST,
        'placement_authorizing_sha256': PLACEMENT_RESULT_SHA,
        'pretruth_graph_sha256': v42.v40.GRAPH_SHA256,
        'pretruth_component_sha256': v42.v40.COMPONENT_SHA256,
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': raw['parent_v31_controls'],
        'sugar_rule': 'exact v31 unchanged',
        'hdb_joint_gate': '(quality_rank < exact_v31_rank) AND (component_best_v31_percentile < own_hdb_v31_percentile)',
        'hdb_placement_key': 'component_best_v31_percentile if joint gate else own exact-v31 percentile',
        'hdb_total_order_sort': '(placement_key, own_exact_v31_percentile, family_id)',
        'joint_positive_candidate_count': 60,
        'panel_wins': wins,
        'panels': panels,
        'order_diagnostics': {
            'sugar': {
                'family_count': SUGAR_N,
                'moved_up_in_total_order_count': 0,
                'moved_down_in_total_order_count': 0,
                'unchanged_count': SUGAR_N,
                'v31_order_sha256': sugar_diag['v31_order_sha256'],
                'v44_total_order_sha256': sugar_diag['v42_total_order_sha256'],
                'exact_v31_unchanged': True,
            },
            'hdbscan': {
                'family_count': HDB_N,
                'joint_positive_candidate_count': 60,
                'moved_up_in_total_order_count': int(hdb_diag['moved_up_in_total_order_count']),
                'moved_down_in_total_order_count': int(hdb_diag['moved_down_in_total_order_count']),
                'unchanged_count': int(hdb_diag['unchanged_count']),
                'v31_order_sha256': hdb_diag['v31_order_sha256'],
                'v44_total_order_sha256': hdb_diag['v42_total_order_sha256'],
            },
        },
        'hdb_candidate_rows': hdb_rows,
        'full_model_freeze': freeze,
        'component_best_threshold_search': False,
        'quality_component_blend_search': False,
        'promotion_coefficient_search': False,
        'promotion_bonus_search': False,
        'promotion_cap_search': False,
        'promotion_interpolation_search': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'oracle_correction_count_used': False,
        'threeway_signal_used': False,
        'boolean_combination_search': False,
        'route_specific_rule': False,
        'year_specific_rule': False,
        'budget_specific_rule': False,
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
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V44_JOINT_COMPONENT_BEST_PLACEMENT_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels, 'order_diagnostics': result['order_diagnostics'], 'full_model_freeze': freeze}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    g = sub.add_parser('pretruth')
    g.add_argument('--sugar-root', type=Path, required=True)
    g.add_argument('--hdbscan-root', type=Path, required=True)
    g.add_argument('--output', type=Path, required=True)
    e = sub.add_parser('evaluate')
    e.add_argument('--sugar-root', type=Path, required=True)
    e.add_argument('--hdbscan-root', type=Path, required=True)
    e.add_argument('--truth-root', type=Path, required=True)
    e.add_argument('--ranker-source', type=Path, required=True)
    e.add_argument('--graph-file', type=Path, required=True)
    e.add_argument('--component-file', type=Path, required=True)
    e.add_argument('--joint-authorizer', type=Path, required=True)
    e.add_argument('--placement-authorizer', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'pretruth':
        return pretruth_mode(a.sugar_root, a.hdbscan_root, a.output)
    return evaluate_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.graph_file, a.component_file, a.joint_authorizer, a.placement_authorizer, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

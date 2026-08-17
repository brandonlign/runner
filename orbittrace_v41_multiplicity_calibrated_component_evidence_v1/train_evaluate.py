#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v40_component_best_evidence_representative_v1 import train_evaluate as v40

VARIANT = 'multiplicity_calibrated_component_best_evidence_representative_v1'
AUTHOR_DIAG_RUN = 31456224004
AUTHOR_DIAG_ARTIFACT = 9088133149
AUTHOR_DIAG_DIGEST = 'sha256:83863ab94c675099de62655f4ebca46f0558809338cd160a444b9c6b26e173fd'


def build_v41_order(
    route: str,
    base_order: list[str],
    components: list[dict[str, Any]],
    rank_maps: dict[str, dict[str, int]],
) -> tuple[list[str], list[dict[str, Any]]]:
    v40.require(route in ('sugar', 'hdbscan'), 'invalid route')
    n_route = len(base_order)
    v40.require(n_route == len(rank_maps[route]) and n_route > 1, 'rank universe mismatch')
    reps: list[dict[str, Any]] = []
    rep_ids: set[str] = set()
    for c in components:
        own_ids = list(map(str, c['sugar_family_ids'] if route == 'sugar' else c['hdbscan_family_ids']))
        if not own_ids:
            continue
        own_rep = min(own_ids, key=lambda fid: (rank_maps[route][fid], fid))
        rep_ids.add(own_rep)
        member_rows = []
        for fid in map(str, c['sugar_family_ids']):
            rr = int(rank_maps['sugar'][fid])
            p = float((rr - 1) / (len(rank_maps['sugar']) - 1))
            member_rows.append(('sugar', fid, rr, p))
        for fid in map(str, c['hdbscan_family_ids']):
            rr = int(rank_maps['hdbscan'][fid])
            p = float((rr - 1) / (len(rank_maps['hdbscan']) - 1))
            member_rows.append(('hdbscan', fid, rr, p))
        v40.require(member_rows, 'empty component')
        best_member = min(member_rows, key=lambda x: (x[3], x[2], x[0], x[1]))
        p_min = float(best_member[3])
        m = int(c['member_count'])
        v40.require(m >= 1 and 0.0 <= p_min <= 1.0, 'invalid component evidence inputs')
        q = float(1.0 - (1.0 - p_min) ** m)
        v40.require(np.isfinite(q) and 0.0 <= q <= 1.0, 'invalid calibrated component evidence')
        reps.append({
            'component_id': str(c['component_id']),
            'component_evidence': q,
            'raw_component_p_min': p_min,
            'calibrated_component_q': q,
            'component_member_count': m,
            'representative_family_id': own_rep,
            'representative_v31_rank': int(rank_maps[route][own_rep]),
            'representative_v31_percentile': float((rank_maps[route][own_rep] - 1) / (n_route - 1)),
            'component_sugar_member_count': int(c['sugar_member_count']),
            'component_hdbscan_member_count': int(c['hdbscan_member_count']),
            'best_evidence_route': best_member[0],
            'best_evidence_family_id': best_member[1],
            'best_evidence_v31_rank': int(best_member[2]),
            'best_evidence_percentile': p_min,
            'calibration_formula': 'q=1-(1-p_min)**member_count',
        })
    primary_rows = sorted(
        reps,
        key=lambda r: (float(r['calibrated_component_q']), int(r['representative_v31_rank']), str(r['component_id'])),
    )
    primary = [str(r['representative_family_id']) for r in primary_rows]
    v40.require(len(primary) == len(rep_ids) and len(primary) == len(set(primary)), f'{route} duplicate primary representative')
    secondary = [fid for fid in base_order if fid not in rep_ids]
    order = primary + secondary
    v40.require(len(order) == len(base_order) and set(order) == set(base_order), f'{route} invalid v41 total order')
    for i, r in enumerate(primary_rows):
        r['v41_primary_position'] = i + 1
    return order, primary_rows


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    return v40.pretruth_mode(sugar_root, hdbscan_root, output)


def evaluate_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    component_file: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    engine = output / '_frozen_v40_engine'
    engine.mkdir(parents=True, exist_ok=True)

    original_builder = v40.build_v40_order
    v40.build_v40_order = build_v41_order
    try:
        rc = v40.evaluate_mode(
            sugar_root, hdbscan_root, truth_root, ranker_source,
            graph_file, component_file, engine,
        )
    finally:
        v40.build_v40_order = original_builder
    v40.require(rc == 0, 'frozen v40 evaluation engine failed')

    raw_path = engine / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_RESULT.json'
    v40.require(raw_path.is_file(), 'frozen evaluation engine result missing')
    raw = json.loads(raw_path.read_text())
    v40.require(raw['parent_v31_reproduction_pass'] is True and len(raw['parent_v31_controls']) == 4, 'v31 parent reproduction failed')
    v40.require(raw['pretruth_graph_sha256'] == v40.GRAPH_SHA256, 'graph identity changed')
    v40.require(raw['pretruth_component_sha256'] == v40.COMPONENT_SHA256, 'component identity changed')
    v40.require(int(raw['component_count']) == 196 and int(raw['non_singleton_component_count']) == 113 and int(raw['singleton_component_count']) == 83, 'component counts changed')

    panels = list(raw['panels'])
    wins = int(sum(bool(r['superiority_pair_pass']) for r in panels))
    v40.require(wins == int(raw['panel_wins']), 'panel win count mismatch')
    passed = bool(wins == 4)

    order_diag = {}
    for route in ('sugar', 'hdbscan'):
        src = dict(raw['order_diagnostics'][route])
        order_diag[route] = {
            'family_count': int(src['family_count']),
            'route_component_count': int(src['route_component_count']),
            'primary_representative_count': int(src['primary_representative_count']),
            'secondary_fragment_count': int(src['secondary_fragment_count']),
            'moved_up_in_total_order_count': int(src['moved_up_in_total_order_count']),
            'v31_local_order_sha256': src['v31_local_order_sha256'],
            'v31_fused_order_sha256': src['v31_fused_order_sha256'],
            'v41_total_order_sha256': src['v40_total_order_sha256'],
            'component_evidence_rule': 'q=1-(1-p_min)**member_count, where p_min is minimum normalized exact-v31 percentile across all component members',
            'representative_rule': 'best own-route exact-v31 fused rank within component',
            'primary_sort': '(calibrated_component_q, representative_own_v31_rank, component_id)',
            'secondary_rule': 'append all non-representatives in exact v31 fused order only after every route component representative',
        }

    freeze = {'verdict': 'NOT_FROZEN_V41_MULTIPLICITY_CALIBRATED_COMPONENT_EVIDENCE_FAIL', 'reference_sha256': None}
    engine_ref = engine / 'v40_component_best_evidence_representative_reference.npz'
    if passed:
        v40.require(engine_ref.is_file(), 'passing evaluation missing frozen reference')
        dst = output / 'v41_multiplicity_calibrated_component_evidence_reference.npz'
        shutil.copyfile(engine_ref, dst)
        freeze = {
            'verdict': 'PASS_V41_FULL_EXPOSED_MULTIPLICITY_CALIBRATED_COMPONENT_EVIDENCE_REFERENCE_FREEZE',
            'reference_sha256': v40.v22.sha(dst),
            'pretruth_graph_sha256': v40.GRAPH_SHA256,
            'pretruth_component_sha256': v40.COMPONENT_SHA256,
            'training_examples': int(raw['full_model_freeze']['training_examples']),
            'training_groups': int(raw['full_model_freeze']['training_groups']),
            'feature_dimension': int(raw['feature_dimension']),
            'k': int(raw['nearest_k']),
            'annual_margin': raw['v31_annual_margin'],
            'annual_combiner': raw['v31_annual_combiner'],
            'component_calibration': 'q=1-(1-p_min)**member_count',
            'representative_rule': 'smallest own-route v31 fused rank in component',
            'in_sample_reference_score_used_for_promotion': False,
        }
    (output / 'V41_MULTIPLICITY_CALIBRATED_COMPONENT_EVIDENCE_MODEL_FREEZE.json').write_text(
        json.dumps(freeze, indent=2, sort_keys=True) + '\n'
    )

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V41_MULTIPLICITY_CALIBRATED_COMPONENT_EVIDENCE_V1',
        'verdict': 'PASS_V41_MULTIPLICITY_CALIBRATED_COMPONENT_EVIDENCE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V41_MULTIPLICITY_CALIBRATED_COMPONENT_EVIDENCE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'replace v40 raw component p_min evidence with canonical minimum-order-statistic calibration q=1-(1-p_min)**member_count',
        'authorizing_diagnostic': '#1083 v40 component-minimum multiplicity calibration diagnostic',
        'authorizing_diagnostic_run': AUTHOR_DIAG_RUN,
        'authorizing_diagnostic_artifact': AUTHOR_DIAG_ARTIFACT,
        'authorizing_diagnostic_digest': AUTHOR_DIAG_DIGEST,
        'pretruth_graph_sha256': v40.GRAPH_SHA256,
        'pretruth_component_sha256': v40.COMPONENT_SHA256,
        'component_count': int(raw['component_count']),
        'non_singleton_component_count': int(raw['non_singleton_component_count']),
        'singleton_component_count': int(raw['singleton_component_count']),
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': raw['parent_v31_controls'],
        'feature_dimension': int(raw['feature_dimension']),
        'recovery_f1_threshold': float(raw['recovery_f1_threshold']),
        'nearest_k': int(raw['nearest_k']),
        'v31_distance': raw['v31_distance'],
        'v31_annual_margin': raw['v31_annual_margin'],
        'v31_annual_combiner': raw['v31_annual_combiner'],
        'component_raw_evidence': 'p_min=min normalized exact-v31 percentile over all Sugar/HDB component members',
        'component_calibrated_evidence': 'q=1-(1-p_min)**member_count',
        'component_calibration_member_count': 'total frozen Sugar+HDB component membership count',
        'component_representative': 'best own-route exact-v31 fused rank within component',
        'component_rule_symmetric_across_routes': True,
        'component_rule_year_dependent': False,
        'component_rule_budget_dependent': False,
        'primary_order': 'all route-component representatives by (q, own v31 rank, component_id)',
        'secondary_order': 'all non-representatives in exact v31 order after all primary representatives',
        'promotion_variant': VARIANT,
        'panel_wins': wins,
        'panels': panels,
        'fold_diagnostics': raw['fold_diagnostics'],
        'order_diagnostics': order_diag,
        'primary_component_rows': raw['primary_component_rows'],
        'full_model_freeze': freeze,
        'effective_component_size_fit': False,
        'calibration_exponent_search': False,
        'calibration_coefficient_search': False,
        'calibration_pseudocount_search': False,
        'raw_calibrated_blend_search': False,
        'transfer_threshold_search': False,
        'route_specific_rule': False,
        'year_specific_rule': False,
        'budget_specific_rule': False,
        'component_evidence_aggregation_search': False,
        'representative_family_search': False,
        'secondary_insertion_search': False,
        'component_size_threshold_search': False,
        'radius_search': False,
        'metric_search': False,
        'graph_pruning': False,
        'graph_expansion': False,
        'component_definition_search': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'candidate_generation_changed': False,
        'candidate_membership_changed': False,
        'oracle_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V41_MULTIPLICITY_CALIBRATED_COMPONENT_EVIDENCE_RESULT.json').write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
    )
    print(json.dumps({
        'verdict': result['verdict'],
        'panel_wins': wins,
        'panels': panels,
        'order_diagnostics': order_diag,
        'full_model_freeze': freeze,
    }, indent=2, sort_keys=True, allow_nan=False))
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
    e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'pretruth':
        return pretruth_mode(a.sugar_root, a.hdbscan_root, a.output)
    return evaluate_mode(
        a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source,
        a.graph_file, a.component_file, a.output,
    )


if __name__ == '__main__':
    raise SystemExit(main())

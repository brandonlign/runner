#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v40_component_best_evidence_representative_v1 import train_evaluate as v40

VARIANT = 'conservative_conjunctive_shared_support_rank_transfer_v1'
AUTHOR_RUN = 31456963941
AUTHOR_ARTIFACT = 9088402091
AUTHOR_DIGEST = 'sha256:d1943f629964633f44e154252a225f7171c380674ae6e60e5fcbbd3f8b890dd7'
AUTHOR_RESULT_SHA = '2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842'
FULL_UNIVERSE_RUN = 31457788803
FULL_UNIVERSE_ARTIFACT = 9088683367
V42_RUN = 31457295276
V42_ARTIFACT = 9088524431
HDB_N = 229
SUGAR_N = 267

_QUALITY_RANK: dict[str, int] = {}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def validate_authorizing_diagnostic(path: Path) -> None:
    require(v40.v22.sha(path) == AUTHOR_RESULT_SHA, '#1091 authorizing result identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_SIGNAL_DIAGNOSTIC', '#1091 verdict changed')
    require(r['joint_direction_supported_both_years'] is True, '#1091 direction not supported')
    require(r['joint_signal_definition'] == '(quality_suppression > 0) AND component_closure_opportunity', '#1091 joint definition changed')
    require(r['new_rank_or_score_evaluated'] is False and r['selector_evaluated'] is False, '#1091 not diagnostic-only')
    require(r['replacement_rule_evaluated'] is False and r['successor_selected'] is False, '#1091 selected a successor')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1091 SonotaCo role changed')
    require(r['target_information_access'] is False and r['target_region_events_accessed'] is False, '#1091 target access changed')
    require(r['maarsy_scientific_access'] is False and r['dms_scientific_access'] is False, '#1091 protected-survey access changed')
    require(r['blind_exclusion'] == [20.0, 55.0], '#1091 blind exclusion changed')


def load_quality_rank(hdbscan_root: Path) -> tuple[list[str], dict[str, int], str]:
    meta = json.loads((hdbscan_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fam = json.loads((hdbscan_root / 'family_memberships.json').read_text())
    require(meta['truth_accessed'] is False and fam['truth_accessed'] is False, 'HDB payload not pretruth')
    require(int(meta['feature_dimension']) == 71, 'HDB feature dimension changed')
    ids = list(map(str, meta['family_ids']))
    quality = list(map(str, meta['quality_order']))
    require(len(ids) == HDB_N and len(set(ids)) == HDB_N, 'HDB family universe changed')
    require(len(quality) == HDB_N and set(quality) == set(ids), 'HDB quality order universe changed')
    require([str(x['family_id']) for x in fam['families']] == ids, 'HDB membership order changed')
    require(meta['target_information_access'] is False, 'HDB manifest target access changed')
    require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, 'HDB manifest protected-survey access changed')
    qrank = {fid: i + 1 for i, fid in enumerate(quality)}
    return quality, qrank, v40.order_sha(quality)


def component_best_percentiles(
    components: list[dict[str, Any]],
    rank_maps: dict[str, dict[str, int]],
) -> dict[str, float]:
    require(len(rank_maps['sugar']) == SUGAR_N and len(rank_maps['hdbscan']) == HDB_N, 'route rank universe changed')
    out: dict[str, float] = {}
    for c in components:
        cid = str(c['component_id'])
        vals: list[float] = []
        for fid in map(str, c['sugar_family_ids']):
            vals.append(float((int(rank_maps['sugar'][fid]) - 1) / (SUGAR_N - 1)))
        for fid in map(str, c['hdbscan_family_ids']):
            vals.append(float((int(rank_maps['hdbscan'][fid]) - 1) / (HDB_N - 1)))
        require(vals, 'empty frozen component')
        p = float(min(vals))
        require(np.isfinite(p) and 0.0 <= p <= 1.0, 'invalid component percentile')
        require(cid not in out, 'duplicate component id')
        out[cid] = p
    require(len(out) == 196, 'component count changed')
    return out


def build_v43_order(
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
                'v43_support_key_percentile': float(i / (SUGAR_N - 1)),
                'joint_gate': False,
                'sugar_unchanged': True,
            }
            for i, fid in enumerate(base_order)
        ]
        return list(map(str, base_order)), rows

    require(len(base_order) == HDB_N and set(base_order) == set(_QUALITY_RANK), 'HDB quality-rank map not initialized')
    vrank = rank_maps['hdbscan']
    component_best = component_best_percentiles(components, rank_maps)
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
        rq = int(_QUALITY_RANK[fid])
        ph = float((rv - 1) / (HDB_N - 1))
        pq = float((rq - 1) / (HDB_N - 1))
        cid = hdb_component[fid]
        pc = float(component_best[cid])
        quality_suppressed = bool(pq < ph)
        component_opportunity = bool(pc < ph)
        joint = bool(quality_suppressed and component_opportunity)
        key = float(max(pq, pc) if joint else ph)
        if joint:
            require(key < ph, 'joint-positive conservative key must improve over v31')
        else:
            require(abs(key - ph) < 1e-15, 'nonjoint key changed')
        limiting = 'none'
        if joint:
            limiting = 'quality' if pq >= pc else 'component'
        rows.append({
            'representative_family_id': fid,
            'family_id': fid,
            'component_id': cid,
            'v31_rank': rv,
            'quality_rank': rq,
            'v31_percentile': ph,
            'quality_percentile': pq,
            'component_best_v31_percentile': pc,
            'quality_suppressed': quality_suppressed,
            'component_opportunity': component_opportunity,
            'joint_gate': joint,
            'v43_support_key_percentile': key,
            'limiting_support_source': limiting,
            'conservative_percentile_gain': float(ph - key) if joint else 0.0,
        })

    by_id = {str(r['family_id']): r for r in rows}
    order = sorted(
        map(str, base_order),
        key=lambda fid: (
            float(by_id[fid]['v43_support_key_percentile']),
            float(by_id[fid]['v31_percentile']),
            fid,
        ),
    )
    require(len(order) == HDB_N and set(order) == set(map(str, base_order)), 'invalid v43 HDB total order')
    new_rank = {fid: i + 1 for i, fid in enumerate(order)}
    for r in rows:
        r['v43_rank'] = int(new_rank[str(r['family_id'])])
    return order, rows


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    return v40.pretruth_mode(sugar_root, hdbscan_root, output)


def evaluate_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    component_file: Path,
    authorizing_diagnostic: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(v40.v22.sha(graph_file) == v40.GRAPH_SHA256, 'pretruth graph identity changed')
    require(v40.v22.sha(component_file) == v40.COMPONENT_SHA256, 'pretruth component identity changed')
    validate_authorizing_diagnostic(authorizing_diagnostic)

    _quality_order, qrank, quality_sha = load_quality_rank(hdbscan_root)
    global _QUALITY_RANK
    _QUALITY_RANK = dict(qrank)

    engine = output / '_frozen_v40_engine'
    engine.mkdir(parents=True, exist_ok=True)
    original_builder = v40.build_v40_order
    original_variant = v40.VARIANT
    v40.build_v40_order = build_v43_order
    v40.VARIANT = VARIANT
    try:
        rc = v40.evaluate_mode(
            sugar_root,
            hdbscan_root,
            truth_root,
            ranker_source,
            graph_file,
            component_file,
            engine,
        )
    finally:
        v40.build_v40_order = original_builder
        v40.VARIANT = original_variant
    require(rc == 0, 'frozen v40 evaluation engine failed')

    raw_path = engine / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_RESULT.json'
    require(raw_path.is_file(), 'frozen engine result missing')
    raw = json.loads(raw_path.read_text())
    require(raw['parent_v31_reproduction_pass'] is True and len(raw['parent_v31_controls']) == 4, 'exact v31 parent reproduction failed')
    require(raw['pretruth_graph_sha256'] == v40.GRAPH_SHA256 and raw['pretruth_component_sha256'] == v40.COMPONENT_SHA256, 'frozen geometry changed')
    require(int(raw['component_count']) == 196 and int(raw['non_singleton_component_count']) == 113 and int(raw['singleton_component_count']) == 83, 'component counts changed')

    sugar_rows = list(raw['primary_component_rows']['sugar'])
    hdb_rows = list(raw['primary_component_rows']['hdbscan'])
    require(len(sugar_rows) == SUGAR_N and len(hdb_rows) == HDB_N, 'candidate diagnostic row count changed')
    require(all(bool(r['sugar_unchanged']) for r in sugar_rows), 'Sugar was modified')

    joint_count = int(sum(bool(r['joint_gate']) for r in hdb_rows))
    quality_suppressed_count = int(sum(bool(r['quality_suppressed']) for r in hdb_rows))
    component_opportunity_count = int(sum(bool(r['component_opportunity']) for r in hdb_rows))
    quality_limiting_count = int(sum(r['limiting_support_source'] == 'quality' for r in hdb_rows))
    component_limiting_count = int(sum(r['limiting_support_source'] == 'component' for r in hdb_rows))

    sugar_v31_order = [str(x['family_id']) for x in sorted(sugar_rows, key=lambda r: int(r['v31_rank']))]
    sugar_v43_order = list(sugar_v31_order)
    hdb_v31_order = [str(x['family_id']) for x in sorted(hdb_rows, key=lambda r: int(r['v31_rank']))]
    hdb_v43_order = [str(x['family_id']) for x in sorted(hdb_rows, key=lambda r: int(r['v43_rank']))]
    require(sugar_v43_order == sugar_v31_order, 'Sugar v43 order differs from v31')

    old_h = {fid: i + 1 for i, fid in enumerate(hdb_v31_order)}
    new_h = {fid: i + 1 for i, fid in enumerate(hdb_v43_order)}
    moved_up = int(sum(new_h[fid] < old_h[fid] for fid in hdb_v31_order))
    moved_down = int(sum(new_h[fid] > old_h[fid] for fid in hdb_v31_order))
    unchanged = int(HDB_N - moved_up - moved_down)

    panels = list(raw['panels'])
    wins = int(sum(bool(x['superiority_pair_pass']) for x in panels))
    require(wins == int(raw['panel_wins']), 'panel win count mismatch')
    passed = bool(wins == 4)

    freeze: dict[str, Any] = {
        'verdict': 'NOT_FROZEN_V43_CONSERVATIVE_CONJUNCTIVE_RANK_TRANSFER_FAIL',
        'reference_sha256': None,
    }
    engine_ref = engine / 'v40_component_best_evidence_representative_reference.npz'
    if passed:
        require(engine_ref.is_file(), 'passing engine reference missing')
        dst = output / 'v43_conservative_conjunctive_rank_transfer_reference.npz'
        shutil.copyfile(engine_ref, dst)
        freeze = {
            'verdict': 'PASS_V43_FULL_EXPOSED_CONSERVATIVE_CONJUNCTIVE_RANK_TRANSFER_REFERENCE_FREEZE',
            'reference_sha256': v40.v22.sha(dst),
            'pretruth_graph_sha256': v40.GRAPH_SHA256,
            'pretruth_component_sha256': v40.COMPONENT_SHA256,
            'quality_order_sha256': quality_sha,
            'training_examples': int(raw['full_model_freeze']['training_examples']),
            'training_groups': int(raw['full_model_freeze']['training_groups']),
            'feature_dimension': int(raw['feature_dimension']),
            'k': int(raw['nearest_k']),
            'joint_gate': '(p_quality < p_v31) AND (p_component_best < p_v31)',
            'promotion_key': 'max(p_quality,p_component_best) if joint else p_v31',
            'sugar_rule': 'exact v31 unchanged',
            'in_sample_reference_score_used_for_promotion': False,
        }
    (output / 'V43_CONSERVATIVE_CONJUNCTIVE_RANK_TRANSFER_MODEL_FREEZE.json').write_text(
        json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n'
    )

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V43_CONSERVATIVE_CONJUNCTIVE_RANK_TRANSFER_V1',
        'verdict': 'PASS_V43_CONSERVATIVE_CONJUNCTIVE_RANK_TRANSFER_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V43_CONSERVATIVE_CONJUNCTIVE_RANK_TRANSFER_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'replace failed v42 full-quality-rank placement with the conservative shared-support key max(normalized immutable quality percentile, frozen component-best normalized v31 percentile) for the same exact AND-positive HDB candidates; Sugar exact v31 unchanged',
        'authorizing_diagnostic': '#1091 PASS_V31_QUALITY_COMPONENT_JOINT_SIGNAL_DIAGNOSTIC',
        'authorizing_diagnostic_run': AUTHOR_RUN,
        'authorizing_diagnostic_artifact': AUTHOR_ARTIFACT,
        'authorizing_diagnostic_digest': AUTHOR_DIGEST,
        'authorizing_diagnostic_sha256': AUTHOR_RESULT_SHA,
        'full_universe_diagnostic_run': FULL_UNIVERSE_RUN,
        'full_universe_diagnostic_artifact': FULL_UNIVERSE_ARTIFACT,
        'failed_parent_successor_run': V42_RUN,
        'failed_parent_successor_artifact': V42_ARTIFACT,
        'pretruth_graph_sha256': v40.GRAPH_SHA256,
        'pretruth_component_sha256': v40.COMPONENT_SHA256,
        'quality_order_sha256': quality_sha,
        'quality_order_role': 'immutable pre-SonotaCo #839/#853 quality-diversity order from #950 manifest',
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
        'sugar_rule': 'exact v31 unchanged',
        'hdb_joint_gate': '(quality_percentile < exact_v31_percentile) AND (component_best_v31_percentile < exact_v31_percentile)',
        'hdb_support_key': 'max(quality_percentile, component_best_v31_percentile) if joint gate else exact_v31_percentile',
        'hdb_total_order_sort': '(support_key_percentile, exact_v31_percentile, family_id)',
        'joint_positive_candidate_count': joint_count,
        'quality_suppressed_candidate_count': quality_suppressed_count,
        'component_opportunity_candidate_count': component_opportunity_count,
        'quality_limiting_joint_candidate_count': quality_limiting_count,
        'component_limiting_joint_candidate_count': component_limiting_count,
        'panel_wins': wins,
        'panels': panels,
        'fold_diagnostics': raw['fold_diagnostics'],
        'order_diagnostics': {
            'sugar': {
                'family_count': SUGAR_N,
                'moved_up_in_total_order_count': 0,
                'moved_down_in_total_order_count': 0,
                'unchanged_count': SUGAR_N,
                'v31_order_sha256': v40.order_sha(sugar_v31_order),
                'v43_total_order_sha256': v40.order_sha(sugar_v43_order),
                'exact_v31_unchanged': True,
            },
            'hdbscan': {
                'family_count': HDB_N,
                'joint_positive_candidate_count': joint_count,
                'moved_up_in_total_order_count': moved_up,
                'moved_down_in_total_order_count': moved_down,
                'unchanged_count': unchanged,
                'v31_order_sha256': v40.order_sha(hdb_v31_order),
                'v43_total_order_sha256': v40.order_sha(hdb_v43_order),
            },
        },
        'hdb_candidate_rows': hdb_rows,
        'full_model_freeze': freeze,
        'quality_suppression_threshold_search': False,
        'component_opportunity_threshold_search': False,
        'boolean_combination_search': False,
        'support_min_search': False,
        'support_mean_search': False,
        'support_geometric_mean_search': False,
        'support_weight_search': False,
        'top_k_selected': False,
        'oracle_correction_count_used': False,
        'rank_window_selected': False,
        'promotion_coefficient_search': False,
        'promotion_interpolation_search': False,
        'promotion_bonus_search': False,
        'promotion_cap_search': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'sugar_modified': False,
        'alternate_quality_order_search': False,
        'global_quality_fusion': False,
        'component_score_global_ordering': False,
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
    (output / 'V43_CONSERVATIVE_CONJUNCTIVE_RANK_TRANSFER_RESULT.json').write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
    )
    print(json.dumps({
        'verdict': result['verdict'],
        'panel_wins': wins,
        'joint_positive_candidate_count': joint_count,
        'panels': panels,
        'order_diagnostics': result['order_diagnostics'],
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
    e.add_argument('--authorizing-diagnostic', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'pretruth':
        return pretruth_mode(a.sugar_root, a.hdbscan_root, a.output)
    return evaluate_mode(
        a.sugar_root,
        a.hdbscan_root,
        a.truth_root,
        a.ranker_source,
        a.graph_file,
        a.component_file,
        a.authorizing_diagnostic,
        a.output,
    )


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v40_component_best_evidence_representative_v1 import train_evaluate as v40

VARIANT = 'quality_component_gated_quality_rank_rescue_v1'
AUTHOR_RUN = 31456963941
AUTHOR_ARTIFACT = 9088402091
AUTHOR_DIGEST = 'sha256:d1943f629964633f44e154252a225f7171c380674ae6e60e5fcbbd3f8b890dd7'
AUTHOR_RESULT_SHA = '2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842'
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
    qsha = v40.order_sha(quality)
    return quality, qrank, qsha


def component_best_percentiles(
    components: list[dict[str, Any]],
    rank_maps: dict[str, dict[str, int]],
) -> dict[str, float]:
    out: dict[str, float] = {}
    require(len(rank_maps['sugar']) == SUGAR_N and len(rank_maps['hdbscan']) == HDB_N, 'route rank universe changed')
    for c in components:
        cid = str(c['component_id'])
        vals: list[float] = []
        for fid in map(str, c['sugar_family_ids']):
            rr = int(rank_maps['sugar'][fid])
            vals.append(float((rr - 1) / (SUGAR_N - 1)))
        for fid in map(str, c['hdbscan_family_ids']):
            rr = int(rank_maps['hdbscan'][fid])
            vals.append(float((rr - 1) / (HDB_N - 1)))
        require(vals, 'empty frozen component')
        p = float(min(vals))
        require(np.isfinite(p) and 0.0 <= p <= 1.0, 'invalid frozen component percentile')
        require(cid not in out, 'duplicate component id')
        out[cid] = p
    require(len(out) == 196, 'component count changed')
    return out


def build_v42_order(
    route: str,
    base_order: list[str],
    components: list[dict[str, Any]],
    rank_maps: dict[str, dict[str, int]],
) -> tuple[list[str], list[dict[str, Any]]]:
    require(route in ('sugar', 'hdbscan'), 'invalid route')
    if route == 'sugar':
        # Frozen v42 protocol: Sugar is exact v31, byte-for-byte order identity.
        rows = [
            {
                'representative_family_id': str(fid),
                'family_id': str(fid),
                'v31_rank': i + 1,
                'v42_key': i + 1,
                'joint_gate': False,
                'sugar_unchanged': True,
            }
            for i, fid in enumerate(base_order)
        ]
        return list(base_order), rows

    require(len(base_order) == HDB_N and set(base_order) == set(_QUALITY_RANK), 'HDB quality-rank map not initialized on exact universe')
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
    for fid in base_order:
        fid = str(fid)
        rv = int(vrank[fid])
        rq = int(_QUALITY_RANK[fid])
        cid = hdb_component[fid]
        ph = float((rv - 1) / (HDB_N - 1))
        pc = float(component_best[cid])
        quality_suppressed = bool(rq < rv)
        component_opportunity = bool(pc < ph)
        joint = bool(quality_suppressed and component_opportunity)
        key = int(rq if joint else rv)
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
            'v42_key': key,
            'promotion_rank_gain': int(rv - key) if joint else 0,
        })

    by_id = {str(r['family_id']): r for r in rows}
    order = sorted(base_order, key=lambda fid: (int(by_id[str(fid)]['v42_key']), int(vrank[str(fid)]), str(fid)))
    require(len(order) == HDB_N and set(order) == set(base_order), 'invalid v42 HDB total order')
    new_rank = {str(fid): i + 1 for i, fid in enumerate(order)}
    for r in rows:
        r['v42_rank'] = int(new_rank[str(r['family_id'])])
    return list(map(str, order)), rows


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    # v42 inherits the exact #1064/#1072 graph/component construction.
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

    quality_order, qrank, quality_sha = load_quality_rank(hdbscan_root)
    global _QUALITY_RANK
    _QUALITY_RANK = dict(qrank)

    engine = output / '_frozen_v40_engine'
    engine.mkdir(parents=True, exist_ok=True)
    original_builder = v40.build_v40_order
    original_variant = v40.VARIANT
    v40.build_v40_order = build_v42_order
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

    # The monkeypatched builder rows are deterministic candidate-level v42 diagnostics.
    sugar_rows = list(raw['primary_component_rows']['sugar'])
    hdb_rows = list(raw['primary_component_rows']['hdbscan'])
    require(len(sugar_rows) == SUGAR_N and len(hdb_rows) == HDB_N, 'v42 candidate diagnostic row count changed')
    require(all(bool(r['sugar_unchanged']) for r in sugar_rows), 'Sugar was modified')
    joint_count = int(sum(bool(r['joint_gate']) for r in hdb_rows))
    quality_suppressed_count = int(sum(bool(r['quality_suppressed']) for r in hdb_rows))
    component_opportunity_count = int(sum(bool(r['component_opportunity']) for r in hdb_rows))

    # Reconstruct exact orders from candidate rows to avoid relying on v40 metadata labels.
    sugar_v31_order = [str(x['family_id']) for x in sorted(sugar_rows, key=lambda r: int(r['v31_rank']))]
    sugar_v42_order = list(sugar_v31_order)
    hdb_v31_order = [str(x['family_id']) for x in sorted(hdb_rows, key=lambda r: int(r['v31_rank']))]
    hdb_v42_order = [str(x['family_id']) for x in sorted(hdb_rows, key=lambda r: int(r['v42_rank']))]
    require(sugar_v42_order == sugar_v31_order, 'Sugar v42 order differs from v31')

    old_h = {fid: i + 1 for i, fid in enumerate(hdb_v31_order)}
    new_h = {fid: i + 1 for i, fid in enumerate(hdb_v42_order)}
    hdb_moved_up = int(sum(new_h[fid] < old_h[fid] for fid in hdb_v31_order))
    hdb_moved_down = int(sum(new_h[fid] > old_h[fid] for fid in hdb_v31_order))
    hdb_unchanged = int(HDB_N - hdb_moved_up - hdb_moved_down)

    panels = list(raw['panels'])
    wins = int(sum(bool(x['superiority_pair_pass']) for x in panels))
    require(wins == int(raw['panel_wins']), 'panel win count mismatch')
    passed = bool(wins == 4)

    freeze: dict[str, Any] = {
        'verdict': 'NOT_FROZEN_V42_QUALITY_COMPONENT_GATED_RESCUE_FAIL',
        'reference_sha256': None,
    }
    engine_ref = engine / 'v40_component_best_evidence_representative_reference.npz'
    if passed:
        require(engine_ref.is_file(), 'passing engine reference missing')
        dst = output / 'v42_quality_component_gated_rescue_reference.npz'
        shutil.copyfile(engine_ref, dst)
        freeze = {
            'verdict': 'PASS_V42_FULL_EXPOSED_QUALITY_COMPONENT_GATED_RESCUE_REFERENCE_FREEZE',
            'reference_sha256': v40.v22.sha(dst),
            'pretruth_graph_sha256': v40.GRAPH_SHA256,
            'pretruth_component_sha256': v40.COMPONENT_SHA256,
            'quality_order_sha256': quality_sha,
            'training_examples': int(raw['full_model_freeze']['training_examples']),
            'training_groups': int(raw['full_model_freeze']['training_groups']),
            'feature_dimension': int(raw['feature_dimension']),
            'k': int(raw['nearest_k']),
            'joint_gate': '(quality_rank < v31_rank) AND (component_best_v31_percentile < own_hdb_v31_percentile)',
            'promotion_key': 'quality_rank if joint gate else v31_rank',
            'sugar_rule': 'exact v31 unchanged',
            'in_sample_reference_score_used_for_promotion': False,
        }
    (output / 'V42_QUALITY_COMPONENT_GATED_RESCUE_MODEL_FREEZE.json').write_text(
        json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n'
    )

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V42_QUALITY_COMPONENT_GATED_RESCUE_V1',
        'verdict': 'PASS_V42_QUALITY_COMPONENT_GATED_RESCUE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V42_QUALITY_COMPONENT_GATED_RESCUE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'HDB-only exact AND gate between immutable quality suppression and frozen component opportunity; joint-positive candidates use immutable quality rank as promotion key; Sugar exact v31 unchanged',
        'authorizing_diagnostic': '#1091 PASS_V31_QUALITY_COMPONENT_JOINT_SIGNAL_DIAGNOSTIC',
        'authorizing_diagnostic_run': AUTHOR_RUN,
        'authorizing_diagnostic_artifact': AUTHOR_ARTIFACT,
        'authorizing_diagnostic_digest': AUTHOR_DIGEST,
        'authorizing_diagnostic_sha256': AUTHOR_RESULT_SHA,
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
        'hdb_quality_suppressed_condition': 'quality_rank < exact_v31_rank',
        'hdb_component_opportunity_condition': 'frozen component best normalized exact-v31 percentile < own HDB normalized exact-v31 percentile',
        'hdb_joint_gate': 'quality_suppressed AND component_opportunity',
        'hdb_promotion_key': 'quality_rank if joint gate else exact_v31_rank',
        'hdb_total_order_sort': '(promotion_key, exact_v31_rank, family_id)',
        'joint_positive_candidate_count': joint_count,
        'quality_suppressed_candidate_count': quality_suppressed_count,
        'component_opportunity_candidate_count': component_opportunity_count,
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
                'v42_total_order_sha256': v40.order_sha(sugar_v42_order),
                'exact_v31_unchanged': True,
            },
            'hdbscan': {
                'family_count': HDB_N,
                'joint_positive_candidate_count': joint_count,
                'quality_suppressed_candidate_count': quality_suppressed_count,
                'component_opportunity_candidate_count': component_opportunity_count,
                'moved_up_in_total_order_count': hdb_moved_up,
                'moved_down_in_total_order_count': hdb_moved_down,
                'unchanged_count': hdb_unchanged,
                'v31_order_sha256': v40.order_sha(hdb_v31_order),
                'v42_total_order_sha256': v40.order_sha(hdb_v42_order),
            },
        },
        'hdb_candidate_rows': hdb_rows,
        'full_model_freeze': freeze,
        'quality_suppression_threshold_search': False,
        'component_opportunity_threshold_search': False,
        'boolean_combination_search': False,
        'top_k_selected': False,
        'oracle_correction_count_used': False,
        'rank_window_selected': False,
        'promotion_coefficient_search': False,
        'promotion_interpolation_search': False,
        'promotion_bonus_search': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'sugar_modified': False,
        'alternate_quality_order_search': False,
        'global_quality_fusion': False,
        'component_score_ordering': False,
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
    (output / 'V42_QUALITY_COMPONENT_GATED_RESCUE_RESULT.json').write_text(
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

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from orbittrace_v43_conservative_conjunctive_rank_transfer_v1 import train_evaluate as v43

v40 = v43.v40

VARIANT = 'component_prioritized_joint_slot_permutation_v1'
PLACEMENT_RUN = 31458734952
PLACEMENT_ARTIFACT = 9088994714
PLACEMENT_DIGEST = 'sha256:5bddfbe4abda60006757561d4c6477102317e02f5fb9555330e0b62eaf3353df'
PLACEMENT_RESULT_SHA = '939f4288a5f0d2de84ef566bb93713da664230deb65777c422795c93fba10c6d'
HDB_N = 229
SUGAR_N = 267
JOINT_N = 60

_QUALITY_RANK: dict[str, int] = {}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def validate_placement_diagnostic(path: Path) -> None:
    require(v40.v22.sha(path) == PLACEMENT_RESULT_SHA, '#1113 placement result identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC', '#1113 verdict changed')
    require(r['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_COMPONENT_SELECTOR_OR_SUCCESSOR_EVALUATED', '#1113 role changed')
    require(int(r['family_count']) == HDB_N and int(r['joint_family_count']) == JOINT_N, '#1113 family counts changed')
    require(r['placement_statistic'] == 'component_best_v31_percentile from frozen #1098 signal; lower is better', '#1113 placement statistic changed')
    require(r['placement_direction_supported_both_years_both_levels'] is True, '#1113 direction not supported')
    require(r['graph_sha256'] == v40.GRAPH_SHA256 and r['component_sha256'] == v40.COMPONENT_SHA256, '#1113 geometry identity changed')
    require(set(r['annual_diagnostics']) == {'2013', '2014'}, '#1113 annual universe changed')
    require(r['new_rank_or_score_evaluated'] is False and r['selector_evaluated'] is False, '#1113 was not diagnostic-only')
    require(r['replacement_rule_evaluated'] is False and r['successor_selected'] is False, '#1113 selected a successor')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1113 SonotaCo role changed')
    require(r['target_information_access'] is False and r['target_region_events_accessed'] is False, '#1113 target firewall changed')
    require(r['maarsy_scientific_access'] is False and r['dms_scientific_access'] is False, '#1113 survey firewall changed')
    require(r['blind_exclusion'] == [20.0, 55.0], '#1113 blind exclusion changed')


def build_v45_order(
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
                'v45_rank': i + 1,
                'joint_gate': False,
                'sugar_unchanged': True,
            }
            for i, fid in enumerate(base_order)
        ]
        return list(map(str, base_order)), rows

    require(len(base_order) == HDB_N and set(map(str, base_order)) == set(_QUALITY_RANK), 'HDB quality-rank map not initialized')
    vrank = rank_maps['hdbscan']
    component_best = v43.component_best_percentiles(components, rank_maps)

    hdb_component: dict[str, str] = {}
    for c in components:
        cid = str(c['component_id'])
        for fid in map(str, c['hdbscan_family_ids']):
            require(fid not in hdb_component, 'HDB family occurs in multiple components')
            hdb_component[fid] = cid
    require(set(hdb_component) == set(map(str, base_order)), 'HDB component assignment incomplete')

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
        })

    by_id = {str(r['family_id']): r for r in rows}
    joint_ids = [str(fid) for fid in map(str, base_order) if bool(by_id[str(fid)]['joint_gate'])]
    require(len(joint_ids) == JOINT_N, 'joint-positive HDB count changed')
    joint_positions = sorted(int(vrank[fid]) for fid in joint_ids)
    ordered_joint = sorted(
        joint_ids,
        key=lambda fid: (
            float(by_id[fid]['component_best_v31_percentile']),
            int(by_id[fid]['v31_rank']),
            fid,
        ),
    )

    order = list(map(str, base_order))
    for pos, fid in zip(joint_positions, ordered_joint):
        order[pos - 1] = fid
    require(len(order) == HDB_N and len(set(order)) == HDB_N and set(order) == set(map(str, base_order)), 'invalid v45 HDB permutation')

    joint_set = set(joint_ids)
    for pos, old_fid in enumerate(map(str, base_order), start=1):
        if pos not in joint_positions:
            require(order[pos - 1] == old_fid, f'nonjoint v31 slot moved at position {pos}')
            require(old_fid not in joint_set, f'joint family unexpectedly occupies nonjoint position {pos}')
        else:
            require(order[pos - 1] in joint_set, f'nonjoint family entered joint slot {pos}')

    new_rank = {fid: i + 1 for i, fid in enumerate(order)}
    require(sorted(new_rank[fid] for fid in joint_ids) == joint_positions, 'joint slot set changed')
    for r in rows:
        fid = str(r['family_id'])
        r['v45_rank'] = int(new_rank[fid])
        r['v45_rank_delta'] = int(r['v31_rank'] - r['v45_rank'])
        r['v45_joint_slot_position'] = int(r['v45_rank']) if bool(r['joint_gate']) else None
        if not bool(r['joint_gate']):
            require(int(r['v45_rank']) == int(r['v31_rank']), f'nonjoint family moved: {fid}')

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
    placement_diagnostic: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(v40.v22.sha(graph_file) == v40.GRAPH_SHA256, 'pretruth graph identity changed')
    require(v40.v22.sha(component_file) == v40.COMPONENT_SHA256, 'pretruth component identity changed')
    validate_placement_diagnostic(placement_diagnostic)

    _quality_order, qrank, quality_sha = v43.load_quality_rank(hdbscan_root)
    global _QUALITY_RANK
    _QUALITY_RANK = dict(qrank)

    engine = output / '_frozen_v40_engine'
    engine.mkdir(parents=True, exist_ok=True)
    original_builder = v40.build_v40_order
    original_variant = v40.VARIANT
    v40.build_v40_order = build_v45_order
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
    require(len(sugar_rows) == SUGAR_N and len(hdb_rows) == HDB_N, 'candidate row count changed')
    require(all(bool(r['sugar_unchanged']) for r in sugar_rows), 'Sugar was modified')

    joint_count = int(sum(bool(r['joint_gate']) for r in hdb_rows))
    require(joint_count == JOINT_N, 'v45 joint count changed')
    nonjoint_count = HDB_N - joint_count

    sugar_v31_order = [str(x['family_id']) for x in sorted(sugar_rows, key=lambda r: int(r['v31_rank']))]
    sugar_v45_order = [str(x['family_id']) for x in sorted(sugar_rows, key=lambda r: int(r['v45_rank']))]
    hdb_v31_order = [str(x['family_id']) for x in sorted(hdb_rows, key=lambda r: int(r['v31_rank']))]
    hdb_v45_order = [str(x['family_id']) for x in sorted(hdb_rows, key=lambda r: int(r['v45_rank']))]
    require(sugar_v45_order == sugar_v31_order, 'Sugar v45 order differs from v31')

    row_by_id = {str(r['family_id']): r for r in hdb_rows}
    joint_ids = [fid for fid in hdb_v31_order if bool(row_by_id[fid]['joint_gate'])]
    nonjoint_ids = [fid for fid in hdb_v31_order if not bool(row_by_id[fid]['joint_gate'])]
    joint_positions_v31 = sorted(int(row_by_id[fid]['v31_rank']) for fid in joint_ids)
    joint_positions_v45 = sorted(int(row_by_id[fid]['v45_rank']) for fid in joint_ids)
    require(joint_positions_v45 == joint_positions_v31, 'joint slot set changed')
    require(all(int(row_by_id[fid]['v45_rank']) == int(row_by_id[fid]['v31_rank']) for fid in nonjoint_ids), 'nonjoint family moved')

    old_h = {fid: i + 1 for i, fid in enumerate(hdb_v31_order)}
    new_h = {fid: i + 1 for i, fid in enumerate(hdb_v45_order)}
    moved_up = int(sum(new_h[fid] < old_h[fid] for fid in hdb_v31_order))
    moved_down = int(sum(new_h[fid] > old_h[fid] for fid in hdb_v31_order))
    unchanged = int(HDB_N - moved_up - moved_down)

    def prefix_diag(k: int) -> dict[str, Any]:
        a = set(hdb_v31_order[:k])
        b = set(hdb_v45_order[:k])
        return {
            'budget': k,
            'v31_set_size': len(a),
            'v45_set_size': len(b),
            'intersection_count': len(a & b),
            'incoming_count': len(b - a),
            'outgoing_count': len(a - b),
            'membership_changed': bool(a != b),
        }

    panels = list(raw['panels'])
    wins = int(sum(bool(x['superiority_pair_pass']) for x in panels))
    require(wins == int(raw['panel_wins']), 'panel win count mismatch')
    passed = bool(wins == 4)

    freeze: dict[str, Any] = {
        'verdict': 'NOT_FROZEN_V45_COMPONENT_PRIORITIZED_JOINT_SLOT_FAIL',
        'reference_sha256': None,
    }
    engine_ref = engine / 'v40_component_best_evidence_representative_reference.npz'
    if passed:
        require(engine_ref.is_file(), 'passing engine reference missing')
        dst = output / 'v45_component_prioritized_joint_slot_reference.npz'
        shutil.copyfile(engine_ref, dst)
        freeze = {
            'verdict': 'PASS_V45_FULL_EXPOSED_COMPONENT_PRIORITIZED_JOINT_SLOT_REFERENCE_FREEZE',
            'reference_sha256': v40.v22.sha(dst),
            'pretruth_graph_sha256': v40.GRAPH_SHA256,
            'pretruth_component_sha256': v40.COMPONENT_SHA256,
            'quality_order_sha256': quality_sha,
            'training_examples': int(raw['full_model_freeze']['training_examples']),
            'training_groups': int(raw['full_model_freeze']['training_groups']),
            'feature_dimension': int(raw['feature_dimension']),
            'k': int(raw['nearest_k']),
            'joint_gate': '(p_quality < p_v31) AND (p_component_best < p_v31)',
            'joint_priority': '(p_component_best, v31_rank, family_id)',
            'slot_rule': 'permute joint-positive identities only over their exact-v31 occupied positions',
            'sugar_rule': 'exact v31 unchanged',
            'in_sample_reference_score_used_for_promotion': False,
        }
    (output / 'V45_COMPONENT_PRIORITIZED_JOINT_SLOT_MODEL_FREEZE.json').write_text(
        json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n'
    )

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V45_COMPONENT_PRIORITIZED_JOINT_SLOT_V1',
        'verdict': 'PASS_V45_COMPONENT_PRIORITIZED_JOINT_SLOT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V45_COMPONENT_PRIORITIZED_JOINT_SLOT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'within the exact 60-family joint-positive HDB set, permute identities only across the exact-v31 positions already occupied by that set, prioritized by frozen component-best exact-v31 percentile; all nonjoint HDB positions and Sugar remain exact v31',
        'pre_result_frozen_protocol_blob': '83c6b82259cb184e312aac51f74b525582eabc69',
        'authorizing_diagnostic': '#1113 PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC',
        'authorizing_diagnostic_run': PLACEMENT_RUN,
        'authorizing_diagnostic_artifact': PLACEMENT_ARTIFACT,
        'authorizing_diagnostic_digest': PLACEMENT_DIGEST,
        'authorizing_diagnostic_sha256': PLACEMENT_RESULT_SHA,
        'pretruth_graph_sha256': v40.GRAPH_SHA256,
        'pretruth_component_sha256': v40.COMPONENT_SHA256,
        'quality_order_sha256': quality_sha,
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
        'hdb_joint_priority': '(component_best_v31_percentile, exact_v31_rank, family_id)',
        'hdb_slot_rule': 'joint-positive identities permuted only across the exact-v31 positions originally occupied by joint-positive identities',
        'joint_positive_candidate_count': joint_count,
        'nonjoint_candidate_count': nonjoint_count,
        'nonjoint_positions_unchanged': True,
        'joint_slot_set_unchanged': True,
        'joint_slot_count': len(joint_positions_v31),
        'prefix_diagnostics': {
            'top9': prefix_diag(9),
            'top11': prefix_diag(11),
        },
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
                'v45_total_order_sha256': v40.order_sha(sugar_v45_order),
                'exact_v31_unchanged': True,
            },
            'hdbscan': {
                'family_count': HDB_N,
                'joint_positive_candidate_count': joint_count,
                'nonjoint_candidate_count': nonjoint_count,
                'moved_up_in_total_order_count': moved_up,
                'moved_down_in_total_order_count': moved_down,
                'unchanged_count': unchanged,
                'v31_order_sha256': v40.order_sha(hdb_v31_order),
                'v45_total_order_sha256': v40.order_sha(hdb_v45_order),
                'nonjoint_positions_unchanged': True,
                'joint_slot_set_unchanged': True,
            },
        },
        'hdb_candidate_rows': hdb_rows,
        'full_model_freeze': freeze,
        'component_percentile_threshold_search': False,
        'quality_suppression_magnitude_rule': False,
        'third_sign_filter_used': False,
        'equal_ranksum_used': False,
        'weighted_fusion_used': False,
        'top_k_selected': False,
        'oracle_correction_count_used': False,
        'rank_window_selected': False,
        'promotion_coefficient_search': False,
        'promotion_interpolation_search': False,
        'promotion_bonus_search': False,
        'promotion_cap_search': False,
        'slot_expansion': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'sugar_modified': False,
        'alternate_quality_order_search': False,
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
    (output / 'V45_COMPONENT_PRIORITIZED_JOINT_SLOT_RESULT.json').write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
    )
    print(json.dumps({
        'verdict': result['verdict'],
        'panel_wins': wins,
        'joint_positive_candidate_count': joint_count,
        'prefix_diagnostics': result['prefix_diagnostics'],
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
    e.add_argument('--placement-diagnostic', type=Path, required=True)
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
        a.placement_diagnostic,
        a.output,
    )


if __name__ == '__main__':
    raise SystemExit(main())

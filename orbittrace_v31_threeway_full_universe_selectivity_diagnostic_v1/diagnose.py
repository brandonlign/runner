#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from orbittrace_v40_component_best_evidence_representative_v1 import train_evaluate as v40

GRAPH_SHA256 = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA256 = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
JOINT_SIGNAL_SHA256 = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
THREEWAY_AUTH_SHA256 = '31681b318f6e2732cd8338d484959dfdcade08d65b7f90225d9a0c269d4630eb'
JOINT_SOURCE_RUN = 31457923695
JOINT_SOURCE_ARTIFACT = 9088724826
THREEWAY_AUTH_RUN = 31458509957
THREEWAY_AUTH_ARTIFACT = 9088912217
HDB_N = 229
SUGAR_N = 267
PARENT_JOINT_N = 60
RECOVERY = 0.5
EXPECTED_V31 = {
    ('sugar', 2013): (0.2719801488280529, 16),
    ('sugar', 2014): (0.31529041952487225, 17),
    ('hdbscan', 2013): (0.14888037368183737, 9),
    ('hdbscan', 2014): (0.15198123772301594, 9),
}


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


def fraction(n: int, d: int) -> float:
    require(d > 0, 'empty conditional selector class')
    return float(n / d)


def validate_joint_signal(path: Path) -> dict[str, Any]:
    require(sha(path) == JOINT_SIGNAL_SHA256, '#1098 joint-signal file identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', '#1098 signal verdict changed')
    require(r['scientific_role'] == 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION', '#1098 signal role changed')
    require(int(r['family_count']) == HDB_N and len(r['families']) == HDB_N, '#1098 HDB family universe changed')
    require(sum(bool(x['joint_signal']) for x in r['families']) == PARENT_JOINT_N, '#1098 joint-positive count changed')
    require(r['graph_sha256'] == GRAPH_SHA256 and r['component_sha256'] == COMPONENT_SHA256, '#1098 geometry identity changed')
    for k in (
        'threshold_selected', 'top_k_selected', 'rank_window_selected',
        'alternate_boolean_rule_evaluated', 'oracle_identity_hardcoded',
        'target_information_access', 'target_region_events_accessed',
        'maarsy_scientific_access', 'dms_scientific_access',
    ):
        require(r[k] is False, f'#1098 forbidden flag changed: {k}')
    require(r['blind_exclusion'] == [20.0, 55.0], '#1098 blind exclusion changed')
    for row in r['families']:
        require(bool(row['joint_signal']) == bool(row['positive_quality_suppression'] and row['component_closure_opportunity']), '#1098 joint Boolean changed')
    return r


def validate_threeway_authorization(path: Path) -> dict[str, Any]:
    require(sha(path) == THREEWAY_AUTH_SHA256, '#1114 authorization identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V31_THREEWAY_CONSENSUS_DIAGNOSTIC', '#1114 verdict changed')
    require(r['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_THREEWAY_SELECTOR_ORDER_OR_SUCCESSOR_EVALUATED', '#1114 role changed')
    require(r['threeway_definition'] == 'positive_quality_suppression AND component_closure_opportunity AND crossroute_positive', '#1114 definition changed')
    require(r['threeway_direction_supported_both_years'] is True, '#1114 direction not supported')
    for k in (
        'new_rank_or_score_evaluated', 'selector_order_evaluated',
        'replacement_rule_evaluated', 'promotion_position_evaluated',
        'literature_panel_evaluated', 'successor_selected',
        'threshold_search', 'boolean_combination_search', 'rank_window_search',
        'top_k_search', 'candidate_membership_changed', 'candidate_generation_changed',
        'oracle_identity_used_for_statistic', 'post_result_second_search',
    ):
        require(r[k] is False, f'#1114 forbidden flag changed: {k}')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1114 SonotaCo role changed')
    require(r['target_information_access'] is False and r['target_region_events_accessed'] is False, '#1114 protected target access changed')
    require(r['maarsy_scientific_access'] is False and r['dms_scientific_access'] is False, '#1114 protected survey access changed')
    require(r['blind_exclusion'] == [20.0, 55.0], '#1114 blind exclusion changed')
    return r


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    return int(v40.pretruth_mode(sugar_root, hdbscan_root, output))


def diagnose_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    component_file: Path,
    joint_signal_file: Path,
    threeway_authorization_file: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(sha(graph_file) == GRAPH_SHA256, 'pretruth graph identity changed')
    require(sha(component_file) == COMPONENT_SHA256, 'pretruth component identity changed')
    graph = json.loads(graph_file.read_text())
    comp = json.loads(component_file.read_text())
    require(graph['truth_accessed'] is False and comp['truth_accessed'] is False, 'geometry is not pretruth')
    require(int(graph['edge_count']) == 2334 and float(graph['radius']) == 1.0, 'frozen graph shape changed')
    require(int(comp['component_count']) == 196, 'frozen component count changed')
    require(graph['target_information_access'] is False and comp['target_information_access'] is False, 'geometry target access changed')
    require(graph['maarsy_scientific_access'] is False and graph['dms_scientific_access'] is False, 'graph protected survey access changed')
    require(comp['maarsy_scientific_access'] is False and comp['dms_scientific_access'] is False, 'component protected survey access changed')
    require(graph['blind_exclusion'] == [20.0, 55.0] and comp['blind_exclusion'] == [20.0, 55.0], 'geometry blind exclusion changed')

    parent_signal = validate_joint_signal(joint_signal_file)
    validate_threeway_authorization(threeway_authorization_file)

    captured_orders: dict[str, list[str]] = {}
    captured_rank_maps: dict[str, dict[str, int]] = {}
    original_builder = v40.build_v40_order

    def capture_no_reorder(
        route: str,
        base_order: list[str],
        components: list[dict[str, Any]],
        rank_maps: dict[str, dict[str, int]],
    ) -> tuple[list[str], list[dict[str, Any]]]:
        captured_orders[route] = list(map(str, base_order))
        for rr, mapping in rank_maps.items():
            captured_rank_maps[rr] = {str(k): int(v) for k, v in mapping.items()}
        rows = [{'representative_family_id': str(fid)} for fid in base_order]
        return list(map(str, base_order)), rows

    v40.build_v40_order = capture_no_reorder
    try:
        engine_out = output / '_v31_capture_engine'
        rc = v40.evaluate_mode(
            sugar_root,
            hdbscan_root,
            truth_root,
            ranker_source,
            graph_file,
            component_file,
            engine_out,
        )
    finally:
        v40.build_v40_order = original_builder
    require(rc == 0, 'frozen v31 capture engine failed')
    require(set(captured_orders) == {'sugar', 'hdbscan'}, 'failed to capture exact v31 route orders')
    require(len(captured_orders['sugar']) == SUGAR_N and len(captured_orders['hdbscan']) == HDB_N, 'v31 route universe changed')
    require(set(captured_rank_maps) == {'sugar', 'hdbscan'}, 'failed to capture exact v31 rank maps')

    engine = json.loads((engine_out / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_RESULT.json').read_text())
    require(engine['parent_v31_reproduction_pass'] is True and len(engine['parent_v31_controls']) == 4, 'exact v31 parent reproduction failed')
    controls = {
        (str(r['comparator']), int(r['year'])): (float(r['macro_f1']), int(r['recovered_f1_gt_0_5']))
        for r in engine['parent_v31_controls']
    }
    for key, exp in EXPECTED_V31.items():
        require(key in controls and abs(controls[key][0] - exp[0]) < 1e-12 and controls[key][1] == exp[1], f'v31 control mismatch {key}')
    for row in engine['panels']:
        key = (str(row['comparator']), int(row['year']))
        require(abs(float(row['candidate_macro_f1']) - EXPECTED_V31[key][0]) < 1e-12, f'capture order changed macro {key}')
        require(int(row['candidate_recovered_f1_gt_0_5']) == EXPECTED_V31[key][1], f'capture order changed recovery {key}')

    sugar_ids = list(map(str, graph['sugar_family_ids']))
    hdb_ids = list(map(str, graph['hdbscan_family_ids']))
    adjacency = graph['hdbscan_to_sugar_adjacency']
    require(len(sugar_ids) == SUGAR_N and len(set(sugar_ids)) == SUGAR_N, 'graph Sugar family universe changed')
    require(len(hdb_ids) == HDB_N and len(set(hdb_ids)) == HDB_N, 'graph HDB family universe changed')
    require(len(adjacency) == HDB_N, 'graph HDB adjacency length changed')
    require(set(sugar_ids) == set(captured_orders['sugar']), 'graph/v31 Sugar universe mismatch')
    require(set(hdb_ids) == set(captured_orders['hdbscan']), 'graph/v31 HDB universe mismatch')

    parent_rows = {str(r['family_id']): r for r in parent_signal['families']}
    require(set(parent_rows) == set(hdb_ids), '#1098 signal/graph HDB universe mismatch')
    signal_rows: list[dict[str, Any]] = []
    for hi, fid in enumerate(hdb_ids):
        p = parent_rows[fid]
        hrank = int(captured_rank_maps['hdbscan'][fid])
        ph = float((hrank - 1) / (HDB_N - 1))
        require(int(p['v31_rank']) == hrank, f'#1098/v31 rank mismatch for {fid}')
        require(abs(float(p['v31_percentile']) - ph) < 1e-15, f'#1098/v31 percentile mismatch for {fid}')
        raw_neighbors = adjacency[hi]
        require(isinstance(raw_neighbors, list), f'invalid adjacency row for {fid}')
        neighbor_indices = [int(x) for x in raw_neighbors]
        require(all(0 <= j < SUGAR_N for j in neighbor_indices), f'invalid Sugar neighbor index for {fid}')
        if neighbor_indices:
            ranked = sorted(
                (
                    int(captured_rank_maps['sugar'][sugar_ids[j]]),
                    sugar_ids[j],
                )
                for j in neighbor_indices
            )
            best_rank, best_fid = ranked[0]
            best_p = float((best_rank - 1) / (SUGAR_N - 1))
            direct_positive = bool(best_p < ph)
            best_neighbor_id: str | None = str(best_fid)
            best_neighbor_rank: int | None = int(best_rank)
            best_neighbor_percentile: float | None = best_p
        else:
            direct_positive = False
            best_neighbor_id = None
            best_neighbor_rank = None
            best_neighbor_percentile = None
        joint = bool(p['joint_signal'])
        threeway = bool(joint and direct_positive)
        signal_rows.append({
            'family_id': fid,
            'v31_hdb_rank': hrank,
            'v31_hdb_percentile': ph,
            'positive_quality_suppression': bool(p['positive_quality_suppression']),
            'component_closure_opportunity': bool(p['component_closure_opportunity']),
            'parent_joint_signal': joint,
            'direct_sugar_neighbor_count': len(neighbor_indices),
            'best_direct_sugar_neighbor_family_id': best_neighbor_id,
            'best_direct_sugar_neighbor_v31_rank': best_neighbor_rank,
            'best_direct_sugar_neighbor_v31_percentile': best_neighbor_percentile,
            'direct_crossroute_positive': direct_positive,
            'threeway_signal': threeway,
            'component_best_v31_percentile': float(p['component_best_v31_percentile']),
        })

    parent_joint_count = int(sum(bool(r['parent_joint_signal']) for r in signal_rows))
    direct_positive_count = int(sum(bool(r['direct_crossroute_positive']) for r in signal_rows))
    threeway_count = int(sum(bool(r['threeway_signal']) for r in signal_rows))
    require(parent_joint_count == PARENT_JOINT_N, 'parent joint count changed during extension')
    require(all((not r['threeway_signal']) or r['parent_joint_signal'] for r in signal_rows), 'three-way flag is not a subset of parent joint gate')

    vector = {
        'verdict': 'PASS_V31_THREEWAY_FULL_UNIVERSE_SIGNAL_FREEZE',
        'scientific_role': 'FIXED_229_HDB_THREEWAY_SELECTOR_VECTOR_BEFORE_RECOVERABILITY_SUMMARIES',
        'family_count': HDB_N,
        'parent_joint_family_count': parent_joint_count,
        'direct_crossroute_positive_family_count': direct_positive_count,
        'threeway_family_count': threeway_count,
        'threeway_family_fraction': float(threeway_count / HDB_N),
        'direct_crossroute_definition': 'best direct radius-1 Sugar exact-v31 normalized rank percentile < own HDB exact-v31 normalized rank percentile; false if no direct Sugar neighbor',
        'threeway_definition': 'parent_joint_signal AND direct_crossroute_positive',
        'parent_joint_source_run': JOINT_SOURCE_RUN,
        'parent_joint_source_artifact': JOINT_SOURCE_ARTIFACT,
        'parent_joint_source_sha256': JOINT_SIGNAL_SHA256,
        'threeway_authorization_run': THREEWAY_AUTH_RUN,
        'threeway_authorization_artifact': THREEWAY_AUTH_ARTIFACT,
        'threeway_authorization_sha256': THREEWAY_AUTH_SHA256,
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'families': signal_rows,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'edge_distance_rule_selected': False,
        'neighbor_count_rule_selected': False,
        'alternate_neighbor_aggregation_evaluated': False,
        'alternate_boolean_rule_evaluated': False,
        'oracle_identity_hardcoded': False,
        'truth_aware_group_identity_used_for_signal': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    vector_sha = canonical_sha(vector)
    vector['canonical_sha256_without_self_field'] = vector_sha
    vector_path = output / 'V31_THREEWAY_FULL_UNIVERSE_SIGNAL.json'
    vector_path.write_text(json.dumps(vector, indent=2, sort_keys=True, allow_nan=False) + '\n')

    # Outcome-recoverability summaries begin only after the complete 229-family vector above is fixed.
    hmeta = json.loads((hdbscan_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    hfp = json.loads((hdbscan_root / 'family_memberships.json').read_text())
    require(hmeta['truth_accessed'] is False and hfp['truth_accessed'] is False, 'HDB payload not pretruth')
    hids = list(map(str, hmeta['family_ids']))
    fams = list(hfp['families'])
    require(len(hids) == HDB_N and [str(f['family_id']) for f in fams] == hids, 'HDB membership identity changed')
    require(set(hids) == set(hdb_ids), 'HDB payload/graph universe mismatch')
    require(hmeta['target_information_access'] is False, 'HDB payload target access changed')
    require(hmeta['maarsy_scientific_access'] is False and hmeta['dms_scientific_access'] is False, 'HDB payload protected survey access changed')

    by = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v40.v22.eligible_from_year_truth(by)
    hidden: dict[str, Any] = {}
    hidden.update(by[2013])
    hidden.update(by[2014])
    flag_by_id = {str(r['family_id']): r for r in signal_rows}

    truth_rows: list[dict[str, Any]] = []
    for fid, fam in zip(hids, fams):
        t = v40.v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v40.v24.annual_f1_for_fixed_label(fam, str(label), by))
            group = 'SHOWER/' + str(label)
        else:
            f13 = f14 = 0.0
            group = 'NEG/' + fid
        s = flag_by_id[fid]
        truth_rows.append({
            'family_id': fid,
            'diagnostic_group': group,
            'parent_joint_signal': bool(s['parent_joint_signal']),
            'direct_crossroute_positive': bool(s['direct_crossroute_positive']),
            'threeway_signal': bool(s['threeway_signal']),
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
        })

    annual: dict[str, Any] = {}
    direction_flags: list[bool] = []
    for year in (2013, 2014):
        rk = f'recoverable_{year}'
        joint_rows = [r for r in truth_rows if r['parent_joint_signal']]
        tri = [r for r in joint_rows if r['threeway_signal']]
        residual = [r for r in joint_rows if not r['threeway_signal']]
        require(len(joint_rows) == PARENT_JOINT_N, f'{year} parent joint population changed')
        require(tri and residual, f'{year} empty threeway/joint-only family class')
        tri_rec = int(sum(bool(r[rk]) for r in tri))
        residual_rec = int(sum(bool(r[rk]) for r in residual))
        tri_frac = fraction(tri_rec, len(tri))
        residual_frac = fraction(residual_rec, len(residual))
        family_pass = bool(tri_frac > residual_frac)

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in joint_rows:
            grouped[str(r['diagnostic_group'])].append(r)
        triple_groups: list[dict[str, Any]] = []
        residual_groups: list[dict[str, Any]] = []
        for group, rows in sorted(grouped.items()):
            triple_members = [r for r in rows if r['threeway_signal']]
            residual_members = [r for r in rows if not r['threeway_signal']]
            if triple_members:
                triple_groups.append({
                    'diagnostic_group': group,
                    'selected_family_count': len(triple_members),
                    'recoverable': bool(any(bool(r[rk]) for r in triple_members)),
                })
            else:
                require(residual_members, 'empty parent-joint diagnostic group')
                residual_groups.append({
                    'diagnostic_group': group,
                    'selected_family_count': len(residual_members),
                    'recoverable': bool(any(bool(r[rk]) for r in residual_members)),
                })
        require(triple_groups and residual_groups, f'{year} empty threeway/joint-only group class')
        tri_g_rec = int(sum(bool(r['recoverable']) for r in triple_groups))
        residual_g_rec = int(sum(bool(r['recoverable']) for r in residual_groups))
        tri_g_frac = fraction(tri_g_rec, len(triple_groups))
        residual_g_frac = fraction(residual_g_rec, len(residual_groups))
        group_pass = bool(tri_g_frac > residual_g_frac)
        direction_flags.extend([family_pass, group_pass])

        annual[str(year)] = {
            'family_level': {
                'threeway_count': len(tri),
                'joint_only_count': len(residual),
                'threeway_recoverable_count': tri_rec,
                'joint_only_recoverable_count': residual_rec,
                'threeway_recoverable_fraction': tri_frac,
                'joint_only_recoverable_fraction': residual_frac,
                'threeway_minus_joint_only_fraction': float(tri_frac - residual_frac),
                'direction_pass': family_pass,
            },
            'diagnostic_group_level': {
                'threeway_group_count': len(triple_groups),
                'joint_only_group_count': len(residual_groups),
                'threeway_group_recoverable_count': tri_g_rec,
                'joint_only_group_recoverable_count': residual_g_rec,
                'threeway_group_recoverable_fraction': tri_g_frac,
                'joint_only_group_recoverable_fraction': residual_g_frac,
                'threeway_minus_joint_only_group_fraction': float(tri_g_frac - residual_g_frac),
                'direction_pass': group_pass,
            },
        }

    breadth_pass = bool(1 <= threeway_count < PARENT_JOINT_N)
    passed = bool(breadth_pass and all(direction_flags))
    result = {
        'verdict': 'PASS_V31_THREEWAY_FULL_UNIVERSE_SELECTIVITY_DIAGNOSTIC' if passed else 'FAIL_V31_THREEWAY_FULL_UNIVERSE_SELECTIVITY_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_CONDITIONAL_SELECTOR_SPECIFICITY_DIAGNOSTIC_NO_ORDER_OR_SUCCESSOR_EVALUATED',
        'question': 'Does the direct cross-route sign strictly prune the fixed 60-family #1098 gate and enrich recoverability among retained three-way families/groups versus the joint-positive families/groups it removes?',
        'threeway_direction_supported_both_years_both_levels': passed,
        'breadth_refinement_pass': breadth_pass,
        'family_count': HDB_N,
        'parent_joint_family_count': parent_joint_count,
        'threeway_family_count': threeway_count,
        'threeway_family_fraction_of_all_hdb': float(threeway_count / HDB_N),
        'threeway_fraction_of_parent_joint': float(threeway_count / PARENT_JOINT_N),
        'direct_crossroute_positive_family_count_all_hdb': direct_positive_count,
        'signal_vector_sha256': vector_sha,
        'parent_joint_source_run': JOINT_SOURCE_RUN,
        'parent_joint_source_artifact': JOINT_SOURCE_ARTIFACT,
        'parent_joint_source_sha256': JOINT_SIGNAL_SHA256,
        'threeway_authorization_run': THREEWAY_AUTH_RUN,
        'threeway_authorization_artifact': THREEWAY_AUTH_ARTIFACT,
        'threeway_authorization_sha256': THREEWAY_AUTH_SHA256,
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': engine['parent_v31_controls'],
        'annual_diagnostics': annual,
        'new_rank_or_score_evaluated': False,
        'candidate_total_order_evaluated': False,
        'selector_order_evaluated': False,
        'placement_rule_evaluated': False,
        'replacement_rule_evaluated': False,
        'literature_panel_evaluated': False,
        'successor_selected': False,
        'threshold_search': False,
        'effect_size_threshold_selected': False,
        'top_k_search': False,
        'rank_window_search': False,
        'edge_distance_rule_search': False,
        'neighbor_count_rule_search': False,
        'alternate_neighbor_aggregation_search': False,
        'boolean_combination_search': False,
        'pairwise_fallback_evaluated': False,
        'or_logic_search': False,
        'xor_logic_search': False,
        'component_size_search': False,
        'q_calibration_search': False,
        'quality_suppression_magnitude_search': False,
        'route_specific_rule': False,
        'year_specific_rule': False,
        'budget_specific_rule': False,
        'graph_or_component_redefinition': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'diversity_search': False,
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
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V31_THREEWAY_FULL_UNIVERSE_SELECTIVITY_DIAGNOSTIC.json').write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('pretruth')
    a.add_argument('--sugar-root', type=Path, required=True)
    a.add_argument('--hdbscan-root', type=Path, required=True)
    a.add_argument('--output', type=Path, required=True)
    b = sub.add_parser('diagnose')
    b.add_argument('--sugar-root', type=Path, required=True)
    b.add_argument('--hdbscan-root', type=Path, required=True)
    b.add_argument('--truth-root', type=Path, required=True)
    b.add_argument('--ranker-source', type=Path, required=True)
    b.add_argument('--graph-file', type=Path, required=True)
    b.add_argument('--component-file', type=Path, required=True)
    b.add_argument('--joint-signal-file', type=Path, required=True)
    b.add_argument('--threeway-authorization-file', type=Path, required=True)
    b.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.mode == 'pretruth':
        return pretruth_mode(args.sugar_root, args.hdbscan_root, args.output)
    return diagnose_mode(
        args.sugar_root,
        args.hdbscan_root,
        args.truth_root,
        args.ranker_source,
        args.graph_file,
        args.component_file,
        args.joint_signal_file,
        args.threeway_authorization_file,
        args.output,
    )


if __name__ == '__main__':
    raise SystemExit(main())

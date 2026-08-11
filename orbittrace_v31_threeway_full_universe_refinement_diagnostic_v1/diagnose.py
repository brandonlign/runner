#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

SOURCE_RUN = 31457788803
SOURCE_ARTIFACT = 9088683367
SOURCE_ZIP_DIGEST = 'sha256:1ad3513e021136b402e8aa121faa37675e2982d57aa2a14f1bc5e28d81b61b11'
SOURCE_SIGNAL_SHA = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
SOURCE_ENGINE_SHA = '6cb413b133a0bff6886b7108e9a383d4a341ff254cc70b175dbdf595609e4732'
GRAPH_SHA = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
JOINT_CANONICAL_SHA = '47966ec3e5b29f56c5bb536ed19f24a99ff41f11bc2d20778240b16c5e44fd47'
CROSS_RUN = 31457199102
CROSS_ARTIFACT = 9088482597
CROSS_ZIP_DIGEST = 'sha256:c709ca3f5aaef103a1cf7668fce7241cb52a4c43b36c0263d5b6b34b8208e6c4'
CROSS_RESULT_SHA = '62ed82eeb4f10b4371ec2072af7de527482ab070866693a2230be564ebf6af35'
N_HDB = 229
N_SUGAR = 267
JOINT_COUNT = 60
RECOVERY = 0.5


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256('\n'.join(order).encode()).hexdigest()


def canonical_sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n'
    return hashlib.sha256(raw.encode()).hexdigest()


def freeze_vector(source_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    signal_path = source_root / 'diag' / 'V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL.json'
    engine_path = source_root / 'diag' / '_v31_capture_engine' / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_RESULT.json'
    graph_path = source_root / 'pretruth' / 'CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY.json'
    require(signal_path.is_file() and engine_path.is_file() and graph_path.is_file(), '#1098 source artifact incomplete')
    require(sha(signal_path) == SOURCE_SIGNAL_SHA, '#1098 signal JSON changed')
    require(sha(engine_path) == SOURCE_ENGINE_SHA, '#1098 capture engine JSON changed')
    require(sha(graph_path) == GRAPH_SHA, '#1098 graph JSON changed')

    signal = json.loads(signal_path.read_text())
    engine = json.loads(engine_path.read_text())
    graph = json.loads(graph_path.read_text())

    require(signal['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', '#1098 signal verdict changed')
    require(signal['scientific_role'] == 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION', '#1098 signal role changed')
    require(signal['canonical_sha256_without_self_field'] == JOINT_CANONICAL_SHA, '#1098 canonical signal identity changed')
    require(signal['joint_signal_definition'] == '(v31_percentile > quality_percentile) AND (component_best_v31_percentile < v31_percentile)', '#1098 joint definition changed')
    require(int(signal['family_count']) == N_HDB and len(signal['families']) == N_HDB, '#1098 HDB universe changed')
    require(sum(bool(r['joint_signal']) for r in signal['families']) == JOINT_COUNT, '#1098 joint family count changed')
    for k in ('threshold_selected', 'top_k_selected', 'rank_window_selected', 'alternate_boolean_rule_evaluated', 'oracle_identity_hardcoded', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(signal[k] is False, f'#1098 signal firewall changed: {k}')
    require(signal['blind_exclusion'] == [20.0, 55.0], '#1098 blind exclusion changed')

    require(engine['parent_v31_reproduction_pass'] is True, '#1098 v31 capture reproduction changed')
    sugar_order = [str(r['representative_family_id']) for r in engine['primary_component_rows']['sugar']]
    hdb_order = [str(r['representative_family_id']) for r in engine['primary_component_rows']['hdbscan']]
    require(len(sugar_order) == N_SUGAR and len(set(sugar_order)) == N_SUGAR, 'captured Sugar order changed')
    require(len(hdb_order) == N_HDB and len(set(hdb_order)) == N_HDB, 'captured HDB order changed')
    require(order_sha(sugar_order) == engine['order_diagnostics']['sugar']['v31_fused_order_sha256'], 'Sugar order SHA mismatch')
    require(order_sha(hdb_order) == engine['order_diagnostics']['hdbscan']['v31_fused_order_sha256'], 'HDB order SHA mismatch')

    require(graph['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY' and graph['truth_accessed'] is False, 'graph identity changed')
    require(int(graph['edge_count']) == 2334, 'graph edge count changed')
    require(graph['target_information_access'] is False and graph['target_region_events_accessed'] is False, 'graph target firewall changed')
    require(graph['maarsy_scientific_access'] is False and graph['dms_scientific_access'] is False, 'graph survey firewall changed')
    require(graph['blind_exclusion'] == [20.0, 55.0], 'graph blind exclusion changed')

    sugar_ids = list(map(str, graph['sugar_family_ids']))
    hdb_ids = list(map(str, graph['hdbscan_family_ids']))
    require(len(sugar_ids) == N_SUGAR and len(set(sugar_ids)) == N_SUGAR and set(sugar_ids) == set(sugar_order), 'graph Sugar universe changed')
    require(len(hdb_ids) == N_HDB and len(set(hdb_ids)) == N_HDB and set(hdb_ids) == set(hdb_order), 'graph HDB universe changed')
    require(len(graph['hdbscan_to_sugar_adjacency']) == N_HDB, 'graph HDB adjacency changed')

    sugar_rank = {fid: i + 1 for i, fid in enumerate(sugar_order)}
    hdb_rank = {fid: i + 1 for i, fid in enumerate(hdb_order)}
    hdb_graph_index = {fid: i for i, fid in enumerate(hdb_ids)}
    source_rows = {str(r['family_id']): r for r in signal['families']}
    require(len(source_rows) == N_HDB and set(source_rows) == set(hdb_order), '#1098 family rows changed')

    rows: list[dict[str, Any]] = []
    for source_row in signal['families']:
        fid = str(source_row['family_id'])
        vrank = int(source_row['v31_rank'])
        vpercentile = float(source_row['v31_percentile'])
        require(vrank == hdb_rank[fid], f'HDB rank mismatch for {fid}')
        require(abs(vpercentile - ((vrank - 1) / 228.0)) < 1e-15, f'HDB percentile mismatch for {fid}')
        positive_quality = bool(source_row['positive_quality_suppression'])
        component_opportunity = bool(source_row['component_closure_opportunity'])
        joint = bool(source_row['joint_signal'])
        require(joint == bool(positive_quality and component_opportunity), f'joint sign mismatch for {fid}')

        adjacency = list(map(int, graph['hdbscan_to_sugar_adjacency'][hdb_graph_index[fid]]))
        for j in adjacency:
            require(0 <= j < N_SUGAR, f'invalid Sugar adjacency index for {fid}')
        if adjacency:
            best_sugar_rank = min(sugar_rank[sugar_ids[j]] for j in adjacency)
            best_sugar_percentile = float((best_sugar_rank - 1) / 266.0)
            gap = float(vpercentile - best_sugar_percentile)
            cross_positive = bool(gap > 0.0)
        else:
            best_sugar_rank = None
            best_sugar_percentile = None
            gap = None
            cross_positive = False

        rows.append({
            'family_id': fid,
            'v31_rank': vrank,
            'v31_percentile': vpercentile,
            'positive_quality_suppression': positive_quality,
            'component_closure_opportunity': component_opportunity,
            'joint_signal': joint,
            'sugar_neighbor_count': len(adjacency),
            'best_sugar_rank': best_sugar_rank,
            'best_sugar_percentile': best_sugar_percentile,
            'crossroute_rank_gap': gap,
            'crossroute_positive': cross_positive,
            'threeway_signal': bool(joint and cross_positive),
        })

    triple_count = sum(bool(r['threeway_signal']) for r in rows)
    vector = {
        'verdict': 'PASS_V31_THREEWAY_FULL_UNIVERSE_VECTOR_FREEZE',
        'scientific_role': 'FULL_FIXED_229_HDB_THREEWAY_VECTOR_FROZEN_BEFORE_VALIDATION_OR_OUTCOME_AUDIT',
        'source_run': SOURCE_RUN,
        'source_artifact': SOURCE_ARTIFACT,
        'source_zip_digest': SOURCE_ZIP_DIGEST,
        'source_signal_sha256': SOURCE_SIGNAL_SHA,
        'source_engine_sha256': SOURCE_ENGINE_SHA,
        'graph_sha256': GRAPH_SHA,
        'family_count': N_HDB,
        'joint_family_count': JOINT_COUNT,
        'threeway_family_count': triple_count,
        'threeway_definition': 'joint_signal AND crossroute_positive',
        'crossroute_rank_gap_definition': 'v31_hdb_percentile - best_radius1_sugar_neighbor_v31_percentile',
        'crossroute_positive_definition': 'crossroute_rank_gap > 0; no Sugar neighbor is false',
        'families': rows,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'neighbor_aggregation_search': False,
        'alternate_crossroute_statistic_search': False,
        'boolean_combination_search': False,
        'new_rank_or_score_evaluated': False,
        'selector_order_evaluated': False,
        'replacement_rule_evaluated': False,
        'promotion_position_evaluated': False,
        'literature_panel_evaluated': False,
        'oracle_identity_hardcoded': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    vector_sha = canonical_sha(vector)
    vector['canonical_sha256_without_self_field'] = vector_sha
    out = output / 'V31_THREEWAY_FULL_UNIVERSE_VECTOR.json'
    out.write_text(json.dumps(vector, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': vector['verdict'],
        'family_count': N_HDB,
        'joint_family_count': JOINT_COUNT,
        'threeway_family_count': triple_count,
        'canonical_sha256_without_self_field': vector_sha,
    }, indent=2, sort_keys=True))
    return 0


def recoverability_stats(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    require(rows, f'empty {key} stratum')
    rec = sum(bool(r['recoverable']) for r in rows)
    return {
        'count': len(rows),
        'recoverable_count': rec,
        'recoverable_fraction': float(rec / len(rows)),
    }


def compare_strata(threeway: list[dict[str, Any]], joint_only: list[dict[str, Any]]) -> dict[str, Any]:
    a = recoverability_stats(threeway, 'threeway')
    b = recoverability_stats(joint_only, 'joint_only')
    pa = float(a['recoverable_fraction'])
    pb = float(b['recoverable_fraction'])
    infinite = bool(pb == 0.0 and pa > 0.0)
    rr = None if pb == 0.0 else float(pa / pb)
    rr_pass = bool(infinite or (rr is not None and rr > 1.0))
    direction = bool(pa > pb and rr_pass)
    return {
        'threeway': a,
        'joint_only': b,
        'threeway_minus_joint_only_recoverable_fraction': float(pa - pb),
        'risk_ratio': rr,
        'risk_ratio_infinite': infinite,
        'risk_ratio_condition_pass': rr_pass,
        'direction_pass': direction,
    }


def audit_vector(vector_path: Path, cross_result: Path, hdb_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    vector = json.loads(vector_path.read_text())
    require(vector['verdict'] == 'PASS_V31_THREEWAY_FULL_UNIVERSE_VECTOR_FREEZE', 'three-way vector verdict changed')
    require(vector['scientific_role'] == 'FULL_FIXED_229_HDB_THREEWAY_VECTOR_FROZEN_BEFORE_VALIDATION_OR_OUTCOME_AUDIT', 'three-way vector role changed')
    require(int(vector['family_count']) == N_HDB and len(vector['families']) == N_HDB, 'three-way vector universe changed')
    require(int(vector['joint_family_count']) == JOINT_COUNT, 'three-way source joint count changed')
    require(vector['threeway_definition'] == 'joint_signal AND crossroute_positive', 'three-way definition changed')
    for k in ('threshold_selected', 'top_k_selected', 'rank_window_selected', 'neighbor_aggregation_search', 'alternate_crossroute_statistic_search', 'boolean_combination_search', 'new_rank_or_score_evaluated', 'selector_order_evaluated', 'replacement_rule_evaluated', 'promotion_position_evaluated', 'literature_panel_evaluated', 'oracle_identity_hardcoded', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(vector[k] is False, f'vector firewall changed: {k}')
    require(vector['blind_exclusion'] == [20.0, 55.0], 'vector blind exclusion changed')
    expected_vector_sha = str(vector['canonical_sha256_without_self_field'])
    check = dict(vector)
    del check['canonical_sha256_without_self_field']
    require(canonical_sha(check) == expected_vector_sha, 'three-way vector canonical SHA mismatch')

    rows_by_id = {str(r['family_id']): r for r in vector['families']}
    require(len(rows_by_id) == N_HDB, 'three-way vector duplicate family')

    cross = json.loads(cross_result.read_text())
    require(sha(cross_result) == CROSS_RESULT_SHA, '#1093 result SHA changed')
    require(cross['verdict'] == 'PASS_V31_CONCORDANT_INDEPENDENT_SUPPRESSION_DIAGNOSTIC', '#1093 verdict changed')
    require(cross['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CONCORDANT_SELECTOR_OR_SUCCESSOR_EVALUATED', '#1093 role changed')
    require(cross['crossroute_positive_definition'] == 'crossroute_rank_gap>0; unlinked/no usable Sugar rank is false', '#1093 cross-route sign changed')
    require(cross['new_rank_or_score_evaluated'] is False and cross['selector_evaluated'] is False and cross['replacement_rule_evaluated'] is False and cross['successor_selected'] is False, '#1093 not diagnostic-only')
    require(cross['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1093 SonotaCo role changed')
    require(cross['target_information_access'] is False and cross['target_region_events_accessed'] is False, '#1093 target firewall changed')
    require(cross['maarsy_scientific_access'] is False and cross['dms_scientific_access'] is False, '#1093 survey firewall changed')
    require(cross['blind_exclusion'] == [20.0, 55.0], '#1093 blind exclusion changed')

    validated_rows = 0
    for year in ('2013', '2014'):
        for r in cross['annual_diagnostics'][year]['groups']:
            fid = str(r['representative_family_id'])
            require(fid in rows_by_id, f'#1093 representative missing from vector: {fid}')
            vr = rows_by_id[fid]
            require(int(vr['v31_rank']) == int(r['v31_rank']), f'#1093 v31 rank mismatch for {fid}')
            require(bool(vr['crossroute_positive']) == bool(r['crossroute_positive']), f'#1093 cross-route sign mismatch for {fid}')
            a = vr['crossroute_rank_gap']
            b = r['crossroute_rank_gap']
            if a is None or b is None:
                require(a is None and b is None, f'#1093 null-gap mismatch for {fid}')
            else:
                require(abs(float(a) - float(b)) < 1e-15, f'#1093 rank-gap mismatch for {fid}')
            validated_rows += 1
    require(validated_rows == 36, '#1093 validation row count changed')

    hfp = json.loads((hdb_root / 'family_memberships.json').read_text())
    hmeta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    require(hfp['truth_accessed'] is False and hmeta['truth_accessed'] is False, '#950 HDB payload not pretruth')
    fams = hfp['families']
    require(len(fams) == N_HDB and [str(f['family_id']) for f in fams] == list(map(str, hmeta['family_ids'])), '#950 HDB family identity changed')
    require(set(rows_by_id) == {str(f['family_id']) for f in fams}, '#950/vector family universe mismatch')

    from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
    from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24

    by_year = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v22.eligible_from_year_truth(by_year)
    hidden: dict[str, str] = {}
    hidden.update(by_year[2013])
    hidden.update(by_year[2014])

    truth_rows: list[dict[str, Any]] = []
    for fam in fams:
        fid = str(fam['family_id'])
        t = v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v24.annual_f1_for_fixed_label(fam, str(label), by_year))
            group = 'SHOWER/' + str(label)
        else:
            f13 = f14 = 0.0
            group = 'NEG/' + fid
        sr = rows_by_id[fid]
        truth_rows.append({
            'family_id': fid,
            'diagnostic_group': group,
            'joint_signal': bool(sr['joint_signal']),
            'threeway_signal': bool(sr['threeway_signal']),
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
        })

    triple_count = int(vector['threeway_family_count'])
    strict_subset = bool(0 < triple_count < JOINT_COUNT)
    annual: dict[str, Any] = {}
    annual_gates: list[bool] = []
    for year in (2013, 2014):
        recover_key = f'recoverable_{year}'
        family_joint = [r for r in truth_rows if r['joint_signal']]
        require(len(family_joint) == JOINT_COUNT, f'{year} joint family count changed')
        family_threeway = [dict(r, recoverable=bool(r[recover_key])) for r in family_joint if r['threeway_signal']]
        family_joint_only = [dict(r, recoverable=bool(r[recover_key])) for r in family_joint if not r['threeway_signal']]
        require(len(family_threeway) == triple_count and len(family_joint_only) == JOINT_COUNT - triple_count, f'{year} family split changed')
        family_cmp = compare_strata(family_threeway, family_joint_only)

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in truth_rows:
            grouped[str(r['diagnostic_group'])].append(r)
        group_rows: list[dict[str, Any]] = []
        for group, members in sorted(grouped.items()):
            group_rows.append({
                'diagnostic_group': group,
                'family_count': len(members),
                'group_joint': bool(any(m['joint_signal'] for m in members)),
                'group_threeway': bool(any(m['threeway_signal'] for m in members)),
                'recoverable': bool(any(m[recover_key] for m in members)),
            })
        joint_groups = [r for r in group_rows if r['group_joint']]
        threeway_groups = [r for r in joint_groups if r['group_threeway']]
        joint_only_groups = [r for r in joint_groups if not r['group_threeway']]
        require(threeway_groups and joint_only_groups, f'{year} empty group refinement stratum')
        group_cmp = compare_strata(threeway_groups, joint_only_groups)

        gate = bool(family_cmp['direction_pass'] and group_cmp['direction_pass'])
        annual_gates.append(gate)
        annual[str(year)] = {
            'interpretation_gate_pass': gate,
            'family_level_within_joint': family_cmp,
            'diagnostic_group_level_within_joint': group_cmp,
            'joint_group_count': len(joint_groups),
            'threeway_group_count': len(threeway_groups),
            'joint_only_group_count': len(joint_only_groups),
        }

    passed = bool(strict_subset and all(annual_gates))
    result = {
        'verdict': 'PASS_V31_THREEWAY_FULL_UNIVERSE_REFINEMENT_DIAGNOSTIC' if passed else 'FAIL_V31_THREEWAY_FULL_UNIVERSE_REFINEMENT_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_INCREMENTAL_FULL_UNIVERSE_SELECTOR_REFINEMENT_DIAGNOSTIC_NO_ORDER_EVALUATED',
        'source_run': SOURCE_RUN,
        'source_artifact': SOURCE_ARTIFACT,
        'source_zip_digest': SOURCE_ZIP_DIGEST,
        'source_signal_sha256': SOURCE_SIGNAL_SHA,
        'cross_validation_run': CROSS_RUN,
        'cross_validation_artifact': CROSS_ARTIFACT,
        'cross_validation_zip_digest': CROSS_ZIP_DIGEST,
        'cross_validation_result_sha256': CROSS_RESULT_SHA,
        'vector_sha256': expected_vector_sha,
        'family_count': N_HDB,
        'joint_family_count': JOINT_COUNT,
        'threeway_family_count': triple_count,
        'joint_only_family_count': JOINT_COUNT - triple_count,
        'threeway_family_fraction_of_all_hdb': float(triple_count / N_HDB),
        'threeway_family_fraction_of_joint': float(triple_count / JOINT_COUNT),
        'family_count_reduction_from_joint': JOINT_COUNT - triple_count,
        'strict_nonempty_subset_of_joint': strict_subset,
        'annual_diagnostics': annual,
        'threeway_incremental_refinement_supported_both_years': passed,
        'interpretation_gate': 'strict nonempty subset of 60 and threeway recoverability fraction > joint-only with RR>1 or infinite at family and diagnostic-group levels in both years',
        'new_rank_or_score_evaluated': False,
        'selector_order_evaluated': False,
        'replacement_rule_evaluated': False,
        'promotion_position_evaluated': False,
        'literature_panel_evaluated': False,
        'successor_selected': False,
        'signal_magnitude_used': False,
        'rank_gap_threshold_search': False,
        'threshold_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'neighbor_aggregation_search': False,
        'alternate_crossroute_statistic_search': False,
        'boolean_combination_search': False,
        'or_logic_search': False,
        'component_size_search': False,
        'route_specific_rule': False,
        'year_specific_rule': False,
        'budget_specific_rule': False,
        'feature_search': False,
        'model_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'candidate_membership_changed': False,
        'candidate_generation_changed': False,
        'oracle_identity_used_for_statistic': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = output / 'V31_THREEWAY_FULL_UNIVERSE_REFINEMENT_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    f = sub.add_parser('freeze')
    f.add_argument('--source-root', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('audit')
    a.add_argument('--vector', type=Path, required=True)
    a.add_argument('--cross-result', type=Path, required=True)
    a.add_argument('--hdb-root', type=Path, required=True)
    a.add_argument('--truth-root', type=Path, required=True)
    a.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.mode == 'freeze':
        return freeze_vector(args.source_root, args.output)
    return audit_vector(args.vector, args.cross_result, args.hdb_root, args.truth_root, args.output)


if __name__ == '__main__':
    raise SystemExit(main())

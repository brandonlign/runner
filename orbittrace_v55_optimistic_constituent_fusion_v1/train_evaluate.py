#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from orbittrace_v31_local_geometry_margin_oof_v1 import train_evaluate as v31

HDB_N = 229
V51_VECTOR_SHA256 = '5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc'
V51_VECTOR_CANONICAL = '0e13b3f9e6b791a13a3e90d853f8704573b1264dffcb67236e6423491ad70020'
V51_RESULT_SHA256 = 'fef1d2c5bb83748de5c5511615915e76ce6fcd0801afbddb0e01bab09b9ab76d'
V54_SPLIT_SHA256 = '3a065240c07e2abd0e0a6b9d0b712fd21009096c06a714237390de22ea483667'
V54_SPLIT_CANONICAL = 'b55b86574c45a509c1da3f34b7c00957a4e1926fe11e3c3fa9badff772b3d5f2'
V54_RESULT_SHA256 = '4cea3be96bd643585da4754c6ef039f454d3f83fcbdf7329ec4b1b39ff7d9159'
V31_HDB_LOCAL_SHA256 = '9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595'
V19_HDB_ORDER_SHA256 = 'e1e82ad70fb8c575ee7ee269906668931f07cbe3375c15ab84b0717b1f2c85dc'
V31_HDB_FUSED_SHA256 = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'
V55_HDB_ORDER_SHA256 = '9cb7cf0597394f7c253452ed5788eb0dce6bcc6ad6442647ecb54dc31d438132'
RANKER_SOURCE_SHA256 = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
PARENT_SOURCE_BLOB = '917e3cd6f9310ca1282e0efa58ed0924d03ed4da'
PARENT = {
    ('sugar', 2013): (0.2719801488280529, 16),
    ('sugar', 2014): (0.31529041952487225, 17),
    ('hdbscan', 2013): (0.14888037368183737, 9),
    ('hdbscan', 2014): (0.15198123772301594, 9),
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256('\n'.join(map(str, order)).encode()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256((json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()


def validate_v51(vector_file: Path, result_file: Path) -> dict[str, Any]:
    require(sha(vector_file) == V51_VECTOR_SHA256, 'v51 vector identity changed')
    require(sha(result_file) == V51_RESULT_SHA256, 'v51 result identity changed')
    vector = json.loads(vector_file.read_text())
    result = json.loads(result_file.read_text())
    require(vector['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_VECTOR_CAPTURE', 'v51 vector verdict changed')
    require(vector['scientific_role'] == 'EXACT_V31_FUSION_INPUT_RANKS_CAPTURED_BEFORE_DIAGNOSTIC_RECOVERABILITY_ATTACHMENT', 'v51 vector role changed')
    require(vector['canonical_sha256_without_self_field'] == V51_VECTOR_CANONICAL, 'v51 vector canonical changed')
    chk = dict(vector)
    del chk['canonical_sha256_without_self_field']
    require(canonical_sha(chk) == V51_VECTOR_CANONICAL, 'v51 vector canonical bytes changed')
    require(int(vector['family_count']) == HDB_N and len(vector['families']) == HDB_N, 'v51 family universe changed')
    require(vector['local_order_sha256'] == V31_HDB_LOCAL_SHA256, 'v51 local order changed')
    require(vector['v19_order_sha256'] == V19_HDB_ORDER_SHA256, 'v51 v19 order changed')
    require(vector['fused_order_sha256'] == V31_HDB_FUSED_SHA256, 'v51 fused order changed')
    require(vector['diagnostic_recoverability_attached'] is False and vector['annual_own_family_f1_attached'] is False, 'v51 vector contains outcomes')
    require(vector['literature_budget_used_in_statistic'] is False and vector['component_quality_topology_signal_used'] is False, 'v51 vector used forbidden rescue signal')
    require(vector['target_information_access'] is False and vector['target_region_events_accessed'] is False, 'v51 target firewall changed')
    require(vector['maarsy_scientific_access'] is False and vector['dms_scientific_access'] is False, 'v51 survey firewall changed')
    require(vector['blind_exclusion'] == [20.0, 55.0] and vector['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'v51 role/firewall changed')

    require(result['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC', 'v51 diagnostic did not pass')
    require(result['direction_supported_both_years'] is True, 'v51 direction did not pass both years')
    require(result['vector_file_sha256'] == V51_VECTOR_SHA256 and result['vector_canonical_sha256'] == V51_VECTOR_CANONICAL, 'v51 result/vector provenance changed')
    for k in ('new_candidate_order_evaluated','literature_panel_evaluated','selector_evaluated','replacement_rule_evaluated','successor_selected','minimax_successor_evaluated','alternate_rank_statistic_search','threshold_search','quantile_search','top_k_search','rank_window_search','fusion_weight_search','rank_algebra_search','pareto_order_evaluated','post_result_second_search','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(result[k] is False, f'v51 forbidden authorizer flag set: {k}')
    require(result['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and result['blind_exclusion'] == [20.0, 55.0], 'v51 result firewall changed')
    return vector


def validate_v54(split_file: Path, result_file: Path) -> None:
    require(sha(split_file) == V54_SPLIT_SHA256, 'v54 split identity changed')
    require(sha(result_file) == V54_RESULT_SHA256, 'v54 result identity changed')
    split = json.loads(split_file.read_text())
    result = json.loads(result_file.read_text())
    require(split['verdict'] == 'PASS_V54_V19_ADVANTAGE_FULL_UNIVERSE_SPLIT_FREEZE', 'v54 split verdict changed')
    require(split['scientific_role'] == 'COMPLETE_229_FAMILY_HDB_V19_ADVANTAGE_SPLIT_FROZEN_BEFORE_V54_RECOVERABILITY_ATTACHMENT', 'v54 split role changed')
    require(split['canonical_sha256_without_self_field'] == V54_SPLIT_CANONICAL, 'v54 split canonical changed')
    chk = dict(split)
    del chk['canonical_sha256_without_self_field']
    require(canonical_sha(chk) == V54_SPLIT_CANONICAL, 'v54 split canonical bytes changed')
    require(int(split['family_count']) == HDB_N and len(split['families']) == HDB_N, 'v54 split universe changed')
    require(int(split['positive_v19_advantage_count']) == 104 and int(split['nonpositive_v19_advantage_count']) == 125, 'v54 structural split changed')
    require(split['current_v54_recoverability_attached'] is False and split['annual_own_family_f1_attached'] is False, 'v54 split contains outcomes')
    for k in ('literature_budget_used_in_split','top_k_used_in_split','rank_window_used_in_split','boundary_identity_used','group_identity_used','v1157_surfaced_missed_identity_used','component_quality_topology_signal_used','new_candidate_order_evaluated','selector_evaluated','successor_selected','nonzero_threshold_selected','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(split[k] is False, f'v54 split forbidden flag set: {k}')
    require(split['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and split['blind_exclusion'] == [20.0, 55.0], 'v54 split firewall changed')

    require(result['verdict'] == 'PASS_V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC', 'v54 diagnostic did not pass')
    require(result['direction_supported_both_years'] is True, 'v54 direction did not pass both years')
    require(int(result['family_count']) == HDB_N, 'v54 result universe changed')
    require(result['split_file_sha256'] == V54_SPLIT_SHA256 and result['split_canonical_sha256'] == V54_SPLIT_CANONICAL, 'v54 result/split provenance changed')
    for k in ('new_candidate_order_evaluated','literature_panel_evaluated','selector_evaluated','replacement_rule_evaluated','successor_selected','v19_only_order_evaluated','minimum_rank_order_evaluated','weighted_fusion_evaluated','nonlinear_fusion_evaluated','representative_group_aggregation_evaluated','auc_evaluated','correlation_evaluated','regression_evaluated','p_value_evaluated','nonzero_threshold_search','absolute_gap_search','quantile_search','top_k_search','rank_window_search','literature_budget_analysis','boundary_identity_used','v1157_surfaced_missed_identity_used','component_quality_topology_rescue','feature_search','model_search','k_search','metric_search','scaling_search','diversity_search','source_quota_selected','post_result_second_search','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(result[k] is False, f'v54 forbidden authorizer flag set: {k}')
    require(result['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and result['blind_exclusion'] == [20.0, 55.0], 'v54 result firewall changed')


def freeze_mode(vector_file: Path, v51_result_file: Path, v54_split_file: Path, v54_result_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    vector = validate_v51(vector_file, v51_result_file)
    validate_v54(v54_split_file, v54_result_file)
    rows = list(vector['families'])
    ids = [str(r['family_id']) for r in rows]
    require(len(ids) == HDB_N and len(set(ids)) == HDB_N, 'invalid v51 family identity universe')
    require(sorted(int(r['local_rank']) for r in rows) == list(range(1, HDB_N + 1)), 'local ranks not complete permutation')
    require(sorted(int(r['v19_rank']) for r in rows) == list(range(1, HDB_N + 1)), 'v19 ranks not complete permutation')

    by_id: dict[str, dict[str, int]] = {}
    for r in rows:
        fid = str(r['family_id'])
        rl = int(r['local_rank'])
        rv = int(r['v19_rank'])
        lp = float(r['local_rank_percentile'])
        vp = float(r['v19_rank_percentile'])
        require(abs(lp - (rl - 1) / (HDB_N - 1)) < 1e-15, 'local percentile arithmetic changed')
        require(abs(vp - (rv - 1) / (HDB_N - 1)) < 1e-15, 'v19 percentile arithmetic changed')
        by_id[fid] = {'local_rank': rl, 'v19_rank': rv}

    v31_order = sorted(ids, key=lambda fid: (by_id[fid]['local_rank'] + by_id[fid]['v19_rank'], by_id[fid]['local_rank'], by_id[fid]['v19_rank'], fid))
    require(order_sha(v31_order) == V31_HDB_FUSED_SHA256, 'reconstructed v31 HDB order changed')
    v55_order = sorted(ids, key=lambda fid: (min(by_id[fid]['local_rank'], by_id[fid]['v19_rank']), max(by_id[fid]['local_rank'], by_id[fid]['v19_rank']), fid))
    require(order_sha(v55_order) == V55_HDB_ORDER_SHA256, 'v55 HDB order identity changed')

    old = {fid: i + 1 for i, fid in enumerate(v31_order)}
    new = {fid: i + 1 for i, fid in enumerate(v55_order)}
    moved = sum(old[fid] != new[fid] for fid in ids)
    moved_up = sum(new[fid] < old[fid] for fid in ids)
    moved_down = sum(new[fid] > old[fid] for fid in ids)
    require((moved, moved_up, moved_down) == (221, 104, 117), 'v55 structural movement changed')
    top9_delta = len(set(v31_order[:9]) ^ set(v55_order[:9])) // 2
    top11_delta = len(set(v31_order[:11]) ^ set(v55_order[:11])) // 2
    require(top9_delta == 4 and top11_delta == 4, 'v55 prefix structural consequence changed')

    out_rows = []
    for fid in ids:
        rl = by_id[fid]['local_rank']
        rv = by_id[fid]['v19_rank']
        out_rows.append({
            'family_id': fid,
            'local_rank': rl,
            'v19_rank': rv,
            'best_input_rank': min(rl, rv),
            'worst_input_rank': max(rl, rv),
            'v31_fused_rank': old[fid],
            'v55_rank': new[fid],
            'rank_displacement_v31_minus_v55': old[fid] - new[fid],
        })
    out_rows.sort(key=lambda r: int(r['v55_rank']))

    payload: dict[str, Any] = {
        'verdict': 'PASS_V55_OPTIMISTIC_CONSTITUENT_HDB_ORDER_FREEZE',
        'scientific_role': 'COMPLETE_HDB_TOTAL_ORDER_FROZEN_FROM_OUTCOME_FREE_V51_CONSTITUENT_RANKS_AFTER_BINDING_V54_MECHANISM_PASS_BEFORE_V55_PANEL_OUTCOME',
        'authorizing_v51_run': 31493423814,
        'authorizing_v51_artifact': 9101972590,
        'authorizing_v51_artifact_digest': 'sha256:56258a0be52d83c0d6dbfcffdb9fd9a2c6b73587ba8d92d7bdccdef9729868c9',
        'authorizing_v54_run': 31497952186,
        'authorizing_v54_artifact': 9103776799,
        'authorizing_v54_artifact_digest': 'sha256:db9bd25f8d8cea942f5db5dac655227ddb2e5c413a5f6ce7893e28abc03b795e',
        'v51_vector_sha256': V51_VECTOR_SHA256,
        'v51_vector_canonical_sha256': V51_VECTOR_CANONICAL,
        'v51_result_sha256': V51_RESULT_SHA256,
        'v54_split_sha256': V54_SPLIT_SHA256,
        'v54_split_canonical_sha256': V54_SPLIT_CANONICAL,
        'v54_result_sha256': V54_RESULT_SHA256,
        'family_count': HDB_N,
        'hdb_rule': '(min(local_rank,v19_rank), max(local_rank,v19_rank), family_id), ascending',
        'sugar_rule': 'exact v31 unchanged',
        'v31_hdb_order_sha256': V31_HDB_FUSED_SHA256,
        'v55_hdb_order_sha256': V55_HDB_ORDER_SHA256,
        'v31_hdb_order': v31_order,
        'v55_hdb_order': v55_order,
        'families': out_rows,
        'moved_position_count': moved,
        'moved_up_count': moved_up,
        'moved_down_count': moved_down,
        'top9_membership_substitution_count_vs_v31': top9_delta,
        'top11_membership_substitution_count_vs_v31': top11_delta,
        'current_v55_panel_outcome_accessed': False,
        'annual_own_family_f1_used_for_order': False,
        'recoverability_label_used_for_order': False,
        'v54_annual_outcome_used_for_order': False,
        'v54_outcome_identity_used_for_order': False,
        'literature_budget_used_for_order': False,
        'boundary_identity_used': False,
        'component_quality_topology_crossroute_signal_used': False,
        'fusion_weight_selected': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'alternate_tie_rule_evaluated': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'blind_exclusion': [20.0, 55.0],
    }
    payload['canonical_sha256_without_self_field'] = canonical_sha(payload)
    out = output / 'V55_OPTIMISTIC_CONSTITUENT_HDB_ORDER_FREEZE.json'
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': payload['verdict'],
        'v55_hdb_order_sha256': V55_HDB_ORDER_SHA256,
        'moved_position_count': moved,
        'moved_up_count': moved_up,
        'moved_down_count': moved_down,
        'top9_membership_substitution_count_vs_v31': top9_delta,
        'top11_membership_substitution_count_vs_v31': top11_delta,
        'canonical_sha256_without_self_field': payload['canonical_sha256_without_self_field'],
        'file_sha256': sha(out),
    }, indent=2, sort_keys=True))
    return 0


def exact_parent_capture(sugar_root: Path, hdbscan_root: Path, truth_root: Path, ranker_source: Path, output: Path) -> tuple[dict[str, Any], dict[int, dict[str, list[str]]]]:
    output.mkdir(parents=True, exist_ok=True)
    require(v31.v22.sha(ranker_source) == RANKER_SOURCE_SHA256, '#839 ranker source changed')
    original = v31.v19.fusion_orders
    captured: list[dict[str, list[str]]] = []

    def capture_and_delegate(order_a, order_b):
        a = list(map(str, order_a))
        b = list(map(str, order_b))
        result = original(order_a, order_b)
        rs = list(map(str, result['rank_sum']))
        captured.append({'local_order': a, 'v19_order': b, 'fused_order': rs})
        return result

    old_argv = list(sys.argv)
    v31.v19.fusion_orders = capture_and_delegate
    try:
        sys.argv = [
            'train_evaluate.py', '--sugar-root', str(sugar_root), '--hdbscan-root', str(hdbscan_root),
            '--truth-root', str(truth_root), '--ranker-source', str(ranker_source), '--output', str(output),
        ]
        rc = v31.main()
        require(rc == 0, 'frozen v31 parent failed')
    finally:
        sys.argv = old_argv
        v31.v19.fusion_orders = original

    require(len(captured) == 2, 'expected exactly two v31 fusion calls')
    by_n = {len(x['fused_order']): x for x in captured}
    require(set(by_n) == {267, HDB_N}, 'unexpected v31 fusion route sizes')
    parent_path = output / 'V31_LOCAL_GEOMETRY_OOF_RESULT.json'
    require(parent_path.is_file(), 'exact-v31 parent result missing')
    parent = json.loads(parent_path.read_text())
    require(parent['verdict'] == 'FAIL_V31_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'v31 parent verdict changed')
    require(parent['panel_wins'] == 2 and len(parent['panels']) == 4, 'v31 parent panel state changed')
    require(parent['strict_whole_shower_oof'] is True and parent['feature_dimension'] == 71 and parent['nearest_k'] == 1, 'v31 parent geometry changed')
    require(parent['annual_margin'] == 'd_nonpositive-d_positive' and parent['annual_combiner'] == 'min(margin_2013,margin_2014)', 'v31 parent score changed')
    require(parent['fusion'] == 'one equal rank-sum with exact v19', 'v31 parent fusion changed')
    require(parent['diversity'] == {'lambda': 0.8, 'scale': 1.0}, 'v31 parent diversity changed')
    require(parent['candidate_membership_changed'] is False and parent['pretruth_feature_changed'] is False, 'v31 parent universe changed')
    require(parent['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'v31 SonotaCo role changed')
    require(parent['target_information_access'] is False and parent['target_region_events_accessed'] is False, 'v31 target firewall changed')
    require(parent['maarsy_scientific_access'] is False and parent['dms_scientific_access'] is False, 'v31 survey firewall changed')
    require(parent['blind_exclusion'] == [20.0, 55.0], 'v31 blind exclusion changed')

    pmap = {(str(x['comparator']), int(x['year'])): x for x in parent['panels']}
    require(set(pmap) == set(PARENT), 'v31 parent panel identities changed')
    for key, (f1, recovered) in PARENT.items():
        row = pmap[key]
        require(abs(float(row['candidate_macro_f1']) - f1) < 1e-12, f'{key} v31 macro F1 changed')
        require(int(row['candidate_recovered_f1_gt_0_5']) == recovered, f'{key} v31 recovery changed')

    h = by_n[HDB_N]
    require(order_sha(h['local_order']) == V31_HDB_LOCAL_SHA256, 'runtime HDB local order changed')
    require(order_sha(h['v19_order']) == V19_HDB_ORDER_SHA256, 'runtime HDB v19 order changed')
    require(order_sha(h['fused_order']) == V31_HDB_FUSED_SHA256, 'runtime HDB v31 fused order changed')
    return parent, by_n


def evaluate_mode(sugar_root: Path, hdbscan_root: Path, truth_root: Path, ranker_source: Path, order_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    freeze = json.loads(order_file.read_text())
    require(freeze['verdict'] == 'PASS_V55_OPTIMISTIC_CONSTITUENT_HDB_ORDER_FREEZE', 'v55 order-freeze verdict changed')
    require(freeze['scientific_role'] == 'COMPLETE_HDB_TOTAL_ORDER_FROZEN_FROM_OUTCOME_FREE_V51_CONSTITUENT_RANKS_AFTER_BINDING_V54_MECHANISM_PASS_BEFORE_V55_PANEL_OUTCOME', 'v55 order-freeze role changed')
    require(freeze['v31_hdb_order_sha256'] == V31_HDB_FUSED_SHA256 and freeze['v55_hdb_order_sha256'] == V55_HDB_ORDER_SHA256, 'v55 frozen order identity changed')
    expected_canonical = str(freeze['canonical_sha256_without_self_field'])
    chk = dict(freeze)
    del chk['canonical_sha256_without_self_field']
    require(canonical_sha(chk) == expected_canonical, 'v55 order-freeze canonical identity changed')
    v55_order = list(map(str, freeze['v55_hdb_order']))
    require(len(v55_order) == HDB_N and len(set(v55_order)) == HDB_N and order_sha(v55_order) == V55_HDB_ORDER_SHA256, 'invalid v55 HDB permutation')
    require(freeze['current_v55_panel_outcome_accessed'] is False and freeze['annual_own_family_f1_used_for_order'] is False and freeze['recoverability_label_used_for_order'] is False, 'v55 order used current outcomes')
    require(freeze['v54_annual_outcome_used_for_order'] is False and freeze['v54_outcome_identity_used_for_order'] is False, 'v55 order used v54 outcomes rather than authorization only')
    require(freeze['literature_budget_used_for_order'] is False and freeze['boundary_identity_used'] is False and freeze['component_quality_topology_crossroute_signal_used'] is False, 'v55 order used forbidden rescue signal')

    parent, captured = exact_parent_capture(sugar_root, hdbscan_root, truth_root, ranker_source, output / 'parent_v31')
    pmap = {(str(x['comparator']), int(x['year'])): x for x in parent['panels']}
    sugar_fused = list(map(str, captured[267]['fused_order']))
    hdb_fused = list(map(str, captured[HDB_N]['fused_order']))
    require(order_sha(hdb_fused) == V31_HDB_FUSED_SHA256, 'runtime v31 HDB order changed')
    require(list(map(str, freeze['v31_hdb_order'])) == hdb_fused, 'frozen reconstructed v31 HDB order differs from runtime')

    hmeta = json.loads((hdbscan_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    hfp = json.loads((hdbscan_root / 'family_memberships.json').read_text())
    hids = list(map(str, hmeta['family_ids']))
    hfams = list(hfp['families'])
    require(hmeta['truth_accessed'] is False and hfp['truth_accessed'] is False, '#950 HDB payload not pretruth')
    require(len(hids) == HDB_N and [str(f['family_id']) for f in hfams] == hids, '#950 HDB family universe changed')
    require(set(v55_order) == set(hids), 'v55 HDB order universe differs from #950')
    ranked_hdb = v31.v22.rerank(hfams, v55_order)

    panels: list[dict[str, Any]] = []
    for route, year in (('sugar', 2013), ('sugar', 2014)):
        row = pmap[(route, year)]
        panels.append({
            'comparator': route,
            'year': year,
            'budget': int(row['budget']),
            'candidate_macro_f1': float(row['candidate_macro_f1']),
            'literature_macro_f1': float(row['literature_macro_f1']),
            'candidate_recovered_f1_gt_0_5': int(row['candidate_recovered_f1_gt_0_5']),
            'literature_recovered_f1_gt_0_5': int(row['literature_recovered_f1_gt_0_5']),
            'macro_f1_ratio': float(row['macro_f1_ratio']),
            'recovery_ratio': float(row['recovery_ratio']),
            'superiority_pair_pass': bool(row['superiority_pair_pass']),
        })

    for year in (2013, 2014):
        truth = json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text())
        evaluation = json.loads((truth_root / f'evaluation_hdbscan_{year}.json').read_text())
        budget = int(evaluation['candidate_budget']['comparator_budget'])
        cur = v31.v22.evaluate(ranked_hdb, truth, budget)
        lit = evaluation['comparator_summary']
        cm = float(cur['macro_f1'])
        cr = int(cur['recovered_f1_gt_0_5'])
        lm = float(lit['macro_f1'])
        lr = int(lit['recovered_f1_gt_0_5'])
        panels.append({
            'comparator': 'hdbscan',
            'year': year,
            'budget': budget,
            'candidate_macro_f1': cm,
            'literature_macro_f1': lm,
            'candidate_recovered_f1_gt_0_5': cr,
            'literature_recovered_f1_gt_0_5': lr,
            'macro_f1_ratio': cm / lm if lm else float('inf'),
            'recovery_ratio': cr / lr if lr else float('inf'),
            'superiority_pair_pass': bool(cm > lm and cr >= lr),
        })

    wins = int(sum(bool(x['superiority_pair_pass']) for x in panels))
    passed = bool(wins == 4)
    parent_controls = []
    for route, year in (('sugar', 2013), ('sugar', 2014), ('hdbscan', 2013), ('hdbscan', 2014)):
        row = pmap[(route, year)]
        parent_controls.append({'comparator': route, 'year': year, 'macro_f1': float(row['candidate_macro_f1']), 'recovered_f1_gt_0_5': int(row['candidate_recovered_f1_gt_0_5'])})

    result: dict[str, Any] = {
        'scientific_stage': 'EXPOSED_SONOTACO_V55_OPTIMISTIC_CONSTITUENT_FUSION_V1',
        'verdict': 'PASS_V55_OPTIMISTIC_CONSTITUENT_FUSION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V55_OPTIMISTIC_CONSTITUENT_FUSION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'HDB replaces exact-v31 equal rank-sum with the frozen optimistic best-constituent lexicographic order over the same exact local/diversity and immutable-v19 ranks; Sugar exact v31 unchanged',
        'authorizing_diagnostics': ['PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC', 'PASS_V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC'],
        'authorizing_v54_run': 31497952186,
        'authorizing_v54_artifact': 9103776799,
        'authorizing_v54_split_sha256': V54_SPLIT_SHA256,
        'authorizing_v54_result_sha256': V54_RESULT_SHA256,
        'authorizing_v51_run': 31493423814,
        'authorizing_v51_artifact': 9101972590,
        'authorizing_v51_vector_sha256': V51_VECTOR_SHA256,
        'authorizing_v51_result_sha256': V51_RESULT_SHA256,
        'parent': 'v31 local-geometry-margin OOF',
        'parent_source_blob': PARENT_SOURCE_BLOB,
        'parent_reproduction_pass': True,
        'parent_controls': parent_controls,
        'ranker_source_sha256': RANKER_SOURCE_SHA256,
        'sugar_rule': 'exact v31 unchanged',
        'sugar_order_sha256': order_sha(sugar_fused),
        'hdb_v31_order_sha256': V31_HDB_FUSED_SHA256,
        'hdb_v55_order_sha256': order_sha(v55_order),
        'hdb_rule': '(min(local_rank,v19_rank), max(local_rank,v19_rank), family_id), ascending',
        'hdb_moved_position_count': int(freeze['moved_position_count']),
        'hdb_top9_membership_substitution_count_vs_v31': int(freeze['top9_membership_substitution_count_vs_v31']),
        'hdb_top11_membership_substitution_count_vs_v31': int(freeze['top11_membership_substitution_count_vs_v31']),
        'panel_wins': wins,
        'panels': panels,
        'candidate_membership_changed': False,
        'pretruth_feature_changed': False,
        'v54_outcome_used_for_ranking': False,
        'v54_outcome_identity_used_for_ranking': False,
        'v19_only_order_evaluated': False,
        'asymmetric_v19_promotion_evaluated': False,
        'weighted_minimum_used': False,
        'soft_minimum_used': False,
        'alternate_tie_rule_evaluated': False,
        'fusion_weight_search': False,
        'second_fusion_rule_evaluated': False,
        'threshold_search': False,
        'quantile_search': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'hdb_subgroup_exception': False,
        'component_quality_topology_crossroute_rescue': False,
        'boundary_identity_used': False,
        'oracle_identity_used_for_ranking': False,
        'diversity_changed': False,
        'local_score_changed': False,
        'v19_order_changed': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'metric_search': False,
        'scaling_search': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = output / 'V55_OPTIMISTIC_CONSTITUENT_FUSION_RESULT.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels, 'hdb_v55_order_sha256': result['hdb_v55_order_sha256']}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    f = sub.add_parser('freeze')
    f.add_argument('--vector-file', type=Path, required=True)
    f.add_argument('--v51-result-file', type=Path, required=True)
    f.add_argument('--v54-split-file', type=Path, required=True)
    f.add_argument('--v54-result-file', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    e = sub.add_parser('evaluate')
    e.add_argument('--sugar-root', type=Path, required=True)
    e.add_argument('--hdbscan-root', type=Path, required=True)
    e.add_argument('--truth-root', type=Path, required=True)
    e.add_argument('--ranker-source', type=Path, required=True)
    e.add_argument('--order-file', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'freeze':
        return freeze_mode(a.vector_file, a.v51_result_file, a.v54_split_file, a.v54_result_file, a.output)
    return evaluate_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.order_file, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from orbittrace_v52_consensus_bottleneck_minimax_v1 import train_evaluate as v52

CORRECTED_PROTOCOL_BLOB = 'fc1be0830488858b1ff95e218b9b2236557f759f'
ACTUAL_V51_ROLE = 'POST_V50_V31_FUSION_MECHANISM_DIAGNOSTIC_ONLY_NO_NEW_ORDER_OR_PANEL_EVALUATED'


def validate_v51_actual(vector_file: Path, diag_file: Path):
    v52.require(v52.sha(vector_file) == v52.V51_VECTOR_SHA, 'v51 vector identity changed')
    v52.require(v52.sha(diag_file) == v52.V51_DIAG_SHA, 'v51 diagnostic identity changed')
    vector = json.loads(vector_file.read_text())
    diag = json.loads(diag_file.read_text())

    v52.require(vector['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_VECTOR_CAPTURE', 'v51 vector verdict changed')
    v52.require(vector['scientific_role'] == 'EXACT_V31_FUSION_INPUT_RANKS_CAPTURED_BEFORE_DIAGNOSTIC_RECOVERABILITY_ATTACHMENT', 'v51 vector role changed')
    v52.require(vector['parent_source_blob'] == v52.PARENT_SOURCE_BLOB and vector['ranker_source_sha256'] == v52.RANKER_SHA, 'v51 parent source changed')
    v52.require(int(vector['family_count']) == v52.HDB_N and len(vector['families']) == v52.HDB_N, 'v51 family count changed')
    v52.require(vector['local_order_sha256'] == v52.LOCAL_SHA and vector['fused_order_sha256'] == v52.V31_HDB_SHA, 'v51 order identity changed')
    v52.require(vector['diagnostic_recoverability_attached'] is False and vector['annual_own_family_f1_attached'] is False, 'v51 vector contains diagnostic outcome')
    for k in ('literature_budget_used_in_statistic', 'boundary_identity_used', 'component_quality_topology_signal_used', 'new_candidate_order_evaluated', 'selector_evaluated', 'successor_selected', 'threshold_selected', 'top_k_selected', 'rank_window_selected', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        v52.require(vector[k] is False, f'v51 vector forbidden flag set: {k}')
    check = dict(vector)
    expected = str(check.pop('canonical_sha256_without_self_field'))
    v52.require(v52.canonical_sha(check) == expected, 'v51 vector canonical identity changed')
    v52.require(vector['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and vector['blind_exclusion'] == [20.0, 55.0], 'v51 vector firewall changed')

    v52.require(diag['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC', 'v51 diagnostic verdict changed')
    v52.require(diag['scientific_role'] == ACTUAL_V51_ROLE, 'v51 diagnostic role changed')
    v52.require(diag['parent_source_blob'] == v52.PARENT_SOURCE_BLOB and diag['ranker_source_sha256'] == v52.RANKER_SHA, 'v51 diagnostic parent source changed')
    v52.require(int(diag['family_count']) == v52.HDB_N and diag['direction_supported_both_years'] is True, 'v51 diagnostic population/direction changed')
    v52.require(diag['vector_file_sha256'] == v52.V51_VECTOR_SHA, 'v51 diagnostic vector identity changed')
    for y in ('2013', '2014'):
        a = diag['annual_diagnostics'][y]
        v52.require(a['direction_pass'] is True, f'v51 {y} direction changed')
        v52.require(float(a['recoverable']['median_consensus_bottleneck']) < float(a['nonrecoverable']['median_consensus_bottleneck']), f'v51 {y} median direction changed')
    for k in ('new_candidate_order_evaluated','literature_panel_evaluated','selector_evaluated','replacement_rule_evaluated','successor_selected','minimax_successor_evaluated','representative_group_aggregation_evaluated','auc_evaluated','correlation_evaluated','regression_evaluated','p_value_evaluated','alternate_rank_statistic_search','rank_disagreement_test','threshold_search','quantile_search','top_k_search','rank_window_search','literature_budget_analysis','fusion_weight_search','rank_algebra_search','pareto_order_evaluated','component_quality_topology_rescue','boundary_identity_used','oracle_identity_used_for_ranking','feature_search','model_search','k_search','metric_search','scaling_search','diversity_search','source_quota_selected','post_result_second_search','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        v52.require(diag[k] is False, f'v51 diagnostic forbidden flag set: {k}')
    v52.require(diag['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and diag['blind_exclusion'] == [20.0, 55.0], 'v51 diagnostic firewall changed')
    return vector, diag


v52.validate_v51 = validate_v51_actual
v52.PROTOCOL_BLOB = CORRECTED_PROTOCOL_BLOB

if __name__ == '__main__':
    raise SystemExit(v52.main())

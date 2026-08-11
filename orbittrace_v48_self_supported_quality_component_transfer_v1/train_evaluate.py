#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v42_quality_component_gated_rescue_v1 import train_evaluate as v42

VARIANT = 'v48_self_supported_quality_component_transfer_v1'
HDB_N = 229
SUGAR_N = 267
SELF_SUPPORTED_N = 35
SIGNAL_SHA256 = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
GAP_RESULT_SHA256 = 'c372b4aac0547198cb6ac4239d604fddc12fdd0f11a930ab39a1e46d01f5e461'
GAP_VECTOR_SHA256 = '145ceb528e66f924c00c152cf2e5a38a2424ffda8f0a39a7eb80680c1bd5dadd'
GAP_VECTOR_CANONICAL_SHA256 = '0a9eda015ca367697a1dca678a0e8f7d986880fc424a0cbf4573567ab8776672'
V31_HDB_ORDER_SHA256 = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'
V48_HDB_ORDER_SHA256 = '62041ea9f6e094471a7decf02c71491fc553e93af86a655e21bf1035d0904db6'
AUTHOR_1139_RUN = 31488131546
AUTHOR_1139_ARTIFACT = 9099927842
AUTHOR_1139_DIGEST = 'sha256:67960fbd5fd76173da62c6d1823d507c99ee6431862ce56351aa7a194ec81e07'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return v42.v40.v22.sha(path)


def order_sha(order: list[str]) -> str:
    return v42.v40.order_sha(list(map(str, order)))


def validate_1139(result_path: Path, vector_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    require(sha(result_path) == GAP_RESULT_SHA256, '#1139 result identity changed')
    require(sha(vector_path) == GAP_VECTOR_SHA256, '#1139 vector identity changed')
    r = json.loads(result_path.read_text())
    v = json.loads(vector_path.read_text())
    require(r['verdict'] == 'PASS_V46_JOINT_INHERITANCE_GAP_DIAGNOSTIC', '#1139 verdict changed')
    require(r['scientific_role'] == 'POST_V46_DIAGNOSTIC_ONLY_JOINT_INHERITANCE_GAP_NO_SUCCESSOR_EVALUATED', '#1139 role changed')
    require(r['direction_supported_both_years'] is True, '#1139 direction not supported')
    require(int(r['joint_family_count']) == 60, '#1139 joint count changed')
    require(r['source_signal_sha256'] == SIGNAL_SHA256, '#1139 source signal changed')
    require(r['vector_file_sha256'] == GAP_VECTOR_SHA256, '#1139 vector SHA reference changed')
    require(r['vector_canonical_sha256'] == GAP_VECTOR_CANONICAL_SHA256, '#1139 vector canonical reference changed')
    for k in (
        'new_rank_or_score_evaluated','selector_evaluated','replacement_rule_evaluated','successor_selected',
        'group_aggregation_evaluated','auc_evaluated','correlation_evaluated','regression_evaluated',
        'p_value_evaluated','threshold_search','quantile_search','top_k_search','rank_window_search',
        'alternate_statistic_search','alternate_direction_test','component_size_rule_search',
        'quality_rank_placement_retry','component_placement_retry','component_representative_retry',
        'pareto_layer_evaluated','pairwise_dominance_evaluated','boundary_identity_used',
        'boundary_rescue_list_created','oracle_identity_used_for_ranking',
        'truth_aware_group_identity_used_for_ranking','feature_search','model_search','k_search',
        'scaling_search','diversity_search','fusion_search','source_quota_selected','post_result_second_search',
        'target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access',
    ):
        require(r[k] is False, f'#1139 forbidden result flag set: {k}')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and r['blind_exclusion'] == [20.0, 55.0], '#1139 firewall changed')

    require(v['verdict'] == 'PASS_V46_JOINT_INHERITANCE_GAP_VECTOR_FREEZE', '#1139 vector verdict changed')
    require(v['scientific_role'] == 'EXACT_60_JOINT_FAMILY_INHERITANCE_GAP_FROZEN_BEFORE_OUTCOME_TRUTH', '#1139 vector role changed')
    require(v['source_signal_sha256'] == SIGNAL_SHA256, '#1139 vector source changed')
    require(int(v['joint_family_count']) == 60 and len(v['families']) == 60, '#1139 vector population changed')
    require(v['canonical_sha256_without_self_field'] == GAP_VECTOR_CANONICAL_SHA256, '#1139 vector canonical identity changed')
    require(v['truth_accessed'] is False and v['literature_budget_used'] is False and v['boundary_identity_used'] is False, '#1139 vector was not truth/budget independent')
    for k in ('new_rank_or_score_evaluated','selector_evaluated','successor_selected','threshold_selected','top_k_selected','rank_window_selected','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(v[k] is False, f'#1139 forbidden vector flag set: {k}')
    require(v['blind_exclusion'] == [20.0, 55.0], '#1139 vector blind exclusion changed')
    return r, v


def load_signal(path: Path) -> dict[str, Any]:
    require(sha(path) == SIGNAL_SHA256, '#1098 signal identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', '#1098 verdict changed')
    require(r['scientific_role'] == 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION', '#1098 role changed')
    require(int(r['family_count']) == HDB_N and len(r['families']) == HDB_N, '#1098 universe changed')
    require(sum(bool(x['joint_signal']) for x in r['families']) == 60, '#1098 joint count changed')
    require(r['graph_sha256'] == v42.v40.GRAPH_SHA256 and r['component_sha256'] == v42.v40.COMPONENT_SHA256, '#1098 geometry changed')
    for k in ('threshold_selected','top_k_selected','rank_window_selected','alternate_boolean_rule_evaluated','oracle_identity_hardcoded','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(r[k] is False, f'#1098 forbidden flag set: {k}')
    require(r['blind_exclusion'] == [20.0, 55.0], '#1098 blind exclusion changed')
    return r


def self_supported_row(r: dict[str, Any]) -> dict[str, Any]:
    fid = str(r['family_id'])
    rv = int(r['v31_rank'])
    rq = int(r['quality_rank'])
    pv = float(r['v31_percentile'])
    pq = float(r['quality_percentile'])
    pc = float(r['component_best_v31_percentile'])
    require(np.isfinite(pv) and np.isfinite(pq) and np.isfinite(pc), 'nonfinite support percentile')
    require(0.0 <= pv <= 1.0 and 0.0 <= pq <= 1.0 and 0.0 <= pc <= 1.0, 'invalid support percentile')
    quality_suppressed = bool(rq < rv)
    component_opportunity = bool(pc < pv)
    joint = bool(quality_suppressed and component_opportunity)
    require(bool(r['positive_quality_suppression']) == quality_suppressed, 'quality suppression identity changed')
    require(bool(r['component_closure_opportunity']) == component_opportunity, 'component opportunity identity changed')
    require(bool(r['joint_signal']) == joint, 'joint signal identity changed')
    quality_suppression = float(pv - pq)
    inheritance_gap = float(pv - pc)
    self_supported = bool(joint and pq <= pc)
    require(self_supported == bool(joint and quality_suppression >= inheritance_gap), 'self-support algebra changed')
    key = int(rq if self_supported else rv)
    return {
        'family_id': fid,
        'component_id': str(r['component_id']),
        'v31_rank': rv,
        'quality_rank': rq,
        'v31_percentile': pv,
        'quality_percentile': pq,
        'component_best_v31_percentile': pc,
        'quality_suppression': quality_suppression,
        'inheritance_gap': inheritance_gap,
        'quality_suppressed': quality_suppressed,
        'component_opportunity': component_opportunity,
        'original_joint_gate': joint,
        'self_supported_gate': self_supported,
        'promotion_key': key,
    }


def freeze_order_mode(signal_file: Path, gap_result: Path, gap_vector: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    signal = load_signal(signal_file)
    _, vector = validate_1139(gap_result, gap_vector)
    rows = [self_supported_row(x) for x in signal['families']]
    by_id = {str(x['family_id']): x for x in rows}
    require(len(by_id) == HDB_N, 'duplicate HDB family id')
    v31_order = [str(x['family_id']) for x in sorted(rows, key=lambda x: (int(x['v31_rank']), str(x['family_id'])))]
    require(order_sha(v31_order) == V31_HDB_ORDER_SHA256, 'exact v31 HDB order changed')
    joint_ids = {str(x['family_id']) for x in rows if bool(x['original_joint_gate'])}
    vector_ids = {str(x['family_id']) for x in vector['families']}
    require(len(joint_ids) == 60 and joint_ids == vector_ids, '#1098/#1139 joint identities differ')
    vector_by_id = {str(x['family_id']): x for x in vector['families']}
    for fid in sorted(joint_ids):
        r = by_id[fid]
        vr = vector_by_id[fid]
        require(abs(float(vr['inheritance_gap']) - float(r['inheritance_gap'])) < 1e-15, '#1139 inheritance gap changed')
        require(abs(float(vr['v31_percentile']) - float(r['v31_percentile'])) < 1e-15, '#1139 v31 percentile changed')
        require(abs(float(vr['component_best_v31_percentile']) - float(r['component_best_v31_percentile'])) < 1e-15, '#1139 component percentile changed')
    self_count = int(sum(bool(x['self_supported_gate']) for x in rows))
    require(self_count == SELF_SUPPORTED_N, 'truth-blind self-supported count changed')
    v48_order = [
        str(x['family_id'])
        for x in sorted(rows, key=lambda x: (int(x['promotion_key']), int(x['v31_rank']), str(x['family_id'])))
    ]
    require(order_sha(v48_order) == V48_HDB_ORDER_SHA256, 'truth-blind v48 HDB order changed')
    new_rank = {fid: i + 1 for i, fid in enumerate(v48_order)}
    for x in rows:
        x['v48_rank'] = int(new_rank[str(x['family_id'])])
    moved = int(sum(int(x['v48_rank']) != int(x['v31_rank']) for x in rows))
    freeze = {
        'verdict': 'PASS_V48_SELF_SUPPORTED_ORDER_FREEZE',
        'scientific_role': 'V48_COMPLETE_HDB_ORDER_FROZEN_BEFORE_OUTCOME_TRUTH',
        'source_1098_signal_sha256': SIGNAL_SHA256,
        'authorizing_1139_run': AUTHOR_1139_RUN,
        'authorizing_1139_artifact': AUTHOR_1139_ARTIFACT,
        'authorizing_1139_artifact_digest': AUTHOR_1139_DIGEST,
        'authorizing_1139_result_sha256': GAP_RESULT_SHA256,
        'authorizing_1139_vector_sha256': GAP_VECTOR_SHA256,
        'authorizing_1139_vector_canonical_sha256': GAP_VECTOR_CANONICAL_SHA256,
        'hdb_family_count': HDB_N,
        'joint_positive_candidate_count': 60,
        'self_supported_candidate_count': self_count,
        'v31_hdb_order_sha256': V31_HDB_ORDER_SHA256,
        'v48_hdb_order_sha256': V48_HDB_ORDER_SHA256,
        'moved_candidate_count': moved,
        'self_supported_condition': 'joint_signal AND quality_percentile <= component_best_v31_percentile',
        'equivalent_gain_condition': 'quality_suppression >= inheritance_gap',
        'promotion_key': 'quality_rank if self_supported else exact_v31_rank',
        'total_order_sort': '(promotion_key, exact_v31_rank, family_id)',
        'hdb_order': v48_order,
        'candidate_rows': rows,
        'truth_accessed': False,
        'literature_budget_used': False,
        'year_specific_rule': False,
        'budget_specific_rule': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'coefficient_selected': False,
        'oracle_identity_used_for_ranking': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V48_SELF_SUPPORTED_ORDER_FREEZE.json').write_text(json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': freeze['verdict'],
        'self_supported_candidate_count': self_count,
        'moved_candidate_count': moved,
        'v48_hdb_order_sha256': V48_HDB_ORDER_SHA256,
    }, indent=2, sort_keys=True))
    return 0


def build_v48_order(
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
                'v42_key': i + 1,
                'joint_gate': False,
                'self_supported_gate': False,
                'sugar_unchanged': True,
            }
            for i, fid in enumerate(base_order)
        ]
        return list(map(str, base_order)), rows

    qrank = dict(v42._QUALITY_RANK)
    require(len(base_order) == HDB_N and set(base_order) == set(qrank), 'HDB quality map not initialized on exact universe')
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
    for fid in map(str, base_order):
        rv = int(vrank[fid])
        rq = int(qrank[fid])
        pv = float((rv - 1) / (HDB_N - 1))
        pq = float((rq - 1) / (HDB_N - 1))
        cid = hdb_component[fid]
        pc = float(component_best[cid])
        quality_suppressed = bool(rq < rv)
        component_opportunity = bool(pc < pv)
        joint = bool(quality_suppressed and component_opportunity)
        quality_suppression = float(pv - pq)
        inheritance_gap = float(pv - pc)
        self_supported = bool(joint and pq <= pc)
        require(self_supported == bool(joint and quality_suppression >= inheritance_gap), 'runtime self-support algebra changed')
        key = int(rq if self_supported else rv)
        rows.append({
            'representative_family_id': fid,
            'family_id': fid,
            'component_id': cid,
            'v31_rank': rv,
            'quality_rank': rq,
            'v31_percentile': pv,
            'quality_percentile': pq,
            'component_best_v31_percentile': pc,
            'quality_suppression': quality_suppression,
            'inheritance_gap': inheritance_gap,
            'quality_suppressed': quality_suppressed,
            'component_opportunity': component_opportunity,
            'original_joint_gate': joint,
            'joint_gate': self_supported,
            'self_supported_gate': self_supported,
            'v42_key': key,
            'promotion_rank_gain': int(rv - key) if self_supported else 0,
        })
    require(sum(bool(x['original_joint_gate']) for x in rows) == 60, 'runtime joint count changed')
    require(sum(bool(x['self_supported_gate']) for x in rows) == SELF_SUPPORTED_N, 'runtime self-supported count changed')
    by_id = {str(x['family_id']): x for x in rows}
    order = sorted(base_order, key=lambda fid: (int(by_id[str(fid)]['v42_key']), int(vrank[str(fid)]), str(fid)))
    order = list(map(str, order))
    require(order_sha(order) == V48_HDB_ORDER_SHA256, 'runtime v48 HDB order changed')
    new_rank = {fid: i + 1 for i, fid in enumerate(order)}
    for x in rows:
        x['v42_rank'] = int(new_rank[str(x['family_id'])])
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
    authorizing_1091: Path,
    authorizing_1139: Path,
    vector_1139: Path,
    frozen_order: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    validate_1139(authorizing_1139, vector_1139)
    f = json.loads(frozen_order.read_text())
    require(f['verdict'] == 'PASS_V48_SELF_SUPPORTED_ORDER_FREEZE', 'v48 pretruth order freeze missing')
    require(f['scientific_role'] == 'V48_COMPLETE_HDB_ORDER_FROZEN_BEFORE_OUTCOME_TRUTH', 'v48 order freeze role changed')
    require(int(f['self_supported_candidate_count']) == SELF_SUPPORTED_N, 'v48 frozen self-supported count changed')
    require(f['v31_hdb_order_sha256'] == V31_HDB_ORDER_SHA256 and f['v48_hdb_order_sha256'] == V48_HDB_ORDER_SHA256, 'v48 frozen order identity changed')
    require(f['truth_accessed'] is False and f['literature_budget_used'] is False, 'v48 order was not frozen truth/budget free')

    original_builder = v42.build_v42_order
    original_variant = v42.VARIANT
    v42.build_v42_order = build_v48_order
    v42.VARIANT = VARIANT
    engine = output / '_frozen_v42_engine'
    try:
        rc = v42.evaluate_mode(
            sugar_root,
            hdbscan_root,
            truth_root,
            ranker_source,
            graph_file,
            component_file,
            authorizing_1091,
            engine,
        )
    finally:
        v42.build_v42_order = original_builder
        v42.VARIANT = original_variant
    require(rc == 0, 'frozen v42 execution engine failed')

    raw_path = engine / 'V42_QUALITY_COMPONENT_GATED_RESCUE_RESULT.json'
    require(raw_path.is_file(), 'frozen v42 engine result missing')
    raw = json.loads(raw_path.read_text())
    require(raw['parent_v31_reproduction_pass'] is True and len(raw['parent_v31_controls']) == 4, 'exact v31 parent reproduction failed')
    require(raw['pretruth_graph_sha256'] == v42.v40.GRAPH_SHA256 and raw['pretruth_component_sha256'] == v42.v40.COMPONENT_SHA256, 'frozen geometry changed')
    require(raw['sugar_rule'] == 'exact v31 unchanged' and raw['sugar_modified'] is False, 'Sugar changed')
    hdb_rows = list(raw['hdb_candidate_rows'])
    require(len(hdb_rows) == HDB_N, 'HDB row count changed')
    require(sum(bool(x['original_joint_gate']) for x in hdb_rows) == 60, 'runtime original joint count changed')
    require(sum(bool(x['self_supported_gate']) for x in hdb_rows) == SELF_SUPPORTED_N, 'runtime self-supported count changed')
    hdb_order = [str(x['family_id']) for x in sorted(hdb_rows, key=lambda x: int(x['v42_rank']))]
    require(order_sha(hdb_order) == V48_HDB_ORDER_SHA256, 'evaluated HDB order differs from pretruth freeze')
    require(hdb_order == list(map(str, f['hdb_order'])), 'evaluated HDB identities differ from pretruth freeze')

    panels = list(raw['panels'])
    require(len(panels) == 4, 'panel count changed')
    wins = int(sum(bool(x['superiority_pair_pass']) for x in panels))
    passed = bool(wins == 4)
    freeze: dict[str, Any] = {'verdict': 'NOT_FROZEN_V48_SELF_SUPPORTED_TRANSFER_FAIL', 'reference_sha256': None}
    engine_ref = engine / 'v42_quality_component_gated_rescue_reference.npz'
    if passed:
        require(engine_ref.is_file(), 'passing engine reference missing')
        dst = output / 'v48_self_supported_quality_component_transfer_reference.npz'
        shutil.copyfile(engine_ref, dst)
        freeze = {
            'verdict': 'PASS_V48_FULL_EXPOSED_SELF_SUPPORTED_TRANSFER_REFERENCE_FREEZE',
            'reference_sha256': sha(dst),
            'v48_hdb_order_sha256': V48_HDB_ORDER_SHA256,
            'self_supported_candidate_count': SELF_SUPPORTED_N,
        }

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V48_SELF_SUPPORTED_QUALITY_COMPONENT_TRANSFER_V1',
        'verdict': 'PASS_V48_SELF_SUPPORTED_QUALITY_COMPONENT_TRANSFER_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V48_SELF_SUPPORTED_QUALITY_COMPONENT_TRANSFER_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'HDB-only self-supported refinement of the fixed #1098 joint gate: a joint family may use immutable quality rank only when quality_percentile <= component_best_v31_percentile; Sugar exact v31 unchanged',
        'authorizing_1091_run': 31456963941,
        'authorizing_1091_artifact': 9088402091,
        'authorizing_1091_sha256': '2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842',
        'authorizing_1139_run': AUTHOR_1139_RUN,
        'authorizing_1139_artifact': AUTHOR_1139_ARTIFACT,
        'authorizing_1139_artifact_digest': AUTHOR_1139_DIGEST,
        'authorizing_1139_result_sha256': GAP_RESULT_SHA256,
        'authorizing_1139_vector_sha256': GAP_VECTOR_SHA256,
        'authorizing_1139_vector_canonical_sha256': GAP_VECTOR_CANONICAL_SHA256,
        'pretruth_graph_sha256': raw['pretruth_graph_sha256'],
        'pretruth_component_sha256': raw['pretruth_component_sha256'],
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': raw['parent_v31_controls'],
        'sugar_rule': 'exact v31 unchanged',
        'sugar_modified': False,
        'hdb_family_count': HDB_N,
        'hdb_original_joint_candidate_count': 60,
        'hdb_self_supported_candidate_count': SELF_SUPPORTED_N,
        'hdb_self_supported_condition': 'joint_signal AND quality_percentile <= component_best_v31_percentile',
        'hdb_equivalent_gain_condition': 'quality_suppression >= inheritance_gap',
        'hdb_promotion_key': 'quality_rank if self_supported else exact_v31_rank',
        'hdb_total_order_sort': '(promotion_key, exact_v31_rank, family_id)',
        'v31_hdb_order_sha256': V31_HDB_ORDER_SHA256,
        'v48_hdb_order_sha256': V48_HDB_ORDER_SHA256,
        'panel_wins': wins,
        'panels': panels,
        'hdb_candidate_rows': hdb_rows,
        'full_model_freeze': freeze,
        'alternate_balance_inequality_search': False,
        'epsilon_or_tolerance_relaxation': False,
        'inheritance_gap_threshold_search': False,
        'quality_suppression_threshold_search': False,
        'component_threshold_search': False,
        'quantile_search': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'identity_exception_used': False,
        'v47_gap_only_rescue': False,
        'alternate_boolean_gate_search': False,
        'or_rule_evaluated': False,
        'coefficient_search': False,
        'interpolation_search': False,
        'bonus_or_cap_search': False,
        'weighted_fusion_search': False,
        'equal_ranksum_retry': False,
        'pareto_layer_evaluated': False,
        'pairwise_dominance_evaluated': False,
        'component_representative_retry': False,
        'component_best_placement_retry': False,
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
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V48_SELF_SUPPORTED_QUALITY_COMPONENT_TRANSFER_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'panel_wins': wins,
        'hdb_self_supported_candidate_count': SELF_SUPPORTED_N,
        'panels': panels,
        'v48_hdb_order_sha256': V48_HDB_ORDER_SHA256,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    g = sub.add_parser('pretruth')
    g.add_argument('--sugar-root', type=Path, required=True)
    g.add_argument('--hdbscan-root', type=Path, required=True)
    g.add_argument('--output', type=Path, required=True)
    f = sub.add_parser('freeze-order')
    f.add_argument('--signal-file', type=Path, required=True)
    f.add_argument('--gap-result', type=Path, required=True)
    f.add_argument('--gap-vector', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    e = sub.add_parser('evaluate')
    e.add_argument('--sugar-root', type=Path, required=True)
    e.add_argument('--hdbscan-root', type=Path, required=True)
    e.add_argument('--truth-root', type=Path, required=True)
    e.add_argument('--ranker-source', type=Path, required=True)
    e.add_argument('--graph-file', type=Path, required=True)
    e.add_argument('--component-file', type=Path, required=True)
    e.add_argument('--authorizing-1091', type=Path, required=True)
    e.add_argument('--authorizing-1139', type=Path, required=True)
    e.add_argument('--vector-1139', type=Path, required=True)
    e.add_argument('--frozen-order', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'pretruth':
        return pretruth_mode(a.sugar_root, a.hdbscan_root, a.output)
    if a.mode == 'freeze-order':
        return freeze_order_mode(a.signal_file, a.gap_result, a.gap_vector, a.output)
    return evaluate_mode(
        a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source,
        a.graph_file, a.component_file, a.authorizing_1091,
        a.authorizing_1139, a.vector_1139, a.frozen_order, a.output,
    )


if __name__ == '__main__':
    raise SystemExit(main())
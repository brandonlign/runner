#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from orbittrace_v44_joint_component_best_placement_v1 import train_evaluate as v44

v42 = v44.v42
v40 = v42.v40

VARIANT = 'pareto_frontier_gated_component_best_placement_v1'
FRONTIER_RUN = 31459760333
FRONTIER_ARTIFACT = 9089357860
FRONTIER_DIGEST = 'sha256:ce055dc38f5f56d82e6330590fa30becaf6896ab4323de7e1d4abf4644e97a9a'
FRONTIER_VECTOR_SHA = '5ca5cab6f6a47c05d013237190ad21b247a13e22fa06988ee36dc0832a37fc02'
FRONTIER_CANONICAL_SHA = '8373f4946e7f84c7c3ee0ac51167881722d4f8b78c34383400f1967824df6798'
FRONTIER_RESULT_SHA = 'c114464d7798d7b765d365f2e3979c35128794173ccc712b120d5955361db6e1'
HDB_N = 229
SUGAR_N = 267

_FRONTIER_ROWS: dict[str, dict[str, Any]] = {}
_QUALITY_RANK: dict[str, int] = {}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def validate_frontier(vector_path: Path, result_path: Path) -> dict[str, dict[str, Any]]:
    require(v40.v22.sha(vector_path) == FRONTIER_VECTOR_SHA, '#1126 vector file identity changed')
    require(v40.v22.sha(result_path) == FRONTIER_RESULT_SHA, '#1126 result file identity changed')
    v = json.loads(vector_path.read_text())
    r = json.loads(result_path.read_text())
    require(v['verdict'] == 'PASS_V31_JOINT_COMPONENT_PARETO_FRONTIER_VECTOR_FREEZE', '#1126 vector verdict changed')
    require(v['scientific_role'] == 'FIXED_60_JOINT_FAMILY_PARETO_FRONTIER_FROZEN_BEFORE_OUTCOME_TRUTH_OR_1113_AUTHORIZATION', '#1126 vector role changed')
    require(v['canonical_sha256_without_self_field'] == FRONTIER_CANONICAL_SHA, '#1126 canonical vector changed')
    require(int(v['family_count']) == HDB_N and int(v['joint_family_count']) == 60 and len(v['families']) == 60, '#1126 vector universe changed')
    require(1 <= int(v['frontier_family_count']) < 60, '#1126 frontier is not a strict nonempty subset')
    require(int(v['frontier_family_count']) + int(v['dominated_family_count']) == 60, '#1126 frontier partition changed')
    for k in ('threshold_selected','quantile_selected','top_k_selected','rank_window_selected','literature_budget_used','second_pareto_layer_evaluated','relaxed_dominance_evaluated','epsilon_dominance_evaluated','weighted_score_evaluated','candidate_total_order_evaluated','promotion_position_evaluated','oracle_identity_hardcoded','truth_aware_group_identity_used_for_frontier','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(v[k] is False, f'#1126 vector forbidden flag changed: {k}')
    require(v['blind_exclusion'] == [20.0,55.0], '#1126 vector blind exclusion changed')

    require(r['verdict'] == 'PASS_V31_JOINT_COMPONENT_PARETO_FRONTIER_DIAGNOSTIC', '#1126 diagnostic verdict changed')
    require(r['scientific_role'] == 'POST_RESULT_THRESHOLD_FREE_PRIORITY_STRUCTURE_DIAGNOSTIC_NO_ORDER_OR_SUCCESSOR_EVALUATED', '#1126 result role changed')
    require(r['frontier_priority_supported_both_years_both_levels'] is True, '#1126 priority direction not supported')
    require(int(r['frontier_family_count']) == int(v['frontier_family_count']), '#1126 result/vector frontier count mismatch')
    require(r['source_signal_sha256'] == v44.SIGNAL_SHA, '#1126 parent signal identity changed')
    for k in ('new_rank_or_score_evaluated','candidate_total_order_evaluated','selector_order_evaluated','promotion_position_evaluated','replacement_rule_evaluated','literature_panel_evaluated','successor_selected','threshold_search','quantile_search','effect_size_threshold_selected','top_k_search','rank_window_search','budget_specific_rule','year_specific_rule','second_pareto_layer_evaluated','relaxed_dominance_evaluated','epsilon_dominance_evaluated','weighted_score_evaluated','alternate_component_statistic_search','component_size_search','q_calibration_search','graph_or_component_redefinition','feature_search','model_search','fusion_search','source_quota_selected','oracle_identity_hardcoded','truth_aware_group_identity_used_for_ranking','post_result_second_search','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(r[k] is False, f'#1126 result forbidden flag changed: {k}')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and r['blind_exclusion'] == [20.0,55.0], '#1126 result firewall changed')

    rows = {str(x['family_id']): x for x in v['families']}
    require(len(rows) == 60, 'duplicate #1126 frontier family')
    return rows


def build_v45_order(
    route: str,
    base_order: list[str],
    components: list[dict[str, Any]],
    rank_maps: dict[str, dict[str, int]],
) -> tuple[list[str], list[dict[str, Any]]]:
    require(route in ('sugar','hdbscan'), 'invalid route')
    if route == 'sugar':
        rows = [{
            'representative_family_id': str(fid),
            'family_id': str(fid),
            'v31_rank': i+1,
            'v31_percentile': float(i/(SUGAR_N-1)),
            'v45_placement_key': float(i/(SUGAR_N-1)),
            'pareto_frontier_record': False,
            'sugar_unchanged': True,
        } for i,fid in enumerate(base_order)]
        return list(map(str,base_order)), rows

    require(len(base_order) == HDB_N and len(_FRONTIER_ROWS) == 60, 'frontier map not initialized')
    require(set(_QUALITY_RANK) == set(map(str,base_order)), 'quality rank map not initialized')
    vrank = rank_maps['hdbscan']
    component_best = v44.component_best_percentiles(components, rank_maps)
    hdb_component: dict[str,str] = {}
    for c in components:
        cid = str(c['component_id'])
        for fid in map(str,c['hdbscan_family_ids']):
            require(fid not in hdb_component, 'HDB family in multiple components')
            hdb_component[fid] = cid
    require(set(hdb_component) == set(map(str,base_order)), 'HDB component assignment incomplete')

    rows: list[dict[str,Any]] = []
    reconstructed_joint: set[str] = set()
    reconstructed_frontier: set[str] = set()
    for fid0 in base_order:
        fid = str(fid0)
        rv = int(vrank[fid]); rq = int(_QUALITY_RANK[fid])
        ph = float((rv-1)/(HDB_N-1)); pq = float((rq-1)/(HDB_N-1))
        cid = hdb_component[fid]; pc = float(component_best[cid])
        quality_suppressed = bool(rq < rv)
        component_opportunity = bool(pc < ph)
        joint = bool(quality_suppressed and component_opportunity)
        if joint:
            reconstructed_joint.add(fid)
            require(fid in _FRONTIER_ROWS, f'joint family missing #1126 row {fid}')
            src = _FRONTIER_ROWS[fid]
            require(int(src['v31_rank']) == rv, f'#1126/v31 rank mismatch {fid}')
            require(abs(float(src['v31_percentile'])-ph) < 1e-15, f'#1126/v31 percentile mismatch {fid}')
            require(abs(float(src['component_best_v31_percentile'])-pc) < 1e-15, f'#1126 component percentile mismatch {fid}')
            frontier = bool(src['pareto_frontier_record'])
        else:
            require(fid not in _FRONTIER_ROWS, f'nonjoint family present in #1126 vector {fid}')
            frontier = False
        key = float(pc if frontier else ph)
        if frontier:
            reconstructed_frontier.add(fid)
            require(pc <= ph, 'frontier component placement worsens own v31')
        else:
            require(abs(key-ph) < 1e-15, 'nonfrontier placement changed')
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
            'pareto_frontier_record': frontier,
            'v45_placement_key': key,
        })

    require(reconstructed_joint == set(_FRONTIER_ROWS), 'reconstructed #1098 joint universe differs from #1126')
    expected_frontier = {fid for fid,row in _FRONTIER_ROWS.items() if bool(row['pareto_frontier_record'])}
    require(reconstructed_frontier == expected_frontier, 'reconstructed frontier identity changed')
    by_id = {str(r['family_id']):r for r in rows}
    order = sorted(map(str,base_order), key=lambda fid:(float(by_id[fid]['v45_placement_key']),float(by_id[fid]['v31_percentile']),fid))
    require(len(order) == HDB_N and set(order) == set(map(str,base_order)), 'invalid v45 HDB total order')
    new_rank = {fid:i+1 for i,fid in enumerate(order)}
    for r in rows:
        r['v45_rank'] = int(new_rank[str(r['family_id'])])
    return order, rows


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    return v40.pretruth_mode(sugar_root,hdbscan_root,output)


def evaluate_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    component_file: Path,
    authorizing_diagnostic: Path,
    placement_diagnostic: Path,
    frontier_vector: Path,
    frontier_result: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True,exist_ok=True)
    require(v40.v22.sha(graph_file) == v40.GRAPH_SHA256, 'pretruth graph identity changed')
    require(v40.v22.sha(component_file) == v40.COMPONENT_SHA256, 'pretruth component identity changed')
    v42.validate_authorizing_diagnostic(authorizing_diagnostic)
    v44.validate_placement_authorizer(placement_diagnostic)

    global _FRONTIER_ROWS, _QUALITY_RANK
    _FRONTIER_ROWS = validate_frontier(frontier_vector,frontier_result)
    _quality_order, qrank, quality_sha = v42.load_quality_rank(hdbscan_root)
    _QUALITY_RANK = dict(qrank)

    engine = output / '_frozen_v40_engine'
    original_builder = v40.build_v40_order
    original_variant = v40.VARIANT
    v40.build_v40_order = build_v45_order
    v40.VARIANT = VARIANT
    try:
        rc = v40.evaluate_mode(sugar_root,hdbscan_root,truth_root,ranker_source,graph_file,component_file,engine)
    finally:
        v40.build_v40_order = original_builder
        v40.VARIANT = original_variant
    require(rc == 0, 'frozen v40 evaluation engine failed')

    raw_path = engine / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_RESULT.json'
    require(raw_path.is_file(), 'frozen v40 result missing')
    raw = json.loads(raw_path.read_text())
    require(raw['parent_v31_reproduction_pass'] is True and len(raw['parent_v31_controls']) == 4, 'exact v31 parent reproduction failed')
    require(raw['pretruth_graph_sha256'] == v40.GRAPH_SHA256 and raw['pretruth_component_sha256'] == v40.COMPONENT_SHA256, 'frozen geometry changed')
    require(int(raw['component_count']) == 196 and int(raw['non_singleton_component_count']) == 113 and int(raw['singleton_component_count']) == 83, 'component counts changed')

    sugar_rows = list(raw['primary_component_rows']['sugar'])
    hdb_rows = list(raw['primary_component_rows']['hdbscan'])
    require(len(sugar_rows) == SUGAR_N and len(hdb_rows) == HDB_N, 'candidate row count changed')
    require(all(bool(r['sugar_unchanged']) for r in sugar_rows), 'Sugar changed')
    frontier_count = int(sum(bool(r['pareto_frontier_record']) for r in hdb_rows))
    joint_count = int(sum(bool(r['joint_gate']) for r in hdb_rows))
    require(joint_count == 60 and frontier_count == sum(bool(x['pareto_frontier_record']) for x in _FRONTIER_ROWS.values()), 'v45 gate/frontier count mismatch')

    sugar_v31_order = [str(x['family_id']) for x in sorted(sugar_rows,key=lambda r:int(r['v31_rank']))]
    hdb_v31_order = [str(x['family_id']) for x in sorted(hdb_rows,key=lambda r:int(r['v31_rank']))]
    hdb_v45_order = [str(x['family_id']) for x in sorted(hdb_rows,key=lambda r:int(r['v45_rank']))]
    old = {fid:i+1 for i,fid in enumerate(hdb_v31_order)}; new = {fid:i+1 for i,fid in enumerate(hdb_v45_order)}
    moved_up = int(sum(new[fid] < old[fid] for fid in hdb_v31_order)); moved_down = int(sum(new[fid] > old[fid] for fid in hdb_v31_order)); unchanged = HDB_N-moved_up-moved_down
    panels = list(raw['panels']); wins = int(sum(bool(x['superiority_pair_pass']) for x in panels)); require(wins == int(raw['panel_wins']), 'panel win count mismatch'); passed = bool(wins == 4)

    engine_ref = engine / 'v40_component_best_evidence_representative_reference.npz'
    freeze: dict[str,Any] = {'verdict':'NOT_FROZEN_V45_PARETO_FRONTIER_COMPONENT_PLACEMENT_FAIL','reference_sha256':None}
    if passed:
        require(engine_ref.is_file(), 'passing v45 engine reference missing')
        dst = output / 'v45_pareto_frontier_component_placement_reference.npz'
        shutil.copyfile(engine_ref,dst)
        freeze = {
            'verdict':'PASS_V45_FULL_EXPOSED_PARETO_FRONTIER_COMPONENT_PLACEMENT_REFERENCE_FREEZE',
            'reference_sha256':v40.v22.sha(dst),
            'pretruth_graph_sha256':v40.GRAPH_SHA256,
            'pretruth_component_sha256':v40.COMPONENT_SHA256,
            'quality_order_sha256':quality_sha,
            'frontier_vector_sha256':FRONTIER_VECTOR_SHA,
            'frontier_vector_canonical_sha256':FRONTIER_CANONICAL_SHA,
            'frontier_rule':'#1126 frozen Pareto frontier minimizing (v31 percentile, component-best percentile)',
            'frontier_placement':'component_best_v31_percentile',
            'nonfrontier_placement':'exact_v31_percentile',
            'sugar_rule':'exact v31 unchanged',
            'in_sample_reference_score_used_for_promotion':False,
        }
    (output/'V45_PARETO_FRONTIER_COMPONENT_PLACEMENT_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True,allow_nan=False)+'\n')

    result = {
        'scientific_stage':'EXPOSED_SONOTACO_V45_PARETO_FRONTIER_COMPONENT_PLACEMENT_V1',
        'verdict':'PASS_V45_PARETO_FRONTIER_COMPONENT_PLACEMENT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V45_PARETO_FRONTIER_COMPONENT_PLACEMENT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change':'apply component-best placement only to truth-blind #1126 Pareto-frontier records inside the exact reconstructed #1098 joint gate; all other HDB candidates and all Sugar candidates retain exact-v31 placement',
        'gate_authorizing_run':v42.AUTHOR_RUN,
        'gate_authorizing_artifact':v42.AUTHOR_ARTIFACT,
        'gate_authorizing_sha256':v42.AUTHOR_RESULT_SHA,
        'placement_authorizing_run':v44.PLACEMENT_RUN,
        'placement_authorizing_artifact':v44.PLACEMENT_ARTIFACT,
        'placement_authorizing_sha256':v44.PLACEMENT_RESULT_SHA,
        'frontier_source_run':FRONTIER_RUN,
        'frontier_source_artifact':FRONTIER_ARTIFACT,
        'frontier_source_digest':FRONTIER_DIGEST,
        'frontier_vector_sha256':FRONTIER_VECTOR_SHA,
        'frontier_vector_canonical_sha256':FRONTIER_CANONICAL_SHA,
        'frontier_result_sha256':FRONTIER_RESULT_SHA,
        'frontier_family_count':frontier_count,
        'joint_positive_candidate_count':joint_count,
        'quality_order_sha256':quality_sha,
        'parent_v31_reproduction_pass':True,
        'parent_v31_controls':raw['parent_v31_controls'],
        'pretruth_graph_sha256':raw['pretruth_graph_sha256'],
        'pretruth_component_sha256':raw['pretruth_component_sha256'],
        'sugar_rule':'exact v31 unchanged',
        'hdb_frontier_rule':'frozen #1126 Pareto-frontier record flag',
        'hdb_frontier_placement_key':'component_best_v31_percentile',
        'hdb_nonfrontier_placement_key':'exact_v31_percentile',
        'hdb_total_order_sort':'(placement_key, exact_v31_percentile, family_id)',
        'panel_wins':wins,
        'panels':panels,
        'order_diagnostics':{
            'sugar':{
                'family_count':SUGAR_N,
                'moved_up_in_total_order_count':0,
                'moved_down_in_total_order_count':0,
                'unchanged_count':SUGAR_N,
                'v31_order_sha256':v40.order_sha(sugar_v31_order),
                'v45_total_order_sha256':v40.order_sha(sugar_v31_order),
                'exact_v31_unchanged':True,
            },
            'hdbscan':{
                'family_count':HDB_N,
                'joint_positive_candidate_count':joint_count,
                'pareto_frontier_candidate_count':frontier_count,
                'moved_up_in_total_order_count':moved_up,
                'moved_down_in_total_order_count':moved_down,
                'unchanged_count':unchanged,
                'v31_order_sha256':v40.order_sha(hdb_v31_order),
                'v45_total_order_sha256':v40.order_sha(hdb_v45_order),
            },
        },
        'hdb_candidate_rows':hdb_rows,
        'full_model_freeze':freeze,
        'frontier_cardinality_used_as_parameter':False,
        'top_k_selected':False,
        'threshold_search':False,
        'quantile_search':False,
        'rank_window_selected':False,
        'budget_specific_rule':False,
        'year_specific_rule':False,
        'second_pareto_layer_evaluated':False,
        'relaxed_dominance_evaluated':False,
        'epsilon_dominance_evaluated':False,
        'quality_rank_placement_used':False,
        'quality_component_blend_search':False,
        'promotion_coefficient_search':False,
        'promotion_bonus_search':False,
        'promotion_cap_search':False,
        'alternate_component_statistic_search':False,
        'component_size_search':False,
        'q_calibration_search':False,
        'graph_or_component_redefinition':False,
        'candidate_generation_changed':False,
        'candidate_membership_changed':False,
        'feature_search':False,
        'model_search':False,
        'k_search':False,
        'scaling_search':False,
        'diversity_search':False,
        'fusion_search':False,
        'source_quota_selected':False,
        'oracle_identity_used_for_ranking':False,
        'truth_aware_group_identity_used_for_ranking':False,
        'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access':False,
        'target_region_events_accessed':False,
        'maarsy_scientific_access':False,
        'dms_scientific_access':False,
        'blind_exclusion':[20.0,55.0],
    }
    (output/'V45_PARETO_FRONTIER_COMPONENT_PLACEMENT_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'frontier_family_count':frontier_count,'panels':panels,'order_diagnostics':result['order_diagnostics'],'full_model_freeze':freeze},indent=2,sort_keys=True,allow_nan=False))
    return 0


def main() -> int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('pretruth'); a.add_argument('--sugar-root',type=Path,required=True); a.add_argument('--hdbscan-root',type=Path,required=True); a.add_argument('--output',type=Path,required=True)
    b=sub.add_parser('evaluate'); b.add_argument('--sugar-root',type=Path,required=True); b.add_argument('--hdbscan-root',type=Path,required=True); b.add_argument('--truth-root',type=Path,required=True); b.add_argument('--ranker-source',type=Path,required=True); b.add_argument('--graph-file',type=Path,required=True); b.add_argument('--component-file',type=Path,required=True); b.add_argument('--authorizing-diagnostic',type=Path,required=True); b.add_argument('--placement-diagnostic',type=Path,required=True); b.add_argument('--frontier-vector',type=Path,required=True); b.add_argument('--frontier-result',type=Path,required=True); b.add_argument('--output',type=Path,required=True)
    x=p.parse_args()
    if x.mode=='pretruth': return pretruth_mode(x.sugar_root,x.hdbscan_root,x.output)
    return evaluate_mode(x.sugar_root,x.hdbscan_root,x.truth_root,x.ranker_source,x.graph_file,x.component_file,x.authorizing_diagnostic,x.placement_diagnostic,x.frontier_vector,x.frontier_result,x.output)

if __name__=='__main__': raise SystemExit(main())

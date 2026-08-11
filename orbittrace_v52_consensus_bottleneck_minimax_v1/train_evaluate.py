#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from orbittrace_v31_local_geometry_margin_oof_v1 import train_evaluate as v31

HDB_N = 229
SUGAR_N = 267
PROTOCOL_BLOB = 'd2fa6ca637becc952950ee6eaa56deba09c81d82'
PARENT_SOURCE_BLOB = '917e3cd6f9310ca1282e0efa58ed0924d03ed4da'
RANKER_SHA = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V51_VECTOR_SHA = '5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc'
V51_DIAG_SHA = 'fef1d2c5bb83748de5c5511615915e76ce6fcd0801afbddb0e01bab09b9ab76d'
V51_RUN = 31493423814
V51_ARTIFACT = 9101972590
V51_DIGEST = 'sha256:56258a0be52d83c0d6dbfcffdb9fd9a2c6b73587ba8d92d7bdccdef9729868c9'
V51_HEAD = '3da2587e569a7487db51df2ad1e2624b75e88c61'
LOCAL_SHA = '9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595'
V31_HDB_SHA = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'
V52_HDB_SHA = '75fb44015e348c6b1bf0367e74db8e273e29862e132b5ef3305b2ddb409d8cc7'
EXPECTED_CHANGED = 217
EXPECTED_UP = 117
EXPECTED_DOWN = 100
EXPECTED_UNCHANGED = 12
EXPECTED_MAX_UP = 55
EXPECTED_MAX_DOWN = 71
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


def validate_v51(vector_file: Path, diag_file: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    require(sha(vector_file) == V51_VECTOR_SHA, 'v51 vector identity changed')
    require(sha(diag_file) == V51_DIAG_SHA, 'v51 diagnostic identity changed')
    vector = json.loads(vector_file.read_text())
    diag = json.loads(diag_file.read_text())
    require(vector['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_VECTOR_CAPTURE', 'v51 vector verdict changed')
    require(vector['scientific_role'] == 'EXACT_V31_FUSION_INPUT_RANKS_CAPTURED_BEFORE_DIAGNOSTIC_RECOVERABILITY_ATTACHMENT', 'v51 vector role changed')
    require(vector['parent_source_blob'] == PARENT_SOURCE_BLOB and vector['ranker_source_sha256'] == RANKER_SHA, 'v51 parent source changed')
    require(int(vector['family_count']) == HDB_N and len(vector['families']) == HDB_N, 'v51 family count changed')
    require(vector['local_order_sha256'] == LOCAL_SHA and vector['fused_order_sha256'] == V31_HDB_SHA, 'v51 order identity changed')
    require(vector['diagnostic_recoverability_attached'] is False and vector['annual_own_family_f1_attached'] is False, 'v51 vector contains diagnostic outcome')
    require(vector['literature_budget_used_in_statistic'] is False and vector['boundary_identity_used'] is False and vector['component_quality_topology_signal_used'] is False, 'v51 statistic contaminated by prior mechanisms')
    require(vector['new_candidate_order_evaluated'] is False and vector['selector_evaluated'] is False and vector['successor_selected'] is False, 'v51 vector evaluated successor')
    require(vector['threshold_selected'] is False and vector['top_k_selected'] is False and vector['rank_window_selected'] is False, 'v51 vector selected tuning')
    check = dict(vector); expected = str(check.pop('canonical_sha256_without_self_field'))
    require(canonical_sha(check) == expected, 'v51 vector canonical identity changed')

    require(diag['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC', 'v51 diagnostic verdict changed')
    require(diag['scientific_role'] == 'POST_V31_INTERNAL_CONSENSUS_BOTTLENECK_DIAGNOSTIC_ONLY_NO_SUCCESSOR_EVALUATED', 'v51 diagnostic role changed')
    require(int(diag['family_count']) == HDB_N and diag['direction_supported_both_years'] is True, 'v51 diagnostic population/direction changed')
    for y in ('2013', '2014'):
        a = diag['annual_diagnostics'][y]
        require(a['direction_pass'] is True, f'v51 {y} direction changed')
        require(float(a['recoverable']['median_consensus_bottleneck']) < float(a['nonrecoverable']['median_consensus_bottleneck']), f'v51 {y} median direction changed')
    for k in ('new_rank_or_score_used_for_ranking', 'candidate_total_order_evaluated', 'selector_evaluated', 'replacement_rule_evaluated', 'literature_panel_evaluated', 'successor_selected', 'minimax_successor_evaluated', 'pareto_rule_evaluated', 'threshold_search', 'top_k_search', 'rank_window_search', 'fusion_weight_search', 'rank_algebra_search', 'literature_budget_analysis', 'boundary_identity_used', 'post_result_second_search', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(diag[k] is False, f'v51 forbidden diagnostic flag set: {k}')
    require(diag['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and diag['blind_exclusion'] == [20.0, 55.0], 'v51 firewall changed')
    return vector, diag


def derive_order(vector: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    rows = list(vector['families'])
    ids = [str(r['family_id']) for r in rows]
    require(len(set(ids)) == HDB_N, 'duplicate v51 family identity')
    by = {str(r['family_id']): r for r in rows}
    local_ranks = sorted(int(r['local_rank']) for r in rows)
    v19_ranks = sorted(int(r['v19_rank']) for r in rows)
    require(local_ranks == list(range(1, HDB_N + 1)), 'v51 local ranks not permutation')
    require(v19_ranks == list(range(1, HDB_N + 1)), 'v51 v19 ranks not permutation')
    local_order = [str(r['family_id']) for r in sorted(rows, key=lambda r: (int(r['local_rank']), str(r['family_id'])))]
    require(order_sha(local_order) == LOCAL_SHA, 'v51 local order reconstruction changed')

    # v31 fused order is frozen independently by hash; exact fused ranks are supplied at runtime
    # and at freeze time by a caller-provided exact-v31 order.
    for r in rows:
        lr = int(r['local_rank']); vr = int(r['v19_rank'])
        b = max((lr - 1) / (HDB_N - 1), (vr - 1) / (HDB_N - 1))
        require(abs(float(r['consensus_bottleneck']) - b) < 1e-15, 'v51 bottleneck arithmetic changed')
    return ids, local_order, by


def freeze_mode(vector_file: Path, diag_file: Path, v31_order_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    vector, _ = validate_v51(vector_file, diag_file)
    ids, local_order, by = derive_order(vector)
    v31_obj = json.loads(v31_order_file.read_text())
    v31_order = list(map(str, v31_obj['v31_hdb_order']))
    require(len(v31_order) == HDB_N and set(v31_order) == set(ids), 'exact-v31 order universe changed')
    require(order_sha(v31_order) == V31_HDB_SHA, 'exact-v31 order identity changed')
    v31_rank = {f: i + 1 for i, f in enumerate(v31_order)}
    order = sorted(ids, key=lambda f: (float(by[f]['consensus_bottleneck']), int(v31_rank[f]), f))
    require(order_sha(order) == V52_HDB_SHA, 'v52 minimax order identity changed')
    new_rank = {f: i + 1 for i, f in enumerate(order)}
    moved = [f for f in v31_order if new_rank[f] != v31_rank[f]]
    up = [f for f in moved if new_rank[f] < v31_rank[f]]
    down = [f for f in moved if new_rank[f] > v31_rank[f]]
    stats = {
        'moved_candidate_count': len(moved),
        'moved_up_count': len(up),
        'moved_down_count': len(down),
        'unchanged_count': HDB_N - len(moved),
        'maximum_upward_displacement': max((v31_rank[f] - new_rank[f] for f in up), default=0),
        'maximum_downward_displacement': max((new_rank[f] - v31_rank[f] for f in down), default=0),
    }
    require(stats == {
        'moved_candidate_count': EXPECTED_CHANGED,
        'moved_up_count': EXPECTED_UP,
        'moved_down_count': EXPECTED_DOWN,
        'unchanged_count': EXPECTED_UNCHANGED,
        'maximum_upward_displacement': EXPECTED_MAX_UP,
        'maximum_downward_displacement': EXPECTED_MAX_DOWN,
    }, 'v52 structural consequences changed')
    payload: dict[str, Any] = {
        'verdict': 'PASS_V52_CONSENSUS_BOTTLENECK_MINIMAX_ORDER_FREEZE',
        'scientific_role': 'COMPLETE_V52_HDB_MINIMAX_ORDER_FROZEN_BEFORE_CURRENT_OUTCOME_EVALUATION',
        'authorizing_v51_run': V51_RUN,
        'authorizing_v51_artifact': V51_ARTIFACT,
        'authorizing_v51_digest': V51_DIGEST,
        'authorizing_v51_head': V51_HEAD,
        'authorizing_vector_sha256': V51_VECTOR_SHA,
        'authorizing_diagnostic_sha256': V51_DIAG_SHA,
        'family_count': HDB_N,
        'local_order_sha256': LOCAL_SHA,
        'v31_hdb_order': v31_order,
        'v31_hdb_order_sha256': V31_HDB_SHA,
        'v52_hdb_order': order,
        'v52_hdb_order_sha256': V52_HDB_SHA,
        'order_rule': '(consensus_bottleneck=max(local_rank_percentile,v19_rank_percentile), exact_v31_fused_rank, family_id); lower first',
        **stats,
        'current_outcome_truth_used_to_define_order': False,
        'literature_budget_used_to_define_order': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'alternate_tiebreak_evaluated': False,
        'fusion_weight_selected': False,
        'pareto_rule_used': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    payload['canonical_sha256_without_self_field'] = canonical_sha(payload)
    p = output / 'V52_CONSENSUS_BOTTLENECK_MINIMAX_ORDER_FREEZE.json'
    p.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': payload['verdict'], 'v52_hdb_order_sha256': V52_HDB_SHA, **stats, 'file_sha256': sha(p), 'canonical_sha256_without_self_field': payload['canonical_sha256_without_self_field']}, indent=2, sort_keys=True))
    return 0


def run_v31(sugar_root: Path, hdb_root: Path, truth_root: Path, ranker_source: Path, output: Path, replacement_hdb_order: list[str] | None = None, expected_vector: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    output.mkdir(parents=True, exist_ok=True)
    require(v31.v22.sha(ranker_source) == RANKER_SHA, '#839 ranker source changed')
    original = v31.v19.fusion_orders
    captured: list[dict[str, list[str]]] = []

    def patched(order_a, order_b):
        a = list(map(str, order_a)); b = list(map(str, order_b))
        require(len(a) == len(b) and set(a) == set(b), 'v31 fusion input universes changed')
        base = original(order_a, order_b)
        rs = list(map(str, base['rank_sum']))
        captured.append({'local_order': a, 'v19_order': b, 'v31_fused_order': rs})
        if len(a) == HDB_N and replacement_hdb_order is not None:
            require(expected_vector is not None, 'missing v52 expected vector')
            by = {str(r['family_id']): r for r in expected_vector['families']}
            require(order_sha(a) == LOCAL_SHA, 'runtime HDB local order changed')
            manifest = list(map(str, expected_vector.get('_v19_order_runtime', b)))
            require(b == manifest, 'runtime HDB v19 order changed')
            require(order_sha(rs) == V31_HDB_SHA, 'runtime exact-v31 fused order changed')
            v31rank = {f: i + 1 for i, f in enumerate(rs)}
            recomputed = sorted(a, key=lambda f: (float(by[f]['consensus_bottleneck']), v31rank[f], f))
            require(recomputed == replacement_hdb_order and order_sha(recomputed) == V52_HDB_SHA, 'runtime v52 minimax order differs from freeze')
            out = dict(base); out['rank_sum'] = list(replacement_hdb_order); return out
        return base

    old_argv = list(sys.argv)
    v31.v19.fusion_orders = patched
    try:
        sys.argv = ['train_evaluate.py', '--sugar-root', str(sugar_root), '--hdbscan-root', str(hdb_root), '--truth-root', str(truth_root), '--ranker-source', str(ranker_source), '--output', str(output)]
        rc = v31.main(); require(rc == 0, 'v31 engine failed')
    finally:
        sys.argv = old_argv; v31.v19.fusion_orders = original
    require(len(captured) == 2 and {len(x['local_order']) for x in captured} == {SUGAR_N, HDB_N}, 'unexpected v31 fusion calls')
    rp = output / 'V31_LOCAL_GEOMETRY_OOF_RESULT.json'; require(rp.is_file(), 'v31 result missing')
    return json.loads(rp.read_text()), {str(len(x['local_order'])): x for x in captured}


def validate_parent(parent: dict[str, Any]) -> None:
    require(parent['panel_wins'] == 2 and len(parent['panels']) == 4, 'v31 parent panel state changed')
    require(parent['strict_whole_shower_oof'] is True and parent['feature_dimension'] == 71 and parent['nearest_k'] == 1, 'v31 geometry changed')
    require(parent['annual_margin'] == 'd_nonpositive-d_positive' and parent['annual_combiner'] == 'min(margin_2013,margin_2014)', 'v31 score changed')
    require(parent['fusion'] == 'one equal rank-sum with exact v19' and parent['diversity'] == {'lambda': 0.8, 'scale': 1.0}, 'v31 fusion/diversity changed')
    pmap = {(str(x['comparator']), int(x['year'])): x for x in parent['panels']}
    require(set(pmap) == set(PARENT), 'v31 panel identities changed')
    for key, (f1, rec) in PARENT.items():
        row = pmap[key]; require(abs(float(row['candidate_macro_f1']) - f1) < 1e-12 and int(row['candidate_recovered_f1_gt_0_5']) == rec, f'{key} v31 control changed')
    require(parent['target_information_access'] is False and parent['target_region_events_accessed'] is False and parent['maarsy_scientific_access'] is False and parent['dms_scientific_access'] is False, 'v31 firewall changed')
    require(parent['blind_exclusion'] == [20.0, 55.0] and parent['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'v31 role changed')


def evaluate_mode(sugar_root: Path, hdb_root: Path, truth_root: Path, ranker_source: Path, vector_file: Path, diag_file: Path, freeze_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    vector, _ = validate_v51(vector_file, diag_file)
    f = json.loads(freeze_file.read_text())
    require(f['verdict'] == 'PASS_V52_CONSENSUS_BOTTLENECK_MINIMAX_ORDER_FREEZE' and f['scientific_role'] == 'COMPLETE_V52_HDB_MINIMAX_ORDER_FROZEN_BEFORE_CURRENT_OUTCOME_EVALUATION', 'v52 freeze changed')
    require(f['authorizing_vector_sha256'] == V51_VECTOR_SHA and f['authorizing_diagnostic_sha256'] == V51_DIAG_SHA, 'v52 authorizer changed')
    require(f['v31_hdb_order_sha256'] == V31_HDB_SHA and f['v52_hdb_order_sha256'] == V52_HDB_SHA, 'v52 order identity changed')
    require(order_sha(list(map(str, f['v31_hdb_order']))) == V31_HDB_SHA and order_sha(list(map(str, f['v52_hdb_order']))) == V52_HDB_SHA, 'v52 serialized order hash changed')
    require(f['current_outcome_truth_used_to_define_order'] is False and f['literature_budget_used_to_define_order'] is False, 'v52 order not outcome-independent')

    parent_dir = output / '_parent_v31'; variant_dir = output / '_variant_v52'
    parent, pcapture = run_v31(sugar_root, hdb_root, truth_root, ranker_source, parent_dir)
    validate_parent(parent)
    ph = pcapture[str(HDB_N)]
    require(order_sha(ph['local_order']) == LOCAL_SHA and order_sha(ph['v31_fused_order']) == V31_HDB_SHA, 'parent runtime HDB capture changed')
    # bind runtime immutable v19 order to captured v51 vector execution
    vector = dict(vector); vector['_v19_order_runtime'] = list(ph['v19_order'])
    variant, vcapture = run_v31(sugar_root, hdb_root, truth_root, ranker_source, variant_dir, list(map(str, f['v52_hdb_order'])), vector)
    vh = vcapture[str(HDB_N)]; vs = vcapture[str(SUGAR_N)]
    require(order_sha(vh['local_order']) == LOCAL_SHA and order_sha(vh['v31_fused_order']) == V31_HDB_SHA, 'variant runtime constituent orders changed')
    require(vs == pcapture[str(SUGAR_N)], 'Sugar fusion inputs/output changed from exact parent')

    panels = list(variant['panels']); require(len(panels) == 4, 'variant panels changed')
    wins = sum(bool(x['superiority_pair_pass']) for x in panels)
    passed = wins == 4
    freeze: dict[str, Any] = {'verdict': 'NOT_FROZEN_V52_CONSENSUS_BOTTLENECK_MINIMAX_FAIL', 'reference_sha256': None}
    parent_ref = variant_dir / 'v31_local_geometry_reference.npz'
    if passed:
        require(parent_ref.is_file(), 'passing v52 reference missing')
        dst = output / 'v52_consensus_bottleneck_minimax_reference.npz'; shutil.copyfile(parent_ref, dst)
        freeze = {'verdict': 'PASS_V52_FULL_EXPOSED_CONSENSUS_BOTTLENECK_MINIMAX_REFERENCE_FREEZE', 'reference_sha256': v31.v22.sha(dst), 'v31_hdb_order_sha256': V31_HDB_SHA, 'v52_hdb_order_sha256': V52_HDB_SHA, 'sugar_rule': 'exact v31 unchanged', 'hdb_rule': 'minimize worst normalized constituent rank; exact-v31 fused rank then family_id tie-break', 'in_sample_reference_score_used_for_promotion': False}
    (output / 'V52_CONSENSUS_BOTTLENECK_MINIMAX_MODEL_FREEZE.json').write_text(json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n')

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V52_CONSENSUS_BOTTLENECK_MINIMAX_V1',
        'verdict': 'PASS_V52_CONSENSUS_BOTTLENECK_MINIMAX_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V52_CONSENSUS_BOTTLENECK_MINIMAX_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'Sugar exact v31; HDB replaces only final equal rank-sum with order by max(local_rank_percentile,v19_rank_percentile), then exact-v31 fused rank and family_id',
        'pre_result_frozen_protocol_blob': PROTOCOL_BLOB,
        'parent_source_blob': PARENT_SOURCE_BLOB,
        'authorizing_v51_run': V51_RUN,
        'authorizing_v51_artifact': V51_ARTIFACT,
        'authorizing_v51_digest': V51_DIGEST,
        'authorizing_v51_vector_sha256': V51_VECTOR_SHA,
        'authorizing_v51_diagnostic_sha256': V51_DIAG_SHA,
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': [{'comparator': k[0], 'year': k[1], 'macro_f1': v[0], 'recovered_f1_gt_0_5': v[1]} for k, v in PARENT.items()],
        'hdb_local_order_sha256': LOCAL_SHA,
        'v31_hdb_order_sha256': V31_HDB_SHA,
        'v52_hdb_order_sha256': V52_HDB_SHA,
        'moved_candidate_count': EXPECTED_CHANGED,
        'moved_up_count': EXPECTED_UP,
        'moved_down_count': EXPECTED_DOWN,
        'unchanged_count': EXPECTED_UNCHANGED,
        'maximum_upward_displacement': EXPECTED_MAX_UP,
        'maximum_downward_displacement': EXPECTED_MAX_DOWN,
        'sugar_rule': 'exact v31 unchanged',
        'hdb_rule': '(consensus_bottleneck=max(local_rank_percentile,v19_rank_percentile), exact_v31_fused_rank, family_id)',
        'panel_wins': wins,
        'panels': panels,
        'full_model_freeze': freeze,
        'threshold_search': False,
        'quantile_search': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'fusion_weight_search': False,
        'alternate_max_min_search': False,
        'pareto_rule_evaluated': False,
        'alternate_tiebreak_search': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'route_specific_exception_beyond_frozen_sugar_parent': False,
        'diversity_search': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'metric_search': False,
        'scaling_search': False,
        'component_quality_signal_used': False,
        'source_quota_selected': False,
        'oracle_identity_used_for_ranking': False,
        'boundary_rescue_list_created': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V52_CONSENSUS_BOTTLENECK_MINIMAX_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    shutil.rmtree(parent_dir); shutil.rmtree(variant_dir)
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels, 'v52_hdb_order_sha256': V52_HDB_SHA, 'full_model_freeze': freeze}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='mode', required=True)
    f = sub.add_parser('freeze-order'); f.add_argument('--vector-file', type=Path, required=True); f.add_argument('--diagnostic-file', type=Path, required=True); f.add_argument('--v31-order-file', type=Path, required=True); f.add_argument('--output', type=Path, required=True)
    e = sub.add_parser('evaluate'); e.add_argument('--sugar-root', type=Path, required=True); e.add_argument('--hdbscan-root', type=Path, required=True); e.add_argument('--truth-root', type=Path, required=True); e.add_argument('--ranker-source', type=Path, required=True); e.add_argument('--vector-file', type=Path, required=True); e.add_argument('--diagnostic-file', type=Path, required=True); e.add_argument('--freeze-file', type=Path, required=True); e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'freeze-order': return freeze_mode(a.vector_file, a.diagnostic_file, a.v31_order_file, a.output)
    return evaluate_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.vector_file, a.diagnostic_file, a.freeze_file, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

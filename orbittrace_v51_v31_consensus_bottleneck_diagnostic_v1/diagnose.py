#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v31_local_geometry_margin_oof_v1 import train_evaluate as v31

HDB_N = 229
RECOVERY = 0.5
PARENT_SOURCE_BLOB = '917e3cd6f9310ca1282e0efa58ed0924d03ed4da'
RANKER_SOURCE_SHA256 = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
HDB_LOCAL_ORDER_SHA256 = '9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595'
HDB_FUSED_ORDER_SHA256 = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'
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


def summarize(values: list[float]) -> dict[str, Any]:
    require(values, 'empty consensus-bottleneck class')
    x = np.asarray(values, dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite consensus bottleneck')
    return {
        'count': int(len(x)),
        'median_consensus_bottleneck': float(np.median(x)),
        'q25_consensus_bottleneck': float(np.percentile(x, 25.0, method='linear')),
        'q75_consensus_bottleneck': float(np.percentile(x, 75.0, method='linear')),
        'min_consensus_bottleneck': float(np.min(x)),
        'max_consensus_bottleneck': float(np.max(x)),
    }


def exact_parent_capture(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    output: Path,
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    output.mkdir(parents=True, exist_ok=True)
    require(v31.v22.sha(ranker_source) == RANKER_SOURCE_SHA256, '#839 ranker source changed')

    original = v31.v19.fusion_orders
    captured: list[dict[str, list[str]]] = []

    def capture_and_delegate(order_a, order_b):
        a = list(map(str, order_a))
        b = list(map(str, order_b))
        require(len(a) == len(b) and set(a) == set(b), 'v31 fusion input universes changed')
        result = original(order_a, order_b)
        require('rank_sum' in result, 'v31 fusion rank_sum missing')
        rs = list(map(str, result['rank_sum']))
        require(len(rs) == len(a) and set(rs) == set(a), 'v31 fusion output universe changed')
        captured.append({'local_order': a, 'v19_order': b, 'fused_order': rs})
        return result

    old_argv = list(sys.argv)
    v31.v19.fusion_orders = capture_and_delegate
    try:
        sys.argv = [
            'train_evaluate.py',
            '--sugar-root', str(sugar_root),
            '--hdbscan-root', str(hdbscan_root),
            '--truth-root', str(truth_root),
            '--ranker-source', str(ranker_source),
            '--output', str(output),
        ]
        rc = v31.main()
        require(rc == 0, 'frozen v31 parent execution failed')
    finally:
        sys.argv = old_argv
        v31.v19.fusion_orders = original

    require(len(captured) == 2, 'expected exactly two v31 fusion calls')
    by_n = {len(x['local_order']): x for x in captured}
    require(set(by_n) == {267, HDB_N}, 'unexpected v31 fusion route sizes')
    h = by_n[HDB_N]

    result_path = output / 'V31_LOCAL_GEOMETRY_OOF_RESULT.json'
    require(result_path.is_file(), 'frozen v31 parent result missing')
    parent = json.loads(result_path.read_text())
    require(parent['verdict'] == 'FAIL_V31_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'v31 parent verdict changed')
    require(parent['panel_wins'] == 2 and len(parent['panels']) == 4, 'v31 parent panel state changed')
    require(parent['strict_whole_shower_oof'] is True and parent['feature_dimension'] == 71 and parent['nearest_k'] == 1, 'v31 parent geometry changed')
    require(parent['annual_margin'] == 'd_nonpositive-d_positive' and parent['annual_combiner'] == 'min(margin_2013,margin_2014)', 'v31 parent score changed')
    require(parent['fusion'] == 'one equal rank-sum with exact v19', 'v31 parent fusion changed')
    require(parent['diversity'] == {'lambda': 0.8, 'scale': 1.0}, 'v31 parent diversity changed')
    require(parent['candidate_membership_changed'] is False and parent['pretruth_feature_changed'] is False, 'v31 parent universe changed')
    require(parent['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'v31 SonotaCo role changed')
    require(parent['target_information_access'] is False and parent['target_region_events_accessed'] is False, 'v31 target firewall changed')
    require(parent['maarsy_scientific_access'] is False and parent['dms_scientific_access'] is False, 'v31 protected-survey firewall changed')
    require(parent['blind_exclusion'] == [20.0, 55.0], 'v31 blind exclusion changed')

    pmap = {(str(x['comparator']), int(x['year'])): x for x in parent['panels']}
    require(set(pmap) == set(PARENT), 'v31 parent panel identities changed')
    for key, (f1, recovered) in PARENT.items():
        row = pmap[key]
        require(abs(float(row['candidate_macro_f1']) - f1) < 1e-12, f'{key} v31 macro F1 changed')
        require(int(row['candidate_recovered_f1_gt_0_5']) == recovered, f'{key} v31 recovery changed')

    require(order_sha(h['local_order']) == HDB_LOCAL_ORDER_SHA256, 'captured HDB local order changed')
    require(order_sha(h['fused_order']) == HDB_FUSED_ORDER_SHA256, 'captured HDB fused order changed')
    require(parent['order_diagnostics']['hdbscan']['local_diversity_order_sha256'] == HDB_LOCAL_ORDER_SHA256, 'parent HDB local hash changed')
    require(parent['order_diagnostics']['hdbscan']['fused_order_sha256'] == HDB_FUSED_ORDER_SHA256, 'parent HDB fused hash changed')
    return parent, h


def capture_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    parent, h = exact_parent_capture(sugar_root, hdbscan_root, truth_root, ranker_source, output / 'parent_v31')

    meta = json.loads((hdbscan_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((hdbscan_root / 'family_memberships.json').read_text())
    ids = list(map(str, meta['family_ids']))
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, '#950 HDB payload not pretruth')
    require(meta['feature_dimension'] == 71 and len(ids) == HDB_N and len(fp['families']) == HDB_N, '#950 HDB universe changed')
    require([str(f['family_id']) for f in fp['families']] == ids, '#950 HDB membership order changed')
    require(meta['target_information_access'] is False, '#950 target access changed')
    require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, '#950 protected-survey access changed')
    manifest_v19 = list(map(str, meta['v19_order']))
    require(h['v19_order'] == manifest_v19, 'captured v19 order differs from immutable #950 manifest')
    require(set(h['local_order']) == set(ids) == set(manifest_v19), 'captured HDB fusion universe changed')

    local_rank = {fid: i + 1 for i, fid in enumerate(h['local_order'])}
    v19_rank = {fid: i + 1 for i, fid in enumerate(manifest_v19)}
    rows = []
    for fid in ids:
        lr = int(local_rank[fid])
        vr = int(v19_rank[fid])
        lp = float((lr - 1) / (HDB_N - 1))
        vp = float((vr - 1) / (HDB_N - 1))
        bottleneck = float(max(lp, vp))
        require(0.0 <= lp <= 1.0 and 0.0 <= vp <= 1.0 and 0.0 <= bottleneck <= 1.0, 'invalid normalized fusion rank')
        rows.append({
            'family_id': fid,
            'local_rank': lr,
            'local_rank_percentile': lp,
            'v19_rank': vr,
            'v19_rank_percentile': vp,
            'consensus_bottleneck': bottleneck,
        })
    rows.sort(key=lambda x: str(x['family_id']))

    parent_controls = []
    pmap = {(str(x['comparator']), int(x['year'])): x for x in parent['panels']}
    for route, year in (('sugar', 2013), ('sugar', 2014), ('hdbscan', 2013), ('hdbscan', 2014)):
        row = pmap[(route, year)]
        parent_controls.append({
            'comparator': route,
            'year': year,
            'macro_f1': float(row['candidate_macro_f1']),
            'recovered_f1_gt_0_5': int(row['candidate_recovered_f1_gt_0_5']),
        })

    vector: dict[str, Any] = {
        'verdict': 'PASS_V51_V31_CONSENSUS_BOTTLENECK_VECTOR_CAPTURE',
        'scientific_role': 'EXACT_V31_FUSION_INPUT_RANKS_CAPTURED_BEFORE_DIAGNOSTIC_RECOVERABILITY_ATTACHMENT',
        'parent': 'v31 local-geometry-margin OOF',
        'parent_source_blob': PARENT_SOURCE_BLOB,
        'ranker_source_sha256': RANKER_SOURCE_SHA256,
        'family_count': HDB_N,
        'statistic': 'consensus_bottleneck = max((local_rank-1)/(229-1),(v19_rank-1)/(229-1)); lower means neither exact-v31 fusion input ranks the family poorly',
        'local_order_sha256': order_sha(h['local_order']),
        'v19_order_sha256': order_sha(manifest_v19),
        'fused_order_sha256': order_sha(h['fused_order']),
        'parent_controls': parent_controls,
        'families': rows,
        'exact_v31_exposed_oof_parent_reproduced': True,
        'diagnostic_recoverability_attached': False,
        'annual_own_family_f1_attached': False,
        'literature_budget_used_in_statistic': False,
        'boundary_identity_used': False,
        'component_quality_topology_signal_used': False,
        'new_candidate_order_evaluated': False,
        'selector_evaluated': False,
        'successor_selected': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
    }
    vector['canonical_sha256_without_self_field'] = canonical_sha(vector)
    out = output / 'V51_V31_CONSENSUS_BOTTLENECK_VECTOR.json'
    out.write_text(json.dumps(vector, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': vector['verdict'],
        'family_count': HDB_N,
        'local_order_sha256': vector['local_order_sha256'],
        'v19_order_sha256': vector['v19_order_sha256'],
        'fused_order_sha256': vector['fused_order_sha256'],
        'canonical_sha256_without_self_field': vector['canonical_sha256_without_self_field'],
        'file_sha256': sha(out),
    }, indent=2, sort_keys=True))
    return 0


def diagnose_mode(vector_file: Path, hdb_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    vector = json.loads(vector_file.read_text())
    require(vector['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_VECTOR_CAPTURE', 'v51 vector verdict changed')
    require(vector['scientific_role'] == 'EXACT_V31_FUSION_INPUT_RANKS_CAPTURED_BEFORE_DIAGNOSTIC_RECOVERABILITY_ATTACHMENT', 'v51 vector role changed')
    require(vector['parent_source_blob'] == PARENT_SOURCE_BLOB and vector['ranker_source_sha256'] == RANKER_SOURCE_SHA256, 'v51 parent source changed')
    require(int(vector['family_count']) == HDB_N and len(vector['families']) == HDB_N, 'v51 HDB population changed')
    require(vector['local_order_sha256'] == HDB_LOCAL_ORDER_SHA256 and vector['fused_order_sha256'] == HDB_FUSED_ORDER_SHA256, 'v51 captured v31 order changed')
    require(vector['diagnostic_recoverability_attached'] is False and vector['annual_own_family_f1_attached'] is False, 'v51 vector already contains diagnostic outcome')
    require(vector['literature_budget_used_in_statistic'] is False and vector['boundary_identity_used'] is False and vector['component_quality_topology_signal_used'] is False, 'v51 statistic contaminated by prior rescue signals')
    expected_canonical = str(vector['canonical_sha256_without_self_field'])
    check = dict(vector)
    del check['canonical_sha256_without_self_field']
    require(canonical_sha(check) == expected_canonical, 'v51 vector canonical identity changed')

    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((hdb_root / 'family_memberships.json').read_text())
    ids = list(map(str, meta['family_ids']))
    fams = list(fp['families'])
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, '#950 HDB payload not pretruth')
    require(meta['feature_dimension'] == 71 and len(ids) == HDB_N and len(fams) == HDB_N, '#950 HDB universe changed')
    require([str(f['family_id']) for f in fams] == ids, '#950 HDB membership order changed')
    fam_by_id = {str(f['family_id']): f for f in fams}
    vector_rows = list(vector['families'])
    vector_ids = [str(r['family_id']) for r in vector_rows]
    require(len(set(vector_ids)) == HDB_N and set(vector_ids) == set(ids), 'v51 vector identities changed')

    by = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v31.v22.eligible_from_year_truth(by)
    hidden: dict[str, Any] = {}
    hidden.update(by[2013])
    hidden.update(by[2014])

    diag_rows = []
    for r in vector_rows:
        fid = str(r['family_id'])
        bottleneck = float(r['consensus_bottleneck'])
        require(np.isfinite(bottleneck) and 0.0 <= bottleneck <= 1.0, 'invalid frozen consensus bottleneck')
        expected = max(float(r['local_rank_percentile']), float(r['v19_rank_percentile']))
        require(abs(bottleneck - expected) < 1e-15, 'consensus-bottleneck arithmetic changed')
        fam = fam_by_id[fid]
        t = v31.v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v31.v24.annual_f1_for_fixed_label(fam, str(label), by))
        else:
            f13 = f14 = 0.0
        diag_rows.append({
            'family_id': fid,
            'consensus_bottleneck': bottleneck,
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
        })

    annual: dict[str, Any] = {}
    directions: list[bool] = []
    for year in (2013, 2014):
        rk = f'recoverable_{year}'
        rec = [x for x in diag_rows if bool(x[rk])]
        non = [x for x in diag_rows if not bool(x[rk])]
        require(rec and non, f'{year} empty consensus-bottleneck class')
        rec_s = summarize([float(x['consensus_bottleneck']) for x in rec])
        non_s = summarize([float(x['consensus_bottleneck']) for x in non])
        direction = bool(rec_s['median_consensus_bottleneck'] < non_s['median_consensus_bottleneck'])
        directions.append(direction)
        annual[str(year)] = {
            'recoverable': rec_s,
            'nonrecoverable': non_s,
            'median_difference_recoverable_minus_nonrecoverable': float(rec_s['median_consensus_bottleneck'] - non_s['median_consensus_bottleneck']),
            'direction_pass': direction,
        }

    passed = bool(all(directions))
    result: dict[str, Any] = {
        'verdict': 'PASS_V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC' if passed else 'FAIL_V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC',
        'scientific_role': 'POST_V50_V31_FUSION_MECHANISM_DIAGNOSTIC_ONLY_NO_NEW_ORDER_OR_PANEL_EVALUATED',
        'question': 'Across all 229 fixed HDB families, is the median worst normalized rank across exact-v31 local and v19 fusion inputs lower for recoverable than nonrecoverable families in both exposed years?',
        'parent': 'v31 local-geometry-margin OOF',
        'parent_source_blob': PARENT_SOURCE_BLOB,
        'ranker_source_sha256': RANKER_SOURCE_SHA256,
        'vector_file_sha256': sha(vector_file),
        'vector_canonical_sha256': expected_canonical,
        'family_count': HDB_N,
        'statistic': vector['statistic'],
        'recovery_f1_threshold': RECOVERY,
        'annual_diagnostics': annual,
        'direction_supported_both_years': passed,
        'new_candidate_order_evaluated': False,
        'literature_panel_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'minimax_successor_evaluated': False,
        'representative_group_aggregation_evaluated': False,
        'auc_evaluated': False,
        'correlation_evaluated': False,
        'regression_evaluated': False,
        'p_value_evaluated': False,
        'alternate_rank_statistic_search': False,
        'rank_disagreement_test': False,
        'threshold_search': False,
        'quantile_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'literature_budget_analysis': False,
        'fusion_weight_search': False,
        'rank_algebra_search': False,
        'pareto_order_evaluated': False,
        'component_quality_topology_rescue': False,
        'boundary_identity_used': False,
        'oracle_identity_used_for_ranking': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'metric_search': False,
        'scaling_search': False,
        'diversity_search': False,
        'source_quota_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = output / 'V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    c = sub.add_parser('capture')
    c.add_argument('--sugar-root', type=Path, required=True)
    c.add_argument('--hdbscan-root', type=Path, required=True)
    c.add_argument('--truth-root', type=Path, required=True)
    c.add_argument('--ranker-source', type=Path, required=True)
    c.add_argument('--output', type=Path, required=True)
    d = sub.add_parser('diagnose')
    d.add_argument('--vector-file', type=Path, required=True)
    d.add_argument('--hdb-root', type=Path, required=True)
    d.add_argument('--truth-root', type=Path, required=True)
    d.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'capture':
        return capture_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.output)
    return diagnose_mode(a.vector_file, a.hdb_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

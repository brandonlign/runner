#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

HDB_N = 229
RECOVERY = 0.5
V51_VECTOR_SHA256 = '5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc'
V51_VECTOR_CANONICAL = '0e13b3f9e6b791a13a3e90d853f8704573b1264dffcb67236e6423491ad70020'
V51_RESULT_SHA256 = 'fef1d2c5bb83748de5c5511615915e76ce6fcd0801afbddb0e01bab09b9ab76d'
LOCAL_ORDER_SHA256 = '9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595'
V19_ORDER_SHA256 = 'e1e82ad70fb8c575ee7ee269906668931f07cbe3375c15ab84b0717b1f2c85dc'
V31_FUSED_SHA256 = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256((json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()


def summarize(values: list[int]) -> dict[str, Any]:
    require(values, 'empty Pareto-dominator class')
    x = np.asarray(values, dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite Pareto-dominator count')
    return {
        'count': int(len(x)),
        'median_pareto_dominator_count': float(np.median(x)),
        'q25_pareto_dominator_count': float(np.percentile(x, 25.0, method='linear')),
        'q75_pareto_dominator_count': float(np.percentile(x, 75.0, method='linear')),
        'min_pareto_dominator_count': int(np.min(x)),
        'max_pareto_dominator_count': int(np.max(x)),
    }


def load_v51(vector_file: Path, result_file: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    require(sha(vector_file) == V51_VECTOR_SHA256, 'v51 vector identity changed')
    require(sha(result_file) == V51_RESULT_SHA256, 'v51 diagnostic result identity changed')
    v = json.loads(vector_file.read_text())
    r = json.loads(result_file.read_text())
    require(v['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_VECTOR_CAPTURE', 'v51 vector verdict changed')
    require(v['scientific_role'] == 'EXACT_V31_FUSION_INPUT_RANKS_CAPTURED_BEFORE_DIAGNOSTIC_RECOVERABILITY_ATTACHMENT', 'v51 vector role changed')
    require(v['canonical_sha256_without_self_field'] == V51_VECTOR_CANONICAL, 'v51 vector canonical identity changed')
    check = dict(v)
    del check['canonical_sha256_without_self_field']
    require(canonical_sha(check) == V51_VECTOR_CANONICAL, 'v51 vector canonical payload changed')
    require(int(v['family_count']) == HDB_N and len(v['families']) == HDB_N, 'v51 HDB universe changed')
    require(v['local_order_sha256'] == LOCAL_ORDER_SHA256, 'v51 local order changed')
    require(v['v19_order_sha256'] == V19_ORDER_SHA256, 'v51 v19 order changed')
    require(v['fused_order_sha256'] == V31_FUSED_SHA256, 'v51 fused order changed')
    require(v['diagnostic_recoverability_attached'] is False and v['annual_own_family_f1_attached'] is False, 'v51 vector contains diagnostic outcomes')
    require(v['literature_budget_used_in_statistic'] is False and v['component_quality_topology_signal_used'] is False, 'v51 vector contaminated by rescue signals')
    require(v['target_information_access'] is False and v['target_region_events_accessed'] is False, 'v51 target firewall changed')
    require(v['maarsy_scientific_access'] is False and v['dms_scientific_access'] is False, 'v51 survey firewall changed')
    require(v['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and v['blind_exclusion'] == [20.0, 55.0], 'v51 role/firewall changed')

    require(r['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_DIAGNOSTIC', 'v51 diagnostic did not pass')
    require(r['direction_supported_both_years'] is True, 'v51 direction support changed')
    require(r['vector_file_sha256'] == V51_VECTOR_SHA256 and r['vector_canonical_sha256'] == V51_VECTOR_CANONICAL, 'v51 result provenance changed')
    require(r['new_candidate_order_evaluated'] is False and r['minimax_successor_evaluated'] is False and r['successor_selected'] is False, 'v51 evaluated a successor')
    require(r['literature_panel_evaluated'] is False and r['rank_algebra_search'] is False and r['fusion_weight_search'] is False, 'v51 performed forbidden rank/panel search')
    require(r['target_information_access'] is False and r['target_region_events_accessed'] is False, 'v51 result target firewall changed')
    require(r['maarsy_scientific_access'] is False and r['dms_scientific_access'] is False, 'v51 result survey firewall changed')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and r['blind_exclusion'] == [20.0, 55.0], 'v51 result role/firewall changed')
    return v, r


def freeze_mode(vector_file: Path, result_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    v, _ = load_v51(vector_file, result_file)
    rows = list(v['families'])
    ids = [str(x['family_id']) for x in rows]
    require(len(set(ids)) == HDB_N, 'duplicate HDB family identity')
    local = sorted(int(x['local_rank']) for x in rows)
    v19 = sorted(int(x['v19_rank']) for x in rows)
    require(local == list(range(1, HDB_N + 1)), 'local ranks are not a complete permutation')
    require(v19 == list(range(1, HDB_N + 1)), 'v19 ranks are not a complete permutation')

    pts = [(str(x['family_id']), int(x['local_rank']), int(x['v19_rank'])) for x in rows]
    out_rows: list[dict[str, Any]] = []
    for fid, rl, rv in pts:
        count = 0
        for other, ol, ov in pts:
            if other == fid:
                continue
            if ol <= rl and ov <= rv and (ol < rl or ov < rv):
                count += 1
        require(0 <= count <= HDB_N - 1, 'invalid Pareto-dominator count')
        out_rows.append({
            'family_id': fid,
            'local_rank': rl,
            'v19_rank': rv,
            'pareto_dominator_count': int(count),
        })
    out_rows.sort(key=lambda x: str(x['family_id']))
    counts = [int(x['pareto_dominator_count']) for x in out_rows]
    require(min(counts) == 0, 'Pareto-dominator minimum changed')
    require(max(counts) == 188, 'Pareto-dominator maximum changed')
    require(len(set(counts)) == 133, 'Pareto-dominator distinct-count identity changed')

    payload: dict[str, Any] = {
        'verdict': 'PASS_V53_LOCAL_V19_PARETO_DOMINATOR_VECTOR_FREEZE',
        'scientific_role': 'COMPLETE_229_FAMILY_LOCAL_V19_PARETO_DOMINATOR_VECTOR_FROZEN_BEFORE_V53_RECOVERABILITY_ATTACHMENT',
        'source_v51_run': 31493423814,
        'source_v51_artifact': 9101972590,
        'source_v51_artifact_digest': 'sha256:56258a0be52d83c0d6dbfcffdb9fd9a2c6b73587ba8d92d7bdccdef9729868c9',
        'source_v51_vector_sha256': V51_VECTOR_SHA256,
        'source_v51_vector_canonical_sha256': V51_VECTOR_CANONICAL,
        'source_v51_result_sha256': V51_RESULT_SHA256,
        'family_count': HDB_N,
        'statistic': 'pareto_dominator_count = number of other families no worse in both exact-v31 local and v19 integer ranks and strictly better in at least one',
        'local_order_sha256': LOCAL_ORDER_SHA256,
        'v19_order_sha256': V19_ORDER_SHA256,
        'v31_fused_order_sha256': V31_FUSED_SHA256,
        'min_pareto_dominator_count': 0,
        'max_pareto_dominator_count': 188,
        'distinct_pareto_dominator_count_values': 133,
        'families': out_rows,
        'current_v53_recoverability_attached': False,
        'annual_own_family_f1_attached': False,
        'literature_budget_used': False,
        'boundary_identity_used': False,
        'v52_substituted_identity_used': False,
        'component_quality_topology_signal_used': False,
        'new_candidate_order_evaluated': False,
        'pareto_frontier_order_evaluated': False,
        'pareto_layer_order_evaluated': False,
        'selector_evaluated': False,
        'successor_selected': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'blind_exclusion': [20.0, 55.0],
    }
    payload['canonical_sha256_without_self_field'] = canonical_sha(payload)
    out = output / 'V53_LOCAL_V19_PARETO_DOMINATOR_VECTOR.json'
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': payload['verdict'],
        'family_count': HDB_N,
        'min_pareto_dominator_count': 0,
        'max_pareto_dominator_count': 188,
        'distinct_pareto_dominator_count_values': 133,
        'canonical_sha256_without_self_field': payload['canonical_sha256_without_self_field'],
        'file_sha256': sha(out),
    }, indent=2, sort_keys=True))
    return 0


def diagnose_mode(vector_file: Path, hdb_root: Path, truth_root: Path, output: Path) -> int:
    from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
    from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24

    output.mkdir(parents=True, exist_ok=True)
    vector = json.loads(vector_file.read_text())
    require(vector['verdict'] == 'PASS_V53_LOCAL_V19_PARETO_DOMINATOR_VECTOR_FREEZE', 'v53 vector verdict changed')
    require(vector['scientific_role'] == 'COMPLETE_229_FAMILY_LOCAL_V19_PARETO_DOMINATOR_VECTOR_FROZEN_BEFORE_V53_RECOVERABILITY_ATTACHMENT', 'v53 vector role changed')
    require(int(vector['family_count']) == HDB_N and len(vector['families']) == HDB_N, 'v53 population changed')
    require(vector['local_order_sha256'] == LOCAL_ORDER_SHA256 and vector['v19_order_sha256'] == V19_ORDER_SHA256 and vector['v31_fused_order_sha256'] == V31_FUSED_SHA256, 'v53 source-rank identity changed')
    require(vector['current_v53_recoverability_attached'] is False and vector['annual_own_family_f1_attached'] is False, 'v53 vector already contains outcomes')
    require(vector['literature_budget_used'] is False and vector['boundary_identity_used'] is False and vector['v52_substituted_identity_used'] is False, 'v53 vector contaminated by boundary information')
    require(vector['component_quality_topology_signal_used'] is False, 'v53 vector contaminated by rejected signal')
    expected_canonical = str(vector['canonical_sha256_without_self_field'])
    check = dict(vector)
    del check['canonical_sha256_without_self_field']
    require(canonical_sha(check) == expected_canonical, 'v53 vector canonical identity changed')

    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((hdb_root / 'family_memberships.json').read_text())
    ids = list(map(str, meta['family_ids']))
    fams = list(fp['families'])
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, '#950 HDB payload not pretruth')
    require(meta['feature_dimension'] == 71 and len(ids) == HDB_N and len(fams) == HDB_N, '#950 HDB universe changed')
    require([str(f['family_id']) for f in fams] == ids, '#950 HDB membership order changed')
    require(meta['target_information_access'] is False, '#950 target access changed')
    require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, '#950 protected-survey access changed')
    fam_by_id = {str(f['family_id']): f for f in fams}
    vector_rows = list(vector['families'])
    vector_ids = [str(r['family_id']) for r in vector_rows]
    require(len(set(vector_ids)) == HDB_N and set(vector_ids) == set(ids), 'v53 vector identities differ from #950')

    by = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v22.eligible_from_year_truth(by)
    hidden: dict[str, Any] = {}
    hidden.update(by[2013])
    hidden.update(by[2014])

    diag_rows = []
    for r in vector_rows:
        fid = str(r['family_id'])
        dc = int(r['pareto_dominator_count'])
        require(0 <= dc <= HDB_N - 1, 'invalid frozen Pareto-dominator count')
        fam = fam_by_id[fid]
        t = v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v24.annual_f1_for_fixed_label(fam, str(label), by))
        else:
            f13 = f14 = 0.0
        diag_rows.append({
            'family_id': fid,
            'pareto_dominator_count': dc,
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
        require(rec and non, f'{year} empty Pareto-dominator class')
        rec_s = summarize([int(x['pareto_dominator_count']) for x in rec])
        non_s = summarize([int(x['pareto_dominator_count']) for x in non])
        direction = bool(rec_s['median_pareto_dominator_count'] < non_s['median_pareto_dominator_count'])
        directions.append(direction)
        annual[str(year)] = {
            'recoverable': rec_s,
            'nonrecoverable': non_s,
            'median_difference_recoverable_minus_nonrecoverable': float(rec_s['median_pareto_dominator_count'] - non_s['median_pareto_dominator_count']),
            'direction_pass': direction,
        }

    passed = bool(all(directions))
    result: dict[str, Any] = {
        'verdict': 'PASS_V53_LOCAL_V19_PARETO_DOMINATOR_DIAGNOSTIC' if passed else 'FAIL_V53_LOCAL_V19_PARETO_DOMINATOR_DIAGNOSTIC',
        'scientific_role': 'POST_V52_LOCAL_V19_PARETO_DOMINATOR_MECHANISM_DIAGNOSTIC_ONLY_NO_SUCCESSOR_ORDER_OR_PANEL_EVALUATED',
        'question': 'Across all 229 fixed HDB families, is median two-rank Pareto-dominator count lower for annual-recoverable than nonrecoverable families in both exposed years?',
        'source_v51_run': 31493423814,
        'source_v51_artifact': 9101972590,
        'source_v51_vector_sha256': V51_VECTOR_SHA256,
        'source_v51_result_sha256': V51_RESULT_SHA256,
        'vector_file_sha256': sha(vector_file),
        'vector_canonical_sha256': expected_canonical,
        'family_count': HDB_N,
        'recovery_f1_threshold': RECOVERY,
        'statistic': vector['statistic'],
        'annual_diagnostics': annual,
        'direction_supported_both_years': passed,
        'new_candidate_order_evaluated': False,
        'literature_panel_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'dominator_count_successor_evaluated': False,
        'pareto_frontier_test_evaluated': False,
        'pareto_layer_test_evaluated': False,
        'representative_group_aggregation_evaluated': False,
        'auc_evaluated': False,
        'correlation_evaluated': False,
        'regression_evaluated': False,
        'p_value_evaluated': False,
        'alternate_dominance_convention_evaluated': False,
        'threshold_search': False,
        'quantile_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'literature_budget_analysis': False,
        'fusion_weight_search': False,
        'rank_algebra_search': False,
        'component_quality_topology_rescue': False,
        'v52_identity_rescue': False,
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
    out = output / 'V53_LOCAL_V19_PARETO_DOMINATOR_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    f = sub.add_parser('freeze')
    f.add_argument('--vector-file', type=Path, required=True)
    f.add_argument('--result-file', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    d = sub.add_parser('diagnose')
    d.add_argument('--vector-file', type=Path, required=True)
    d.add_argument('--hdb-root', type=Path, required=True)
    d.add_argument('--truth-root', type=Path, required=True)
    d.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'freeze':
        return freeze_mode(a.vector_file, a.result_file, a.output)
    return diagnose_mode(a.vector_file, a.hdb_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

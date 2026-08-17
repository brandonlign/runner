#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

SOURCE_RUN = 31454067856
SOURCE_ARTIFACT = 9087373195
SOURCE_DIGEST = 'sha256:361e6113110dcc58761a458fc842f8c3e613f79d0e13a85c593bad297cd49d7a'
SOURCE_COMMIT = 'b0f9efdafb6c4662fc8ac84bd6201bc54cd3191e'
SUGAR_N = 267
HDB_N = 229
EXPECTED_V31 = {
    ('sugar', 2013): (0.2719801488280529, 16, 34),
    ('sugar', 2014): (0.31529041952487225, 17, 46),
    ('hdbscan', 2013): (0.14888037368183737, 9, 11),
    ('hdbscan', 2014): (0.15198123772301594, 9, 9),
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def finite(x: float) -> bool:
    return bool(np.isfinite(float(x)))


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    linked = [r for r in rows if r['crossroute_rank_gap'] is not None]
    if not linked:
        return {
            'groups': len(rows),
            'groups_with_frozen_link': 0,
            'median_crossroute_rank_gap': None,
            'mean_crossroute_rank_gap': None,
            'min_crossroute_rank_gap': None,
            'max_crossroute_rank_gap': None,
            'q25_crossroute_rank_gap': None,
            'q75_crossroute_rank_gap': None,
            'strictly_positive_gap_count': 0,
            'strictly_positive_gap_fraction': None,
            'median_hdb_percentile': None,
            'median_sugar_percentile': None,
        }
    gaps = np.asarray([float(r['crossroute_rank_gap']) for r in linked], dtype=float)
    ph = np.asarray([float(r['p_hdb']) for r in linked], dtype=float)
    ps = np.asarray([float(r['p_sugar']) for r in linked], dtype=float)
    require(np.all(np.isfinite(gaps)) and np.all(np.isfinite(ph)) and np.all(np.isfinite(ps)), 'nonfinite derived rank disagreement')
    q25, q75 = np.percentile(gaps, [25.0, 75.0], method='linear')
    positive = int(np.sum(gaps > 0.0))
    return {
        'groups': len(rows),
        'groups_with_frozen_link': len(linked),
        'median_crossroute_rank_gap': float(np.median(gaps)),
        'mean_crossroute_rank_gap': float(np.mean(gaps)),
        'min_crossroute_rank_gap': float(np.min(gaps)),
        'max_crossroute_rank_gap': float(np.max(gaps)),
        'q25_crossroute_rank_gap': float(q25),
        'q75_crossroute_rank_gap': float(q75),
        'strictly_positive_gap_count': positive,
        'strictly_positive_gap_fraction': float(positive / len(linked)),
        'median_hdb_percentile': float(np.median(ph)),
        'median_sugar_percentile': float(np.median(ps)),
    }


def validate_source(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    diag_path = root / 'diag' / 'V31_CROSSROUTE_RADIUS1_CORROBORATION_DIAGNOSTIC.json'
    graph_path = root / 'pretruth' / 'CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY.json'
    require(diag_path.is_file(), f'missing source diagnostic: {diag_path}')
    require(graph_path.is_file(), f'missing source pretruth graph: {graph_path}')
    d = json.loads(diag_path.read_text())
    g = json.loads(graph_path.read_text())

    require(d['verdict'] == 'PASS_V31_CROSSROUTE_RADIUS1_CORROBORATION_DIAGNOSTIC', 'source diagnostic verdict changed')
    require(d['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CROSSROUTE_RANK_EVALUATED', 'source diagnostic role changed')
    require(d['crossroute_score_or_rerank_evaluated'] is False and d['successor_selected'] is False, 'source unexpectedly evaluated a rank/successor')
    require(d['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'source SonotaCo role changed')
    for k in ('maarsy_scientific_access', 'dms_scientific_access', 'target_information_access', 'target_region_events_accessed'):
        require(d[k] is False, f'source firewall violation: {k}')
    require(d['blind_exclusion'] == [20.0, 55.0], 'source blind exclusion changed')

    require(g['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY', 'source graph verdict changed')
    require(g['scientific_role'] == 'PRETRUTH_CROSS_ROUTE_GRAPH_IDENTITY_ONLY', 'source graph role changed')
    require(g['truth_accessed'] is False and float(g['radius']) == 1.0, 'source graph is not frozen pretruth radius-1')
    require(g['radius_search'] is False and g['metric_search'] is False, 'source graph search flags changed')
    for k in ('maarsy_scientific_access', 'dms_scientific_access', 'target_information_access', 'target_region_events_accessed'):
        require(g[k] is False, f'source graph firewall violation: {k}')
    require(g['blind_exclusion'] == [20.0, 55.0], 'source graph blind exclusion changed')
    require(int(g['edge_count']) == 2334, 'source cross-route graph edge count changed')
    require(len(g['sugar_family_ids']) == SUGAR_N and len(g['hdbscan_family_ids']) == HDB_N, 'source route family counts changed')

    got = {}
    for r in d['v31_reproduction']:
        key = (str(r['comparator']), int(r['year']))
        got[key] = (float(r['macro_f1']), int(r['recovered_f1_gt_0_5']), int(r['candidate_used']))
    require(set(got) == set(EXPECTED_V31), 'source v31 panel set changed')
    for key, exp in EXPECTED_V31.items():
        cur = got[key]
        require(abs(cur[0] - exp[0]) < 1e-12 and cur[1] == exp[1] and cur[2] == exp[2], f'source v31 reproduction changed: {key}')

    require(set(d['annual_diagnostics']) == {'2013', '2014'}, 'source annual diagnostics changed')
    for year, hb, sb in ((2013, 11, 34), (2014, 9, 46)):
        a = d['annual_diagnostics'][str(year)]
        require(int(a['hdb_budget']) == hb and int(a['sugar_budget']) == sb, f'source budget changed {year}')
        require(int(a['annual_recoverable_hdb_groups']) == 18, f'source recoverable HDB group count changed {year}')
        require(int(a['surfaced_hdb_groups']) == 9 and int(a['missed_hdb_groups']) == 9, f'source surfaced/missed split changed {year}')
        require(len(a['groups']) == 18, f'source group row count changed {year}')

    commit_file = root / 'execution_commit.txt'
    require(commit_file.is_file() and commit_file.read_text().strip() == SOURCE_COMMIT, 'source execution commit changed')
    return d, g


def derive_row(src: dict[str, Any]) -> dict[str, Any]:
    row = dict(src)
    sr = src.get('best_sugar_neighbor_rank')
    hr = src.get('linked_hdb_rank')
    require((sr is None) == (hr is None), 'partial frozen cross-route rank pair')
    if sr is None:
        row['p_hdb'] = None
        row['p_sugar'] = None
        row['crossroute_rank_gap'] = None
        return row
    sr = int(sr)
    hr = int(hr)
    require(1 <= sr <= SUGAR_N and 1 <= hr <= HDB_N, 'frozen cross-route rank outside route universe')
    ph = float((hr - 1) / (HDB_N - 1))
    ps = float((sr - 1) / (SUGAR_N - 1))
    gap = float(ph - ps)
    require(finite(ph) and finite(ps) and finite(gap), 'nonfinite rank disagreement')
    row['p_hdb'] = ph
    row['p_sugar'] = ps
    row['crossroute_rank_gap'] = gap
    return row


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--input-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    source, graph = validate_source(a.input_root)
    annual_out = {}
    directional_years = []
    for year in (2013, 2014):
        src = source['annual_diagnostics'][str(year)]
        rows = [derive_row(r) for r in src['groups']]
        surfaced = [r for r in rows if bool(r['surfaced_hdb'])]
        missed = [r for r in rows if not bool(r['surfaced_hdb'])]
        require(len(surfaced) == 9 and len(missed) == 9, f'derived surfaced/missed split changed {year}')
        ss = summarize(surfaced)
        ms = summarize(missed)
        require(ss['median_crossroute_rank_gap'] is not None and ms['median_crossroute_rank_gap'] is not None, f'missing median rank gap {year}')
        delta = float(ms['median_crossroute_rank_gap'] - ss['median_crossroute_rank_gap'])
        # The protocol's direction is descriptive, not a selected effect-size gate:
        # missed groups must have both a positive median gap and a larger median gap than surfaced groups.
        direction = bool(ms['median_crossroute_rank_gap'] > 0.0 and delta > 0.0)
        directional_years.append(direction)
        annual_out[str(year)] = {
            'hdb_budget': int(src['hdb_budget']),
            'sugar_budget': int(src['sugar_budget']),
            'annual_recoverable_hdb_groups': 18,
            'surfaced_hdb_groups': 9,
            'missed_hdb_groups': 9,
            'surfaced_summary': ss,
            'missed_summary': ms,
            'missed_minus_surfaced_median_gap': delta,
            'positive_rank_disagreement_direction': direction,
            'groups': rows,
        }

    both_years = bool(all(directional_years))
    result = {
        'verdict': 'PASS_V31_CROSSROUTE_RANK_DISAGREEMENT_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CROSSROUTE_RANK_TRANSFER_EVALUATED',
        'source_run_id': SOURCE_RUN,
        'source_artifact_id': SOURCE_ARTIFACT,
        'source_artifact_digest': SOURCE_DIGEST,
        'source_execution_commit': SOURCE_COMMIT,
        'source_diagnostic_verdict': source['verdict'],
        'source_pretruth_graph_verdict': graph['verdict'],
        'sugar_family_count': SUGAR_N,
        'hdbscan_family_count': HDB_N,
        'rank_gap_definition': '((linked_hdb_rank-1)/228)-((best_sugar_neighbor_rank-1)/266)',
        'positive_gap_meaning': 'the frozen radius-1-corresponding physical structure is ranked better by Sugar than by HDB',
        'percentile_method': 'zero-based rank percentile within each fixed route universe',
        'quartile_method': "numpy.percentile method='linear'",
        'annual_diagnostics': annual_out,
        'positive_direction_in_both_years': both_years,
        'interpretation_boundary': 'direction supported only when missed median gap is >0 and exceeds surfaced median gap in both years; no effect-size threshold selected',
        'new_rank_or_score_evaluated': False,
        'crossroute_rank_transfer_evaluated': False,
        'successor_selected': False,
        'absolute_gap_search': False,
        'rank_ratio_search': False,
        'log_transform_search': False,
        'overlap_weight_search': False,
        'distance_weight_search': False,
        'clipping_search': False,
        'threshold_search': False,
        'coefficient_search': False,
        'budget_normalization_search': False,
        'alternate_disagreement_statistic_search': False,
        'fusion_search': False,
        'selector_search': False,
        'route_specific_rule_search': False,
        'post_result_second_search': False,
        'oracle_identity_hardcoded': False,
        'graph_changed': False,
        'radius_changed': False,
        'metric_changed': False,
        'feature_changed': False,
        'membership_changed': False,
        'candidate_generation_changed': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V31_CROSSROUTE_RANK_DISAGREEMENT_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'positive_direction_in_both_years': both_years,
        'annual': {
            y: {
                'surfaced_summary': x['surfaced_summary'],
                'missed_summary': x['missed_summary'],
                'missed_minus_surfaced_median_gap': x['missed_minus_surfaced_median_gap'],
                'positive_rank_disagreement_direction': x['positive_rank_disagreement_direction'],
            }
            for y, x in annual_out.items()
        },
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

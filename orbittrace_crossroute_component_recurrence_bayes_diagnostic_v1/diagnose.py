#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.special import gammaln
from scipy.stats import mannwhitneyu

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24

FEATURE_DIM = 71
RECOVERY = 0.5
RADIUS = 1.0
GRAPH_SHA256 = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA256 = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def wrap180(x: float) -> float:
    return float((float(x) + 180.0) % 360.0 - 180.0)


def annual_distance(a: np.ndarray, b: np.ndarray) -> float:
    d_sol = wrap180(float(a[0]) - float(b[0])) / 4.0
    d_lon = wrap180(float(a[1]) - float(b[1])) * math.cos(math.radians(0.5 * (float(a[2]) + float(b[2])))) / 2.0
    d_lat = (float(a[2]) - float(b[2])) / 2.0
    d_vg = (math.exp(float(a[3])) - math.exp(float(b[3]))) / 2.0
    return float(math.sqrt(d_sol*d_sol + d_lon*d_lon + d_lat*d_lat + d_vg*d_vg))


def load_pretruth(root: Path) -> tuple[dict[str, Any], np.ndarray, list[str]]:
    meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((root / 'family_memberships.json').read_text())
    ids = list(map(str, meta['family_ids']))
    X = np.load(root / 'features.npy', allow_pickle=False)
    C = np.load(root / 'centroids.npy', allow_pickle=False)
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and meta['feature_dimension'] == FEATURE_DIM, 'invalid immutable pretruth payload')
    require(X.shape == (len(ids), FEATURE_DIM) and C.shape == (len(ids), 8), 'pretruth array shape changed')
    require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], 'pretruth array identity changed')
    require([str(f['family_id']) for f in fp['families']] == ids, 'family order changed')
    return {'meta': meta, 'fp': fp, 'ids': ids}, C, ids


class DSU:
    def __init__(self, tokens: list[str]):
        self.parent = {t: t for t in tokens}

    def find(self, x: str) -> str:
        p = self.parent[x]
        if p != x:
            self.parent[x] = self.find(p)
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if ra < rb:
            self.parent[rb] = ra
        else:
            self.parent[ra] = rb


def component_rows_from_graph(graph: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    sids = list(map(str, graph['sugar_family_ids']))
    hids = list(map(str, graph['hdbscan_family_ids']))
    stokens = [f'sugar/{x}' for x in sids]
    htokens = [f'hdbscan/{x}' for x in hids]
    tokens = stokens + htokens
    dsu = DSU(tokens)
    for hi, si, _d in graph['edges']:
        dsu.union(htokens[int(hi)], stokens[int(si)])
    raw: dict[str, list[str]] = defaultdict(list)
    for t in tokens:
        raw[dsu.find(t)].append(t)
    rows = []
    token_to_component = {}
    for members in sorted((sorted(v) for v in raw.values()), key=lambda xs: xs[0]):
        cid = members[0]
        for t in members:
            token_to_component[t] = cid
        sugar_members = [x.split('/', 1)[1] for x in members if x.startswith('sugar/')]
        hdb_members = [x.split('/', 1)[1] for x in members if x.startswith('hdbscan/')]
        rows.append({
            'component_id': cid,
            'member_count': len(members),
            'sugar_member_count': len(sugar_members),
            'hdbscan_member_count': len(hdb_members),
            'sugar_family_ids': sugar_members,
            'hdbscan_family_ids': hdb_members,
        })
    require(len(token_to_component) == len(tokens), 'component assignment incomplete')
    return rows, token_to_component


def log_bayes_factor(k: int, n: int, p13: float) -> float:
    require(n > 0 and 0 <= k <= n and 0.0 < p13 < 1.0, 'invalid recurrence-Bayes inputs')
    log_comb = float(gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1))
    return float(math.log(n + 1) + log_comb + k * math.log(p13) + (n - k) * math.log(1.0 - p13))


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    s, Cs, sids = load_pretruth(sugar_root)
    h, Ch, hids = load_pretruth(hdbscan_root)
    require(len(sids) == 267 and len(hids) == 229, 'route family counts changed')

    edges: list[list[Any]] = []
    h_to_s = [[] for _ in hids]
    s_to_h = [[] for _ in sids]
    for hi in range(len(hids)):
        for si in range(len(sids)):
            d = max(annual_distance(Ch[hi, :4], Cs[si, :4]), annual_distance(Ch[hi, 4:], Cs[si, 4:]))
            if d <= RADIUS:
                edges.append([hi, si, float(d)])
                h_to_s[hi].append(si)
                s_to_h[si].append(hi)
    graph = {
        'verdict': 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY',
        'scientific_role': 'PRETRUTH_CROSS_ROUTE_GRAPH_IDENTITY_ONLY',
        'radius': RADIUS,
        'distance': 'max(two annual #1049 four-coordinate distances)',
        'sugar_family_ids': sids,
        'hdbscan_family_ids': hids,
        'edges': edges,
        'hdbscan_to_sugar_adjacency': h_to_s,
        'sugar_to_hdbscan_adjacency': s_to_h,
        'edge_count': len(edges),
        'truth_accessed': False,
        'radius_search': False,
        'metric_search': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    graph_path = output / 'CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY.json'
    graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True, allow_nan=False) + '\n')
    require(len(edges) == 2334 and v22.sha(graph_path) == GRAPH_SHA256, 'exact #1064 graph identity changed')

    components, token_to_component = component_rows_from_graph(graph)
    comp = {
        'verdict': 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY',
        'scientific_role': 'PRETRUTH_CONNECTED_COMPONENT_IDENTITY_ONLY',
        'graph_sha256': GRAPH_SHA256,
        'component_definition': 'ordinary undirected connected components over all frozen Sugar/HDB radius-1 graph vertices including singleton isolates',
        'component_id_rule': 'lexicographically smallest canonical route/family token in component',
        'component_count': len(components),
        'non_singleton_component_count': int(sum(r['member_count'] > 1 for r in components)),
        'singleton_component_count': int(sum(r['member_count'] == 1 for r in components)),
        'components': components,
        'token_to_component': token_to_component,
        'truth_accessed': False,
        'radius_search': False,
        'metric_search': False,
        'within_route_edges_added': False,
        'graph_pruning': False,
        'graph_expansion': False,
        'component_size_threshold_selected': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    comp_path = output / 'CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY.json'
    comp_path.write_text(json.dumps(comp, indent=2, sort_keys=True, allow_nan=False) + '\n')
    require(len(components) == 196 and sum(r['member_count'] > 1 for r in components) == 113 and v22.sha(comp_path) == COMPONENT_SHA256, 'exact #1072 component identity changed')

    family_maps = {
        'sugar': {str(f['family_id']): f for f in s['fp']['families']},
        'hdbscan': {str(f['family_id']): f for f in h['fp']['families']},
    }
    universe_events: set[str] = set()
    for route in ('sugar', 'hdbscan'):
        for f in family_maps[route].values():
            universe_events.update(map(str, f['event_ids']))
    n13 = int(sum(e.startswith('SNT2013:') for e in universe_events))
    n14 = int(sum(e.startswith('SNT2014:') for e in universe_events))
    require(n13 > 0 and n14 > 0 and n13 + n14 == len(universe_events), 'unexpected event-year prefixes in fixed universes')
    p13 = float(n13 / (n13 + n14))

    rows = []
    for c in components:
        events: set[str] = set()
        for fid in map(str, c['sugar_family_ids']):
            events.update(map(str, family_maps['sugar'][fid]['event_ids']))
        for fid in map(str, c['hdbscan_family_ids']):
            events.update(map(str, family_maps['hdbscan'][fid]['event_ids']))
        k13 = int(sum(e.startswith('SNT2013:') for e in events))
        k14 = int(sum(e.startswith('SNT2014:') for e in events))
        require(k13 + k14 == len(events) and len(events) > 0, 'component contains unexpected event-year prefix')
        rows.append({
            'component_id': str(c['component_id']),
            'member_count': int(c['member_count']),
            'sugar_member_count': int(c['sugar_member_count']),
            'hdbscan_member_count': int(c['hdbscan_member_count']),
            'unique_event_count_2013': k13,
            'unique_event_count_2014': k14,
            'unique_event_count_total': len(events),
            'log_bayes_factor_stable_recurrence': log_bayes_factor(k13, len(events), p13),
        })

    out = {
        'verdict': 'PASS_CROSSROUTE_COMPONENT_RECURRENCE_BAYES_PRETRUTH_FREEZE',
        'scientific_role': 'PRETRUTH_COMPONENT_RECURRENCE_STABILITY_STATISTIC_ONLY',
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'component_count': len(components),
        'event_universe_definition': 'unique event IDs appearing in either immutable fixed Sugar or HDB candidate universe',
        'event_universe_unique_2013': n13,
        'event_universe_unique_2014': n14,
        'exposure_fraction_2013': p13,
        'statistic': 'log(n+1)+logC(n,k)+k*log(p13)+(n-k)*log(1-p13)',
        'null': 'component event years follow fixed candidate-universe exposure p13',
        'alternative': 'component Bernoulli year fraction integrated under Beta(1,1)',
        'component_event_union_deduplicated': True,
        'components': rows,
        'truth_accessed': False,
        'alternate_prior_search': False,
        'pseudocount_search': False,
        'transform_search': False,
        'clipping_search': False,
        'balance_statistic_search': False,
        'count_threshold_search': False,
        'significance_threshold_selected': False,
        'rank_or_selector_evaluated': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    path = output / 'CROSSROUTE_COMPONENT_RECURRENCE_BAYES_PRETRUTH.json'
    path.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': out['verdict'], 'component_count': len(rows), 'event_universe_2013': n13, 'event_universe_2014': n14, 'p13': p13}, indent=2, sort_keys=True))
    return 0


def summarize(vals_pos: list[float], vals_neg: list[float]) -> dict[str, Any]:
    require(vals_pos and vals_neg, 'diagnostic requires both recoverable and nonrecoverable components')
    pos = np.asarray(vals_pos, dtype=float)
    neg = np.asarray(vals_neg, dtype=float)
    u = mannwhitneyu(pos, neg, alternative='greater')
    auc = float(u.statistic / (len(pos) * len(neg)))
    return {
        'positive_count': len(pos),
        'negative_count': len(neg),
        'positive_mean_logbf': float(np.mean(pos)),
        'negative_mean_logbf': float(np.mean(neg)),
        'positive_median_logbf': float(np.median(pos)),
        'negative_median_logbf': float(np.median(neg)),
        'mann_whitney_auc': auc,
        'one_sided_p_value_descriptive_only': float(u.pvalue),
        'direction_positive': bool(float(np.median(pos)) > float(np.median(neg)) and auc > 0.5),
    }


def diagnose_mode(sugar_root: Path, hdbscan_root: Path, truth_root: Path, pretruth_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    pre = json.loads(pretruth_file.read_text())
    require(pre['verdict'] == 'PASS_CROSSROUTE_COMPONENT_RECURRENCE_BAYES_PRETRUTH_FREEZE' and pre['truth_accessed'] is False, 'invalid pretruth recurrence statistic')
    require(pre['graph_sha256'] == GRAPH_SHA256 and pre['component_sha256'] == COMPONENT_SHA256 and int(pre['component_count']) == 196, 'pretruth graph/component identity mismatch')
    stat_by_component = {str(r['component_id']): float(r['log_bayes_factor_stable_recurrence']) for r in pre['components']}

    component_identity = json.loads((pretruth_file.parent / 'CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY.json').read_text())
    require(v22.sha(pretruth_file.parent / 'CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY.json') == COMPONENT_SHA256, 'component file changed after pretruth freeze')
    components = component_identity['components']

    roots = {'sugar': sugar_root, 'hdbscan': hdbscan_root}
    route_results = {}
    for route in ('sugar', 'hdbscan'):
        fp = json.loads((roots[route] / 'family_memberships.json').read_text())
        require(fp['truth_accessed'] is False, 'membership payload became truth-bearing')
        fams = fp['families']
        by_year = {year: json.loads((truth_root / f'truth_{route}_{year}.json').read_text()) for year in (2013, 2014)}
        eligible = v22.eligible_from_year_truth(by_year)
        hidden: dict[str, str] = {}
        hidden.update(by_year[2013]); hidden.update(by_year[2014])
        fam_quality: dict[str, tuple[float, float]] = {}
        for f in fams:
            fid = str(f['family_id'])
            t = v22.family_truth(f, hidden, eligible)
            label = t['best_label']
            if not t['positive'] or label is None:
                fam_quality[fid] = (0.0, 0.0)
            else:
                fam_quality[fid] = tuple(map(float, v24.annual_f1_for_fixed_label(f, str(label), by_year)))

        dual_pos: list[float] = []; dual_neg: list[float] = []
        y14_pos: list[float] = []; y14_neg: list[float] = []
        component_rows = []
        for c in components:
            own = list(map(str, c['sugar_family_ids'] if route == 'sugar' else c['hdbscan_family_ids']))
            if not own:
                continue
            dual = any(fam_quality[f][0] > RECOVERY and fam_quality[f][1] > RECOVERY for f in own)
            rec14 = any(fam_quality[f][1] > RECOVERY for f in own)
            val = stat_by_component[str(c['component_id'])]
            (dual_pos if dual else dual_neg).append(val)
            (y14_pos if rec14 else y14_neg).append(val)
            component_rows.append({
                'component_id': str(c['component_id']),
                'own_route_family_count': len(own),
                'dual_year_recoverable': dual,
                'recoverable_2014': rec14,
                'log_bayes_factor_stable_recurrence': val,
            })
        dual_summary = summarize(dual_pos, dual_neg)
        y14_summary = summarize(y14_pos, y14_neg)
        route_results[route] = {
            'component_count': len(component_rows),
            'dual_year_recoverability': dual_summary,
            'year_2014_recoverability': y14_summary,
            'components': component_rows,
            'route_direction_supported': bool(dual_summary['direction_positive'] and y14_summary['direction_positive']),
        }

    supported = bool(route_results['sugar']['route_direction_supported'] and route_results['hdbscan']['route_direction_supported'])
    result = {
        'verdict': 'PASS_CROSSROUTE_COMPONENT_RECURRENCE_BAYES_DIAGNOSTIC' if supported else 'FAIL_CROSSROUTE_COMPONENT_RECURRENCE_BAYES_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_RANK_OR_SELECTOR_EVALUATED',
        'direction_supported_both_routes': supported,
        'pretruth_statistic_verdict': pre['verdict'],
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'exposure_fraction_2013': float(pre['exposure_fraction_2013']),
        'statistic': pre['statistic'],
        'routes': route_results,
        'successor_selected': False,
        'rank_or_selector_evaluated': False,
        'threshold_selected': False,
        'alternate_prior_search': False,
        'alternate_statistic_search': False,
        'feature_search': False,
        'fusion_search': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'CROSSROUTE_COMPONENT_RECURRENCE_BAYES_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'direction_supported_both_routes': supported,
        'sugar_dual': route_results['sugar']['dual_year_recoverability'],
        'sugar_2014': route_results['sugar']['year_2014_recoverability'],
        'hdbscan_dual': route_results['hdbscan']['dual_year_recoverability'],
        'hdbscan_2014': route_results['hdbscan']['year_2014_recoverability'],
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('pretruth')
    a.add_argument('--sugar-root', type=Path, required=True); a.add_argument('--hdbscan-root', type=Path, required=True); a.add_argument('--output', type=Path, required=True)
    b = sub.add_parser('diagnose')
    b.add_argument('--sugar-root', type=Path, required=True); b.add_argument('--hdbscan-root', type=Path, required=True); b.add_argument('--truth-root', type=Path, required=True); b.add_argument('--pretruth-file', type=Path, required=True); b.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.mode == 'pretruth':
        return pretruth_mode(args.sugar_root, args.hdbscan_root, args.output)
    return diagnose_mode(args.sugar_root, args.hdbscan_root, args.truth_root, args.pretruth_file, args.output)


if __name__ == '__main__':
    raise SystemExit(main())

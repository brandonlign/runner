#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM = 71
RECOVERY = 0.5
RADIUS = 1.0
GRAPH_SHA256 = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
EXPECTED_V31 = {
    ('sugar', 2013): (0.2719801488280529, 16, 34),
    ('sugar', 2014): (0.31529041952487225, 17, 46),
    ('hdbscan', 2013): (0.14888037368183737, 9, 11),
    ('hdbscan', 2014): (0.15198123772301594, 9, 9),
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def order_sha(order: list[str]) -> str:
    return hashlib.sha256('\n'.join(map(str, order)).encode()).hexdigest()


def wrap180(x: float) -> float:
    return float((float(x) + 180.0) % 360.0 - 180.0)


def annual_distance(a: np.ndarray, b: np.ndarray) -> float:
    d_sol = wrap180(float(a[0]) - float(b[0])) / 4.0
    d_lon = wrap180(float(a[1]) - float(b[1])) * math.cos(math.radians(0.5 * (float(a[2]) + float(b[2])))) / 2.0
    d_lat = (float(a[2]) - float(b[2])) / 2.0
    d_vg = (math.exp(float(a[3])) - math.exp(float(b[3]))) / 2.0
    return float(math.sqrt(d_sol*d_sol + d_lon*d_lon + d_lat*d_lat + d_vg*d_vg))


def load_pretruth(root: Path) -> tuple[dict[str, Any], np.ndarray, np.ndarray, list[str]]:
    meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((root / 'family_memberships.json').read_text())
    ids = list(map(str, meta['family_ids']))
    X = np.load(root / 'features.npy', allow_pickle=False)
    C = np.load(root / 'centroids.npy', allow_pickle=False)
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and meta['feature_dimension'] == FEATURE_DIM, 'invalid immutable pretruth payload')
    require(X.shape == (len(ids), FEATURE_DIM) and C.shape == (len(ids), 8), 'pretruth array shape changed')
    require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], 'pretruth array identity changed')
    require([str(f['family_id']) for f in fp['families']] == ids, 'family order changed')
    return {'meta': meta, 'fp': fp, 'ids': ids}, X, C, ids


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
    raw = defaultdict(list)
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
    require(sum(r['member_count'] for r in rows) == len(tokens), 'component sizes do not cover vertex universe')
    return rows, token_to_component


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    _s, _Xs, Cs, sids = load_pretruth(sugar_root)
    _h, _Xh, Ch, hids = load_pretruth(hdbscan_root)
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
    require(len(edges) == 2334, 'cross-route radius-1 edge count changed')
    require(v22.sha(graph_path) == GRAPH_SHA256, 'cross-route radius-1 graph identity changed')

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
    print(json.dumps({
        'graph_verdict': graph['verdict'],
        'graph_sha256': v22.sha(graph_path),
        'edge_count': len(edges),
        'component_verdict': comp['verdict'],
        'component_count': len(components),
        'non_singleton_component_count': comp['non_singleton_component_count'],
        'component_identity_sha256': v22.sha(comp_path),
    }, indent=2, sort_keys=True))
    return 0


def median_or_none(xs: list[float | int]) -> float | None:
    return None if not xs else float(np.median(np.asarray(xs, dtype=float)))


def diagnostic_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    component_file: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(v22.sha(graph_file) == GRAPH_SHA256, 'frozen pretruth graph identity changed')
    graph = json.loads(graph_file.read_text())
    comp = json.loads(component_file.read_text())
    require(graph['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY' and graph['truth_accessed'] is False, 'invalid pretruth graph')
    require(graph['edge_count'] == 2334 and graph['radius'] == 1.0, 'pretruth graph definition changed')
    require(comp['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY' and comp['truth_accessed'] is False, 'invalid pretruth components')
    require(comp['graph_sha256'] == GRAPH_SHA256, 'component graph identity changed')
    recomputed_components, recomputed_map = component_rows_from_graph(graph)
    require(recomputed_components == comp['components'] and recomputed_map == comp['token_to_component'], 'pretruth connected-component assignments changed')
    require(v22.sha(ranker_source) == v24.RANKER_SOURCE_SHA, '#839 ranker source changed')

    roots = {'sugar': sugar_root, 'hdbscan': hdbscan_root}
    truth: dict[tuple[str, int], dict] = {}
    frozen_eval: dict[tuple[str, int], dict] = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((truth_root / f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route, year)] = json.loads((truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(ranker_source, 'frozen_839_component_closure_diag')
    route_data: dict[str, dict[str, Any]] = {}
    Xs, y13s, y14s, groups = [], [], [], []
    offsets = {}
    cursor = 0

    for route in v24.ROUTES:
        root = roots[route]
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp = json.loads((root / 'family_memberships.json').read_text())
        ids = list(map(str, meta['family_ids']))
        fams = fp['families']
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and meta['feature_dimension'] == FEATURE_DIM, f'{route} invalid immutable pretruth payload')
        require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], f'{route} immutable array identity changed')
        require([str(f['family_id']) for f in fams] == ids, f'{route} family order changed')
        by = {y: truth[(route, y)] for y in v24.YEARS}
        eligible = v22.eligible_from_year_truth(by)
        hidden = {}
        hidden.update(by[2013])
        hidden.update(by[2014])
        base_truth = [v22.family_truth(f, hidden, eligible) for f in fams]
        q13, q14, rg = [], [], []
        for i, (fam, t) in enumerate(zip(fams, base_truth)):
            label = t['best_label']
            rg.append(('SHOWER/' + str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                a13 = a14 = 0.0
            else:
                a13, a14 = v24.annual_f1_for_fixed_label(fam, str(label), by)
            q13.append(float(a13))
            q14.append(float(a14))
        offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        Xs.append(X)
        y13s.append(np.asarray(q13, dtype=float))
        y14s.append(np.asarray(q14, dtype=float))
        groups.extend(rg)
        route_data[route] = {
            'meta': meta,
            'fams': fams,
            'ids': ids,
            'centroids': C,
            'groups': rg,
            'y13': np.asarray(q13, dtype=float),
            'y14': np.asarray(q14, dtype=float),
        }

    require(graph['sugar_family_ids'] == route_data['sugar']['ids'], 'Sugar graph family universe changed')
    require(graph['hdbscan_family_ids'] == route_data['hdbscan']['ids'], 'HDB graph family universe changed')
    require(len(route_data['sugar']['ids']) == 267 and len(route_data['hdbscan']['ids']) == 229, 'route family counts changed')

    Xall = np.vstack(Xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    groups_all = list(map(str, groups))
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups_all], dtype=int)
    m13 = np.zeros(cursor, dtype=float)
    m14 = np.zeros(cursor, dtype=float)
    fold_diag = []
    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        require({groups_all[i] for i in np.where(tr)[0]}.isdisjoint({groups_all[i] for i in np.where(te)[0]}), f'group leakage fold {fold}')
        mu = np.mean(Xall[tr], axis=0)
        sd = np.std(Xall[tr], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        Ztr = (Xall[tr] - mu[None, :]) / scale[None, :]
        Zte = (Xall[te] - mu[None, :]) / scale[None, :]
        te_idx = np.where(te)[0]
        annual_refs = {}
        for year, yall, out in ((2013, y13all, m13), (2014, y14all, m14)):
            pos = yall[tr] > RECOVERY
            neg = ~pos
            require(pos.any() and neg.any(), f'{year} fold {fold} lacks references')
            P, N = Ztr[pos], Ztr[neg]
            for j, gi in enumerate(te_idx.tolist()):
                dpos = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))
                dneg = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))
                require(np.isfinite(dpos) and np.isfinite(dneg), f'nonfinite v31 distance {year} fold {fold}')
                out[gi] = dneg - dpos
            annual_refs[str(year)] = {'positive_references': int(pos.sum()), 'nonpositive_references': int(neg.sum())}
        fold_diag.append({'fold': fold, 'train_examples': int(tr.sum()), 'test_examples': int(te.sum()), 'annual_references': annual_refs})

    combined = np.minimum(m13, m14)
    route_orders: dict[str, list[str]] = {}
    ranked = {}
    for route in v24.ROUTES:
        lo, hi = offsets[route]
        rd = route_data[route]
        ids = rd['ids']
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(combined[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        local = [ids[i] for i in idx]
        fused = list(v19.fusion_orders(local, list(map(str, rd['meta']['v19_order'])))['rank_sum'])
        route_orders[route] = fused
        ranked[route] = v22.rerank(rd['fams'], fused)

    reproduction = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(ranked[route], truth[(route, year)], budget)
        exp = EXPECTED_V31[(route, year)]
        require(abs(float(cur['macro_f1']) - exp[0]) < 1e-12 and int(cur['recovered_f1_gt_0_5']) == exp[1] and int(cur['candidate_used']) == exp[2], f'v31 reproduction mismatch {route} {year}')
        reproduction.append({'comparator': route, 'year': year, **cur})

    token_to_component = comp['token_to_component']
    comp_by_id = {r['component_id']: dict(r) for r in comp['components']}
    group_by_token = {}
    for route in v24.ROUTES:
        for fid, g in zip(route_data[route]['ids'], route_data[route]['groups']):
            group_by_token[f'{route}/{fid}'] = str(g)
    require(set(group_by_token) == set(token_to_component), 'truth group/token universe mismatch')

    component_truth_rows = []
    multi_shower_components = []
    for cid, row in sorted(comp_by_id.items()):
        members = [f'sugar/{x}' for x in row['sugar_family_ids']] + [f'hdbscan/{x}' for x in row['hdbscan_family_ids']]
        labels = sorted({group_by_token[t] for t in members if group_by_token[t].startswith('SHOWER/')})
        neg_count = int(sum(group_by_token[t].startswith('NEG/') for t in members))
        out = {
            **row,
            'strict_shower_labels': labels,
            'distinct_strict_shower_label_count': len(labels),
            'neg_member_count': neg_count,
            'contains_neg_member': bool(neg_count > 0),
            'mixes_distinct_strict_showers': bool(len(labels) > 1),
        }
        component_truth_rows.append(out)
        if row['member_count'] > 1 and len(labels) > 1:
            multi_shower_components.append(out)

    non_singleton = [r for r in component_truth_rows if r['member_count'] > 1]
    purity = {
        'component_count': len(component_truth_rows),
        'non_singleton_component_count': len(non_singleton),
        'singleton_component_count': int(sum(r['member_count'] == 1 for r in component_truth_rows)),
        'non_singleton_multi_shower_component_count': len(multi_shower_components),
        'non_singleton_multi_shower_component_fraction': float(len(multi_shower_components) / len(non_singleton)) if non_singleton else None,
        'non_singleton_with_neg_member_count': int(sum(r['contains_neg_member'] for r in non_singleton)),
        'multi_shower_components': multi_shower_components,
    }

    s_rank = {fid: i + 1 for i, fid in enumerate(route_orders['sugar'])}
    h_rank = {fid: i + 1 for i, fid in enumerate(route_orders['hdbscan'])}
    h_index = {fid: i for i, fid in enumerate(route_data['hdbscan']['ids'])}

    annual = {}
    positive_opportunity_years = []
    for year, yvals in ((2013, route_data['hdbscan']['y13']), (2014, route_data['hdbscan']['y14'])):
        h_budget = int(frozen_eval[('hdbscan', year)]['candidate_budget']['comparator_budget'])
        s_budget = int(frozen_eval[('sugar', year)]['candidate_budget']['comparator_budget'])
        top_ids = route_orders['hdbscan'][:h_budget]
        top_components = [token_to_component[f'hdbscan/{fid}'] for fid in top_ids]
        unique_top_components = sorted(set(top_components))
        repeated = []
        for cid in unique_top_components:
            members = [(fid, h_rank[fid]) for fid in top_ids if token_to_component[f'hdbscan/{fid}'] == cid]
            if len(members) > 1:
                repeated.append({'component_id': cid, 'selected_hdb_families': [{'family_id': f, 'v31_rank': r} for f, r in members], 'slots': len(members)})

        group_candidates = defaultdict(list)
        for i, fid in enumerate(route_data['hdbscan']['ids']):
            g = str(route_data['hdbscan']['groups'][i])
            if g.startswith('SHOWER/') and float(yvals[i]) > RECOVERY:
                group_candidates[g].append(fid)
        rows = []
        for g, fids in sorted(group_candidates.items()):
            rep = min(fids, key=lambda x: h_rank[x])
            cid = token_to_component[f'hdbscan/{rep}']
            crow = comp_by_id[cid]
            h_members = list(map(str, crow['hdbscan_family_ids']))
            s_members = list(map(str, crow['sugar_family_ids']))
            best_h = min((h_rank[f] for f in h_members), default=None)
            best_s = min((s_rank[f] for f in s_members), default=None)
            rep_rank = int(h_rank[rep])
            p_rep = float((rep_rank - 1) / 228.0)
            percentiles = [float((h_rank[f] - 1) / 228.0) for f in h_members]
            percentiles += [float((s_rank[f] - 1) / 266.0) for f in s_members]
            best_component_percentile = min(percentiles) if percentiles else p_rep
            surfaced = bool(rep_rank <= h_budget)
            non_singleton_component = bool(int(crow['member_count']) > 1)
            opportunity = bool((not surfaced) and non_singleton_component and best_component_percentile < p_rep)
            rows.append({
                'group': g,
                'representative_family_id': rep,
                'representative_annual_f1': float(yvals[h_index[rep]]),
                'representative_hdb_v31_rank': rep_rank,
                'representative_hdb_percentile': p_rep,
                'surfaced_hdb': surfaced,
                'component_id': cid,
                'component_member_count': int(crow['member_count']),
                'component_sugar_member_count': int(crow['sugar_member_count']),
                'component_hdbscan_member_count': int(crow['hdbscan_member_count']),
                'component_is_non_singleton': non_singleton_component,
                'best_component_hdb_v31_rank': best_h,
                'best_component_sugar_v31_rank': best_s,
                'best_component_normalized_v31_percentile': float(best_component_percentile),
                'component_already_represented_in_hdb_budget': bool(any(h_rank[f] <= h_budget for f in h_members)),
                'component_has_sugar_member_in_same_sized_prefix': bool(any(s_rank[f] <= h_budget for f in s_members)),
                'component_has_sugar_member_in_sugar_budget': bool(any(s_rank[f] <= s_budget for f in s_members)),
                'component_closure_opportunity': opportunity,
            })
        surfaced_rows = [r for r in rows if r['surfaced_hdb']]
        missed_rows = [r for r in rows if not r['surfaced_hdb']]
        opportunities = [r for r in missed_rows if r['component_closure_opportunity']]

        def group_summary(xs: list[dict[str, Any]]) -> dict[str, Any]:
            return {
                'count': len(xs),
                'non_singleton_component_count': int(sum(r['component_is_non_singleton'] for r in xs)),
                'component_already_represented_in_hdb_budget_count': int(sum(r['component_already_represented_in_hdb_budget'] for r in xs)),
                'median_best_component_hdb_v31_rank': median_or_none([r['best_component_hdb_v31_rank'] for r in xs if r['best_component_hdb_v31_rank'] is not None]),
                'median_best_component_sugar_v31_rank': median_or_none([r['best_component_sugar_v31_rank'] for r in xs if r['best_component_sugar_v31_rank'] is not None]),
            }

        annual[str(year)] = {
            'hdb_budget': h_budget,
            'sugar_budget': s_budget,
            'top_budget_unique_component_count': len(unique_top_components),
            'top_budget_duplicate_component_slots': int(h_budget - len(unique_top_components)),
            'top_budget_repeated_components': repeated,
            'annual_recoverable_hdb_groups': len(rows),
            'surfaced_recoverable_hdb_groups': len(surfaced_rows),
            'missed_recoverable_hdb_groups': len(missed_rows),
            'surfaced_summary': group_summary(surfaced_rows),
            'missed_summary': group_summary(missed_rows),
            'component_closure_opportunity_count': len(opportunities),
            'component_closure_opportunity_fraction_of_missed': float(len(opportunities) / len(missed_rows)) if missed_rows else None,
            'component_closure_opportunities': opportunities,
            'recoverable_group_rows': rows,
        }
        positive_opportunity_years.append(len(opportunities) >= 1)

    zero_multi_shower = bool(len(multi_shower_components) == 0)
    direction_supported = bool(zero_multi_shower and all(positive_opportunity_years))
    result = {
        'verdict': 'PASS_V31_CROSSROUTE_COMPONENT_CLOSURE_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_COMPONENT_RANK_OR_SELECTOR_EVALUATED',
        'question': 'whether exact frozen radius-1 connected components are pure latent-structure surrogates with closure opportunities for recoverable-but-missed HDB groups',
        'pretruth_graph_sha256': GRAPH_SHA256,
        'pretruth_component_identity_sha256': v22.sha(component_file),
        'component_definition': comp['component_definition'],
        'component_id_rule': comp['component_id_rule'],
        'v31_reproduction': reproduction,
        'v31_order_sha256': {route: order_sha(route_orders[route]) for route in v24.ROUTES},
        'component_physical_purity': purity,
        'annual_diagnostics': annual,
        'interpretation_condition_zero_multi_shower_components': zero_multi_shower,
        'interpretation_condition_opportunity_in_each_year': bool(all(positive_opportunity_years)),
        'component_closure_direction_supported': direction_supported,
        'new_rank_or_score_evaluated': False,
        'component_score_evaluated': False,
        'component_selector_evaluated': False,
        'hard_one_per_component_evaluated': False,
        'representative_rule_evaluated': False,
        'graph_propagation_evaluated': False,
        'successor_selected': False,
        'radius_search': False,
        'metric_search': False,
        'feature_search': False,
        'within_route_edges_added': False,
        'graph_pruning': False,
        'graph_expansion': False,
        'component_size_threshold_selected': False,
        'component_rank_aggregation_search': False,
        'component_support_bonus_search': False,
        'transfer_coefficient_search': False,
        'overlap_weight_search': False,
        'jaccard_weight_search': False,
        'distance_weight_search': False,
        'budget_specific_successor': False,
        'candidate_generation_changed': False,
        'membership_changed': False,
        'post_result_second_search': False,
        'oracle_identity_hardcoded': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
        'fold_diagnostics': fold_diag,
        'component_truth_rows': component_truth_rows,
    }
    (output / 'V31_CROSSROUTE_COMPONENT_CLOSURE_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'component_closure_direction_supported': direction_supported,
        'component_physical_purity': purity,
        'annual': {
            y: {
                'hdb_budget': d['hdb_budget'],
                'top_budget_unique_component_count': d['top_budget_unique_component_count'],
                'top_budget_duplicate_component_slots': d['top_budget_duplicate_component_slots'],
                'component_closure_opportunity_count': d['component_closure_opportunity_count'],
                'component_closure_opportunity_fraction_of_missed': d['component_closure_opportunity_fraction_of_missed'],
                'surfaced_summary': d['surfaced_summary'],
                'missed_summary': d['missed_summary'],
            }
            for y, d in annual.items()
        },
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('pretruth')
    a.add_argument('--sugar-root', type=Path, required=True)
    a.add_argument('--hdbscan-root', type=Path, required=True)
    a.add_argument('--output', type=Path, required=True)
    b = sub.add_parser('diagnose')
    b.add_argument('--sugar-root', type=Path, required=True)
    b.add_argument('--hdbscan-root', type=Path, required=True)
    b.add_argument('--truth-root', type=Path, required=True)
    b.add_argument('--ranker-source', type=Path, required=True)
    b.add_argument('--graph-file', type=Path, required=True)
    b.add_argument('--component-file', type=Path, required=True)
    b.add_argument('--output', type=Path, required=True)
    x = p.parse_args()
    if x.mode == 'pretruth':
        return pretruth_mode(x.sugar_root, x.hdbscan_root, x.output)
    return diagnostic_mode(x.sugar_root, x.hdbscan_root, x.truth_root, x.ranker_source, x.graph_file, x.component_file, x.output)


if __name__ == '__main__':
    raise SystemExit(main())

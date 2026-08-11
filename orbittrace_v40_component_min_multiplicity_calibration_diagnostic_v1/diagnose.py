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
from scipy.stats import spearmanr

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM = 71
RECOVERY = 0.5
RADIUS = 1.0
GRAPH_SHA256 = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA256 = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
EXPECTED_V31 = {
    ('sugar', 2013): (0.2719801488280529, 16),
    ('sugar', 2014): (0.31529041952487225, 17),
    ('hdbscan', 2013): (0.14888037368183737, 9),
    ('hdbscan', 2014): (0.15198123772301594, 9),
}
EXPECTED_V40_ORDER_SHA = {
    'sugar': '1dc01938a8cb83622ce023b516162be524e0812aa4b0a886c23267c0881aee2c',
    'hdbscan': 'c6d29171c410f731a30f6eacba5bfe8de05c8cddf17d7bcbfd4dabb867fd7899',
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
    for token in tokens:
        raw[dsu.find(token)].append(token)
    rows = []
    token_to_component = {}
    for members in sorted((sorted(v) for v in raw.values()), key=lambda xs: xs[0]):
        cid = members[0]
        for token in members:
            token_to_component[token] = cid
        sugar_ids = [x.split('/', 1)[1] for x in members if x.startswith('sugar/')]
        hdb_ids = [x.split('/', 1)[1] for x in members if x.startswith('hdbscan/')]
        rows.append({
            'component_id': cid,
            'member_count': len(members),
            'sugar_member_count': len(sugar_ids),
            'hdbscan_member_count': len(hdb_ids),
            'sugar_family_ids': sugar_ids,
            'hdbscan_family_ids': hdb_ids,
        })
    require(len(token_to_component) == len(tokens), 'component assignment incomplete')
    require(sum(r['member_count'] for r in rows) == len(tokens), 'component coverage mismatch')
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
    gpath = output / 'CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY.json'
    gpath.write_text(json.dumps(graph, indent=2, sort_keys=True, allow_nan=False) + '\n')
    require(len(edges) == 2334 and v22.sha(gpath) == GRAPH_SHA256, 'exact #1064 graph identity changed')
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
    cpath = output / 'CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY.json'
    cpath.write_text(json.dumps(comp, indent=2, sort_keys=True, allow_nan=False) + '\n')
    require(v22.sha(cpath) == COMPONENT_SHA256, 'exact #1072 component identity changed')
    print(json.dumps({'graph_sha256': v22.sha(gpath), 'component_sha256': v22.sha(cpath), 'component_count': len(components)}, indent=2, sort_keys=True))
    return 0


def v40_order(route: str, base_order: list[str], components: list[dict[str, Any]], rank_maps: dict[str, dict[str, int]]) -> list[str]:
    n_route = len(base_order)
    reps = []
    rep_ids = set()
    for c in components:
        own_ids = list(map(str, c['sugar_family_ids'] if route == 'sugar' else c['hdbscan_family_ids']))
        if not own_ids:
            continue
        own_rep = min(own_ids, key=lambda fid: (rank_maps[route][fid], fid))
        rep_ids.add(own_rep)
        member_p = []
        for fid in map(str, c['sugar_family_ids']):
            rr = rank_maps['sugar'][fid]
            member_p.append((rr - 1) / (len(rank_maps['sugar']) - 1))
        for fid in map(str, c['hdbscan_family_ids']):
            rr = rank_maps['hdbscan'][fid]
            member_p.append((rr - 1) / (len(rank_maps['hdbscan']) - 1))
        evidence = float(min(member_p))
        reps.append((evidence, int(rank_maps[route][own_rep]), str(c['component_id']), own_rep))
    primary = [x[3] for x in sorted(reps)]
    secondary = [fid for fid in base_order if fid not in rep_ids]
    out = primary + secondary
    require(len(out) == len(base_order) and set(out) == set(base_order), f'{route} invalid v40 replay order')
    return out


def corr_row(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    require(len(rows) >= 2, f'{name} too few components')
    m = np.asarray([float(x['member_count']) for x in rows], dtype=float)
    p = np.asarray([float(x['p_min']) for x in rows], dtype=float)
    q = np.asarray([float(x['q_calibrated']) for x in rows], dtype=float)
    rho_raw = float(spearmanr(m, p).statistic)
    rho_cal = float(spearmanr(m, q).statistic)
    require(np.isfinite(rho_raw) and np.isfinite(rho_cal), f'{name} nonfinite Spearman statistic')
    return {
        'universe': name,
        'component_count': len(rows),
        'rho_raw_size_vs_p_min': rho_raw,
        'rho_calibrated_size_vs_q': rho_cal,
        'raw_negative': bool(rho_raw < 0.0),
        'calibrated_absolute_correlation_smaller': bool(abs(rho_cal) < abs(rho_raw)),
        'gate_pass': bool(rho_raw < 0.0 and abs(rho_cal) < abs(rho_raw)),
    }


def diagnose_mode(sugar_root: Path, hdbscan_root: Path, truth_root: Path, ranker_source: Path, graph_file: Path, component_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(v22.sha(graph_file) == GRAPH_SHA256 and v22.sha(component_file) == COMPONENT_SHA256, 'pretruth graph/component identity changed')
    graph = json.loads(graph_file.read_text())
    comp = json.loads(component_file.read_text())
    require(graph['truth_accessed'] is False and comp['truth_accessed'] is False, 'truth contaminated pretruth identity')
    require(comp['component_count'] == 196 and comp['non_singleton_component_count'] == 113 and comp['singleton_component_count'] == 83, 'component counts changed')
    require(v22.sha(ranker_source) == v24.RANKER_SOURCE_SHA, '#839 ranker source changed')
    roots = {'sugar': sugar_root, 'hdbscan': hdbscan_root}
    truth = {}
    frozen = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((truth_root / f'truth_{route}_{year}.json').read_text())
        frozen[(route, year)] = json.loads((truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(ranker_source, 'frozen_839_v40_multiplicity_diag')
    data = {}
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
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and meta['feature_dimension'] == FEATURE_DIM, f'{route} invalid pretruth payload')
        require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], f'{route} pretruth identity changed')
        require([str(f['family_id']) for f in fams] == ids, f'{route} family order changed')
        by = {y: truth[(route, y)] for y in v24.YEARS}
        eligible = v22.eligible_from_year_truth(by)
        hidden = {}; hidden.update(by[2013]); hidden.update(by[2014])
        base = [v22.family_truth(f, hidden, eligible) for f in fams]
        q13, q14, rg = [], [], []
        for i, (fam, t) in enumerate(zip(fams, base)):
            label = t['best_label']
            rg.append(('SHOWER/' + str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                a13 = a14 = 0.0
            else:
                a13, a14 = v24.annual_f1_for_fixed_label(fam, str(label), by)
            q13.append(float(a13)); q14.append(float(a14))
        offsets[route] = (cursor, cursor + len(ids)); cursor += len(ids)
        Xs.append(X); y13s.append(np.asarray(q13, float)); y14s.append(np.asarray(q14, float)); groups.extend(rg)
        data[route] = {'meta': meta, 'fams': fams, 'ids': ids, 'centroids': C, 'y13': np.asarray(q13, float), 'y14': np.asarray(q14, float)}

    require(graph['sugar_family_ids'] == data['sugar']['ids'] and graph['hdbscan_family_ids'] == data['hdbscan']['ids'], 'graph family identity changed')
    Xall = np.vstack(Xs); y13all = np.concatenate(y13s); y14all = np.concatenate(y14s); groups = list(map(str, groups))
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    m13 = np.zeros(cursor, float); m14 = np.zeros(cursor, float)
    for fold in range(5):
        tr = folds != fold; te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f'group leakage fold {fold}')
        mu = Xall[tr].mean(0); sd = Xall[tr].std(0, ddof=0); scale = sd.copy(); scale[scale == 0.0] = 1.0
        Ztr = (Xall[tr] - mu) / scale; Zte = (Xall[te] - mu) / scale; teidx = np.where(te)[0]
        for yall, out in ((y13all, m13), (y14all, m14)):
            pos = yall[tr] > RECOVERY; neg = ~pos
            require(pos.any() and neg.any(), f'fold {fold} missing references')
            P = Ztr[pos]; N = Ztr[neg]
            for j, gi in enumerate(teidx.tolist()):
                out[gi] = float(np.min(np.linalg.norm(N - Zte[j], axis=1)) - np.min(np.linalg.norm(P - Zte[j], axis=1)))
    combined = np.minimum(m13, m14)

    orders = {}; ranked = {}
    for route in v24.ROUTES:
        lo, hi = offsets[route]; rd = data[route]; ids = rd['ids']
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(combined[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        local = [ids[i] for i in idx]
        fused = list(v19.fusion_orders(local, list(map(str, rd['meta']['v19_order'])))['rank_sum'])
        orders[route] = fused; ranked[route] = v22.rerank(rd['fams'], fused)

    reproduction = []
    for route, year in v24.PANELS:
        budget = int(frozen[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(ranked[route], truth[(route, year)], budget)
        exp = EXPECTED_V31[(route, year)]
        require(abs(float(cur['macro_f1']) - exp[0]) < 1e-12 and int(cur['recovered_f1_gt_0_5']) == exp[1], f'v31 reproduction failed {route} {year}')
        reproduction.append({'comparator': route, 'year': year, **cur})

    rank_maps = {route: {fid: i + 1 for i, fid in enumerate(orders[route])} for route in v24.ROUTES}
    v40_orders = {route: v40_order(route, orders[route], comp['components'], rank_maps) for route in v24.ROUTES}
    for route in v24.ROUTES:
        require(order_sha(v40_orders[route]) == EXPECTED_V40_ORDER_SHA[route], f'exact v40 order replay failed {route}')

    component_rows = []
    for c in comp['components']:
        member_rows = []
        sugar_best_rank = None; hdb_best_rank = None
        for fid in map(str, c['sugar_family_ids']):
            rr = int(rank_maps['sugar'][fid]); p = float((rr - 1) / (len(rank_maps['sugar']) - 1)); member_rows.append(('sugar', fid, rr, p))
            sugar_best_rank = rr if sugar_best_rank is None else min(sugar_best_rank, rr)
        for fid in map(str, c['hdbscan_family_ids']):
            rr = int(rank_maps['hdbscan'][fid]); p = float((rr - 1) / (len(rank_maps['hdbscan']) - 1)); member_rows.append(('hdbscan', fid, rr, p))
            hdb_best_rank = rr if hdb_best_rank is None else min(hdb_best_rank, rr)
        require(member_rows, 'empty component')
        p_min = float(min(x[3] for x in member_rows))
        m = int(c['member_count'])
        q = float(1.0 - (1.0 - p_min) ** m)
        component_rows.append({
            'component_id': str(c['component_id']),
            'member_count': m,
            'sugar_member_count': int(c['sugar_member_count']),
            'hdbscan_member_count': int(c['hdbscan_member_count']),
            'has_sugar': bool(c['sugar_member_count'] > 0),
            'has_hdbscan': bool(c['hdbscan_member_count'] > 0),
            'p_min': p_min,
            'q_calibrated': q,
            'multiplicity_inflation': float(q - p_min),
            'best_sugar_v31_rank': sugar_best_rank,
            'best_sugar_v31_percentile': None if sugar_best_rank is None else float((sugar_best_rank - 1) / (len(rank_maps['sugar']) - 1)),
            'best_hdbscan_v31_rank': hdb_best_rank,
            'best_hdbscan_v31_percentile': None if hdb_best_rank is None else float((hdb_best_rank - 1) / (len(rank_maps['hdbscan']) - 1)),
        })
    by_component = {r['component_id']: r for r in component_rows}
    correlations = [
        corr_row(component_rows, 'all_components'),
        corr_row([x for x in component_rows if x['has_sugar']], 'sugar_bearing_components'),
        corr_row([x for x in component_rows if x['has_hdbscan']], 'hdbscan_bearing_components'),
    ]
    gate = bool(all(x['gate_pass'] for x in correlations))

    token_to_component = comp['token_to_component']
    h_index = {fid: i for i, fid in enumerate(data['hdbscan']['ids'])}
    annual = {}
    for year, yvals in ((2013, data['hdbscan']['y13']), (2014, data['hdbscan']['y14'])):
        budget = int(frozen[('hdbscan', year)]['candidate_budget']['comparator_budget'])
        v31_prefix = orders['hdbscan'][:budget]
        v40_prefix = v40_orders['hdbscan'][:budget]
        old = set(v31_prefix)
        entrants = [fid for fid in v40_prefix if fid not in old]
        entrant_rows = []
        for fid in entrants:
            cid = token_to_component[f'hdbscan/{fid}']
            cs = by_component[cid]
            entrant_rows.append({
                'family_id': fid,
                'v31_rank': int(rank_maps['hdbscan'][fid]),
                'v40_rank': int(v40_orders['hdbscan'].index(fid) + 1),
                'component_id': cid,
                'component_member_count': int(cs['member_count']),
                'component_p_min': float(cs['p_min']),
                'component_q_calibrated': float(cs['q_calibrated']),
                'component_multiplicity_inflation': float(cs['multiplicity_inflation']),
                'annual_f1': float(yvals[h_index[fid]]),
                'individually_annual_recoverable': bool(float(yvals[h_index[fid]]) > RECOVERY),
            })
        annual[str(year)] = {'budget': budget, 'v31_prefix_families': v31_prefix, 'v40_prefix_families': v40_prefix, 'v40_new_entrant_count': len(entrants), 'v40_new_entrant_rows': entrant_rows}

    result = {
        'verdict': 'PASS_V40_COMPONENT_MIN_MULTIPLICITY_CALIBRATION_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CALIBRATED_ORDER_OR_PANEL_EVALUATED',
        'question': 'whether v40 raw component-minimum evidence has component-size dependence and canonical minimum-order-statistic calibration reduces it',
        'pretruth_graph_sha256': GRAPH_SHA256,
        'pretruth_component_sha256': COMPONENT_SHA256,
        'v31_reproduction': reproduction,
        'v40_order_reproduction_sha256': {r: order_sha(v40_orders[r]) for r in v24.ROUTES},
        'raw_component_evidence': 'p_min=min normalized exact-v31 percentile over all frozen component members',
        'canonical_calibration': 'q=1-(1-p_min)**member_count',
        'calibration_interpretation': 'minimum-order-statistic probability integral transform under independent Uniform(0,1) reference; no independence claim is made for real components',
        'component_rows': component_rows,
        'correlation_tests': correlations,
        'predeclared_multiplicity_calibration_direction_supported': gate,
        'annual_hdb_v40_entrant_localization': annual,
        'new_candidate_order_evaluated': False,
        'new_component_order_evaluated': False,
        'new_panel_evaluation_performed': False,
        'component_size_threshold_selected': False,
        'effective_component_size_fit': False,
        'calibration_exponent_search': False,
        'calibration_coefficient_search': False,
        'calibration_pseudocount_search': False,
        'route_specific_calibration': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'oracle_identity_used_for_rule': False,
        'successor_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V40_COMPONENT_MIN_MULTIPLICITY_CALIBRATION_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'correlation_tests': correlations, 'predeclared_multiplicity_calibration_direction_supported': gate, 'annual_hdb_v40_entrant_localization': annual}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    g = sub.add_parser('pretruth')
    g.add_argument('--sugar-root', type=Path, required=True)
    g.add_argument('--hdbscan-root', type=Path, required=True)
    g.add_argument('--output', type=Path, required=True)
    d = sub.add_parser('diagnose')
    d.add_argument('--sugar-root', type=Path, required=True)
    d.add_argument('--hdbscan-root', type=Path, required=True)
    d.add_argument('--truth-root', type=Path, required=True)
    d.add_argument('--ranker-source', type=Path, required=True)
    d.add_argument('--graph-file', type=Path, required=True)
    d.add_argument('--component-file', type=Path, required=True)
    d.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'pretruth':
        return pretruth_mode(a.sugar_root, a.hdbscan_root, a.output)
    return diagnose_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.graph_file, a.component_file, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

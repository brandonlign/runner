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
COMPONENT_SHA256 = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
VARIANT = 'connected_component_best_evidence_first_representative_v1'
PARENT = {
    ('sugar', 2013): (0.2719801488280529, 16),
    ('sugar', 2014): (0.31529041952487225, 17),
    ('hdbscan', 2013): (0.14888037368183737, 9),
    ('hdbscan', 2014): (0.15198123772301594, 9),
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
    require(v22.sha(comp_path) == COMPONENT_SHA256, 'connected-component identity changed from #1072')
    print(json.dumps({
        'graph_verdict': graph['verdict'],
        'graph_sha256': v22.sha(graph_path),
        'edge_count': len(edges),
        'component_verdict': comp['verdict'],
        'component_sha256': v22.sha(comp_path),
        'component_count': len(components),
        'non_singleton_component_count': comp['non_singleton_component_count'],
        'singleton_component_count': comp['singleton_component_count'],
    }, indent=2, sort_keys=True))
    return 0


def build_v40_order(route: str, base_order: list[str], components: list[dict[str, Any]], rank_maps: dict[str, dict[str, int]]) -> tuple[list[str], list[dict[str, Any]]]:
    require(route in ('sugar', 'hdbscan'), 'invalid route')
    n_route = len(base_order)
    require(n_route == len(rank_maps[route]) and n_route > 1, 'rank universe mismatch')
    reps = []
    rep_ids = set()
    for c in components:
        own_ids = list(map(str, c['sugar_family_ids'] if route == 'sugar' else c['hdbscan_family_ids']))
        if not own_ids:
            continue
        own_rep = min(own_ids, key=lambda fid: (rank_maps[route][fid], fid))
        rep_ids.add(own_rep)
        member_rows = []
        for fid in map(str, c['sugar_family_ids']):
            rr = int(rank_maps['sugar'][fid])
            p = float((rr - 1) / (len(rank_maps['sugar']) - 1))
            member_rows.append(('sugar', fid, rr, p))
        for fid in map(str, c['hdbscan_family_ids']):
            rr = int(rank_maps['hdbscan'][fid])
            p = float((rr - 1) / (len(rank_maps['hdbscan']) - 1))
            member_rows.append(('hdbscan', fid, rr, p))
        require(member_rows, 'empty component')
        best_member = min(member_rows, key=lambda x: (x[3], x[2], x[0], x[1]))
        evidence = float(best_member[3])
        reps.append({
            'component_id': str(c['component_id']),
            'component_evidence': evidence,
            'representative_family_id': own_rep,
            'representative_v31_rank': int(rank_maps[route][own_rep]),
            'representative_v31_percentile': float((rank_maps[route][own_rep] - 1) / (n_route - 1)),
            'component_member_count': int(c['member_count']),
            'component_sugar_member_count': int(c['sugar_member_count']),
            'component_hdbscan_member_count': int(c['hdbscan_member_count']),
            'best_evidence_route': best_member[0],
            'best_evidence_family_id': best_member[1],
            'best_evidence_v31_rank': int(best_member[2]),
            'best_evidence_percentile': float(best_member[3]),
        })
    primary_rows = sorted(reps, key=lambda r: (float(r['component_evidence']), int(r['representative_v31_rank']), str(r['component_id'])))
    primary = [str(r['representative_family_id']) for r in primary_rows]
    require(len(primary) == len(rep_ids) and len(primary) == len(set(primary)), f'{route} duplicate primary representative')
    secondary = [fid for fid in base_order if fid not in rep_ids]
    order = primary + secondary
    require(len(order) == len(base_order) and set(order) == set(base_order), f'{route} invalid v40 total order')
    for i, r in enumerate(primary_rows):
        r['v40_primary_position'] = i + 1
    return order, primary_rows


def evaluate_mode(sugar_root: Path, hdbscan_root: Path, truth_root: Path, ranker_source: Path, graph_file: Path, component_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(v22.sha(graph_file) == GRAPH_SHA256, 'pretruth graph file identity changed')
    require(v22.sha(component_file) == COMPONENT_SHA256, 'pretruth component file identity changed')
    graph = json.loads(graph_file.read_text())
    comp = json.loads(component_file.read_text())
    require(graph['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY' and graph['truth_accessed'] is False, 'invalid pretruth graph')
    require(comp['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY' and comp['truth_accessed'] is False, 'invalid pretruth components')
    require(comp['graph_sha256'] == GRAPH_SHA256 and int(comp['component_count']) == 196, 'component identity mismatch')
    require(int(comp['non_singleton_component_count']) == 113 and int(comp['singleton_component_count']) == 83, 'component count mismatch')
    require(v22.sha(ranker_source) == v24.RANKER_SOURCE_SHA, '#839 ranker source changed')
    roots = {'sugar': sugar_root, 'hdbscan': hdbscan_root}
    truth = {}
    frozen_eval = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((truth_root / f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route, year)] = json.loads((truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(ranker_source, 'frozen_839_v40_component_evidence')
    route_data = {}
    Xs = []
    y13s = []
    y14s = []
    groups = []
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
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and meta['feature_dimension'] == FEATURE_DIM, f'{route} invalid pretruth payload after truth')
        require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], f'{route} pretruth identity changed')
        require([str(f['family_id']) for f in fams] == ids, f'{route} family order changed')
        by = {y: truth[(route, y)] for y in v24.YEARS}
        eligible = v22.eligible_from_year_truth(by)
        hidden = {}
        hidden.update(by[2013])
        hidden.update(by[2014])
        base = [v22.family_truth(f, hidden, eligible) for f in fams]
        q13, q14, rg = [], [], []
        for i, (fam, t) in enumerate(zip(fams, base)):
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
        route_data[route] = {'meta': meta, 'fams': fams, 'ids': ids, 'centroids': C}

    require(graph['sugar_family_ids'] == route_data['sugar']['ids'], 'Sugar graph family identity changed')
    require(graph['hdbscan_family_ids'] == route_data['hdbscan']['ids'], 'HDB graph family identity changed')
    require(len(route_data['sugar']['ids']) == 267 and len(route_data['hdbscan']['ids']) == 229, 'route family counts changed')
    Xall = np.vstack(Xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM), 'stacked feature shape changed')
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    m13 = np.zeros(cursor, dtype=float)
    m14 = np.zeros(cursor, dtype=float)
    fold_diag = []
    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f'group leakage fold {fold}')
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
            require(pos.any() and neg.any(), f'{year} fold {fold} lacks positive/nonpositive references')
            P = Ztr[pos]
            N = Ztr[neg]
            for j, gi in enumerate(te_idx.tolist()):
                dpos = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))
                dneg = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))
                require(np.isfinite(dpos) and np.isfinite(dneg), f'nonfinite nearest distance {year} fold {fold}')
                out[gi] = dneg - dpos
            annual_refs[str(year)] = {'positive_references': int(pos.sum()), 'nonpositive_references': int(neg.sum())}
        fold_diag.append({'fold': fold, 'train_examples': int(tr.sum()), 'test_examples': int(te.sum()), 'zero_variance_features': int(np.sum(sd == 0.0)), 'annual_references': annual_refs})

    combined = np.minimum(m13, m14)
    require(np.all(np.isfinite(combined)), 'nonfinite exact v31 combined margin')
    base_orders = {}
    base_ranked = {}
    local_orders = {}
    for route in v24.ROUTES:
        lo, hi = offsets[route]
        rd = route_data[route]
        ids = rd['ids']
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(combined[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        local = [ids[i] for i in idx]
        fused = list(v19.fusion_orders(local, list(map(str, rd['meta']['v19_order'])))['rank_sum'])
        local_orders[route] = local
        base_orders[route] = fused
        base_ranked[route] = v22.rerank(rd['fams'], fused)

    parent_controls = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(base_ranked[route], truth[(route, year)], budget)
        exp = PARENT[(route, year)]
        require(abs(float(cur['macro_f1']) - exp[0]) < 1e-12 and int(cur['recovered_f1_gt_0_5']) == exp[1], f'v31 parent control mismatch {route} {year}')
        parent_controls.append({'comparator': route, 'year': year, **cur})

    rank_maps = {route: {fid: i + 1 for i, fid in enumerate(base_orders[route])} for route in v24.ROUTES}
    components = list(comp['components'])
    successor_orders = {}
    primary_rows = {}
    for route in v24.ROUTES:
        successor_orders[route], primary_rows[route] = build_v40_order(route, base_orders[route], components, rank_maps)
    successor_ranked = {route: v22.rerank(route_data[route]['fams'], successor_orders[route]) for route in v24.ROUTES}

    panels = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(successor_ranked[route], truth[(route, year)], budget)
        lit = frozen_eval[(route, year)]['comparator_summary']
        cm = float(cur['macro_f1'])
        cr = int(cur['recovered_f1_gt_0_5'])
        lm = float(lit['macro_f1'])
        lr = int(lit['recovered_f1_gt_0_5'])
        panels.append({'comparator': route, 'year': year, 'budget': budget, 'candidate_macro_f1': cm, 'literature_macro_f1': lm, 'candidate_recovered_f1_gt_0_5': cr, 'literature_recovered_f1_gt_0_5': lr, 'macro_f1_ratio': cm / lm if lm else float('inf'), 'recovery_ratio': cr / lr if lr else float('inf'), 'superiority_pair_pass': bool(cm > lm and cr >= lr)})
    wins = sum(int(r['superiority_pair_pass']) for r in panels)
    passed = bool(wins == 4)

    order_diag = {}
    for route in v24.ROUTES:
        old_rank = rank_maps[route]
        new_rank = {fid: i + 1 for i, fid in enumerate(successor_orders[route])}
        primary_ids = [str(r['representative_family_id']) for r in primary_rows[route]]
        moved_up = [fid for fid in successor_orders[route] if new_rank[fid] < old_rank[fid]]
        order_diag[route] = {'family_count': len(base_orders[route]), 'route_component_count': len(primary_ids), 'primary_representative_count': len(primary_ids), 'secondary_fragment_count': len(base_orders[route]) - len(primary_ids), 'moved_up_in_total_order_count': len(moved_up), 'v31_local_order_sha256': order_sha(local_orders[route]), 'v31_fused_order_sha256': order_sha(base_orders[route]), 'v40_total_order_sha256': order_sha(successor_orders[route]), 'component_evidence_rule': 'minimum normalized exact-v31 rank percentile over all Sugar/HDB members of frozen connected component', 'representative_rule': 'best own-route exact-v31 fused rank within component', 'primary_sort': '(component_evidence, representative_own_v31_rank, component_id)', 'secondary_rule': 'append all non-representatives in exact v31 fused order only after every route component representative'}

    freeze = {'verdict': 'NOT_FROZEN_V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_FAIL', 'reference_sha256': None}
    if passed:
        mu = np.mean(Xall, axis=0)
        sd = np.std(Xall, axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        path = output / 'v40_component_best_evidence_representative_reference.npz'
        np.savez_compressed(path, X=Xall, mean=mu, scale=scale, y13=(y13all > RECOVERY).astype(np.int8), y14=(y14all > RECOVERY).astype(np.int8), groups=np.asarray(groups, dtype=str))
        freeze = {'verdict': 'PASS_V40_FULL_EXPOSED_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_REFERENCE_FREEZE', 'reference_sha256': v22.sha(path), 'pretruth_graph_sha256': GRAPH_SHA256, 'pretruth_component_sha256': COMPONENT_SHA256, 'training_examples': cursor, 'training_groups': len(set(groups)), 'feature_dimension': FEATURE_DIM, 'k': 1, 'distance': 'ordinary Euclidean after full-training z-score for v31; frozen radius-1 connected-component identity for component ordering', 'annual_margin': 'd_nonpositive-d_positive', 'annual_combiner': 'min(margin_2013,margin_2014)', 'component_evidence': 'minimum normalized v31 rank percentile among all component members', 'representative_rule': 'smallest own-route v31 fused rank in component', 'in_sample_reference_score_used_for_promotion': False}
    (output / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_MODEL_FREEZE.json').write_text(json.dumps(freeze, indent=2, sort_keys=True) + '\n')

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V40_CONNECTED_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_V1',
        'verdict': 'PASS_V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'rank each frozen connected component once by best normalized exact-v31 member evidence and emit one best own-route representative per component before secondary fragments',
        'authorizing_diagnostic': '#1072 connected-component closure diagnostic; no component score/order/selector evaluated there',
        'pretruth_graph_sha256': GRAPH_SHA256,
        'pretruth_component_sha256': COMPONENT_SHA256,
        'component_count': int(comp['component_count']),
        'non_singleton_component_count': int(comp['non_singleton_component_count']),
        'singleton_component_count': int(comp['singleton_component_count']),
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': parent_controls,
        'feature_dimension': FEATURE_DIM,
        'recovery_f1_threshold': RECOVERY,
        'nearest_k': 1,
        'v31_distance': 'ordinary Euclidean across all 71 fold-training standardized dimensions',
        'v31_annual_margin': 'd_nonpositive-d_positive',
        'v31_annual_combiner': 'min(margin_2013,margin_2014)',
        'component_evidence': 'minimum normalized exact-v31 rank percentile over all members of frozen component',
        'component_representative': 'own-route member with smallest exact-v31 fused rank',
        'primary_order': 'all route component representatives sorted by (component_evidence, own representative v31 rank, component_id)',
        'secondary_order': 'remaining fragments in exact v31 fused order after all route component representatives',
        'component_rule_symmetric_across_routes': True,
        'component_rule_budget_dependent': False,
        'component_rule_year_dependent': False,
        'component_score_coefficient': None,
        'strict_whole_shower_oof': True,
        'candidate_membership_changed': False,
        'candidate_generation_changed': False,
        'pretruth_feature_changed': False,
        'diversity': {'lambda': 0.8, 'scale': 1.0},
        'v31_fusion': 'one equal rank-sum with exact v19 before component ordering',
        'promotion_variant': VARIANT,
        'panel_wins': wins,
        'panels': panels,
        'fold_diagnostics': fold_diag,
        'order_diagnostics': order_diag,
        'primary_component_rows': primary_rows,
        'full_model_freeze': freeze,
        'radius_search': False,
        'metric_search': False,
        'feature_search': False,
        'within_route_edges_added': False,
        'graph_pruning': False,
        'graph_expansion': False,
        'component_size_threshold_search': False,
        'component_definition_search': False,
        'component_evidence_aggregation_search': False,
        'component_best_k_search': False,
        'component_mean_median_harmonic_search': False,
        'representative_family_search': False,
        'route_specific_rule': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'transfer_coefficient_search': False,
        'transfer_threshold_search': False,
        'overlap_weight_search': False,
        'jaccard_weight_search': False,
        'distance_weight_search': False,
        'graph_propagation_search': False,
        'secondary_insertion_search': False,
        'k_search': False,
        'scaling_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'oracle_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels, 'order_diagnostics': order_diag, 'full_model_freeze': freeze}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    g = sub.add_parser('pretruth')
    g.add_argument('--sugar-root', type=Path, required=True)
    g.add_argument('--hdbscan-root', type=Path, required=True)
    g.add_argument('--output', type=Path, required=True)
    e = sub.add_parser('evaluate')
    e.add_argument('--sugar-root', type=Path, required=True)
    e.add_argument('--hdbscan-root', type=Path, required=True)
    e.add_argument('--truth-root', type=Path, required=True)
    e.add_argument('--ranker-source', type=Path, required=True)
    e.add_argument('--graph-file', type=Path, required=True)
    e.add_argument('--component-file', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'pretruth':
        return pretruth_mode(a.sugar_root, a.hdbscan_root, a.output)
    return evaluate_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.graph_file, a.component_file, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

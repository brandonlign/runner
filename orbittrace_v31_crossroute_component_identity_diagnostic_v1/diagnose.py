#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
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
    ('sugar', 2013): (0.2719801488280529, 16),
    ('sugar', 2014): (0.31529041952487225, 17),
    ('hdbscan', 2013): (0.14888037368183737, 9),
    ('hdbscan', 2014): (0.15198123772301594, 9),
}


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


def graph_and_components_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    _, _, Cs, sids = load_pretruth(sugar_root)
    _, _, Ch, hids = load_pretruth(hdbscan_root)
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

    nodes = [f'SUGAR/{fid}' for fid in sids] + [f'HDB/{fid}' for fid in hids]
    adj: dict[str, set[str]] = {n: set() for n in nodes}
    for hi, si, _ in edges:
        hn = f'HDB/{hids[int(hi)]}'
        sn = f'SUGAR/{sids[int(si)]}'
        adj[hn].add(sn)
        adj[sn].add(hn)

    seen: set[str] = set()
    components = []
    node_to_component: dict[str, str] = {}
    for start in sorted(nodes):
        if start in seen:
            continue
        stack = [start]
        members: list[str] = []
        seen.add(start)
        while stack:
            cur = stack.pop()
            members.append(cur)
            for nxt in sorted(adj[cur], reverse=True):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        members = sorted(members)
        cid = hashlib.sha256('\n'.join(members).encode()).hexdigest()
        for n in members:
            node_to_component[n] = cid
        components.append({
            'component_id': cid,
            'members': members,
            'member_count': len(members),
            'sugar_member_count': sum(m.startswith('SUGAR/') for m in members),
            'hdb_member_count': sum(m.startswith('HDB/') for m in members),
        })
    components.sort(key=lambda c: c['component_id'])
    require(len(node_to_component) == len(nodes), 'component assignment incomplete')
    cresult = {
        'verdict': 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_IDENTITY',
        'scientific_role': 'PRETRUTH_COMPONENT_ASSIGNMENT_ONLY',
        'source_graph_sha256': GRAPH_SHA256,
        'component_rule': 'ordinary undirected connected components on exact bipartite radius-1 graph; isolated candidates are singleton components',
        'component_id_rule': 'sha256(newline-joined lexicographically sorted node keys)',
        'component_count': len(components),
        'components': components,
        'node_to_component': node_to_component,
        'truth_accessed': False,
        'radius_search': False,
        'metric_search': False,
        'edge_filter_search': False,
        'hop_search': False,
        'neg_handling_search': False,
        'component_size_threshold_search': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    cpath = output / 'CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_IDENTITY.json'
    cpath.write_text(json.dumps(cresult, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'graph_verdict': graph['verdict'], 'graph_sha256': v22.sha(gpath), 'component_verdict': cresult['verdict'], 'component_count': len(components), 'component_sha256': v22.sha(cpath)}, indent=2, sort_keys=True))
    return 0


def diagnose_mode(sugar_root: Path, hdbscan_root: Path, truth_root: Path, ranker_source: Path, graph_file: Path, component_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(v22.sha(graph_file) == GRAPH_SHA256, 'pretruth graph file identity changed')
    graph = json.loads(graph_file.read_text())
    comp = json.loads(component_file.read_text())
    require(graph['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY' and graph['truth_accessed'] is False, 'invalid pretruth graph')
    require(comp['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_IDENTITY' and comp['truth_accessed'] is False, 'invalid pretruth component assignment')
    require(comp['source_graph_sha256'] == GRAPH_SHA256, 'component graph source changed')
    require(v22.sha(ranker_source) == v24.RANKER_SOURCE_SHA, '#839 ranker source changed')
    roots = {'sugar': sugar_root, 'hdbscan': hdbscan_root}

    truth = {}
    frozen = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((truth_root / f'truth_{route}_{year}.json').read_text())
        frozen[(route, year)] = json.loads((truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(ranker_source, 'frozen_839_crossroute_component_diag')
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
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and meta['feature_dimension'] == FEATURE_DIM, f'{route} invalid pretruth payload after truth')
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
        route_data[route] = {'meta': meta, 'fams': fams, 'ids': ids, 'centroids': C, 'groups': rg, 'y13': np.asarray(q13, float), 'y14': np.asarray(q14, float)}

    require(graph['sugar_family_ids'] == route_data['sugar']['ids'] and graph['hdbscan_family_ids'] == route_data['hdbscan']['ids'], 'graph family identity changed')
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
            require(pos.any() and neg.any(), f'fold {fold} missing annual references')
            P = Ztr[pos]; N = Ztr[neg]
            for j, gi in enumerate(teidx.tolist()):
                out[gi] = float(np.min(np.linalg.norm(N - Zte[j], axis=1)) - np.min(np.linalg.norm(P - Zte[j], axis=1)))
    combined = np.minimum(m13, m14)

    orders = {}; ranked = {}
    for route in v24.ROUTES:
        lo, hi = offsets[route]; rd = route_data[route]; ids = rd['ids']
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

    node_to_component = comp['node_to_component']
    truth_group_by_node: dict[str, str] = {}
    for i, fid in enumerate(route_data['sugar']['ids']):
        truth_group_by_node[f'SUGAR/{fid}'] = route_data['sugar']['groups'][i]
    for i, fid in enumerate(route_data['hdbscan']['ids']):
        truth_group_by_node[f'HDB/{fid}'] = route_data['hdbscan']['groups'][i]
    component_rows = []
    impure_components = 0
    impure_candidates = 0
    for c in comp['components']:
        members = list(map(str, c['members']))
        gs = [truth_group_by_node[n] for n in members]
        showers = sorted({g for g in gs if not g.startswith('NEG/')})
        neg_present = any(g.startswith('NEG/') for g in gs)
        pure = len(showers) <= 1
        if not pure:
            impure_components += 1
            impure_candidates += len(members)
        component_rows.append({'component_id': c['component_id'], 'member_count': len(members), 'sugar_member_count': int(c['sugar_member_count']), 'hdb_member_count': int(c['hdb_member_count']), 'distinct_nonneg_strict_shower_group_count': len(showers), 'nonneg_strict_shower_groups': showers, 'neg_present': neg_present, 'strict_shower_pure': pure})

    hrd = route_data['hdbscan']
    h_rank = {fid: i + 1 for i, fid in enumerate(orders['hdbscan'])}
    annual = {}
    for year, yvals in ((2013, hrd['y13']), (2014, hrd['y14'])):
        budget = int(frozen[('hdbscan', year)]['candidate_budget']['comparator_budget'])
        top = orders['hdbscan'][:budget]
        top_components = [node_to_component[f'HDB/{fid}'] for fid in top]
        counts = Counter(top_components)
        unique = len(counts)
        repeated = [{'component_id': cid, 'slots': int(n), 'families': [fid for fid in top if node_to_component[f'HDB/{fid}'] == cid]} for cid, n in sorted(counts.items()) if n > 1]
        group_candidates = defaultdict(list)
        for i, fid in enumerate(hrd['ids']):
            g = hrd['groups'][i]
            if g.startswith('SHOWER/') and float(yvals[i]) > RECOVERY:
                group_candidates[g].append(fid)
        rows = []
        for g, fids in sorted(group_candidates.items()):
            rep = min(fids, key=lambda fid: (h_rank[fid], fid))
            cid = node_to_component[f'HDB/{rep}']
            surfaced = h_rank[rep] <= budget
            rows.append({'group': g, 'representative_family_id': rep, 'v31_fused_rank': int(h_rank[rep]), 'surfaced': bool(surfaced), 'component_id': cid, 'component_represented_in_top_budget': bool(cid in counts)})
        missed = [r for r in rows if not r['surfaced']]
        absent = [r for r in missed if not r['component_represented_in_top_budget']]
        represented = [r for r in missed if r['component_represented_in_top_budget']]
        annual[str(year)] = {'budget': budget, 'unique_component_count_in_top_budget': unique, 'duplicate_component_slots': int(budget - unique), 'repeated_component_rows': repeated, 'annual_recoverable_groups': len(rows), 'surfaced_recoverable_groups': int(sum(r['surfaced'] for r in rows)), 'missed_recoverable_groups': len(missed), 'missed_component_absent_count': len(absent), 'missed_component_represented_count': len(represented), 'recoverable_group_rows': rows}

    direction = bool(impure_components == 0 and annual['2013']['duplicate_component_slots'] >= 2 and annual['2014']['duplicate_component_slots'] >= 1 and annual['2013']['missed_component_absent_count'] >= 2 and annual['2014']['missed_component_absent_count'] >= 1)
    result = {
        'verdict': 'PASS_V31_CROSSROUTE_COMPONENT_IDENTITY_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_COMPONENT_SELECTOR_EVALUATED',
        'source_graph_sha256': GRAPH_SHA256,
        'pretruth_component_sha256': v22.sha(component_file),
        'v31_reproduction': reproduction,
        'component_count': int(comp['component_count']),
        'component_truth_purity': {'impure_multishower_component_count': impure_components, 'candidates_in_impure_multishower_components': impure_candidates, 'strict_shower_pure_component_count': int(comp['component_count']) - impure_components},
        'component_rows': component_rows,
        'annual_hdb_diagnostics': annual,
        'predeclared_component_direction_supported': direction,
        'predeclared_requirements': {'zero_multishower_components': impure_components == 0, 'hdb_2013_duplicate_slots_ge_2': annual['2013']['duplicate_component_slots'] >= 2, 'hdb_2014_duplicate_slots_ge_1': annual['2014']['duplicate_component_slots'] >= 1, 'hdb_2013_missed_absent_components_ge_2': annual['2013']['missed_component_absent_count'] >= 2, 'hdb_2014_missed_absent_components_ge_1': annual['2014']['missed_component_absent_count'] >= 1},
        'new_rank_or_score_evaluated': False,
        'component_representative_rule_evaluated': False,
        'component_cap_selected': False,
        'radius_search': False,
        'metric_search': False,
        'edge_filter_search': False,
        'hop_search': False,
        'neg_handling_search': False,
        'component_size_threshold_search': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
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
    (output / 'V31_CROSSROUTE_COMPONENT_IDENTITY_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'component_count': result['component_count'], 'component_truth_purity': result['component_truth_purity'], 'annual_hdb_diagnostics': {y: {k: v for k, v in d.items() if k not in ('repeated_component_rows','recoverable_group_rows')} for y, d in annual.items()}, 'predeclared_component_direction_supported': direction, 'predeclared_requirements': result['predeclared_requirements']}, indent=2, sort_keys=True, allow_nan=False))
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
        return graph_and_components_mode(a.sugar_root, a.hdbscan_root, a.output)
    return diagnose_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.graph_file, a.component_file, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

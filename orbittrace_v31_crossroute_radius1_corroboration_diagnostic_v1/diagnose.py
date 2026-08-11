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
EXPECTED_V31 = {
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


def graph_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    s, _, Cs, sids = load_pretruth(sugar_root)
    h, _, Ch, hids = load_pretruth(hdbscan_root)
    edges = []
    h_to_s = [[] for _ in hids]
    s_to_h = [[] for _ in sids]
    for hi in range(len(hids)):
        for si in range(len(sids)):
            d = max(annual_distance(Ch[hi, :4], Cs[si, :4]), annual_distance(Ch[hi, 4:], Cs[si, 4:]))
            if d <= RADIUS:
                edges.append([hi, si, float(d)])
                h_to_s[hi].append(si)
                s_to_h[si].append(hi)
    result = {
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
    (output / 'CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'edge_count': len(edges)}, indent=2, sort_keys=True))
    return 0


def diagnose_mode(sugar_root: Path, hdbscan_root: Path, truth_root: Path, ranker_source: Path, graph_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    pre = json.loads(graph_file.read_text())
    require(pre['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY' and pre['truth_accessed'] is False and float(pre['radius']) == RADIUS, 'invalid cross-route pretruth graph')
    require(v22.sha(ranker_source) == v24.RANKER_SOURCE_SHA, '#839 ranker source changed')
    roots = {'sugar': sugar_root, 'hdbscan': hdbscan_root}

    truth = {}
    frozen = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((truth_root / f'truth_{route}_{year}.json').read_text())
        frozen[(route, year)] = json.loads((truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(ranker_source, 'frozen_839_crossroute_radius1_diag')
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

    require(pre['sugar_family_ids'] == route_data['sugar']['ids'] and pre['hdbscan_family_ids'] == route_data['hdbscan']['ids'], 'cross-route graph family identity changed after truth')
    Xall = np.vstack(Xs); y13all = np.concatenate(y13s); y14all = np.concatenate(y14s); groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM), 'stacked feature shape changed')
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    m13 = np.zeros(cursor, float); m14 = np.zeros(cursor, float)
    for fold in range(5):
        tr = folds != fold; te = folds == fold
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

    orders = {}; ranks = {}; ranked = {}
    for route in v24.ROUTES:
        lo, hi = offsets[route]; rd = route_data[route]; ids = rd['ids']
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(combined[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        local = [ids[i] for i in idx]
        fused = list(v19.fusion_orders(local, list(map(str, rd['meta']['v19_order'])))['rank_sum'])
        orders[route] = fused; ranks[route] = {fid: i + 1 for i, fid in enumerate(fused)}; ranked[route] = v22.rerank(rd['fams'], fused)

    reproduction = []
    for route, year in v24.PANELS:
        budget = int(frozen[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(ranked[route], truth[(route, year)], budget)
        exp = EXPECTED_V31[(route, year)]
        require(abs(float(cur['macro_f1']) - exp[0]) < 1e-12 and int(cur['recovered_f1_gt_0_5']) == exp[1], f'v31 reproduction failed {route} {year}')
        reproduction.append({'comparator': route, 'year': year, **cur})

    srd, hrd = route_data['sugar'], route_data['hdbscan']
    edges = pre['edges']; hadj = pre['hdbscan_to_sugar_adjacency']
    require(len(hadj) == len(hrd['ids']), 'cross-route HDB adjacency length changed')
    purity = {'total_edges': len(edges), 'same_shower_group': 0, 'different_shower_groups': 0, 'involving_neg': 0}
    for hi, si, _ in edges:
        hg = hrd['groups'][int(hi)]; sg = srd['groups'][int(si)]
        if hg.startswith('NEG/') or sg.startswith('NEG/'):
            purity['involving_neg'] += 1
        elif hg == sg:
            purity['same_shower_group'] += 1
        else:
            purity['different_shower_groups'] += 1
    den = max(1, purity['total_edges'])
    purity['same_shower_fraction'] = purity['same_shower_group'] / den
    purity['different_shower_fraction'] = purity['different_shower_groups'] / den
    purity['neg_involved_fraction'] = purity['involving_neg'] / den

    annual = {}
    for year in (2013, 2014):
        hy = hrd['y13'] if year == 2013 else hrd['y14']
        hbudget = int(frozen[('hdbscan', year)]['candidate_budget']['comparator_budget'])
        sbudget = int(frozen[('sugar', year)]['candidate_budget']['comparator_budget'])
        group_to_positive = defaultdict(list)
        for hi, fid in enumerate(hrd['ids']):
            g = hrd['groups'][hi]
            if g.startswith('SHOWER/') and float(hy[hi]) > RECOVERY:
                group_to_positive[g].append(hi)
        rows = []
        for g, hinds in sorted(group_to_positive.items()):
            hrep = min(hinds, key=lambda i: (ranks['hdbscan'][hrd['ids'][i]], hrd['ids'][i]))
            candidate_links = []
            for hi in hinds:
                for si in hadj[hi]:
                    candidate_links.append((ranks['sugar'][srd['ids'][si]], ranks['hdbscan'][hrd['ids'][hi]], srd['ids'][si], hrd['ids'][hi], srd['groups'][si]))
            if candidate_links:
                best = min(candidate_links)
                best_srank, linked_hrank, sfid, hfid, sg = best
                relation = 'SAME_SHOWER' if sg == g else ('NEG' if sg.startswith('NEG/') else 'OTHER_SHOWER')
            else:
                best_srank = linked_hrank = None; sfid = hfid = None; relation = 'NO_EDGE'
            rows.append({
                'group': g,
                'hdb_representative_family_id': hrd['ids'][hrep],
                'hdb_representative_rank': int(ranks['hdbscan'][hrd['ids'][hrep]]),
                'surfaced_hdb': bool(ranks['hdbscan'][hrd['ids'][hrep]] <= hbudget),
                'recoverable_hdb_candidates': len(hinds),
                'crossroute_edges_from_recoverable_candidates': len(candidate_links),
                'best_sugar_neighbor_family_id': sfid,
                'best_sugar_neighbor_rank': None if best_srank is None else int(best_srank),
                'linked_hdb_family_id': hfid,
                'linked_hdb_rank': None if linked_hrank is None else int(linked_hrank),
                'best_neighbor_relation': relation,
                'best_sugar_neighbor_in_sugar_budget': bool(best_srank is not None and best_srank <= sbudget),
                'best_sugar_neighbor_in_hdb_sized_prefix': bool(best_srank is not None and best_srank <= hbudget),
            })
        surfaced = [r for r in rows if r['surfaced_hdb']]; missed = [r for r in rows if not r['surfaced_hdb']]
        def summary(rs: list[dict[str, Any]]) -> dict[str, Any]:
            ranks_found = [r['best_sugar_neighbor_rank'] for r in rs if r['best_sugar_neighbor_rank'] is not None]
            return {
                'groups': len(rs),
                'groups_with_any_crossroute_edge': int(sum(r['best_sugar_neighbor_rank'] is not None for r in rs)),
                'groups_with_same_shower_best_neighbor': int(sum(r['best_neighbor_relation'] == 'SAME_SHOWER' for r in rs)),
                'groups_with_sugar_neighbor_in_sugar_budget': int(sum(r['best_sugar_neighbor_in_sugar_budget'] for r in rs)),
                'groups_with_sugar_neighbor_in_hdb_sized_prefix': int(sum(r['best_sugar_neighbor_in_hdb_sized_prefix'] for r in rs)),
                'median_best_sugar_neighbor_rank': None if not ranks_found else float(np.median(np.asarray(ranks_found, float))),
            }
        annual[str(year)] = {
            'hdb_budget': hbudget,
            'sugar_budget': sbudget,
            'annual_recoverable_hdb_groups': len(rows),
            'surfaced_hdb_groups': len(surfaced),
            'missed_hdb_groups': len(missed),
            'surfaced_summary': summary(surfaced),
            'missed_summary': summary(missed),
            'groups': rows,
        }

    result = {
        'verdict': 'PASS_V31_CROSSROUTE_RADIUS1_CORROBORATION_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CROSSROUTE_RANK_EVALUATED',
        'question': 'whether exact inherited radius-1 Sugar-HDB cross-route neighbors provide independent high-ranked corroboration for HDB recoverable groups missed by exact v31',
        'pretruth_crossroute_graph': {'radius': RADIUS, 'edge_count': len(edges), 'distance': pre['distance']},
        'v31_reproduction': reproduction,
        'v31_order_sha256': {r: order_sha(orders[r]) for r in v24.ROUTES},
        'global_crossroute_edge_purity': purity,
        'annual_diagnostics': annual,
        'crossroute_score_or_rerank_evaluated': False,
        'successor_selected': False,
        'radius_search': False,
        'metric_search': False,
        'neighbor_aggregation_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V31_CROSSROUTE_RADIUS1_CORROBORATION_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    compact = {'verdict': result['verdict'], 'edge_purity': purity, 'annual': {y: {k:v for k,v in d.items() if k != 'groups'} for y,d in annual.items()}}
    print(json.dumps(compact, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    g = sub.add_parser('graph'); g.add_argument('--sugar-root', type=Path, required=True); g.add_argument('--hdbscan-root', type=Path, required=True); g.add_argument('--output', type=Path, required=True)
    d = sub.add_parser('diagnose'); d.add_argument('--sugar-root', type=Path, required=True); d.add_argument('--hdbscan-root', type=Path, required=True); d.add_argument('--truth-root', type=Path, required=True); d.add_argument('--ranker-source', type=Path, required=True); d.add_argument('--graph-file', type=Path, required=True); d.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'graph': return graph_mode(a.sugar_root, a.hdbscan_root, a.output)
    return diagnose_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.graph_file, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

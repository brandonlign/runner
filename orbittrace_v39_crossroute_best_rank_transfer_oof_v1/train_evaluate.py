#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
VARIANT = 'symmetric_crossroute_best_rank_percentile_transfer_v1'
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


def graph_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    s, _, Cs, sids = load_pretruth(sugar_root)
    h, _, Ch, hids = load_pretruth(hdbscan_root)
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
    path = output / 'CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    sha = v22.sha(path)
    require(len(edges) == 2334, 'cross-route radius-1 edge count changed')
    require(sha == GRAPH_SHA256, 'cross-route radius-1 graph serialized identity changed')
    print(json.dumps({'verdict': result['verdict'], 'edge_count': len(edges), 'sha256': sha}, indent=2, sort_keys=True))
    return 0


def best_rank_transfer(
    route: str,
    ids: list[str],
    base_order: list[str],
    other_ids: list[str],
    other_order: list[str],
    adjacency: list[list[int]],
) -> tuple[list[str], list[dict[str, Any]]]:
    require(len(adjacency) == len(ids), f'{route} adjacency length mismatch')
    base_rank = {fid: i + 1 for i, fid in enumerate(base_order)}
    other_rank = {fid: i + 1 for i, fid in enumerate(other_order)}
    require(set(base_rank) == set(ids) and set(other_rank) == set(other_ids), f'{route} rank universe mismatch')
    n_self = len(ids)
    n_other = len(other_ids)
    require(n_self > 1 and n_other > 1, 'route universe too small')
    rows = []
    for i, fid in enumerate(ids):
        rself = int(base_rank[fid])
        pself = float((rself - 1) / (n_self - 1))
        neigh = adjacency[i]
        if neigh:
            nranks = [(int(other_rank[other_ids[int(j)]]), other_ids[int(j)]) for j in neigh]
            best_other_rank, best_other_fid = min(nranks)
            pcross = float((best_other_rank - 1) / (n_other - 1))
            peff = float(min(pself, pcross))
        else:
            best_other_rank = None
            best_other_fid = None
            pcross = None
            peff = pself
        require(np.isfinite(pself) and np.isfinite(peff), f'{route} nonfinite transferred percentile')
        require(peff <= pself + 1e-15, f'{route} transfer worsened candidate')
        rows.append({
            'family_id': fid,
            'v31_fused_rank': rself,
            'p_self': pself,
            'crossroute_neighbor_count': len(neigh),
            'best_crossroute_neighbor_family_id': best_other_fid,
            'best_crossroute_neighbor_v31_rank': best_other_rank,
            'p_cross': pcross,
            'p_v39': peff,
            'improved_by_crossroute': bool(pcross is not None and pcross < pself),
        })
    by_id = {r['family_id']: r for r in rows}
    order = sorted(ids, key=lambda fid: (float(by_id[fid]['p_v39']), int(by_id[fid]['v31_fused_rank']), fid))
    require(len(order) == len(ids) and set(order) == set(ids), f'{route} invalid transferred total order')
    return order, rows


def evaluate_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(v22.sha(graph_file) == GRAPH_SHA256, 'pretruth graph file identity changed')
    graph = json.loads(graph_file.read_text())
    require(graph['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY', 'invalid pretruth graph verdict')
    require(graph['scientific_role'] == 'PRETRUTH_CROSS_ROUTE_GRAPH_IDENTITY_ONLY' and graph['truth_accessed'] is False, 'graph is not pretruth-only')
    require(float(graph['radius']) == RADIUS and int(graph['edge_count']) == 2334, 'pretruth graph definition changed')
    require(graph['radius_search'] is False and graph['metric_search'] is False, 'graph search flags changed')
    require(v22.sha(ranker_source) == v24.RANKER_SOURCE_SHA, '#839 ranker source changed')
    roots = {'sugar': sugar_root, 'hdbscan': hdbscan_root}

    truth: dict[tuple[str, int], dict] = {}
    frozen_eval: dict[tuple[str, int], dict] = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((truth_root / f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route, year)] = json.loads((truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(ranker_source, 'frozen_839_v39_crossroute_best_rank')
    route_data: dict[str, dict[str, Any]] = {}
    Xs: list[np.ndarray] = []
    y13s: list[np.ndarray] = []
    y14s: list[np.ndarray] = []
    groups: list[str] = []
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
    base_orders: dict[str, list[str]] = {}
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

    successor_orders: dict[str, list[str]] = {}
    transfer_rows: dict[str, list[dict[str, Any]]] = {}
    successor_orders['sugar'], transfer_rows['sugar'] = best_rank_transfer(
        'sugar', route_data['sugar']['ids'], base_orders['sugar'],
        route_data['hdbscan']['ids'], base_orders['hdbscan'],
        graph['sugar_to_hdbscan_adjacency'],
    )
    successor_orders['hdbscan'], transfer_rows['hdbscan'] = best_rank_transfer(
        'hdbscan', route_data['hdbscan']['ids'], base_orders['hdbscan'],
        route_data['sugar']['ids'], base_orders['sugar'],
        graph['hdbscan_to_sugar_adjacency'],
    )
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
        panels.append({
            'comparator': route,
            'year': year,
            'budget': budget,
            'candidate_macro_f1': cm,
            'literature_macro_f1': lm,
            'candidate_recovered_f1_gt_0_5': cr,
            'literature_recovered_f1_gt_0_5': lr,
            'macro_f1_ratio': cm / lm if lm else float('inf'),
            'recovery_ratio': cr / lr if lr else float('inf'),
            'superiority_pair_pass': bool(cm > lm and cr >= lr),
        })
    wins = sum(int(r['superiority_pair_pass']) for r in panels)
    passed = bool(wins == 4)

    order_diag = {}
    for route in v24.ROUTES:
        rows = transfer_rows[route]
        by_id = {r['family_id']: r for r in rows}
        old_rank = {fid: i + 1 for i, fid in enumerate(base_orders[route])}
        new_rank = {fid: i + 1 for i, fid in enumerate(successor_orders[route])}
        linked = [r for r in rows if r['crossroute_neighbor_count'] > 0]
        improved = [r for r in rows if r['improved_by_crossroute']]
        moved_up = [fid for fid in successor_orders[route] if new_rank[fid] < old_rank[fid]]
        order_diag[route] = {
            'family_count': len(rows),
            'linked_family_count': len(linked),
            'crossroute_percentile_improved_family_count': len(improved),
            'moved_up_in_total_order_count': len(moved_up),
            'v31_local_order_sha256': order_sha(local_orders[route]),
            'v31_fused_order_sha256': order_sha(base_orders[route]),
            'v39_total_order_sha256': order_sha(successor_orders[route]),
            'maximum_percentile_improvement': float(max((float(r['p_self']) - float(r['p_v39']) for r in rows), default=0.0)),
            'mean_percentile_improvement': float(np.mean([float(r['p_self']) - float(r['p_v39']) for r in rows])),
            'transfer_rule': 'p_v39=min(p_self,min cross-route-neighbor v31 percentile); unlinked p_v39=p_self',
            'tie_break': 'lower own exact v31 fused rank, then family id',
        }

    freeze = {'verdict': 'NOT_FROZEN_V39_CROSSROUTE_BEST_RANK_TRANSFER_FAIL', 'reference_sha256': None}
    if passed:
        mu = np.mean(Xall, axis=0)
        sd = np.std(Xall, axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        path = output / 'v39_crossroute_best_rank_transfer_reference.npz'
        np.savez_compressed(
            path,
            X=Xall,
            mean=mu,
            scale=scale,
            y13=(y13all > RECOVERY).astype(np.int8),
            y14=(y14all > RECOVERY).astype(np.int8),
            groups=np.asarray(groups, dtype=str),
        )
        freeze = {
            'verdict': 'PASS_V39_FULL_EXPOSED_CROSSROUTE_BEST_RANK_TRANSFER_REFERENCE_FREEZE',
            'reference_sha256': v22.sha(path),
            'pretruth_graph_sha256': GRAPH_SHA256,
            'training_examples': cursor,
            'training_groups': len(set(groups)),
            'feature_dimension': FEATURE_DIM,
            'k': 1,
            'distance': 'ordinary Euclidean after full-training z-score for v31; frozen radius-1 cross-route centroid graph for transfer',
            'annual_margin': 'd_nonpositive-d_positive',
            'annual_combiner': 'min(margin_2013,margin_2014)',
            'transfer_rule': 'symmetric minimum of own normalized v31 rank percentile and best radius-1 cross-route-neighbor normalized v31 rank percentile',
            'in_sample_reference_score_used_for_promotion': False,
        }
    (output / 'V39_CROSSROUTE_BEST_RANK_TRANSFER_MODEL_FREEZE.json').write_text(json.dumps(freeze, indent=2, sort_keys=True) + '\n')

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V39_SYMMETRIC_CROSSROUTE_BEST_RANK_TRANSFER_V1',
        'verdict': 'PASS_V39_CROSSROUTE_BEST_RANK_TRANSFER_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V39_CROSSROUTE_BEST_RANK_TRANSFER_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'symmetric best-route normalized v31 rank-percentile transfer along exact frozen radius-1 cross-route edges',
        'authorizing_diagnostics': ['#1064 frozen cross-route radius-1 physical correspondence', '#1066 positive cross-route rank-disagreement direction in both years'],
        'pretruth_graph_sha256': GRAPH_SHA256,
        'pretruth_graph_edge_count': 2334,
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': parent_controls,
        'feature_dimension': FEATURE_DIM,
        'recovery_f1_threshold': RECOVERY,
        'nearest_k': 1,
        'v31_distance': 'ordinary Euclidean across all 71 fold-training standardized dimensions',
        'v31_annual_margin': 'd_nonpositive-d_positive',
        'v31_annual_combiner': 'min(margin_2013,margin_2014)',
        'transfer_score': 'p_v39=min(p_self,p_cross_best) for linked candidates; p_self when unlinked',
        'transfer_symmetric_across_routes': True,
        'transfer_budget_dependent': False,
        'transfer_coefficient': None,
        'strict_whole_shower_oof': True,
        'candidate_membership_changed': False,
        'candidate_generation_changed': False,
        'pretruth_feature_changed': False,
        'diversity': {'lambda': 0.8, 'scale': 1.0},
        'v31_fusion': 'one equal rank-sum with exact v19 before cross-route transfer',
        'promotion_variant': VARIANT,
        'panel_wins': wins,
        'panels': panels,
        'fold_diagnostics': fold_diag,
        'order_diagnostics': order_diag,
        'transfer_rows': transfer_rows,
        'full_model_freeze': freeze,
        'route_specific_exception': False,
        'averaging_weight_search': False,
        'additive_penalty_search': False,
        'multiplicative_penalty_search': False,
        'positive_gap_threshold_search': False,
        'overlap_threshold_search': False,
        'radius_search': False,
        'metric_search': False,
        'feature_search': False,
        'distance_weight_search': False,
        'jaccard_weight_search': False,
        'clipping_search': False,
        'nonlinear_transform_search': False,
        'neighbor_count_bonus_search': False,
        'component_size_bonus_search': False,
        'connected_component_closure': False,
        'graph_propagation_search': False,
        'hard_dedup_search': False,
        'budget_specific_rule': False,
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
    (output / 'V39_CROSSROUTE_BEST_RANK_TRANSFER_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels, 'order_diagnostics': order_diag, 'full_model_freeze': freeze}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    g = sub.add_parser('graph')
    g.add_argument('--sugar-root', type=Path, required=True)
    g.add_argument('--hdbscan-root', type=Path, required=True)
    g.add_argument('--output', type=Path, required=True)
    e = sub.add_parser('evaluate')
    e.add_argument('--sugar-root', type=Path, required=True)
    e.add_argument('--hdbscan-root', type=Path, required=True)
    e.add_argument('--truth-root', type=Path, required=True)
    e.add_argument('--ranker-source', type=Path, required=True)
    e.add_argument('--graph-file', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'graph':
        return graph_mode(a.sugar_root, a.hdbscan_root, a.output)
    return evaluate_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.graph_file, a.output)


if __name__ == '__main__':
    raise SystemExit(main())

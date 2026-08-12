#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

ROUTES = ('sugar', 'hdbscan')
YEARS = (2013, 2014)
BLIND = (20.0, 55.0)
EXPECTED_COUNTS = {'sugar': 267, 'hdbscan': 229}
EXPECTED_PARENT_SHA = {
    'sugar': '5b3d27e11079f36148bbfb8bfdab60882fae380143fcfd84c6dc290c53295aae',
    'hdbscan': '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d',
}
EXPECTED_V31 = {
    ('sugar', 2013): (0.2719801488280529, 16),
    ('sugar', 2014): (0.31529041952487225, 17),
    ('hdbscan', 2013): (0.14888037368183737, 9),
    ('hdbscan', 2014): (0.15198123772301594, 9),
}
EXPECTED_LITERATURE = {
    ('sugar', 2013): (0.20372657466522806, 13, 13),
    ('sugar', 2014): (0.25901527732153334, 15, 15),
    ('hdbscan', 2013): (0.16813025050497152, 10, 10),
    ('hdbscan', 2014): (0.15689595582646423, 9, 9),
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(x: np.ndarray) -> str:
    a = np.ascontiguousarray(x)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(json.dumps(list(a.shape), separators=(',', ':')).encode())
    h.update(a.tobytes(order='C'))
    return h.hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256('\n'.join(map(str, order)).encode()).hexdigest()


def signed_circular_delta(a: float, b: float) -> float:
    return (float(a) - float(b) + 180.0) % 360.0 - 180.0


def unit(lon_deg: float, lat_deg: float) -> np.ndarray:
    lon = math.radians(float(lon_deg))
    lat = math.radians(float(lat_deg))
    return np.asarray([
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    ], dtype=float)


def angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    return math.degrees(math.acos(float(np.clip(np.dot(a, b), -1.0, 1.0))))


def project_row(row: dict[str, Any], year: int) -> dict[str, Any]:
    require(int(row['year']) == year, 'row year mismatch')
    sol = float(row['sol']) % 360.0
    require(not (BLIND[0] <= sol <= BLIND[1]), f'protected-region row reached v61: {row.get("id")}')
    vg = float(row['vg'])
    require(math.isfinite(vg) and vg > 0.0, f'nonpositive/nonfinite vg: {row.get("id")}')
    lon = float(row['sun_lon'])
    lat = float(row['ecl_lat'])
    require(all(math.isfinite(v) for v in (sol, lon, lat)), f'nonfinite accessible observable: {row.get("id")}')
    return {'id': str(row['id']), 'year': year, 'sol': sol, 'sun_lon': lon, 'ecl_lat': lat, 'vg': vg}


def physical_residual(actual: dict[str, Any], pred_u: np.ndarray, pred_logv: float) -> float:
    ua = unit(actual['sun_lon'], actual['ecl_lat'])
    radiant = angle_deg(ua, pred_u) / 3.0
    speed = abs(math.log(float(actual['vg'])) - float(pred_logv)) / math.log(1.08)
    return float(math.hypot(radiant, speed))


def q90(values: list[float]) -> float:
    return float(np.quantile(values, 0.90)) if values else 10.0


def annual_predictive(rows: list[dict[str, Any]], center_sol: float) -> dict[str, Any]:
    require(rows, 'annual family membership unexpectedly empty')
    static_u = np.mean(np.asarray([unit(r['sun_lon'], r['ecl_lat']) for r in rows], dtype=float), axis=0)
    norm = float(np.linalg.norm(static_u))
    require(math.isfinite(norm) and norm > 1e-12, 'degenerate static radiant')
    static_u /= norm
    static_logv = float(np.mean([math.log(float(r['vg'])) for r in rows]))
    static_residuals = [physical_residual(r, static_u, static_logv) for r in rows]

    if len(rows) < 4:
        pred = list(static_residuals)
        learned = 0.0
    else:
        pred = []
        for held in range(len(rows)):
            train = [i for i in range(len(rows)) if i != held]
            x = np.asarray([signed_circular_delta(rows[i]['sol'], center_sol) / 10.0 for i in train], dtype=float)
            design = np.column_stack([np.ones(len(train), dtype=float), x])
            target = np.column_stack([
                np.asarray([unit(rows[i]['sun_lon'], rows[i]['ecl_lat'])[0] for i in train], dtype=float),
                np.asarray([unit(rows[i]['sun_lon'], rows[i]['ecl_lat'])[1] for i in train], dtype=float),
                np.asarray([unit(rows[i]['sun_lon'], rows[i]['ecl_lat'])[2] for i in train], dtype=float),
                np.asarray([math.log(float(rows[i]['vg'])) for i in train], dtype=float),
            ])
            coef, *_ = np.linalg.lstsq(design, target, rcond=None)
            xh = signed_circular_delta(rows[held]['sol'], center_sol) / 10.0
            yh = np.asarray([1.0, xh], dtype=float) @ coef
            pu = np.asarray(yh[:3], dtype=float)
            pnorm = float(np.linalg.norm(pu))
            require(math.isfinite(pnorm) and pnorm > 1e-12, 'degenerate predicted radiant')
            pu /= pnorm
            require(math.isfinite(float(yh[3])), 'nonfinite predicted log(vg)')
            pred.append(physical_residual(rows[held], pu, float(yh[3])))
        learned = 1.0

    return {
        'n': len(rows),
        'learned': learned,
        'pred_median': float(np.median(pred)),
        'pred_q90': q90(pred),
        'pred_max': float(max(pred)),
        'static_median': float(np.median(static_residuals)),
        'static_q90': q90(static_residuals),
    }


def family_features(family: dict[str, Any], lookup: dict[int, dict[str, dict[str, Any]]], centers: dict[int, float]) -> dict[str, Any]:
    annual = []
    total = 0
    learned_total = 0.0
    for year in YEARS:
        prefix = f'SNT{year}:'
        ids = [str(eid) for eid in family['event_ids'] if str(eid).startswith(prefix)]
        require(ids, f'missing annual members: {family["family_id"]} {year}')
        require(len(ids) == len(set(ids)), f'duplicate annual member IDs: {family["family_id"]} {year}')
        rows = []
        for eid in ids:
            require(eid in lookup[year], f'candidate member missing from frozen label-free rows: {eid}')
            rows.append(lookup[year][eid])
        a = annual_predictive(rows, float(centers[year]))
        annual.append(a)
        total += int(a['n'])
        learned_total += float(a['learned']) * int(a['n'])
    pred_q90 = float(max(a['pred_q90'] for a in annual))
    pred_median = float(max(a['pred_median'] for a in annual))
    pred_max = float(max(a['pred_max'] for a in annual))
    static_q90 = float(max(a['static_q90'] for a in annual))
    return {
        'pred_q90_max': pred_q90,
        'pred_median_max': pred_median,
        'pred_max_max': pred_max,
        'static_q90_max': static_q90,
        'q90_gain': float(static_q90 - pred_q90),
        'learned_fraction': float(learned_total / max(total, 1)),
        'annual': annual,
    }


def predictive_order(feature_rows: list[dict[str, Any]]) -> list[str]:
    return [
        str(r['family_id'])
        for r in sorted(
            feature_rows,
            key=lambda r: (
                float(r['features']['pred_q90_max']),
                float(r['features']['pred_median_max']),
                -float(r['features']['q90_gain']),
                str(r['family_id']),
            ),
        )
    ]


def equal_rank_fusion(parent: list[str], pred: list[str]) -> list[str]:
    require(len(parent) == len(pred) and set(parent) == set(pred), 'fusion universe mismatch')
    pr = {fid: i + 1 for i, fid in enumerate(parent)}
    qr = {fid: i + 1 for i, fid in enumerate(pred)}
    return sorted(parent, key=lambda fid: (pr[fid] + qr[fid], pr[fid], fid))


def load_route_pretruth(route: str, root: Path, prep_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], np.ndarray, dict[int, dict[str, dict[str, Any]]]]:
    meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    payload = json.loads((root / 'family_memberships.json').read_text())
    require(meta['truth_accessed'] is False and payload['truth_accessed'] is False, f'{route} payload is not pretruth')
    require(meta['target_information_access'] is False and meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, f'{route} pretruth firewall changed')
    ids = list(map(str, meta['family_ids']))
    families = payload['families']
    require(len(ids) == EXPECTED_COUNTS[route] and [str(f['family_id']) for f in families] == ids, f'{route} candidate universe changed')
    centers = np.load(root / 'centroids.npy', allow_pickle=False)
    require(centers.shape == (len(ids), 8), f'{route} centroid matrix shape changed')
    require(array_sha(centers) == meta['centroid_sha256'], f'{route} centroid matrix hash changed')

    lookup: dict[int, dict[str, dict[str, Any]]] = {}
    for year in YEARS:
        raw = json.loads((prep_root / f'{route}_{year}.json').read_text())
        projected = [project_row(row, year) for row in raw]
        by = {row['id']: row for row in projected}
        require(len(by) == len(projected), f'{route} {year} duplicate row IDs')
        lookup[year] = by
    return meta, families, centers, lookup


def run_pretruth(a: argparse.Namespace) -> int:
    a.output.mkdir(parents=True, exist_ok=True)
    parent = json.loads(a.parent_orders.read_text())
    require(parent['verdict'] == 'PASS_EXACT_V31_PARENT_ORDER_RECONSTRUCTION', 'parent-order export invalid')
    require(parent['scientific_change'] is False, 'parent-order export is not provenance-only')

    manifest = json.loads((a.prep_root / 'label_free_preparation_manifest.json').read_text())
    require(manifest['verdict'] == 'PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION', 'label-free preparation verdict changed')
    require(manifest['shower_truth_accessed'] is False, 'truth reached label-free preparation')
    require(manifest['target_information_access'] is False and manifest['maarsy_scientific_access'] is False, 'preparation firewall changed')
    require(manifest['target_region_retained'] is False, 'protected target region retained')

    out_routes = {}
    for route in ROUTES:
        meta, families, centroids, lookup = load_route_pretruth(route, getattr(a, f'{route}_root'), a.prep_root)
        pinfo = parent['routes'][route]
        parent_order = list(map(str, pinfo['v31_fused_order']))
        require(len(parent_order) == EXPECTED_COUNTS[route], f'{route} parent count changed')
        require(order_sha(parent_order) == EXPECTED_PARENT_SHA[route], f'{route} parent hash changed')
        require(set(parent_order) == set(map(str, meta['family_ids'])), f'{route} parent universe mismatch')

        feature_rows = []
        for i, family in enumerate(families):
            centers = {2013: float(centroids[i, 0]), 2014: float(centroids[i, 4])}
            feature_rows.append({'family_id': str(family['family_id']), 'features': family_features(family, lookup, centers)})
        pred = predictive_order(feature_rows)
        fused = equal_rank_fusion(parent_order, pred)
        out_routes[route] = {
            'candidate_count': len(fused),
            'parent_order_sha256': order_sha(parent_order),
            'predictive_order_sha256': order_sha(pred),
            'fused_order_sha256': order_sha(fused),
            'predictive_order': pred,
            'fused_order': fused,
            'feature_rows': feature_rows,
            'centroid_sha256': meta['centroid_sha256'],
        }

    result = {
        'schema': 'ORBITTRACE_V61_PREDICTIVE_CONSISTENCY_PRETRUTH_V1',
        'scientific_stage': 'EXPOSED_SONOTACO_V61_PRETRUTH_ONLY',
        'routes': out_routes,
        'ranking_rule': '(pred_q90_max, pred_median_max, -q90_gain, family_id); equal 1-based rank-sum with exact v31 parent',
        'parameter_search': False,
        'threshold_search': False,
        'weight_search': False,
        'feature_search': False,
        'regression_search': False,
        'route_specific_rule': False,
        'candidate_deletion': False,
        'membership_changed': False,
        'truth_accessed': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V61_PREDICTIVE_CONSISTENCY_PRETRUTH.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'pretruth_sha256': sha(out), 'route_hashes': {r: out_routes[r]['fused_order_sha256'] for r in ROUTES}}, indent=2, sort_keys=True))
    return 0


def evaluate(families: list[dict[str, Any]], order: list[str], truth: dict[str, str], budget: int) -> dict[str, Any]:
    by = {str(f['family_id']): f for f in families}
    require(len(order) == len(by) and set(order) == set(by), 'evaluation order universe mismatch')
    counts = Counter(v for v in truth.values() if v != 'SPORADIC')
    labels = sorted(k for k, n in counts.items() if n >= 4)
    truth_sets = {label: {eid for eid, value in truth.items() if value == label} for label in labels}
    truth_ids = set(truth)
    active = []
    for rank, fid in enumerate(order, start=1):
        members = set(map(str, by[fid]['event_ids'])) & truth_ids
        if members:
            active.append((rank, fid, members))
    active = active[:int(budget)]
    mat = np.zeros((len(labels), len(active)), dtype=float)
    for i, label in enumerate(labels):
        actual = truth_sets[label]
        for j, (_rank, _fid, pred) in enumerate(active):
            overlap = len(actual & pred)
            if overlap:
                precision = overlap / len(pred)
                recall = overlap / len(actual)
                mat[i, j] = 2.0 * precision * recall / (precision + recall)
    n = max(len(labels), len(active))
    cost = np.zeros((n, n), dtype=float)
    cost[:len(labels), :len(active)] = -mat
    ri, cj = linear_sum_assignment(cost)
    vals = [float(mat[i, j]) if j < len(active) else 0.0 for i, j in zip(ri.tolist(), cj.tolist()) if i < len(labels)]
    return {
        'eligible_showers': len(labels),
        'macro_f1': float(np.mean(vals)) if vals else 0.0,
        'recovered_f1_gt_0_5': int(sum(v > 0.5 for v in vals)),
        'candidate_used': len(active),
    }


def run_evaluate(a: argparse.Namespace) -> int:
    a.output.mkdir(parents=True, exist_ok=True)
    pre = json.loads(a.pretruth.read_text())
    require(pre['schema'] == 'ORBITTRACE_V61_PREDICTIVE_CONSISTENCY_PRETRUTH_V1', 'wrong pretruth schema')
    require(pre['truth_accessed'] is False and pre['target_information_access'] is False and pre['target_region_events_accessed'] is False, 'pretruth firewall invalid')

    panels = []
    parent_controls = []
    for route in ROUTES:
        root = getattr(a, f'{route}_root')
        payload = json.loads((root / 'family_memberships.json').read_text())
        require(payload['truth_accessed'] is False, f'{route} membership payload changed')
        families = payload['families']
        parent_order = list(map(str, a.parent[route]))
        fused_order = list(map(str, pre['routes'][route]['fused_order']))
        require(order_sha(parent_order) == EXPECTED_PARENT_SHA[route], f'{route} parent order changed before evaluation')
        require(order_sha(fused_order) == pre['routes'][route]['fused_order_sha256'], f'{route} fused order changed before evaluation')
        require(set(parent_order) == set(fused_order) == {str(f['family_id']) for f in families}, f'{route} evaluation universe mismatch')

        for year in YEARS:
            truth = json.loads((a.truth_root / f'truth_{route}_{year}.json').read_text())
            frozen_eval = json.loads((a.truth_root / f'evaluation_{route}_{year}.json').read_text())
            lit_macro, lit_recovered, budget = EXPECTED_LITERATURE[(route, year)]
            require(int(frozen_eval['candidate_budget']['comparator_budget']) == budget, f'{route} {year} budget changed')
            summary = frozen_eval['comparator_summary']
            require(abs(float(summary['macro_f1']) - lit_macro) < 1e-15 and int(summary['recovered_f1_gt_0_5']) == lit_recovered, f'{route} {year} literature comparator changed')

            control = evaluate(families, parent_order, truth, budget)
            exp_macro, exp_rec = EXPECTED_V31[(route, year)]
            require(abs(float(control['macro_f1']) - exp_macro) < 1e-12 and int(control['recovered_f1_gt_0_5']) == exp_rec, f'{route} {year} exact v31 parent control failed')
            parent_controls.append({'comparator': route, 'year': year, **control})

            cur = evaluate(families, fused_order, truth, budget)
            pair_pass = bool(float(cur['macro_f1']) > lit_macro and int(cur['recovered_f1_gt_0_5']) >= lit_recovered)
            panels.append({
                'comparator': route,
                'year': year,
                'budget': budget,
                'candidate_macro_f1': float(cur['macro_f1']),
                'literature_macro_f1': lit_macro,
                'candidate_recovered_f1_gt_0_5': int(cur['recovered_f1_gt_0_5']),
                'literature_recovered_f1_gt_0_5': lit_recovered,
                'parent_v31_macro_f1': exp_macro,
                'parent_v31_recovered_f1_gt_0_5': exp_rec,
                'superiority_pair_pass': pair_pass,
            })

    wins = sum(int(p['superiority_pair_pass']) for p in panels)
    passed = wins == 4
    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V61_PREDICTIVE_CONSISTENCY_RANK_FUSION_V1',
        'verdict': 'PASS_V61_ALL_FOUR_LITERATURE_SUPERIORITY_PAIRS' if passed else 'FAIL_V61_ALL_FOUR_LITERATURE_SUPERIORITY_PAIRS',
        'panel_wins': wins,
        'panels': panels,
        'v31_parent_controls': parent_controls,
        'pretruth_sha256': sha(a.pretruth),
        'first_valid_outcome_binding': True,
        'parameter_search': False,
        'threshold_search': False,
        'weight_search': False,
        'feature_search': False,
        'regression_search': False,
        'route_specific_rule': False,
        'post_result_rescue': False,
        'candidate_membership_changed': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V61_PREDICTIVE_CONSISTENCY_RANK_FUSION_RESULT.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='stage', required=True)

    pre = sub.add_parser('pretruth')
    pre.add_argument('--parent-orders', type=Path, required=True)
    pre.add_argument('--sugar-root', type=Path, required=True)
    pre.add_argument('--hdbscan-root', type=Path, required=True)
    pre.add_argument('--prep-root', type=Path, required=True)
    pre.add_argument('--output', type=Path, required=True)

    ev = sub.add_parser('evaluate')
    ev.add_argument('--pretruth', type=Path, required=True)
    ev.add_argument('--parent-orders', type=Path, required=True)
    ev.add_argument('--sugar-root', type=Path, required=True)
    ev.add_argument('--hdbscan-root', type=Path, required=True)
    ev.add_argument('--truth-root', type=Path, required=True)
    ev.add_argument('--output', type=Path, required=True)
    return p.parse_args()


def main() -> int:
    a = parse_args()
    if a.stage == 'pretruth':
        return run_pretruth(a)
    parent_payload = json.loads(a.parent_orders.read_text())
    a.parent = {route: list(map(str, parent_payload['routes'][route]['v31_fused_order'])) for route in ROUTES}
    return run_evaluate(a)


if __name__ == '__main__':
    raise SystemExit(main())

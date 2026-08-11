#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v31_local_geometry_margin_oof_v1 import train_evaluate as v31

v22 = v31.v22
v24 = v31.v24
v19 = v31.v19

FEATURE_DIM = 71
RECOVERY = 0.5
HDB_N = 229
RANKGAP_SHA256 = 'e4e09546e17b9a5da7ce12ad9af4bb7129533fd9b5be846ebc859719f01a9758'
EXPECTED_HDB_HASHES = {
    'annual_margin_2013_sha256': '99520a9f07b7cf188002fb79ba03592ffda8724f43c8adfeb97541f038ffdb19',
    'annual_margin_2014_sha256': 'd989def64913d7d9807c6d2433642fdde5e29d031d315ddff5a8353668f19d00',
    'combined_margin_sha256': '647e81df101ba7b0e511e618004dc2f01fae166cc78d55461f02a9c811650e7d',
    'local_diversity_order_sha256': '9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595',
    'fused_order_sha256': '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d',
}
EXPECTED_CONTROLS = {
    ('sugar', 2013): (0.2719801488280529, 16),
    ('sugar', 2014): (0.31529041952487225, 17),
    ('hdbscan', 2013): (0.14888037368183737, 9),
    ('hdbscan', 2014): (0.15198123772301594, 9),
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def canonical_sha(obj: Any) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(b).hexdigest()


def validate_parent(parent: dict[str, Any]) -> None:
    require(parent['verdict'] == 'FAIL_V31_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'exact v31 parent verdict changed')
    require(parent['panel_wins'] == 2 and len(parent['panels']) == 4, 'exact v31 parent panel structure changed')
    seen: dict[tuple[str, int], tuple[float, int]] = {}
    for row in parent['panels']:
        key = (str(row['comparator']), int(row['year']))
        seen[key] = (float(row['candidate_macro_f1']), int(row['candidate_recovered_f1_gt_0_5']))
    require(set(seen) == set(EXPECTED_CONTROLS), 'exact v31 parent panel universe changed')
    for key, exp in EXPECTED_CONTROLS.items():
        cur = seen[key]
        require(abs(cur[0] - exp[0]) < 1e-12 and cur[1] == exp[1], f'exact v31 parent control changed: {key}')
    hd = parent['order_diagnostics']['hdbscan']
    for k, exp in EXPECTED_HDB_HASHES.items():
        require(str(hd[k]) == exp, f'exact v31 parent HDB hash changed: {k}')
    require(parent['strict_whole_shower_oof'] is True, 'v31 OOF firewall changed')
    require(parent['annual_margin'] == 'd_nonpositive-d_positive', 'v31 annual margin changed')
    require(parent['annual_combiner'] == 'min(margin_2013,margin_2014)', 'v31 annual combiner changed')
    require(parent['fusion'] == 'one equal rank-sum with exact v19', 'v31 fusion changed')
    for k in ('target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(parent[k] is False, f'v31 protected-data flag changed: {k}')
    require(parent['blind_exclusion'] == [20.0, 55.0], 'v31 blind exclusion changed')


def reproduce_v31_margins(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    parent_result: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require(sha256(ranker_source) == v24.RANKER_SOURCE_SHA, '#839 ranker source changed')
    parent = json.loads(parent_result.read_text())
    validate_parent(parent)

    roots = {'sugar': sugar_root, 'hdbscan': hdbscan_root}
    for route in v24.ROUTES:
        root = roots[route]
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp = json.loads((root / 'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, f'{route} payload not pretruth')
        require(int(meta['feature_dimension']) == FEATURE_DIM, f'{route} feature dimension changed')
        require(meta['target_information_access'] is False, f'{route} target access changed')
        require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, f'{route} protected survey access changed')
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        require(X.ndim == 2 and X.shape[1] == FEATURE_DIM and C.ndim == 2 and C.shape[1] == 8, f'{route} array shape changed')
        require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], f'{route} array identity changed')

    truth: dict[tuple[str, int], Any] = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((truth_root / f'truth_{route}_{year}.json').read_text())

    ranker = v22.load_module(ranker_source, 'frozen_839_v31_annual_min_diagnostic')
    route_data: dict[str, dict[str, Any]] = {}
    Xs: list[np.ndarray] = []
    y13s: list[np.ndarray] = []
    y14s: list[np.ndarray] = []
    groups: list[str] = []
    route_offsets: dict[str, tuple[int, int]] = {}
    cursor = 0

    for route in v24.ROUTES:
        root = roots[route]
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp = json.loads((root / 'family_memberships.json').read_text())
        ids = list(map(str, meta['family_ids']))
        fams = list(fp['families'])
        require([str(f['family_id']) for f in fams] == ids, f'{route} membership order changed')
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        by = {y: truth[(route, y)] for y in v24.YEARS}
        eligible = v22.eligible_from_year_truth(by)
        hidden: dict[str, Any] = {}
        hidden.update(by[2013])
        hidden.update(by[2014])
        base = [v22.family_truth(f, hidden, eligible) for f in fams]
        y13: list[float] = []
        y14: list[float] = []
        rg: list[str] = []
        for i, (fam, t) in enumerate(zip(fams, base)):
            label = t['best_label']
            rg.append(('SHOWER/' + str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                q13 = q14 = 0.0
            else:
                q13, q14 = v24.annual_f1_for_fixed_label(fam, str(label), by)
            y13.append(float(q13))
            y14.append(float(q14))
        route_offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        Xs.append(X)
        y13s.append(np.asarray(y13, dtype=float))
        y14s.append(np.asarray(y14, dtype=float))
        groups.extend(rg)
        route_data[route] = {'meta': meta, 'fams': fams, 'ids': ids, 'centroids': C}

    Xall = np.vstack(Xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM), 'stacked feature shape changed')
    require(len(y13all) == len(y14all) == len(groups) == cursor, 'stacked target/group shape changed')

    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    margin13 = np.zeros(cursor, dtype=float)
    margin14 = np.zeros(cursor, dtype=float)
    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        tr_groups = {groups[i] for i in np.where(tr)[0]}
        te_groups = {groups[i] for i in np.where(te)[0]}
        require(tr_groups.isdisjoint(te_groups), f'group leakage fold {fold}')
        mu = np.mean(Xall[tr], axis=0)
        sd = np.std(Xall[tr], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        Ztr = (Xall[tr] - mu[None, :]) / scale[None, :]
        Zte = (Xall[te] - mu[None, :]) / scale[None, :]
        te_idx = np.where(te)[0]
        for year, yall, out in ((2013, y13all, margin13), (2014, y14all, margin14)):
            pos = yall[tr] > RECOVERY
            neg = ~pos
            require(pos.any() and neg.any(), f'{year} fold {fold} lacks positive/nonpositive references')
            P = Ztr[pos]
            N = Ztr[neg]
            for j, global_i in enumerate(te_idx.tolist()):
                dpos = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))
                dneg = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))
                out[global_i] = dneg - dpos

    require(np.all(np.isfinite(margin13)) and np.all(np.isfinite(margin14)), 'nonfinite annual margin')
    combined = np.minimum(margin13, margin14)
    require(np.all(np.isfinite(combined)), 'nonfinite combined margin')

    lo, hi = route_offsets['hdbscan']
    rd = route_data['hdbscan']
    ids = list(map(str, rd['ids']))
    require(len(ids) == HDB_N, 'HDB family count changed')
    m13 = margin13[lo:hi]
    m14 = margin14[lo:hi]
    scores = combined[lo:hi]
    require(v22.array_sha(m13) == EXPECTED_HDB_HASHES['annual_margin_2013_sha256'], 'HDB 2013 annual margin does not reproduce v31')
    require(v22.array_sha(m14) == EXPECTED_HDB_HASHES['annual_margin_2014_sha256'], 'HDB 2014 annual margin does not reproduce v31')
    require(v22.array_sha(scores) == EXPECTED_HDB_HASHES['combined_margin_sha256'], 'HDB combined margin does not reproduce v31')

    tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
    idx = ranker.diversity_order(scores, rd['centroids'], 0.8, 1.0, tie)
    local_order = [ids[i] for i in idx]
    v19_order = list(map(str, rd['meta']['v19_order']))
    fused = list(v19.fusion_orders(local_order, v19_order)['rank_sum'])
    require(v31.order_sha(local_order) == EXPECTED_HDB_HASHES['local_diversity_order_sha256'], 'HDB local/diversity order does not reproduce v31')
    require(v31.order_sha(fused) == EXPECTED_HDB_HASHES['fused_order_sha256'], 'HDB fused order does not reproduce v31')
    rank = {fid: i + 1 for i, fid in enumerate(fused)}

    rows: list[dict[str, Any]] = []
    by_index = {fid: i for i, fid in enumerate(ids)}
    for fid in fused:
        i = by_index[fid]
        c = float(scores[i])
        a13 = float(m13[i])
        a14 = float(m14[i])
        g13 = float(a13 - c)
        g14 = float(a14 - c)
        require(g13 >= -1e-15 and g14 >= -1e-15, 'negative bottleneck gap')
        rows.append({
            'family_id': fid,
            'v31_rank': int(rank[fid]),
            'margin_2013': a13,
            'margin_2014': a14,
            'combined_margin': c,
            'bottleneck_gap_2013': max(0.0, g13),
            'bottleneck_gap_2014': max(0.0, g14),
        })
    require(len(rows) == HDB_N and len({r['family_id'] for r in rows}) == HDB_N, 'invalid HDB margin vector')

    meta = {
        'parent_hdb_hashes': EXPECTED_HDB_HASHES,
        'parent_controls': {f'{k[0]}_{k[1]}': [v[0], v[1]] for k, v in EXPECTED_CONTROLS.items()},
        'family_count': HDB_N,
    }
    return rows, meta


def freeze_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    parent_result: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    rows, meta = reproduce_v31_margins(sugar_root, hdbscan_root, truth_root, ranker_source, parent_result)
    csha = canonical_sha(rows)
    result = {
        'verdict': 'PASS_V31_HDB_ANNUAL_MARGIN_VECTOR_FREEZE',
        'scientific_role': 'EXACT_V31_HDB_ANNUAL_MARGIN_VECTOR_FROZEN_BEFORE_1046_SURFACED_MISSED_STATUS_ATTACHMENT',
        'question': 'Does exact v31 annual min disproportionately bottleneck recoverable HDB groups that v31 misses?',
        'family_count': HDB_N,
        'families': rows,
        'canonical_family_vector_sha256': csha,
        'parent_hdb_hashes': meta['parent_hdb_hashes'],
        'parent_controls': meta['parent_controls'],
        'statistic_predeclared': 'for year y and #1046 fixed first-recoverable family, bottleneck_gap_y = margin_y - min(margin_2013,margin_2014)',
        'rankgap_1046_loaded_before_vector_freeze': False,
        'new_rank_or_score_used_for_ranking': False,
        'alternate_annual_combiner_evaluated': False,
        'threshold_selected': False,
        'quantile_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'budget_specific_rule': False,
        'year_specific_order': False,
        'successor_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    path = output / 'V31_HDB_ANNUAL_MARGIN_VECTOR.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'family_count': HDB_N, 'canonical_family_vector_sha256': csha}, indent=2, sort_keys=True))
    return 0


def summary(vals: list[float]) -> dict[str, Any]:
    require(vals, 'empty diagnostic class')
    x = np.asarray(vals, dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite diagnostic value')
    return {
        'count': int(len(x)),
        'median_bottleneck_gap': float(np.median(x)),
        'mean_bottleneck_gap': float(np.mean(x)),
        'positive_gap_count': int(np.sum(x > 0.0)),
        'positive_gap_fraction': float(np.mean(x > 0.0)),
        'min_bottleneck_gap': float(np.min(x)),
        'max_bottleneck_gap': float(np.max(x)),
    }


def diagnose_mode(vector_file: Path, rankgap_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    vector = json.loads(vector_file.read_text())
    require(vector['verdict'] == 'PASS_V31_HDB_ANNUAL_MARGIN_VECTOR_FREEZE', 'annual margin vector verdict changed')
    require(vector['scientific_role'] == 'EXACT_V31_HDB_ANNUAL_MARGIN_VECTOR_FROZEN_BEFORE_1046_SURFACED_MISSED_STATUS_ATTACHMENT', 'annual margin vector role changed')
    require(int(vector['family_count']) == HDB_N and len(vector['families']) == HDB_N, 'annual margin vector universe changed')
    require(vector['canonical_family_vector_sha256'] == canonical_sha(vector['families']), 'annual margin vector canonical hash changed')
    require(vector['rankgap_1046_loaded_before_vector_freeze'] is False, '1046 status was available before vector freeze')
    for k in ('new_rank_or_score_used_for_ranking', 'alternate_annual_combiner_evaluated', 'threshold_selected', 'quantile_selected', 'top_k_selected', 'rank_window_selected', 'budget_specific_rule', 'year_specific_order', 'successor_selected', 'post_result_second_search', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(vector[k] is False, f'forbidden vector flag set: {k}')
    require(vector['blind_exclusion'] == [20.0, 55.0], 'vector blind exclusion changed')

    require(sha256(rankgap_file) == RANKGAP_SHA256, '#1046 rank-gap artifact identity changed')
    rg = json.loads(rankgap_file.read_text())
    require(rg['verdict'] == 'PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC', '#1046 verdict changed')
    require(rg['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED', '#1046 role changed')
    require(rg['new_rank_evaluated'] is False and rg['successor_selected'] is False, '#1046 was not diagnostic-only')
    require(rg['target_information_access'] is False and rg['target_region_events_accessed'] is False, '#1046 target firewall changed')
    require(rg['maarsy_scientific_access'] is False and rg['dms_scientific_access'] is False, '#1046 survey firewall changed')
    require(rg['blind_exclusion'] == [20.0, 55.0], '#1046 blind exclusion changed')
    require(rg['v31_reproduction']['2013']['budget'] == 11 and rg['v31_reproduction']['2014']['budget'] == 9, '#1046 budget provenance changed')
    require(abs(float(rg['v31_reproduction']['2013']['macro_f1']) - EXPECTED_CONTROLS[('hdbscan', 2013)][0]) < 1e-12, '#1046 v31 2013 reproduction changed')
    require(abs(float(rg['v31_reproduction']['2014']['macro_f1']) - EXPECTED_CONTROLS[('hdbscan', 2014)][0]) < 1e-12, '#1046 v31 2014 reproduction changed')

    by_id = {str(r['family_id']): r for r in vector['families']}
    require(len(by_id) == HDB_N, 'duplicate family in annual margin vector')

    annual: dict[str, Any] = {}
    detailed: dict[str, list[dict[str, Any]]] = {}
    pass_flags: list[bool] = []
    expected = {2013: {'candidate': 18, 'surfaced': 9, 'missed': 9}, 2014: {'candidate': 19, 'surfaced': 9, 'missed': 10}}
    for year in (2013, 2014):
        src = rg['annual'][str(year)]
        require(int(src['candidate_recoverable_showers']) == expected[year]['candidate'], f'#1046 candidate-recoverable count changed {year}')
        require(int(src['v31_surfaced_recoverable_showers']) == expected[year]['surfaced'], f'#1046 surfaced count changed {year}')
        require(int(src['recoverable_but_missed_showers']) == expected[year]['missed'], f'#1046 missed count changed {year}')
        rows = [r for r in src['rows'] if bool(r.get('candidate_recoverable', False))]
        require(len(rows) == expected[year]['candidate'], f'#1046 recoverable row count changed {year}')
        missed: list[float] = []
        surfaced: list[float] = []
        outrows: list[dict[str, Any]] = []
        gap_key = f'bottleneck_gap_{year}'
        for r in rows:
            fid = r.get('first_recoverable_family_id_by_v31_fused_rank')
            require(fid is not None and str(fid) in by_id, f'#1046 recoverable representative missing from vector {year}')
            is_missed = bool(r.get('recoverable_but_missed', False))
            is_surfaced = bool(r.get('v31_surfaced_recoverable', False))
            require(is_missed != is_surfaced, f'#1046 recoverable status not exclusive {year}')
            gap = float(by_id[str(fid)][gap_key])
            require(np.isfinite(gap) and gap >= 0.0, f'invalid bottleneck gap {year}')
            if is_missed:
                missed.append(gap)
                cls = 'RECOVERABLE_BUT_MISSED'
            else:
                surfaced.append(gap)
                cls = 'SURFACED_RECOVERABLE'
            outrows.append({
                'diagnostic_group': str(r['label']),
                'fixed_recoverable_family_id': str(fid),
                'class': cls,
                'bottleneck_gap': gap,
                'own_year_margin': float(by_id[str(fid)][f'margin_{year}']),
                'combined_min_margin': float(by_id[str(fid)]['combined_margin']),
                'v31_rank': int(by_id[str(fid)]['v31_rank']),
            })
        require(len(missed) == expected[year]['missed'] and len(surfaced) == expected[year]['surfaced'], f'diagnostic class count changed {year}')
        ms = summary(missed)
        ss = summary(surfaced)
        positive_pass = bool(ms['median_bottleneck_gap'] > 0.0)
        separation_pass = bool(ms['median_bottleneck_gap'] > ss['median_bottleneck_gap'])
        annual[str(year)] = {
            'missed_recoverable': ms,
            'surfaced_recoverable': ss,
            'median_difference_missed_minus_surfaced': float(ms['median_bottleneck_gap'] - ss['median_bottleneck_gap']),
            'missed_median_strictly_positive': positive_pass,
            'missed_median_strictly_greater_than_surfaced': separation_pass,
            'direction_pass': bool(positive_pass and separation_pass),
        }
        detailed[str(year)] = outrows
        pass_flags.extend([positive_pass, separation_pass])

    passed = bool(all(pass_flags))
    result = {
        'verdict': 'PASS_V31_ANNUAL_MIN_BOTTLENECK_DIAGNOSTIC' if passed else 'FAIL_V31_ANNUAL_MIN_BOTTLENECK_DIAGNOSTIC',
        'scientific_role': 'POST_V56_MECHANISM_DIAGNOSTIC_ONLY_NO_ALTERNATE_COMBINER_OR_SUCCESSOR_EVALUATED',
        'question': 'Among #1046 annual-recoverable HDB groups, are groups missed by v31 more strongly bottlenecked by the other-year margin than surfaced recoverable groups in both years?',
        'margin_vector_sha256': sha256(vector_file),
        'margin_vector_canonical_sha256': vector['canonical_family_vector_sha256'],
        'source_1046_run': 31451236076,
        'source_1046_artifact': 9086399760,
        'source_1046_artifact_digest': 'sha256:a2c373df77ef7e0065c1d8aceb1f6e5826f1e30b6286f2331c362d959f1d7f69',
        'source_1046_result_sha256': RANKGAP_SHA256,
        'statistic': 'for year y, first recoverable family under exact v31: margin_y - min(margin_2013,margin_2014)',
        'annual_diagnostics': annual,
        'diagnostic_rows': detailed,
        'all_four_direction_inequalities_pass': passed,
        'new_rank_or_score_used_for_ranking': False,
        'alternate_annual_combiner_evaluated': False,
        'annual_specific_order_evaluated': False,
        'threshold_search': False,
        'quantile_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'budget_specific_rule': False,
        'representative_search': False,
        'feature_search': False,
        'metric_search': False,
        'k_search': False,
        'scaling_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'model_search': False,
        'component_or_topology_search': False,
        'crossroute_search': False,
        'source_quota_selected': False,
        'oracle_identity_used_for_ranking': False,
        'successor_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    path = output / 'V31_ANNUAL_MIN_BOTTLENECK_DIAGNOSTIC.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'annual_diagnostics': annual}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('freeze')
    a.add_argument('--sugar-root', type=Path, required=True)
    a.add_argument('--hdbscan-root', type=Path, required=True)
    a.add_argument('--truth-root', type=Path, required=True)
    a.add_argument('--ranker-source', type=Path, required=True)
    a.add_argument('--parent-result', type=Path, required=True)
    a.add_argument('--output', type=Path, required=True)
    b = sub.add_parser('diagnose')
    b.add_argument('--vector-file', type=Path, required=True)
    b.add_argument('--rankgap-file', type=Path, required=True)
    b.add_argument('--output', type=Path, required=True)
    x = p.parse_args()
    if x.mode == 'freeze':
        return freeze_mode(x.sugar_root, x.hdbscan_root, x.truth_root, x.ranker_source, x.parent_result, x.output)
    return diagnose_mode(x.vector_file, x.rankgap_file, x.output)


if __name__ == '__main__':
    raise SystemExit(main())

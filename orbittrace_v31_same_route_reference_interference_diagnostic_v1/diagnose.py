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
RANKER_SHA256 = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
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
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_parent(path: Path) -> dict[str, Any]:
    parent = json.loads(path.read_text())
    require(parent['verdict'] == 'FAIL_V31_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'v31 parent verdict changed')
    require(parent['panel_wins'] == 2 and len(parent['panels']) == 4, 'v31 parent panel state changed')
    require(parent['strict_whole_shower_oof'] is True and parent['feature_dimension'] == FEATURE_DIM and parent['nearest_k'] == 1, 'v31 geometry changed')
    require(parent['distance'] == 'ordinary Euclidean across all 71 fold-training standardized dimensions', 'v31 distance changed')
    require(parent['annual_margin'] == 'd_nonpositive-d_positive' and parent['annual_combiner'] == 'min(margin_2013,margin_2014)', 'v31 score changed')
    require(parent['diversity'] == {'lambda': 0.8, 'scale': 1.0} and parent['fusion'] == 'one equal rank-sum with exact v19', 'v31 downstream ranking changed')
    require(parent['candidate_membership_changed'] is False and parent['pretruth_feature_changed'] is False, 'v31 representation changed')
    require(parent['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'v31 SonotaCo role changed')
    require(parent['target_information_access'] is False and parent['target_region_events_accessed'] is False, 'v31 target firewall changed')
    require(parent['maarsy_scientific_access'] is False and parent['dms_scientific_access'] is False, 'v31 survey firewall changed')
    require(parent['blind_exclusion'] == [20.0, 55.0], 'v31 blind exclusion changed')
    pmap = {(str(x['comparator']), int(x['year'])): x for x in parent['panels']}
    require(set(pmap) == set(EXPECTED_CONTROLS), 'v31 panel universe changed')
    for key, exp in EXPECTED_CONTROLS.items():
        cur = pmap[key]
        require(abs(float(cur['candidate_macro_f1']) - exp[0]) < 1e-12 and int(cur['candidate_recovered_f1_gt_0_5']) == exp[1], f'v31 control changed {key}')
    hd = parent['order_diagnostics']['hdbscan']
    for k, exp in EXPECTED_HDB_HASHES.items():
        require(str(hd[k]) == exp, f'v31 internal HDB identity changed {k}')
    return parent


def freeze_counterfactual(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    parent_result: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(sha256(ranker_source) == RANKER_SHA256, '#839 ranker source changed')
    validate_parent(parent_result)

    roots = {'sugar': sugar_root, 'hdbscan': hdbscan_root}
    truth: dict[tuple[str, int], Any] = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((truth_root / f'truth_{route}_{year}.json').read_text())

    ranker = v22.load_module(ranker_source, 'frozen_839_same_route_reference_interference')
    route_data: dict[str, dict[str, Any]] = {}
    Xs: list[np.ndarray] = []
    y13s: list[np.ndarray] = []
    y14s: list[np.ndarray] = []
    groups: list[str] = []
    routes: list[str] = []
    offsets: dict[str, tuple[int, int]] = {}
    cursor = 0

    for route in v24.ROUTES:
        root = roots[route]
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp = json.loads((root / 'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, f'{route} payload not pretruth')
        require(int(meta['feature_dimension']) == FEATURE_DIM, f'{route} feature dimension changed')
        require(meta['target_information_access'] is False and meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, f'{route} protected-data payload flag changed')
        ids = list(map(str, meta['family_ids']))
        fams = list(fp['families'])
        require([str(f['family_id']) for f in fams] == ids, f'{route} membership order changed')
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        require(X.shape == (len(ids), FEATURE_DIM) and C.shape == (len(ids), 8), f'{route} array shape changed')
        require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], f'{route} array identity changed')

        by = {year: truth[(route, year)] for year in v24.YEARS}
        eligible = v22.eligible_from_year_truth(by)
        hidden: dict[str, Any] = {}
        hidden.update(by[2013]); hidden.update(by[2014])
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
            y13.append(float(q13)); y14.append(float(q14))

        offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        Xs.append(X); y13s.append(np.asarray(y13, dtype=float)); y14s.append(np.asarray(y14, dtype=float)); groups.extend(rg); routes.extend([route] * len(ids))
        route_data[route] = {'meta': meta, 'fams': fams, 'ids': ids, 'centroids': C}

    Xall = np.vstack(Xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    groups = list(map(str, groups))
    route_arr = np.asarray(routes, dtype=str)
    require(Xall.shape == (cursor, FEATURE_DIM) and len(y13all) == len(y14all) == len(groups) == len(routes) == cursor, 'stacked input mismatch')
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)

    lo_h, hi_h = offsets['hdbscan']
    hdb_global = set(range(lo_h, hi_h))
    n_h = hi_h - lo_h
    require(n_h == HDB_N, 'HDB family count changed')

    mixed_pos_dist = {2013: np.full(n_h, np.nan), 2014: np.full(n_h, np.nan)}
    mixed_neg_dist = {2013: np.full(n_h, np.nan), 2014: np.full(n_h, np.nan)}
    same_pos_dist = {2013: np.full(n_h, np.nan), 2014: np.full(n_h, np.nan)}
    same_neg_dist = {2013: np.full(n_h, np.nan), 2014: np.full(n_h, np.nan)}
    fold_diag: list[dict[str, Any]] = []

    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f'group leakage fold {fold}')
        mu = np.mean(Xall[tr], axis=0)
        sd = np.std(Xall[tr], axis=0, ddof=0)
        scale = sd.copy(); scale[scale == 0.0] = 1.0
        Ztr = (Xall[tr] - mu[None, :]) / scale[None, :]
        Zte = (Xall[te] - mu[None, :]) / scale[None, :]
        tr_idx = np.where(tr)[0]
        te_idx = np.where(te)[0]
        tr_hdb = route_arr[tr] == 'hdbscan'
        annual_counts: dict[str, Any] = {}

        for year, yall in ((2013, y13all), (2014, y14all)):
            pos = yall[tr] > RECOVERY
            neg = ~pos
            spos = pos & tr_hdb
            sneg = neg & tr_hdb
            require(pos.any() and neg.any(), f'{year} fold {fold} lacks mixed reference class')
            require(spos.any() and sneg.any(), f'{year} fold {fold} lacks HDB-only reference class')
            annual_counts[str(year)] = {
                'mixed_positive': int(pos.sum()),
                'mixed_nonpositive': int(neg.sum()),
                'hdb_positive': int(spos.sum()),
                'hdb_nonpositive': int(sneg.sum()),
            }
            P = Ztr[pos]; N = Ztr[neg]; SP = Ztr[spos]; SN = Ztr[sneg]
            for j, gi in enumerate(te_idx.tolist()):
                if gi not in hdb_global:
                    continue
                h = gi - lo_h
                z = Zte[j]
                mixed_pos_dist[year][h] = float(np.min(np.linalg.norm(P - z[None, :], axis=1)))
                mixed_neg_dist[year][h] = float(np.min(np.linalg.norm(N - z[None, :], axis=1)))
                same_pos_dist[year][h] = float(np.min(np.linalg.norm(SP - z[None, :], axis=1)))
                same_neg_dist[year][h] = float(np.min(np.linalg.norm(SN - z[None, :], axis=1)))

        fold_diag.append({
            'fold': fold,
            'train_examples': int(tr.sum()),
            'test_examples': int(te.sum()),
            'hdb_test_examples': int(sum(int(i in hdb_global) for i in te_idx.tolist())),
            'zero_variance_features': int(np.sum(sd == 0.0)),
            'annual_reference_counts': annual_counts,
        })

    for year in (2013, 2014):
        for arr in (mixed_pos_dist[year], mixed_neg_dist[year], same_pos_dist[year], same_neg_dist[year]):
            require(np.all(np.isfinite(arr)), f'nonfinite HDB distance array {year}')

    mixed_margin = {year: mixed_neg_dist[year] - mixed_pos_dist[year] for year in (2013, 2014)}
    same_margin = {year: same_neg_dist[year] - same_pos_dist[year] for year in (2013, 2014)}
    delta = {year: same_margin[year] - mixed_margin[year] for year in (2013, 2014)}
    combined = np.minimum(mixed_margin[2013], mixed_margin[2014])
    require(v22.array_sha(mixed_margin[2013]) == EXPECTED_HDB_HASHES['annual_margin_2013_sha256'], 'mixed 2013 margin does not reproduce v31')
    require(v22.array_sha(mixed_margin[2014]) == EXPECTED_HDB_HASHES['annual_margin_2014_sha256'], 'mixed 2014 margin does not reproduce v31')
    require(v22.array_sha(combined) == EXPECTED_HDB_HASHES['combined_margin_sha256'], 'mixed combined margin does not reproduce v31')

    rd = route_data['hdbscan']
    ids = list(map(str, rd['ids']))
    tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(HDB_N)]
    idx = ranker.diversity_order(combined, rd['centroids'], 0.8, 1.0, tie)
    local_order = [ids[i] for i in idx]
    v19_order = list(map(str, rd['meta']['v19_order']))
    fused = list(v19.fusion_orders(local_order, v19_order)['rank_sum'])
    require(v31.order_sha(local_order) == EXPECTED_HDB_HASHES['local_diversity_order_sha256'], 'mixed local order does not reproduce v31')
    require(v31.order_sha(fused) == EXPECTED_HDB_HASHES['fused_order_sha256'], 'mixed fused order does not reproduce v31')
    rank = {fid: i + 1 for i, fid in enumerate(fused)}
    index = {fid: i for i, fid in enumerate(ids)}

    rows: list[dict[str, Any]] = []
    for fid in fused:
        i = index[fid]
        row: dict[str, Any] = {'family_id': fid, 'v31_rank': int(rank[fid])}
        for year in (2013, 2014):
            row[str(year)] = {
                'mixed_d_positive': float(mixed_pos_dist[year][i]),
                'mixed_d_nonpositive': float(mixed_neg_dist[year][i]),
                'mixed_margin': float(mixed_margin[year][i]),
                'hdb_only_d_positive': float(same_pos_dist[year][i]),
                'hdb_only_d_nonpositive': float(same_neg_dist[year][i]),
                'hdb_only_margin': float(same_margin[year][i]),
                'delta_hdb_only_minus_mixed_margin': float(delta[year][i]),
            }
        rows.append(row)
    require(len(rows) == HDB_N and len({r['family_id'] for r in rows}) == HDB_N, 'invalid frozen HDB vector')

    csha = canonical_sha(rows)
    result = {
        'verdict': 'PASS_V31_SAME_ROUTE_REFERENCE_COUNTERFACTUAL_VECTOR_FREEZE',
        'scientific_role': 'FULL_229_HDB_MIXED_VS_HDB_ONLY_REFERENCE_VECTOR_FROZEN_BEFORE_1046_STATUS_ATTACHMENT',
        'family_count': HDB_N,
        'families': rows,
        'canonical_family_vector_sha256': csha,
        'counterfactual': 'same exact stacked-route fold scaler and annual labels as v31; nearest-reference eligibility restricted from Sugar+HDB to HDB only',
        'delta_definition': 'HDB-only annual margin minus exact mixed-route annual margin',
        'fold_diagnostics': fold_diag,
        'parent_hdb_hashes': EXPECTED_HDB_HASHES,
        'rankgap_1046_loaded_before_vector_freeze': False,
        'candidate_order_evaluated': False,
        'literature_panel_evaluated': False,
        'route_weight_or_quota_used': False,
        'partial_source_removal_evaluated': False,
        'separate_positive_negative_source_rule_evaluated': False,
        'route_specific_scaling_used': False,
        'feature_search': False,
        'metric_search': False,
        'k_search': False,
        'threshold_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'successor_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    path = output / 'V31_SAME_ROUTE_REFERENCE_COUNTERFACTUAL_VECTOR.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'family_count': HDB_N, 'canonical_family_vector_sha256': csha, 'fold_diagnostics': fold_diag}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def summary(values: list[float]) -> dict[str, Any]:
    require(values, 'empty diagnostic class')
    x = np.asarray(values, dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite diagnostic class')
    return {
        'count': int(len(x)),
        'median_delta': float(np.median(x)),
        'mean_delta': float(np.mean(x)),
        'positive_delta_count': int(np.sum(x > 0.0)),
        'positive_delta_fraction': float(np.mean(x > 0.0)),
        'min_delta': float(np.min(x)),
        'max_delta': float(np.max(x)),
    }


def diagnose(vector_file: Path, rankgap_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    v = json.loads(vector_file.read_text())
    require(v['verdict'] == 'PASS_V31_SAME_ROUTE_REFERENCE_COUNTERFACTUAL_VECTOR_FREEZE', 'counterfactual vector verdict changed')
    require(v['scientific_role'] == 'FULL_229_HDB_MIXED_VS_HDB_ONLY_REFERENCE_VECTOR_FROZEN_BEFORE_1046_STATUS_ATTACHMENT', 'counterfactual vector role changed')
    require(int(v['family_count']) == HDB_N and len(v['families']) == HDB_N, 'counterfactual vector universe changed')
    require(v['canonical_family_vector_sha256'] == canonical_sha(v['families']), 'counterfactual canonical vector changed')
    require(v['rankgap_1046_loaded_before_vector_freeze'] is False, '#1046 status available before vector freeze')
    for k in ('candidate_order_evaluated','literature_panel_evaluated','route_weight_or_quota_used','partial_source_removal_evaluated','separate_positive_negative_source_rule_evaluated','route_specific_scaling_used','feature_search','metric_search','k_search','threshold_search','annual_combiner_search','diversity_search','fusion_search','successor_selected','post_result_second_search','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(v[k] is False, f'forbidden vector flag set {k}')
    require(v['blind_exclusion'] == [20.0, 55.0], 'counterfactual blind exclusion changed')

    require(sha256(rankgap_file) == RANKGAP_SHA256, '#1046 result identity changed')
    rg = json.loads(rankgap_file.read_text())
    require(rg['verdict'] == 'PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC', '#1046 verdict changed')
    require(rg['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED', '#1046 role changed')
    require(rg['new_rank_evaluated'] is False and rg['successor_selected'] is False, '#1046 not diagnostic-only')
    require(rg['target_information_access'] is False and rg['target_region_events_accessed'] is False and rg['maarsy_scientific_access'] is False and rg['dms_scientific_access'] is False, '#1046 firewall changed')
    require(rg['blind_exclusion'] == [20.0, 55.0], '#1046 blind exclusion changed')

    by_id = {str(r['family_id']): r for r in v['families']}
    require(len(by_id) == HDB_N, 'duplicate counterfactual family')
    expected = {2013: {'candidate': 18, 'surfaced': 9, 'missed': 9}, 2014: {'candidate': 19, 'surfaced': 9, 'missed': 10}}
    annual: dict[str, Any] = {}
    detail: dict[str, list[dict[str, Any]]] = {}
    flags: list[bool] = []

    for year in (2013, 2014):
        src = rg['annual'][str(year)]
        require(int(src['candidate_recoverable_showers']) == expected[year]['candidate'], f'#1046 candidate count changed {year}')
        require(int(src['v31_surfaced_recoverable_showers']) == expected[year]['surfaced'], f'#1046 surfaced count changed {year}')
        require(int(src['recoverable_but_missed_showers']) == expected[year]['missed'], f'#1046 missed count changed {year}')
        rows = [r for r in src['rows'] if bool(r.get('candidate_recoverable', False))]
        require(len(rows) == expected[year]['candidate'], f'#1046 recoverable rows changed {year}')
        missed: list[float] = []
        surfaced: list[float] = []
        outrows: list[dict[str, Any]] = []
        for r in rows:
            fid = r.get('first_recoverable_family_id_by_v31_fused_rank')
            require(fid is not None and str(fid) in by_id, f'#1046 representative missing {year}')
            is_missed = bool(r.get('recoverable_but_missed', False))
            is_surfaced = bool(r.get('v31_surfaced_recoverable', False))
            require(is_missed != is_surfaced, f'#1046 status not exclusive {year}')
            vals = by_id[str(fid)][str(year)]
            d = float(vals['delta_hdb_only_minus_mixed_margin'])
            require(np.isfinite(d), f'nonfinite counterfactual delta {year}')
            if is_missed:
                missed.append(d); cls = 'RECOVERABLE_BUT_MISSED'
            else:
                surfaced.append(d); cls = 'SURFACED_RECOVERABLE'
            outrows.append({
                'diagnostic_group': str(r['label']),
                'fixed_recoverable_family_id': str(fid),
                'class': cls,
                'delta_hdb_only_minus_mixed_margin': d,
                'mixed_margin': float(vals['mixed_margin']),
                'hdb_only_margin': float(vals['hdb_only_margin']),
                'mixed_d_positive': float(vals['mixed_d_positive']),
                'mixed_d_nonpositive': float(vals['mixed_d_nonpositive']),
                'hdb_only_d_positive': float(vals['hdb_only_d_positive']),
                'hdb_only_d_nonpositive': float(vals['hdb_only_d_nonpositive']),
                'v31_rank': int(by_id[str(fid)]['v31_rank']),
            })
        require(len(missed) == expected[year]['missed'] and len(surfaced) == expected[year]['surfaced'], f'class count changed {year}')
        ms = summary(missed); ss = summary(surfaced)
        pos = bool(ms['median_delta'] > 0.0)
        sep = bool(ms['median_delta'] > ss['median_delta'])
        annual[str(year)] = {
            'missed_recoverable': ms,
            'surfaced_recoverable': ss,
            'median_difference_missed_minus_surfaced': float(ms['median_delta'] - ss['median_delta']),
            'missed_median_strictly_positive': pos,
            'missed_median_strictly_greater_than_surfaced': sep,
            'direction_pass': bool(pos and sep),
        }
        detail[str(year)] = outrows
        flags.extend([pos, sep])

    passed = bool(all(flags))
    result = {
        'verdict': 'PASS_V31_SAME_ROUTE_REFERENCE_INTERFERENCE_DIAGNOSTIC' if passed else 'FAIL_V31_SAME_ROUTE_REFERENCE_INTERFERENCE_DIAGNOSTIC',
        'scientific_role': 'POST_V59_ROUTE_POOL_MECHANISM_DIAGNOSTIC_ONLY_NO_SAME_ROUTE_ORDER_OR_SUCCESSOR_EVALUATED',
        'question': 'Does restricting only the nearest-reference pool from stacked Sugar+HDB to HDB improve missed recoverable HDB groups more than surfaced recoverable groups in both years?',
        'counterfactual_vector_sha256': sha256(vector_file),
        'counterfactual_vector_canonical_sha256': v['canonical_family_vector_sha256'],
        'source_1046_run': 31451236076,
        'source_1046_artifact': 9086399760,
        'source_1046_artifact_digest': 'sha256:a2c373df77ef7e0065c1d8aceb1f6e5826f1e30b6286f2331c362d959f1d7f69',
        'source_1046_result_sha256': RANKGAP_SHA256,
        'statistic': 'Delta_y = HDB-only-reference annual margin - exact mixed-route v31 annual margin on #1046 fixed first-recoverable family',
        'annual_diagnostics': annual,
        'diagnostic_rows': detail,
        'all_four_direction_inequalities_pass': passed,
        'same_route_candidate_order_evaluated': False,
        'literature_panel_evaluated': False,
        'route_weight_or_quota_search': False,
        'partial_source_removal_search': False,
        'separate_positive_negative_source_rule_search': False,
        'route_specific_scaling_search': False,
        'feature_search': False,
        'metric_search': False,
        'k_search': False,
        'threshold_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'alternate_representative_search': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
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
    path = output / 'V31_SAME_ROUTE_REFERENCE_INTERFERENCE_DIAGNOSTIC.json'
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
        return freeze_counterfactual(x.sugar_root, x.hdbscan_root, x.truth_root, x.ranker_source, x.parent_result, x.output)
    return diagnose(x.vector_file, x.rankgap_file, x.output)


if __name__ == '__main__':
    raise SystemExit(main())

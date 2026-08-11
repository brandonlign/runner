#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v31_local_geometry_margin_oof_v1 import train_evaluate as v31
from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM = 71
RECOVERY = 0.5
MAD_GAUSSIAN_FACTOR = 1.4826
RANKER_SOURCE_SHA256 = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
PARENT_SOURCE_BLOB = '917e3cd6f9310ca1282e0efa58ed0924d03ed4da'
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


def reproduce_parent(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    output: Path,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    old_argv = list(sys.argv)
    try:
        sys.argv = [
            'train_evaluate.py',
            '--sugar-root', str(sugar_root),
            '--hdbscan-root', str(hdbscan_root),
            '--truth-root', str(truth_root),
            '--ranker-source', str(ranker_source),
            '--output', str(output),
        ]
        rc = v31.main()
        require(rc == 0, 'exact v31 parent execution failed')
    finally:
        sys.argv = old_argv
    path = output / 'V31_LOCAL_GEOMETRY_OOF_RESULT.json'
    require(path.is_file(), 'exact v31 parent result missing')
    parent = json.loads(path.read_text())
    require(parent['verdict'] == 'FAIL_V31_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'v31 parent verdict changed')
    require(parent['panel_wins'] == 2 and len(parent['panels']) == 4, 'v31 parent panel state changed')
    require(parent['strict_whole_shower_oof'] is True, 'v31 OOF semantics changed')
    require(parent['feature_dimension'] == FEATURE_DIM and parent['nearest_k'] == 1, 'v31 geometry changed')
    require(parent['distance'] == 'ordinary Euclidean across all 71 fold-training standardized dimensions', 'v31 distance changed')
    require(parent['annual_margin'] == 'd_nonpositive-d_positive', 'v31 margin changed')
    require(parent['annual_combiner'] == 'min(margin_2013,margin_2014)', 'v31 combiner changed')
    require(parent['diversity'] == {'lambda': 0.8, 'scale': 1.0}, 'v31 diversity changed')
    require(parent['fusion'] == 'one equal rank-sum with exact v19', 'v31 fusion changed')
    require(parent['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'v31 SonotaCo role changed')
    require(parent['target_information_access'] is False and parent['target_region_events_accessed'] is False, 'v31 target firewall changed')
    require(parent['maarsy_scientific_access'] is False and parent['dms_scientific_access'] is False, 'v31 survey firewall changed')
    require(parent['blind_exclusion'] == [20.0, 55.0], 'v31 blind exclusion changed')
    pmap = {(str(x['comparator']), int(x['year'])): x for x in parent['panels']}
    require(set(pmap) == set(PARENT), 'v31 parent panel identities changed')
    for key, (f1, recovered) in PARENT.items():
        row = pmap[key]
        require(abs(float(row['candidate_macro_f1']) - f1) < 1e-12, f'{key} v31 F1 changed')
        require(int(row['candidate_recovered_f1_gt_0_5']) == recovered, f'{key} v31 recovery changed')
    return parent


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--sugar-root', type=Path, required=True)
    p.add_argument('--hdbscan-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--ranker-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(v22.sha(a.ranker_source) == RANKER_SOURCE_SHA256, '#839 ranker source changed')
    parent = reproduce_parent(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.output / 'parent_v31')

    roots = {'sugar': a.sugar_root, 'hdbscan': a.hdbscan_root}
    truth: dict[tuple[str, int], Any] = {}
    frozen_eval: dict[tuple[str, int], Any] = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((a.truth_root / f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route, year)] = json.loads((a.truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(a.ranker_source, 'frozen_839_v60_robust_mad_geometry')
    route_data: dict[str, Any] = {}
    Xs: list[np.ndarray] = []
    y13s: list[np.ndarray] = []
    y14s: list[np.ndarray] = []
    groups: list[str] = []
    offsets: dict[str, tuple[int, int]] = {}
    cursor = 0

    for route in v24.ROUTES:
        root = roots[route]
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp = json.loads((root / 'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, f'{route} pretruth payload changed')
        require(meta['feature_dimension'] == FEATURE_DIM, f'{route} feature dimension changed')
        require(meta['target_information_access'] is False, f'{route} target firewall changed')
        require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, f'{route} survey firewall changed')
        ids = list(map(str, meta['family_ids']))
        fams = list(fp['families'])
        require([str(f['family_id']) for f in fams] == ids, f'{route} family alignment changed')
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
        route_groups: list[str] = []
        for i, (f, t) in enumerate(zip(fams, base)):
            label = t['best_label']
            route_groups.append(('SHOWER/' + str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                q13 = q14 = 0.0
            else:
                q13, q14 = v24.annual_f1_for_fixed_label(f, str(label), by)
            y13.append(float(q13)); y14.append(float(q14))

        offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        Xs.append(X)
        y13s.append(np.asarray(y13, float))
        y14s.append(np.asarray(y14, float))
        groups.extend(route_groups)
        route_data[route] = {'meta': meta, 'fams': fams, 'ids': ids, 'centroids': C}

    Xall = np.vstack(Xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM), 'v60 stacked feature mismatch')
    require(len(y13all) == len(y14all) == len(groups) == cursor, 'v60 stacked target mismatch')
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)

    margin13 = np.zeros(cursor, dtype=float)
    margin14 = np.zeros(cursor, dtype=float)
    fold_diag: list[dict[str, Any]] = []

    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f'group leakage fold {fold}')

        Xtr = Xall[tr]
        center = np.median(Xtr, axis=0)
        mad = np.median(np.abs(Xtr - center[None, :]), axis=0)
        robust = MAD_GAUSSIAN_FACTOR * mad
        pop_std = np.std(Xtr, axis=0, ddof=0)
        mad_zero = robust == 0.0
        scale = robust.copy()
        scale[mad_zero] = pop_std[mad_zero]
        both_zero = scale == 0.0
        scale[both_zero] = 1.0
        require(np.all(np.isfinite(center)) and np.all(np.isfinite(scale)) and np.all(scale > 0.0), f'fold {fold} invalid robust scale')

        Ztr = (Xtr - center[None, :]) / scale[None, :]
        Zte = (Xall[te] - center[None, :]) / scale[None, :]
        te_idx = np.where(te)[0]
        annual_diag: dict[str, Any] = {}
        for year, yall, out in ((2013, y13all, margin13), (2014, y14all, margin14)):
            pos = yall[tr] > RECOVERY
            neg = ~pos
            require(pos.any() and neg.any(), f'{year} fold {fold} lacks positive/nonpositive references')
            P = Ztr[pos]
            N = Ztr[neg]
            dpos_all: list[float] = []
            dneg_all: list[float] = []
            for j, global_i in enumerate(te_idx.tolist()):
                dpos = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))
                dneg = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))
                require(np.isfinite(dpos) and np.isfinite(dneg), f'{year} fold {fold} nonfinite distance')
                out[global_i] = dneg - dpos
                dpos_all.append(dpos); dneg_all.append(dneg)
            annual_diag[str(year)] = {
                'positive_references': int(pos.sum()),
                'nonpositive_references': int(neg.sum()),
                'mean_nearest_positive_distance': float(np.mean(dpos_all)),
                'mean_nearest_nonpositive_distance': float(np.mean(dneg_all)),
            }

        fold_diag.append({
            'fold': fold,
            'train_examples': int(tr.sum()),
            'test_examples': int(te.sum()),
            'mad_zero_features': int(mad_zero.sum()),
            'std_fallback_features': int(mad_zero.sum() - both_zero.sum()),
            'unit_fallback_features': int(both_zero.sum()),
            'scale_min': float(np.min(scale)),
            'scale_median': float(np.median(scale)),
            'scale_max': float(np.max(scale)),
            'annual_references': annual_diag,
        })

    combined = np.minimum(margin13, margin14)
    require(np.all(np.isfinite(combined)), 'nonfinite v60 combined margin')

    variants: dict[str, Any] = {}
    order_diag: dict[str, Any] = {}
    v19_control: list[dict[str, Any]] = []
    for route in v24.ROUTES:
        lo, hi = offsets[route]
        rd = route_data[route]
        ids = rd['ids']
        scores = combined[lo:hi]
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(scores, rd['centroids'], 0.8, 1.0, tie)
        local_order = [ids[i] for i in idx]
        v19_order = list(map(str, rd['meta']['v19_order']))
        fused = list(v19.fusion_orders(local_order, v19_order)['rank_sum'])
        variants[route] = v22.rerank(rd['fams'], fused)
        order_diag[route] = {
            'annual_margin_2013_sha256': v22.array_sha(margin13[lo:hi]),
            'annual_margin_2014_sha256': v22.array_sha(margin14[lo:hi]),
            'combined_margin_sha256': v22.array_sha(scores),
            'local_diversity_order_sha256': order_sha(local_order),
            'fused_order_sha256': order_sha(fused),
            'diversity': {'lambda': 0.8, 'scale': 1.0},
            'fusion': 'equal rank-sum with exact v19',
        }
        for year in v24.YEARS:
            budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
            cur = v22.evaluate(v22.rerank(rd['fams'], v19_order), truth[(route, year)], budget)
            exp = v24.V19_METRICS[(route, year)]
            require(abs(float(cur['macro_f1']) - float(exp[0])) < 1e-12, f'{route} {year} v19 F1 changed')
            require(int(cur['recovered_f1_gt_0_5']) == int(exp[1]), f'{route} {year} v19 recovery changed')
            v19_control.append({'comparator': route, 'year': year, **cur})

    panels: list[dict[str, Any]] = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(variants[route], truth[(route, year)], budget)
        lit = frozen_eval[(route, year)]['comparator_summary']
        cm = float(cur['macro_f1']); cr = int(cur['recovered_f1_gt_0_5'])
        lm = float(lit['macro_f1']); lr = int(lit['recovered_f1_gt_0_5'])
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

    wins = int(sum(bool(x['superiority_pair_pass']) for x in panels))
    passed = bool(wins == 4)
    pmap = {(str(x['comparator']), int(x['year'])): x for x in parent['panels']}
    parent_controls = [
        {
            'comparator': route,
            'year': year,
            'macro_f1': float(pmap[(route, year)]['candidate_macro_f1']),
            'recovered_f1_gt_0_5': int(pmap[(route, year)]['candidate_recovered_f1_gt_0_5']),
        }
        for route, year in (('sugar', 2013), ('sugar', 2014), ('hdbscan', 2013), ('hdbscan', 2014))
    ]

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V60_ROBUST_MAD_LOCAL_GEOMETRY_V1',
        'verdict': 'PASS_V60_ROBUST_MAD_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V60_ROBUST_MAD_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'replace exact-v31 fold-training mean/population-std scaling with fold-training median and 1.4826*MAD; zero-MAD falls back to population std then 1.0 only if both are zero',
        'parent': 'v31 local-geometry-margin OOF',
        'parent_source_blob': PARENT_SOURCE_BLOB,
        'parent_reproduction_pass': True,
        'parent_controls': parent_controls,
        'feature_dimension': FEATURE_DIM,
        'scaling_center': 'fold-training featurewise median',
        'scaling_primary': '1.4826 * fold-training featurewise median absolute deviation',
        'mad_gaussian_factor': MAD_GAUSSIAN_FACTOR,
        'zero_mad_fallback': 'fold-training population std; if also zero then 1.0',
        'distance': 'ordinary Euclidean across all 71 robust-fold-scaled dimensions',
        'recovery_f1_threshold': RECOVERY,
        'nearest_k': 1,
        'annual_margin': 'd_nonpositive-d_positive',
        'annual_combiner': 'min(margin_2013,margin_2014)',
        'strict_whole_shower_oof': True,
        'candidate_membership_changed': False,
        'pretruth_feature_changed': False,
        'diversity': {'lambda': 0.8, 'scale': 1.0},
        'fusion': 'one equal rank-sum with exact v19',
        'panel_wins': wins,
        'panels': panels,
        'v19_control': v19_control,
        'fold_diagnostics': fold_diag,
        'order_diagnostics': order_diag,
        'fold_search_or_change': False,
        'reference_pool_changed': False,
        'robust_scale_search': False,
        'alternate_mad_factor_evaluated': False,
        'iqr_scaling_used': False,
        'clipping_used': False,
        'winsorization_used': False,
        'quantile_transform_used': False,
        'rank_transform_used': False,
        'huber_scaling_used': False,
        'standard_robust_blend_used': False,
        'feature_dropping_used': False,
        'epsilon_scale_floor_used': False,
        'k_search': False,
        'metric_search': False,
        'feature_search': False,
        'block_weight_search': False,
        'threshold_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'route_specific_rule': False,
        'boundary_identity_used': False,
        'oracle_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V60_ROBUST_MAD_LOCAL_GEOMETRY_RESULT.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels, 'fold_diagnostics': fold_diag, 'order_diagnostics': order_diag}, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

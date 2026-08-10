#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

ROUTES = ('sugar', 'hdbscan')
YEARS = (2013, 2014)
PANELS = (('sugar', 2013), ('sugar', 2014), ('hdbscan', 2013), ('hdbscan', 2014))
FEATURE_DIM = 71
RANKER_SOURCE_SHA = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V24_RESULT_SHA = 'c8d95bc02ad1436c9924ec14a25bcd36e0eacd960fda1fb33db3a91738fe30cf'
DIAGNOSTIC_RESULT_SHA = '93a79f49dbb907c93c5dbb0c1b91fac4633f07fb0d0ffe21d2edfb1cec167871'
EXPECTED_V24 = {
    ('sugar', 2013): (0.27806630131631344, 16),
    ('sugar', 2014): (0.32869544907104964, 17),
    ('hdbscan', 2013): (0.14257102406283795, 10),
    ('hdbscan', 2014): (0.12833942693327394, 7),
}
V19_METRICS = {
    ('sugar', 2013): (0.2813397742020527, 17),
    ('sugar', 2014): (0.3328665843994243, 18),
    ('hdbscan', 2013): (0.1386807102765093, 9),
    ('hdbscan', 2014): (0.11367457228624304, 5),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256('\n'.join(order).encode()).hexdigest()


def descending_rank_percentile(scores: np.ndarray, tie: list[tuple[int, str]]) -> tuple[np.ndarray, list[int]]:
    """Return deterministic high-is-good rank percentiles and the corresponding order.

    The score itself determines order first. Exact numerical ties use only the already-frozen
    tie_rank and stable family ID. No truth or comparator budget enters this conversion.
    """
    scores = np.asarray(scores, dtype=np.float64)
    require(scores.ndim == 1 and len(scores) == len(tie), 'rank-percentile input mismatch')
    require(np.all(np.isfinite(scores)), 'nonfinite annual OOF prediction')
    order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), int(tie[i][0]), str(tie[i][1])))
    pct = np.empty(len(scores), dtype=np.float64)
    if len(scores) <= 1:
        pct[:] = 1.0
    else:
        for rank0, idx in enumerate(order):
            pct[idx] = 1.0 - rank0 / (len(scores) - 1)
    return pct, order


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--v24-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--ranker-source', type=Path, required=True)
    p.add_argument('--diagnostic-json', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    v24_result_path = a.v24_root / 'result' / 'V24_EXPOSED_TWOHEAD_OOF_RESULT.json'
    require(sha(v24_result_path) == V24_RESULT_SHA, 'v24 result identity changed')
    v24_result = json.loads(v24_result_path.read_text())
    require(v24_result['verdict'] == 'FAIL_V24_TWOHEAD_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'v24 verdict changed')
    require(v24_result['post_result_second_search'] is False, 'v24 post-result search flag changed')
    require(sha(a.diagnostic_json) == DIAGNOSTIC_RESULT_SHA, 'v24 diagnostic identity changed')
    diag = json.loads(a.diagnostic_json.read_text())
    require(diag['conclusion']['diagnosis'] == 'RANK_PLACEMENT_HEADROOM_REMAINS', 'v25 not authorized by diagnostic')
    require(diag['new_method_evaluated'] is False and diag['parameter_search'] is False, 'diagnostic role changed')
    require(sha(a.ranker_source) == RANKER_SOURCE_SHA, '#839 ranker source changed')

    truth_year: dict[tuple[str, int], dict[str, str]] = {}
    frozen_eval: dict[tuple[str, int], dict[str, Any]] = {}
    for route, year in PANELS:
        truth_year[(route, year)] = json.loads((a.truth_root / f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route, year)] = json.loads((a.truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(a.ranker_source, 'frozen_839_v25_train')
    route_data: dict[str, dict[str, Any]] = {}
    Xs: list[np.ndarray] = []
    y13s: list[np.ndarray] = []
    y14s: list[np.ndarray] = []
    groups: list[str] = []
    offsets: dict[str, tuple[int, int]] = {}
    cursor = 0
    target_diag: dict[str, Any] = {}

    for route in ROUTES:
        root = a.v24_root / route
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        payload = json.loads((root / 'family_memberships.json').read_text())
        require(meta['feature_dimension'] == FEATURE_DIM, 'feature dimension changed')
        require(meta['truth_accessed'] is False and payload['truth_accessed'] is False, 'frozen route payload became truth-bearing')
        ids = list(map(str, meta['family_ids']))
        fams = payload['families']
        require([str(f['family_id']) for f in fams] == ids, 'family alignment changed')
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        require(X.shape == (len(ids), FEATURE_DIM) and C.shape == (len(ids), 8), 'frozen array shape changed')
        require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], 'frozen array hash changed')

        by_year = {year: truth_year[(route, year)] for year in YEARS}
        eligible = v22.eligible_from_year_truth(by_year)
        hidden = dict(by_year[2013]); hidden.update(by_year[2014])
        truths = [v22.family_truth(f, hidden, eligible) for f in fams]
        y13: list[float] = []
        y14: list[float] = []
        route_groups: list[str] = []
        for i, (family, base_truth) in enumerate(zip(fams, truths)):
            best_label = base_truth['best_label']
            route_groups.append(('SHOWER/' + str(best_label)) if best_label is not None else (f'NEG/{route}/' + ids[i]))
            if not base_truth['positive'] or best_label is None:
                y13.append(0.0); y14.append(0.0)
            else:
                f13, f14 = v24.annual_f1_for_fixed_label(family, str(best_label), by_year)
                y13.append(f13); y14.append(f14)
        arr13 = np.asarray(y13, dtype=np.float64)
        arr14 = np.asarray(y14, dtype=np.float64)
        offsets[route] = (cursor, cursor + len(ids)); cursor += len(ids)
        Xs.append(X); y13s.append(arr13); y14s.append(arr14); groups.extend(route_groups)
        route_data[route] = {'meta': meta, 'families': fams, 'ids': ids, 'centroids': C}
        target_diag[route] = {
            'families': len(ids),
            'eligible_recurrent_showers': len(eligible),
            'v22_positive_families': int(sum(t['positive'] for t in truths)),
            'nonzero_2013_targets': int(np.sum(arr13 > 0)),
            'nonzero_2014_targets': int(np.sum(arr14 > 0)),
            'group_assignment_changed_from_v22': False,
        }

    Xall = np.vstack(Xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM), 'stacked feature shape mismatch')
    require(len(y13all) == len(y14all) == len(groups) == cursor, 'stacked training shape mismatch')
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    weights = ranker.grouped_weights(groups)
    oof13 = np.zeros(cursor, dtype=np.float64)
    oof14 = np.zeros(cursor, dtype=np.float64)
    fold_diag: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        require(train.any() and test.any(), f'empty grouped fold {fold}')
        m13 = ranker.model(); m14 = ranker.model()
        m13.fit(Xall[train], y13all[train], sample_weight=weights[train])
        m14.fit(Xall[train], y14all[train], sample_weight=weights[train])
        oof13[test] = m13.predict(Xall[test])
        oof14[test] = m14.predict(Xall[test])
        test_groups = {groups[i] for i in np.where(test)[0]}
        train_groups = {groups[i] for i in np.where(train)[0]}
        require(test_groups.isdisjoint(train_groups), f'group leakage in fold {fold}')
        fold_diag.append({
            'fold': fold,
            'train_examples': int(train.sum()),
            'test_examples': int(test.sum()),
            'train_groups': len(train_groups),
            'test_groups': len(test_groups),
        })

    # Mandatory exact v24 replay before the successor is evaluated.
    v24_control: list[dict[str, Any]] = []
    v25_orders: dict[str, list[dict[str, Any]]] = {}
    order_diag: dict[str, Any] = {}
    for route in ROUTES:
        lo, hi = offsets[route]
        rd = route_data[route]
        ids = rd['ids']
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        p13 = oof13[lo:hi]
        p14 = oof14[lo:hi]

        # Exact v24 raw-score path.
        raw_min = np.minimum(p13, p14)
        raw_idx = ranker.diversity_order(raw_min, rd['centroids'], 0.8, 1.0, tie)
        raw_quality_order = [ids[i] for i in raw_idx]
        v19_order = list(map(str, rd['meta']['v19_order']))
        v24_fused_order = list(v19.fusion_orders(raw_quality_order, v19_order)['rank_sum'])
        v24_ranked = v22.rerank(rd['families'], v24_fused_order)
        for year in YEARS:
            budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
            cur = v22.evaluate(v24_ranked, truth_year[(route, year)], budget)
            expected = EXPECTED_V24[(route, year)]
            require(abs(cur['macro_f1'] - expected[0]) < 1e-12 and cur['recovered_f1_gt_0_5'] == expected[1], f'v24 control mismatch {route} {year}')
            v24_control.append({'comparator': route, 'year': year, **cur})

        # Sole v25 scientific change: rank-percentile calibration before worst-year consensus.
        pct13, order13 = descending_rank_percentile(p13, tie)
        pct14, order14 = descending_rank_percentile(p14, tie)
        q25 = np.minimum(pct13, pct14)
        idx25 = ranker.diversity_order(q25, rd['centroids'], 0.8, 1.0, tie)
        quality25 = [ids[i] for i in idx25]
        final25 = list(v19.fusion_orders(quality25, v19_order)['rank_sum'])
        v25_orders[route] = v22.rerank(rd['families'], final25)
        order_diag[route] = {
            'annual_2013_prediction_order_sha256': order_sha([ids[i] for i in order13]),
            'annual_2014_prediction_order_sha256': order_sha([ids[i] for i in order14]),
            'q25_sha256': v22.array_sha(q25),
            'v25_quality_order_sha256': order_sha(quality25),
            'v19_order_sha256': order_sha(v19_order),
            'v25_final_order_sha256': order_sha(final25),
            'percentile_definition': '1-rank0/(N-1), descending prediction, ties by frozen tie_rank then stable ID',
            'quality_combiner': 'min(percentile_2013,percentile_2014)',
            'diversity_lambda': 0.8,
            'diversity_scale': 1.0,
            'final_fusion': 'parameter-free equal rank_sum with exact v19 rank-sum',
        }

    panels: list[dict[str, Any]] = []
    for route, year in PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(v25_orders[route], truth_year[(route, year)], budget)
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

    panel_wins = sum(int(x['superiority_pair_pass']) for x in panels)
    passed = panel_wins == 4
    full_freeze: dict[str, Any] = {'verdict': 'NOT_FROZEN_V25_OOF_FAIL', 'model_2013_sha256': None, 'model_2014_sha256': None}
    if passed:
        full13 = ranker.model(); full14 = ranker.model()
        full13.fit(Xall, y13all, sample_weight=weights)
        full14.fit(Xall, y14all, sample_weight=weights)
        full13.set_params(n_jobs=1); full14.set_params(n_jobs=1)
        path13 = a.output / 'v25_sonotaco_2013_quality_head.joblib'
        path14 = a.output / 'v25_sonotaco_2014_quality_head.joblib'
        joblib.dump(full13, path13); joblib.dump(full14, path14)
        full_freeze = {
            'verdict': 'PASS_V25_FULL_SONOTACO_TWOHEAD_MODEL_FREEZE',
            'model_2013_sha256': sha(path13),
            'model_2014_sha256': sha(path14),
            'feature_dimension': FEATURE_DIM,
            'training_examples': len(groups),
            'training_groups': len(set(groups)),
            'deployment_head_calibration': 'within-catalogue deterministic descending rank percentile',
            'deployment_quality_combiner': 'min(percentile_2013,percentile_2014)',
            'deployment_diversity': {'lambda': 0.8, 'scale': 1.0},
            'deployment_final_fusion': 'equal rank_sum with frozen v19 rank-sum',
            'in_sample_full_fit_score_used_for_promotion': False,
        }
    (a.output / 'V25_FULL_MODEL_FREEZE.json').write_text(json.dumps(full_freeze, indent=2, sort_keys=True) + '\n')

    result = {
        'scientific_stage': 'V25_EXPOSED_SONOTACO_TWOHEAD_RANK_PERCENTILE_CONSENSUS_OOF_DEVELOPMENT',
        'v24_result_sha256': V24_RESULT_SHA,
        'v24_diagnostic_sha256': DIAGNOSTIC_RESULT_SHA,
        'v24_control_reproduction_pass': True,
        'v24_control': v24_control,
        'feature_dimension': FEATURE_DIM,
        'annual_heads_changed_from_v24': False,
        'annual_targets_changed_from_v24': False,
        'group_assignment_changed_from_v24': False,
        'folds': fold_diag,
        'target_diagnostics': target_diag,
        'order_diagnostics': order_diag,
        'single_deployable_successor': 'twohead_rank_percentile_consensus_v19_rank_sum',
        'panels': panels,
        'panel_wins': panel_wins,
        'verdict': 'PASS_V25_EXPOSED_TWOHEAD_RANK_CONSENSUS_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V25_TWOHEAD_RANK_CONSENSUS_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'full_model_freeze': full_freeze,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'full_fit_in_sample_score_used': False,
        'parameter_search': False,
        'post_result_second_search': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
    }
    (a.output / 'V25_EXPOSED_RANK_CONSENSUS_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': panel_wins, 'panels': panels, 'full_model_freeze': full_freeze}, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

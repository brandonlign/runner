#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

ROUTES = ('sugar', 'hdbscan')
YEARS = (2013, 2014)
PANELS = (('sugar', 2013), ('sugar', 2014), ('hdbscan', 2013), ('hdbscan', 2014))
FEATURE_DIM = 71
RANKER_SOURCE_SHA = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
VARIANTS = ('twohead_worst_prediction_quality', 'twohead_worst_prediction_v19_rank_sum')
PREFERENCE = {'twohead_worst_prediction_quality': 2, 'twohead_worst_prediction_v19_rank_sum': 1}
V19_METRICS = {
    ('sugar', 2013): (0.2813397742020527, 17),
    ('sugar', 2014): (0.3328665843994243, 18),
    ('hdbscan', 2013): (0.1386807102765093, 9),
    ('hdbscan', 2014): (0.11367457228624304, 5),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def annual_f1_for_fixed_label(
    family: dict[str, Any],
    label: str,
    by_year: dict[int, dict[str, str]],
) -> tuple[float, float]:
    member_ids = set(map(str, family['event_ids']))
    vals: list[float] = []
    for year in YEARS:
        truth = by_year[year]
        truth_ids = set(truth)
        pred = member_ids & truth_ids
        actual = {eid for eid, value in truth.items() if str(value) == str(label)}
        overlap = len(pred & actual)
        if not pred or not actual or overlap == 0:
            vals.append(0.0)
            continue
        precision = overlap / len(pred)
        recall = overlap / len(actual)
        vals.append(float(2.0 * precision * recall / (precision + recall)) if precision + recall else 0.0)
    return vals[0], vals[1]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--sugar-root', type=Path, required=True)
    p.add_argument('--hdbscan-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--ranker-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    require(v22.sha(a.ranker_source) == RANKER_SOURCE_SHA, '#839 ranker source changed')

    roots = {'sugar': a.sugar_root, 'hdbscan': a.hdbscan_root}
    truth_year: dict[tuple[str, int], dict[str, str]] = {}
    frozen_eval: dict[tuple[str, int], dict[str, Any]] = {}
    for route, year in PANELS:
        truth_year[(route, year)] = json.loads((a.truth_root / f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route, year)] = json.loads((a.truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(a.ranker_source, 'frozen_839_v24_train')
    route_data: dict[str, dict[str, Any]] = {}
    Xs: list[np.ndarray] = []
    targets_2013: list[np.ndarray] = []
    targets_2014: list[np.ndarray] = []
    groups: list[str] = []
    route_offsets: dict[str, tuple[int, int]] = {}
    cursor = 0
    target_diag: dict[str, Any] = {}

    for route in ROUTES:
        root = roots[route]
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fam_payload = json.loads((root / 'family_memberships.json').read_text())
        require(meta['feature_dimension'] == FEATURE_DIM and meta['truth_accessed'] is False, 'invalid v22 pretruth manifest')
        require(fam_payload['truth_accessed'] is False, 'membership payload already truth-bearing')
        ids = list(map(str, meta['family_ids']))
        fams = fam_payload['families']
        require([str(f['family_id']) for f in fams] == ids, 'family alignment changed')
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        require(X.shape == (len(ids), FEATURE_DIM) and C.shape == (len(ids), 8), 'pretruth array shape changed')
        require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], 'pretruth array hash changed')

        by_year = {year: truth_year[(route, year)] for year in YEARS}
        eligible = v22.eligible_from_year_truth(by_year)
        hidden: dict[str, str] = {}
        hidden.update(by_year[2013])
        hidden.update(by_year[2014])
        require(len(hidden) == len(by_year[2013]) + len(by_year[2014]), f'{route} duplicate IDs across years')

        # Best-label/group assignment and positive qualification are exactly v22.
        v22_truths = [v22.family_truth(f, hidden, eligible) for f in fams]
        y13: list[float] = []
        y14: list[float] = []
        route_groups: list[str] = []
        for i, (family, base_truth) in enumerate(zip(fams, v22_truths)):
            best_label = base_truth['best_label']
            route_groups.append(('SHOWER/' + str(best_label)) if best_label is not None else (f'NEG/{route}/' + ids[i]))
            if not base_truth['positive'] or best_label is None:
                y13.append(0.0)
                y14.append(0.0)
                continue
            a13, a14 = annual_f1_for_fixed_label(family, str(best_label), by_year)
            y13.append(a13)
            y14.append(a14)

        arr13 = np.asarray(y13, dtype=np.float64)
        arr14 = np.asarray(y14, dtype=np.float64)
        route_offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        Xs.append(X)
        targets_2013.append(arr13)
        targets_2014.append(arr14)
        groups.extend(route_groups)
        route_data[route] = {'meta': meta, 'families': fams, 'ids': ids, 'centroids': C, 'v22_truths': v22_truths, 'eligible': eligible}
        target_diag[route] = {
            'families': len(ids),
            'eligible_recurrent_showers': len(eligible),
            'v22_positive_families': int(sum(t['positive'] for t in v22_truths)),
            'nonzero_2013_targets': int(np.sum(arr13 > 0)),
            'nonzero_2014_targets': int(np.sum(arr14 > 0)),
            'target_2013_mean': float(np.mean(arr13)),
            'target_2014_mean': float(np.mean(arr14)),
            'group_assignment_changed_from_v22': False,
        }

    Xall = np.vstack(Xs)
    y13all = np.concatenate(targets_2013)
    y14all = np.concatenate(targets_2014)
    groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM), 'stacked feature shape mismatch')
    require(len(y13all) == len(y14all) == len(groups) == cursor, 'stacked target shape mismatch')

    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    weights = ranker.grouped_weights(groups)
    oof13 = np.zeros(cursor, dtype=np.float64)
    oof14 = np.zeros(cursor, dtype=np.float64)
    fold_diag: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        require(train.any() and test.any(), f'empty grouped fold {fold}')
        model13 = ranker.model()
        model14 = ranker.model()
        model13.fit(Xall[train], y13all[train], sample_weight=weights[train])
        model14.fit(Xall[train], y14all[train], sample_weight=weights[train])
        oof13[test] = model13.predict(Xall[test])
        oof14[test] = model14.predict(Xall[test])
        test_groups = {groups[i] for i in np.where(test)[0]}
        train_groups = {groups[i] for i in np.where(train)[0]}
        require(test_groups.isdisjoint(train_groups), f'group leakage in fold {fold}')
        fold_diag.append({
            'fold': fold,
            'train_examples': int(train.sum()),
            'test_examples': int(test.sum()),
            'train_groups': len(train_groups),
            'test_groups': len(test_groups),
            'test_positive_2013_targets': int(np.sum(y13all[test] > 0)),
            'test_positive_2014_targets': int(np.sum(y14all[test] > 0)),
        })

    worst_prediction = np.minimum(oof13, oof14)
    require(np.all(np.isfinite(worst_prediction)), 'nonfinite v24 OOF prediction')

    variants: dict[str, dict[str, list[dict[str, Any]]]] = {}
    control_panels: list[dict[str, Any]] = []
    for route in ROUTES:
        lo, hi = route_offsets[route]
        rd = route_data[route]
        ids = rd['ids']
        scores = worst_prediction[lo:hi]
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(scores, rd['centroids'], 0.8, 1.0, tie)
        quality_order = [ids[i] for i in idx]
        v19_order = list(map(str, rd['meta']['v19_order']))
        fused = list(v19.fusion_orders(quality_order, v19_order)['rank_sum'])
        variants[route] = {
            'twohead_worst_prediction_quality': v22.rerank(rd['families'], quality_order),
            'twohead_worst_prediction_v19_rank_sum': v22.rerank(rd['families'], fused),
            'v19_control': v22.rerank(rd['families'], v19_order),
        }
        for year in YEARS:
            budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
            cur = v22.evaluate(variants[route]['v19_control'], truth_year[(route, year)], budget)
            expected = V19_METRICS[(route, year)]
            require(abs(cur['macro_f1'] - expected[0]) < 1e-12 and cur['recovered_f1_gt_0_5'] == expected[1], f'v19 fixed-membership control mismatch {route} {year}')
            control_panels.append({'comparator': route, 'year': year, **cur})

    rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        panels: list[dict[str, Any]] = []
        for route, year in PANELS:
            budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
            cur = v22.evaluate(variants[route][variant], truth_year[(route, year)], budget)
            lit = frozen_eval[(route, year)]['comparator_summary']
            cm = float(cur['macro_f1'])
            cr = int(cur['recovered_f1_gt_0_5'])
            lm = float(lit['macro_f1'])
            lr = int(lit['recovered_f1_gt_0_5'])
            macro_ratio = cm / lm if lm else float('inf')
            recovery_ratio = cr / lr if lr else float('inf')
            win = bool(cm > lm and cr >= lr)
            panels.append({
                'comparator': route,
                'year': year,
                'budget': budget,
                'candidate_macro_f1': cm,
                'literature_macro_f1': lm,
                'candidate_recovered_f1_gt_0_5': cr,
                'literature_recovered_f1_gt_0_5': lr,
                'macro_f1_ratio': macro_ratio,
                'recovery_ratio': recovery_ratio,
                'superiority_pair_pass': win,
            })
        wins = sum(int(x['superiority_pair_pass']) for x in panels)
        min_macro = min(x['macro_f1_ratio'] for x in panels)
        min_recovery = min(x['recovery_ratio'] for x in panels)
        mean_macro = float(np.mean([x['macro_f1_ratio'] for x in panels]))
        mean_recovery = float(np.mean([x['recovery_ratio'] for x in panels]))
        rows.append({
            'variant': variant,
            'panel_wins': wins,
            'all_panel_win': wins == 4,
            'min_macro_f1_ratio': min_macro,
            'min_recovery_ratio': min_recovery,
            'mean_macro_f1_ratio': mean_macro,
            'mean_recovery_ratio': mean_recovery,
            'selection_key': [wins, min_macro, min_recovery, mean_macro, mean_recovery, PREFERENCE[variant]],
            'panels': panels,
        })

    winner = max(rows, key=lambda row: tuple(row['selection_key']))
    passed = bool(winner['all_panel_win'])

    full_freeze: dict[str, Any] = {'verdict': 'NOT_FROZEN_V24_OOF_FAIL', 'model_2013_sha256': None, 'model_2014_sha256': None}
    if passed:
        full13 = ranker.model()
        full14 = ranker.model()
        full13.fit(Xall, y13all, sample_weight=weights)
        full14.fit(Xall, y14all, sample_weight=weights)
        full13.set_params(n_jobs=1)
        full14.set_params(n_jobs=1)
        path13 = a.output / 'v24_sonotaco_2013_quality_head.joblib'
        path14 = a.output / 'v24_sonotaco_2014_quality_head.joblib'
        joblib.dump(full13, path13)
        joblib.dump(full14, path14)
        full_freeze = {
            'verdict': 'PASS_V24_FULL_SONOTACO_TWOHEAD_MODEL_FREEZE',
            'model_2013_sha256': v22.sha(path13),
            'model_2014_sha256': v22.sha(path14),
            'feature_dimension': FEATURE_DIM,
            'training_examples': len(groups),
            'training_groups': len(set(groups)),
            'training_target_2013_sha256': v22.array_sha(y13all),
            'training_target_2014_sha256': v22.array_sha(y14all),
            'training_feature_sha256': v22.array_sha(Xall),
            'deployment_combiner': 'min(predicted_F1_2013,predicted_F1_2014)',
            'in_sample_full_fit_score_used_for_promotion': False,
        }
    (a.output / 'V24_FULL_MODEL_FREEZE.json').write_text(json.dumps(full_freeze, indent=2, sort_keys=True) + '\n')

    result = {
        'scientific_stage': 'V24_EXPOSED_SONOTACO_TWOHEAD_WORST_PREDICTION_STRICT_GROUP_OOF_DEVELOPMENT',
        'preregistered_before_v23_result': True,
        'v23_authorizing_result_sha256': '422397a9f290e913ef8d14e497d0fa8ae94da0f4a5521c0825cc631252c9a4fe',
        'feature_dimension': FEATURE_DIM,
        'target_definition_2013': 'F1_2013 for unchanged v22 fixed best label; zero for unchanged v22 nonpositive families',
        'target_definition_2014': 'F1_2014 for unchanged v22 fixed best label; zero for unchanged v22 nonpositive families',
        'oof_quality_combiner': 'min(predicted_F1_2013,predicted_F1_2014)',
        'group_assignment_changed_from_v22': False,
        'same_shower_all_fragments_both_routes_same_fold': True,
        'folds': fold_diag,
        'target_diagnostics': target_diag,
        'v19_control_reproduction_pass': True,
        'v19_control': control_panels,
        'all_results': rows,
        'winner': winner,
        'verdict': 'PASS_V24_EXPOSED_TWOHEAD_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V24_TWOHEAD_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'full_model_freeze': full_freeze,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'full_fit_in_sample_score_used': False,
        'post_result_second_search': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
    }
    (a.output / 'V24_EXPOSED_TWOHEAD_OOF_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'winner': winner, 'full_model_freeze': full_freeze, 'target_diagnostics': target_diag}, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

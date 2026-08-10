#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
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
V24_DIAGNOSTIC_SHA = '93a79f49dbb907c93c5dbb0c1b91fac4633f07fb0d0ffe21d2edfb1cec167871'
V25_RESULT_SHA = '4bbb1af9cd4ab04c397cab82eed9383d248017b3641358f15a5a348cb06c8796'
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--v24-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--ranker-source', type=Path, required=True)
    p.add_argument('--diagnostic-json', type=Path, required=True)
    p.add_argument('--v25-result-json', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    v24_result_path = a.v24_root / 'result' / 'V24_EXPOSED_TWOHEAD_OOF_RESULT.json'
    require(sha(v24_result_path) == V24_RESULT_SHA, 'v24 result identity changed')
    v24_result = json.loads(v24_result_path.read_text())
    require(v24_result['verdict'] == 'FAIL_V24_TWOHEAD_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'v24 verdict changed')
    require(v24_result['post_result_second_search'] is False, 'v24 post-result search flag changed')
    require(sha(a.diagnostic_json) == V24_DIAGNOSTIC_SHA, 'v24 diagnostic identity changed')
    diagnostic = json.loads(a.diagnostic_json.read_text())
    require(diagnostic['conclusion']['diagnosis'] == 'RANK_PLACEMENT_HEADROOM_REMAINS', 'rank-placement diagnosis changed')
    require(diagnostic['new_method_evaluated'] is False and diagnostic['parameter_search'] is False, 'diagnostic role changed')
    require(sha(a.v25_result_json) == V25_RESULT_SHA, 'v25 result identity changed')
    v25_result = json.loads(a.v25_result_json.read_text())
    require(v25_result['verdict'] == 'FAIL_V25_TWOHEAD_RANK_CONSENSUS_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'v25 verdict changed')
    require(v25_result['parameter_search'] is False and v25_result['post_result_second_search'] is False, 'v25 search flags changed')
    require(sha(a.ranker_source) == RANKER_SOURCE_SHA, '#839 ranker source changed')

    truth_year: dict[tuple[str, int], dict[str, str]] = {}
    frozen_eval: dict[tuple[str, int], dict[str, Any]] = {}
    for route, year in PANELS:
        truth_year[(route, year)] = json.loads((a.truth_root / f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route, year)] = json.loads((a.truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(a.ranker_source, 'frozen_839_v26_train')
    route_data: dict[str, dict[str, Any]] = {}
    Xs: list[np.ndarray] = []
    base_w: list[np.ndarray] = []
    groups: list[str] = []
    offsets: dict[str, tuple[int, int]] = {}
    cursor = 0
    raw_target_diag: dict[str, Any] = {}

    for route in ROUTES:
        root = a.v24_root / route
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        payload = json.loads((root / 'family_memberships.json').read_text())
        require(meta['feature_dimension'] == FEATURE_DIM, 'feature dimension changed')
        require(meta['truth_accessed'] is False and payload['truth_accessed'] is False, 'frozen route payload became truth-bearing')
        require(meta['target_information_access'] is False and meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, 'route firewall identity changed')
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
        w: list[float] = []
        route_groups: list[str] = []
        for i, (family, base_truth) in enumerate(zip(fams, truths)):
            best_label = base_truth['best_label']
            group = ('SHOWER/' + str(best_label)) if best_label is not None else (f'NEG/{route}/' + ids[i])
            route_groups.append(group)
            if not base_truth['positive'] or best_label is None:
                w.append(0.0)
            else:
                f13, f14 = v24.annual_f1_for_fixed_label(family, str(best_label), by_year)
                w.append(float(min(f13, f14)))
        warr = np.asarray(w, dtype=np.float64)
        offsets[route] = (cursor, cursor + len(ids)); cursor += len(ids)
        Xs.append(X); base_w.append(warr); groups.extend(route_groups)
        route_data[route] = {'meta': meta, 'families': fams, 'ids': ids, 'centroids': C}
        raw_target_diag[route] = {
            'families': len(ids),
            'eligible_recurrent_showers': len(eligible),
            'v22_positive_families': int(sum(t['positive'] for t in truths)),
            'nonzero_worst_year_quality': int(np.sum(warr > 0)),
            'worst_year_quality_mean': float(np.mean(warr)),
        }

    Xall = np.vstack(Xs)
    wall = np.concatenate(base_w)
    groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM) and len(wall) == len(groups) == cursor, 'stacked table mismatch')

    # Sole v26 target: within-fixed-group arithmetic-mean centered worst-year quality.
    group_values: dict[str, list[float]] = defaultdict(list)
    for g, value in zip(groups, wall.tolist()):
        group_values[g].append(float(value))
    group_means = {g: float(np.mean(vals)) for g, vals in group_values.items()}
    target = np.asarray([float(w) - group_means[g] for g, w in zip(groups, wall.tolist())], dtype=np.float64)
    require(np.all(np.isfinite(target)), 'nonfinite v26 target')
    # Centering identity is exact to floating tolerance for every multi-example group.
    for g, vals in group_values.items():
        idx = [i for i, gg in enumerate(groups) if gg == g]
        require(abs(float(np.mean(target[idx]))) < 1e-12, f'group target not centered: {g}')

    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    weights = ranker.grouped_weights(groups)
    oof = np.zeros(cursor, dtype=np.float64)
    fold_diag: list[dict[str, Any]] = []
    for fold in range(5):
        train = folds != fold
        test = folds == fold
        require(train.any() and test.any(), f'empty grouped fold {fold}')
        model = ranker.model()
        model.fit(Xall[train], target[train], sample_weight=weights[train])
        oof[test] = model.predict(Xall[test])
        test_groups = {groups[i] for i in np.where(test)[0]}
        train_groups = {groups[i] for i in np.where(train)[0]}
        require(test_groups.isdisjoint(train_groups), f'group leakage in fold {fold}')
        fold_diag.append({
            'fold': fold,
            'train_examples': int(train.sum()),
            'test_examples': int(test.sum()),
            'train_groups': len(train_groups),
            'test_groups': len(test_groups),
            'mean_train_target': float(np.mean(target[train])),
            'mean_test_target': float(np.mean(target[test])),
        })

    # Mandatory fixed-membership v19 control reproduction.
    v19_control: list[dict[str, Any]] = []
    v26_ranked: dict[str, list[dict[str, Any]]] = {}
    order_diag: dict[str, Any] = {}
    for route in ROUTES:
        lo, hi = offsets[route]
        rd = route_data[route]
        ids = rd['ids']
        v19_order = list(map(str, rd['meta']['v19_order']))
        v19_ranked = v22.rerank(rd['families'], v19_order)
        for year in YEARS:
            budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
            cur = v22.evaluate(v19_ranked, truth_year[(route, year)], budget)
            expected = V19_METRICS[(route, year)]
            require(abs(cur['macro_f1'] - expected[0]) < 1e-12 and cur['recovered_f1_gt_0_5'] == expected[1], f'v19 control mismatch {route} {year}')
            v19_control.append({'comparator': route, 'year': year, **cur})

        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(oof[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        relative_order = [ids[i] for i in idx]
        final_order = list(v19.fusion_orders(relative_order, v19_order)['rank_sum'])
        v26_ranked[route] = v22.rerank(rd['families'], final_order)
        order_diag[route] = {
            'oof_relative_score_sha256': v22.array_sha(oof[lo:hi]),
            'relative_quality_order_sha256': order_sha(relative_order),
            'v19_order_sha256': order_sha(v19_order),
            'v26_final_order_sha256': order_sha(final_order),
            'diversity_lambda': 0.8,
            'diversity_scale': 1.0,
            'final_fusion': 'parameter-free equal rank_sum with exact v19 rank-sum',
        }

    panels: list[dict[str, Any]] = []
    for route, year in PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(v26_ranked[route], truth_year[(route, year)], budget)
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

    panel_wins = sum(int(row['superiority_pair_pass']) for row in panels)
    passed = panel_wins == 4
    full_freeze: dict[str, Any] = {'verdict': 'NOT_FROZEN_V26_OOF_FAIL', 'model_sha256': None}
    if passed:
        full = ranker.model()
        full.fit(Xall, target, sample_weight=weights)
        full.set_params(n_jobs=1)
        model_path = a.output / 'v26_sonotaco_relative_representative_quality.joblib'
        joblib.dump(full, model_path)
        full_freeze = {
            'verdict': 'PASS_V26_FULL_SONOTACO_RELATIVE_QUALITY_MODEL_FREEZE',
            'model_sha256': sha(model_path),
            'feature_dimension': FEATURE_DIM,
            'training_examples': len(groups),
            'training_groups': len(set(groups)),
            'target_sha256': v22.array_sha(target),
            'target_definition': 'worst_year_F1 - arithmetic mean worst_year_F1 within fixed strict group',
            'deployment_group_information_required': False,
            'deployment_final_fusion': 'equal rank_sum with frozen v19 rank-sum',
            'in_sample_full_fit_score_used_for_promotion': False,
        }
    (a.output / 'V26_FULL_MODEL_FREEZE.json').write_text(json.dumps(full_freeze, indent=2, sort_keys=True) + '\n')

    group_sizes = np.asarray([len(v) for v in group_values.values()], dtype=np.int64)
    result = {
        'scientific_stage': 'V26_EXPOSED_SONOTACO_RELATIVE_REPRESENTATIVE_QUALITY_STRICT_GROUP_OOF_DEVELOPMENT',
        'v24_result_sha256': V24_RESULT_SHA,
        'v24_diagnostic_sha256': V24_DIAGNOSTIC_SHA,
        'v25_result_sha256': V25_RESULT_SHA,
        'feature_dimension': FEATURE_DIM,
        'target_definition': 'W=min(F1_2013,F1_2014) for unchanged v22-positive family else 0; T26=W-mean_W(fixed strict group) across stacked routes',
        'group_centering_statistic': 'arithmetic_mean',
        'group_assignment_changed_from_v22': False,
        'same_shower_all_fragments_both_routes_same_fold': True,
        'deployment_group_information_required': False,
        'target_diagnostics': {
            'routes': raw_target_diag,
            'strict_groups': len(group_values),
            'multi_example_groups': int(np.sum(group_sizes > 1)),
            'max_group_size': int(np.max(group_sizes)) if len(group_sizes) else 0,
            'target_mean': float(np.mean(target)),
            'target_min': float(np.min(target)),
            'target_max': float(np.max(target)),
            'target_sha256': v22.array_sha(target),
        },
        'folds': fold_diag,
        'v19_control_reproduction_pass': True,
        'v19_control': v19_control,
        'order_diagnostics': order_diag,
        'single_deployable_successor': 'relative_representative_quality_v19_rank_sum',
        'panels': panels,
        'panel_wins': panel_wins,
        'verdict': 'PASS_V26_EXPOSED_RELATIVE_REPRESENTATIVE_QUALITY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V26_RELATIVE_REPRESENTATIVE_QUALITY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'full_model_freeze': full_freeze,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'full_fit_in_sample_score_used': False,
        'parameter_search': False,
        'post_result_second_search': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
    }
    (a.output / 'V26_EXPOSED_RELATIVE_QUALITY_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': panel_wins, 'panels': panels, 'target_diagnostics': result['target_diagnostics'], 'full_model_freeze': full_freeze}, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

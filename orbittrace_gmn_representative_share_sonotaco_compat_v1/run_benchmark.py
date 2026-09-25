#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22

MODEL_SHA256 = 'acae7fa4b4702e8d3f823defb5f2b3a3e2922b12c3bb07269b6e354316a558cb'
GMN_RESULT_SHA256 = '862ecbe4ffb30e4f1a26692d4ab1b13e7a632ec2b88bc571adfc8181244459c2'
GMN_FREEZE_SHA256 = '749d40fd8786b3f09270b098c4d96607bb5f6dd8972b6a389f9b22f629cd15fc'
QUALITY_SOURCE_SHA256 = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
RAW_FEATURE_DIM = 34
FULL_FEATURE_DIM = 71
DIVERSITY = {'lambda': 0.8, 'scale': 1.0}
EXPECTED = {
    'sugar': {
        'n': 267,
        'score_sha256': '51270f33c1a689a638a44d534df1bccebc29a149345bce7096d09b517313dc83',
        'order_sha256': 'ab60a11644ac5518ac686e44adacd039a8428d9b29c56a24d6ca3764b93a9b93',
    },
    'hdbscan': {
        'n': 229,
        'score_sha256': 'dfcf711a7d61ad05aeb4e4417a9e3ea4786bccad7c91a7ed46b4f951842aab01',
        'order_sha256': 'b9d1fcf75238e09ef3df766fb9eb296e4151a34ace6271b48a101adc5248c2b9',
    },
}
LITERATURE = {
    ('sugar', 2013): (0.20372657466522806, 13),
    ('sugar', 2014): (0.25901527732153334, 15),
    ('hdbscan', 2013): (0.16813025050497152, 10),
    ('hdbscan', 2014): (0.15689595582646423, 9),
}


def req(ok: bool, msg: str) -> None:
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


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f'cannot import {path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def freeze_orders(a: argparse.Namespace) -> int:
    a.output.mkdir(parents=True, exist_ok=True)
    req(sha(a.model) == MODEL_SHA256, 'frozen GMN model changed')
    req(sha(a.gmn_result) == GMN_RESULT_SHA256, 'binding GMN result changed')
    req(sha(a.gmn_freeze) == GMN_FREEZE_SHA256, 'GMN full-model freeze changed')
    req(sha(a.quality_source) == QUALITY_SOURCE_SHA256, '#839 source changed')

    gmn_result = json.loads(a.gmn_result.read_text())
    gmn_freeze = json.loads(a.gmn_freeze.read_text())
    req(gmn_result['verdict'] == 'PASS_GMN_REPRESENTATIVE_SHARE_RANKING_V1', 'GMN authorization is not PASS')
    req(gmn_result['sonotaco_2013_2014_access'] is False, 'GMN development SonotaCo boundary changed')
    req(gmn_result['sonotaco_benchmark_authorized_by_this_result'] is True, 'GMN benchmark authorization missing')
    req(gmn_freeze['verdict'] == 'PASS_GMN_REPRESENTATIVE_SHARE_FULL_MODEL_FREEZE', 'GMN model is not frozen')
    req(gmn_freeze['model_sha256'] == MODEL_SHA256, 'GMN model hash metadata changed')
    req(gmn_freeze['feature_dimension'] == RAW_FEATURE_DIM, 'GMN model feature dimension changed')
    req(gmn_freeze['deployment_diversity'] == {'complete_backfill': True, 'family_deletion': False, 'lambda': 0.8, 'scale': 1.0}, 'GMN deployment diversity changed')
    for k in ('sonotaco_2013_2014_access', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        req(gmn_freeze[k] is False, f'GMN freeze firewall changed: {k}')
    req(gmn_freeze['blind_exclusion'] == [20.0, 55.0], 'GMN blind exclusion changed')

    model = joblib.load(a.model)
    req(getattr(model, 'n_features_in_', None) == RAW_FEATURE_DIM, 'frozen model expects wrong feature count')
    qmod = load_module(a.quality_source, 'frozen_839_representative_share_compat')

    routes: dict[str, Any] = {}
    for route in ('sugar', 'hdbscan'):
        root = a.payload_root / route
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fam = json.loads((root / 'family_memberships.json').read_text())
        req(meta['truth_accessed'] is False and fam['truth_accessed'] is False, f'{route} pretruth marker changed')
        req(meta['feature_dimension'] == FULL_FEATURE_DIM, f'{route} feature dimension changed')
        req(meta['feature_blocks'] == {'raw_839': 34, 'relative_noncat_839': 30, 'rank_percentiles': 3, 'consensus_graph': 4}, f'{route} feature blocks changed')
        req(meta['target_information_access'] is False, f'{route} target firewall changed')
        req(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, f'{route} survey firewall changed')
        ids = list(map(str, meta['family_ids']))
        req(len(ids) == EXPECTED[route]['n'], f'{route} candidate count changed')
        req([str(x['family_id']) for x in fam['families']] == ids, f'{route} membership alignment changed')
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        req(X.shape == (len(ids), FULL_FEATURE_DIM), f'{route} feature shape changed')
        req(C.shape == (len(ids), 8), f'{route} centroid shape changed')
        req(v22.array_sha(X) == meta['feature_sha256'], f'{route} feature bytes changed')
        req(v22.array_sha(C) == meta['centroid_sha256'], f'{route} centroid bytes changed')

        scores = np.asarray(model.predict(X[:, :RAW_FEATURE_DIM]), float)
        req(scores.shape == (len(ids),) and np.isfinite(scores).all(), f'{route} score invalid')
        score_hash = array_sha(scores)
        req(score_hash == EXPECTED[route]['score_sha256'], f'{route} truth-blind score hash changed')
        tie = [(int(meta['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = qmod.diversity_order(scores, C, DIVERSITY['lambda'], DIVERSITY['scale'], tie)
        order = [ids[i] for i in idx]
        req(len(order) == len(ids) and len(set(order)) == len(ids), f'{route} incomplete order')
        oh = order_sha(order)
        req(oh == EXPECTED[route]['order_sha256'], f'{route} truth-blind order hash changed')
        routes[route] = {
            'candidate_count': len(ids),
            'score_sha256': score_hash,
            'order_sha256': oh,
            'complete_order': order,
            'score_min': float(np.min(scores)),
            'score_max': float(np.max(scores)),
        }

    result = {
        'scientific_stage': 'PRETRUTH_GMN_REPRESENTATIVE_SHARE_SONOTACO_COMPAT_ORDER_FREEZE_V1',
        'scientific_role': 'ONE_SHOT_COMPATIBILITY_GENERALIZATION_BENCHMARK_PRETRUTH_ORDER_FREEZE',
        'truth_accessed': False,
        'model_sha256': MODEL_SHA256,
        'gmn_result_sha256': GMN_RESULT_SHA256,
        'gmn_full_model_freeze_sha256': GMN_FREEZE_SHA256,
        'quality_source_sha256': QUALITY_SOURCE_SHA256,
        'raw_feature_dimension': RAW_FEATURE_DIM,
        'full_pretruth_feature_dimension': FULL_FEATURE_DIM,
        'raw_feature_block': [0, 34],
        'diversity': DIVERSITY,
        'v19_fusion_used': False,
        'v31_local_geometry_used': False,
        'model_retrained': False,
        'score_transform_used': False,
        'source_quota_used': False,
        'route_specific_scientific_rule': False,
        'family_deletion': False,
        'routes': routes,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY_COMPATIBILITY_BENCHMARK',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'PRETRUTH_ORDER_FREEZE.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'truth_accessed': False,
        'routes': {r: {k: v for k, v in routes[r].items() if k != 'complete_order'} for r in routes},
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


def evaluate(a: argparse.Namespace) -> int:
    a.output.mkdir(parents=True, exist_ok=True)
    frozen = json.loads(a.order_freeze.read_text())
    req(frozen['truth_accessed'] is False, 'order freeze was not pretruth')
    req(frozen['model_sha256'] == MODEL_SHA256, 'order freeze model changed')
    req(frozen['diversity'] == DIVERSITY, 'order freeze diversity changed')
    for route in ('sugar', 'hdbscan'):
        rr = frozen['routes'][route]
        req(rr['candidate_count'] == EXPECTED[route]['n'], f'{route} order count changed')
        req(rr['score_sha256'] == EXPECTED[route]['score_sha256'], f'{route} frozen score changed')
        req(rr['order_sha256'] == EXPECTED[route]['order_sha256'], f'{route} frozen order changed')
        req(order_sha(list(map(str, rr['complete_order']))) == EXPECTED[route]['order_sha256'], f'{route} embedded order changed')

    truth: dict[tuple[str, int], Any] = {}
    evaluation: dict[tuple[str, int], Any] = {}
    for route in ('sugar', 'hdbscan'):
        for year in (2013, 2014):
            truth[(route, year)] = json.loads((a.truth_root / f'truth_{route}_{year}.json').read_text())
            evaluation[(route, year)] = json.loads((a.truth_root / f'evaluation_{route}_{year}.json').read_text())

    panels: list[dict[str, Any]] = []
    for route in ('sugar', 'hdbscan'):
        fam_payload = json.loads((a.payload_root / route / 'family_memberships.json').read_text())
        fams = list(fam_payload['families'])
        order = list(map(str, frozen['routes'][route]['complete_order']))
        ranked = v22.rerank(fams, order)
        for year in (2013, 2014):
            budget = int(evaluation[(route, year)]['candidate_budget']['comparator_budget'])
            cur = v22.evaluate(ranked, truth[(route, year)], budget)
            lit = evaluation[(route, year)]['comparator_summary']
            lm = float(lit['macro_f1'])
            lr = int(lit['recovered_f1_gt_0_5'])
            exp_lm, exp_lr = LITERATURE[(route, year)]
            req(abs(lm - exp_lm) < 1e-12 and lr == exp_lr, f'{route} {year} literature comparator changed')
            cm = float(cur['macro_f1'])
            cr = int(cur['recovered_f1_gt_0_5'])
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
    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_GMN_REPRESENTATIVE_SHARE_COMPATIBILITY_V1',
        'scientific_role': 'ONE_SHOT_COMPATIBILITY_GENERALIZATION_BENCHMARK_NOT_EXTERNAL_VALIDATION',
        'verdict': 'PASS_GMN_REPRESENTATIVE_SHARE_SONOTACO_COMPATIBILITY_4_OF_4' if passed else 'FAIL_GMN_REPRESENTATIVE_SHARE_SONOTACO_COMPATIBILITY',
        'panel_wins': wins,
        'panels': panels,
        'order_freeze_sha256': sha(a.order_freeze),
        'route_order_sha256': {route: frozen['routes'][route]['order_sha256'] for route in ('sugar', 'hdbscan')},
        'model_sha256': MODEL_SHA256,
        'model_retrained': False,
        'model_or_target_changed_after_gmn': False,
        'feature_subset_changed': False,
        'score_transform_used': False,
        'diversity_changed': False,
        'v19_fusion_used': False,
        'v31_local_geometry_used': False,
        'source_quota_used': False,
        'source_normalization_used': False,
        'route_specific_scientific_rule': False,
        'budget_specific_rule': False,
        'topk_or_rank_window_rule': False,
        'boundary_identity_used': False,
        'oracle_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY_COMPATIBILITY_BENCHMARK',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'SONOTACO_COMPATIBILITY_RESULT.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command', required=True)

    f = sub.add_parser('freeze')
    f.add_argument('--model', type=Path, required=True)
    f.add_argument('--gmn-result', type=Path, required=True)
    f.add_argument('--gmn-freeze', type=Path, required=True)
    f.add_argument('--quality-source', type=Path, required=True)
    f.add_argument('--payload-root', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)

    e = sub.add_parser('evaluate')
    e.add_argument('--payload-root', type=Path, required=True)
    e.add_argument('--truth-root', type=Path, required=True)
    e.add_argument('--order-freeze', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)

    a = p.parse_args()
    if a.command == 'freeze':
        return freeze_orders(a)
    return evaluate(a)


if __name__ == '__main__':
    raise SystemExit(main())

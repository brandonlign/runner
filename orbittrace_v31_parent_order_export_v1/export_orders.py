#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

ROUTES = ('sugar', 'hdbscan')
YEARS = (2013, 2014)
FEATURE_DIM = 71
RECOVERY = 0.5
EXPECTED = {
    'sugar': {
        'margin13': 'ed083a89f4e133387bce031b37dab48dd28a3115dd8d43745738dd597ad39364',
        'margin14': '1a912b48132132495e0a604126d423fc81b98c50a9d24cf0cf138474f933317f',
        'combined': '7bfaefa16a6680ea9f4fd927c3888d1aabb94ccde30fcd6c4cc5f256319e8124',
        'local_order': '71c5ac75889aeeb10a569e7f9ac576616cca4670adf62f9ea04ed3a7e0e8827e',
        'fused_order': '5b3d27e11079f36148bbfb8bfdab60882fae380143fcfd84c6dc290c53295aae',
    },
    'hdbscan': {
        'margin13': '99520a9f07b7cf188002fb79ba03592ffda8724f43c8adfeb97541f038ffdb19',
        'margin14': 'd989def64913d7d9807c6d2433642fdde5e29d031d315ddff5a8353668f19d00',
        'combined': '647e81df101ba7b0e511e618004dc2f01fae166cc78d55461f02a9c811650e7d',
        'local_order': '9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595',
        'fused_order': '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d',
    },
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def order_sha(order: list[str]) -> str:
    return hashlib.sha256('\n'.join(order).encode()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--sugar-root', type=Path, required=True)
    p.add_argument('--hdbscan-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--ranker-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    require(v22.sha(a.ranker_source) == v24.RANKER_SOURCE_SHA, '#839 ranker source changed')

    roots = {'sugar': a.sugar_root, 'hdbscan': a.hdbscan_root}
    truth = {}
    for route in ROUTES:
        for year in YEARS:
            truth[(route, year)] = json.loads((a.truth_root / f'truth_{route}_{year}.json').read_text())

    ranker = v22.load_module(a.ranker_source, 'frozen_839_v31_parent_export')
    route_data = {}
    xs = []
    y13s = []
    y14s = []
    groups: list[str] = []
    offsets = {}
    cursor = 0

    for route in ROUTES:
        root = roots[route]
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        payload = json.loads((root / 'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and payload['truth_accessed'] is False, f'{route} pretruth identity failed')
        ids = list(map(str, meta['family_ids']))
        fams = payload['families']
        require([str(f['family_id']) for f in fams] == ids, f'{route} family alignment changed')
        x = np.load(root / 'features.npy', allow_pickle=False)
        c = np.load(root / 'centroids.npy', allow_pickle=False)
        require(x.shape == (len(ids), FEATURE_DIM) and c.shape == (len(ids), 8), f'{route} array shape changed')
        require(v22.array_sha(x) == meta['feature_sha256'] and v22.array_sha(c) == meta['centroid_sha256'], f'{route} array hash changed')

        by_year = {year: truth[(route, year)] for year in YEARS}
        eligible = v22.eligible_from_year_truth(by_year)
        hidden = {}
        hidden.update(by_year[2013])
        hidden.update(by_year[2014])
        base_truth = [v22.family_truth(f, hidden, eligible) for f in fams]
        y13 = []
        y14 = []
        route_groups = []
        for i, (family, t) in enumerate(zip(fams, base_truth)):
            label = t['best_label']
            route_groups.append(('SHOWER/' + str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                a13 = a14 = 0.0
            else:
                a13, a14 = v24.annual_f1_for_fixed_label(family, str(label), by_year)
            y13.append(float(a13))
            y14.append(float(a14))
        offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        xs.append(x)
        y13s.append(np.asarray(y13, dtype=float))
        y14s.append(np.asarray(y14, dtype=float))
        groups.extend(route_groups)
        route_data[route] = {'meta': meta, 'ids': ids, 'centroids': c}

    xall = np.vstack(xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    margin13 = np.zeros(cursor, dtype=float)
    margin14 = np.zeros(cursor, dtype=float)

    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        mu = np.mean(xall[tr], axis=0)
        sd = np.std(xall[tr], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        ztr = (xall[tr] - mu[None, :]) / scale[None, :]
        zte = (xall[te] - mu[None, :]) / scale[None, :]
        te_idx = np.where(te)[0]
        for yall, out in ((y13all, margin13), (y14all, margin14)):
            pos = yall[tr] > RECOVERY
            neg = ~pos
            require(pos.any() and neg.any(), f'fold {fold} lacks references')
            pmat = ztr[pos]
            nmat = ztr[neg]
            for j, global_i in enumerate(te_idx.tolist()):
                dpos = float(np.min(np.linalg.norm(pmat - zte[j][None, :], axis=1)))
                dneg = float(np.min(np.linalg.norm(nmat - zte[j][None, :], axis=1)))
                out[global_i] = dneg - dpos

    combined = np.minimum(margin13, margin14)
    routes_out = {}
    for route in ROUTES:
        lo, hi = offsets[route]
        rd = route_data[route]
        ids = rd['ids']
        exp = EXPECTED[route]
        require(v22.array_sha(margin13[lo:hi]) == exp['margin13'], f'{route} 2013 margin hash mismatch')
        require(v22.array_sha(margin14[lo:hi]) == exp['margin14'], f'{route} 2014 margin hash mismatch')
        require(v22.array_sha(combined[lo:hi]) == exp['combined'], f'{route} combined margin hash mismatch')
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(combined[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        local_order = [ids[i] for i in idx]
        require(order_sha(local_order) == exp['local_order'], f'{route} local order hash mismatch')
        v19_order = list(map(str, rd['meta']['v19_order']))
        fused = list(v19.fusion_orders(local_order, v19_order)['rank_sum'])
        require(order_sha(fused) == exp['fused_order'], f'{route} fused order hash mismatch')
        routes_out[route] = {
            'candidate_count': len(fused),
            'v31_fused_order': fused,
            'v31_fused_order_sha256': order_sha(fused),
            'local_diversity_order_sha256': order_sha(local_order),
            'annual_margin_2013_sha256': v22.array_sha(margin13[lo:hi]),
            'annual_margin_2014_sha256': v22.array_sha(margin14[lo:hi]),
            'combined_margin_sha256': v22.array_sha(combined[lo:hi]),
        }

    result = {
        'schema': 'ORBITTRACE_V31_PARENT_ORDERS_EXPORT_V1',
        'scientific_role': 'PROVENANCE_RECONSTRUCTION_ONLY',
        'source_v31_workflow_run_id': 31449126218,
        'source_v31_artifact_id': 9085657207,
        'source_v31_artifact_digest': 'sha256:6a5c791dcab88bba956205e3453b8357631510aaff5ca9c4b2e29ef6208a9577',
        'routes': routes_out,
        'scientific_change': False,
        'sonotaco_truth_accessed_only_to_reconstruct_existing_v31_parent': True,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
        'verdict': 'PASS_EXACT_V31_PARENT_ORDER_RECONSTRUCTION',
    }
    path = a.output / 'V31_PARENT_ORDERS_EXPORT_V1.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'route_hashes': {r: routes_out[r]['v31_fused_order_sha256'] for r in ROUTES}}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

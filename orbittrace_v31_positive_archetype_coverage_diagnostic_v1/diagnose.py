#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM = 71
RECOVERY = 0.5
EXPECTED_V31 = {
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


def median_or_none(values: list[int]) -> float | None:
    return None if not values else float(np.median(np.asarray(values, dtype=float)))


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

    for route in v24.ROUTES:
        root = roots[route]
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp = json.loads((root / 'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension'] == FEATURE_DIM and fp['truth_accessed'] is False, f'{route} invalid pretruth payload')
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        require(X.shape[1] == FEATURE_DIM and C.shape[1] == 8, f'{route} array shape changed')
        require(v22.array_sha(X) == meta['feature_sha256'] and v22.array_sha(C) == meta['centroid_sha256'], f'{route} array identity changed')

    truth = {}
    frozen_eval = {}
    for route, year in v24.PANELS:
        truth[(route, year)] = json.loads((a.truth_root / f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route, year)] = json.loads((a.truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(a.ranker_source, 'frozen_839_positive_archetype_diag')
    route_data = {}
    Xs, y13s, y14s, groups = [], [], [], []
    route_offsets = {}
    cursor = 0
    for route in v24.ROUTES:
        root = roots[route]
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp = json.loads((root / 'family_memberships.json').read_text())
        ids = list(map(str, meta['family_ids']))
        fams = fp['families']
        require([str(f['family_id']) for f in fams] == ids, f'{route} family order changed')
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        by = {y: truth[(route, y)] for y in v24.YEARS}
        eligible = v22.eligible_from_year_truth(by)
        hidden = {}
        hidden.update(by[2013]); hidden.update(by[2014])
        base = [v22.family_truth(f, hidden, eligible) for f in fams]
        y13, y14, rg = [], [], []
        for i, (f, t) in enumerate(zip(fams, base)):
            label = t['best_label']
            rg.append(('SHOWER/' + str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                q13 = q14 = 0.0
            else:
                q13, q14 = v24.annual_f1_for_fixed_label(f, str(label), by)
            y13.append(float(q13)); y14.append(float(q14))
        route_offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        Xs.append(X); y13s.append(np.asarray(y13, dtype=float)); y14s.append(np.asarray(y14, dtype=float)); groups.extend(rg)
        route_data[route] = {'meta': meta, 'fams': fams, 'ids': ids, 'centroids': C, 'groups': rg, 'y13': np.asarray(y13, dtype=float), 'y14': np.asarray(y14, dtype=float)}

    Xall = np.vstack(Xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM) and len(y13all) == len(y14all) == len(groups) == cursor, 'stacked input mismatch')
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)

    margin13 = np.zeros(cursor, dtype=float)
    margin14 = np.zeros(cursor, dtype=float)
    pos_ref_family = {2013: [''] * cursor, 2014: [''] * cursor}
    pos_ref_group = {2013: [''] * cursor, 2014: [''] * cursor}
    global_ids = []
    global_routes = []
    for route in v24.ROUTES:
        global_ids.extend(route_data[route]['ids'])
        global_routes.extend([route] * len(route_data[route]['ids']))

    fold_diag = []
    for fold in range(5):
        tr = folds != fold; te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f'group leakage fold {fold}')
        mu = np.mean(Xall[tr], axis=0)
        sd = np.std(Xall[tr], axis=0, ddof=0)
        scale = sd.copy(); scale[scale == 0.0] = 1.0
        Ztr = (Xall[tr] - mu[None, :]) / scale[None, :]
        Zte = (Xall[te] - mu[None, :]) / scale[None, :]
        tr_idx = np.where(tr)[0]
        te_idx = np.where(te)[0]
        annual_diag = {}
        for year, yall, out in ((2013, y13all, margin13), (2014, y14all, margin14)):
            pos = yall[tr] > RECOVERY
            neg = ~pos
            require(pos.any() and neg.any(), f'{year} fold {fold} lacks positive/nonpositive references')
            pos_local = np.where(pos)[0]
            P = Ztr[pos]
            N = Ztr[neg]
            for j, global_i in enumerate(te_idx.tolist()):
                dp = np.linalg.norm(P - Zte[j][None, :], axis=1)
                dn = np.linalg.norm(N - Zte[j][None, :], axis=1)
                kp = int(np.argmin(dp))
                dpos = float(dp[kp]); dneg = float(np.min(dn))
                out[global_i] = dneg - dpos
                ref_global = int(tr_idx[int(pos_local[kp])])
                pos_ref_family[year][global_i] = str(global_ids[ref_global])
                pos_ref_group[year][global_i] = str(groups[ref_global])
                require(pos_ref_group[year][global_i].startswith('SHOWER/'), f'{year} nearest positive reference is not shower group')
            annual_diag[str(year)] = {'positive_references': int(pos.sum()), 'nonpositive_references': int(neg.sum())}
        fold_diag.append({'fold': fold, 'train_examples': int(tr.sum()), 'test_examples': int(te.sum()), 'annual_references': annual_diag})

    combined = np.minimum(margin13, margin14)
    require(np.all(np.isfinite(combined)), 'nonfinite v31 margin')
    route_orders = {}
    route_ranked = {}
    for route in v24.ROUTES:
        lo, hi = route_offsets[route]
        rd = route_data[route]
        tie = [(int(rd['meta']['tie_rank'][i]), rd['ids'][i]) for i in range(len(rd['ids']))]
        idx = ranker.diversity_order(combined[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        local_order = [rd['ids'][i] for i in idx]
        fused = list(v19.fusion_orders(local_order, list(map(str, rd['meta']['v19_order'])))['rank_sum'])
        route_orders[route] = {'local': local_order, 'fused': fused, 'local_sha256': order_sha(local_order), 'fused_sha256': order_sha(fused)}
        route_ranked[route] = v22.rerank(rd['fams'], fused)

    reproduction = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(route_ranked[route], truth[(route, year)], budget)
        exp = EXPECTED_V31[(route, year)]
        require(abs(float(cur['macro_f1']) - float(exp[0])) < 1e-12 and int(cur['recovered_f1_gt_0_5']) == int(exp[1]), f'v31 reproduction mismatch {route} {year}')
        reproduction.append({'comparator': route, 'year': year, **cur})

    # HDB only: diagnose fixed-budget positive-reference archetype coverage. No new ordering is evaluated.
    route = 'hdbscan'
    lo, hi = route_offsets[route]
    rd = route_data[route]
    fused = route_orders[route]['fused']
    local_index = {fid: i for i, fid in enumerate(rd['ids'])}
    fused_rank = {fid: i + 1 for i, fid in enumerate(fused)}

    candidate_rows = {}
    for fid in rd['ids']:
        i = local_index[fid]
        gi = lo + i
        sig = [pos_ref_group[2013][gi], pos_ref_group[2014][gi]]
        candidate_rows[fid] = {
            'family_id': fid,
            'v31_fused_rank': int(fused_rank[fid]),
            'strict_group': str(rd['groups'][i]),
            'annual_f1_2013': float(rd['y13'][i]),
            'annual_f1_2014': float(rd['y14'][i]),
            'nearest_positive_family_2013': pos_ref_family[2013][gi],
            'nearest_positive_group_2013': sig[0],
            'nearest_positive_family_2014': pos_ref_family[2014][gi],
            'nearest_positive_group_2014': sig[1],
            'positive_archetype_signature': sig,
            'margin_2013': float(margin13[gi]),
            'margin_2014': float(margin14[gi]),
            'combined_margin': float(combined[gi]),
        }

    annual = {}
    for year, yvals in ((2013, rd['y13']), (2014, rd['y14'])):
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        top_ids = fused[:budget]
        top_sigs = [tuple(candidate_rows[fid]['positive_archetype_signature']) for fid in top_ids]
        top_sig_set = set(top_sigs)
        collisions = defaultdict(list)
        for fid, sig in zip(top_ids, top_sigs):
            collisions[sig].append(fid)
        collision_rows = [
            {'positive_archetype_signature': list(sig), 'families': fids, 'slots': len(fids)}
            for sig, fids in sorted(collisions.items()) if len(fids) > 1
        ]

        group_candidates = defaultdict(list)
        for i, fid in enumerate(rd['ids']):
            g = str(rd['groups'][i])
            if g.startswith('SHOWER/') and float(yvals[i]) > RECOVERY:
                group_candidates[g].append(fid)
        recoverable_rows = []
        for g, fids in sorted(group_candidates.items()):
            rep = min(fids, key=lambda x: fused_rank[x])
            row = candidate_rows[rep]
            rank = int(row['v31_fused_rank'])
            sig = tuple(row['positive_archetype_signature'])
            recoverable_rows.append({
                'group': g,
                'representative_family_id': rep,
                'representative_annual_f1': float(rd['y13'][local_index[rep]] if year == 2013 else rd['y14'][local_index[rep]]),
                'v31_fused_rank': rank,
                'surfaced': bool(rank <= budget),
                'positive_archetype_signature': list(sig),
                'signature_novel_vs_top_budget': bool(sig not in top_sig_set),
            })
        missed = [r for r in recoverable_rows if not r['surfaced']]
        novel = [r for r in missed if r['signature_novel_vs_top_budget']]
        covered = [r for r in missed if not r['signature_novel_vs_top_budget']]
        annual[str(year)] = {
            'budget': budget,
            'top_budget_families': [candidate_rows[fid] for fid in top_ids],
            'top_budget_unique_signature_count': len(top_sig_set),
            'top_budget_duplicate_slots': int(budget - len(top_sig_set)),
            'top_budget_collision_sets': collision_rows,
            'recoverable_groups': len(recoverable_rows),
            'surfaced_recoverable_groups': int(sum(r['surfaced'] for r in recoverable_rows)),
            'missed_recoverable_groups': len(missed),
            'missed_novel_signature_count': len(novel),
            'missed_novel_signature_fraction': float(len(novel) / len(missed)) if missed else None,
            'missed_covered_signature_count': len(covered),
            'missed_novel_signature_rank_median': median_or_none([int(r['v31_fused_rank']) for r in novel]),
            'missed_covered_signature_rank_median': median_or_none([int(r['v31_fused_rank']) for r in covered]),
            'recoverable_group_rows': recoverable_rows,
        }

    result = {
        'verdict': 'PASS_V31_POSITIVE_ARCHETYPE_COVERAGE_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED',
        'question': 'whether exact v31 tiny HDB budgets contain repeated ordered annual nearest-positive reference-group signatures while missed recoverable groups contain signatures absent from the selected set',
        'signature_definition': ['nearest_positive_group_2013', 'nearest_positive_group_2014'],
        'signature_ordered_by_year': True,
        'v31_reproduction': reproduction,
        'v31_hdb_fused_order_sha256': route_orders['hdbscan']['fused_sha256'],
        'annual': annual,
        'candidate_signature_rows': [candidate_rows[fid] for fid in fused],
        'fold_diagnostics': fold_diag,
        'new_rank_or_score_evaluated': False,
        'successor_selected': False,
        'signature_search': False,
        'distance_threshold_selected': False,
        'replacement_rule_evaluated': False,
        'cutoff_selected': False,
        'feature_search': False,
        'metric_search': False,
        'k_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'post_result_second_search': False,
        'oracle_identity_hardcoded': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (a.output / 'V31_POSITIVE_ARCHETYPE_COVERAGE_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'annual': {y: {k: v for k, v in d.items() if k not in ('top_budget_families', 'top_budget_collision_sets', 'recoverable_group_rows')} for y, d in annual.items()},
        'collisions': {y: d['top_budget_collision_sets'] for y, d in annual.items()},
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

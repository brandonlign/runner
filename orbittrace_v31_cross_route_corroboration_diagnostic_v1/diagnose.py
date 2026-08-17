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
EXPECTED = {
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


def median_or_none(xs):
    return None if not xs else float(np.median(np.asarray(xs, dtype=float)))


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

    ranker = v22.load_module(a.ranker_source, 'frozen_839_cross_route_diag')
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
        hidden = {}; hidden.update(by[2013]); hidden.update(by[2014])
        base_truth = [v22.family_truth(f, hidden, eligible) for f in fams]
        y13, y14, rg = [], [], []
        for i, (f, t) in enumerate(zip(fams, base_truth)):
            label = t['best_label']
            rg.append(('SHOWER/' + str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                q13 = q14 = 0.0
            else:
                q13, q14 = v24.annual_f1_for_fixed_label(f, str(label), by)
            y13.append(float(q13)); y14.append(float(q14))
        route_offsets[route] = (cursor, cursor + len(ids)); cursor += len(ids)
        Xs.append(X); y13s.append(np.asarray(y13, dtype=float)); y14s.append(np.asarray(y14, dtype=float)); groups.extend(rg)
        route_data[route] = {
            'meta': meta, 'fams': fams, 'ids': ids, 'centroids': C,
            'groups': rg, 'y13': np.asarray(y13, dtype=float), 'y14': np.asarray(y14, dtype=float),
            'event_sets': [set(map(str, f['event_ids'])) for f in fams],
        }

    Xall = np.vstack(Xs); y13all = np.concatenate(y13s); y14all = np.concatenate(y14s); groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM), 'stacked feature mismatch')
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    m13 = np.zeros(cursor, dtype=float); m14 = np.zeros(cursor, dtype=float)
    fold_diag = []
    for fold in range(5):
        tr = folds != fold; te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f'group leakage fold {fold}')
        mu = np.mean(Xall[tr], axis=0); sd = np.std(Xall[tr], axis=0, ddof=0); scale = sd.copy(); scale[scale == 0.0] = 1.0
        Ztr = (Xall[tr] - mu[None, :]) / scale[None, :]; Zte = (Xall[te] - mu[None, :]) / scale[None, :]
        te_idx = np.where(te)[0]
        annual = {}
        for year, yall, out in ((2013, y13all, m13), (2014, y14all, m14)):
            pos = yall[tr] > RECOVERY; neg = ~pos
            require(pos.any() and neg.any(), f'{year} fold {fold} lacks references')
            P = Ztr[pos]; N = Ztr[neg]
            for j, gi in enumerate(te_idx.tolist()):
                dpos = float(np.min(np.linalg.norm(P - Zte[j][None, :], axis=1)))
                dneg = float(np.min(np.linalg.norm(N - Zte[j][None, :], axis=1)))
                require(np.isfinite(dpos) and np.isfinite(dneg), 'nonfinite distance')
                out[gi] = dneg - dpos
            annual[str(year)] = {'positive_references': int(pos.sum()), 'nonpositive_references': int(neg.sum())}
        fold_diag.append({'fold': fold, 'train_examples': int(tr.sum()), 'test_examples': int(te.sum()), 'annual_references': annual})

    combined = np.minimum(m13, m14)
    route_orders = {}; ranked = {}
    for route in v24.ROUTES:
        lo, hi = route_offsets[route]; rd = route_data[route]
        tie = [(int(rd['meta']['tie_rank'][i]), rd['ids'][i]) for i in range(len(rd['ids']))]
        idx = ranker.diversity_order(combined[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        local = [rd['ids'][i] for i in idx]
        fused = list(v19.fusion_orders(local, list(map(str, rd['meta']['v19_order'])))['rank_sum'])
        route_orders[route] = {'local': local, 'fused': fused, 'local_sha256': order_sha(local), 'fused_sha256': order_sha(fused)}
        ranked[route] = v22.rerank(rd['fams'], fused)

    reproduction = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(ranked[route], truth[(route, year)], budget)
        exp = EXPECTED[(route, year)]
        require(abs(float(cur['macro_f1']) - exp[0]) < 1e-12 and int(cur['recovered_f1_gt_0_5']) == exp[1], f'v31 reproduction mismatch {route} {year}')
        reproduction.append({'comparator': route, 'year': year, **cur})

    # Freeze truth-free HDB -> Sugar membership corroborators after both exact v31 orders exist.
    s = route_data['sugar']; h = route_data['hdbscan']
    s_rank = {fid: i + 1 for i, fid in enumerate(route_orders['sugar']['fused'])}
    h_rank = {fid: i + 1 for i, fid in enumerate(route_orders['hdbscan']['fused'])}
    h_index = {fid: i for i, fid in enumerate(h['ids'])}
    matches = {}
    for hi, hfid in enumerate(h['ids']):
        H = h['event_sets'][hi]
        best = None
        for si, sfid in enumerate(s['ids']):
            S = s['event_sets'][si]
            ov = len(H & S)
            if ov == 0:
                continue
            jac = float(ov / len(H | S))
            key = (jac, ov, -s_rank[sfid], sfid)
            if best is None or key > best[0]:
                best = (key, sfid, si, jac, ov)
        if best is None:
            matches[hfid] = {
                'hdb_family_id': hfid, 'hdb_v31_fused_rank': int(h_rank[hfid]),
                'sugar_family_id': None, 'max_jaccard': 0.0, 'shared_event_count': 0,
                'exact_membership_equal': False, 'sugar_v31_fused_rank': None, 'sugar_v31_rank_percentile': None,
            }
        else:
            _, sfid, si, jac, ov = best
            matches[hfid] = {
                'hdb_family_id': hfid, 'hdb_v31_fused_rank': int(h_rank[hfid]),
                'sugar_family_id': sfid, 'max_jaccard': float(jac), 'shared_event_count': int(ov),
                'exact_membership_equal': bool(H == s['event_sets'][si]),
                'sugar_v31_fused_rank': int(s_rank[sfid]),
                'sugar_v31_rank_percentile': float((s_rank[sfid] - 1) / max(1, len(s['ids']) - 1)),
            }

    annual = {}
    for year, yvals in ((2013, h['y13']), (2014, h['y14'])):
        h_budget = int(frozen_eval[('hdbscan', year)]['candidate_budget']['comparator_budget'])
        s_budget = int(frozen_eval[('sugar', year)]['candidate_budget']['comparator_budget'])
        group_candidates = defaultdict(list)
        for i, fid in enumerate(h['ids']):
            g = str(h['groups'][i])
            if g.startswith('SHOWER/') and float(yvals[i]) > RECOVERY:
                group_candidates[g].append(fid)
        reps = []
        for g, fids in sorted(group_candidates.items()):
            rep = min(fids, key=lambda x: h_rank[x])
            m = matches[rep]
            strong = bool(m['max_jaccard'] >= 0.5 and m['sugar_v31_fused_rank'] is not None and m['sugar_v31_fused_rank'] <= s_budget)
            reps.append({
                'group': g, 'representative_family_id': rep, 'hdb_v31_fused_rank': int(h_rank[rep]),
                'surfaced': bool(h_rank[rep] <= h_budget), 'annual_f1': float(yvals[h_index[rep]]),
                **m, 'strong_cross_route_corroboration': strong,
            })
        surfaced = [x for x in reps if x['surfaced']]; missed = [x for x in reps if not x['surfaced']]

        def summary(xs):
            if not xs:
                return {'count': 0}
            ranks = [x['sugar_v31_fused_rank'] for x in xs if x['sugar_v31_fused_rank'] is not None]
            return {
                'count': len(xs),
                'nonzero_overlap_count': int(sum(x['shared_event_count'] > 0 for x in xs)),
                'jaccard_ge_0_5_count': int(sum(x['max_jaccard'] >= 0.5 for x in xs)),
                'exact_membership_count': int(sum(x['exact_membership_equal'] for x in xs)),
                'matched_sugar_within_budget_count': int(sum(x['sugar_v31_fused_rank'] is not None and x['sugar_v31_fused_rank'] <= s_budget for x in xs)),
                'strong_cross_route_corroboration_count': int(sum(x['strong_cross_route_corroboration'] for x in xs)),
                'strong_cross_route_corroboration_fraction': float(sum(x['strong_cross_route_corroboration'] for x in xs) / len(xs)),
                'median_max_jaccard': median_or_none([x['max_jaccard'] for x in xs]),
                'median_sugar_v31_fused_rank': median_or_none(ranks),
            }

        top_rows = []
        for fid in route_orders['hdbscan']['fused'][:h_budget]:
            i = h_index[fid]; m = matches[fid]
            top_rows.append({
                'family_id': fid, 'hdb_v31_fused_rank': int(h_rank[fid]), 'annual_f1': float(yvals[i]),
                'candidate_recoverable': bool(float(yvals[i]) > RECOVERY),
                **m,
                'strong_cross_route_corroboration': bool(m['max_jaccard'] >= 0.5 and m['sugar_v31_fused_rank'] is not None and m['sugar_v31_fused_rank'] <= s_budget),
            })
        top_rec = [x for x in top_rows if x['candidate_recoverable']]
        top_nonrec = [x for x in top_rows if not x['candidate_recoverable']]
        annual[str(year)] = {
            'hdb_budget': h_budget, 'sugar_budget': s_budget,
            'recoverable_groups': len(reps), 'surfaced_recoverable_groups': len(surfaced), 'missed_recoverable_groups': len(missed),
            'surfaced_summary': summary(surfaced), 'missed_summary': summary(missed),
            'top_budget_recoverable_candidate_summary': summary(top_rec),
            'top_budget_nonrecoverable_candidate_summary': summary(top_nonrec),
            'recoverable_group_rows': reps, 'top_budget_candidate_rows': top_rows,
        }

    result = {
        'verdict': 'PASS_V31_CROSS_ROUTE_CORROBORATION_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED',
        'v31_reproduction': reproduction,
        'v31_order_sha256': {r: route_orders[r]['fused_sha256'] for r in v24.ROUTES},
        'match_definition': 'maximum event-membership Jaccard; tie shared-event count, lower Sugar v31 rank, Sugar family id',
        'strong_corroboration_definition': 'max_jaccard>=0.5 and matched Sugar v31 rank within frozen year-specific Sugar literature budget',
        'annual': annual,
        'hdb_to_sugar_matches': [matches[fid] for fid in route_orders['hdbscan']['fused']],
        'fold_diagnostics': fold_diag,
        'new_rank_or_score_evaluated': False, 'successor_selected': False,
        'alternate_overlap_metric_search': False, 'centroid_match_search': False, 'radius_search': False,
        'event_weight_search': False, 'source_weight_search': False, 'membership_change': False,
        'fusion_search': False, 'selector_search': False, 'oracle_identity_hardcoded': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY', 'maarsy_scientific_access': False, 'dms_scientific_access': False,
        'target_information_access': False, 'target_region_events_accessed': False, 'blind_exclusion': [20.0, 55.0],
    }
    (a.output / 'V31_CROSS_ROUTE_CORROBORATION_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'annual': {y: {k: v for k, v in d.items() if k not in ('recoverable_group_rows','top_budget_candidate_rows')} for y, d in annual.items()},
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

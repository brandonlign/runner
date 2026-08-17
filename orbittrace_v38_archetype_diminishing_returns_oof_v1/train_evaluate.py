#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM = 71
RECOVERY = 0.5
VARIANT = 'positive_archetype_diminishing_returns_v31'
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


def diminishing_returns_order(base_order: list[str], signatures: dict[str, tuple[str, str]]) -> tuple[list[str], list[dict]]:
    """Canonical v38 total order: minimize base_rank * (1 + selected same-signature count)."""
    rank = {fid: i + 1 for i, fid in enumerate(base_order)}
    require(len(rank) == len(base_order), 'duplicate family in base order')
    require(set(signatures) == set(base_order), 'signature/base-order family mismatch')
    remaining = set(base_order)
    counts: Counter[tuple[str, str]] = Counter()
    out: list[str] = []
    trace: list[dict] = []
    while remaining:
        fid = min(
            remaining,
            key=lambda x: (rank[x] * (1 + counts[signatures[x]]), rank[x]),
        )
        sig = signatures[fid]
        occurrence_before = int(counts[sig])
        priority = int(rank[fid] * (1 + occurrence_before))
        out.append(fid)
        trace.append({
            'selected_position': len(out),
            'family_id': fid,
            'v31_fused_rank': int(rank[fid]),
            'signature': list(sig),
            'same_signature_selected_before': occurrence_before,
            'priority': priority,
        })
        counts[sig] += 1
        remaining.remove(fid)
    require(len(out) == len(base_order) and set(out) == set(base_order), 'invalid v38 total order')
    return out, trace


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

    # Immutable pretruth payload identity before truth interpretation.
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

    ranker = v22.load_module(a.ranker_source, 'frozen_839_v38_archetype_dr')
    route_data = {}
    Xs: list[np.ndarray] = []
    y13s: list[np.ndarray] = []
    y14s: list[np.ndarray] = []
    groups: list[str] = []
    global_ids: list[str] = []
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
        hidden.update(by[2013])
        hidden.update(by[2014])
        base_truth = [v22.family_truth(f, hidden, eligible) for f in fams]
        y13: list[float] = []
        y14: list[float] = []
        rg: list[str] = []
        for i, (f, t) in enumerate(zip(fams, base_truth)):
            label = t['best_label']
            rg.append(('SHOWER/' + str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                q13 = q14 = 0.0
            else:
                q13, q14 = v24.annual_f1_for_fixed_label(f, str(label), by)
            y13.append(float(q13))
            y14.append(float(q14))
        route_offsets[route] = (cursor, cursor + len(ids))
        cursor += len(ids)
        Xs.append(X)
        y13s.append(np.asarray(y13, dtype=float))
        y14s.append(np.asarray(y14, dtype=float))
        groups.extend(rg)
        global_ids.extend(ids)
        route_data[route] = {'meta': meta, 'fams': fams, 'ids': ids, 'centroids': C}

    Xall = np.vstack(Xs)
    y13all = np.concatenate(y13s)
    y14all = np.concatenate(y14s)
    groups = list(map(str, groups))
    require(Xall.shape == (cursor, FEATURE_DIM) and len(y13all) == len(y14all) == len(groups) == len(global_ids) == cursor, 'stacked input mismatch')

    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    margin13 = np.zeros(cursor, dtype=float)
    margin14 = np.zeros(cursor, dtype=float)
    pos_ref_group = {2013: [''] * cursor, 2014: [''] * cursor}
    pos_ref_family = {2013: [''] * cursor, 2014: [''] * cursor}
    fold_diag = []

    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        require(tr.any() and te.any(), f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}), f'group leakage fold {fold}')
        mu = np.mean(Xall[tr], axis=0)
        sd = np.std(Xall[tr], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
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
                dpos = float(dp[kp])
                dneg = float(np.min(dn))
                require(np.isfinite(dpos) and np.isfinite(dneg), f'nonfinite nearest distance {year} fold {fold}')
                out[global_i] = dneg - dpos
                ref_global = int(tr_idx[int(pos_local[kp])])
                pos_ref_family[year][global_i] = str(global_ids[ref_global])
                pos_ref_group[year][global_i] = str(groups[ref_global])
                require(pos_ref_group[year][global_i].startswith('SHOWER/'), f'nearest positive reference lacks strict shower group {year} fold {fold}')
            annual_diag[str(year)] = {
                'positive_references': int(pos.sum()),
                'nonpositive_references': int(neg.sum()),
            }
        fold_diag.append({
            'fold': fold,
            'train_examples': int(tr.sum()),
            'test_examples': int(te.sum()),
            'zero_variance_features': int(np.sum(sd == 0.0)),
            'annual_references': annual_diag,
        })

    combined = np.minimum(margin13, margin14)
    require(np.all(np.isfinite(combined)), 'nonfinite combined local-geometry margin')
    for year in (2013, 2014):
        require(all(pos_ref_group[year]), f'missing positive-reference group {year}')

    parent_variants = {}
    successor_variants = {}
    order_diag = {}
    selection_trace = {}

    for route in v24.ROUTES:
        lo, hi = route_offsets[route]
        rd = route_data[route]
        ids = rd['ids']
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(combined[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        local_order = [ids[i] for i in idx]
        v19_order = list(map(str, rd['meta']['v19_order']))
        v31_fused = list(v19.fusion_orders(local_order, v19_order)['rank_sum'])
        parent_variants[route] = v22.rerank(rd['fams'], v31_fused)

        signatures: dict[str, tuple[str, str]] = {}
        local_index = {fid: i for i, fid in enumerate(ids)}
        for fid in ids:
            gi = lo + local_index[fid]
            signatures[fid] = (pos_ref_group[2013][gi], pos_ref_group[2014][gi])
        v38_order, trace = diminishing_returns_order(v31_fused, signatures)
        successor_variants[route] = v22.rerank(rd['fams'], v38_order)
        selection_trace[route] = trace

        order_diag[route] = {
            'annual_margin_2013_sha256': v22.array_sha(margin13[lo:hi]),
            'annual_margin_2014_sha256': v22.array_sha(margin14[lo:hi]),
            'combined_margin_sha256': v22.array_sha(combined[lo:hi]),
            'v31_local_diversity_order_sha256': order_sha(local_order),
            'v31_fused_order_sha256': order_sha(v31_fused),
            'v38_total_order_sha256': order_sha(v38_order),
            'distinct_positive_archetype_signatures': len(set(signatures.values())),
            'selector': 'greedy minimum v31_fused_rank*(1+selected_same_signature_count), tie smaller v31_fused_rank',
            'signature': '(nearest_positive_group_2013,nearest_positive_group_2014)',
            'diversity': {'lambda': 0.8, 'scale': 1.0},
            'v31_fusion': 'equal rank-sum with exact v19',
        }

    parent_controls = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(parent_variants[route], truth[(route, year)], budget)
        exp = PARENT[(route, year)]
        require(abs(float(cur['macro_f1']) - float(exp[0])) < 1e-12 and int(cur['recovered_f1_gt_0_5']) == int(exp[1]), f'v31 parent control mismatch {route} {year}')
        parent_controls.append({'comparator': route, 'year': year, **cur})

    panels = []
    for route, year in v24.PANELS:
        budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
        cur = v22.evaluate(successor_variants[route], truth[(route, year)], budget)
        lit = frozen_eval[(route, year)]['comparator_summary']
        cm = float(cur['macro_f1'])
        cr = int(cur['recovered_f1_gt_0_5'])
        lm = float(lit['macro_f1'])
        lr = int(lit['recovered_f1_gt_0_5'])
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
    wins = sum(int(x['superiority_pair_pass']) for x in panels)
    passed = bool(wins == 4)

    freeze = {'verdict': 'NOT_FROZEN_V38_ARCHETYPE_DIMINISHING_RETURNS_FAIL', 'reference_sha256': None}
    if passed:
        mu = np.mean(Xall, axis=0)
        sd = np.std(Xall, axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        path = a.output / 'v38_archetype_diminishing_returns_reference.npz'
        np.savez_compressed(
            path,
            X=Xall,
            mean=mu,
            scale=scale,
            y13=(y13all > RECOVERY).astype(np.int8),
            y14=(y14all > RECOVERY).astype(np.int8),
            groups=np.asarray(groups, dtype=str),
        )
        freeze = {
            'verdict': 'PASS_V38_FULL_EXPOSED_ARCHETYPE_DIMINISHING_RETURNS_REFERENCE_FREEZE',
            'reference_sha256': v22.sha(path),
            'training_examples': cursor,
            'training_groups': len(set(groups)),
            'feature_dimension': FEATURE_DIM,
            'k': 1,
            'distance': 'ordinary Euclidean after full-training z-score',
            'annual_margin': 'd_nonpositive-d_positive',
            'annual_combiner': 'min(margin_2013,margin_2014)',
            'signature': '(nearest_positive_group_2013,nearest_positive_group_2014)',
            'selector': 'greedy minimum base_v31_rank*(1+selected_same_signature_count)',
            'in_sample_reference_score_used_for_promotion': False,
        }
    (a.output / 'V38_ARCHETYPE_DIMINISHING_RETURNS_MODEL_FREEZE.json').write_text(json.dumps(freeze, indent=2, sort_keys=True) + '\n')

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V38_POSITIVE_ARCHETYPE_DIMINISHING_RETURNS_V1',
        'verdict': 'PASS_V38_ARCHETYPE_DIMINISHING_RETURNS_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V38_ARCHETYPE_DIMINISHING_RETURNS_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'post-v31 parameter-free diminishing returns on repeated ordered annual nearest-positive reference-group signatures',
        'authorizing_diagnostic': '#1058 positive-archetype coverage diagnostic; no successor order evaluated there',
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': parent_controls,
        'feature_dimension': FEATURE_DIM,
        'recovery_f1_threshold': RECOVERY,
        'nearest_k': 1,
        'distance': 'ordinary Euclidean across all 71 fold-training standardized dimensions',
        'scaling': 'fold-training mean and population std; zero std -> 1.0',
        'annual_margin': 'd_nonpositive-d_positive',
        'annual_combiner': 'min(margin_2013,margin_2014)',
        'signature': '(nearest_positive_group_2013,nearest_positive_group_2014)',
        'signature_ordered_by_year': True,
        'selector': 'greedy minimum v31_fused_rank*(1+selected_same_signature_count); tie lower v31_fused_rank',
        'selector_coefficient': None,
        'selector_budget_dependent': False,
        'strict_whole_shower_oof': True,
        'candidate_membership_changed': False,
        'candidate_generation_changed': False,
        'pretruth_feature_changed': False,
        'diversity': {'lambda': 0.8, 'scale': 1.0},
        'v31_fusion': 'one equal rank-sum with exact v19',
        'promotion_variant': VARIANT,
        'panel_wins': wins,
        'panels': panels,
        'fold_diagnostics': fold_diag,
        'order_diagnostics': order_diag,
        'selection_trace': selection_trace,
        'full_model_freeze': freeze,
        'coefficient_search': False,
        'additive_penalty_search': False,
        'hard_dedup_search': False,
        'signature_cap_search': False,
        'occurrence_exponent_search': False,
        'budget_normalized_penalty_search': False,
        'rank_window_search': False,
        'signature_search': False,
        'route_specific_rule': False,
        'k_search': False,
        'metric_search': False,
        'scaling_search': False,
        'feature_search': False,
        'threshold_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'budget_specific_rule': False,
        'oracle_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (a.output / 'V38_ARCHETYPE_DIMINISHING_RETURNS_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'panel_wins': wins, 'panels': panels, 'order_diagnostics': order_diag, 'full_model_freeze': freeze}, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

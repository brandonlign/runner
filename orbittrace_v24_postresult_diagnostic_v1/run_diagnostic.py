#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

ROUTES = ('sugar', 'hdbscan')
YEARS = (2013, 2014)
FEATURE_DIM = 71
V24_RESULT_SHA = 'c8d95bc02ad1436c9924ec14a25bcd36e0eacd960fda1fb33db3a91738fe30cf'
RANKER_SOURCE_SHA = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_V24 = {
    ('sugar', 2013): (0.27806630131631344, 16),
    ('sugar', 2014): (0.32869544907104964, 17),
    ('hdbscan', 2013): (0.14257102406283795, 10),
    ('hdbscan', 2014): (0.12833942693327394, 7),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assignment_details(families: list[dict[str, Any]], truth: dict[str, str], budget: int) -> dict[str, Any]:
    from collections import Counter

    counts = Counter(v for v in truth.values() if v != 'SPORADIC')
    labels = sorted(k for k, n in counts.items() if n >= 4)
    truth_sets = {label: {eid for eid, value in truth.items() if value == label} for label in labels}
    truth_ids = set(truth)
    active = []
    for family in families:
        members = set(map(str, family['event_ids'])) & truth_ids
        if members:
            active.append((int(family['rank']), str(family['family_id']), members))
    active = sorted(active, key=lambda x: (x[0], x[1]))[:int(budget)]
    f1 = np.zeros((len(labels), len(active)), dtype=np.float64)
    for i, label in enumerate(labels):
        actual = truth_sets[label]
        for j, (_rank, _fid, pred) in enumerate(active):
            overlap = len(actual & pred)
            if overlap:
                precision = overlap / len(pred)
                recall = overlap / len(actual)
                f1[i, j] = 2.0 * precision * recall / (precision + recall)
    n = max(len(labels), len(active))
    cost = np.zeros((n, n), dtype=np.float64)
    cost[:len(labels), :len(active)] = -f1
    ri, cj = linear_sum_assignment(cost)
    assigned = []
    for i, j in zip(ri.tolist(), cj.tolist()):
        if i >= len(labels):
            continue
        value = float(f1[i, j]) if j < len(active) else 0.0
        row = {'label': labels[i], 'f1': value, 'recovered_f1_gt_0_5': bool(value > 0.5), 'family_id': None, 'candidate_rank': None}
        if j < len(active):
            row['candidate_rank'] = int(active[j][0])
            row['family_id'] = str(active[j][1])
        assigned.append(row)
    return {
        'eligible_showers': len(labels),
        'candidate_used': len(active),
        'macro_f1': float(np.mean([x['f1'] for x in assigned])) if assigned else 0.0,
        'recovered_f1_gt_0_5': int(sum(x['recovered_f1_gt_0_5'] for x in assigned)),
        'assignments': assigned,
    }


def best_single_family_by_label(families: list[dict[str, Any]], truth: dict[str, str]) -> dict[str, dict[str, Any]]:
    from collections import Counter

    counts = Counter(v for v in truth.values() if v != 'SPORADIC')
    labels = sorted(k for k, n in counts.items() if n >= 4)
    truth_sets = {label: {eid for eid, value in truth.items() if value == label} for label in labels}
    truth_ids = set(truth)
    out: dict[str, dict[str, Any]] = {}
    for label in labels:
        actual = truth_sets[label]
        best = {'label': label, 'family_id': None, 'rank': None, 'f1': 0.0, 'precision': 0.0, 'recall': 0.0, 'overlap': 0}
        for family in families:
            pred = set(map(str, family['event_ids'])) & truth_ids
            if not pred:
                continue
            overlap = len(actual & pred)
            if not overlap:
                continue
            precision = overlap / len(pred)
            recall = overlap / len(actual)
            score = 2.0 * precision * recall / (precision + recall)
            key = (score, precision, overlap, -int(family['rank']), str(family['family_id']))
            cur = (best['f1'], best['precision'], best['overlap'], -(best['rank'] or 10**9), str(best['family_id'] or ''))
            if key > cur:
                best = {
                    'label': label,
                    'family_id': str(family['family_id']),
                    'rank': int(family['rank']),
                    'f1': float(score),
                    'precision': float(precision),
                    'recall': float(recall),
                    'overlap': int(overlap),
                }
        out[label] = best
    return out


def oracle_front(families: list[dict[str, Any]], truth: dict[str, str], budget: int) -> dict[str, Any]:
    best = best_single_family_by_label(families, truth)
    rows = sorted(best.values(), key=lambda r: (-r['f1'], -r['precision'], -r['overlap'], r['label']))
    selected = []
    used = set()
    for row in rows:
        fid = row['family_id']
        if fid is None or fid in used or row['f1'] <= 0:
            continue
        selected.append(fid)
        used.add(fid)
        if len(selected) >= budget:
            break
    by_id = {str(f['family_id']): f for f in families}
    candidate = []
    for rank, fid in enumerate(selected, start=1):
        f = dict(by_id[fid])
        f['rank'] = rank
        candidate.append(f)
    detail = assignment_details(candidate, truth, budget)
    return {'selected_family_ids': selected, 'evaluation': {k: v for k, v in detail.items() if k != 'assignments'}, 'assignments': detail['assignments']}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--v24-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--ranker-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    result_path = a.v24_root / 'result' / 'V24_EXPOSED_TWOHEAD_OOF_RESULT.json'
    require(sha(result_path) == V24_RESULT_SHA, 'v24 result identity changed')
    frozen_result = json.loads(result_path.read_text())
    require(frozen_result['verdict'] == 'FAIL_V24_TWOHEAD_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'v24 verdict changed')
    require(frozen_result['post_result_second_search'] is False, 'v24 post-result search flag changed')
    require(sha(a.ranker_source) == RANKER_SOURCE_SHA, '#839 ranker source changed')

    truth_year: dict[tuple[str, int], dict[str, str]] = {}
    frozen_eval: dict[tuple[str, int], dict[str, Any]] = {}
    for route in ROUTES:
        for year in YEARS:
            truth_year[(route, year)] = json.loads((a.truth_root / f'truth_{route}_{year}.json').read_text())
            frozen_eval[(route, year)] = json.loads((a.truth_root / f'evaluation_{route}_{year}.json').read_text())

    ranker = v22.load_module(a.ranker_source, 'frozen_839_v24_diagnostic')
    route_data: dict[str, dict[str, Any]] = {}
    Xs = []
    y13s = []
    y14s = []
    groups: list[str] = []
    offsets = {}
    cursor = 0

    for route in ROUTES:
        root = a.v24_root / route
        meta = json.loads((root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        payload = json.loads((root / 'family_memberships.json').read_text())
        ids = list(map(str, meta['family_ids']))
        fams = payload['families']
        X = np.load(root / 'features.npy', allow_pickle=False)
        C = np.load(root / 'centroids.npy', allow_pickle=False)
        require(X.shape == (len(ids), FEATURE_DIM), 'feature shape changed')
        by_year = {year: truth_year[(route, year)] for year in YEARS}
        eligible = v22.eligible_from_year_truth(by_year)
        hidden = dict(by_year[2013]); hidden.update(by_year[2014])
        truths = [v22.family_truth(f, hidden, eligible) for f in fams]
        y13 = []; y14 = []; route_groups = []
        for i, (f, t) in enumerate(zip(fams, truths)):
            best_label = t['best_label']
            route_groups.append(('SHOWER/' + str(best_label)) if best_label is not None else (f'NEG/{route}/' + ids[i]))
            if not t['positive'] or best_label is None:
                y13.append(0.0); y14.append(0.0)
            else:
                a13, a14 = v24.annual_f1_for_fixed_label(f, str(best_label), by_year)
                y13.append(a13); y14.append(a14)
        offsets[route] = (cursor, cursor + len(ids)); cursor += len(ids)
        Xs.append(X); y13s.append(np.asarray(y13)); y14s.append(np.asarray(y14)); groups.extend(route_groups)
        route_data[route] = {'meta': meta, 'families': fams, 'ids': ids, 'centroids': C}

    Xall = np.vstack(Xs); y13all = np.concatenate(y13s); y14all = np.concatenate(y14s)
    folds = np.asarray([v22.v1.deterministic_fold(g) for g in groups], dtype=int)
    weights = ranker.grouped_weights(groups)
    oof13 = np.zeros(cursor); oof14 = np.zeros(cursor)
    for fold in range(5):
        train = folds != fold; test = folds == fold
        m13 = ranker.model(); m14 = ranker.model()
        m13.fit(Xall[train], y13all[train], sample_weight=weights[train])
        m14.fit(Xall[train], y14all[train], sample_weight=weights[train])
        oof13[test] = m13.predict(Xall[test]); oof14[test] = m14.predict(Xall[test])
    worst = np.minimum(oof13, oof14)

    replay: dict[str, Any] = {}
    for route in ROUTES:
        lo, hi = offsets[route]
        rd = route_data[route]
        ids = rd['ids']
        tie = [(int(rd['meta']['tie_rank'][i]), ids[i]) for i in range(len(ids))]
        idx = ranker.diversity_order(worst[lo:hi], rd['centroids'], 0.8, 1.0, tie)
        quality = [ids[i] for i in idx]
        v19_order = list(map(str, rd['meta']['v19_order']))
        fused = list(v19.fusion_orders(quality, v19_order)['rank_sum'])
        ranked = v22.rerank(rd['families'], fused)
        route_rows = {'order_sha256': hashlib.sha256('\n'.join(fused).encode()).hexdigest(), 'panels': {}}
        for year in YEARS:
            budget = int(frozen_eval[(route, year)]['candidate_budget']['comparator_budget'])
            details = assignment_details(ranked, truth_year[(route, year)], budget)
            expected = EXPECTED_V24[(route, year)]
            require(abs(details['macro_f1'] - expected[0]) < 1e-12 and details['recovered_f1_gt_0_5'] == expected[1], f'v24 replay mismatch {route} {year}')
            best = best_single_family_by_label(ranked, truth_year[(route, year)])
            assigned_recovered = {row['label'] for row in details['assignments'] if row['recovered_f1_gt_0_5']}
            missed = []
            for label, row in best.items():
                if label in assigned_recovered:
                    continue
                if row['f1'] > 0.5:
                    missed.append(row)
            missed.sort(key=lambda r: (r['rank'] if r['rank'] is not None else 10**9, -r['f1'], r['label']))
            top_profile = []
            for family in ranked[:min(30, len(ranked))]:
                fid = str(family['family_id'])
                best_row = max(
                    ({'label': lab, **vals} for lab, vals in best.items() if vals['family_id'] == fid),
                    key=lambda x: x['f1'],
                    default=None,
                )
                top_profile.append({'rank': int(family['rank']), 'family_id': fid, 'best_year_label': None if best_row is None else best_row['label'], 'best_year_f1': 0.0 if best_row is None else best_row['f1']})
            oracle = oracle_front(ranked, truth_year[(route, year)], budget)
            route_rows['panels'][str(year)] = {
                'budget': budget,
                'replay_evaluation': {k: v for k, v in details.items() if k != 'assignments'},
                'assignments': details['assignments'],
                'strong_missed_labels_best_family': missed[:25],
                'top30_best_year_match_profile': top_profile,
                'unique_label_oracle_front': oracle,
            }
        replay[route] = route_rows

    h14 = replay['hdbscan']['panels']['2014']
    strong_below = [r for r in h14['strong_missed_labels_best_family'] if r['rank'] is not None and r['rank'] > h14['budget']]
    conclusion = {
        'hdbscan_2014_strong_unrecovered_labels_with_family_below_budget': len(strong_below),
        'hdbscan_2014_first_strong_below_budget': strong_below[:10],
        'hdbscan_2014_oracle_macro_f1': h14['unique_label_oracle_front']['evaluation']['macro_f1'],
        'hdbscan_2014_oracle_recovered': h14['unique_label_oracle_front']['evaluation']['recovered_f1_gt_0_5'],
        'diagnosis': 'RANK_PLACEMENT_HEADROOM_REMAINS' if strong_below and h14['unique_label_oracle_front']['evaluation']['recovered_f1_gt_0_5'] >= 9 else 'FIXED_MEMBERSHIP_OR_UNIVERSE_MAY_BE_BINDING',
    }

    result = {
        'stage': 'V24_POSTRESULT_ARTIFACT_ONLY_DIAGNOSTIC',
        'v24_result_sha256': V24_RESULT_SHA,
        'v24_science_replayed_exactly': True,
        'replay': replay,
        'conclusion': conclusion,
        'new_method_evaluated': False,
        'parameter_search': False,
        'candidate_change': False,
        'membership_change': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
    }
    out = a.output / 'V24_POSTRESULT_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'conclusion': conclusion, 'replay_hdbscan_2013': replay['hdbscan']['panels']['2013']['replay_evaluation'], 'replay_hdbscan_2014': replay['hdbscan']['panels']['2014']['replay_evaluation']}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

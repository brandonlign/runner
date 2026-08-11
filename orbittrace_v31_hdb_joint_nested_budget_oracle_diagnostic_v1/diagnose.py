#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22

YEARS = (2013, 2014)
BUDGET = {2013: 11, 2014: 9}
RECOVERY = 0.5
STRICT_EPS = 1e-9


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def annual_matrix(families: list[dict[str, Any]], truth: dict[str, str]) -> tuple[list[str], np.ndarray]:
    counts = Counter(v for v in truth.values() if v != 'SPORADIC')
    labels = sorted(k for k, n in counts.items() if n >= 4)
    truth_sets = {l: {eid for eid, v in truth.items() if v == l} for l in labels}
    truth_ids = set(truth)
    mat = np.zeros((len(labels), len(families)), dtype=np.float64)
    for j, family in enumerate(families):
        pred = set(map(str, family['event_ids'])) & truth_ids
        require(bool(pred), f'family {family["family_id"]} inactive in annual evaluator')
        for i, label in enumerate(labels):
            actual = truth_sets[label]
            overlap = len(actual & pred)
            if overlap:
                precision = overlap / len(pred)
                recall = overlap / len(actual)
                mat[i, j] = 2.0 * precision * recall / (precision + recall)
    return labels, mat


def exact_eval(families: list[dict[str, Any]], truth: dict[str, str], selected_ids: list[str]) -> dict[str, Any]:
    by_id = {str(f['family_id']): f for f in families}
    order = list(map(str, selected_ids)) + [str(f['family_id']) for f in families if str(f['family_id']) not in set(selected_ids)]
    ranked = v22.rerank(families, order)
    return v22.evaluate(ranked, truth, len(selected_ids))


def strict_groups(families: list[dict[str, Any]], truth13: dict[str, str], truth14: dict[str, str]) -> dict[str, str]:
    eligible = v22.eligible_from_year_truth({2013: truth13, 2014: truth14})
    hidden: dict[str, str] = {}
    hidden.update(truth13)
    hidden.update(truth14)
    out = {}
    for f in families:
        fid = str(f['family_id'])
        t = v22.family_truth(f, hidden, eligible)
        out[fid] = ('SHOWER/' + str(t['best_label'])) if t['best_label'] is not None else ('NEG/hdbscan/' + fid)
    return out


def build_problem(
    mats: dict[int, np.ndarray],
    literature: dict[int, dict[str, Any]],
    v31_top9: list[str],
    v31_top11: list[str],
    ids: list[str],
    overlap_required: int | None,
    objective: str,
):
    n = len(ids)
    id_index = {fid: i for i, fid in enumerate(ids)}
    off_x9 = 0
    off_x11 = n
    off_y13 = 2 * n
    off_y14 = off_y13 + mats[2013].size
    N = off_y14 + mats[2014].size

    rows: list[dict[int, float]] = []
    lbs: list[float] = []
    ubs: list[float] = []

    def addrow(d: dict[int, float], lb: float = -np.inf, ub: float = np.inf) -> None:
        rows.append(d); lbs.append(lb); ubs.append(ub)

    addrow({off_x9 + j: 1.0 for j in range(n)}, BUDGET[2014], BUDGET[2014])
    addrow({off_x11 + j: 1.0 for j in range(n)}, BUDGET[2013], BUDGET[2013])
    for j in range(n):
        addrow({off_x9 + j: 1.0, off_x11 + j: -1.0}, -np.inf, 0.0)

    for year, off in ((2013, off_y13), (2014, off_y14)):
        mat = mats[year]
        xoff = off_x11 if year == 2013 else off_x9
        for i in range(mat.shape[0]):
            addrow({off + i * n + j: 1.0 for j in range(n)}, -np.inf, 1.0)
        for j in range(n):
            d = {xoff + j: -1.0}
            for i in range(mat.shape[0]):
                d[off + i * n + j] = 1.0
            addrow(d, -np.inf, 0.0)
        macro_needed = float(literature[year]['macro_f1']) * mat.shape[0] + STRICT_EPS
        addrow({off + i*n+j: float(mat[i,j]) for i in range(mat.shape[0]) for j in range(n) if mat[i,j] > 0.0}, macro_needed, np.inf)
        addrow({off + i*n+j: 1.0 for i in range(mat.shape[0]) for j in range(n) if mat[i,j] > RECOVERY}, int(literature[year]['recovered_f1_gt_0_5']), np.inf)

    top9_idx = {id_index[fid] for fid in v31_top9}
    top11_idx = {id_index[fid] for fid in v31_top11}
    overlap_terms = {off_x9+j: 1.0 for j in top9_idx}
    for j in top11_idx:
        overlap_terms[off_x11+j] = overlap_terms.get(off_x11+j, 0.0) + 1.0
    if overlap_required is not None:
        addrow(overlap_terms, float(overlap_required), float(overlap_required))

    rr: list[int] = []; cc: list[int] = []; vv: list[float] = []
    for r, d in enumerate(rows):
        for col, val in d.items():
            rr.append(r); cc.append(col); vv.append(val)
    A = csr_matrix((vv, (rr, cc)), shape=(len(rows), N))
    constraints = LinearConstraint(A, np.asarray(lbs, float), np.asarray(ubs, float))
    bounds = Bounds(np.zeros(N), np.ones(N))
    integrality = np.ones(N, dtype=int)
    c = np.zeros(N, dtype=float)

    if objective == 'maximize_v31_overlap':
        for col, val in overlap_terms.items():
            c[col] = -val
    elif objective == 'maximize_total_assigned_f1':
        for year, off in ((2013, off_y13), (2014, off_y14)):
            mat = mats[year]
            for i in range(mat.shape[0]):
                for j in range(n):
                    c[off + i*n+j] = -float(mat[i,j])
    else:
        raise ValueError(objective)
    meta = {'n': n, 'off_x9': off_x9, 'off_x11': off_x11, 'N': N}
    return c, integrality, bounds, constraints, meta


def solve(c, integrality, bounds, constraints):
    res = milp(c, integrality=integrality, bounds=bounds, constraints=constraints, options={'time_limit': 120.0})
    require(bool(res.success), f'MILP failed: {res.message}')
    require(res.x is not None, 'MILP returned no solution')
    return res


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--hdbscan-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--labelset-result', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=True)

    fp = json.loads((a.hdbscan_root / 'family_memberships.json').read_text())
    require(fp['truth_accessed'] is False, 'HDB membership payload is truth-bearing')
    families = fp['families']; ids = [str(f['family_id']) for f in families]
    require(len(ids) == 229 and len(set(ids)) == 229, 'fixed HDB candidate universe changed')

    parent = json.loads(a.labelset_result.read_text())
    require(parent['verdict'] == 'PASS_V31_HDB_LABELSET_SUBSTITUTION_DIAGNOSTIC', 'authoritative #1053 result mismatch')
    require(parent['candidate_membership_changed'] is False and parent['deployable_rank_selected'] is False, '#1053 role mismatch')
    v31_top11 = list(map(str, parent['annual']['2013']['top_budget_families']))
    v31_top9 = list(map(str, parent['annual']['2014']['top_budget_families']))
    require(v31_top11[:9] == v31_top9, 'v31 annual prefixes are not one common order')
    require(len(v31_top11) == 11 and len(v31_top9) == 9, 'v31 HDB budgets changed')

    truths = {y: json.loads((a.truth_root / f'truth_hdbscan_{y}.json').read_text()) for y in YEARS}
    mats = {}; labels = {}
    for y in YEARS:
        labels[y], mats[y] = annual_matrix(families, truths[y])
    literature = {y: parent['annual'][str(y)]['literature'] for y in YEARS}

    c1, integ1, bounds1, cons1, meta1 = build_problem(mats, literature, v31_top9, v31_top11, ids, None, 'maximize_v31_overlap')
    r1 = solve(c1, integ1, bounds1, cons1)
    max_overlap = int(round(-float(r1.fun)))
    require(0 <= max_overlap <= 20, 'invalid overlap objective')

    c2, integ2, bounds2, cons2, meta2 = build_problem(mats, literature, v31_top9, v31_top11, ids, max_overlap, 'maximize_total_assigned_f1')
    r2 = solve(c2, integ2, bounds2, cons2)
    x9 = r2.x[meta2['off_x9']:meta2['off_x9']+meta2['n']]
    x11 = r2.x[meta2['off_x11']:meta2['off_x11']+meta2['n']]
    sel9_set = {ids[j] for j in np.where(x9 > 0.5)[0].tolist()}
    sel11_set = {ids[j] for j in np.where(x11 > 0.5)[0].tolist()}
    require(len(sel9_set) == 9 and len(sel11_set) == 11 and sel9_set.issubset(sel11_set), 'nested solution invalid')

    # Stable common order for exact evaluator: selected top 9 in original v31 order when possible,
    # then new top-9 families by family id; selected 10-11 similarly. Set membership, not within-prefix order,
    # determines the unchanged Hungarian evaluator result because all 229 families are annual-active.
    base_rank = {fid: i for i, fid in enumerate(v31_top11)}
    def stable_key(fid: str): return (base_rank.get(fid, 10**9), fid)
    sel9 = sorted(sel9_set, key=stable_key)
    extra = sorted(sel11_set - sel9_set, key=stable_key)
    sel11 = sel9 + extra

    exact2014 = exact_eval(families, truths[2014], sel9)
    exact2013 = exact_eval(families, truths[2013], sel11)
    pass2014 = bool(exact2014['macro_f1'] > float(literature[2014]['macro_f1']) and exact2014['recovered_f1_gt_0_5'] >= int(literature[2014]['recovered_f1_gt_0_5']))
    pass2013 = bool(exact2013['macro_f1'] > float(literature[2013]['macro_f1']) and exact2013['recovered_f1_gt_0_5'] >= int(literature[2013]['recovered_f1_gt_0_5']))
    require(pass2013 and pass2014, 'MILP-feasible nested set does not pass unchanged evaluator')

    groups = strict_groups(families, truths[2013], truths[2014])
    in9 = sorted(sel9_set - set(v31_top9)); out9 = sorted(set(v31_top9) - sel9_set)
    in11 = sorted(sel11_set - set(v31_top11)); out11 = sorted(set(v31_top11) - sel11_set)
    incoming_unique = sorted(set(in11) | set(in9))
    result = {
        'verdict': 'PASS_V31_HDB_JOINT_NESTED_BUDGET_ORACLE_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_TRUTH_AWARE_ORACLE_DIAGNOSTIC_FORMALIZING_ALREADY_OBSERVED_EXPLORATORY_RESULT',
        'independent_confirmation': False,
        'candidate_universe_size': len(ids),
        'budgets': {'2013': 11, '2014': 9},
        'joint_nested_can_clear_both_hdb_pair_gates': True,
        'maximum_v31_prefix_overlap_sum': max_overlap,
        'v31_prefix_overlap': {'top9': len(sel9_set & set(v31_top9)), 'top11': len(sel11_set & set(v31_top11))},
        'replacement_counts': {'top9': len(in9), 'top11': len(in11), 'distinct_incoming_families': len(incoming_unique), 'distinct_incoming_strict_groups': len({groups[f] for f in incoming_unique})},
        '2014_top9': {'selected_families': sel9, 'incoming_families': in9, 'outgoing_families': out9, 'incoming_groups': [groups[f] for f in in9], 'outgoing_groups': [groups[f] for f in out9], 'candidate': exact2014, 'literature': literature[2014], 'pair_gate_pass': pass2014},
        '2013_top11': {'selected_families': sel11, 'incoming_families': in11, 'outgoing_families': out11, 'incoming_groups': [groups[f] for f in in11], 'outgoing_groups': [groups[f] for f in out11], 'candidate': exact2013, 'literature': literature[2013], 'pair_gate_pass': pass2013},
        'oracle_identities_promotable': False,
        'deployable_rank_selected': False,
        'successor_selected': False,
        'feature_search': False,
        'model_search': False,
        'rank_search': False,
        'threshold_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (a.output / 'V31_HDB_JOINT_NESTED_BUDGET_ORACLE_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path

MODULE = Path('/tmp/orbittrace_final_matched_evaluator_v1.py')


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load():
    spec = importlib.util.spec_from_file_location('final_eval_v1', MODULE)
    require(spec is not None and spec.loader is not None, 'cannot load evaluator')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def family(fid: str, *ids: str) -> dict:
    return {'family_id': fid, 'event_ids': list(ids)}


def base_payload(year: int, comp: str) -> dict:
    # A and B are both exactly 4-row showers; x1/x2 are sporadic.
    truth = {
        'a1':'A','a2':'A','a3':'A','a4':'A',
        'b1':'B','b2':'B','b3':'B','b4':'B',
        'x1':'SPORADIC','x2':'SPORADIC',
    }
    return {
        'year': year,
        'comparator_id': comp,
        'row_ids': sorted(truth),
        'row_truth': truth,
        'candidate_order': ['C_A','C_A_DUP','C_B'],
        'candidate_families': [
            family('C_A','a1','a2','a3','a4'),
            family('C_A_DUP','a1','a2','a3','a4'),
            family('C_B','b1','b2','b3','b4'),
        ],
        'comparator_families': [
            family('K_A','a1','a2','a3','a4'),
            family('K_B','b1','b2','b3','b4'),
        ],
    }


def test_budget_and_one_to_one(ev) -> None:
    r = ev.evaluate_pair(base_payload(2013, 'TEST'))
    # Comparator budget=2, so C_B is excluded even though it is a perfect third family.
    require(r['candidate_budget']['comparator_budget'] == 2, 'budget !=2')
    require(r['candidate_budget']['candidate_used'] == 2, 'candidate did not obey budget')
    require(abs(r['candidate_summary']['macro_f1'] - 0.5) < 1e-15, 'candidate shotgun budget not penalized')
    require(abs(r['comparator_summary']['macro_f1'] - 1.0) < 1e-15, 'comparator perfect score changed')
    require(r['candidate_summary']['recovered_f1_gt_0_5'] == 1, 'duplicate A counted as second recovery')
    assigned = {x['label']: x['candidate']['family_id'] for x in r['per_shower']}
    require(assigned['A'] == 'C_A', 'rank tie-break did not choose earlier candidate')
    require(assigned['B'] is None, 'excluded C_B leaked through budget')


def perfect_sparse_payload(year: int, comp: str) -> dict:
    p = base_payload(year, comp)
    p['candidate_order'] = ['C_A','C_B']
    p['candidate_families'] = [
        family('C_A','a1','a2','a3','a4'),
        family('C_B','b1','b2','b3','b4'),
    ]
    # Two comparator families exist (budget parity) but contain only sporadic rows.
    p['comparator_families'] = [family('K_X1','x1'), family('K_X2','x2')]
    return p


def test_sparse_bootstrap(ev) -> None:
    r13 = ev.evaluate_pair(perfect_sparse_payload(2013, 'TEST_SPARSE'))
    r14 = ev.evaluate_pair(perfect_sparse_payload(2014, 'TEST_SPARSE'))
    require(r13['point_comparison']['sparse_pass'] is True, 'synthetic sparse point pass failed')
    require(r13['point_comparison']['broad_pass'] is False, 'one-stratum fixture incorrectly broad-passed')
    b = ev.bootstrap_two_year([r13, r14], 'TEST_SPARSE')
    require(abs(b['sparse_4_9_advantage_lower_95'] - 1.0) < 1e-15, 'sparse bootstrap 4-9 lower bound changed')
    require(abs(b['sparse_4_24_advantage_lower_95'] - 1.0) < 1e-15, 'sparse bootstrap 4-24 lower bound changed')
    require(b['sparse_uncertainty_pass'] is True, 'synthetic sparse uncertainty did not pass')


def test_truth_floor(ev) -> None:
    p = base_payload(2013, 'TEST_FLOOR')
    p['row_truth']['c1'] = 'C'
    p['row_truth']['c2'] = 'C'
    p['row_truth']['c3'] = 'C'
    p['row_ids'] += ['c1','c2','c3']
    r = ev.evaluate_pair(p)
    require(r['truth_evaluation']['eligible_shower_count'] == 2, '1-3-row shower entered evaluation')


def main() -> int:
    ev = load()
    test_budget_and_one_to_one(ev)
    test_sparse_bootstrap(ev)
    test_truth_floor(ev)
    print('PASS_FINAL_MATCHED_EVALUATOR_V1_SYNTHETIC_SELF_TEST')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

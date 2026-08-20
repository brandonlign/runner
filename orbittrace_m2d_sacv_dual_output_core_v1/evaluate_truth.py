from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

import orbittrace_m2d_sacv_fallback_recurrence_v1.evaluate_truth as ev

SACV_V1_PRETRUTH_SHA256 = '77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'
SACV_V1_ROLE = 'TARGET_EXCLUDED_SACV_MEMBERSHIPS_FROZEN_BEFORE_SHOWER_TRUTH'
DUAL_ROLE = 'TARGET_EXCLUDED_SACV_PRIMARY_PLUS_NESTED_RECURRENT_CORE_FROZEN_BEFORE_SHOWER_TRUTH'
DUAL_SCHEMA = 'ORBITTRACE_M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_RESULT'


def req(x: bool, msg: str) -> None:
    if not x:
        raise RuntimeError(msg)


def by_key(payload: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(s['denominator']), int(s['bucket'])): s for s in payload['subsets']}


def primary_gates(ps: dict[str, Any], comp: str) -> dict[str, bool]:
    return {
        'paired_count_at_least_20': ps['count'] >= 20,
        'nonempty_fraction_at_least_075': ps['nonempty_fraction'] >= 0.75,
        'mean_extraction_precision_at_least_080': ps['extraction_mean_precision'] >= 0.80,
        'mean_extraction_precision_strictly_higher_than_parent': ps['extraction_mean_precision'] > ps['parent_mean_precision'],
        'mean_extraction_f1_retains_at_least_075_parent': ps['extraction_mean_f1'] >= 0.75 * ps['parent_mean_f1'],
        'nonempty_precision_nonregression_fraction_at_least_050': ps['nonempty_precision_nonregression_fraction'] >= 0.50,
        'at_least_one_parent_recovered_assignment_strictly_refined': ps['strict_refined_assignment_count'] >= 1,
        'precision_exact_frozen_sacv_v1': abs(ps['extraction_mean_precision'] - ev.SACV_V1_BASE[comp]['precision']) <= 1e-15,
        'f1_exact_frozen_sacv_v1': abs(ps['extraction_mean_f1'] - ev.SACV_V1_BASE[comp]['f1']) <= 1e-15,
    }


def core_gates(ps: dict[str, Any]) -> dict[str, bool]:
    # Here paired_summary's parent fields are the immutable SACV-v1 primary
    # metrics for exactly those same-parent assignments that possess a core.
    return {
        'nonempty_fraction_at_least_075': ps['nonempty_fraction'] >= 0.75,
        'mean_core_precision_at_least_080': ps['extraction_mean_precision'] >= 0.80,
        'mean_core_precision_strictly_higher_than_primary': ps['extraction_mean_precision'] > ps['parent_mean_precision'],
        'mean_core_f1_retains_at_least_075_primary': ps['extraction_mean_f1'] >= 0.75 * ps['parent_mean_f1'],
        'nonempty_precision_nonregression_fraction_at_least_050': ps['nonempty_precision_nonregression_fraction'] >= 0.50,
        'at_least_one_primary_assignment_strictly_refined': ps['strict_refined_assignment_count'] >= 1,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for n in ('fair-pretruth', 'sacv-pretruth', 'sacv-v1-pretruth', 'internal-prelabel', 'quality-source', 'support-source-parts', 'candidate-payload', 'baseline-payload', 'scorer-parts', 'v8-result-json', 'output'):
        ap.add_argument('--' + n, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(ev.sha(a.fair_pretruth) == ev.FAIR_SHA, 'fair changed')
    req(ev.sha(a.internal_prelabel) == ev.INTERNAL_SHA, 'internal changed')
    req(ev.sha(a.quality_source) == ev.QUALITY_SHA and ev.sha(a.v8_result_json) == ev.V8_SHA, 'runtime changed')
    req(ev.sha(a.sacv_v1_pretruth) == SACV_V1_PRETRUTH_SHA256, 'SACV v1 oracle changed')

    fair = json.loads(a.fair_pretruth.read_text())
    dual = json.loads(a.sacv_pretruth.read_text())
    oracle = json.loads(a.sacv_v1_pretruth.read_text())
    req(dual['scientific_role'] == DUAL_ROLE, 'wrong dual-output role')
    req(dual['fair_pretruth_sha256'] == ev.FAIR_SHA, 'dual parent changed')
    req(dual['sacv_v1_pretruth_sha256'] == SACV_V1_PRETRUTH_SHA256, 'dual oracle identity changed')
    req(dual['primary_output_exact_sacv_v1'] is True and dual['nested_core_changes_primary_matching'] is False, 'dual role contamination')
    req(dual['shower_truth_used'] is False and dual['target_information_access'] is False and dual['target_region_events_accessed'] is False and dual['post_result_parameter_search'] is False, 'dual firewall')
    req(oracle['scientific_role'] == SACV_V1_ROLE and oracle['fair_pretruth_sha256'] == ev.FAIR_SHA, 'oracle role/parent')

    fs, xs, os = by_key(fair), by_key(dual), by_key(oracle)
    expected = {(d, b) for d in ev.DENOMS for b in ev.BUCKETS}
    req(set(fs) == set(xs) == set(os) == expected, 'panel mismatch')

    primary_id_equal = 0
    nested_core_occurrences = 0
    for key in fs:
        pp = list(fs[key]['successor_candidates'])
        xx = list(xs[key]['extractions'])
        oo = list(os[key]['extractions'])
        req(len(pp) == len(xx) == len(oo), 'candidate count changed')
        for pos, (p, x, o) in enumerate(zip(pp, xx, oo), 1):
            req(int(p['internal_mass_rank']) == int(x['rank']) == int(o['rank']) == pos, f'rank mismatch {key}/{pos}')
            req(str(p['family_id']) == str(x['family_id']) == str(o['family_id']), f'identity {key}/{pos}')
            req(str(p['family_hash']) == str(x['family_hash']) == str(o['family_hash']), f'hash identity {key}/{pos}')
            parent_ids = set(map(str, p['event_ids']))
            primary_ids = list(map(str, x['output_ids']))
            oracle_ids = list(map(str, o['output_ids']))
            req(primary_ids == oracle_ids, f'PRIMARY_ID_ORACLE_MISMATCH {key}/{pos}')
            req(bool(x['refined']) == bool(o['refined']), f'PRIMARY_REFINED_ORACLE_MISMATCH {key}/{pos}')
            req(set(primary_ids).issubset(parent_ids), f'primary escaped {key}/{pos}')
            core_ids = list(map(str, x['recurrent_core_ids']))
            req(set(core_ids).issubset(parent_ids), f'core escaped {key}/{pos}')
            if core_ids:
                nested_core_occurrences += 1
                req(primary_ids == sorted(parent_ids), f'core outside exact SACV parent fallback {key}/{pos}')
                req(x['route'] == 'sacv_v1_parent_with_recurrent_core', f'core route {key}/{pos}')
                req(x['original_sacv_validated'] is False, f'core on validated SACV {key}/{pos}')
            primary_id_equal += 1
    req(primary_id_equal == 328 == int(dual['summary']['primary_oracle_exact_id_equal_occurrences']), 'primary equality total')
    req(nested_core_occurrences == int(dual['summary']['nested_core_occurrences']), 'core count summary mismatch')

    # Hidden shower truth begins only here, after all primary/core memberships and
    # exact primary-to-oracle equality have been verified and frozen.
    q = ev.load(a.quality_source, 'sacv_dual_truth_q')
    q.v1.mult.YEARS = ev.YEARS
    q.v1.mult.MONTH_KEYS = ev.MONTH_KEYS
    q.v1.mult.TOP_K = 100
    rt = q.v1.mult.load_frozen_runtime()
    support = rt.load_support_module(a.support_source_parts)
    support.YEARS = ev.YEARS
    support.MONTH_KEYS = ev.MONTH_KEYS
    support.CORPUS = 'orbittrace-m2d-sacv-dual-output-core-v1-gmn-truth'
    support.RANKING_VARIANTS = ('persistence',)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == ev.BLIND, 'blind changed')
    setattr(a, 'fixed4_baseline_json', a.v8_result_json)
    _c, base, _s = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(ev.YEARS) and [x['key'] for x in sources] == list(ev.MONTH_KEYS), 'source set changed')

    comparisons: list[dict[str, Any]] = []
    primary_paired = {c: [] for c in ('sugar2017', 'hdbscan2025')}
    core_paired = {c: [] for c in ('sugar2017', 'hdbscan2025')}

    for d in ev.DENOMS:
        for b in ev.BUCKETS:
            fsub, xsub = fs[(d, b)], xs[(d, b)]
            parents = list(fsub['successor_candidates'])
            primary_outs = [{'family_id': x['family_id'], 'event_ids': x['output_ids']} for x in xsub['extractions']]
            core_outs = [{'family_id': x['family_id'], 'event_ids': x['recurrent_core_ids']} for x in xsub['extractions']]
            for y in ev.YEARS:
                key = f'd{d}_b{b}_y{y}'
                annual = set(map(str, fsub['annual_event_ids'][str(y)]))
                panel = fair['panels'][key]
                for comp in ('sugar2017', 'hdbscan2025'):
                    k = len(panel[comp]['clusters'])
                    pm = ev.matrices(parents[:k], hidden, annual)
                    xm = ev.matrices(primary_outs[:k], hidden, annual)
                    cm = ev.matrices(core_outs[:k], hidden, annual)
                    req(pm['labels'] == xm['labels'] == cm['labels'], 'truth labels')
                    pa = ev.assigned(pm)
                    xa = ev.assigned(xm)
                    local_primary = []
                    local_core = []
                    for i, label in enumerate(pm['labels']):
                        j = int(pa['candidate_by_label'][i])
                        if j < 0 or float(pa['assigned_f1'][i]) <= 0.5:
                            continue
                        pN = int(pm['nmem'][j])
                        xN = int(xm['nmem'][j])
                        prow = {
                            'denominator': d, 'bucket': b, 'year': y, 'label': label,
                            'candidate_index': j, 'candidate_rank': j + 1,
                            'parent_member_count': pN, 'extraction_member_count': xN,
                            'parent_precision': float(pm['p'][i, j]), 'parent_recall': float(pm['r'][i, j]), 'parent_f1': float(pm['f'][i, j]),
                            'extraction_precision': float(xm['p'][i, j]), 'extraction_recall': float(xm['r'][i, j]), 'extraction_f1': float(xm['f'][i, j]),
                            'strict_refined': xN < pN,
                        }
                        local_primary.append(prow)
                        primary_paired[comp].append(prow)

                        cN = int(cm['nmem'][j])
                        if cN > 0:
                            crow = {
                                'denominator': d, 'bucket': b, 'year': y, 'label': label,
                                'candidate_index': j, 'candidate_rank': j + 1,
                                'parent_member_count': xN, 'extraction_member_count': cN,
                                # paired_summary interprets these as reference vs extraction;
                                # reference here is exact SACV-v1 primary, not M2D parent.
                                'parent_precision': float(xm['p'][i, j]), 'parent_recall': float(xm['r'][i, j]), 'parent_f1': float(xm['f'][i, j]),
                                'extraction_precision': float(cm['p'][i, j]), 'extraction_recall': float(cm['r'][i, j]), 'extraction_f1': float(cm['f'][i, j]),
                                'strict_refined': cN < xN,
                            }
                            local_core.append(crow)
                            core_paired[comp].append(crow)
                    comparisons.append({
                        'denominator': d, 'bucket': b, 'year': y, 'comparator': comp, 'capacity_k': k,
                        'parent': ev.pack(pa), 'rematched_primary_diagnostic': ev.pack(xa),
                        'paired_parent_recovered_primary': local_primary,
                        'paired_parent_recovered_nested_core': local_core,
                    })

    primary_all_gates: dict[str, bool] = {}
    aggregates: dict[str, Any] = {}
    eligible_comparators: list[str] = []
    failed_eligible_core_routes: list[str] = []
    for comp in ('sugar2017', 'hdbscan2025'):
        cr = [r for r in comparisons if r['comparator'] == comp]
        pa = ev.aggregate(cr, 'parent')
        req(ev.exact_parent(comp, pa), f'parent reproduction {comp}: {pa}')
        pps = ev.paired_summary(primary_paired[comp])
        pg = primary_gates(pps, comp)
        for k, v in pg.items():
            primary_all_gates[f'{comp}_{k}'] = bool(v)

        cps = ev.paired_summary(core_paired[comp])
        power_eligible = cps['count'] >= 20
        cg = core_gates(cps) if power_eligible else {}
        if power_eligible:
            eligible_comparators.append(comp)
            if not all(cg.values()):
                failed_eligible_core_routes.append(comp)
        aggregates[comp] = {
            'parent': pa,
            'primary_same_discovery': pps,
            'primary_gates': pg,
            'nested_core': {
                'paired_same_discovery': cps,
                'power_eligible_n_ge_20': power_eligible,
                'gates': cg,
                'status': ('PASS' if power_eligible and all(cg.values()) else 'FAIL' if power_eligible else 'POWER_INCONCLUSIVE'),
            },
        }

    primary_exact = all(primary_all_gates.values())
    if not primary_exact:
        verdict = 'FAIL_M2D_SACV_DUAL_OUTPUT_CORE_V1_PRIMARY_INTEGRITY'
    elif not eligible_comparators:
        verdict = 'POWER_INCONCLUSIVE_M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_DEVELOPMENT'
    elif failed_eligible_core_routes:
        verdict = 'FAIL_M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_DEVELOPMENT'
    else:
        verdict = 'PASS_M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_DEVELOPMENT'

    out = {
        'schema': DUAL_SCHEMA,
        'verdict': verdict,
        'fair_pretruth_sha256': ev.FAIR_SHA,
        'dual_pretruth_sha256': ev.sha(a.sacv_pretruth),
        'sacv_v1_pretruth_sha256': SACV_V1_PRETRUTH_SHA256,
        'primary_oracle_exact_id_equal_occurrences': primary_id_equal,
        'nested_core_occurrences': nested_core_occurrences,
        'eligible_core_comparators': eligible_comparators,
        'failed_eligible_core_routes': failed_eligible_core_routes,
        'aggregates': aggregates,
        'primary_gates': primary_all_gates,
        'primary_discovery_membership_changed': False,
        'primary_discovery_rank_changed': False,
        'nested_core_changes_primary_matching': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'sonotaco_scientific_access': False,
        'post_result_parameter_search': False,
        'post_target_reveal_development': True,
        'frozen_sacv_v1_baseline': ev.SACV_V1_BASE,
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': verdict, 'eligible_core_comparators': eligible_comparators, 'failed_eligible_core_routes': failed_eligible_core_routes, 'aggregates': aggregates, 'result_sha256': ev.sha(a.output)}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V8_RESULT_SHA256 = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
FAIR_SHA = '8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
SACV_V1_PRETRUTH_SHA = '77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'
BUCKETS = (0, 1, 2, 3)


def req(x: bool, msg: str) -> None:
    if not x:
        raise RuntimeError(msg)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f'cannot import {path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compact(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != 'first_rank_by_label'}


def zero_filled_mrr(m: dict[str, Any]) -> float:
    eligible = int(m['eligible_labels'])
    qualified = int(m['qualified_matches'])
    conditional = float(m['mrr'])
    req(eligible >= qualified >= 0, 'invalid eligible/qualified counts')
    if eligible == 0:
        return 0.0
    if qualified == 0:
        req(conditional == 0.0, 'nonzero conditional MRR with zero qualified matches')
        return 0.0
    return conditional * qualified / eligible


def aggregate(panels: list[dict[str, Any]], key: str) -> dict[str, Any]:
    vals = [p[key] for p in panels]
    eligible = sum(int(x['eligible_labels']) for x in vals)
    mass = sum(float(x['mrr']) * int(x['qualified_matches']) for x in vals)
    return {
        'qualified_total': sum(int(x['qualified_matches']) for x in vals),
        'conditional_mrr_mean': float(np.mean([float(x['mrr']) for x in vals])),
        'zero_filled_mrr_mean': float(np.mean([zero_filled_mrr(x) for x in vals])),
        'zero_filled_mrr_pooled': mass / eligible if eligible else 0.0,
        'eligible_total': eligible,
        'reciprocal_mass': mass,
        'precision_mean': float(np.mean([float(x['top100_dominant_precision']) for x in vals])),
        'fragmentation_mean': float(np.mean([float(x['fragmentation_median_top500']) for x in vals])),
        'recovered_at_25_total': sum(int(x['recovered_at_25']) for x in vals),
        'recovered_at_50_total': sum(int(x['recovered_at_50']) for x in vals),
        'recovered_at_100_total': sum(int(x['recovered_at_100']) for x in vals),
        'recovered_at_500_total': sum(int(x['recovered_at_500']) for x in vals),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ('prelabel', 'pretruth', 'parent-runner', 'quality-source', 'support-source-parts', 'candidate-payload', 'baseline-payload', 'scorer-parts', 'v8-result-json', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, 'quality source changed')
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, 'v8 result changed')
    pre_sha = sha256(a.prelabel)
    audit_sha = sha256(a.pretruth)
    pre = json.loads(a.prelabel.read_text())
    audit = json.loads(a.pretruth.read_text())

    req(pre['schema'] == 'ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRELABEL', 'wrong prelabel schema')
    req(pre['scientific_role'] == 'TARGET_EXCLUDED_COMPLETE_SACV_VALIDATED_PAIR_CATALOGUE_FROZEN_BEFORE_SHOWER_TRUTH', 'wrong prelabel role')
    req(pre['fair_pretruth_sha256'] == FAIR_SHA and pre['sacv_v1_pretruth_sha256'] == SACV_V1_PRETRUTH_SHA, 'frozen source mismatch')
    req(pre['configuration'] == {
        'annual_hypothesis_order': 'excess_desc_parent_support_desc_contamination_asc_radius_asc_center_id_asc',
        'pair_validation': 'exact_sacv_v1_reciprocal_crossyear_validation',
        'pair_membership': 'exact_union_of_endpoint_sacv_balls_within_immutable_parent',
        'pareto_objectives_minimized': ['immutable_m2d_parent_rank', 'sacv_2022_hypothesis_rank', 'sacv_2023_hypothesis_rank'],
        'pareto': 'ordinary_nondominated_layers',
        'final_order': 'pareto_layer_asc_pair_hash_asc',
        'pair_hash': 'sha256(parent_family_hash|center_2022_id|center_2023_id)',
        'duplicate_membership_policy': 'retain_distinct_pair_identities_and_consume_budget',
        'equal_budget': 'exact_sacv_v1_parent_candidate_count_per_panel',
        'fallback_fill': 'forbidden',
    }, 'configuration changed')
    for flag in ('shower_truth_used', 'target_information_access', 'target_region_events_accessed', 'sonotaco_scientific_access'):
        req(pre.get(flag) is False, f'prelabel firewall {flag}')

    req(audit['schema'] == 'ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH', 'wrong pretruth schema')
    req(audit['scientific_role'] == 'ZERO_LABEL_PRETRUTH_AUTHORIZATION', 'wrong pretruth role')
    req(audit['verdict'] == 'PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH', 'pretruth not authorized')
    req(audit['prelabel_sha256'] == pre_sha, 'pretruth/prelabel mismatch')
    req(len(audit['gates']) == 10 and all(bool(v) for v in audit['gates'].values()), 'pretruth gates')

    subset = {(int(r['denominator']), int(r['bucket'])): r for r in pre['panels']}
    req(set(subset) == {(d, b) for d in (128, 1024) for b in BUCKETS}, 'panel set')
    for row in pre['panels']:
        succ = list(row['successor_candidates'])
        base = list(row['sacv_v1_candidates'])
        K = int(row['equal_budget_k'])
        req(len(base) == K and len(succ) >= K and row['capacity_ok'] is True, 'capacity changed')
        req([int(x['rank']) for x in base] == list(range(1, K + 1)), 'SACV rank drift')
        req([int(x['rank']) for x in succ] == list(range(1, len(succ) + 1)), 'successor rank drift')
        req(all(x['catalogue_source'] == 'm2d_sacv_validated_pair' for x in succ), 'wrong successor source')
        req(all(x['catalogue_source'] == 'exact_sacv_v1' for x in base), 'wrong baseline source')
        annual = set(row['annual_event_ids']['2022']) | set(row['annual_event_ids']['2023'])
        req(len(annual) == int(row['event_count']), 'panel event count')
        req(all(set(x['event_ids']).issubset(annual) for x in succ[:K] + base), 'candidate outside panel')

    parent = load_module(a.parent_runner, 'sacv_pareto_pair_truth_parent')
    q = load_module(a.quality_source, 'sacv_pareto_pair_truth_gmn')
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = 'orbittrace-m2d-sacv-pareto-pair-catalogue-v1'
    support.RANKING_VARIANTS = ('persistence',)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, 'firewall changed')
    setattr(a, 'fixed4_baseline_json', a.v8_result_json)
    _candidate, baseline_payload, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(baseline_payload)
    req(isinstance(hidden, dict), 'hidden truth unavailable')
    req(sorted(scan) == list(YEARS) and [x['key'] for x in sources] == list(MONTH_KEYS), 'truth/source set changed')

    events = []
    for year in YEARS:
        events.extend(parent.normalize_event(r, year) for r in list(scan[year]))
    req(len(events) == 738682, 'target-excluded event universe changed')
    req(all(not (BLIND[0] <= float(e['sol']) <= BLIND[1]) for e in events), 'protected region entered truth runtime')
    ids = {str(e['id']) for e in events}
    req(len(ids) == len(events), 'event ids nonunique')
    for row in pre['panels']:
        for year in YEARS:
            req(set(row['annual_event_ids'][str(year)]).issubset(ids), 'panel ids absent from runtime')

    panels = []
    for d in (128, 1024):
        for b in BUCKETS:
            frozen = subset[(d, b)]
            K = int(frozen['equal_budget_k'])
            succ = list(frozen['successor_candidates'])[:K]
            base = list(frozen['sacv_v1_candidates'])
            req(len(succ) == len(base) == K, 'equal budget drift')
            for year in YEARS:
                annual = set(frozen['annual_event_ids'][str(year)])
                bm = compact(parent.metrics(base, hidden, annual))
                sm = compact(parent.metrics(succ, hidden, annual))
                req(int(bm['eligible_labels']) == int(sm['eligible_labels']), 'eligibility changed')
                panels.append({
                    'denominator': d,
                    'bucket': b,
                    'year': year,
                    'equal_budget_k': K,
                    'sacv_v1_equal_budget': bm,
                    'successor_equal_budget': sm,
                    'sacv_v1_zero_filled_mrr': zero_filled_mrr(bm),
                    'successor_zero_filled_mrr': zero_filled_mrr(sm),
                    'qualified_nonlower': int(sm['qualified_matches']) >= int(bm['qualified_matches']),
                    'qualified_strict_win': int(sm['qualified_matches']) > int(bm['qualified_matches']),
                })

    scales: dict[str, Any] = {}
    for d in (128, 1024):
        ps = [p for p in panels if p['denominator'] == d]
        req(len(ps) == 8, 'missing annual panels')
        ba = aggregate(ps, 'sacv_v1_equal_budget')
        sa = aggregate(ps, 'successor_equal_budget')
        non = sum(bool(p['qualified_nonlower']) for p in ps)
        strict = sum(bool(p['qualified_strict_win']) for p in ps)
        scales[str(d)] = {
            'panel_count': 8,
            'sacv_v1_equal_budget': ba,
            'successor_equal_budget': sa,
            'qualified_nonlower_panels': non,
            'qualified_strict_win_panels': strict,
            'qualified_loss_panels': 8 - non,
        }

    gates: dict[str, bool] = {}
    for name, d in (('fine', '1024'), ('coarse', '128')):
        ba = scales[d]['sacv_v1_equal_budget']
        sa = scales[d]['successor_equal_budget']
        gates[f'{name}_qualified_total_not_lower'] = sa['qualified_total'] >= ba['qualified_total']
        gates[f'{name}_qualified_nonlower_at_least_6_of_8'] = scales[d]['qualified_nonlower_panels'] >= 6
        gates[f'{name}_zero_filled_mrr_mean_not_lower'] = sa['zero_filled_mrr_mean'] >= ba['zero_filled_mrr_mean']
        gates[f'{name}_precision_mean_not_lower'] = sa['precision_mean'] >= ba['precision_mean']
        gates[f'{name}_fragmentation_mean_not_higher'] = sa['fragmentation_mean'] <= ba['fragmentation_mean']

    strict_improvement = False
    for d in ('128', '1024'):
        ba = scales[d]['sacv_v1_equal_budget']
        sa = scales[d]['successor_equal_budget']
        strict_improvement = strict_improvement or sa['qualified_total'] > ba['qualified_total'] or sa['zero_filled_mrr_mean'] > ba['zero_filled_mrr_mean'] or sa['precision_mean'] > ba['precision_mean']
    gates['at_least_one_strict_catalogue_gain'] = strict_improvement

    verdict = 'PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_DEVELOPMENT' if all(gates.values()) else 'FAIL_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_DEVELOPMENT'
    out = {
        'schema': 'ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_TRUTH',
        'scientific_role': 'TARGET_EXCLUDED_GMN_2022_2023_SPARSE_CATALOGUE_DEVELOPMENT',
        'verdict': verdict,
        'prelabel_sha256': pre_sha,
        'pretruth_sha256': audit_sha,
        'ranking_metric_gate': 'zero_filled_eligible_query_mrr_panel_mean',
        'historical_conditional_mrr_role': 'diagnostic_only',
        'panels': panels,
        'scale_aggregates': scales,
        'gates': gates,
        'blind_exclusion': list(BLIND),
        'target_information_access': False,
        'target_region_events_accessed': False,
        'sonotaco_scientific_access': False,
        'asfn_event_level_access': False,
        'efn_event_level_access': False,
        'amos_scientific_access': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'method_parameter_selection_from_result': False,
        'post_target_reveal_development': True,
    }
    p = a.output / 'M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_RESULT.json'
    p.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': verdict, 'scales': scales, 'gates': gates, 'result_sha256': sha256(p)}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

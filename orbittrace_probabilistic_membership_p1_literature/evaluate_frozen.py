#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import pickle
from pathlib import Path
from typing import Any

YEARS = (2023, 2025)
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
BINS = ('4-9', '10-24', '25-49', '50-99', '100+')
ELIGIBLE_CLASS = 'P1 matched-literature pretruth panel checkpoint'
INELIGIBLE_CLASS = 'P1_MATCHED_INPUT_INELIGIBLE_EXACT_V8_SUPPORT'
P1_SOURCE_SHA256 = 'e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508'


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f'cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_checkpoint(path: Path, expected_panel: str) -> dict[str, Any]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(path.suffix + '.sha256')
    require(sidecar.exists() and sidecar.read_text().strip() == hashlib.sha256(raw).hexdigest(), f'checkpoint SHA mismatch {expected_panel}')
    obj = pickle.loads(raw)
    require(obj['classification'] in {ELIGIBLE_CLASS, INELIGIBLE_CLASS}, f'wrong checkpoint classification {expected_panel}')
    require(obj['panel'] == expected_panel, f'checkpoint panel mismatch {expected_panel}')
    require(obj['years'] == list(YEARS), f'checkpoint years changed {expected_panel}')
    require(obj['blind_exclusion'] == [BLIND_LOW, BLIND_HIGH], f'checkpoint blind interval changed {expected_panel}')
    require(obj['competitor_cluster_values_accessed'] is False, f'competitor labels entered pretruth {expected_panel}')
    require(obj['known_shower_truth_accessed'] is False, f'truth entered pretruth {expected_panel}')
    if obj['classification'] == ELIGIBLE_CLASS:
        require(obj['p1_source_sha256'] == P1_SOURCE_SHA256, f'P1 source changed {expected_panel}')
        require(obj['membership_and_rank_frozen_before_truth'] is True, f'pretruth freeze missing {expected_panel}')
        require(len(obj['p1_membership_pretruth_sha256']) == 64, f'membership hash missing {expected_panel}')
        require(len(obj['v8_order_pretruth_sha256']) == 64, f'order hash missing {expected_panel}')
        actual_membership_sha = hashlib.sha256(json.dumps(obj['p1_expanded_families'], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        actual_order_sha = hashlib.sha256(json.dumps(obj['v8_multiplicity_order'], separators=(',', ':')).encode()).hexdigest()
        require(actual_membership_sha == obj['p1_membership_pretruth_sha256'], f'membership hash changed {expected_panel}')
        require(actual_order_sha == obj['v8_order_pretruth_sha256'], f'order hash changed {expected_panel}')
    else:
        require(obj['p1_membership_executed'] is False, f'ineligible panel ran P1 {expected_panel}')
        require(obj['no_support_relaxation'] is True, f'ineligible panel relaxed support {expected_panel}')
        require(int(obj['support_failure']['required_episode_events']) == 128, f'ineligible support rule changed {expected_panel}')
    return obj


def subset_mean(rows: list[dict[str, Any]], bins: set[str]) -> float | None:
    vals = [float(r['f1']) for r in rows if str(r['size_bin']) in bins]
    return float(sum(vals) / len(vals)) if vals else None


def annual_pairwise_gates(
    p1_rows: list[dict[str, Any]], p1_summary: dict[str, Any],
    comp_rows: list[dict[str, Any]], comp_summary: dict[str, Any],
) -> dict[str, Any]:
    require({r['label'] for r in p1_rows} == {r['label'] for r in comp_rows}, 'annual truth label sets differ')
    require(len(p1_rows) == len(comp_rows), 'annual evaluation denominator differs')
    for bin_name in BINS:
        require(p1_summary[bin_name]['showers'] == comp_summary[bin_name]['showers'], f'size-bin denominator differs {bin_name}')
    all_delta = float(p1_summary['all']['mean_f1'] - comp_summary['all']['mean_f1'])
    bin_delta: dict[str, float | None] = {}
    nonempty: list[float] = []
    for bin_name in BINS:
        a = p1_summary[bin_name]['mean_f1']; b = comp_summary[bin_name]['mean_f1']
        if a is None or b is None:
            bin_delta[bin_name] = None
        else:
            d = float(a - b); bin_delta[bin_name] = d; nonempty.append(d)
    p1_4_24 = subset_mean(p1_rows, {'4-9', '10-24'})
    comp_4_24 = subset_mean(comp_rows, {'4-9', '10-24'})
    delta_4_24 = None if p1_4_24 is None or comp_4_24 is None else float(p1_4_24 - comp_4_24)
    broad = {
        'macro_f1_gain_ge_0_05': all_delta >= 0.05,
        'no_size_stratum_regression_gt_0_05': bool(nonempty) and min(nonempty) >= -0.05,
        'at_least_two_strata_gain_ge_0_10': sum(d >= 0.10 for d in nonempty) >= 2,
        'f1_gt_0_5_count_not_lower': int(p1_summary['all']['f1_gt_0_5']) >= int(comp_summary['all']['f1_gt_0_5']),
    }
    sparse = {
        'four_to_nine_gain_ge_0_10': bin_delta['4-9'] is not None and float(bin_delta['4-9']) >= 0.10,
        'four_to_twentyfour_gain_ge_0_10': delta_4_24 is not None and delta_4_24 >= 0.10,
        'macro_f1_not_more_than_0_10_lower': all_delta >= -0.10,
        'retain_at_least_80pct_f1_gt_0_5_count': int(p1_summary['all']['f1_gt_0_5']) >= 0.80 * int(comp_summary['all']['f1_gt_0_5']),
    }
    return {
        'macro_f1_delta_p1_minus_comparator': all_delta,
        'size_bin_delta_p1_minus_comparator': bin_delta,
        'combined_4_24': {'p1_mean_f1': p1_4_24, 'comparator_mean_f1': comp_4_24, 'delta': delta_4_24},
        'broad_gates': broad,
        'sparse_gates': sparse,
        'broad_pass': all(broad.values()),
        'sparse_pass': all(sparse.values()),
    }


def reconstruct_v8_memberships(expanded: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Recover seed-only membership sets from pretruth P1 copies; no truth is involved."""
    out: list[dict[str, Any]] = []
    for family in expanded:
        row = json.loads(json.dumps(family))
        additions = set(map(str, row.get('p1_added_event_ids', [])))
        members = set(map(str, row['event_ids']))
        require(additions <= members, f"P1 additions outside expanded family {row['family_id']}")
        seeds = sorted(members - additions)
        require(len(seeds) > 0, f"empty reconstructed v8 family {row['family_id']}")
        row['event_ids'] = seeds
        row['event_count'] = len(seeds)
        row.pop('p1_added_event_ids', None)
        row.pop('p1_added_event_count', None)
        out.append(row)
    return out


def internal_v8_report(exact: Any, p1_families: list[dict[str, Any]], truth: dict[str, str], years: dict[str, int]) -> dict[str, Any]:
    v8_families = reconstruct_v8_memberships(p1_families)
    p1_rows, p1_summary = exact.v8_annual_with_richer_summary(p1_families, truth, years)
    v8_rows, v8_summary = exact.v8_annual_with_richer_summary(v8_families, truth, years)
    delta: dict[str, Any] = {}
    for year in YEARS:
        y=str(year); delta[y]={}
        for bin_name in (*BINS, 'all'):
            a=p1_summary[y][bin_name]['mean_f1']; b=v8_summary[y][bin_name]['mean_f1']
            delta[y][bin_name] = None if a is None or b is None else float(a-b)
    return {
        'p1_annual': p1_summary,
        'v8_annual': v8_summary,
        'mean_f1_delta_p1_minus_v8': delta,
        'p1_per_label': p1_rows,
        'v8_per_label': v8_rows,
    }


def evaluate_eligible_panel(
    panel: str, checkpoint: dict[str, Any], exact: Any, base: Any,
    parsers: dict[int, Any], archives: dict[int, Path], mapping_audit: Path,
    assignment_paths: dict[str, dict[int, Path]],
) -> dict[str, Any]:
    # FIRST competitor-cluster access for this panel, after the checkpoint hashes were verified above.
    if panel == 'hdbscan':
        assignments = {year: exact.load_hdbscan(assignment_paths[panel][year], year) for year in YEARS}
    else:
        assignments = {year: exact.load_sugar(assignment_paths[panel][year], year) for year in YEARS}
    expected_ids = {year: set(assignments[year]) for year in YEARS}
    require({str(y): len(expected_ids[y]) for y in YEARS} == checkpoint['exact_event_rows'], f'exact-row count changed {panel}')

    # FIRST mapped known-shower truth access for this panel.
    truth = exact.parse_common_truth(parsers, archives, mapping_audit, base, {panel: expected_ids})[panel]
    years = {event_id: int(event_id[3:7]) for event_id in truth}
    families = checkpoint['p1_expanded_families']
    family_members = {str(eid) for f in families for eid in f['event_ids']}
    require(family_members <= set(truth), f'P1 member outside common truth {panel}')

    p1_rows_by_year, p1_summary = exact.v8_annual_with_richer_summary(families, truth, years)
    comp_rows_by_year: dict[str, Any] = {}
    comp_summary: dict[str, Any] = {}
    gates: dict[str, Any] = {}
    for year in YEARS:
        rows, summary = exact.best_competitor_matches(assignments[year], truth, year)
        comp_rows_by_year[str(year)] = rows
        comp_summary[str(year)] = summary
        gates[str(year)] = annual_pairwise_gates(p1_rows_by_year[str(year)], p1_summary[str(year)], rows, summary)

    return {
        'status': 'ELIGIBLE_EVALUATED',
        'exact_event_rows': checkpoint['exact_event_rows'],
        'p1_family_count': len(families),
        'v8_order_pretruth_sha256': checkpoint['v8_order_pretruth_sha256'],
        'p1_membership_pretruth_sha256': checkpoint['p1_membership_pretruth_sha256'],
        'p1_diagnostics': checkpoint['p1_diagnostics'],
        'p1_annual': p1_summary,
        'competitor_annual': comp_summary,
        'pairwise_gates': gates,
        'broad_pairwise_pass': all(gates[str(y)]['broad_pass'] for y in YEARS),
        'sparse_pairwise_pass': all(gates[str(y)]['sparse_pass'] for y in YEARS),
        'p1_false_positive_burden': exact.burden_for_families(families, truth),
        'competitor_false_positive_burden': {str(y): exact.burden_for_clusters(assignments[y], truth) for y in YEARS},
        'internal_v8_nonregression': internal_v8_report(exact, families, truth, years),
        'p1_per_label': p1_rows_by_year,
        'competitor_per_label': comp_rows_by_year,
    }


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--hdbscan-pretruth', required=True, type=Path)
    p.add_argument('--sugar-pretruth', required=True, type=Path)
    p.add_argument('--exact-row-runner', required=True, type=Path)
    p.add_argument('--base-runner', required=True, type=Path)
    p.add_argument('--support-source-parts', required=True, type=Path)
    p.add_argument('--candidate-payload', required=True, type=Path)
    p.add_argument('--baseline-payload', required=True, type=Path)
    p.add_argument('--scorer-parts', required=True, type=Path)
    p.add_argument('--parser-2023', required=True, type=Path)
    p.add_argument('--parser-2025', required=True, type=Path)
    p.add_argument('--mapping-audit', required=True, type=Path)
    p.add_argument('--archive-2023', required=True, type=Path)
    p.add_argument('--archive-2025', required=True, type=Path)
    p.add_argument('--hdbscan-2023', required=True, type=Path)
    p.add_argument('--hdbscan-2025', required=True, type=Path)
    p.add_argument('--sugar-2023', required=True, type=Path)
    p.add_argument('--sugar-2025', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args=p.parse_args()

    checkpoints={
        'hdbscan': load_checkpoint(args.hdbscan_pretruth, 'hdbscan'),
        'sugar': load_checkpoint(args.sugar_pretruth, 'sugar'),
    }
    # Until here, no truth or competitor cluster values have been loaded in this process.
    exact=load_module(args.exact_row_runner,'p1_posttruth_exact')
    old=load_module(args.base_runner,'p1_posttruth_base')
    support=old.load_support_module(args.support_source_parts)
    _candidate,base,_scorer=support.load_sources(args)
    archives={2023:args.archive_2023,2025:args.archive_2025}
    require(exact.sha256_file(args.mapping_audit)==exact.MAPPING_AUDIT_SHA256,'mapping audit hash changed')
    for year in YEARS:
        require(exact.sha256_file(archives[year])==exact.ARCHIVE_SHA256[year],f'archive hash changed {year}')
    parsers={2023:load_module(args.parser_2023,'p1_truth_2023'),2025:load_module(args.parser_2025,'p1_truth_2025')}
    assignment_paths={
        'hdbscan':{2023:args.hdbscan_2023,2025:args.hdbscan_2025},
        'sugar':{2023:args.sugar_2023,2025:args.sugar_2025},
    }

    results: dict[str, Any]={}
    any_ineligible=False
    for panel in ('hdbscan','sugar'):
        checkpoint=checkpoints[panel]
        if checkpoint['classification']==INELIGIBLE_CLASS:
            any_ineligible=True
            results[panel]={
                'status': INELIGIBLE_CLASS,
                'support_failure': checkpoint['support_failure'],
                'competitor_cluster_values_accessed': False,
                'known_shower_truth_accessed': False,
                'broad_pairwise_pass': False,
                'sparse_pairwise_pass': False,
            }
            continue
        results[panel]=evaluate_eligible_panel(panel,checkpoint,exact,base,parsers,archives,args.mapping_audit,assignment_paths)

    broad=(not any_ineligible) and all(results[p]['broad_pairwise_pass'] for p in ('hdbscan','sugar'))
    sparse=(not any_ineligible) and all(results[p]['sparse_pairwise_pass'] for p in ('hdbscan','sugar'))
    if any_ineligible:
        classification=INELIGIBLE_CLASS
    elif broad:
        classification='BROAD_CATALOGUE_SUPERIORITY'
    elif sparse:
        classification='SPARSE_STREAM_SUPERIORITY'
    else:
        classification='NO_LITERATURE_SUPERIORITY'

    for panel in ('hdbscan','sugar'):
        if results[panel]['status']=='ELIGIBLE_EVALUATED':
            for year in YEARS:
                require(math.isfinite(float(results[panel]['pairwise_gates'][str(year)]['macro_f1_delta_p1_minus_comparator'])),f'nonfinite endpoint {panel} {year}')

    result={
        'classification':classification,
        'years':list(YEARS),
        'blind_exclusion':[BLIND_LOW,BLIND_HIGH],
        'p1_source_sha256':P1_SOURCE_SHA256,
        'pairwise_only_no_cross_denominator_comparison':True,
        'matched_input_ineligible':any_ineligible,
        'broad_catalogue_superiority':broad,
        'sparse_stream_superiority':sparse,
        'panels':results,
        'claim_boundary':'Matched SonotaCo exact-row comparison only. Ineligible exact-v8 support cannot count as superiority and is not repaired. Eligible panels use the same frozen broad/sparse gates as v6. No result here is pristine external validation or target authorization.',
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    args.output.with_suffix(args.output.suffix+'.sha256').write_text(hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()+'\n')
    print('ORBITTRACE_P1_MATCHED_RESULT_BEGIN')
    print(json.dumps({'classification':classification,'matched_input_ineligible':any_ineligible,'broad_catalogue_superiority':broad,'sparse_stream_superiority':sparse,'panel_status':{p:results[p]['status'] for p in results}},indent=2,sort_keys=True))
    print('ORBITTRACE_P1_MATCHED_RESULT_END')
    return 0


if __name__=='__main__':
    raise SystemExit(main())

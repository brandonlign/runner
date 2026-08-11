#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

HDB_N = 229
EXPECTED_SOURCES = {'hard': 19, 'p19': 54, 'p20': 156}
EXPECTED_V31_ORDER_SHA = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'
EXPECTED_RANK_VECTOR_CANONICAL = '3c3e7d8d9a19e9ceee191901f14fec6b0ff8678fa4e67b65b1a78572df008301'
RANKGAP_SHA256 = 'e4e09546e17b9a5da7ce12ad9af4bb7129533fd9b5be846ebc859719f01a9758'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256(('\n'.join(map(str, order)) + '\n').encode()).hexdigest()


def freeze_mode(manifest_file: Path, rank_vector_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    m = json.loads(manifest_file.read_text())
    require(m['truth_accessed'] is False, '#950 manifest truth flag changed')
    require(m['target_information_access'] is False, '#950 target access changed')
    require(m['maarsy_scientific_access'] is False and m['dms_scientific_access'] is False, '#950 protected survey access changed')
    ids = list(map(str, m['family_ids']))
    sources = list(map(str, m['sources']))
    require(len(ids) == HDB_N and len(sources) == HDB_N, '#950 HDB universe changed')
    require(len(set(ids)) == HDB_N, 'duplicate #950 HDB family id')
    require(dict(Counter(sources)) == EXPECTED_SOURCES, '#950 HDB source counts changed')

    rv = json.loads(rank_vector_file.read_text())
    require(rv['verdict'] == 'PASS_V31_SAME_ROUTE_REFERENCE_COUNTERFACTUAL_VECTOR_FREEZE', 'reference rank vector verdict changed')
    require(rv['scientific_role'] == 'FULL_229_HDB_MIXED_VS_HDB_ONLY_REFERENCE_VECTOR_FROZEN_BEFORE_1046_STATUS_ATTACHMENT', 'reference rank vector role changed')
    require(int(rv['family_count']) == HDB_N and len(rv['families']) == HDB_N, 'reference rank vector universe changed')
    require(rv['canonical_family_vector_sha256'] == EXPECTED_RANK_VECTOR_CANONICAL, 'reference rank vector canonical identity changed')
    require(rv['rankgap_1046_loaded_before_vector_freeze'] is False, '#1046 status was available during reference rank freeze')
    require(rv['candidate_order_evaluated'] is False and rv['literature_panel_evaluated'] is False, 'reference vector evaluated counterfactual order')
    require(rv['successor_selected'] is False and rv['post_result_second_search'] is False, 'reference vector selected successor')
    require(rv['target_information_access'] is False and rv['target_region_events_accessed'] is False, 'reference vector target firewall changed')
    require(rv['maarsy_scientific_access'] is False and rv['dms_scientific_access'] is False, 'reference vector survey firewall changed')
    require(rv['blind_exclusion'] == [20.0, 55.0], 'reference vector blind exclusion changed')

    ranks: dict[str, int] = {}
    for row in rv['families']:
        fid = str(row['family_id'])
        require(fid not in ranks, 'duplicate family in reference vector')
        ranks[fid] = int(row['v31_rank'])
    require(set(ranks) == set(ids), '#950/reference family universes differ')
    require(sorted(ranks.values()) == list(range(1, HDB_N + 1)), 'reference v31 ranks invalid')
    v31_order = sorted(ids, key=lambda fid: (ranks[fid], fid))
    require(order_sha(v31_order) == EXPECTED_V31_ORDER_SHA, 'exact v31 HDB fused order changed')

    source_by_id = dict(zip(ids, sources))
    source_members: dict[str, list[str]] = {}
    for src in sorted(EXPECTED_SOURCES):
        members = [fid for fid in ids if source_by_id[fid] == src]
        members.sort(key=lambda fid: (ranks[fid], fid))
        require(len(members) == EXPECTED_SOURCES[src], f'source count changed: {src}')
        source_members[src] = members
    within_rank = {fid: j + 1 for src, members in source_members.items() for j, fid in enumerate(members)}

    rows: list[dict[str, Any]] = []
    for fid in v31_order:
        src = source_by_id[fid]
        n = EXPECTED_SOURCES[src]
        rg = int(ranks[fid])
        rs = int(within_rank[fid])
        pg = float((rg - 1) / (HDB_N - 1))
        ps = float((rs - 1) / (n - 1))
        adv = float(pg - ps)
        rows.append({
            'family_id': fid,
            'source': src,
            'source_candidate_count': n,
            'v31_rank': rg,
            'global_v31_percentile': pg,
            'within_source_v31_rank': rs,
            'within_source_v31_percentile': ps,
            'source_density_advantage': adv,
        })
    require(len(rows) == HDB_N and len({r['family_id'] for r in rows}) == HDB_N, 'invalid source-density vector')

    csha = canonical_sha(rows)
    result = {
        'verdict': 'PASS_V31_SOURCE_DENSITY_VECTOR_FREEZE',
        'scientific_role': 'FULL_229_HDB_V31_WITHIN_SOURCE_PERCENTILE_VECTOR_FROZEN_BEFORE_1046_STATUS_ATTACHMENT',
        'family_count': HDB_N,
        'source_counts': EXPECTED_SOURCES,
        'v31_fused_order_sha256': EXPECTED_V31_ORDER_SHA,
        'reference_rank_vector_canonical_sha256': EXPECTED_RANK_VECTOR_CANONICAL,
        'families': rows,
        'canonical_family_vector_sha256': csha,
        'advantage_definition': 'global_v31_percentile - within_source_v31_percentile; positive means better source-local standing than pooled standing',
        'rankgap_1046_loaded_before_vector_freeze': False,
        'source_quota_evaluated': False,
        'source_weight_evaluated': False,
        'candidate_order_evaluated': False,
        'literature_panel_evaluated': False,
        'source_specific_outcome_subset_selected': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'successor_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    path = output / 'V31_SOURCE_DENSITY_VECTOR.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'source_counts': EXPECTED_SOURCES, 'canonical_family_vector_sha256': csha}, indent=2, sort_keys=True))
    return 0


def summary(vals: list[float]) -> dict[str, Any]:
    require(vals, 'empty diagnostic class')
    x = np.asarray(vals, dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite source advantage')
    return {
        'count': int(len(x)),
        'median_source_density_advantage': float(np.median(x)),
        'mean_source_density_advantage': float(np.mean(x)),
        'positive_advantage_count': int(np.sum(x > 0.0)),
        'positive_advantage_fraction': float(np.mean(x > 0.0)),
        'min_source_density_advantage': float(np.min(x)),
        'max_source_density_advantage': float(np.max(x)),
    }


def diagnose_mode(vector_file: Path, rankgap_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    v = json.loads(vector_file.read_text())
    require(v['verdict'] == 'PASS_V31_SOURCE_DENSITY_VECTOR_FREEZE', 'source-density vector verdict changed')
    require(v['scientific_role'] == 'FULL_229_HDB_V31_WITHIN_SOURCE_PERCENTILE_VECTOR_FROZEN_BEFORE_1046_STATUS_ATTACHMENT', 'source-density vector role changed')
    require(int(v['family_count']) == HDB_N and len(v['families']) == HDB_N, 'source-density vector universe changed')
    require(v['source_counts'] == EXPECTED_SOURCES, 'source-density source counts changed')
    require(v['v31_fused_order_sha256'] == EXPECTED_V31_ORDER_SHA, 'source-density v31 order changed')
    require(v['canonical_family_vector_sha256'] == canonical_sha(v['families']), 'source-density canonical vector changed')
    require(v['rankgap_1046_loaded_before_vector_freeze'] is False, '#1046 status available before source-density vector freeze')
    for k in ('source_quota_evaluated','source_weight_evaluated','candidate_order_evaluated','literature_panel_evaluated','source_specific_outcome_subset_selected','threshold_selected','top_k_selected','rank_window_selected','successor_selected','post_result_second_search','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(v[k] is False, f'forbidden source-density vector flag: {k}')
    require(v['blind_exclusion'] == [20.0, 55.0], 'source-density vector blind exclusion changed')

    require(sha256(rankgap_file) == RANKGAP_SHA256, '#1046 result identity changed')
    rg = json.loads(rankgap_file.read_text())
    require(rg['verdict'] == 'PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC', '#1046 verdict changed')
    require(rg['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED', '#1046 role changed')
    require(rg['new_rank_evaluated'] is False and rg['successor_selected'] is False, '#1046 not diagnostic-only')
    require(rg['target_information_access'] is False and rg['target_region_events_accessed'] is False, '#1046 target firewall changed')
    require(rg['maarsy_scientific_access'] is False and rg['dms_scientific_access'] is False, '#1046 survey firewall changed')
    require(rg['blind_exclusion'] == [20.0, 55.0], '#1046 blind exclusion changed')

    by_id = {str(r['family_id']): r for r in v['families']}
    require(len(by_id) == HDB_N, 'duplicate source-density family')
    expected = {2013: {'candidate': 18, 'surfaced': 9, 'missed': 9}, 2014: {'candidate': 19, 'surfaced': 9, 'missed': 10}}
    annual: dict[str, Any] = {}
    detailed: dict[str, list[dict[str, Any]]] = {}
    flags: list[bool] = []

    for year in (2013, 2014):
        src = rg['annual'][str(year)]
        require(int(src['candidate_recoverable_showers']) == expected[year]['candidate'], f'#1046 candidate count changed {year}')
        require(int(src['v31_surfaced_recoverable_showers']) == expected[year]['surfaced'], f'#1046 surfaced count changed {year}')
        require(int(src['recoverable_but_missed_showers']) == expected[year]['missed'], f'#1046 missed count changed {year}')
        rows = [r for r in src['rows'] if bool(r.get('candidate_recoverable', False))]
        require(len(rows) == expected[year]['candidate'], f'#1046 recoverable row count changed {year}')
        missed: list[float] = []
        surfaced: list[float] = []
        outrows: list[dict[str, Any]] = []
        for r in rows:
            fid = r.get('first_recoverable_family_id_by_v31_fused_rank')
            require(fid is not None and str(fid) in by_id, f'#1046 representative missing {year}')
            is_missed = bool(r.get('recoverable_but_missed', False))
            is_surfaced = bool(r.get('v31_surfaced_recoverable', False))
            require(is_missed != is_surfaced, f'#1046 recoverable status not exclusive {year}')
            vr = by_id[str(fid)]
            a = float(vr['source_density_advantage'])
            require(np.isfinite(a), f'nonfinite source advantage {year}')
            if is_missed:
                missed.append(a); cls = 'RECOVERABLE_BUT_MISSED'
            else:
                surfaced.append(a); cls = 'SURFACED_RECOVERABLE'
            outrows.append({
                'diagnostic_group': str(r['label']),
                'fixed_recoverable_family_id': str(fid),
                'class': cls,
                'source': str(vr['source']),
                'source_candidate_count': int(vr['source_candidate_count']),
                'v31_rank': int(vr['v31_rank']),
                'global_v31_percentile': float(vr['global_v31_percentile']),
                'within_source_v31_rank': int(vr['within_source_v31_rank']),
                'within_source_v31_percentile': float(vr['within_source_v31_percentile']),
                'source_density_advantage': a,
            })
        require(len(missed) == expected[year]['missed'] and len(surfaced) == expected[year]['surfaced'], f'diagnostic class count changed {year}')
        ms = summary(missed); ss = summary(surfaced)
        positive_pass = bool(ms['median_source_density_advantage'] > 0.0)
        separation_pass = bool(ms['median_source_density_advantage'] > ss['median_source_density_advantage'])
        annual[str(year)] = {
            'missed_recoverable': ms,
            'surfaced_recoverable': ss,
            'median_difference_missed_minus_surfaced': float(ms['median_source_density_advantage'] - ss['median_source_density_advantage']),
            'missed_median_strictly_positive': positive_pass,
            'missed_median_strictly_greater_than_surfaced': separation_pass,
            'direction_pass': bool(positive_pass and separation_pass),
        }
        detailed[str(year)] = outrows
        flags.extend([positive_pass, separation_pass])

    passed = bool(all(flags))
    result = {
        'verdict': 'PASS_V31_SOURCE_DENSITY_SUPPRESSION_DIAGNOSTIC' if passed else 'FAIL_V31_SOURCE_DENSITY_SUPPRESSION_DIAGNOSTIC',
        'scientific_role': 'POST_V60_PROPOSAL_SOURCE_DENSITY_MECHANISM_DIAGNOSTIC_ONLY_NO_SOURCE_NORMALIZED_ORDER_EVALUATED',
        'question': 'Do #1046 missed recoverable HDB groups have larger positive source-local-vs-global v31 rank advantage than surfaced recoverable groups in both years?',
        'source_density_vector_sha256': sha256(vector_file),
        'source_density_vector_canonical_sha256': v['canonical_family_vector_sha256'],
        'source_1046_run': 31451236076,
        'source_1046_artifact': 9086399760,
        'source_1046_artifact_digest': 'sha256:a2c373df77ef7e0065c1d8aceb1f6e5826f1e30b6286f2331c362d959f1d7f69',
        'source_1046_result_sha256': RANKGAP_SHA256,
        'statistic': 'source_density_advantage = global exact-v31 percentile - within-immutable-proposal-source exact-v31 percentile on #1046 fixed first-recoverable family',
        'annual_diagnostics': annual,
        'diagnostic_rows': detailed,
        'all_four_direction_inequalities_pass': passed,
        'source_normalized_candidate_order_evaluated': False,
        'source_quota_search': False,
        'source_weight_search': False,
        'source_specific_outcome_subset_search': False,
        'threshold_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'feature_search': False,
        'metric_search': False,
        'k_search': False,
        'scaling_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'alternate_representative_search': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'oracle_identity_used_for_ranking': False,
        'successor_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    path = output / 'V31_SOURCE_DENSITY_SUPPRESSION_DIAGNOSTIC.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'annual_diagnostics': annual}, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('freeze')
    a.add_argument('--manifest-file', type=Path, required=True)
    a.add_argument('--rank-vector-file', type=Path, required=True)
    a.add_argument('--output', type=Path, required=True)
    b = sub.add_parser('diagnose')
    b.add_argument('--vector-file', type=Path, required=True)
    b.add_argument('--rankgap-file', type=Path, required=True)
    b.add_argument('--output', type=Path, required=True)
    x = p.parse_args()
    if x.mode == 'freeze':
        return freeze_mode(x.manifest_file, x.rank_vector_file, x.output)
    return diagnose_mode(x.vector_file, x.rankgap_file, x.output)


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import pickle
import re
import types
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2023, 2025)
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
P1_SOURCE_SHA256 = 'e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508'
V8_SOURCE_COMMIT = 'c9d6c44704013ba0c9430100e98a29a56b453304'
SUPPORT_INELIGIBLE_RE = re.compile(r'^family ([A-Za-z0-9_.:-]+) year (2023|2025) has only ([0-9]+) events in local window$')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f'cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def p1_covariance_for_panel_family(
    p1: Any,
    family: dict[str, Any],
    event_lookup_by_year: dict[int, dict[str, dict[str, Any]]],
    base: Any,
) -> tuple[np.ndarray, float, dict[int, dict[str, float]], dict[str, Any]]:
    residuals: list[np.ndarray] = []
    counts: dict[str, int] = {}
    centers: dict[int, dict[str, float]] = {}
    ordered_family_ids = [str(eid) for eid in family['event_ids']]
    require(len(ordered_family_ids) == len(set(ordered_family_ids)), f"duplicate immutable seed ID in family {family['family_id']}")
    for year in YEARS:
        # Preserve the immutable family event order exactly. Do not route the
        # seed union through a set: OAS is mathematically permutation-invariant,
        # but floating reduction order and pretruth hashes must be deterministic.
        rows = [event_lookup_by_year[year][eid] for eid in ordered_family_ids if eid in event_lookup_by_year[year]]
        require(len(rows) >= 4, f"family {family['family_id']} has <4 immutable seeds in {year}")
        center = p1.pooled_centroid(rows)
        centers[year] = center
        residuals.append(p1.residual_matrix(rows, center, base))
        counts[str(year)] = len(rows)
    x = np.vstack(residuals)
    model = p1.OAS(assume_centered=False).fit(x)
    cov = np.asarray(model.covariance_, dtype=np.float64)
    sign, logdet = np.linalg.slogdet(cov)
    require(sign > 0 and np.isfinite(logdet), f"non-positive covariance for {family['family_id']}")
    inv = np.linalg.inv(cov)
    return inv, float(logdet), centers, {'seed_counts': counts, 'oas_shrinkage': float(model.shrinkage_)}


def apply_exact_p1_membership(
    p1: Any,
    families_in_rank_order: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require(float(p1.INNER_PROB) == 0.99, 'P1 inner probability changed')
    require(float(p1.OUTER_PROB) == 0.9999, 'P1 outer probability changed')
    require(float(p1.BACKGROUND_UPPER_CONFIDENCE) == 0.95, 'P1 background confidence changed')
    require(float(p1.MAP_THRESHOLD) == 0.5, 'P1 responsibility threshold changed')

    event_lookup_by_year = {year: {str(e['id']): e for e in scan_by_year[year]} for year in YEARS}
    arrays_by_year = {year: p1.event_arrays(scan_by_year[year]) for year in YEARS}
    global_seed_ids = set().union(*(set(map(str, f['event_ids'])) for f in families_in_rank_order))

    inner_d2 = float(p1.chi2.ppf(p1.INNER_PROB, 4))
    outer_d2 = float(p1.chi2.ppf(p1.OUTER_PROB, 4))
    inner_v = p1.volume4_from_d2(inner_d2)
    shell_v = p1.volume4_from_d2(outer_d2) - inner_v
    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    family_audits: list[dict[str, Any]] = []

    for family_index, family in enumerate(families_in_rank_order, start=1):
        inv_cov, logdet, centers, cov_audit = p1_covariance_for_panel_family(p1, family, event_lookup_by_year, base)
        sqrt_det = math.exp(0.5 * logdet)
        for year in YEARS:
            center = centers[year]
            events = arrays_by_year[year]['events']
            ids = arrays_by_year[year]['ids']
            x = p1.residual_matrix(events, center, base)
            d2 = np.einsum('ij,jk,ik->i', x, inv_cov, x, optimize=True)
            nonseed = np.asarray([str(eid) not in global_seed_ids for eid in ids], dtype=bool)
            shell = nonseed & (d2 > inner_d2) & (d2 <= outer_d2)
            inner = nonseed & (d2 <= inner_d2)
            n_shell = int(np.sum(shell))
            n_inner = int(np.sum(inner))
            shell_mean_upper = p1.poisson_rate_upper(n_shell, p1.BACKGROUND_UPPER_CONFIDENCE)
            lambda_bg = shell_mean_upper / (sqrt_det * shell_v)
            expected_bg_inner = lambda_bg * sqrt_det * inner_v
            current_seed_count = sum(str(eid) in event_lookup_by_year[year] for eid in family['event_ids'])
            nonseed_excess = max(0.0, float(n_inner) - float(expected_bg_inner))
            stream_total = (float(current_seed_count) + nonseed_excess) / p1.INNER_PROB

            idxs = np.flatnonzero(inner)
            if idxs.size:
                normalizer = ((2.0 * math.pi) ** -2) / sqrt_det
                intensities = stream_total * normalizer * np.exp(-0.5 * d2[idxs])
                for idx, intensity in zip(idxs.tolist(), intensities.tolist()):
                    if intensity <= 0.0:
                        continue
                    eid = str(ids[idx])
                    proposals_by_event[eid].append({
                        'family_index': family_index - 1,
                        'family_id': str(family['family_id']),
                        'year': year,
                        'stream_intensity': float(intensity),
                        'background_intensity_upper': float(lambda_bg),
                        'd2': float(d2[idx]),
                    })
            family_audits.append({
                'family_id': str(family['family_id']),
                'year': year,
                'seed_count': int(current_seed_count),
                'n_inner_nonseed': n_inner,
                'n_shell_nonseed': n_shell,
                'background_intensity_upper': float(lambda_bg),
                'expected_background_inner': float(expected_bg_inner),
                'estimated_nonseed_excess': float(nonseed_excess),
                'estimated_stream_total': float(stream_total),
                **cov_audit,
            })

    assignments: dict[str, dict[str, Any]] = {}
    conflicts = 0
    posterior_values: list[float] = []
    for eid, proposals in proposals_by_event.items():
        require(eid not in global_seed_ids, 'immutable seed entered P1 competition')
        if len(proposals) > 1:
            conflicts += 1
        total_stream = float(sum(p['stream_intensity'] for p in proposals))
        background = float(max(p['background_intensity_upper'] for p in proposals))
        denom = total_stream + background
        if denom <= 0.0:
            continue
        ranked = sorted(proposals, key=lambda p: (-p['stream_intensity'], p['d2'], p['family_index'], p['family_id']))
        best = dict(ranked[0])
        posterior = float(best['stream_intensity'] / denom)
        if posterior <= p1.MAP_THRESHOLD:
            continue
        best['posterior'] = posterior
        assignments[eid] = best
        posterior_values.append(posterior)

    added_by_family: dict[int, list[str]] = defaultdict(list)
    for eid, rec in assignments.items():
        added_by_family[int(rec['family_index'])].append(eid)
    expanded: list[dict[str, Any]] = []
    for idx, family in enumerate(families_in_rank_order):
        out = json.loads(json.dumps(family))
        seeds = set(map(str, family['event_ids']))
        additions = sorted(set(added_by_family.get(idx, [])) - global_seed_ids)
        out['p1_added_event_ids'] = additions
        out['p1_added_event_count'] = len(additions)
        out['event_ids'] = sorted(seeds | set(additions))
        out['event_count'] = len(out['event_ids'])
        expanded.append(out)

    diagnostics = {
        'proposal_events': len(proposals_by_event),
        'conflicted_proposal_events': conflicts,
        'assigned_nonseed_events': len(assignments),
        'families_gaining_members': sum(bool(added_by_family.get(i)) for i in range(len(families_in_rank_order))),
        'posterior_median': float(np.median(posterior_values)) if posterior_values else None,
        'posterior_min': float(min(posterior_values)) if posterior_values else None,
        'posterior_max': float(max(posterior_values)) if posterior_values else None,
        'inner_d2': inner_d2,
        'outer_d2': outer_d2,
        'family_year_audits': family_audits,
    }
    return expanded, diagnostics


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--panel', required=True, choices=('hdbscan', 'sugar'))
    p.add_argument('--strict-id-manifest', required=True, type=Path)
    p.add_argument('--exact-row-runner', required=True, type=Path)
    p.add_argument('--p1-source', required=True, type=Path)
    p.add_argument('--archive-2023', required=True, type=Path)
    p.add_argument('--archive-2025', required=True, type=Path)
    p.add_argument('--support-source-parts', required=True, type=Path)
    p.add_argument('--candidate-payload', required=True, type=Path)
    p.add_argument('--baseline-payload', required=True, type=Path)
    p.add_argument('--scorer-parts', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    require(sha256_file(args.p1_source) == P1_SOURCE_SHA256, 'frozen P1 source changed')
    manifest = json.loads(args.strict_id_manifest.read_text())
    require(manifest['classification'] == 'P1 matched-literature strict pretruth ID-only manifest', 'wrong manifest type')
    require(manifest['years'] == list(YEARS), 'manifest years changed')
    require(manifest['blind_exclusion'] == [BLIND_LOW, BLIND_HIGH], 'manifest blind interval changed')
    require(manifest['competitor_cluster_values_parsed'] is False, 'competitor labels entered manifest')
    require(manifest['known_shower_truth_values_parsed'] is False, 'truth entered manifest')
    require(manifest['native_shower_tokens_parsed'] is False, 'native labels entered manifest')
    sidecar = args.strict_id_manifest.with_suffix(args.strict_id_manifest.suffix + '.sha256')
    require(sidecar.exists() and sidecar.read_text().strip() == canonical_sha(manifest), 'manifest hash mismatch')

    exact = load_module(args.exact_row_runner, f'p1_exact_row_{args.panel}')
    p1 = load_module(args.p1_source, 'p1_frozen_membership_source')
    archives = {2023: args.archive_2023, 2025: args.archive_2025}
    for year in YEARS:
        require(sha256_file(archives[year]) == exact.ARCHIVE_SHA256[year], f'archive hash changed {year}')

    runtime = exact.v8.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    require(float(support.BLIND_LOW) == BLIND_LOW and float(support.BLIND_HIGH) == BLIND_HIGH, 'blind interval changed')
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = 'p1-sonotaco-exact-row-pretruth'
    support.RANKING_VARIANTS = exact.RAW_FIXED4_RANKING_VARIANTS
    source_args = types.SimpleNamespace(
        support_source_parts=args.support_source_parts,
        candidate_payload=args.candidate_payload,
        baseline_payload=args.baseline_payload,
        scorer_parts=args.scorer_parts,
    )
    _candidate, base, _scorer = support.load_sources(source_args)
    exact.v8.YEARS = YEARS
    exact.v8.MONTH_KEYS = tuple()
    exact.v8.mult.YEARS = YEARS
    exact.v8.mult.MONTH_KEYS = tuple()

    ids_by_year = {
        year: set(map(str, manifest['panels'][args.panel][str(year)]['scan_ids']))
        for year in YEARS
    }
    scan_by_year = {
        year: exact.read_exact_geometry(year, archives[year], ids_by_year[year], base)
        for year in YEARS
    }
    require(all(all(not (BLIND_LOW <= float(e['sol']) <= BLIND_HIGH) for e in scan_by_year[y]) for y in YEARS), 'target interval entered P1 panel')

    try:
        v8_panel = exact.run_v8_panel(args.panel, scan_by_year, support, runtime, base)
    except RuntimeError as exc:
        match = SUPPORT_INELIGIBLE_RE.fullmatch(str(exc))
        if match is None:
            raise
        payload = {
            'classification': 'P1_MATCHED_INPUT_INELIGIBLE_EXACT_V8_SUPPORT',
            'panel': args.panel,
            'years': list(YEARS),
            'blind_exclusion': [BLIND_LOW, BLIND_HIGH],
            'support_failure': {
                'family_id': match.group(1),
                'year': int(match.group(2)),
                'available_local_events': int(match.group(3)),
                'required_episode_events': 128,
                'exact_exception': str(exc),
            },
            'competitor_cluster_values_accessed': False,
            'known_shower_truth_accessed': False,
            'p1_membership_executed': False,
            'no_support_relaxation': True,
        }
        args.output.write_bytes(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
        args.output.with_suffix(args.output.suffix + '.sha256').write_text(sha256_file(args.output) + '\n')
        print('P1_MATCHED_INPUT_INELIGIBLE_EXACT_V8_SUPPORT', json.dumps(payload['support_failure'], sort_keys=True))
        return 0

    families_by_id = {str(f['family_id']): f for f in v8_panel['families']}
    order = list(map(str, v8_panel['multiplicity_order']))
    require(len(order) == len(families_by_id) and set(order) == set(families_by_id), 'v8 order/family universe mismatch')
    families = [families_by_id[fid] for fid in order]
    expanded, diagnostics = apply_exact_p1_membership(p1, families, scan_by_year, base)
    family_bytes = json.dumps(expanded, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    order_bytes = json.dumps(order, separators=(',', ':')).encode()
    family_sha = hashlib.sha256(family_bytes).hexdigest()
    order_sha = hashlib.sha256(order_bytes).hexdigest()

    checkpoint = {
        'classification': 'P1 matched-literature pretruth panel checkpoint',
        'panel': args.panel,
        'years': list(YEARS),
        'blind_exclusion': [BLIND_LOW, BLIND_HIGH],
        'v8_source_commit': V8_SOURCE_COMMIT,
        'p1_source_sha256': P1_SOURCE_SHA256,
        'exact_event_rows': {str(y): len(scan_by_year[y]) for y in YEARS},
        'v8_family_count': len(families),
        'v8_multiplicity_order': order,
        'v8_order_pretruth_sha256': order_sha,
        'p1_expanded_families': expanded,
        'p1_membership_pretruth_sha256': family_sha,
        'p1_diagnostics': diagnostics,
        'v8_pretruth': {
            'support_rankings': v8_panel['support_rankings'],
            'repair': v8_panel['repair'],
            'scoring_summary': v8_panel['scoring_summary'],
            'scan_audits': v8_panel['scan_audits'],
            'quartets': v8_panel['quartets'],
            'components': v8_panel['components'],
        },
        'competitor_cluster_values_accessed': False,
        'known_shower_truth_accessed': False,
        'membership_and_rank_frozen_before_truth': True,
    }
    args.output.write_bytes(pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL))
    args.output.with_suffix(args.output.suffix + '.sha256').write_text(sha256_file(args.output) + '\n')
    print(f"PASS_P1_MATCHED_PRETRUTH panel={args.panel} families={len(families)} membership_sha={family_sha} order_sha={order_sha}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

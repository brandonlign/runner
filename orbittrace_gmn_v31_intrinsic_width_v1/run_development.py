#!/usr/bin/env python3
"""Frozen target-excluded GMN v31 + measurement-noise-deconvolved intrinsic width."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np

BLIND = (20.0, 55.0)
YEARS = (2022, 2023)
N = 226
D = 23
TOTAL_MEMBERS = 8794
P19_PRELABEL_SHA = '276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
V8_SHA = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
MANIFEST_SHA = '16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7'
X_SHA = 'fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5'
C_SHA = 'a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f'
MARGIN_SHA = 'f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd'
RANKER_SHA = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
UNCERTAINTY_GZIP_SHA = '01de5502aab911fa251656cd7a71ab4b6ef6158abf3a675495c4ba4d1c349622'
HARD = {
    'recovered_at_25': 21,
    'recovered_at_50': 38,
    'recovered_at_100': 59,
    'top100_dominant_precision': 0.6884631112636006,
    'mrr': 0.046734076055452344,
    'qualified_matches': 95,
}
PARENT = {
    'recovered_at_25': 23,
    'recovered_at_50': 41,
    'recovered_at_100': 66,
    'top100_dominant_precision': 0.7229521515453452,
    'mrr': 0.050244164168646674,
    'qualified_matches': 95,
}


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arrsha(a: np.ndarray) -> str:
    a = np.ascontiguousarray(a)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(str(tuple(a.shape)).encode())
    h.update(a.tobytes())
    return h.hexdigest()


def ordersha(items: list[str]) -> str:
    return hashlib.sha256('\n'.join(items).encode()).hexdigest()


def close(a: float, b: float, atol: float = 1e-15) -> bool:
    return abs(float(a) - float(b)) <= atol


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f'cannot load {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signed_delta(a: float, b: float) -> float:
    return (float(a) - float(b) + 180.0) % 360.0 - 180.0


def equal_fuse(hard: list[str], local: list[str]) -> list[str]:
    hr = {x: i + 1 for i, x in enumerate(hard)}
    lr = {x: i + 1 for i, x in enumerate(local)}
    return sorted(hard, key=lambda x: (hr[x] + lr[x], hr[x], x))


def trim(metrics: dict) -> dict:
    return {k: v for k, v in metrics.items() if k != 'first_rank_by_label'}


def assert_metrics(metrics: dict, expected: dict, label: str) -> None:
    for key, value in expected.items():
        if isinstance(value, float):
            req(close(metrics[key], value), f'{label} {key}: {metrics[key]} != {value}')
        else:
            req(int(metrics[key]) == value, f'{label} {key}: {metrics[key]} != {value}')


def oof_margin(
    X: np.ndarray,
    folds: np.ndarray,
    y: np.ndarray,
    ids: list[str],
    hard_rank: dict[str, int],
) -> np.ndarray:
    out = np.zeros(len(ids), dtype=float)
    for fold in range(5):
        tr = folds != fold
        te = folds == fold
        mu = X[tr].mean(0)
        sd = X[tr].std(0, ddof=0)
        scale = sd.copy()
        scale[scale == 0] = 1.0
        ztr = (X[tr] - mu) / scale
        zte = (X[te] - mu) / scale
        yt = y[tr]
        tids = [ids[i] for i in np.where(tr)[0]]
        positives = ztr[yt]
        negatives = ztr[~yt]
        pids = [tids[i] for i in np.where(yt)[0]]
        nids = [tids[i] for i in np.where(~yt)[0]]
        req(len(positives) > 0 and len(negatives) > 0, f'empty reference class in fold {fold}')
        for j, gi in enumerate(np.where(te)[0]):
            dp = np.linalg.norm(positives - zte[j], axis=1)
            dn = np.linalg.norm(negatives - zte[j], axis=1)
            ip = min(range(len(dp)), key=lambda i: (float(dp[i]), hard_rank[pids[i]], pids[i]))
            inn = min(range(len(dn)), key=lambda i: (float(dn[i]), hard_rank[nids[i]], nids[i]))
            out[gi] = float(dn[inn] - dp[ip])
    req(np.isfinite(out).all(), 'nonfinite OOF margin')
    return out


def load_uncertainty(path: Path) -> dict[str, dict]:
    req(sha(path) == UNCERTAINTY_GZIP_SHA, 'fixed-member uncertainty gzip changed')
    rows: dict[str, dict] = {}
    with gzip.open(path, 'rt', encoding='utf-8') as handle:
        for line in handle:
            row = json.loads(line)
            eid = str(row['id'])
            req(eid not in rows, f'duplicate uncertainty member {eid}')
            req(int(row['year']) in YEARS, f'unexpected uncertainty year {eid}')
            sol = float(row['sol'])
            req(math.isfinite(sol) and not (BLIND[0] <= sol <= BLIND[1]), f'protected uncertainty row {eid}')
            for key in ('ra', 'dec', 'vg', 'ra_sigma', 'dec_sigma', 'vg_sigma'):
                req(math.isfinite(float(row[key])), f'nonfinite uncertainty field {key} {eid}')
            req(0.0 <= float(row['ra']) < 360.0, f'invalid RA {eid}')
            req(-90.0 <= float(row['dec']) <= 90.0, f'invalid Dec {eid}')
            req(float(row['vg']) > 0.0, f'invalid Vg {eid}')
            req(float(row['ra_sigma']) >= 0.0 and float(row['dec_sigma']) >= 0.0 and float(row['vg_sigma']) >= 0.0, f'invalid uncertainty {eid}')
            rows[eid] = row
    req(len(rows) == TOTAL_MEMBERS, f'uncertainty member count changed: {len(rows)}')
    return rows


def annual_intrinsic_width(
    family: dict,
    year: int,
    lookup: dict[str, dict],
    uncertainty: dict[str, dict],
) -> dict:
    centroid = family.get('centroids', {}).get(str(year))
    req(centroid is not None, f'missing centroid {family["family_id"]} {year}')
    eids = [str(e) for e in family['event_ids'] if int(str(e)[:4]) == year]
    n = len(eids)
    req(n >= 4, f'insufficient annual members {family["family_id"]} {year}: {n}')

    phase = np.empty(n, dtype=float)
    physical = np.empty((n, 3), dtype=float)
    q = np.empty(n, dtype=float)
    cos_lat = math.cos(math.radians(float(centroid['ecl_lat'])))
    req(math.isfinite(cos_lat), f'invalid centroid latitude {family["family_id"]} {year}')

    for j, eid in enumerate(eids):
        event = lookup.get(eid)
        u = uncertainty.get(eid)
        req(event is not None, f'fixed member absent from v31 lookup {eid}')
        req(u is not None, f'fixed member absent from uncertainty audit {eid}')
        req(int(u['year']) == year, f'uncertainty year mismatch {eid}')
        req(abs(float(event['sol']) - float(u['sol'])) <= 1e-9, f'solar-longitude provenance mismatch {eid}')
        req(abs(float(event['vg']) - float(u['vg'])) <= 1e-9, f'Vg provenance mismatch {eid}')
        phase[j] = signed_delta(float(event['sol']), float(centroid['sol']))
        vg = float(event['vg'])
        cvg = float(centroid['vg'])
        req(vg > 0.0 and cvg > 0.0, f'invalid speed {eid}')
        physical[j, 0] = signed_delta(float(event['sun_lon']), float(centroid['sun_lon'])) * cos_lat / 4.0
        physical[j, 1] = (float(event['ecl_lat']) - float(centroid['ecl_lat'])) / 4.0
        physical[j, 2] = math.log(vg / cvg) / math.log(1.10)

        dec = math.radians(float(u['dec']))
        ra_term = (float(u['ra_sigma']) * math.cos(dec) / 4.0) ** 2
        dec_term = (float(u['dec_sigma']) / 4.0) ** 2
        vg_term = ((float(u['vg_sigma']) / float(u['vg'])) / math.log(1.10)) ** 2
        q[j] = ra_term + dec_term + vg_term

    req(np.isfinite(phase).all() and np.isfinite(physical).all() and np.isfinite(q).all(), f'nonfinite width inputs {family["family_id"]} {year}')
    req(np.all(q >= 0.0), f'negative noise trace {family["family_id"]} {year}')

    design = np.column_stack([np.ones(n, dtype=float), phase])
    req(int(np.linalg.matrix_rank(design)) == 2, f'rank-deficient annual drift design {family["family_id"]} {year}')
    gram_inv = np.linalg.inv(design.T @ design)
    leverage = np.einsum('ij,ij->i', design @ gram_inv, design)
    req(np.isfinite(leverage).all(), f'nonfinite leverage {family["family_id"]} {year}')
    req(np.all(leverage >= -1e-12) and np.all(leverage <= 1.0 + 1e-12), f'invalid leverage {family["family_id"]} {year}')

    coef, _resid, _rank, _singular = np.linalg.lstsq(design, physical, rcond=None)
    residual = physical - design @ coef
    df = n - 2
    v_obs = float(np.sum(residual * residual) / df)
    v_noise = float(np.sum((1.0 - leverage) * q) / df)
    req(math.isfinite(v_obs) and v_obs >= -1e-12, f'invalid observed variance {family["family_id"]} {year}')
    req(math.isfinite(v_noise) and v_noise >= -1e-12, f'invalid noise variance {family["family_id"]} {year}')
    v_obs = max(0.0, v_obs)
    v_noise = max(0.0, v_noise)
    v_intrinsic = max(0.0, v_obs - v_noise)
    width = math.sqrt(v_intrinsic)
    quality_width = math.sqrt(v_noise)
    req(math.isfinite(width) and math.isfinite(quality_width), f'nonfinite width {family["family_id"]} {year}')
    return {
        'n': n,
        'v_obs': v_obs,
        'v_noise': v_noise,
        'v_intrinsic': v_intrinsic,
        'intrinsic_width': width,
        'quality_width': quality_width,
        'phase_min': float(np.min(phase)),
        'phase_max': float(np.max(phase)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in (
        'ranker_source',
        'support_source_parts',
        'candidate_payload',
        'baseline_payload',
        'scorer_parts',
        'v8_result_json',
        'p19_prelabel_json',
        'offline_manifest',
        'offline_x',
        'offline_centroids',
        'member_uncertainty_gzip',
        'output',
    ):
        parser.add_argument('--' + name.replace('_', '-'), dest=name, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    req(sha(args.ranker_source) == RANKER_SHA, 'ranker changed')
    req(sha(args.v8_result_json) == V8_SHA, 'v8 changed')
    req(sha(args.p19_prelabel_json) == P19_PRELABEL_SHA, 'P19 prelabel changed')
    req(sha(args.offline_manifest) == MANIFEST_SHA, 'offline manifest changed')
    uncertainty = load_uncertainty(args.member_uncertainty_gzip)

    qmod = load(args.ranker_source, 'frozen_ranker')
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1, 13))
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = qmod.v1.mult.MONTH_KEYS
    support.CORPUS = 'orbittrace-gmn-v31-intrinsic-width-v1'
    support.RANKING_VARIANTS = ('persistence',)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, 'firewall changed')
    setattr(args, 'fixed4_baseline_json', args.v8_result_json)
    _candidate, baseline, _scorer = support.load_sources(args)
    scan, _calibration, labels, _sources = support.parse_catalogue(baseline)
    req(sorted(scan) == list(YEARS), 'years changed')

    p19 = json.loads(args.p19_prelabel_json.read_text())
    hard = p19['hard_families']
    hard_order = [str(x) for x in p19['hard_order']]
    req(len(hard) == N and len(hard_order) == N, 'hard universe changed')
    ids = [str(f['family_id']) for f in hard]
    manifest = json.loads(args.offline_manifest.read_text())
    req(ids == list(map(str, manifest['family_input_order'])), 'offline/raw family order mismatch')
    by = {str(f['family_id']): f for f in hard}
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    hard_member_ids = [str(e) for f in hard for e in f['event_ids']]
    req(len(hard_member_ids) == TOTAL_MEMBERS and len(set(hard_member_ids)) == TOTAL_MEMBERS, 'fixed hard member universe changed')
    req(set(hard_member_ids) == set(uncertainty), 'uncertainty IDs differ from exact fixed family members')

    eligible = qmod.v1.eligible_labels(labels)
    truths = {fid: qmod.v1.family_truth(by[fid], labels, eligible) for fid in ids}
    lookup = qmod.v2.event_lookup(scan)
    centroid_matrix = qmod.centroid_matrix(hard)
    req(arrsha(centroid_matrix) == C_SHA, 'reconstructed centroid hash mismatch')
    neighbor_features = qmod.neighbor_features(centroid_matrix)

    rows = []
    for i, family in enumerate(hard):
        structural = qmod.v1.structural_features(family, hard_rank)
        req(len(structural) == 14, 'structural schema changed')
        rows.append(structural[1:11] + qmod.v2.cohesion_features(family, lookup, support, baseline) + neighbor_features[i].tolist())
    X = np.asarray(rows, dtype=float)
    req(X.shape == (N, D) and np.isfinite(X).all(), '23D reconstruction invalid')
    req(arrsha(X) == X_SHA, 'reconstructed 23D hash mismatch')
    Xoff = np.load(args.offline_x, allow_pickle=False)
    Coff = np.load(args.offline_centroids, allow_pickle=False)
    req(arrsha(Xoff) == X_SHA and arrsha(Coff) == C_SHA, 'offline hashes changed')
    req(np.array_equal(X, Xoff) and np.array_equal(centroid_matrix, Coff), 'offline arrays differ from raw reconstruction')

    folds = np.asarray([int(row['fold']) for row in manifest['rows']], dtype=int)
    y = np.asarray([bool(row['truth']['positive']) for row in manifest['rows']], dtype=bool)
    req(set(folds.tolist()) == set(range(5)) and int(y.sum()) == 111, 'offline fold/truth changed')
    raw_groups = [
        ('SHOWER/' + str(truths[fid]['best_label'])) if truths[fid]['best_label'] is not None else ('NEG/' + fid)
        for fid in ids
    ]
    req(raw_groups == [str(row['strict_group']) for row in manifest['rows']], 'strict groups changed')

    parent = oof_margin(X, folds, y, ids, hard_rank)
    req(arrsha(parent) == MARGIN_SHA, 'parent margin hash mismatch')

    intrinsic = []
    quality_only = []
    per_family = []
    for family in hard:
        annual = {}
        for year in YEARS:
            annual[str(year)] = annual_intrinsic_width(family, year, lookup, uncertainty)
        w = max(annual[str(year)]['intrinsic_width'] for year in YEARS)
        qwidth = max(annual[str(year)]['quality_width'] for year in YEARS)
        intrinsic.append(w)
        quality_only.append(qwidth)
        per_family.append({
            'family_id': str(family['family_id']),
            'intrinsic_width': float(w),
            'quality_only_width': float(qwidth),
            'annual': annual,
        })

    intrinsic_vec = np.asarray(intrinsic, dtype=float)
    quality_vec = np.asarray(quality_only, dtype=float)
    req(intrinsic_vec.shape == (N,) and np.isfinite(intrinsic_vec).all() and np.all(intrinsic_vec >= 0.0), 'intrinsic-width vector invalid')
    req(quality_vec.shape == (N,) and np.isfinite(quality_vec).all() and np.all(quality_vec >= 0.0), 'quality-only vector invalid')

    X_intrinsic = np.column_stack([X, intrinsic_vec])
    X_quality = np.column_stack([X, quality_vec])
    candidate = oof_margin(X_intrinsic, folds, y, ids, hard_rank)
    ablation = oof_margin(X_quality, folds, y, ids, hard_rank)

    tie = [(hard_rank[fid], fid) for fid in ids]
    parent_idx = qmod.diversity_order(parent, centroid_matrix, 0.8, 1.0, tie)
    parent_local = [ids[i] for i in parent_idx]
    parent_fused = equal_fuse(hard_order, parent_local)
    fam_stub = [{'family_id': fid} for fid in ids]
    parent_metrics = qmod.v1.monotone_metrics(fam_stub, parent_fused, truths, eligible)
    hard_metrics = qmod.v1.monotone_metrics(fam_stub, hard_order, truths, eligible)
    assert_metrics(parent_metrics, PARENT, 'parent')
    assert_metrics(hard_metrics, HARD, 'hard')

    candidate_idx = qmod.diversity_order(candidate, centroid_matrix, 0.8, 1.0, tie)
    candidate_local = [ids[i] for i in candidate_idx]
    candidate_fused = equal_fuse(hard_order, candidate_local)
    candidate_local_metrics = qmod.v1.monotone_metrics(fam_stub, candidate_local, truths, eligible)
    candidate_metrics = qmod.v1.monotone_metrics(fam_stub, candidate_fused, truths, eligible)

    ablation_idx = qmod.diversity_order(ablation, centroid_matrix, 0.8, 1.0, tie)
    ablation_local = [ids[i] for i in ablation_idx]
    ablation_fused = equal_fuse(hard_order, ablation_local)
    ablation_metrics = qmod.v1.monotone_metrics(fam_stub, ablation_fused, truths, eligible)

    req(int(candidate_metrics['qualified_matches']) == 95, 'qualified count changed')
    gates = {
        'recovered_at_100_strictly_better_than_parent': int(candidate_metrics['recovered_at_100']) > 66,
        'recovered_at_50_not_worse_than_parent': int(candidate_metrics['recovered_at_50']) >= 41,
        'recovered_at_25_not_worse_than_parent': int(candidate_metrics['recovered_at_25']) >= 23,
        'top100_precision_not_worse_than_parent': float(candidate_metrics['top100_dominant_precision']) >= PARENT['top100_dominant_precision'],
        'mrr_not_worse_than_parent': float(candidate_metrics['mrr']) >= PARENT['mrr'],
        'qualified_count_identical': int(candidate_metrics['qualified_matches']) == 95,
        'all_families_have_finite_widths': len(per_family) == N and all(math.isfinite(float(r['intrinsic_width'])) for r in per_family),
        'exact_fixed_member_uncertainty_coverage': len(uncertainty) == TOTAL_MEMBERS and set(hard_member_ids) == set(uncertainty),
    }
    passed = all(gates.values())

    positive_width = intrinsic_vec[y]
    nonpositive_width = intrinsic_vec[~y]
    positive_quality = quality_vec[y]
    nonpositive_quality = quality_vec[~y]
    result = {
        'verdict': 'PASS_GMN_V31_INTRINSIC_WIDTH_V1' if passed else 'FAIL_GMN_V31_INTRINSIC_WIDTH_V1',
        'scientific_role': 'TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY',
        'first_valid_outcome_binding': True,
        'sole_scientific_change': 'append worst-year drift-adjusted measurement-noise-deconvolved intrinsic physical width to exact v31 23D representation',
        'quality_only_ablation_promotion_candidate': False,
        'candidate_count': N,
        'fixed_member_count': TOTAL_MEMBERS,
        'feature_dimension_parent': D,
        'feature_dimension_candidate': D + 1,
        'parent_feature_sha256': arrsha(X),
        'centroid_sha256': arrsha(centroid_matrix),
        'parent_margin_sha256': arrsha(parent),
        'intrinsic_width_sha256': arrsha(intrinsic_vec),
        'quality_only_width_sha256': arrsha(quality_vec),
        'candidate_margin_sha256': arrsha(candidate),
        'quality_only_margin_sha256': arrsha(ablation),
        'candidate_fused_order_sha256': ordersha(candidate_fused),
        'quality_only_fused_order_sha256': ordersha(ablation_fused),
        'uncertainty_gzip_sha256': sha(args.member_uncertainty_gzip),
        'hard_control': HARD,
        'parent_control': PARENT,
        'parent_reproduced_metrics': trim(parent_metrics),
        'intrinsic_width_local_only': trim(candidate_local_metrics),
        'intrinsic_width_equal_rank_fusion': trim(candidate_metrics),
        'quality_only_equal_rank_fusion_ablation': trim(ablation_metrics),
        'pass_gates': gates,
        'intrinsic_width_summary_all': {
            'min': float(intrinsic_vec.min()),
            'median': float(np.median(intrinsic_vec)),
            'max': float(intrinsic_vec.max()),
        },
        'intrinsic_width_summary_positive': {
            'min': float(positive_width.min()),
            'median': float(np.median(positive_width)),
            'max': float(positive_width.max()),
        },
        'intrinsic_width_summary_nonpositive': {
            'min': float(nonpositive_width.min()),
            'median': float(np.median(nonpositive_width)),
            'max': float(nonpositive_width.max()),
        },
        'quality_width_summary_positive': {
            'min': float(positive_quality.min()),
            'median': float(np.median(positive_quality)),
            'max': float(positive_quality.max()),
        },
        'quality_width_summary_nonpositive': {
            'min': float(nonpositive_quality.min()),
            'median': float(np.median(nonpositive_quality)),
            'max': float(nonpositive_quality.max()),
        },
        'per_family': per_family,
        'feature_search': False,
        'uncertainty_multiplier_search': False,
        'drift_model_search': False,
        'annual_combiner_search': False,
        'radiant_speed_subset_search': False,
        'variance_estimator_search': False,
        'metric_search': False,
        'k_search': False,
        'scaling_search': False,
        'reference_change': False,
        'diversity_search': False,
        'fusion_search': False,
        'quality_ablation_selection': False,
        'post_result_second_search': False,
        'blind_exclusion': [20.0, 55.0],
        'sonotaco_2013_2014_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'sonotaco_benchmark_authorized_by_this_result': bool(passed),
    }
    output = args.output / 'GMN_V31_INTRINSIC_WIDTH_V1_RESULT.json'
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'per_family'}, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

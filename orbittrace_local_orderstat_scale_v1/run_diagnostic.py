#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree
from scipy.special import betainc
from scipy.stats import kstest, ks_2samp, spearmanr

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
DIM = 4
SUPPORTS = (4, 8, 16, 32)
PAIRS = {s: (s - 1, 2 * s - 1) for s in SUPPORTS}
COARSE_D = 128
FINE_D = 1024
BUCKETS = (0, 1, 2, 3)
SYNTH_NS = (768, 6144)
SYNTH_TRIALS = 4096
SYNTH_SEED = 2026081601
KS_BONF = 0.00625
TINY = float(np.finfo(float).tiny)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event_hash_u64(eid: str) -> int:
    return int.from_bytes(hashlib.sha256((SALT + str(eid)).encode("utf-8")).digest()[:8], "big")


def selected_indices(hashes: np.ndarray, denominator: int, bucket: int) -> np.ndarray:
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def local_stats_from_neighbor_distances(other_dists: np.ndarray) -> dict[int, dict[str, np.ndarray]]:
    """other_dists[:, q-1] is q-th nearest *other* neighbor distance."""
    req(other_dists.ndim == 2 and other_dists.shape[1] >= 63, "need first 63 other-neighbor distances")
    out: dict[int, dict[str, np.ndarray]] = {}
    for s in SUPPORTS:
        j, k = PAIRS[s]
        rj = np.asarray(other_dists[:, j - 1], dtype=float)
        rk = np.asarray(other_dists[:, k - 1], dtype=float)
        req(np.all(np.isfinite(rj)) and np.all(np.isfinite(rk)), "nonfinite neighbor distance")
        req(np.all(rj > 0.0) and np.all(rk >= rj), "invalid nested neighbor radii")
        u = np.power(rj / rk, DIM)
        u = np.clip(u, 0.0, 1.0)
        p = betainc(float(j), float(k - j), u)
        req(np.all(np.isfinite(p)) and np.all((p >= 0.0) & (p <= 1.0)), "invalid Beta p-value")
        surprise = -np.log10(np.maximum(p, TINY))
        compactness = -np.log(rj)
        out[s] = {"rj": rj, "rk": rk, "u": u, "p": p, "surprise": surprise, "compactness": compactness}
    return out


def synthetic_calibration() -> dict[str, Any]:
    pvals: dict[tuple[int, int], list[float]] = {(n, s): [] for n in SYNTH_NS for s in SUPPORTS}
    max_outer: dict[int, float] = {n: 0.0 for n in SYNTH_NS}
    for n in SYNTH_NS:
        for t in range(SYNTH_TRIALS):
            rng = np.random.default_rng(np.random.SeedSequence([SYNTH_SEED, n, t]))
            pts = rng.random((n, DIM), dtype=float)
            delta = np.abs(pts[1:] - pts[0])
            delta = np.minimum(delta, 1.0 - delta)
            d = np.sqrt(np.sum(delta * delta, axis=1))
            first = np.partition(d, 62)[:63]
            first.sort()
            max_outer[n] = max(max_outer[n], float(first[-1]))
            stats = local_stats_from_neighbor_distances(first.reshape(1, -1))
            for s in SUPPORTS:
                pvals[(n, s)].append(float(stats[s]["p"][0]))

    rows = []
    all_pass = True
    for n in SYNTH_NS:
        # Euclidean r^4 volume law on a flat 4-torus is exact below injectivity radius 0.5.
        req(max_outer[n] < 0.5, f"synthetic outer neighbor exceeded torus injectivity radius for n={n}: {max_outer[n]}")
        for s in SUPPORTS:
            arr = np.asarray(pvals[(n, s)], dtype=float)
            res = kstest(arr, "uniform")
            passed = bool(float(res.pvalue) >= KS_BONF)
            all_pass = all_pass and passed
            rows.append({
                "n": n,
                "support": s,
                "j": PAIRS[s][0],
                "k": PAIRS[s][1],
                "count": len(arr),
                "ks_statistic": float(res.statistic),
                "ks_pvalue": float(res.pvalue),
                "bonferroni_pass": passed,
                "mean_p": float(np.mean(arr)),
                "median_p": float(np.median(arr)),
                "max_outer_radius_seen": float(max_outer[n]),
            })
    return {"all_eight_pass": bool(all_pass), "rows": rows}


def knn_stats(X: np.ndarray) -> dict[int, dict[str, np.ndarray]]:
    req(X.ndim == 2 and X.shape[1] == 6 and len(X) > 64, "invalid GEO6 subset")
    tree = cKDTree(X)
    d, _idx = tree.query(X, k=64, workers=1)
    d = np.asarray(d, dtype=float)
    req(d.shape == (len(X), 64), f"unexpected kNN shape {d.shape}")
    req(np.all(np.abs(d[:, 0]) <= 1e-14), "self neighbor not first")
    return local_stats_from_neighbor_distances(d[:, 1:64])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    parent = load_module(a.parent_runner, "local_orderstat_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")

    print("[local-orderstat] synthetic calibration", flush=True)
    synth = synthetic_calibration()
    print(json.dumps(synth, sort_keys=True), flush=True)

    qmod = load_module(a.quality_source, "local_orderstat_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-local-orderstat-scale-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_truth_unused, sources = support.parse_catalogue(base)
    del hidden_truth_unused
    req(sorted(scan) == list(YEARS), f"wrong GMN years {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), "normalization count changed")
        events.extend(norm)
    req(len(events) == 738682, f"pooled target-excluded count changed: {len(events)}")
    req(len({e["id"] for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    Xfull = parent.geo_matrix(events)
    ids = np.asarray([str(e["id"]) for e in events], dtype=object)
    years = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    hashes = np.asarray([event_hash_u64(str(eid)) for eid in ids], dtype=np.uint64)

    subset_data: dict[tuple[int, int], dict[str, Any]] = {}
    pooled: dict[int, dict[int, dict[str, list[np.ndarray]]]] = {
        d: {s: {"rj": [], "u": []} for s in SUPPORTS} for d in (COARSE_D, FINE_D)
    }
    subset_rows = []
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            ix = selected_indices(hashes, denominator, bucket)
            X = np.asarray(Xfull[ix], dtype=float)
            sub_ids = np.asarray(ids[ix], dtype=object)
            sub_years = years[ix]
            req(all(np.any(sub_years == y) for y in YEARS), "subset lost one year")
            print(f"[local-orderstat] d={denominator} b={bucket} n={len(X)}", flush=True)
            stats = knn_stats(X)
            for s in SUPPORTS:
                pooled[denominator][s]["rj"].append(stats[s]["rj"])
                pooled[denominator][s]["u"].append(stats[s]["u"])
            subset_data[(denominator, bucket)] = {"ids": sub_ids, "stats": stats}
            subset_rows.append({
                "denominator": denominator,
                "bucket": bucket,
                "events_total": len(X),
                "events_by_year": {str(y): int(np.sum(sub_years == y)) for y in YEARS},
                "supports": {
                    str(s): {
                        "j": PAIRS[s][0], "k": PAIRS[s][1],
                        "median_rj": float(np.median(stats[s]["rj"])),
                        "median_u": float(np.median(stats[s]["u"])),
                        "median_p": float(np.median(stats[s]["p"])),
                        "median_surprise": float(np.median(stats[s]["surprise"])),
                    } for s in SUPPORTS
                },
            })

    distribution_rows = []
    rank_rows = []
    dist_wins = 0
    rank_support_wins = 0
    surprise_support_median_rhos: list[float] = []
    raw_support_median_rhos: list[float] = []

    for s in SUPPORTS:
        r128 = np.concatenate(pooled[COARSE_D][s]["rj"])
        r1024 = np.concatenate(pooled[FINE_D][s]["rj"])
        u128 = np.concatenate(pooled[COARSE_D][s]["u"])
        u1024 = np.concatenate(pooled[FINE_D][s]["u"])
        ks_r = float(ks_2samp(r128, r1024).statistic)
        ks_u = float(ks_2samp(u128, u1024).statistic)
        dist_win = ks_u < ks_r
        dist_wins += int(dist_win)
        distribution_rows.append({
            "support": s,
            "j": PAIRS[s][0], "k": PAIRS[s][1],
            "ks_raw_inner_radius": ks_r,
            "ks_local_volume_ratio": ks_u,
            "strict_distributional_win": bool(dist_win),
            "median_rj_d128": float(np.median(r128)),
            "median_rj_d1024": float(np.median(r1024)),
            "median_u_d128": float(np.median(u128)),
            "median_u_d1024": float(np.median(u1024)),
        })

        raw_rhos = []
        surprise_rhos = []
        bucket_details = []
        for bucket in BUCKETS:
            coarse = subset_data[(COARSE_D, bucket)]
            fine = subset_data[(FINE_D, bucket)]
            coarse_ids = coarse["ids"]
            fine_ids = fine["ids"]
            lookup = {str(eid): i for i, eid in enumerate(coarse_ids)}
            coarse_pos = np.asarray([lookup[str(eid)] for eid in fine_ids], dtype=np.int64)
            req(np.array_equal(coarse_ids[coarse_pos], fine_ids), "nested event identity mapping failed")
            c_raw = coarse["stats"][s]["compactness"][coarse_pos]
            f_raw = fine["stats"][s]["compactness"]
            c_sur = coarse["stats"][s]["surprise"][coarse_pos]
            f_sur = fine["stats"][s]["surprise"]
            rr = float(spearmanr(c_raw, f_raw).statistic)
            rs = float(spearmanr(c_sur, f_sur).statistic)
            req(math.isfinite(rr) and math.isfinite(rs), "nonfinite cross-scale Spearman")
            raw_rhos.append(rr)
            surprise_rhos.append(rs)
            bucket_details.append({"bucket": bucket, "raw_compactness_rho": rr, "local_surprise_rho": rs, "surprise_strict_win": rs > rr})
        med_raw = float(np.median(np.asarray(raw_rhos)))
        med_sur = float(np.median(np.asarray(surprise_rhos)))
        rank_win = med_sur > med_raw
        rank_support_wins += int(rank_win)
        raw_support_median_rhos.append(med_raw)
        surprise_support_median_rhos.append(med_sur)
        rank_rows.append({
            "support": s,
            "median_raw_compactness_rho": med_raw,
            "median_local_surprise_rho": med_sur,
            "strict_rank_stability_win": bool(rank_win),
            "buckets": bucket_details,
        })

    overall_raw_median = float(np.median(np.asarray(raw_support_median_rhos)))
    overall_sur_median = float(np.median(np.asarray(surprise_support_median_rhos)))
    gate = {
        "all_eight_synthetic_calibration_tests_pass": bool(synth["all_eight_pass"]),
        "all_four_distributional_wins": dist_wins == 4,
        "rank_stability_wins_at_least_three_of_four": rank_support_wins >= 3,
        "overall_median_support_rho_strictly_better": overall_sur_median > overall_raw_median,
    }
    interpretation = "SUPPORTS_LOCAL_ORDERSTAT_SCALE_CALIBRATION" if all(gate.values()) else "REFUTES_LOCAL_ORDERSTAT_SCALE_CALIBRATION"
    result = {
        "schema": "ORBITTRACE_LOCAL_ORDERSTAT_SCALE_V1",
        "scientific_role": "ZERO_LABEL_STATISTICAL_FEASIBILITY_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "configuration": {
            "intrinsic_dimension": DIM,
            "supports": list(SUPPORTS),
            "pairs": {str(s): {"j": PAIRS[s][0], "k": PAIRS[s][1], "beta_a": PAIRS[s][0], "beta_b": PAIRS[s][1] - PAIRS[s][0]} for s in SUPPORTS},
            "synthetic_ns": list(SYNTH_NS),
            "synthetic_trials": SYNTH_TRIALS,
            "synthetic_seed": SYNTH_SEED,
            "synthetic_ks_bonferroni_p_floor": KS_BONF,
            "coarse_denominator": COARSE_D,
            "fine_denominator": FINE_D,
            "buckets": list(BUCKETS),
        },
        "synthetic_calibration": synth,
        "gmn_distributional_scale": distribution_rows,
        "gmn_same_event_rank_stability": rank_rows,
        "gmn_subsets": sorted(subset_rows, key=lambda r: (r["denominator"], r["bucket"])),
        "summary": {
            "distributional_win_count": dist_wins,
            "rank_stability_win_count": rank_support_wins,
            "overall_median_raw_compactness_rho": overall_raw_median,
            "overall_median_local_surprise_rho": overall_sur_median,
            "gate": gate,
        },
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "shower_truth_used": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    out = a.output / "LOCAL_ORDERSTAT_SCALE_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"interpretation": interpretation, "summary": result["summary"], "synthetic": synth, "distributional": distribution_rows, "rank": rank_rows}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

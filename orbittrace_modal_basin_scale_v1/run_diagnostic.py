#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from sklearn.cluster import MeanShift

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
COARSE_D = 128
FINE_D = 1024
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4
H_SOL = 2.0 * math.sin(math.radians(5.0) / 2.0)
H_RAD = 2.0 * math.sin(math.radians(4.0) / 2.0)
H_LOGV = math.log(1.1)


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
    return int.from_bytes(hashlib.sha256((SALT + str(eid)).encode()).digest()[:8], "big")


def selected_indices(hashes: np.ndarray, denominator: int, bucket: int) -> np.ndarray:
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def member_hash(members: frozenset[str]) -> str:
    return hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:20]


def physical_embedding(events: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([float(e["sol"]) for e in events], dtype=float))
    lon = np.radians(np.asarray([float(e["lon"]) for e in events], dtype=float))
    lat = np.radians(np.asarray([float(e["lat"]) for e in events], dtype=float))
    vg = np.asarray([float(e["vg"]) for e in events], dtype=float)
    req(np.all(np.isfinite(vg)) and np.all(vg > 0.0), "invalid speed")
    clat = np.cos(lat)
    Z = np.column_stack([
        np.cos(sol) / H_SOL,
        np.sin(sol) / H_SOL,
        clat * np.cos(lon) / H_RAD,
        clat * np.sin(lon) / H_RAD,
        np.sin(lat) / H_RAD,
        np.log(vg) / H_LOGV,
    ]).astype(float)
    req(Z.shape == (len(events), 6) and np.all(np.isfinite(Z)), "invalid modal embedding")
    return Z


def modal_candidates(events: list[dict[str, Any]]) -> tuple[list[frozenset[str]], dict[str, Any]]:
    # Frozen input-order rule: exact event ID ascending.
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    Z = physical_embedding(ordered)
    model = MeanShift(
        bandwidth=1.0,
        seeds=None,
        bin_seeding=False,
        min_bin_freq=1,
        cluster_all=True,
        max_iter=300,
        n_jobs=1,
    ).fit(Z)
    labels = np.asarray(model.labels_, dtype=np.int64)
    req(labels.shape == (len(ids),), "wrong MeanShift label shape")
    unique = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    all_basins: list[tuple[int, frozenset[str]]] = []
    eligible: list[frozenset[str]] = []
    rows = []
    for lab in unique:
        idx = np.flatnonzero(labels == lab)
        members = frozenset(ids[int(i)] for i in idx)
        all_basins.append((lab, members))
        if len(members) >= MIN_SUPPORT:
            eligible.append(members)
            rows.append({
                "basin_label": lab,
                "family_hash": member_hash(members),
                "member_count": len(members),
            })
    req(sum(len(m) for _lab, m in all_basins) == len(ids), "MeanShift basins do not partition sample")
    req(len(model.cluster_centers_) == len(unique), "center/label count mismatch")
    counts = sorted((len(m) for _lab, m in all_basins), reverse=True)
    return eligible, {
        "all_basin_count": len(all_basins),
        "eligible_basin_count": len(eligible),
        "singleton_or_small_basin_count": int(sum(len(m) < MIN_SUPPORT for _lab, m in all_basins)),
        "largest_basin_count": int(counts[0]) if counts else 0,
        "largest_basin_fraction": float(counts[0] / len(ids)) if counts else 0.0,
        "median_all_basin_size": float(np.median(np.asarray(counts, dtype=float))) if counts else 0.0,
        "center_count": int(len(model.cluster_centers_)),
        "candidate_rows": sorted(rows, key=lambda r: (-r["member_count"], r["family_hash"])),
    }


def recurrent_candidates(parent_runner: Any, X: np.ndarray, years: np.ndarray, event_ids: list[str]) -> tuple[list[frozenset[str]], dict[str, Any]]:
    model = hdbscan.HDBSCAN(
        min_cluster_size=10,
        min_samples=10,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    recurrent, _annual = parent_runner.recurrent_stability(tree, years)
    labels = np.asarray(parent_runner.eom_labels(tree, recurrent), dtype=np.int64)
    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    candidates = []
    rows = []
    for lab in positive:
        idx = np.flatnonzero(labels == lab)
        members = frozenset(event_ids[int(i)] for i in idx)
        req(len(members) >= 10, "recurrent comparator sub-10 membership")
        candidates.append(members)
        rows.append({"family_hash": member_hash(members), "member_count": len(members)})
    counts = sorted((len(c) for c in candidates), reverse=True)
    return candidates, {
        "candidate_count": len(candidates),
        "largest_candidate_count": int(counts[0]) if counts else 0,
        "largest_candidate_fraction": float(counts[0] / len(event_ids)) if counts else 0.0,
        "candidate_rows": sorted(rows, key=lambda r: (-r["member_count"], r["family_hash"])),
    }


def cross_scale_metrics(coarse: list[frozenset[str]], fine: list[frozenset[str]], fine_universe: frozenset[str]) -> dict[str, Any]:
    restricted: list[frozenset[str]] = []
    for c in coarse:
        r = frozenset(c.intersection(fine_universe))
        if len(r) >= MIN_SUPPORT:
            restricted.append(r)
    scores = []
    exact = 0
    for f in fine:
        best = 0.0
        exact_here = False
        for c in restricted:
            inter = len(f.intersection(c))
            if inter == 0:
                continue
            j = float(inter / len(f.union(c)))
            if j > best:
                best = j
            exact_here = exact_here or (f == c)
        scores.append(best)
        exact += int(exact_here)
    arr = np.asarray(scores, dtype=float)
    return {
        "fine_candidate_count": len(fine),
        "restricted_coarse_candidate_count": len(restricted),
        "candidate_unweighted_mean_best_jaccard": float(np.mean(arr)) if len(arr) else 0.0,
        "median_best_jaccard": float(np.median(arr)) if len(arr) else 0.0,
        "exact_restricted_match_fraction": float(exact / len(fine)) if fine else 0.0,
        "best_jaccards": [float(x) for x in arr],
    }


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
    parent_runner = load_module(a.parent_runner, "modal_basin_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "parent constants changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent support changed")

    qmod = load_module(a.quality_source, "modal_basin_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-modal-basin-scale-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_truth_unused, sources = support.parse_catalogue(base)
    del hidden_truth_unused
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), f"normalization count changed {year}")
        events.extend(norm)
    req(len(events) == 738682, f"pooled target-excluded event count changed: {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    Xfull = parent_runner.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    fits: dict[tuple[int, int], dict[str, Any]] = {}
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            ix = selected_indices(hashes, denominator, bucket)
            sub_events = [events[int(i)] for i in ix]
            X = np.asarray(Xfull[ix], dtype=float)
            years = np.asarray(years_full[ix], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ix]
            req(all(np.any(years == y) for y in YEARS), "subset lost a year")
            print(f"[modal-basin] d={denominator} b={bucket} n={len(ids)}", flush=True)
            modal, modal_summary = modal_candidates(sub_events)
            recurrent, recurrent_summary = recurrent_candidates(parent_runner, X, years, ids)
            fits[(denominator, bucket)] = {
                "ids": frozenset(ids),
                "modal": modal,
                "recurrent": recurrent,
                "row": {
                    "denominator": denominator,
                    "bucket": bucket,
                    "events_total": len(ids),
                    "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
                    "modal": modal_summary,
                    "recurrent_eom": recurrent_summary,
                },
            }
            print(json.dumps(fits[(denominator, bucket)]["row"], sort_keys=True), flush=True)

    pair_rows = []
    modal_means = []
    recurrent_means = []
    modal_all_scores = []
    recurrent_all_scores = []
    bucket_wins = 0
    noncollapse_all = True
    nonempty_all = True
    for bucket in BUCKETS:
        coarse = fits[(COARSE_D, bucket)]
        fine = fits[(FINE_D, bucket)]
        req(fine["ids"].issubset(coarse["ids"]), f"nested subset failed bucket {bucket}")
        mm = cross_scale_metrics(coarse["modal"], fine["modal"], fine["ids"])
        rr = cross_scale_metrics(coarse["recurrent"], fine["recurrent"], fine["ids"])
        modal_mean = float(mm["candidate_unweighted_mean_best_jaccard"])
        recurrent_mean = float(rr["candidate_unweighted_mean_best_jaccard"])
        modal_means.append(modal_mean)
        recurrent_means.append(recurrent_mean)
        modal_all_scores.extend(mm["best_jaccards"])
        recurrent_all_scores.extend(rr["best_jaccards"])
        win = modal_mean > recurrent_mean
        bucket_wins += int(win)
        noncollapse = int(mm["fine_candidate_count"]) >= int(rr["fine_candidate_count"])
        noncollapse_all = noncollapse_all and noncollapse
        nonempty = len(coarse["modal"]) > 0 and len(fine["modal"]) > 0
        nonempty_all = nonempty_all and nonempty
        pair_rows.append({
            "bucket": bucket,
            "modal": mm,
            "recurrent_eom": rr,
            "modal_strict_win": bool(win),
            "fine_candidate_noncollapse": bool(noncollapse),
        })

    modal_pool = float(np.mean(np.asarray(modal_all_scores, dtype=float))) if modal_all_scores else 0.0
    recurrent_pool = float(np.mean(np.asarray(recurrent_all_scores, dtype=float))) if recurrent_all_scores else 0.0
    modal_med_bucket = float(np.median(np.asarray(modal_means, dtype=float)))
    recurrent_med_bucket = float(np.median(np.asarray(recurrent_means, dtype=float)))
    gate = {
        "modal_nonempty_all_eight": bool(nonempty_all),
        "fine_candidate_noncollapse_all_four": bool(noncollapse_all),
        "pooled_candidate_mean_jaccard_strictly_better": modal_pool > recurrent_pool,
        "median_bucket_candidate_mean_jaccard_strictly_better": modal_med_bucket > recurrent_med_bucket,
        "bucket_wins_at_least_three_of_four": bucket_wins >= 3,
    }
    interpretation = "SUPPORTS_PHYSICAL_MODAL_BASIN_CROSS_SCALE_COHERENCE" if all(gate.values()) else "REFUTES_PHYSICAL_MODAL_BASIN_CROSS_SCALE_COHERENCE"
    result = {
        "schema": "ORBITTRACE_MODAL_BASIN_SCALE_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "configuration": {
            "solar_halfwidth_deg": 5.0,
            "radiant_scale_deg": 4.0,
            "speed_multiplicative_scale": 1.1,
            "mean_shift_bandwidth": 1.0,
            "bin_seeding": False,
            "cluster_all": True,
            "max_iter": 300,
            "min_candidate_support": MIN_SUPPORT,
            "coarse_denominator": COARSE_D,
            "fine_denominator": FINE_D,
            "buckets": list(BUCKETS),
        },
        "fits": [fits[(d, b)]["row"] for d in (COARSE_D, FINE_D) for b in BUCKETS],
        "nested_pairs": pair_rows,
        "summary": {
            "modal_pooled_candidate_unweighted_mean_best_jaccard": modal_pool,
            "recurrent_eom_pooled_candidate_unweighted_mean_best_jaccard": recurrent_pool,
            "modal_median_bucket_candidate_mean_best_jaccard": modal_med_bucket,
            "recurrent_eom_median_bucket_candidate_mean_best_jaccard": recurrent_med_bucket,
            "modal_bucket_wins": bucket_wins,
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
    out = a.output / "MODAL_BASIN_SCALE_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"interpretation": interpretation, "summary": result["summary"], "pairs": pair_rows}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
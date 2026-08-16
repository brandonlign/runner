#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import warnings
from pathlib import Path
from typing import Any, Iterable

import hdbscan
import numpy as np
from persistable import Persistable
from persistable.persistable_interactive import (
    compute_defaults,
    X_START_FIRST_LINE, Y_START_FIRST_LINE, X_END_FIRST_LINE, Y_END_FIRST_LINE,
    X_START_SECOND_LINE, Y_START_SECOND_LINE, X_END_SECOND_LINE, Y_END_SECOND_LINE,
    GRANULARITY_PV,
)

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PERSISTABLE_COMMIT = "7eb75b2e8d2fe5a18e49248aa7d1c97f829415be"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
COARSE_D = 128
FINE_D = 1024
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4
MAX_GAP = 15
EPS = 1e-15


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


def default_slices(p: Persistable):
    extent = np.asarray(p._find_end(), dtype=float)
    req(extent.shape == (2,) and np.all(np.isfinite(extent)) and np.all(extent > 0), f"invalid find_end {extent}")
    defaults, _bounds = compute_defaults(extent, p._default_granularity())
    s1 = np.asarray([defaults[X_START_FIRST_LINE], defaults[Y_START_FIRST_LINE]], dtype=float)
    e1 = np.asarray([defaults[X_END_FIRST_LINE], defaults[Y_END_FIRST_LINE]], dtype=float)
    s2 = np.asarray([defaults[X_START_SECOND_LINE], defaults[Y_START_SECOND_LINE]], dtype=float)
    e2 = np.asarray([defaults[X_END_SECOND_LINE], defaults[Y_END_SECOND_LINE]], dtype=float)
    npar = int(defaults[GRANULARITY_PV])
    req(npar >= 2, f"invalid default vineyard granularity {npar}")
    for x in (s1, e1, s2, e2):
        req(x.shape == (2,) and np.all(np.isfinite(x)), "invalid default slice")
    return extent, (s1, e1), (s2, e2), npar


def automatic_persistable_labels(X: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        p = Persistable(X, n_neighbors="auto", n_jobs=1)
        extent, slice1, slice2, npar = default_slices(p)
        vineyard = p._linear_vineyard(slice1, slice2, npar, reduced=False, n_jobs=1)
        vines = vineyard._vineyard_to_vines()
        warning_messages = [str(w.message) for w in ws]
    req(not any("enough neighbors" in s.lower() for s in warning_messages), f"insufficient-neighbor warning: {warning_messages}")
    req(len(vines) >= 3, f"too few prominence vines: {len(vines)}")
    prom = np.column_stack([np.asarray(v[1], dtype=float) for v in vines])
    req(prom.shape[0] == npar and np.all(np.isfinite(prom)) and np.all(prom >= 0), "invalid prominence matrix")
    last_gap = min(MAX_GAP, prom.shape[1] - 1)
    req(last_gap >= 2, "no nontrivial prominence gap available")
    denom = np.maximum(prom[:, 0], EPS)
    curves: dict[int, np.ndarray] = {}
    score_by_gap: dict[int, float] = {}
    for gap in range(2, last_gap + 1):
        curve = np.maximum(prom[:, gap - 1] - prom[:, gap], 0.0) / denom
        req(np.all(np.isfinite(curve)), f"invalid gap curve {gap}")
        curves[gap] = curve
        score_by_gap[gap] = float(np.mean(curve))
    best_score = max(score_by_gap.values())
    gap = min(g for g, s in score_by_gap.items() if abs(s - best_score) <= 1e-15)
    curve = curves[gap]
    t = int(np.flatnonzero(np.abs(curve - np.max(curve)) <= 1e-15)[0])
    params = list(vineyard._parameters)
    req(len(params) == npar, "vineyard parameter count mismatch")
    start, end = params[t]
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    req(start.shape == (2,) and end.shape == (2,) and np.all(np.isfinite(start)) and np.all(np.isfinite(end)), "invalid selected slice")
    labels = np.asarray(p.cluster(n_clusters=int(gap), start=start, end=end, flattening_mode="conservative", keep_low_persistence_clusters=False), dtype=np.int64)
    req(labels.shape == (len(X),), "wrong Persistable label shape")
    return labels, {
        "find_end": extent.tolist(),
        "vineyard_parameters": npar,
        "prominence_vines": int(prom.shape[1]),
        "selected_gap": int(gap),
        "selected_gap_mean_normalized_separation": float(best_score),
        "selected_vineyard_index": int(t),
        "selected_gap_at_index": float(curve[t]),
        "selected_slice": [start.tolist(), end.tolist()],
        "warning_messages": warning_messages,
    }


def persistable_candidates(X: np.ndarray, ids: list[str]) -> tuple[list[frozenset[str]], dict[str, Any]]:
    labels, selector = automatic_persistable_labels(X)
    candidates: list[frozenset[str]] = []
    rows = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        ix = np.flatnonzero(labels == lab)
        members = frozenset(ids[int(i)] for i in ix)
        if len(members) >= MIN_SUPPORT:
            candidates.append(members)
            rows.append({"family_hash": member_hash(members), "member_count": len(members), "label": lab})
    counts = sorted((len(c) for c in candidates), reverse=True)
    return candidates, {
        "eligible_candidate_count": len(candidates),
        "returned_nonnoise_cluster_count": int(len([x for x in np.unique(labels) if int(x) >= 0])),
        "largest_candidate_count": int(counts[0]) if counts else 0,
        "largest_candidate_fraction": float(counts[0] / len(ids)) if counts else 0.0,
        "noise_fraction": float(np.mean(labels < 0)),
        "selector": selector,
        "candidate_rows": sorted(rows, key=lambda r: (-r["member_count"], r["family_hash"])),
    }


def recurrent_candidates(parent: Any, X: np.ndarray, years: np.ndarray, ids: list[str]) -> tuple[list[frozenset[str]], dict[str, Any]]:
    model = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=10, metric="euclidean", cluster_selection_method="eom", cluster_selection_epsilon=0.0, allow_single_cluster=False, prediction_data=False).fit(X)
    tree = model.condensed_tree_._raw_tree
    recurrent, _annual = parent.recurrent_stability(tree, years)
    labels = np.asarray(parent.eom_labels(tree, recurrent), dtype=np.int64)
    candidates = []
    rows = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        ix = np.flatnonzero(labels == lab)
        members = frozenset(ids[int(i)] for i in ix)
        req(len(members) >= 10, "recurrent comparator sub-10 membership")
        candidates.append(members)
        rows.append({"family_hash": member_hash(members), "member_count": len(members)})
    counts = sorted((len(c) for c in candidates), reverse=True)
    return candidates, {"candidate_count": len(candidates), "largest_candidate_count": int(counts[0]) if counts else 0, "candidate_rows": sorted(rows, key=lambda r: (-r["member_count"], r["family_hash"]))}


def cross_scale_metrics(coarse: list[frozenset[str]], fine: list[frozenset[str]], fine_universe: frozenset[str]) -> dict[str, Any]:
    restricted = []
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
            if inter:
                best = max(best, float(inter / len(f.union(c))))
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
    ap.add_argument("--synthetic-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    synthetic = json.loads(a.synthetic_result_json.read_text())
    req(synthetic.get("verdict") == "PASS_PERSISTABLE_AUTO_SELECTOR_SYNTHETIC_FEASIBILITY", "synthetic activation gate not satisfied")
    req(synthetic.get("upstream_persistable_commit") == PERSISTABLE_COMMIT, "synthetic upstream identity changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    parent = load_module(a.parent_runner, "persistable_crossscale_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")
    req(int(parent.MIN_CLUSTER_SIZE) == 10 and int(parent.MIN_SAMPLES) == 10, "parent support changed")

    qmod = load_module(a.quality_source, "persistable_crossscale_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-persistable-crossscale-v1-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_truth_unused, sources = support.parse_catalogue(base)
    del hidden_truth_unused
    req(sorted(scan) == list(YEARS), f"wrong GMN years {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), f"normalization count changed {year}")
        events.extend(norm)
    req(len(events) == 738682, f"pooled target-excluded event count changed {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    Xfull = parent.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    fits: dict[tuple[int, int], dict[str, Any]] = {}
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            ix = selected_indices(hashes, denominator, bucket)
            X = np.asarray(Xfull[ix], dtype=float)
            years = np.asarray(years_full[ix], dtype=np.int64)
            ids = [ids_full[int(i)] for i in ix]
            req(all(np.any(years == y) for y in YEARS), "subset lost a year")
            print(f"[persistable] d={denominator} b={bucket} n={len(ids)}", flush=True)
            pc, ps = persistable_candidates(X, ids)
            rc, rs = recurrent_candidates(parent, X, years, ids)
            fits[(denominator, bucket)] = {"ids": frozenset(ids), "persistable": pc, "recurrent": rc, "row": {"denominator": denominator, "bucket": bucket, "events_total": len(ids), "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS}, "persistable": ps, "recurrent_eom": rs}}
            print(json.dumps(fits[(denominator, bucket)]["row"], sort_keys=True), flush=True)

    pairs = []
    pm, rm, pa, ra = [], [], [], []
    wins = 0
    nonempty_all = True
    noncollapse_all = True
    for bucket in BUCKETS:
        coarse = fits[(COARSE_D, bucket)]
        fine = fits[(FINE_D, bucket)]
        req(fine["ids"].issubset(coarse["ids"]), f"nested subset failed bucket {bucket}")
        pp = cross_scale_metrics(coarse["persistable"], fine["persistable"], fine["ids"])
        rr = cross_scale_metrics(coarse["recurrent"], fine["recurrent"], fine["ids"])
        pmean = float(pp["candidate_unweighted_mean_best_jaccard"])
        rmean = float(rr["candidate_unweighted_mean_best_jaccard"])
        pm.append(pmean); rm.append(rmean); pa.extend(pp["best_jaccards"]); ra.extend(rr["best_jaccards"])
        win = pmean > rmean
        wins += int(win)
        nonempty = len(coarse["persistable"]) > 0 and len(fine["persistable"]) > 0
        nonempty_all = nonempty_all and nonempty
        noncollapse = int(pp["fine_candidate_count"]) >= int(rr["fine_candidate_count"])
        noncollapse_all = noncollapse_all and noncollapse
        pairs.append({"bucket": bucket, "persistable": pp, "recurrent_eom": rr, "persistable_strict_win": bool(win), "fine_candidate_noncollapse": bool(noncollapse)})

    ppool = float(np.mean(np.asarray(pa, dtype=float))) if pa else 0.0
    rpool = float(np.mean(np.asarray(ra, dtype=float))) if ra else 0.0
    pmed = float(np.median(np.asarray(pm, dtype=float)))
    rmed = float(np.median(np.asarray(rm, dtype=float)))
    gate = {
        "persistable_nonempty_all_eight": bool(nonempty_all),
        "fine_candidate_noncollapse_all_four": bool(noncollapse_all),
        "pooled_candidate_mean_jaccard_strictly_better": ppool > rpool,
        "median_bucket_candidate_mean_jaccard_strictly_better": pmed > rmed,
        "bucket_wins_at_least_three_of_four": wins >= 3,
    }
    interpretation = "SUPPORTS_PERSISTABLE_AUTO_CROSS_SCALE_COHERENCE" if all(gate.values()) else "REFUTES_PERSISTABLE_AUTO_CROSS_SCALE_COHERENCE"
    result = {
        "schema": "ORBITTRACE_PERSISTABLE_CROSSSCALE_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "upstream_persistable_commit": PERSISTABLE_COMMIT,
        "fits": [fits[(d,b)]["row"] for d in (COARSE_D,FINE_D) for b in BUCKETS],
        "nested_pairs": pairs,
        "summary": {"persistable_pooled_candidate_unweighted_mean_best_jaccard": ppool, "recurrent_eom_pooled_candidate_unweighted_mean_best_jaccard": rpool, "persistable_median_bucket_candidate_mean_best_jaccard": pmed, "recurrent_eom_median_bucket_candidate_mean_best_jaccard": rmed, "persistable_bucket_wins": wins, "gate": gate},
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
    (a.output / "PERSISTABLE_CROSSSCALE_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"interpretation": interpretation, "summary": result["summary"], "pairs": pairs}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Frozen OrbitTrace GMN 2022+2023 dynamic-programming track-before-detect v1."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
BIN_WIDTH = 2.0
RAD_SCALE_DEG = 3.0
SPEED_SCALE_LOG = math.log(1.08)
PSEUDOCOUNT = 0.5
PREDECESSOR_K = 8
GAPS = (1, 2)
MIN_PATH_STATES = 3
MAX_SEEDS = 5000
MEMBER_RESIDUAL_MAX = 1.0
MIN_MEMBERS = 4
DEDUP_JACCARD = 0.50
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"

CONTROL = {
    "recovered_at_25": 22,
    "recovered_at_50": 40,
    "recovered_at_100": 75,
    "recovered_at_500": 159,
    "top100_dominant_precision": 0.7645689180574315,
    "mrr": 0.019037817654898162,
    "qualified_matches": 256,
}


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def event_field(row: dict[str, Any], names: Iterable[str]) -> float:
    for name in names:
        if name in row and row[name] is not None:
            value = float(row[name])
            if math.isfinite(value):
                return value
    raise RuntimeError(f"event missing required field aliases {tuple(names)}")


def event_id(row: dict[str, Any]) -> str:
    for name in ("id", "event_id", "eventId"):
        if name in row:
            return str(row[name])
    raise RuntimeError("event row lacks ID")


def normalize_event(row: dict[str, Any]) -> dict[str, Any]:
    eid = event_id(row)
    sol = event_field(row, ("sol", "solar_longitude", "solar_lon", "sol_lon")) % 360.0
    lon = event_field(row, ("sun_lon", "sun_centered_longitude", "sun_centered_lon", "lam_sce"))
    lat = event_field(row, ("ecl_lat", "ecliptic_latitude", "lat_sce", "beta"))
    vg = event_field(row, ("vg", "v_g", "geocentric_speed", "velocity"))
    req(vg > 0.0, f"nonpositive speed for {eid}")
    req(not (BLIND[0] <= sol <= BLIND[1]), f"protected event reached DP-TBD normalizer: {eid}")
    coord = sol + 360.0 if sol < BLIND[0] else sol
    year = int(eid[:4]) if len(eid) >= 4 and eid[:4].isdigit() else -1
    req(year in YEARS, f"unexpected event year for {eid}")
    bidx = int(math.floor((coord - BLIND[1]) / BIN_WIDTH))
    return {"id": eid, "year": year, "sol": sol, "coord": coord, "lon": lon, "lat": lat, "vg": vg, "bin": bidx}


def unit(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lon = np.radians(lon_deg)
    lat = np.radians(lat_deg)
    return np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))


def exact_d2(u1: np.ndarray, logv1: np.ndarray, u2: np.ndarray, logv2: np.ndarray) -> np.ndarray:
    dots = np.sum(u1 * u2, axis=1)
    theta = np.degrees(np.arccos(np.clip(dots, -1.0, 1.0))) / RAD_SCALE_DEG
    speed = np.abs(logv1 - logv2) / SPEED_SCALE_LOG
    return theta * theta + speed * speed


def transform(u: np.ndarray, logv: np.ndarray) -> np.ndarray:
    # Chord embedding is used only as an exact-safe search index; scientific distances are recomputed above.
    chord = 2.0 * math.sin(math.radians(RAD_SCALE_DEG) / 2.0)
    return np.column_stack((u / chord, logv / SPEED_SCALE_LOG))


def exact_radius_counts(
    tree: cKDTree,
    query_x: np.ndarray,
    query_u: np.ndarray,
    query_logv: np.ndarray,
    ref_u: np.ndarray,
    ref_logv: np.ndarray,
    subtract_self: bool,
    batch: int = 2000,
) -> np.ndarray:
    """Count exact d<=1 neighbors using the chord tree only as a no-false-negative prefilter."""
    out = np.zeros(len(query_x), dtype=np.int32)
    for start in range(0, len(query_x), batch):
        stop = min(start + batch, len(query_x))
        lists = tree.query_ball_point(query_x[start:stop], r=1.0 + 1e-12)
        lens = np.fromiter((len(x) for x in lists), dtype=np.int64, count=stop-start)
        if int(lens.sum()) == 0:
            continue
        flat = np.concatenate([np.asarray(x, dtype=np.int64) for x in lists])
        qlocal = np.repeat(np.arange(stop-start, dtype=np.int64), lens)
        qglobal = qlocal + start
        d2 = exact_d2(query_u[qglobal], query_logv[qglobal], ref_u[flat], ref_logv[flat])
        good = d2 <= 1.0 + 1e-12
        cnt = np.bincount(qlocal[good], minlength=stop-start).astype(np.int32)
        if subtract_self:
            cnt -= 1
            req(bool(np.all(cnt >= 0)), "self-subtracted neighbor count became negative")
        out[start:stop] = cnt
    return out


def exact_knn(
    tree: cKDTree,
    ref_indices: np.ndarray,
    query_indices: np.ndarray,
    X: np.ndarray,
    U: np.ndarray,
    logv: np.ndarray,
    k: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Exact top-k physical neighbors with adaptive chord candidate expansion and a proof-of-coverage check."""
    nref = len(ref_indices)
    kk = min(max(k * 2, 16), nref)
    qx = X[query_indices]
    while True:
        chord_d, local = tree.query(qx, k=kk)
        if kk == 1:
            chord_d = chord_d[:, None]; local = local[:, None]
        refcand = ref_indices[np.asarray(local, dtype=np.int64)]
        flat_q = np.repeat(query_indices, kk)
        flat_r = refcand.reshape(-1)
        d2 = exact_d2(U[flat_q], logv[flat_q], U[flat_r], logv[flat_r]).reshape(len(query_indices), kk)
        order = np.argsort(d2, axis=1, kind="stable")[:, :k]
        top_idx = np.take_along_axis(refcand, order, axis=1)
        top_d2 = np.take_along_axis(d2, order, axis=1)
        kth_exact = top_d2[:, -1]
        last_chord = np.asarray(chord_d)[:, -1]
        safe = last_chord + 1e-12 >= np.sqrt(kth_exact)
        if bool(np.all(safe)) or kk == nref:
            req(bool(np.all(safe)) or kk == nref, "exact kNN coverage failed")
            return top_idx, top_d2
        kk2 = min(nref, kk * 2)
        req(kk2 > kk, "unable to expand exact kNN candidate set")
        kk = kk2


def fit_path(path: np.ndarray, coords: np.ndarray, U: np.ndarray, logv: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    lam = coords[path]
    center = float(np.mean(lam))
    x = lam - center
    A = np.column_stack((np.ones(len(path)), x))
    cu = np.column_stack([np.linalg.lstsq(A, U[path, j], rcond=None)[0] for j in range(3)])
    cl = np.linalg.lstsq(A, logv[path], rcond=None)[0]
    return cu, cl, center


def predict(cu: np.ndarray, cl: np.ndarray, center: float, lam: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(lam, dtype=float) - center
    A = np.column_stack((np.ones(len(x)), x))
    pu = A @ cu
    norms = np.linalg.norm(pu, axis=1)
    req(bool(np.all(norms > 0)), "zero predicted radiant vector")
    pu /= norms[:, None]
    pl = A @ cl
    return pu, pl


def jaccard_size(a: set[str], b: set[str], intersection: int | None = None) -> float:
    inter = len(a & b) if intersection is None else int(intersection)
    return float(inter / (len(a) + len(b) - inter)) if inter else 0.0


def eligible_labels(hidden: dict[str, str]) -> dict[str, int]:
    count = Counter(label for eid, label in hidden.items() if str(eid)[:4].isdigit() and int(str(eid)[:4]) in YEARS and label != "SPORADIC")
    return {label: n for label, n in count.items() if n >= 4}


def family_truth(f: dict[str, Any], hidden: dict[str, str], eligible: dict[str, int]) -> dict[str, Any]:
    ids = [str(x) for x in f["event_ids"]]
    counts = Counter(hidden.get(eid, "SPORADIC") for eid in ids)
    rows = []
    for label, total in eligible.items():
        overlap = int(counts.get(label, 0))
        if overlap < 1:
            continue
        precision = overlap / max(len(ids), 1)
        recall = overlap / total
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append((f1, precision, overlap, label, recall))
    non = counts.copy(); non.pop("SPORADIC", None)
    dominant = max(non.values(), default=0) / max(len(ids), 1)
    if not rows:
        return {"positive": False, "best_label": None, "dominant_precision": float(dominant)}
    f1, precision, overlap, label, recall = max(rows, key=lambda x: (x[0], x[1], x[2], x[3]))
    return {
        "positive": bool(overlap >= 4 and precision >= 0.50),
        "best_label": label,
        "f1": float(f1),
        "precision": float(precision),
        "recall": float(recall),
        "overlap": int(overlap),
        "dominant_precision": float(dominant),
    }


def metrics(fams: list[dict[str, Any]], hidden: dict[str, str]) -> dict[str, Any]:
    eligible = eligible_labels(hidden)
    truths = {f["family_id"]: family_truth(f, hidden, eligible) for f in fams}
    first: dict[str, int | None] = {label: None for label in eligible}
    counts: Counter[str] = Counter()
    top_prec = []
    for rank, f in enumerate(fams, 1):
        t = truths[f["family_id"]]
        if rank <= 100:
            top_prec.append(float(t["dominant_precision"]))
        if t["positive"] and t["best_label"] in eligible:
            label = str(t["best_label"])
            if rank <= 500:
                counts[label] += 1
            if first[label] is None:
                first[label] = rank
    represented = [lab for lab, rank in first.items() if rank is not None]
    frag = [counts[lab] for lab in represented if first[lab] is not None and first[lab] <= 500]
    return {
        "eligible_labels": len(eligible),
        "qualified_matches": len(represented),
        "recovered_at_25": sum(rank is not None and rank <= 25 for rank in first.values()),
        "recovered_at_50": sum(rank is not None and rank <= 50 for rank in first.values()),
        "recovered_at_100": sum(rank is not None and rank <= 100 for rank in first.values()),
        "recovered_at_500": sum(rank is not None and rank <= 500 for rank in first.values()),
        "top100_dominant_precision": float(np.mean(top_prec)) if top_prec else 0.0,
        "mrr": float(np.mean([1.0/rank for rank in first.values() if rank is not None])) if represented else 0.0,
        "fragmentation_median_top500": float(np.median(frag)) if frag else 0.0,
        "mean_qualified_candidates_per_recovered_label_top500": float(np.mean(frag)) if frag else 0.0,
        "first_rank_by_label": first,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.quality_source) == QUALITY_SHA, "#839 utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen runtime support artifact changed")
    qmod = load_module(a.quality_source, "dptbd_frozen_839_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-gmn-dp-track-before-detect-v1"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"wrong GMN year universe: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source panel changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        rows = list(scan[year])
        events.extend(normalize_event(row) for row in rows)
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected event survived parser")
    req(all(e["year"] in YEARS for e in events), "wrong-year event survived parser")
    req(all(str(eid)[:4].isdigit() and int(str(eid)[:4]) in YEARS for eid in hidden), "wrong-year label reached runtime")

    ids = np.asarray([e["id"] for e in events], dtype=object)
    coords = np.asarray([e["coord"] for e in events], dtype=float)
    bins = np.asarray([e["bin"] for e in events], dtype=np.int32)
    U = unit(np.asarray([e["lon"] for e in events], float), np.asarray([e["lat"] for e in events], float))
    logv = np.log(np.asarray([e["vg"] for e in events], float))
    X = transform(U, logv)
    n = len(events)
    req(n > 0 and X.shape == (n, 4) and np.isfinite(X).all(), "invalid event state matrix")

    by_bin: dict[int, np.ndarray] = {}
    bin_trees: dict[int, cKDTree] = {}
    for b in sorted(set(bins.tolist())):
        idx = np.flatnonzero(bins == b)
        by_bin[int(b)] = idx
        bin_trees[int(b)] = cKDTree(X[idx])

    global_tree = cKDTree(X)
    n_all = exact_radius_counts(global_tree, X, U, logv, U, logv, subtract_self=True)
    n_bin = np.zeros(n, dtype=np.int32)
    for b, idx in by_bin.items():
        local = exact_radius_counts(bin_trees[b], X[idx], U[idx], logv[idx], U[idx], logv[idx], subtract_self=True)
        n_bin[idx] = local
    frac = np.zeros(n, dtype=float)
    for b, idx in by_bin.items():
        frac[idx] = len(idx) / float(n)
    mu = frac * n_all.astype(float)
    emission = np.log((n_bin.astype(float) + PSEUDOCOUNT) / (mu + PSEUDOCOUNT))
    req(np.isfinite(emission).all(), "nonfinite emission evidence")

    # Detection is fully label-blind through candidate-order freeze.
    prelabel = {
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DP_TBD_PRELABEL",
        "event_count": n,
        "year_counts": {str(y): int(sum(e["year"] == y for e in events)) for y in YEARS},
        "bin_count": len(by_bin),
        "emission_min": float(np.min(emission)),
        "emission_median": float(np.median(emission)),
        "emission_max": float(np.max(emission)),
        "truth_used_in_detection": False,
        "hdbscan_candidates_used": False,
        "parameter_search": False,
        "blind_exclusion": list(BLIND),
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (a.output / "DP_TBD_V1_PRELABEL.json").write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")

    V = emission.copy()
    pred = np.full(n, -1, dtype=np.int64)
    plen = np.ones(n, dtype=np.int32)
    sorted_bins = sorted(by_bin)
    for b in sorted_bins:
        dest = by_bin[b]
        best_gain = np.zeros(len(dest), dtype=float)
        best_pred = np.full(len(dest), -1, dtype=np.int64)
        best_pred_len = np.zeros(len(dest), dtype=np.int32)
        for gap in GAPS:
            pb = b - gap
            if pb not in by_bin:
                continue
            ref = by_bin[pb]
            if len(ref) == 0:
                continue
            kk = min(PREDECESSOR_K, len(ref))
            nearest, d2 = exact_knn(bin_trees[pb], ref, dest, X, U, logv, kk)
            gains = V[nearest] - d2 / (2.0 * float(gap))
            row_best = np.max(gains, axis=1)
            # Deterministic tie-break by predecessor event ID among equal-gain exact candidates.
            for j in range(len(dest)):
                g = float(row_best[j])
                if g <= 0.0:
                    continue
                cand_cols = np.flatnonzero(np.isclose(gains[j], g, rtol=0.0, atol=1e-14))
                candidates = nearest[j, cand_cols]
                chosen = min(candidates.tolist(), key=lambda ii: str(ids[ii]))
                replace = g > best_gain[j] + 1e-14
                tie = abs(g - best_gain[j]) <= 1e-14 and (best_pred[j] < 0 or str(ids[chosen]) < str(ids[best_pred[j]]))
                if replace or tie:
                    best_gain[j] = g
                    best_pred[j] = chosen
                    best_pred_len[j] = plen[chosen]
        V[dest] = emission[dest] + best_gain
        use = best_pred >= 0
        pred[dest[use]] = best_pred[use]
        plen[dest[use]] = best_pred_len[use] + 1

    eligible_terminal = np.flatnonzero(plen >= MIN_PATH_STATES)
    merit = V[eligible_terminal] / np.sqrt(plen[eligible_terminal].astype(float))
    terminal_order = sorted(range(len(eligible_terminal)), key=lambda j: (-float(merit[j]), str(ids[eligible_terminal[j]])))
    terminal_order = terminal_order[:MAX_SEEDS]
    seeds = eligible_terminal[np.asarray(terminal_order, dtype=np.int64)]
    seed_merit = merit[np.asarray(terminal_order, dtype=np.int64)]

    accepted: list[dict[str, Any]] = []
    accepted_sets: list[set[str]] = []
    inverted: defaultdict[str, list[int]] = defaultdict(list)

    for seed, tscore in zip(seeds.tolist(), seed_merit.tolist()):
        path_rev = []
        cur = int(seed)
        seen = set()
        while cur >= 0 and cur not in seen:
            path_rev.append(cur); seen.add(cur); cur = int(pred[cur])
        path = np.asarray(path_rev[::-1], dtype=np.int64)
        if len(path) < MIN_PATH_STATES:
            continue
        cu, cl, fit_center = fit_path(path, coords, U, logv)
        lo = float(np.min(coords[path])); hi = float(np.max(coords[path]))
        member_idx: list[int] = []
        bmin = int(math.floor((lo - BLIND[1]) / BIN_WIDTH))
        bmax = int(math.floor((hi - BLIND[1]) / BIN_WIDTH))
        for b in range(bmin, bmax + 1):
            if b not in by_bin:
                continue
            idx = by_bin[b]
            lam_lo = max(lo, BLIND[1] + b * BIN_WIDTH)
            lam_hi = min(hi, BLIND[1] + (b + 1) * BIN_WIDTH)
            if lam_hi + 1e-12 < lam_lo:
                continue
            lam_center = 0.5 * (lam_lo + lam_hi)
            pu_c, pl_c = predict(cu, cl, fit_center, np.asarray([lam_center]))
            pred_x = transform(pu_c, pl_c)[0]
            endpoint_lam = np.asarray([lam_lo, lam_hi], dtype=float)
            pu_e, pl_e = predict(cu, cl, fit_center, endpoint_lam)
            end_x = transform(pu_e, pl_e)
            movement = float(np.max(np.linalg.norm(end_x - pred_x[None, :], axis=1)))
            local_candidates = bin_trees[b].query_ball_point(pred_x, r=1.0 + movement + 1e-10)
            if not local_candidates:
                continue
            global_candidates = idx[np.asarray(local_candidates, dtype=np.int64)]
            inspan = global_candidates[(coords[global_candidates] >= lo - 1e-12) & (coords[global_candidates] <= hi + 1e-12)]
            if len(inspan) == 0:
                continue
            pu, pl = predict(cu, cl, fit_center, coords[inspan])
            residual2 = exact_d2(U[inspan], logv[inspan], pu, pl)
            member_idx.extend(inspan[residual2 <= MEMBER_RESIDUAL_MAX**2 + 1e-12].tolist())
        if not member_idx:
            continue
        member_idx = sorted(set(member_idx), key=lambda ii: str(ids[ii]))
        if len(member_idx) < MIN_MEMBERS:
            continue
        members = tuple(str(ids[ii]) for ii in member_idx)
        mset = set(members)

        overlap_counts: Counter[int] = Counter()
        for eid in mset:
            for ai in inverted.get(eid, []):
                overlap_counts[ai] += 1
        duplicate = False
        for ai, inter in overlap_counts.items():
            if jaccard_size(mset, accepted_sets[ai], inter) >= DEDUP_JACCARD - 1e-12:
                duplicate = True
                break
        if duplicate:
            continue

        cid = hashlib.sha256(("DPTBD1|" + "|".join(members)).encode()).hexdigest()[:20]
        fam = {
            "family_id": cid,
            "event_ids": list(members),
            "score": float(tscore),
            "path_states": int(len(path)),
            "path_span_deg": float(hi - lo),
            "terminal_event_id": str(ids[seed]),
        }
        ai = len(accepted)
        accepted.append(fam); accepted_sets.append(mset)
        for eid in mset:
            inverted[eid].append(ai)

    accepted.sort(key=lambda f: (-float(f["score"]), -int(f["path_states"]), f["family_id"]))
    candidate_order_sha = hashlib.sha256("\n".join(f["family_id"] for f in accepted).encode()).hexdigest()
    (a.output / "DP_TBD_V1_CANDIDATES.json").write_text(json.dumps(accepted, indent=2, sort_keys=True, allow_nan=False) + "\n")

    # Truth interpretation begins only after candidate construction and order are immutable.
    m = metrics(accepted, hidden)
    gates = {
        "recovered_at_100_strictly_better_than_839": int(m["recovered_at_100"]) > CONTROL["recovered_at_100"],
        "recovered_at_50_not_worse_than_839": int(m["recovered_at_50"]) >= CONTROL["recovered_at_50"],
        "recovered_at_25_not_worse_than_839": int(m["recovered_at_25"]) >= CONTROL["recovered_at_25"],
        "top100_precision_not_worse_than_839": float(m["top100_dominant_precision"]) >= CONTROL["top100_dominant_precision"],
        "mrr_not_worse_than_839": float(m["mrr"]) >= CONTROL["mrr"],
        "full_catalogue_qualified_at_least_200": int(m["qualified_matches"]) >= 200,
    }
    passed = all(gates.values())
    beats_full = bool(passed and int(m["recovered_at_500"]) >= CONTROL["recovered_at_500"] and int(m["qualified_matches"]) >= CONTROL["qualified_matches"])
    verdict = "PASS_DP_TBD_V1_GMN_DEVELOPMENT" if passed else "FAIL_DP_TBD_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "beats_839_full": beats_full,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "first_valid_outcome_binding": True,
        "events": n,
        "candidate_count": len(accepted),
        "seed_count": len(seeds),
        "metrics": m,
        "control_839": CONTROL,
        "pass_gates": gates,
        "frozen_constants": {
            "bin_width_deg": BIN_WIDTH,
            "radiant_scale_deg": RAD_SCALE_DEG,
            "speed_scale_ratio": 1.08,
            "pseudocount": PSEUDOCOUNT,
            "predecessor_k": PREDECESSOR_K,
            "allowed_gaps": list(GAPS),
            "min_path_states": MIN_PATH_STATES,
            "max_seeds": MAX_SEEDS,
            "member_residual_max": MEMBER_RESIDUAL_MAX,
            "min_members": MIN_MEMBERS,
            "dedup_jaccard": DEDUP_JACCARD,
        },
        "candidate_order_sha256": candidate_order_sha,
        "parameter_search": False,
        "threshold_search": False,
        "score_weight_search": False,
        "hdbscan_candidates_used": False,
        "candidate_generation_recomputed_after_truth": False,
        "blind_exclusion": list(BLIND),
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "claim_boundary": "GMN 2022+2023 development only; SonotaCo remains unopened by this experiment.",
    }
    (a.output / "DP_TBD_V1_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "beats_839_full": beats_full,
        "events": n,
        "candidate_count": len(accepted),
        "metrics": {k: v for k, v in m.items() if k != "first_rank_by_label"},
        "gates": gates,
        "candidate_order_sha256": candidate_order_sha,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

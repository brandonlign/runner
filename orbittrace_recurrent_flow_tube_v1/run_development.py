#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.spatial import cKDTree

YEAR = 2022
YEARS = (YEAR,)
MONTH_KEYS = tuple(f"{YEAR}-{m:02d}" for m in range(1, 13))
BLIND = (20.0, 55.0)
BIN_WIDTH = 2.0
KNN = 4
MIN_ATOM = 4
MIN_STRATA = 3
MIN_SPAN = 6.0
MIN_EVENTS = 10
PERTURB_REPLICAS = 16
PERTURB_RAD_DEG = 0.35
PERTURB_SPEED_FRAC = 0.01
PERSIST_JACCARD = 0.50
PERSIST_MIN = 0.50
TRAJECTORY_TRIM = 2.5
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"


def req(x: bool, msg: str) -> None:
    if not x:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def circular_diff(a: float, b: float) -> float:
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def unit(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lon = np.radians(lon_deg)
    lat = np.radians(lat_deg)
    return np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))


def angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    return math.degrees(math.acos(float(np.clip(np.dot(a, b), -1.0, 1.0))))


def event_field(row: dict[str, Any], names: Iterable[str]) -> float:
    for name in names:
        if name in row and row[name] is not None:
            v = float(row[name])
            if math.isfinite(v):
                return v
    raise RuntimeError(f"event missing required field aliases {tuple(names)}; keys={sorted(row)[:40]}")


def event_id(row: dict[str, Any]) -> str:
    for name in ("id", "event_id", "eventId"):
        if name in row:
            return str(row[name])
    raise RuntimeError("event row lacks ID")


def normalize_event(row: dict[str, Any]) -> dict[str, Any]:
    eid = event_id(row)
    sol = event_field(row, ("sol", "solar_longitude", "solar_lon", "sol_lon")) % 360.0
    sun_lon = event_field(row, ("sun_lon", "sun_centered_longitude", "sun_centered_lon", "lam_sce"))
    lat = event_field(row, ("ecl_lat", "ecliptic_latitude", "lat_sce", "beta"))
    vg = event_field(row, ("vg", "v_g", "geocentric_speed", "velocity"))
    req(vg > 0.0, f"nonpositive speed for {eid}")
    # Make the accessible domain contiguous across 360->0 without crossing the blind interval.
    coord = sol + 360.0 if sol < BLIND[0] else sol
    req(not (BLIND[0] <= sol <= BLIND[1]), f"protected-region event reached RFT normalizer: {eid}")
    return {"id": eid, "sol": sol, "coord": coord, "lon": sun_lon, "lat": lat, "vg": vg}


def deterministic_normals(eid: str, replica: int) -> tuple[float, float, float]:
    h = hashlib.sha256(f"RFT1|{replica}|{eid}".encode()).digest()
    vals = []
    for off in (0, 8, 16):
        a = int.from_bytes(h[off:off+4], "big")
        b = int.from_bytes(h[off+4:off+8], "big")
        u1 = (a + 0.5) / (2**32)
        u2 = (b + 0.5) / (2**32)
        vals.append(math.sqrt(-2.0 * math.log(max(u1, 1e-15))) * math.cos(2.0 * math.pi * u2))
    return float(vals[0]), float(vals[1]), float(vals[2])


def perturb(events: list[dict[str, Any]], replica: int) -> list[dict[str, Any]]:
    if replica == 0:
        return [dict(x) for x in events]
    out = []
    sigma = math.radians(PERTURB_RAD_DEG)
    for e in events:
        z1, z2, z3 = deterministic_normals(e["id"], replica)
        u = unit(np.asarray([e["lon"]]), np.asarray([e["lat"]]))[0]
        # Stable tangent basis.
        ref = np.asarray([0.0, 0.0, 1.0]) if abs(u[2]) < 0.9 else np.asarray([1.0, 0.0, 0.0])
        t1 = np.cross(u, ref); t1 /= np.linalg.norm(t1)
        t2 = np.cross(u, t1); t2 /= np.linalg.norm(t2)
        up = u + sigma * z1 * t1 + sigma * z2 * t2
        up /= np.linalg.norm(up)
        lon = math.degrees(math.atan2(up[1], up[0]))
        lat = math.degrees(math.asin(float(np.clip(up[2], -1.0, 1.0))))
        vg = e["vg"] * math.exp(math.log1p(PERTURB_SPEED_FRAC) * z3)
        q = dict(e); q["lon"] = lon; q["lat"] = lat; q["vg"] = vg
        out.append(q)
    return out


def pair_d(a: dict[str, Any], b: dict[str, Any]) -> float:
    ua = unit(np.asarray([a["lon"]]), np.asarray([a["lat"]]))[0]
    ub = unit(np.asarray([b["lon"]]), np.asarray([b["lat"]]))[0]
    theta = angle_deg(ua, ub) / 3.0
    speed = abs(math.log(a["vg"] / b["vg"])) / math.log(1.08)
    return float(math.hypot(theta, speed))


@dataclass
class Atom:
    aid: str
    bin_index: int
    center: float
    members: tuple[str, ...]
    u: np.ndarray
    logv: float
    medoid_residual: float


def atoms(events: list[dict[str, Any]]) -> list[Atom]:
    by_bin: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for e in events:
        idx = int(math.floor((e["coord"] - BLIND[1]) / BIN_WIDTH))
        by_bin[idx].append(e)
    out: list[Atom] = []
    for bidx in sorted(by_bin):
        rows = by_bin[bidx]
        if len(rows) < MIN_ATOM:
            continue
        lon = np.asarray([r["lon"] for r in rows], float)
        lat = np.asarray([r["lat"] for r in rows], float)
        vg = np.asarray([r["vg"] for r in rows], float)
        uv = unit(lon, lat)
        transformed = np.column_stack((uv / (2.0 * math.sin(math.radians(3.0) / 2.0)), np.log(vg) / math.log(1.08)))
        tree = cKDTree(transformed)
        neighbor_sets: list[list[int]] = []
        for i in range(len(rows)):
            candidates = tree.query_ball_point(transformed[i], r=1.02)
            ds = []
            for j in candidates:
                if j == i:
                    continue
                d = pair_d(rows[i], rows[j])
                if d <= 1.0 + 1e-12:
                    ds.append((d, event_id(rows[j]), j))
            ds.sort(key=lambda x: (x[0], x[1]))
            neighbor_sets.append([j for _d, _eid, j in ds[:KNN]])
        adj = [set() for _ in rows]
        for i, ns in enumerate(neighbor_sets):
            for j in ns:
                if i in neighbor_sets[j]:
                    adj[i].add(j); adj[j].add(i)
        seen = set()
        for seed in range(len(rows)):
            if seed in seen:
                continue
            stack = [seed]; comp = []; seen.add(seed)
            while stack:
                i = stack.pop(); comp.append(i)
                for j in sorted(adj[i]):
                    if j not in seen:
                        seen.add(j); stack.append(j)
            if len(comp) < MIN_ATOM:
                continue
            mids = []
            for i in comp:
                ds = [pair_d(rows[i], rows[j]) for j in comp if j != i]
                mids.append((float(np.median(ds)) if ds else 0.0, event_id(rows[i]), i))
            med_res, _mid, med_idx = min(mids)
            uu = uv[comp].sum(axis=0); uu /= np.linalg.norm(uu)
            logv = float(np.median(np.log(vg[comp])))
            members = tuple(sorted(event_id(rows[i]) for i in comp))
            aid = hashlib.sha256((f"{bidx}|" + "|".join(members)).encode()).hexdigest()[:16]
            out.append(Atom(aid, bidx, BLIND[1] + (bidx + 0.5) * BIN_WIDTH, members, uu, logv, med_res))
    return out


def transition(a: Atom, b: Atom) -> float | None:
    delta = b.center - a.center
    if delta < 1.5 or delta > 6.5:
        return None
    theta_scale = 1.5 + 0.20 * delta
    speed_scale = math.log(1.04) + 0.004 * delta
    c = (angle_deg(a.u, b.u) / theta_scale) ** 2 + (abs(a.logv - b.logv) / speed_scale) ** 2
    return float(c) if c <= 1.0 + 1e-12 else None


@dataclass
class Tube:
    tid: str
    atom_ids: tuple[str, ...]
    members: tuple[str, ...]
    strata: int
    span: float
    transition_costs: tuple[float, ...]


def build_tubes(atom_list: list[Atom], ownership: bool = True) -> list[Tube]:
    by_id = {a.aid: a for a in atom_list}
    ordered = sorted(atom_list, key=lambda a: (a.bin_index, a.aid))
    edges = []
    for i, a in enumerate(ordered):
        for b in ordered[i+1:]:
            if b.center - a.center > 6.5:
                break
            c = transition(a, b)
            if c is not None:
                edges.append((c, a.aid, b.aid))
    succ: dict[str, tuple[str, float]] = {}
    pred: dict[str, tuple[str, float]] = {}
    if ownership:
        # Deterministic low-cost path ownership. Each atom has at most one predecessor and successor.
        for c, aa, bb in sorted(edges, key=lambda x: (x[0], x[1], x[2])):
            if aa in succ or bb in pred:
                continue
            succ[aa] = (bb, c); pred[bb] = (aa, c)
        starts = [a.aid for a in ordered if a.aid not in pred]
    else:
        # Explanatory ablation: every atom seeds its own cheapest-successor path; downstream reuse is allowed.
        choices: dict[str, tuple[str, float]] = {}
        for c, aa, bb in sorted(edges, key=lambda x: (x[0], x[1], x[2])):
            choices.setdefault(aa, (bb, c))
        succ = choices
        starts = [a.aid for a in ordered]
    tubes = []
    for start in starts:
        path = [start]; costs = []; cur = start; visited = {start}
        while cur in succ:
            nxt, c = succ[cur]
            if nxt in visited:
                break
            path.append(nxt); costs.append(float(c)); visited.add(nxt); cur = nxt
        ats = [by_id[x] for x in path]
        unique_members = tuple(sorted({eid for a in ats for eid in a.members}))
        strata = len({a.bin_index for a in ats})
        span = max(a.center for a in ats) - min(a.center for a in ats)
        if strata < MIN_STRATA or span + 1e-12 < MIN_SPAN or len(unique_members) < MIN_EVENTS:
            continue
        tid = hashlib.sha256("|".join(path).encode()).hexdigest()[:16]
        tubes.append(Tube(tid, tuple(path), unique_members, strata, float(span), tuple(costs)))
    # exact member-duplicate collapse, deterministic best coherence
    best: dict[tuple[str, ...], Tube] = {}
    for t in tubes:
        key = t.members
        val = (float(np.median(t.transition_costs)) if t.transition_costs else 0.0, t.tid)
        if key not in best:
            best[key] = t
        else:
            old = best[key]
            oval = (float(np.median(old.transition_costs)) if old.transition_costs else 0.0, old.tid)
            if val < oval:
                best[key] = t
    return sorted(best.values(), key=lambda t: t.tid)


def jaccard(a: set[str], b: set[str]) -> float:
    inter = len(a & b)
    return float(inter / len(a | b)) if inter else 0.0


def fit_trim(t: Tube, lookup: dict[str, dict[str, Any]], do_trim: bool = True) -> tuple[tuple[str, ...], float]:
    ids = list(t.members)
    if len(ids) < MIN_EVENTS:
        return tuple(), math.inf
    def residuals(current: list[str]) -> tuple[np.ndarray, np.ndarray]:
        lam = np.asarray([lookup[e]["coord"] for e in current], float)
        x = lam - float(np.mean(lam))
        uv = unit(np.asarray([lookup[e]["lon"] for e in current]), np.asarray([lookup[e]["lat"] for e in current]))
        logv = np.log(np.asarray([lookup[e]["vg"] for e in current], float))
        A = np.column_stack((np.ones(len(x)), x))
        cu = np.column_stack([np.linalg.lstsq(A, uv[:, j], rcond=None)[0] for j in range(3)])
        cl = np.linalg.lstsq(A, logv, rcond=None)[0]
        pred_u = A @ cu; pred_u /= np.linalg.norm(pred_u, axis=1, keepdims=True)
        pred_l = A @ cl
        rr = []
        for i in range(len(current)):
            th = angle_deg(uv[i], pred_u[i]) / 3.0
            sv = abs(logv[i] - pred_l[i]) / math.log(1.08)
            rr.append(math.hypot(th, sv))
        return np.asarray(rr, float), pred_u
    r, _ = residuals(ids)
    if do_trim:
        ids = [eid for eid, rv in zip(ids, r) if rv <= TRAJECTORY_TRIM]
        if len(ids) < MIN_EVENTS:
            return tuple(), math.inf
        r, _ = residuals(ids)
    return tuple(sorted(ids)), float(np.median(r)) if len(r) else math.inf


def generate(events: list[dict[str, Any]], ownership: bool = True, do_trim: bool = True, do_persistence: bool = True) -> list[dict[str, Any]]:
    lookup = {e["id"]: e for e in events}
    base_atoms = atoms(events)
    base_tubes = build_tubes(base_atoms, ownership=ownership)
    replica_sets: list[list[set[str]]] = []
    if do_persistence:
        for r in range(1, PERTURB_REPLICAS + 1):
            pe = perturb(events, r)
            replica_sets.append([set(t.members) for t in build_tubes(atoms(pe), ownership=ownership)])
    out = []
    for t in base_tubes:
        bset = set(t.members)
        if do_persistence:
            survive = 0
            for rsets in replica_sets:
                best = max((jaccard(bset, s) for s in rsets), default=0.0)
                survive += int(best >= PERSIST_JACCARD)
            persistence = survive / PERTURB_REPLICAS
            if persistence + 1e-12 < PERSIST_MIN:
                continue
        else:
            persistence = 1.0
        members, med_res = fit_trim(t, lookup, do_trim=do_trim)
        if len(members) < MIN_EVENTS:
            continue
        med_trans = float(np.median(t.transition_costs)) if t.transition_costs else 0.0
        score = persistence * math.log1p(len(members)) * math.log1p(t.strata) / (1.0 + med_trans + med_res)
        cid = hashlib.sha256(("RFT1|" + "|".join(members)).encode()).hexdigest()[:20]
        out.append({
            "family_id": cid,
            "event_ids": list(members),
            "score": float(score),
            "persistence": float(persistence),
            "strata": int(t.strata),
            "span": float(t.span),
            "median_transition_cost": med_trans,
            "median_trajectory_residual": float(med_res),
            "atom_ids": list(t.atom_ids),
        })
    out.sort(key=lambda f: (-f["score"], -f["persistence"], -len(f["event_ids"]), f["family_id"]))
    return out


def eligible_labels(hidden: dict[str, str]) -> dict[str, int]:
    c = Counter(label for eid, label in hidden.items() if str(eid).startswith(str(YEAR)) and label != "SPORADIC")
    return {label: n for label, n in c.items() if n >= 4}


def truth(f: dict[str, Any], hidden: dict[str, str], eligible: dict[str, int]) -> dict[str, Any]:
    ids = [str(x) for x in f["event_ids"]]
    counts = Counter(hidden.get(eid, "SPORADIC") for eid in ids)
    rows = []
    for label, total in eligible.items():
        ov = int(counts.get(label, 0))
        if ov <= 0:
            continue
        p = ov / max(len(ids), 1); r = ov / total
        f1 = 2*p*r/(p+r) if p+r else 0.0
        rows.append((f1, p, ov, label, r))
    if not rows:
        return {"positive": False, "best_label": None, "f1": 0.0, "precision": 0.0, "dominant_precision": 0.0}
    f1, p, ov, label, r = max(rows, key=lambda x: (x[0], x[1], x[2], x[3]))
    non = counts.copy(); non.pop("SPORADIC", None)
    dominant = max(non.values(), default=0) / max(len(ids), 1)
    return {"positive": bool(p >= 0.5 and ov >= 4), "best_label": label, "f1": float(f1), "precision": float(p), "recall": float(r), "overlap": ov, "dominant_precision": float(dominant)}


def metrics(fams: list[dict[str, Any]], hidden: dict[str, str]) -> dict[str, Any]:
    eligible = eligible_labels(hidden)
    truths = {f["family_id"]: truth(f, hidden, eligible) for f in fams}
    first: dict[str, int | None] = {label: None for label in eligible}
    counts: Counter[str] = Counter()
    top_prec = []
    for rank, f in enumerate(fams, 1):
        t = truths[f["family_id"]]
        if rank <= 100:
            top_prec.append(t["dominant_precision"])
        if t["positive"] and t["best_label"] in eligible:
            label = str(t["best_label"])
            counts[label] += int(rank <= 500)
            if first[label] is None:
                first[label] = rank
    represented = [label for label, r in first.items() if r is not None]
    frag = [counts[label] for label in represented if first[label] is not None and first[label] <= 500]
    return {
        "eligible_labels": len(eligible),
        "qualified_matches": len(represented),
        "recovered_at_25": sum(r is not None and r <= 25 for r in first.values()),
        "recovered_at_50": sum(r is not None and r <= 50 for r in first.values()),
        "recovered_at_100": sum(r is not None and r <= 100 for r in first.values()),
        "recovered_at_500": sum(r is not None and r <= 500 for r in first.values()),
        "top100_dominant_precision": float(np.mean(top_prec)) if top_prec else 0.0,
        "mrr": float(np.mean([1.0/r for r in first.values() if r is not None])) if represented else 0.0,
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
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN runtime support artifact changed")
    qmod = load_module(a.quality_source, "rft_frozen_839_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-flow-tube-v1-development-2022-only"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == [YEAR], f"GMN development runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN 2022 source list changed")

    # Fail closed if any protected-region event survived the frozen parser.
    raw = list(scan[YEAR])
    events = [normalize_event(row) for row in raw]
    req(len(events) == len(raw), "event normalization changed event count")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected region survived parser")
    req(all(str(e["id"]).startswith(str(YEAR)) for e in events), "non-2022 event reached development")
    req(all(str(eid).startswith(str(YEAR)) for eid in hidden), "non-2022 label reached development")

    fams = generate(events, ownership=True, do_trim=True, do_persistence=True)
    m = metrics(fams, hidden)
    ab_no_owner = metrics(generate(events, ownership=False, do_trim=True, do_persistence=True), hidden)
    ab_no_persist = metrics(generate(events, ownership=True, do_trim=True, do_persistence=False), hidden)
    ab_no_trim = metrics(generate(events, ownership=True, do_trim=False, do_persistence=True), hidden)

    persistence_top = [float(f["persistence"]) for f in fams[:100]]
    high_persist_share = float(np.mean([x >= 0.75 for x in persistence_top])) if persistence_top else 0.0
    viable = bool(
        int(m["qualified_matches"]) >= 120
        and int(m["recovered_at_100"]) >= 55
        and float(m["top100_dominant_precision"]) >= 0.60
        and float(m["fragmentation_median_top500"]) <= 3.0
        and high_persist_share >= 0.75
    )
    verdict = "PASS_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY" if viable else "FAIL_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY"
    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_DEVELOPMENT_ONLY",
        "events": len(events),
        "retained_candidates": len(fams),
        "metrics": m,
        "top100_persistence_ge_0p75_share": high_persist_share,
        "ablations": {
            "no_path_ownership": ab_no_owner,
            "no_perturbation_persistence": ab_no_persist,
            "no_trajectory_trim": ab_no_trim,
        },
        "frozen_constants": {
            "bin_width_deg": BIN_WIDTH, "knn": KNN, "min_atom": MIN_ATOM,
            "min_strata": MIN_STRATA, "min_span_deg": MIN_SPAN, "min_events": MIN_EVENTS,
            "perturb_replicas": PERTURB_REPLICAS, "perturb_radiant_sigma_deg": PERTURB_RAD_DEG,
            "perturb_speed_sigma_frac": PERTURB_SPEED_FRAC, "persistence_jaccard": PERSIST_JACCARD,
            "persistence_min": PERSIST_MIN, "trajectory_trim": TRAJECTORY_TRIM,
        },
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "sonotaco_2013_2014_access": False,
        "gmn_2023_access": False,
        "candidate_order_sha256": hashlib.sha256("\n".join(f["family_id"] for f in fams).encode()).hexdigest(),
    }
    (a.output / "RFT_V1_GMN2022_DEVELOPMENT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (a.output / "rft_v1_gmn2022_candidates.json").write_text(json.dumps(fams, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "events": len(events), "candidates": len(fams), "metrics": {k:v for k,v in m.items() if k != "first_rank_by_label"}, "high_persist_share": high_persist_share}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

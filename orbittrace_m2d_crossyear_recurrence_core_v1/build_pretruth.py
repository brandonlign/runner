#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
FAIR_PRETRUTH_SHA256 = "8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5"
STRUCTURAL_BLOB = "c1efa8da34dea140726a4c2fe4943eb29a304538"
EXPECTED_COUNTS = {"2022": 315024, "2023": 423658}
EXPECTED_TOTAL = 738682
MIN_ANNUAL_RECURRENCE = 2
INHERITED_NEIGHBOR_SUPPORT = 4


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def same_year_reference_radii(Z: np.ndarray) -> np.ndarray:
    n = len(Z)
    req(n >= 2, "same-year reference requires >=2 events")
    take = min(INHERITED_NEIGHBOR_SUPPORT, n - 1)
    tree = cKDTree(Z)
    # Ask for self plus every required non-self neighbor. Explicitly remove self
    # so exact-coordinate ties cannot accidentally change the neighbor count.
    distances, indices = tree.query(Z, k=take + 1, p=2.0, eps=0.0, workers=1)
    distances = np.asarray(distances, dtype=float)
    indices = np.asarray(indices, dtype=int)
    if distances.ndim == 1:
        distances = distances[:, None]
        indices = indices[:, None]
    out = np.empty(n, dtype=float)
    for i in range(n):
        vals = [float(d) for d, j in zip(distances[i], indices[i]) if int(j) != i]
        # With exact-coordinate ties the query can in principle omit self from a
        # tied k-set. Fall back to an exact all-row distance only for that row.
        if len(vals) < take:
            all_d = np.linalg.norm(Z - Z[i], axis=1)
            vals = sorted(float(all_d[j]) for j in range(n) if j != i)[:take]
        else:
            vals = sorted(vals)[:take]
        req(len(vals) == take and np.all(np.isfinite(vals)), "invalid same-year neighbor distances")
        out[i] = vals[-1]
    req(np.all(np.isfinite(out)) and np.all(out >= 0.0), "invalid same-year reference radii")
    return out


def connected_components(vertices: list[str], edges: set[tuple[str, str]]) -> list[list[str]]:
    adj: dict[str, set[str]] = {v: set() for v in vertices}
    for a, b in edges:
        req(a in adj and b in adj and a != b, "invalid recurrence edge")
        adj[a].add(b)
        adj[b].add(a)
    seen: set[str] = set()
    out: list[list[str]] = []
    for start in sorted(vertices):
        if start in seen or not adj[start]:
            continue
        stack = [start]
        seen.add(start)
        comp: list[str] = []
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nxt in sorted(adj[cur], reverse=True):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        out.append(sorted(comp))
    out.sort(key=lambda c: (-len(c), c))
    return out


def extract_core(candidate: dict[str, Any], by_id: dict[str, dict[str, Any]], structural: Any) -> dict[str, Any]:
    envelope = sorted(str(x) for x in candidate["event_ids"])
    req(len(envelope) == int(candidate["member_count"]) and len(envelope) == len(set(envelope)), "candidate membership mismatch")
    annual: dict[int, list[dict[str, Any]]] = {}
    for y in YEARS:
        annual[y] = [by_id[eid] for eid in envelope if int(by_id[eid]["year"]) == y]

    if any(len(annual[y]) < 2 for y in YEARS):
        return {
            "family_id": str(candidate["family_id"]),
            "family_hash": str(candidate["family_hash"]),
            "rank": int(candidate["internal_mass_rank"]),
            "envelope_member_count": len(envelope),
            "core_event_ids": [],
            "core_member_count": 0,
            "removed_member_count": len(envelope),
            "retained_fraction": 0.0,
            "qualifying_component_count": 0,
            "qualifying_components": [],
            "directed_qualifying_link_count": 0,
            "undirected_edge_count": 0,
            "annual_envelope_counts": {str(y): len(annual[y]) for y in YEARS},
            "annual_core_counts": {str(y): 0 for y in YEARS},
        }

    ids: dict[int, list[str]] = {y: [str(e["id"]) for e in annual[y]] for y in YEARS}
    Z: dict[int, np.ndarray] = {y: np.asarray(structural.physical_embedding(annual[y]), dtype=float) for y in YEARS}
    radii: dict[int, np.ndarray] = {y: same_year_reference_radii(Z[y]) for y in YEARS}
    index: dict[int, dict[str, int]] = {y: {eid: i for i, eid in enumerate(ids[y])} for y in YEARS}
    req(all(len(index[y]) == len(ids[y]) for y in YEARS), "duplicate annual IDs")

    edges: set[tuple[str, str]] = set()
    directed = 0
    for y, other in ((2022, 2023), (2023, 2022)):
        tree = cKDTree(Z[other])
        dist, ix = tree.query(Z[y], k=1, p=2.0, eps=0.0, workers=1)
        dist = np.asarray(dist, dtype=float).reshape(-1)
        ix = np.asarray(ix, dtype=int).reshape(-1)
        req(len(dist) == len(ids[y]) and np.all(np.isfinite(dist)), "invalid cross-year nearest neighbors")
        for i, (d, j) in enumerate(zip(dist, ix)):
            if float(d) <= float(radii[y][i]):
                a, b = ids[y][i], ids[other][int(j)]
                edges.add(tuple(sorted((a, b))))
                directed += 1

    comps = connected_components(envelope, edges)
    qualifying: list[dict[str, Any]] = []
    keep: set[str] = set()
    for comp in comps:
        counts = {y: sum(int(by_id[eid]["year"]) == y for eid in comp) for y in YEARS}
        if all(counts[y] >= MIN_ANNUAL_RECURRENCE for y in YEARS):
            keep.update(comp)
            qualifying.append({
                "event_ids": comp,
                "member_count": len(comp),
                "annual_counts": {str(y): counts[y] for y in YEARS},
            })
    core = sorted(keep)
    req(set(core).issubset(envelope), "core escaped envelope")
    annual_core = {str(y): sum(int(by_id[eid]["year"]) == y for eid in core) for y in YEARS}
    return {
        "family_id": str(candidate["family_id"]),
        "family_hash": str(candidate["family_hash"]),
        "rank": int(candidate["internal_mass_rank"]),
        "envelope_member_count": len(envelope),
        "core_event_ids": core,
        "core_member_count": len(core),
        "removed_member_count": len(envelope) - len(core),
        "retained_fraction": float(len(core) / len(envelope)) if envelope else 0.0,
        "qualifying_component_count": len(qualifying),
        "qualifying_components": qualifying,
        "directed_qualifying_link_count": int(directed),
        "undirected_edge_count": len(edges),
        "annual_envelope_counts": {str(y): len(annual[y]) for y in YEARS},
        "annual_core_counts": annual_core,
    }


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    e = np.asarray([int(r["envelope_member_count"]) for r in rows], dtype=float)
    c = np.asarray([int(r["core_member_count"]) for r in rows], dtype=float)
    return {
        "candidate_count": len(rows),
        "nonempty_core_count": int(np.sum(c > 0)),
        "active_shrink_count": int(np.sum(c < e)),
        "envelope_mean_member_count": float(np.mean(e)) if len(e) else 0.0,
        "core_mean_member_count": float(np.mean(c)) if len(c) else 0.0,
        "envelope_p90_member_count": float(np.quantile(e, 0.9)) if len(e) else 0.0,
        "core_p90_member_count": float(np.quantile(c, 0.9)) if len(c) else 0.0,
        "envelope_max_member_count": int(np.max(e)) if len(e) else 0,
        "core_max_member_count": int(np.max(c)) if len(c) else 0,
        "total_envelope_members_across_candidates": int(np.sum(e)),
        "total_core_members_across_candidates": int(np.sum(c)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fair-pretruth", type=Path, required=True)
    ap.add_argument("--geometry", type=Path, required=True)
    ap.add_argument("--structural-source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.fair_pretruth) == FAIR_PRETRUTH_SHA256, "fair pretruth changed")
    req(blob(a.structural_source) == STRUCTURAL_BLOB, "structural source changed")
    structural = load(a.structural_source, "m2d_recurrence_structural")
    req(tuple(structural.YEARS) == YEARS and int(structural.MIN_SUPPORT) == 4 and float(structural.RADIUS) == 1.0, "structural constants changed")

    fair = json.loads(a.fair_pretruth.read_text())
    req(fair["scientific_role"] == "TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH", "wrong fair pretruth role")
    req(fair["shower_truth_used"] is False and fair["target_information_access"] is False and fair["target_region_events_accessed"] is False, "fair pretruth firewall")

    geom = json.loads(a.geometry.read_text())
    req(geom["scientific_role"] == "LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY", "wrong geometry role")
    req(int(geom["events_total"]) == EXPECTED_TOTAL and geom["events_by_year"] == EXPECTED_COUNTS, "geometry counts changed")
    req(geom["blind_exclusion"] == list(BLIND) and geom["shower_truth_exported"] is False, "geometry firewall")
    events = list(geom["events"])
    req(len(events) == EXPECTED_TOTAL, "geometry row count")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected event in geometry")
    by_id = {str(e["id"]): e for e in events}
    req(len(by_id) == EXPECTED_TOTAL, "duplicate geometry event ID")

    out_subsets: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for s in fair["subsets"]:
        d, b = int(s["denominator"]), int(s["bucket"])
        envelopes = list(s["successor_candidates"])
        req([int(x["internal_mass_rank"]) for x in envelopes] == list(range(1, len(envelopes) + 1)), f"parent rank drift d{d}b{b}")
        req(all(str(eid) in by_id for c in envelopes for eid in c["event_ids"]), f"candidate geometry missing d{d}b{b}")
        cores: list[dict[str, Any]] = []
        for pos, cand in enumerate(envelopes, 1):
            row = extract_core(cand, by_id, structural)
            req(row["rank"] == pos, f"rank mismatch d{d}b{b} rank{pos}")
            cores.append(row)
            all_rows.append(row)
        out_subsets.append({
            "denominator": d,
            "bucket": b,
            "event_count": int(s["event_count"]),
            "annual_event_ids": s["annual_event_ids"],
            "parent_candidate_count": len(envelopes),
            "cores": cores,
            "summary": summary(cores),
        })
        print(json.dumps({"panel": f"d{d}_b{b}", **summary(cores)}, sort_keys=True), flush=True)

    payload = {
        "schema": "ORBITTRACE_M2D_CROSSYEAR_RECURRENCE_CORE_V1_PRETRUTH",
        "scientific_role": "TARGET_EXCLUDED_DUAL_VIEW_M2D_ENVELOPE_CROSSYEAR_RECURRENCE_CORE_FROZEN_BEFORE_TRUTH",
        "fair_pretruth_sha256": FAIR_PRETRUTH_SHA256,
        "geometry_sha256": sha(a.geometry),
        "structural_source_blob": STRUCTURAL_BLOB,
        "years": list(YEARS),
        "blind_exclusion": list(BLIND),
        "inherited_neighbor_support": INHERITED_NEIGHBOR_SUPPORT,
        "minimum_annual_recurrence": MIN_ANNUAL_RECURRENCE,
        "edge_rule": "nearest_opposite_year_distance_le_source_within_year_min4_available_neighbor_radius",
        "component_rule": "retain_all_components_with_at_least_2_members_in_each_year",
        "fallback_rule": "none",
        "subsets": out_subsets,
        "overall_summary": summary(all_rows),
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "external_survey_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": "PASS_M2D_CROSSYEAR_RECURRENCE_CORE_V1_PRETRUTH", "sha256": sha(a.output), "overall_summary": payload["overall_summary"]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

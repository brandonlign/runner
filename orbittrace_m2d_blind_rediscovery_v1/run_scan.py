#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
from types import SimpleNamespace
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
RADIUS = 1.0
MIN_SUPPORT = 4
BLIND_SOURCE_SHA256 = "48434df612f790924e6efce45b6b8d4de1401880f398994bc58eef2fce0987e5"
BLIND_SOURCE_BYTES = 24135
CPP_SHA256 = "4eef6f1b70b5baee5d1983d2480c02d73569b12af868ec23bbb6009d6ca1fa37"
STRUCTURAL_BLOB = "c1efa8da34dea140726a4c2fe4943eb29a304538"
SUPPORT_BLOB = "4988997c023d9df2b504372b4290dcab379a6dcc"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def decode_blind_source(parts_dir: Path, output: Path) -> str:
    parts = sorted(parts_dir.glob("part*.b64"))
    req([p.name for p in parts] == [f"part{i:02d}.b64" for i in range(4)], "wrong blind source parts")
    encoded = "".join("".join(p.read_text(encoding="ascii").split()) for p in parts)
    req(len(encoded) == 9600, f"blind encoded length changed: {len(encoded)}")
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    req(len(source) == BLIND_SOURCE_BYTES, f"blind source bytes changed: {len(source)}")
    req(sha256_bytes(source) == BLIND_SOURCE_SHA256, "blind source SHA changed")
    text = source.decode("utf-8")
    forbidden = [
        "april_candidate_members.csv",
        "247.17",
        "-14.34",
        "37.62",
        "OrbitTrace-April-36.9",
    ]
    req(not any(x in text for x in forbidden), "target literal present in blind source")
    output.write_bytes(source)
    return BLIND_SOURCE_SHA256


def family_id(prefix: str, members: list[str]) -> str:
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode()).hexdigest()[:20]


def family_hash(members: list[str]) -> str:
    return hashlib.sha256("|".join(members).encode()).hexdigest()[:20]


def diagram_sorted(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    if a.size == 0:
        return np.empty((0, 2), dtype=float)
    req(a.ndim == 2 and a.shape[1] == 2 and np.all(np.isfinite(a)), "invalid ToMATo diagram")
    return a[np.lexsort((a[:, 1], a[:, 0]))]


def support_resolved_cut_linear(
    structural: Any,
    events: list[dict[str, Any]],
    *,
    keep_neighbors: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[list[int]] | None, np.ndarray, np.ndarray, np.ndarray]:
    """Exact support-resolved cut with linear hierarchy-membership storage.

    Scientific operations are unchanged from the frozen support-resolved cut. The only
    implementation difference is that internal-node event frozensets are replaced by
    subtree sizes and a leaf->selected-node ownership traversal.
    """
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    Z = structural.physical_embedding(ordered)
    raw = cKDTree(Z).query_ball_point(Z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw]
    req(len(neighbors) == len(ids), "radius graph row count")
    for i, row in enumerate(neighbors):
        req(bool(row) and i in row, f"self missing at radius row {i}")
        req(row[0] >= 0 and row[-1] < len(ids), f"radius index out of range {i}")

    degrees = np.asarray([len(row) for row in neighbors], dtype=np.int64)
    rho = degrees.astype(float) / float(len(ids))
    req(np.all(rho > 0.0) and np.all(np.isfinite(rho)), "invalid radius density")

    model = Tomato(graph_type="manual", density_type="manual")
    model.fit(neighbors, weights=rho)
    leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    L = int(model.n_leaves_)
    req(leaf_labels.shape == (len(ids),) and L >= 1, "bad ToMATo leaves")
    req(int(leaf_labels.min()) >= 0 and int(leaf_labels.max()) + 1 == L, "noncontiguous ToMATo leaves")
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(L - len(children) == roots_expected, "leaf/merge/root arithmetic")

    diagram = np.asarray(model.diagram_, dtype=float)
    ds = diagram_sorted(diagram)
    P = np.sort(np.asarray(diagram[:, 0] - diagram[:, 1], dtype=float)) if diagram.size else np.empty(0, dtype=float)
    req(len(P) == len(children) == len(ds) and np.all(P >= -1e-15), "bad finite persistence")
    P = np.maximum(P, 0.0)

    N = L + len(children)
    parent = np.full(N, -1, dtype=np.int64)
    subtree_size = np.zeros(N, dtype=np.int64)
    subtree_size[:L] = np.bincount(leaf_labels, minlength=L)
    req(np.all(subtree_size[:L] > 0), "empty ToMATo leaf")
    active_peak = np.full(N, np.nan, dtype=float)
    active_key: list[str | None] = [None] * N
    merge_level = np.full(N, np.nan, dtype=float)

    for i, (lab, eid) in enumerate(zip(leaf_labels.tolist(), ids)):
        val = float(rho[i])
        old = active_peak[lab]
        key = active_key[lab]
        if not np.isfinite(old) or val > old or (val == old and (key is None or eid < key)):
            active_peak[lab] = val
            active_key[lab] = eid

    reconstructed: list[list[float]] = []
    dying: set[int] = set()
    for off, pair in enumerate(children):
        node = L + off
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < node and 0 <= b < node and a != b, "bad ToMATo child")
        req(parent[a] == -1 and parent[b] == -1, "hierarchy node has multiple parents")
        parent[a] = node
        parent[b] = node
        subtree_size[node] = subtree_size[a] + subtree_size[b]
        pa, pb = float(active_peak[a]), float(active_peak[b])
        ka, kb = str(active_key[a]), str(active_key[b])
        if pa > pb or (pa == pb and ka < kb):
            winner, loser = a, b
        else:
            winner, loser = b, a
        active_peak[node] = float(active_peak[winner])
        active_key[node] = str(active_key[winner])
        req(loser not in dying, "mode died twice")
        dying.add(loser)
        death = float(active_peak[loser]) - float(P[off])
        merge_level[node] = death
        reconstructed.append([float(active_peak[loser]), death])

    roots = np.flatnonzero(parent == -1)
    req(len(roots) == roots_expected, "root count mismatch")
    req(int(subtree_size[roots].sum()) == len(ids), "roots do not partition events")
    rec = diagram_sorted(np.asarray(reconstructed, dtype=float))
    req(rec.shape == ds.shape and np.allclose(rec, ds, rtol=0.0, atol=1e-12), "ToMATo diagram reconstruction mismatch")

    selected_nodes: list[int] = []
    stack = [int(x) for x in roots[::-1]]
    while stack:
        node = stack.pop()
        if node < L:
            if int(subtree_size[node]) >= MIN_SUPPORT:
                selected_nodes.append(node)
            continue
        a, b = map(int, children[node - L])
        if int(subtree_size[a]) >= MIN_SUPPORT and int(subtree_size[b]) >= MIN_SUPPORT:
            stack.append(b)
            stack.append(a)
        elif int(subtree_size[node]) >= MIN_SUPPORT:
            selected_nodes.append(node)
    req(len(selected_nodes) == len(set(selected_nodes)), "duplicate selected node")

    selected_set = set(selected_nodes)
    leaf_owner = np.full(L, -1, dtype=np.int64)
    stack2: list[tuple[int, int]] = [(int(r), -1) for r in roots[::-1]]
    while stack2:
        node, owner = stack2.pop()
        if node in selected_set:
            owner = node
        if node < L:
            leaf_owner[node] = owner
        else:
            a, b = map(int, children[node - L])
            stack2.append((b, owner))
            stack2.append((a, owner))

    ids_by_node: dict[int, list[str]] = {node: [] for node in selected_nodes}
    for eid, lab in zip(ids, leaf_labels.tolist()):
        owner = int(leaf_owner[int(lab)])
        if owner >= 0:
            ids_by_node[owner].append(eid)
    req(sum(len(v) for v in ids_by_node.values()) <= len(ids), "cut coverage exceeds universe")
    for node in selected_nodes:
        req(len(ids_by_node[node]) == int(subtree_size[node]) >= MIN_SUPPORT, "selected membership size mismatch")

    rows: list[dict[str, Any]] = []
    for node in selected_nodes:
        mem = ids_by_node[node]
        p = int(parent[node])
        outside = 0.0 if p == -1 else float(merge_level[p])
        req(np.isfinite(outside), f"missing outside merge {node}")
        contrast = float(active_peak[node]) - outside
        req(contrast >= -1e-12 and np.isfinite(contrast), f"bad modal contrast {node}")
        contrast = max(contrast, 0.0)
        rows.append({
            "family_id": family_id("TSRC1", mem),
            "family_hash": family_hash(mem),
            "event_ids": mem,
            "member_count": len(mem),
            "node": int(node),
            "is_root": bool(p == -1),
            "active_mode_peak": float(active_peak[node]),
            "active_mode_key": str(active_key[node]),
            "outside_merge_level": outside,
            "modal_contrast": contrast,
        })
    rows.sort(key=lambda r: (-float(r["modal_contrast"]), str(r["family_hash"])))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank

    summary = {
        "candidate_count": len(rows),
        "root_count": len(roots),
        "leaf_count": L,
        "internal_node_count": len(children),
        "covered_event_count": int(sum(int(r["member_count"]) for r in rows)),
        "median_radius_degree": float(np.median(degrees)),
        "p90_radius_degree": float(np.quantile(degrees, 0.9)),
        "max_radius_degree": int(degrees.max()),
        "pairwise_disjoint_by_construction": True,
        "diagram_reconstruction_max_abs_error": float(np.max(np.abs(rec - ds))) if rec.size else 0.0,
    }
    if not keep_neighbors:
        neighbors_out = None
    else:
        neighbors_out = neighbors
    return rows, summary, neighbors_out, leaf_labels, leaf_owner, degrees


def synthetic_events() -> list[dict[str, Any]]:
    rng = np.random.default_rng(20260819)
    rows: list[dict[str, Any]] = []
    k = 0
    for c in range(12):
        sol0 = (11.0 + 29.0 * c) % 360.0
        lon0 = (-155.0 + 27.0 * c + 180.0) % 360.0 - 180.0
        lat0 = -35.0 + 6.0 * c
        vg0 = 18.0 + 2.7 * c
        for year in YEARS:
            for _ in range(10):
                rows.append({
                    "id": f"SYN{k:04d}",
                    "year": year,
                    "sol": float((sol0 + rng.normal(0, 0.7)) % 360.0),
                    "lon": float(((lon0 + rng.normal(0, 0.6) + 180.0) % 360.0) - 180.0),
                    "lat": float(np.clip(lat0 + rng.normal(0, 0.5), -85, 85)),
                    "vg": float(vg0 * math.exp(rng.normal(0, 0.012))),
                })
                k += 1
    for _ in range(80):
        rows.append({
            "id": f"SYN{k:04d}",
            "year": YEARS[k % 2],
            "sol": float(rng.uniform(0, 360)),
            "lon": float(rng.uniform(-180, 180)),
            "lat": float(rng.uniform(-70, 70)),
            "vg": float(rng.uniform(10, 65)),
        })
        k += 1
    return rows


def equivalence_audit(structural: Any, support: Any) -> dict[str, Any]:
    events = synthetic_events()
    original, _orig_summary = support.support_resolved_cut(structural, events)
    optimized, opt_summary, _n, _l, _o, _d = support_resolved_cut_linear(structural, events, keep_neighbors=False)
    req(len(original) == len(optimized), "optimized support cut candidate count differs on synthetic audit")
    fields = ["family_id", "family_hash", "event_ids", "member_count", "node", "is_root", "active_mode_key"]
    float_fields = ["active_mode_peak", "outside_merge_level", "modal_contrast"]
    for i, (a, b) in enumerate(zip(original, optimized)):
        for field in fields:
            req(a[field] == b[field], f"synthetic support-cut mismatch row={i} field={field}")
        for field in float_fields:
            req(abs(float(a[field]) - float(b[field])) <= 1e-15, f"synthetic float mismatch row={i} field={field}")
    return {
        "verdict": "PASS_EXACT_SYNTHETIC_SUPPORT_CUT_EQUIVALENCE",
        "event_count": len(events),
        "candidate_count": len(original),
        "optimized_summary": opt_summary,
    }


def annual_degrees(neighbors: list[list[int]], years: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    is22 = years == 2022
    d22 = np.empty(len(neighbors), dtype=np.int32)
    d23 = np.empty(len(neighbors), dtype=np.int32)
    for i, ns in enumerate(neighbors):
        c22 = 0
        for j in ns:
            c22 += int(bool(is22[j]))
        d22[i] = c22
        d23[i] = len(ns) - c22
    return d22, d23


def write_m2d_binary(
    path: Path,
    candidates: list[dict[str, Any]],
    ordered_events: list[dict[str, Any]],
    neighbors: list[list[int]],
    leaf_labels: np.ndarray,
    leaf_owner: np.ndarray,
    d22: np.ndarray,
    d23: np.ndarray,
) -> dict[str, Any]:
    n_total = len(ordered_events)
    node_to_ci = {int(r["node"]): ci for ci, r in enumerate(candidates)}
    candidate_of = np.full(n_total, -1, dtype=np.int32)
    candidate_indices: list[list[int]] = [[] for _ in candidates]
    for g, lab in enumerate(leaf_labels.tolist()):
        owner = int(leaf_owner[int(lab)])
        ci = node_to_ci.get(owner, -1)
        if ci >= 0:
            candidate_of[g] = ci
            candidate_indices[ci].append(g)
    req(all(len(ix) == int(candidates[ci]["member_count"]) for ci, ix in enumerate(candidate_indices)), "candidate index transport mismatch")

    local_index = np.full(n_total, -1, dtype=np.int32)
    total_internal = 0
    total_cross = 0
    with path.open("wb") as f:
        f.write(b"OTIM1\0\0\0")
        f.write(struct.pack("<III", int(np.count_nonzero(np.asarray([e["year"] for e in ordered_events]) == 2022)), int(np.count_nonzero(np.asarray([e["year"] for e in ordered_events]) == 2023)), len(candidates)))
        for ci, inds in enumerate(candidate_indices):
            m = 0
            xn = 0
            for g in inds:
                for j in neighbors[g]:
                    if j == g:
                        continue
                    cj = int(candidate_of[j])
                    if cj == ci:
                        if j > g:
                            m += 1
                    else:
                        aa = min(int(d22[g]), int(d22[j]))
                        bb = min(int(d23[g]), int(d23[j]))
                        if aa > 0 and bb > 0:
                            xn += 1
            f.write(struct.pack("<III", len(inds), m, xn))
            for g in inds:
                f.write(struct.pack("<ii", int(d22[g]), int(d23[g])))
            for li, g in enumerate(inds):
                local_index[g] = li
            written_m = 0
            for g in inds:
                u = int(local_index[g])
                for j in neighbors[g]:
                    if j != g and int(candidate_of[j]) == ci and j > g:
                        v = int(local_index[j])
                        req(v >= 0, "internal local index missing")
                        f.write(struct.pack("<II", u, v))
                        written_m += 1
            req(written_m == m, f"internal edge write mismatch candidate {ci}")
            written_x = 0
            for g in inds:
                u = int(local_index[g])
                for j in neighbors[g]:
                    if j == g or int(candidate_of[j]) == ci:
                        continue
                    aa = min(int(d22[g]), int(d22[j]))
                    bb = min(int(d23[g]), int(d23[j]))
                    if aa > 0 and bb > 0:
                        f.write(struct.pack("<Iii", u, aa, bb))
                        written_x += 1
            req(written_x == xn, f"cross edge write mismatch candidate {ci}")
            for g in inds:
                local_index[g] = -1
            total_internal += m
            total_cross += xn
            if (ci + 1) % 250 == 0 or ci + 1 == len(candidates):
                print(f"[binary] candidates {ci+1}/{len(candidates)} internal={total_internal:,} cross={total_cross:,}", flush=True)
    return {"candidate_count": len(candidates), "total_internal_edges": total_internal, "total_boundary_edges": total_cross, "bytes": path.stat().st_size}


def parse_scores(path: Path, expected: int) -> dict[int, float]:
    lines = path.read_text().splitlines()
    req(lines and lines[0].startswith("candidate\t"), "bad M2D score header")
    out: dict[int, float] = {}
    for line in lines[1:]:
        p = line.split("\t")
        req(len(p) >= 5, "bad M2D score row")
        out[int(p[0])] = float(p[4])
    req(len(out) == expected and set(out) == set(range(expected)), "missing M2D candidate scores")
    req(all(np.isfinite(v) and v >= 0.0 for v in out.values()), "invalid M2D score")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--structural-source", type=Path, required=True)
    ap.add_argument("--support-source", type=Path, required=True)
    ap.add_argument("--exact-cpp", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(git_blob_sha(a.structural_source) == STRUCTURAL_BLOB, "structural source blob changed")
    req(git_blob_sha(a.support_source) == SUPPORT_BLOB, "support source blob changed")
    req(sha256_path(a.exact_cpp) == CPP_SHA256, "exact M2D C++ bytes changed")

    structural = load_module(a.structural_source, "m2d_blind_structural")
    support = load_module(a.support_source, "m2d_blind_support")
    req(float(structural.RADIUS) == RADIUS and int(structural.MIN_SUPPORT) == MIN_SUPPORT, "structural constants changed")
    req(float(support.RADIUS) == RADIUS and int(support.MIN_SUPPORT) == MIN_SUPPORT, "support constants changed")

    audit = equivalence_audit(structural, support)
    (a.output / "implementation_equivalence.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True), flush=True)

    blind_path = Path("/tmp/orbittrace_blind_loader.py")
    decode_blind_source(a.blind_source_parts, blind_path)
    blind = load_module(blind_path, "m2d_blind_loader")
    blind.YEARS = YEARS
    blind.MONTH_KEYS = MONTH_KEYS
    source_args = SimpleNamespace(candidate_payload=a.candidate_payload, baseline_payload=a.baseline_payload, scorer_parts=a.scorer_parts)
    _candidate, base, _scorer = blind.load_sources(source_args)
    by_year, sources = blind.parse_catalogue(base)
    req(sorted(by_year) == list(YEARS), f"wrong years loaded: {sorted(by_year)}")
    req([s["key"] for s in sources] == list(MONTH_KEYS), "monthly source sequence changed")

    events: list[dict[str, Any]] = []
    annual_counts: dict[str, int] = {}
    for year in YEARS:
        rows = list(by_year[year])
        annual_counts[str(year)] = len(rows)
        for r in rows:
            events.append({
                "id": str(r["id"]),
                "year": int(year),
                "sol": float(r["sol"]),
                "lon": float(r["sun_lon"]),
                "lat": float(r["ecl_lat"]),
                "vg": float(r["vg"]),
            })
    req(len(events) == sum(annual_counts.values()) and len({e["id"] for e in events}) == len(events), "event universe identity failure")
    req(all(e["year"] in YEARS for e in events), "unexpected year")
    print(f"[catalogue] full SPORADIC 2022+2023 events={len(events):,} annual={annual_counts}", flush=True)

    candidates, support_summary, neighbors, leaf_labels, leaf_owner, degrees = support_resolved_cut_linear(structural, events, keep_neighbors=True)
    req(neighbors is not None, "neighbors missing")
    ordered = sorted(events, key=lambda e: str(e["id"]))
    req(len(ordered) == len(neighbors) == len(leaf_labels), "ordered universe mismatch")
    years_arr = np.asarray([int(e["year"]) for e in ordered], dtype=np.int16)
    d22, d23 = annual_degrees(neighbors, years_arr)
    print(f"[support-cut] candidates={len(candidates):,} covered={support_summary['covered_event_count']:,} median_degree={support_summary['median_radius_degree']:.2f} p90={support_summary['p90_radius_degree']:.2f}", flush=True)

    binary = a.output / "m2d_input.bin"
    binary_summary = write_m2d_binary(binary, candidates, ordered, neighbors, leaf_labels, leaf_owner, d22, d23)
    del neighbors

    exe = a.output / "m2d_exact"
    subprocess.run(["g++", "-O3", "-std=c++17", str(a.exact_cpp), "-o", str(exe)], check=True)
    scores_path = a.output / "m2d_scores.tsv"
    stderr_path = a.output / "m2d_exact.stderr.txt"
    with stderr_path.open("wb") as err:
        subprocess.run([str(exe), str(binary), str(scores_path)], check=True, stderr=err)
    scores = parse_scores(scores_path, len(candidates))

    ranked: list[dict[str, Any]] = []
    for ci, row in enumerate(candidates):
        out = dict(row)
        out["internal_2d_mass"] = float(scores[ci])
        out.pop("rank", None)
        ranked.append(out)
    ranked.sort(key=lambda r: (-float(r["internal_2d_mass"]), -float(r["modal_contrast"]), str(r["family_hash"])))
    for rank, row in enumerate(ranked, 1):
        row["rank"] = rank

    payload = {
        "schema": "ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_PRETRUTH",
        "scientific_role": "TARGET_FREE_COMPLETE_M2D_RANKING_BEFORE_ORBITTRACE_REVEAL",
        "configuration": {
            "years": list(YEARS),
            "month_keys": list(MONTH_KEYS),
            "catalogue_filter": "SPORADIC",
            "target_interval_exclusion": None,
            "solar_halfwidth_deg": 5.0,
            "radiant_scale_deg": 4.0,
            "speed_multiplicative_scale": 1.1,
            "radius": RADIUS,
            "minimum_support": MIN_SUPPORT,
            "score": "M_2D(S)=(1/|S|)*sum_{B subseteq S}|B|A(B)",
            "ranking": ["internal_2d_mass_desc", "modal_contrast_desc", "family_hash_asc"],
        },
        "annual_event_counts": annual_counts,
        "event_count": len(ordered),
        "catalogue_sources": sources,
        "support_summary": support_summary,
        "binary_summary": binary_summary,
        "candidate_count": len(ranked),
        "candidates": ranked,
        "implementation_equivalence": audit,
        "source_identity": {
            "blind_loader_sha256": BLIND_SOURCE_SHA256,
            "structural_git_blob": STRUCTURAL_BLOB,
            "support_git_blob": SUPPORT_BLOB,
            "exact_cpp_sha256": CPP_SHA256,
        },
        "shower_truth_used": False,
        "orbittrace_target_information_access": False,
        "orbittrace_canonical_members_access": False,
        "prior_orbittrace_reveal_access": False,
        "post_result_parameter_search": False,
        "verdict": "BLIND_M2D_SCAN_FROZEN_AWAITING_SEPARATE_REVEAL",
    }
    inner = json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False).encode("utf-8")
    gz = gzip.compress(inner, compresslevel=9, mtime=0)
    ranked_path = a.output / "orbittrace_m2d_blind_ranked_pretruth.json.gz"
    ranked_path.write_bytes(gz)
    inner_sha = sha256_bytes(inner)
    gz_sha = sha256_bytes(gz)
    (a.output / "ranked_payload_sha256.txt").write_text(f"{inner_sha}  inner_json\n{gz_sha}  orbittrace_m2d_blind_ranked_pretruth.json.gz\n")

    lines = [
        "# M2D blind OrbitTrace rediscovery — pre-reveal scan",
        "",
        "Verdict: `BLIND_M2D_SCAN_FROZEN_AWAITING_SEPARATE_REVEAL`",
        "",
        "No OrbitTrace coordinate, interval, canonical member ID, HDBSCAN assignment, or prior reveal output was available to candidate generation or ranking.",
        "",
        f"- events: **{len(ordered):,}**",
        f"- candidates: **{len(ranked):,}**",
        f"- covered events: **{support_summary['covered_event_count']:,}**",
        f"- inner ranked payload SHA-256: `{inner_sha}`",
        "",
        "| rank | members | M2D | modal contrast | family hash |",
        "|---:|---:|---:|---:|---|",
    ]
    for row in ranked[:50]:
        lines.append(f"| {row['rank']} | {row['member_count']} | {row['internal_2d_mass']:.12g} | {row['modal_contrast']:.12g} | `{row['family_hash']}` |")
    (a.output / "M2D_BLIND_SCAN.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)

    # Large transport-only intermediates are not part of the evidence artifact.
    binary.unlink(missing_ok=True)
    exe.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

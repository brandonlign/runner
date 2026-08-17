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

EXPECTED_SOURCE_BLOB = "ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2"
THRESHOLD = 0.05
MIN_MEMBERS = 6
YEARS = (2013, 2014)
BLIND = (20.0, 55.0)


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("frozen_dsh_reference", path)
    require(spec is not None and spec.loader is not None, "cannot import frozen D_SH reference")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def wrap_pi(x: np.ndarray) -> np.ndarray:
    return (x + np.pi) % (2.0 * np.pi) - np.pi


def dsh_one_to_many(
    q0: float, e0: float, inc0: float, peri0: float, node0: float,
    q: np.ndarray, e: np.ndarray, inc: np.ndarray, peri: np.ndarray, node: np.ndarray,
) -> np.ndarray:
    # Exact Southworth-Hawkins formula matching the already-audited dense reference.
    node_delta = wrap_pi(node - node0)
    cos_i = math.cos(inc0) * np.cos(inc) + math.sin(inc0) * np.sin(inc) * np.cos(node_delta)
    mutual_i = np.arccos(np.clip(cos_i, -1.0, 1.0))
    denominator = np.cos(0.5 * mutual_i)
    numerator = np.cos(0.5 * (inc0 + inc)) * np.sin(0.5 * node_delta)
    ratio = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator),
        where=np.abs(denominator) > 1e-15,
    )
    peri_delta = wrap_pi(peri - peri0 + 2.0 * np.arcsin(np.clip(ratio, -1.0, 1.0)))
    q_delta = q0 - q
    e_delta = e0 - e
    plane = 2.0 * np.sin(0.5 * mutual_i)
    peri_term = 0.5 * (e0 + e) * 2.0 * np.sin(0.5 * peri_delta)
    out = np.sqrt(np.maximum(q_delta*q_delta + e_delta*e_delta + plane*plane + peri_term*peri_term, 0.0))
    require(np.all(np.isfinite(out)), "nonfinite D_SH distance")
    return out


class UnionFind:
    def __init__(self, n: int):
        self.parent = np.arange(n, dtype=np.int64)
        self.size = np.ones(n, dtype=np.int64)

    def find(self, x: int) -> int:
        p = self.parent
        r = int(x)
        while int(p[r]) != r:
            r = int(p[r])
        while int(p[x]) != x:
            nx = int(p[x]); p[x] = r; x = nx
        return r

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb] or (self.size[ra] == self.size[rb] and ra > rb):
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]


def cluster_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(rows, key=lambda r: str(r["id"]))
    n = len(ordered)
    ids = np.asarray([str(r["id"]) for r in ordered], dtype=object)
    q = np.asarray([float(r["q"]) for r in ordered], dtype=np.float64)
    e = np.asarray([float(r["e"]) for r in ordered], dtype=np.float64)
    inc = np.radians(np.asarray([float(r["inc"]) for r in ordered], dtype=np.float64))
    peri = np.radians(np.asarray([float(r["peri"]) for r in ordered], dtype=np.float64))
    node = np.radians(np.asarray([float(r["node"]) for r in ordered], dtype=np.float64))
    require(np.all(np.isfinite(np.column_stack((q, e, inc, peri, node)))), "nonfinite D_SH input")

    # q is a necessary lower-bound term of D_SH, so exact single-link edges can only
    # occur among points separated by strictly less than THRESHOLD in q. e is another
    # independent squared term and is applied as a second exact necessary prefilter.
    order_q = np.lexsort((np.arange(n), q))
    qs = q[order_q]
    uf = UnionFind(n)
    tested = 0
    edges = 0
    boundary_rechecks = 0

    for pos, i_raw in enumerate(order_q):
        i = int(i_raw)
        right = int(np.searchsorted(qs, q[i] + THRESHOLD, side="left"))
        if right <= pos + 1:
            continue
        js = order_q[pos + 1:right]
        if len(js) == 0:
            continue
        js = js[np.abs(e[js] - e[i]) < THRESHOLD]
        if len(js) == 0:
            continue
        d = dsh_one_to_many(q[i], e[i], inc[i], peri[i], node[i], q[js], e[js], inc[js], peri[js], node[js])
        tested += int(len(js))

        # The dense frozen reference explicitly symmetrizes to remove branch-level
        # floating roundoff. Only pairs within 1e-10 of the decision boundary need a
        # reference recheck; all others are many orders beyond numerical ambiguity.
        near = np.flatnonzero(np.abs(d - THRESHOLD) <= 1e-10)
        if len(near):
            boundary_rechecks += int(len(near))
            for k in near:
                j = int(js[int(k)])
                dd = dsh_one_to_many(q[j], e[j], inc[j], peri[j], node[j], q[[i]], e[[i]], inc[[i]], peri[[i]], node[[i]])[0]
                d[int(k)] = 0.5 * (float(d[int(k)]) + float(dd))

        for j_raw in js[d < THRESHOLD]:
            uf.union(i, int(j_raw)); edges += 1

    groups: dict[int, list[int]] = {}
    for i in range(n):
        r = uf.find(i)
        groups.setdefault(r, []).append(i)
    components = [ix for ix in groups.values() if len(ix) >= MIN_MEMBERS]

    families: list[dict[str, Any]] = []
    for ix in components:
        members = sorted(str(ids[i]) for i in ix)
        fid = "DSH" + hashlib.sha256(("|".join(members)).encode()).hexdigest()[:16]
        families.append({"family_id": fid, "member_ids": members, "member_count": len(members)})
    families.sort(key=lambda r: (-int(r["member_count"]), str(r["family_id"])))
    return families, {
        "event_count": n,
        "candidate_pairs_after_exact_q_e_prefilter": tested,
        "single_link_edges_dsh_lt_0_05": edges,
        "boundary_reference_rechecks": boundary_rechecks,
        "retained_family_count": len(families),
        "largest_family_count": max((int(x["member_count"]) for x in families), default=0),
    }


def numerical_audit(mod: Any) -> dict[str, Any]:
    # Deterministic synthetic orbit panel spanning wraparound and inclination cases.
    rng = np.random.default_rng(20140507)
    n = 96
    q = rng.uniform(0.05, 0.95, n)
    e = rng.uniform(0.05, 0.99, n)
    inc_deg = rng.uniform(0.0, 70.0, n)
    peri_deg = rng.uniform(0.0, 360.0, n)
    node_deg = rng.uniform(0.0, 360.0, n)
    dense = np.asarray(mod.pairwise_dsh(q, e, inc_deg, peri_deg, node_deg), dtype=np.float64)
    inc = np.radians(inc_deg); peri = np.radians(peri_deg); node = np.radians(node_deg)
    rebuilt = np.zeros_like(dense)
    for i in range(n):
        rebuilt[i] = dsh_one_to_many(q[i], e[i], inc[i], peri[i], node[i], q, e, inc, peri, node)
    rebuilt = 0.5 * (rebuilt + rebuilt.T); np.fill_diagonal(rebuilt, 0.0)
    delta = float(np.max(np.abs(dense - rebuilt)))
    require(delta <= 1e-12, f"D_SH scalable formula diverged from frozen dense reference: {delta}")
    require(np.array_equal(dense < THRESHOLD, rebuilt < THRESHOLD), "D_SH threshold decisions diverged in audit")
    return {"synthetic_n": n, "max_abs_distance_delta": delta, "threshold_edge_matrix_exact": True}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True, choices=list(YEARS))
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--reference-source", type=Path, required=True)
    ap.add_argument("--source-git-blob", required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    require(a.source_git_blob == EXPECTED_SOURCE_BLOB, "D_SH reference source blob changed")
    mod = load_module(a.reference_source)
    require(float(mod.RUD2014_DSH_THRESHOLD) == THRESHOLD, "published D_SH threshold changed")
    require(int(mod.RUD2014_MIN_MEMBERS) == MIN_MEMBERS, "published D_SH minimum membership changed")
    audit = numerical_audit(mod)

    rows = json.loads(a.rows.read_text())
    require(isinstance(rows, list) and rows, "empty D_SH rows")
    require(all(int(r["year"]) == a.year for r in rows), "wrong-year D_SH row")
    require(all(not (BLIND[0] <= float(r["sol"]) <= BLIND[1]) for r in rows), "protected row entered D_SH")
    require(all("shower" not in r and "truth" not in r for r in rows), "truth entered D_SH pretruth")
    families, diagnostics = cluster_rows(rows)

    result = {
        "schema": "ORBITTRACE_RUDAWSKA2014_DSH6_PRETRUTH_V1",
        "method": "Rudawska-Jenniskens D_SH single linkage",
        "year": int(a.year),
        "distance": "Southworth-Hawkins D_SH",
        "threshold_strict_lt": THRESHOLD,
        "minimum_members": MIN_MEMBERS,
        "retained_family_count": len(families),
        "families": families,
        "diagnostics": diagnostics,
        "numerical_audit": audit,
        "reference_source_git_blob": EXPECTED_SOURCE_BLOB,
        "reference_source_sha256": sha(a.reference_source),
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    output_sha = dump(a.output / "comparator_primary_output.json", result)
    dump(a.output / "comparator_source_manifest.json", {
        "method": result["method"],
        "year": a.year,
        "reference_source_git_blob": EXPECTED_SOURCE_BLOB,
        "reference_source_sha256": sha(a.reference_source),
        "threshold": THRESHOLD,
        "minimum_members": MIN_MEMBERS,
        "output_sha256": output_sha,
        "truth_accessed": False,
    })
    print(json.dumps({"year": a.year, "events": len(rows), "families": len(families), "diagnostics": diagnostics, "output_sha256": output_sha}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

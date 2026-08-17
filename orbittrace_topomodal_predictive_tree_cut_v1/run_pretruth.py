#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree

H_SOL = 2.0 * math.sin(math.radians(5.0) / 2.0)
H_RAD = 2.0 * math.sin(math.radians(4.0) / 2.0)
H_LOGV = math.log(1.1)
RADIUS = 1.0
MIN_SUPPORT = 4
SALT = "ORBITTRACE_TOPOMODAL_PREDICTIVE_TREE_CUT_V1|"
EXPECTED_TOPOMODAL_SHA256 = "7020ae01b9a3407a15baeca216a167f9d6963e84c7386150bfa24e70530672be"
EXPECTED_TOPOMODAL_MANIFEST_SHA256 = "762a49249b64f5352e7e92d101afd29484e917309b10f8f95a74f12d658f613e"
EXPECTED_ROW_SHA256 = {
    2013: "2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
    2014: "206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def member_hash(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()


def event_hash(eid: str) -> int:
    return int.from_bytes(hashlib.sha256((SALT + str(eid)).encode()).digest()[:8], "big")


def embedding(rows: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([float(r["sol"]) for r in rows], dtype=np.float64))
    lon = np.radians(np.asarray([float(r["sun_lon"]) for r in rows], dtype=np.float64))
    lat = np.radians(np.asarray([float(r["ecl_lat"]) for r in rows], dtype=np.float64))
    vg = np.asarray([float(r["vg"]) for r in rows], dtype=np.float64)
    require(np.all(np.isfinite(vg)) and np.all(vg > 0.0), "invalid speed")
    clat = np.cos(lat)
    z = np.column_stack([
        np.cos(sol) / H_SOL,
        np.sin(sol) / H_SOL,
        clat * np.cos(lon) / H_RAD,
        clat * np.sin(lon) / H_RAD,
        np.sin(lat) / H_RAD,
        np.log(vg) / H_LOGV,
    ])
    require(z.shape == (len(rows), 6) and np.all(np.isfinite(z)), "invalid embedding")
    return z


def projected_candidates(payload: dict[str, Any], annual_ids: list[str]) -> list[dict[str, Any]]:
    index = {eid: i for i, eid in enumerate(annual_ids)}
    unique: dict[tuple[int, ...], dict[str, Any]] = {}
    for fam in payload["families"]:
        ix = tuple(sorted(index[str(e)] for e in fam["event_ids"] if str(e) in index))
        if len(ix) < MIN_SUPPORT:
            continue
        row = unique.get(ix)
        if row is None:
            mids = [annual_ids[i] for i in ix]
            h = member_hash(mids)
            unique[ix] = {
                "annual_member_indices": ix,
                "event_ids": mids,
                "member_count": len(ix),
                "annual_membership_sha256": h,
                "source_family_ids": [str(fam["family_id"])],
                "minimum_original_topomodal_rank": int(fam["rank"]),
            }
        else:
            row["source_family_ids"].append(str(fam["family_id"]))
            row["minimum_original_topomodal_rank"] = min(int(row["minimum_original_topomodal_rank"]), int(fam["rank"]))
    rows = list(unique.values())
    for row in rows:
        row["source_family_ids"] = sorted(set(row["source_family_ids"]))
    require(rows, "no projected candidates")
    return rows


def build_laminar_forest(candidates: list[dict[str, Any]], n_events: int) -> tuple[list[int], list[list[int]], list[int], list[set[int]]]:
    sets = [set(map(int, c["annual_member_indices"])) for c in candidates]
    sizes = [len(s) for s in sets]
    inv: list[list[int]] = [[] for _ in range(n_events)]
    for i, s in enumerate(sets):
        for e in s:
            inv[e].append(i)
    for lst in inv:
        lst.sort(key=lambda i: (sizes[i], candidates[i]["annual_membership_sha256"]))
        for a, b in zip(lst, lst[1:]):
            require(sets[a].issubset(sets[b]), "annual projected hierarchy is not laminar")

    parent = [-1] * len(candidates)
    for i, s in enumerate(sets):
        anchor = min(s, key=lambda e: len(inv[e]))
        choices = [j for j in inv[anchor] if sizes[j] > sizes[i] and s.issubset(sets[j])]
        if choices:
            min_size = min(sizes[j] for j in choices)
            minimal = [j for j in choices if sizes[j] == min_size]
            require(len(minimal) == 1, "annual hierarchy parent is not unique")
            parent[i] = minimal[0]

    children = [[] for _ in candidates]
    roots: list[int] = []
    for i, p in enumerate(parent):
        if p < 0:
            roots.append(i)
        else:
            children[p].append(i)
    for i, kids in enumerate(children):
        seen: set[int] = set()
        for k in kids:
            require(seen.isdisjoint(sets[k]), "sibling candidate overlap")
            seen.update(sets[k])
            require(sets[k] < sets[i], "child is not strict subset of parent")
    return parent, children, roots, sets


def split_graph(annual_ids: list[str], z: np.ndarray) -> tuple[csr_matrix, csr_matrix, np.ndarray, np.ndarray, dict[str, Any]]:
    pairs = cKDTree(z).query_pairs(r=RADIUS, p=2.0, eps=0.0, output_type="ndarray")
    require(pairs.ndim == 2 and pairs.shape[1] == 2 and len(pairs) > 0, "empty physical edge graph")
    hashes = np.asarray([event_hash(eid) for eid in annual_ids], dtype=np.uint64)
    train = ((hashes[pairs[:, 0]] ^ hashes[pairs[:, 1]]) & np.uint64(1)) == np.uint64(0)
    require(np.any(train) and np.any(~train), "edge holdout split collapsed")
    shape = (len(annual_ids), len(annual_ids))
    atr = csr_matrix((np.ones(int(np.sum(train)), dtype=np.int8), (pairs[train, 0], pairs[train, 1])), shape=shape)
    ate = csr_matrix((np.ones(int(np.sum(~train)), dtype=np.int8), (pairs[~train, 0], pairs[~train, 1])), shape=shape)
    dtr = np.asarray(atr.sum(axis=0)).ravel() + np.asarray(atr.sum(axis=1)).ravel()
    dte = np.asarray(ate.sum(axis=0)).ravel() + np.asarray(ate.sum(axis=1)).ravel()
    return atr, ate, dtr.astype(np.float64), dte.astype(np.float64), {
        "physical_edge_count": int(len(pairs)),
        "training_edge_count": int(atr.nnz),
        "heldout_edge_count": int(ate.nnz),
    }


def expected_internal(degrees: np.ndarray, inds: np.ndarray, total_edges: int) -> float:
    if total_edges <= 0:
        return 0.0
    d = degrees[inds]
    vol = float(np.sum(d))
    lam = (vol * vol - float(np.dot(d, d))) / (4.0 * float(total_edges))
    return max(0.0, float(lam))


def score_candidates(candidates: list[dict[str, Any]], atr: csr_matrix, ate: csr_matrix, dtr: np.ndarray, dte: np.ndarray) -> None:
    mtr, mte = int(atr.nnz), int(ate.nnz)
    for c in candidates:
        inds = np.asarray(c["annual_member_indices"], dtype=np.int64)
        e_tr = int(atr[inds][:, inds].nnz)
        e_te = int(ate[inds][:, inds].nnz)
        l_tr = expected_internal(dtr, inds, mtr)
        l_te = expected_internal(dte, inds, mte)
        if l_tr <= 0.0 or l_te <= 0.0:
            alpha = 1.0
            gain = 0.0
        else:
            alpha = max(1.0, float(e_tr) / l_tr)
            gain = float(e_te) * math.log(alpha) - (alpha - 1.0) * l_te
        require(math.isfinite(alpha) and math.isfinite(gain), "nonfinite predictive score")
        c["training_internal_edges"] = e_tr
        c["heldout_internal_edges"] = e_te
        c["training_null_expected_internal_edges"] = l_tr
        c["heldout_null_expected_internal_edges"] = l_te
        c["training_enrichment_alpha"] = alpha
        c["heldout_predictive_gain"] = gain


def predictive_cut(candidates: list[dict[str, Any]], children: list[list[int]], roots: list[int], sets: list[set[int]]) -> list[int]:
    memo: dict[int, tuple[float, list[int]]] = {}
    def rec(i: int) -> tuple[float, list[int]]:
        if i in memo:
            return memo[i]
        child_value = 0.0
        child_selected: list[int] = []
        for j in children[i]:
            v, s = rec(j)
            child_value += v
            child_selected.extend(s)
        node_value = max(0.0, float(candidates[i]["heldout_predictive_gain"]))
        if node_value >= child_value:
            ans = (node_value, [i] if node_value > 0.0 else [])
        else:
            ans = (child_value, child_selected)
        memo[i] = ans
        return ans

    selected: list[int] = []
    for r in roots:
        selected.extend(rec(r)[1])
    require(selected, "predictive cut selected no candidates")
    owner: dict[int, int] = {}
    for i in selected:
        for e in sets[i]:
            require(e not in owner, "predictive antichain overlaps")
            owner[e] = i
    selected.sort(key=lambda i: (-float(candidates[i]["heldout_predictive_gain"]), str(candidates[i]["annual_membership_sha256"])))
    return selected


def run_year(year: int, rows_path: Path, topomodal: dict[str, Any]) -> dict[str, Any]:
    require(sha(rows_path) == EXPECTED_ROW_SHA256[year], f"annual row artifact changed {year}")
    raw = json.loads(rows_path.read_text())
    require(isinstance(raw, list) and raw, "empty annual rows")
    require(all(int(r["year"]) == year for r in raw), "wrong year in annual rows")
    require(all(not (20.0 <= float(r["sol"]) <= 55.0) for r in raw), "protected row entered selector")
    require(all("shower" not in r and "truth" not in r for r in raw), "truth field entered selector")
    ordered = sorted(raw, key=lambda r: str(r["id"]))
    annual_ids = [str(r["id"]) for r in ordered]
    require(len(annual_ids) == len(set(annual_ids)), "duplicate annual IDs")
    candidates = projected_candidates(topomodal, annual_ids)
    parent, children, roots, sets = build_laminar_forest(candidates, len(annual_ids))
    z = embedding(ordered)
    atr, ate, dtr, dte, graph_summary = split_graph(annual_ids, z)
    score_candidates(candidates, atr, ate, dtr, dte)
    selected = predictive_cut(candidates, children, roots, sets)

    out_candidates: list[dict[str, Any]] = []
    for rank, i in enumerate(selected, 1):
        c = candidates[i]
        require(float(c["heldout_predictive_gain"]) > 0.0, "nonpositive selected gain")
        out_candidates.append({
            "family_id": "tptc-" + str(c["annual_membership_sha256"])[:20],
            "rank": rank,
            "event_ids": list(c["event_ids"]),
            "member_count": int(c["member_count"]),
            "annual_membership_sha256": str(c["annual_membership_sha256"]),
            "source_family_ids": list(c["source_family_ids"]),
            "minimum_original_topomodal_rank": int(c["minimum_original_topomodal_rank"]),
            "training_internal_edges": int(c["training_internal_edges"]),
            "heldout_internal_edges": int(c["heldout_internal_edges"]),
            "training_null_expected_internal_edges": float(c["training_null_expected_internal_edges"]),
            "heldout_null_expected_internal_edges": float(c["heldout_null_expected_internal_edges"]),
            "training_enrichment_alpha": float(c["training_enrichment_alpha"]),
            "heldout_predictive_gain": float(c["heldout_predictive_gain"]),
        })
    require([c["rank"] for c in out_candidates] == list(range(1, len(out_candidates) + 1)), "rank discontinuity")
    return {
        "year": year,
        "annual_event_count": len(annual_ids),
        "annual_event_ids_sha256": member_hash(annual_ids),
        "projected_unique_hierarchy_candidate_count": len(candidates),
        "annual_hierarchy_root_count": len(roots),
        "selected_candidate_count": len(out_candidates),
        "graph_summary": graph_summary,
        "candidates": out_candidates,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topomodal", type=Path, required=True)
    ap.add_argument("--topomodal-manifest", type=Path, required=True)
    ap.add_argument("--rows-2013", type=Path, required=True)
    ap.add_argument("--rows-2014", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--scientific-source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    require(sha(a.topomodal) == EXPECTED_TOPOMODAL_SHA256, "frozen TopoModal candidate output changed")
    require(sha(a.topomodal_manifest) == EXPECTED_TOPOMODAL_MANIFEST_SHA256, "frozen TopoModal manifest changed")
    topomodal = json.loads(a.topomodal.read_text())
    require(topomodal.get("method") == "fixed-scale TopoModal flagship", "wrong TopoModal method")
    require(topomodal.get("truth_accessed") is False and topomodal.get("target_information_access") is False, "Topomodal input not pretruth")

    panels = [run_year(2013, a.rows_2013, topomodal), run_year(2014, a.rows_2014, topomodal)]
    result = {
        "schema": "ORBITTRACE_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_PRETRUTH",
        "method": "OrbitTrace TopoModal Predictive Tree Cut v1",
        "scientific_role": "EXPOSED_SONOTACO_2013_2014_SELECTOR_DEVELOPMENT_PRETRUTH",
        "topomodal_primary_output_sha256": EXPECTED_TOPOMODAL_SHA256,
        "topomodal_source_manifest_sha256": EXPECTED_TOPOMODAL_MANIFEST_SHA256,
        "protocol_sha256": sha(a.protocol),
        "scientific_source_sha256": sha(a.scientific_source),
        "configuration": {
            "radius": RADIUS,
            "h_sol": H_SOL,
            "h_rad": H_RAD,
            "h_logv": H_LOGV,
            "min_support": MIN_SUPPORT,
            "edge_split": "xor_parity_of_sha256_event_hash",
            "null": "degree_preserving_configuration_expectation",
            "training_enrichment": "max(1,e_internal_train/lambda_train)",
            "heldout_score": "poisson_log_likelihood_gain",
            "flat_extraction": "node_vs_sum_optimal_children_dynamic_program",
            "ranking": "descending_heldout_predictive_gain_then_membership_sha256",
        },
        "panels": panels,
        "blind_exclusion": [20.0, 55.0],
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    primary_sha = dump(a.output / "selector_primary_output.json", result)
    manifest = {
        "method": result["method"],
        "selector_primary_output_sha256": primary_sha,
        "topomodal_primary_output_sha256": EXPECTED_TOPOMODAL_SHA256,
        "topomodal_source_manifest_sha256": EXPECTED_TOPOMODAL_MANIFEST_SHA256,
        "protocol_sha256": result["protocol_sha256"],
        "scientific_source_sha256": result["scientific_source_sha256"],
        "truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
    }
    manifest_sha = dump(a.output / "selector_source_manifest.json", manifest)
    print(json.dumps({
        "verdict": "PASS_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_PRETRUTH_GENERATION",
        "selector_primary_output_sha256": primary_sha,
        "selector_source_manifest_sha256": manifest_sha,
        "panels": [{
            "year": p["year"],
            "projected": p["projected_unique_hierarchy_candidate_count"],
            "selected": p["selected_candidate_count"],
            **p["graph_summary"],
        } for p in panels],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

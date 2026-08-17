#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
DENOMINATORS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
MIN_SUPPORT = 4
RADIUS = 1.0
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
REFERENCE_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
REFERENCE_SOURCE_BLOB = "c1efa8da34dea140726a4c2fe4943eb29a304538"
PARENT_SOURCE_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
EXPECTED_EVENTS = 738682


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    import subprocess
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def membership_hash(members: tuple[str, ...]) -> str:
    return hashlib.sha256(("\n".join(members) + "\n").encode()).hexdigest()


class DSU:
    def __init__(self, n: int) -> None:
        self.parent = np.arange(n, dtype=np.int64)
        self.size = np.ones(n, dtype=np.int64)

    def find(self, x: int) -> int:
        p = self.parent
        while int(p[x]) != x:
            p[x] = p[int(p[x])]
            x = int(p[x])
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if int(self.size[ra]) < int(self.size[rb]):
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]


def widths_from_positive_integer_levels(levels: np.ndarray, denominator: int) -> tuple[list[int], dict[int, float]]:
    vals = sorted({int(x) for x in levels if int(x) > 0}, reverse=True)
    req(vals, "annual density coordinate has no positive levels")
    widths: dict[int, float] = {}
    for i, v in enumerate(vals):
        nxt = vals[i + 1] if i + 1 < len(vals) else 0
        w = float(v - nxt) / float(denominator)
        req(w > 0.0 and math.isfinite(w), "invalid threshold-cell width")
        widths[v] = w
    return vals, widths


def build_fixed_graph(ref: Any, events: list[dict[str, Any]]) -> tuple[list[str], list[list[int]], np.ndarray, np.ndarray, dict[str, Any]]:
    ordered = sorted(events, key=lambda e: str(e["id"]))
    ids = [str(e["id"]) for e in ordered]
    years = np.asarray([int(e["year"]) for e in ordered], dtype=np.int64)
    req(set(map(int, np.unique(years))) == set(YEARS), "subset does not contain both years")
    z = ref.physical_embedding(ordered)
    tree = cKDTree(z)
    raw = tree.query_ball_point(z, r=RADIUS, p=2.0, eps=0.0, return_sorted=True)
    neighbors = [list(map(int, row)) for row in raw]
    adjacency = [set(row) for row in neighbors]
    for i, row in enumerate(neighbors):
        req(i in row, f"self missing at {i}")
        req(all(0 <= j < len(ids) for j in row), "graph index out of range")
        req(all(i in adjacency[j] for j in row), "graph not symmetric")
    n22 = int(np.sum(years == 2022))
    n23 = int(np.sum(years == 2023))
    req(n22 > 0 and n23 > 0, "zero annual subset size")
    d22 = np.asarray([sum(years[j] == 2022 for j in row) for row in neighbors], dtype=np.int64)
    d23 = np.asarray([sum(years[j] == 2023 for j in row) for row in neighbors], dtype=np.int64)
    req(np.all(d22 >= 0) and np.all(d23 >= 0), "negative annual degree")
    req(np.all(d22 + d23 == np.asarray([len(r) for r in neighbors], dtype=np.int64)), "annual degrees do not partition radius degree")
    return ids, neighbors, d22, d23, {
        "event_count": len(ids),
        "events_2022": n22,
        "events_2023": n23,
        "zero_fraction_rho22": float(np.mean(d22 == 0)),
        "zero_fraction_rho23": float(np.mean(d23 == 0)),
        "positive_both_fraction": float(np.mean((d22 > 0) & (d23 > 0))),
        "median_total_radius_degree": float(np.median(d22 + d23)),
        "p90_total_radius_degree": float(np.quantile(d22 + d23, 0.90)),
    }


def bifiltration_candidates(ref: Any, events: list[dict[str, Any]]) -> tuple[list[frozenset[str]], list[dict[str, Any]], dict[str, Any]]:
    ids, neighbors, d22, d23, graph_summary = build_fixed_graph(ref, events)
    n = len(ids)
    n22 = int(graph_summary["events_2022"])
    n23 = int(graph_summary["events_2023"])
    levels22, widths22 = widths_from_positive_integer_levels(d22, n22)
    levels23, widths23 = widths_from_positive_integer_levels(d23, n23)

    by22: dict[int, list[int]] = defaultdict(list)
    for i, value in enumerate(d22):
        if int(value) > 0:
            by22[int(value)].append(i)

    area: dict[tuple[str, ...], float] = defaultdict(float)
    cell_count: dict[tuple[str, ...], int] = defaultdict(int)
    threshold_pair_count = 0
    reportable_component_instances = 0

    for k23 in levels23:
        eligible = d23 >= int(k23)
        dsu = DSU(n)
        active = np.zeros(n, dtype=bool)
        active_list: list[int] = []
        for k22 in levels22:
            newly = [i for i in by22.get(int(k22), []) if bool(eligible[i])]
            for i in newly:
                active[i] = True
                active_list.append(i)
            for i in newly:
                for j in neighbors[i]:
                    if j != i and bool(active[j]):
                        dsu.union(i, int(j))

            threshold_pair_count += 1
            if not active_list:
                continue
            groups: dict[int, list[str]] = defaultdict(list)
            for i in active_list:
                groups[dsu.find(i)].append(ids[i])
            cell_area = widths22[int(k22)] * widths23[int(k23)]
            req(cell_area > 0.0 and math.isfinite(cell_area), "invalid bifiltration cell area")
            for members_list in groups.values():
                if len(members_list) < MIN_SUPPORT:
                    continue
                members = tuple(sorted(members_list))
                area[members] += cell_area
                cell_count[members] += 1
                reportable_component_instances += 1

    req(area, "bifiltration produced no positive-area reportable component")
    rows: list[dict[str, Any]] = []
    candidate_sets: list[frozenset[str]] = []
    for members, a in area.items():
        req(a > 0.0 and math.isfinite(a), "nonpositive/nonfinite persistence area")
        h = membership_hash(members)
        rows.append({
            "family_hash": h,
            "member_count": len(members),
            "persistence_area": float(a),
            "threshold_cell_count": int(cell_count[members]),
            "event_ids": list(members),
        })
    rows.sort(key=lambda r: (-float(r["persistence_area"]), -int(r["member_count"]), str(r["family_hash"])))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
        candidate_sets.append(frozenset(str(x) for x in row["event_ids"]))

    areas = np.asarray([float(r["persistence_area"]) for r in rows], dtype=float)
    counts = np.asarray([int(r["member_count"]) for r in rows], dtype=int)
    graph_summary.update({
        "candidate_count": len(rows),
        "rho22_positive_level_count": len(levels22),
        "rho23_positive_level_count": len(levels23),
        "threshold_pair_count": threshold_pair_count,
        "reportable_component_instances": reportable_component_instances,
        "persistence_area_sum": float(np.sum(areas)),
        "persistence_area_median": float(np.median(areas)),
        "persistence_area_max": float(np.max(areas)),
        "largest_candidate_count": int(np.max(counts)),
        "largest_candidate_fraction": float(np.max(counts) / len(ids)),
        "candidate_rows": [
            {k: row[k] for k in ("family_hash", "rank", "member_count", "persistence_area", "threshold_cell_count")}
            for row in rows
        ],
    })
    return candidate_sets, rows, graph_summary


def area_weighted_best_jaccard(fine: list[frozenset[str]], fine_rows: list[dict[str, Any]], coarse: list[frozenset[str]], fine_universe: frozenset[str], ref: Any) -> float:
    restricted = ref.restrict_and_dedupe(coarse, fine_universe)
    if not fine:
        return 0.0
    weights = np.asarray([float(r["persistence_area"]) for r in fine_rows], dtype=float)
    req(len(weights) == len(fine) and np.all(weights > 0.0), "area weight alignment")
    vals = []
    for a in fine:
        best = 0.0
        for b in restricted:
            inter = len(a.intersection(b))
            if inter:
                best = max(best, float(inter / len(a.union(b))))
        vals.append(best)
    return float(np.average(np.asarray(vals, dtype=float), weights=weights))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference-source", type=Path, required=True)
    ap.add_argument("--reference-result", type=Path, required=True)
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

    req(git_blob(a.reference_source) == REFERENCE_SOURCE_BLOB, "#1284 structural source changed")
    req(git_blob(a.parent_runner) == PARENT_SOURCE_BLOB, "recurrent parent source changed")
    req(sha256(a.reference_result) == REFERENCE_RESULT_SHA256, "#1284 structural result changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "GMN utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "GMN support result changed")

    ref = load_module(a.reference_source, "bifiltration_reference")
    parent = load_module(a.parent_runner, "bifiltration_parent")
    reference_result = json.loads(a.reference_result.read_text())
    req(reference_result.get("scientific_role") == "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY", "wrong reference role")
    req(reference_result.get("interpretation") == "SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE", "#1284 structural prerequisite not positive")

    qmod = load_module(a.quality_source, "bifiltration_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-annual-density-bifiltration-scale-v1-target-excluded"
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
        norm = [parent.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), f"normalization count changed {year}")
        events.extend(norm)
    req(len(events) == EXPECTED_EVENTS, f"pooled event count changed: {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")

    xfull = parent.geo_matrix(events)
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    ids_full = [str(e["id"]) for e in events]
    hashes = np.asarray([ref.event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    fits: list[dict[str, Any]] = []
    sets_by_key: dict[tuple[int, int], list[frozenset[str]]] = {}
    rows_by_key: dict[tuple[int, int], list[dict[str, Any]]] = {}
    recurrent_by_key: dict[tuple[int, int], list[frozenset[str]]] = {}
    ids_by_key: dict[tuple[int, int], frozenset[str]] = {}

    for denominator in DENOMINATORS:
        for bucket in BUCKETS:
            ix = ref.selected_indices(hashes, denominator, bucket)
            sub_events = [events[int(i)] for i in ix]
            sub_ids = [ids_full[int(i)] for i in ix]
            sub_x = np.asarray(xfull[ix], dtype=float)
            sub_years = np.asarray(years_full[ix], dtype=np.int64)
            req(len(sub_events) > 0, "empty subset")
            req(all(np.any(sub_years == y) for y in YEARS), "subset lost annual view")

            candidates, rows, summary = bifiltration_candidates(ref, sub_events)
            recurrent, recurrent_summary = ref.recurrent_candidates(parent, sub_x, sub_years, sub_ids)
            key = (denominator, bucket)
            sets_by_key[key] = candidates
            rows_by_key[key] = rows
            recurrent_by_key[key] = recurrent
            ids_by_key[key] = frozenset(sub_ids)
            fits.append({
                "denominator": denominator,
                "bucket": bucket,
                "events_total": len(sub_ids),
                "events_by_year": {str(y): int(np.sum(sub_years == y)) for y in YEARS},
                "bifiltration": summary,
                "recurrent_eom": recurrent_summary,
            })
            print(json.dumps({
                "d": denominator,
                "b": bucket,
                "n": len(sub_ids),
                "bifiltration_candidates": len(candidates),
                "recurrent_candidates": len(recurrent),
                "positive_both_fraction": summary["positive_both_fraction"],
                "levels": [summary["rho22_positive_level_count"], summary["rho23_positive_level_count"]],
            }, sort_keys=True), flush=True)

    nested: list[dict[str, Any]] = []
    bif_scores: list[float] = []
    rec_scores: list[float] = []
    strict_wins = 0
    fine_noncollapse = 0
    for bucket in BUCKETS:
        coarse_key = (128, bucket)
        fine_key = (1024, bucket)
        fine_universe = ids_by_key[fine_key]
        bm = ref.cross_scale_metrics(sets_by_key[coarse_key], sets_by_key[fine_key], fine_universe)
        rm = ref.cross_scale_metrics(recurrent_by_key[coarse_key], recurrent_by_key[fine_key], fine_universe)
        bw = area_weighted_best_jaccard(sets_by_key[fine_key], rows_by_key[fine_key], sets_by_key[coarse_key], fine_universe, ref)
        bscore = float(bm["fine_to_coarse_mean_best_jaccard"])
        rscore = float(rm["fine_to_coarse_mean_best_jaccard"])
        bif_scores.append(bscore)
        rec_scores.append(rscore)
        strict_wins += int(bscore > rscore)
        fine_noncollapse += int(len(sets_by_key[fine_key]) >= len(recurrent_by_key[fine_key]))
        nested.append({
            "bucket": bucket,
            "bifiltration": bm,
            "recurrent_eom": rm,
            "bifiltration_area_weighted_best_jaccard_reporting_only": bw,
            "strict_bifiltration_win": bscore > rscore,
            "fine_candidate_noncollapse": len(sets_by_key[fine_key]) >= len(recurrent_by_key[fine_key]),
        })

    b = np.asarray(bif_scores, dtype=float)
    r = np.asarray(rec_scores, dtype=float)
    gates = {
        "nonempty_all_eight_subsets": all(len(sets_by_key[(d, k)]) > 0 for d in DENOMINATORS for k in BUCKETS),
        "fine_candidate_noncollapse_all_four": fine_noncollapse == 4,
        "pooled_mean_best_jaccard_strictly_greater_than_recurrent": float(np.mean(b)) > float(np.mean(r)),
        "median_bucket_best_jaccard_strictly_greater_than_recurrent": float(np.median(b)) > float(np.median(r)),
        "strict_bucket_wins_at_least_3_of_4": strict_wins >= 3,
    }
    interpretation = "SUPPORTS_ANNUAL_DENSITY_BIFILTRATION_CROSS_SCALE_COHERENCE" if all(gates.values()) else "REFUTES_ANNUAL_DENSITY_BIFILTRATION_CROSS_SCALE_COHERENCE"

    pretruth = {
        "schema": "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_PRETRUTH_V1",
        "scientific_role": "ZERO_LABEL_BIFILTRATION_CANDIDATE_FREEZE",
        "configuration": {
            "years": list(YEARS),
            "denominators": list(DENOMINATORS),
            "buckets": list(BUCKETS),
            "radius": RADIUS,
            "min_support": MIN_SUPPORT,
            "density_coordinates": ["annual_radius_degree_over_annual_N_2022", "annual_radius_degree_over_annual_N_2023"],
            "candidate_rule": "all_support_ge_4_connected_components_over_all_positive_joint_superlevel_cells_dedup_exact_membership",
            "canonical_rank": ["persistence_area_desc", "member_count_desc", "membership_sha256_asc"],
        },
        "subsets": [
            {
                "denominator": d,
                "bucket": k,
                "candidates": rows_by_key[(d, k)],
            }
            for d in DENOMINATORS for k in BUCKETS
        ],
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    pretruth_sha = dump(a.output / "ANNUAL_DENSITY_BIFILTRATION_PRETRUTH_V1.json", pretruth)

    result = {
        "schema": "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_SCALE_V1",
        "scientific_role": "ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY",
        "interpretation": interpretation,
        "pretruth_sha256": pretruth_sha,
        "configuration": pretruth["configuration"],
        "fits": fits,
        "nested_pairs": nested,
        "summary": {
            "bifiltration_pooled_fine_to_coarse_mean_best_jaccard": float(np.mean(b)),
            "recurrent_pooled_fine_to_coarse_mean_best_jaccard": float(np.mean(r)),
            "bifiltration_median_bucket_mean_best_jaccard": float(np.median(b)),
            "recurrent_median_bucket_mean_best_jaccard": float(np.median(r)),
            "strict_bifiltration_bucket_wins": strict_wins,
            "fine_candidate_noncollapse_buckets": fine_noncollapse,
            "gates": gates,
        },
        "blind_exclusion": list(BLIND),
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
        "post_result_parameter_search": False,
    }
    result_sha = dump(a.output / "ANNUAL_DENSITY_BIFILTRATION_SCALE_V1.json", result)
    print(json.dumps({"interpretation": interpretation, "pretruth_sha256": pretruth_sha, "result_sha256": result_sha, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

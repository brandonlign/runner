#!/usr/bin/env python3
"""Development lab for label-free consensus consolidation of recurrent stream fragments.

Uses the exact frozen P19+P20 pre-label proposal union on target-excluded GMN 2022/2023.
P19/P20 remain no-gos. This asks whether cross-generator agreement in two-year hypothesis
space can collapse fragment crowds into a useful catalogue without a learned ranker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
CORPUS = "orbittrace-urc-consensus-consolidation-lab-v1"
BLIND = (20.0, 55.0)
P19_RESULT_SHA = "6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319"
P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
P20_RESULT_SHA = "9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303"
P20_PRELABEL_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"
EXPECTED = (226, 1075, 3203, 4504)
RADII = (0.25, 0.50, 0.75, 1.00, 1.50)
QUALITY_WEIGHTS = (0.0, 0.5, 1.0, 2.0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--p19-result-json", type=Path, required=True)
    p.add_argument("--p19-prelabel-json", type=Path, required=True)
    p.add_argument("--p20-result-json", type=Path, required=True)
    p.add_argument("--p20-prelabel-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def circular_diff(a: float, b: float) -> float:
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def pair_distance(a: dict[str, Any], b: dict[str, Any], support: Any, base: Any) -> float:
    ds = []
    for year in YEARS:
        ca = a.get("centroids", {}).get(str(year))
        cb = b.get("centroids", {}).get(str(year))
        if ca is None or cb is None:
            return math.inf
        ds.append(float(support.centroid_distance(ca, cb, base)))
    return max(ds)


def candidate_bins(families: list[dict[str, Any]]) -> dict[int, list[int]]:
    bins: dict[int, list[int]] = defaultdict(list)
    for i, f in enumerate(families):
        c = f.get("centroids", {}).get("2022")
        require(c is not None, f"missing 2022 centroid: {f['family_id']}")
        bins[int(math.floor(float(c["sol"]))) % 360].append(i)
    return bins


def build_edges(families: list[dict[str, Any]], support: Any, base: Any) -> list[tuple[float, int, int]]:
    bins = candidate_bins(families)
    edges: list[tuple[float, int, int]] = []
    seen: set[tuple[int, int]] = set()
    for i, f in enumerate(families):
        c = f["centroids"]["2022"]
        center = int(math.floor(float(c["sol"]))) % 360
        for off in range(-7, 8):
            for j in bins.get((center + off) % 360, []):
                if j <= i or (i, j) in seen:
                    continue
                seen.add((i, j))
                g = families[j]
                c2 = g["centroids"]["2022"]
                if circular_diff(c["sol"], c2["sol"]) > 7.0:
                    continue
                if abs(float(c["ecl_lat"]) - float(c2["ecl_lat"])) > 4.0:
                    continue
                if abs(float(c["vg"]) - float(c2["vg"])) > 4.0:
                    continue
                d = pair_distance(f, g, support, base)
                if d <= max(RADII):
                    edges.append((float(d), i, j))
    return edges


def source_rank_percentiles(sources: list[str]) -> list[float]:
    totals = Counter(sources)
    seen = Counter()
    out = []
    for src in sources:
        seen[src] += 1
        out.append((seen[src] - 1) / max(totals[src] - 1, 1))
    return out


def adjacency(n: int, edges: list[tuple[float, int, int]], radius: float) -> list[set[int]]:
    out = [set([i]) for i in range(n)]
    for d, i, j in edges:
        if d <= radius:
            out[i].add(j)
            out[j].add(i)
    return out


def greedy_consensus_order(
    families: list[dict[str, Any]],
    sources: list[str],
    source_pct: list[float],
    adj: list[set[int]],
    quality_weight: float,
) -> tuple[list[str], dict[str, Any]]:
    scores = []
    for i, f in enumerate(families):
        nb = adj[i]
        nb_sources = {sources[j] for j in nb}
        cross = sum(sources[j] != sources[i] for j in nb)
        degree = len(nb) - 1
        # Cross-generator recurrence agreement is primary. Source-order percentile is
        # only a within-generator quality tie-breaker, and no truth enters this score.
        s = (
            3.0 * (len(nb_sources) - 1)
            + 1.5 * math.log1p(cross)
            + 0.35 * math.log1p(degree)
            - quality_weight * source_pct[i]
        )
        scores.append((s, len(nb_sources), cross, degree, -source_pct[i], str(f["family_id"]), i))
    scores.sort(reverse=True)

    kept: list[int] = []
    removed: set[int] = set()
    cluster_sizes = []
    cluster_source_counts = []
    for _s, _ns, _cross, _deg, _q, _fid, i in scores:
        if i in removed:
            continue
        kept.append(i)
        cluster = adj[i] - removed
        cluster_sizes.append(len(cluster))
        cluster_source_counts.append(len({sources[j] for j in cluster}))
        removed.update(cluster)
    order = [str(families[i]["family_id"]) for i in kept]
    return order, {
        "input": len(families),
        "kept": len(kept),
        "suppressed": len(families) - len(kept),
        "median_cluster_size": float(np.median(cluster_sizes)) if cluster_sizes else 0.0,
        "max_cluster_size": max(cluster_sizes, default=0),
        "clusters_with_multiple_generators": sum(x >= 2 for x in cluster_source_counts),
        "clusters_with_all_three_generators": sum(x >= 3 for x in cluster_source_counts),
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for path, expected, name in (
        (args.p19_result_json, P19_RESULT_SHA, "P19 result"),
        (args.p19_prelabel_json, P19_PRELABEL_SHA, "P19 prelabel"),
        (args.p20_result_json, P20_RESULT_SHA, "P20 result"),
        (args.p20_prelabel_json, P20_PRELABEL_SHA, "P20 prelabel"),
    ):
        require(sha(path) == expected, f"{name} hash changed")
    r19 = json.loads(args.p19_result_json.read_text())
    r20 = json.loads(args.p20_result_json.read_text())
    require(r19["verdict"].startswith("FAIL_P19_"), "P19 identity changed")
    require(r20["verdict"] == "FAIL_P20_RECURRENT_ISOLATED_QUARTET_DEVELOPMENT", "P20 identity changed")
    a = json.loads(args.p19_prelabel_json.read_text())
    b = json.loads(args.p20_prelabel_json.read_text())
    hard = a["hard_families"]
    p19 = a["soft_families"]
    p20 = b["soft_families"]
    require(a["hard_families"] == b["hard_families"], "hard universe differs")
    require(a["hard_order"] == b["hard_order"], "hard order differs")
    require((len(hard), len(p19), len(p20), len(hard)+len(p19)+len(p20)) == EXPECTED, "candidate counts changed")
    families = hard + p19 + p20
    sources = ["hard"] * len(hard) + ["p19"] * len(p19) + ["p20"] * len(p20)
    ids = [str(f["family_id"]) for f in families]
    require(len(ids) == len(set(ids)), "family IDs duplicate")

    v1.mult.YEARS = YEARS
    v1.mult.MONTH_KEYS = MONTH_KEYS
    v1.mult.TOP_K = 100
    runtime = v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    require((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target exclusion changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, base, _scorer = support.load_sources(args)
    scan_by_year, _cal, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "years changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "months changed")

    eligible = v1.eligible_labels(hidden_labels)
    truths = {str(f["family_id"]): v1.family_truth(f, hidden_labels, eligible) for f in families}
    hard_order = [str(x) for x in a["hard_order"]]
    hard_metrics = v1.monotone_metrics(hard, hard_order, truths, eligible)
    union_metrics = v1.monotone_metrics(families, ids, truths, eligible)

    # Edge construction is fully label-free; labels above are never passed into it.
    edges = build_edges(families, support, base)
    source_pct = source_rank_percentiles(sources)
    rows = []
    best = None
    for radius in RADII:
        adj = adjacency(len(families), edges, radius)
        for qw in QUALITY_WEIGHTS:
            order, diag = greedy_consensus_order(families, sources, source_pct, adj, qw)
            metrics = v1.monotone_metrics(families, order, truths, eligible)
            passed = (
                metrics["recovered_at_100"] >= 70
                and metrics["recovered_at_50"] >= hard_metrics["recovered_at_50"]
                and metrics["top100_dominant_precision"] >= hard_metrics["top100_dominant_precision"] - 0.05
                and metrics["qualified_matches"] >= 180
                and metrics["mean_qualified_candidates_per_recovered_label"] <= 3.0
            )
            row = {
                "radius": radius,
                "source_quality_weight": qw,
                "pass": bool(passed),
                "consolidation": diag,
                "metrics": {k:v for k,v in metrics.items() if k != "first_rank_by_label"},
            }
            rows.append(row)
            key = (
                metrics["recovered_at_100"], metrics["recovered_at_50"],
                metrics["top100_dominant_precision"], -metrics["mean_qualified_candidates_per_recovered_label"],
                metrics["mrr"], -diag["kept"],
            )
            if best is None or key > best["key"]:
                best = {"key": key, "row": row, "order": order}
    require(best is not None, "no consensus candidates")
    pass_count = sum(r["pass"] for r in rows)
    verdict = "PASS_URC_LABEL_FREE_CONSENSUS_CONSOLIDATION_FEASIBILITY" if pass_count >= 3 else "FAIL_URC_LABEL_FREE_CONSENSUS_CONSOLIDATION_FEASIBILITY"
    result = {
        "verdict": verdict,
        "scope": "GMN 2022/2023 target-excluded label-free family-of-families consensus lab",
        "candidate_universe": {"hard":len(hard), "p19_soft":len(p19), "p20_soft":len(p20), "union":len(families)},
        "hard_baseline": {k:v for k,v in hard_metrics.items() if k != "first_rank_by_label"},
        "append_union_diagnostic": {k:v for k,v in union_metrics.items() if k != "first_rank_by_label"},
        "edge_count_within_1_5": len(edges),
        "best": {**best["row"], "order_sha256": hashlib.sha256("\n".join(best["order"]).encode()).hexdigest()},
        "robustness": {"tested":len(rows), "passing":pass_count},
        "grid": rows,
        "integrity": {
            "edge_and_consensus_construction_label_free": True,
            "candidate_generation_recomputed": False,
            "candidate_membership_changed": False,
            "sonotaco_2013_2014_access": False,
            "maarsy_scientific_access": False,
            "target_information_access": False,
        },
        "claim_boundary": "Development feasibility only; PASS would support consensus consolidation as a component of a new integrated URC, not revive P19/P20.",
    }
    (args.output / "urc_consensus_consolidation_lab_v1.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
    (args.output / "URC_CONSENSUS_CONSOLIDATION_LAB_V1.md").write_text(
        "# URC label-free consensus consolidation lab v1\n\n"
        f"- verdict: `{verdict}`\n"
        f"- hard r100/r50: `{hard_metrics['recovered_at_100']}/{hard_metrics['recovered_at_50']}`\n"
        f"- best r100/r50: `{best['row']['metrics']['recovered_at_100']}/{best['row']['metrics']['recovered_at_50']}`\n"
        f"- best top100 precision: `{best['row']['metrics']['top100_dominant_precision']:.6f}`\n"
        f"- best qualified: `{best['row']['metrics']['qualified_matches']}`\n"
        f"- best duplicate burden: `{best['row']['metrics']['mean_qualified_candidates_per_recovered_label']:.3f}`\n"
        f"- kept families: `{best['row']['consolidation']['kept']}`\n"
        f"- passing variants: `{pass_count}/{len(rows)}`\n"
    )
    print(json.dumps({
        "verdict":verdict,
        "best_radius":best["row"]["radius"],
        "best_quality_weight":best["row"]["source_quality_weight"],
        "best_r100":best["row"]["metrics"]["recovered_at_100"],
        "best_r50":best["row"]["metrics"]["recovered_at_50"],
        "best_precision":best["row"]["metrics"]["top100_dominant_precision"],
        "best_qualified":best["row"]["metrics"]["qualified_matches"],
        "best_duplicate_burden":best["row"]["metrics"]["mean_qualified_candidates_per_recovered_label"],
        "passing":pass_count,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

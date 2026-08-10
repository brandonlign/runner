#!/usr/bin/env python3
"""GMN-development lab: preserve the exact URC union rank and merge fragment memberships only.

The candidate universe and selected ranking are frozen by PR #839. This lab never changes
candidate existence or rank. It asks whether geometrically coincident fragments can provide
label-free member evidence for the same already-ranked hypotheses.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import numpy as np

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
CORPUS = "orbittrace-urc-ranked-membership-merge-lab-v1"

EXPECTED_UNION_RESULT_SHA = "e932ad2507f6305a96c9d442a556593e470c966f1adfc2f4f2098adbc8f9dbcd"
EXPECTED_ORDER_SHA = "ffc97f7bc4fbc8f13170ffe8a71260e1596190e39e9324c24e8ba7719f427449"
EXPECTED_P19_RESULT_SHA = "6f1ad0626b8a8bda03f18e7f3435f0651af8bebf65cfd1d970a6b61a8ba52319"
EXPECTED_P19_PRELABEL_SHA = "276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8"
EXPECTED_P20_RESULT_SHA = "9ec53f29281b11002a9e22b1086d12e054392e466ea74fe82ead0187289ba303"
EXPECTED_P20_PRELABEL_SHA = "8ca358ae0f3ac96b188de9eac7bcfd6f870470873a2b7ee73b7ae76497c12734"
EXPECTED_COUNTS = (226, 1075, 3203, 4504)
EXPECTED_BASELINE = {
    "recovered_at_25": 22,
    "recovered_at_50": 40,
    "recovered_at_100": 75,
    "recovered_at_500": 159,
    "qualified_matches": 256,
    "top100_dominant_precision": 0.7645689180574315,
    "best_membership_macro_f1_all_eligible": 0.17953659309876194,
}
RADII = (0.25, 0.50, 0.75, 1.00)
MODES = (
    "nearest_cross_source_union",
    "nearest_cross_source_consensus",
    "local_fragment_support2",
    "local_source_support2",
)


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
    p.add_argument("--union-ranker", type=Path, required=True)
    p.add_argument("--union-reference-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(order).encode()).hexdigest()


def circular_diff(a: float, b: float) -> float:
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)


def load_module(path: Path, name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture_fixed_union_order(union: types.ModuleType, args: argparse.Namespace) -> list[str]:
    captured: dict[str, list[str]] = {}
    patched: list[tuple[Any, str, Callable[..., Any]]] = []
    seen_objects: set[int] = set()

    def patch_object(obj: Any) -> None:
        if id(obj) in seen_objects:
            return
        seen_objects.add(id(obj))
        original = getattr(obj, "monotone_metrics", None)
        if not callable(original):
            return

        def wrapped(*a: Any, __orig: Callable[..., Any] = original, **kw: Any) -> Any:
            order = kw.get("order")
            if order is None and len(a) >= 2:
                order = a[1]
            if isinstance(order, (list, tuple)) and order and all(isinstance(x, str) for x in order):
                candidate = list(order)
                if order_sha(candidate) == EXPECTED_ORDER_SHA:
                    captured["order"] = candidate
            return __orig(*a, **kw)

        setattr(obj, "monotone_metrics", wrapped)
        patched.append((obj, "monotone_metrics", original))

    patch_object(union)
    for value in union.__dict__.values():
        if isinstance(value, types.ModuleType):
            patch_object(value)
    patch_object(v1)

    old_argv = sys.argv[:]
    rank_output = args.output / "exact_union_rerun"
    rank_output.mkdir(parents=True, exist_ok=True)
    sys.argv = [
        str(args.union_ranker),
        "--support-source-parts", str(args.support_source_parts),
        "--candidate-payload", str(args.candidate_payload),
        "--baseline-payload", str(args.baseline_payload),
        "--scorer-parts", str(args.scorer_parts),
        "--v8-result-json", str(args.v8_result_json),
        "--p19-result-json", str(args.p19_result_json),
        "--p19-prelabel-json", str(args.p19_prelabel_json),
        "--p20-result-json", str(args.p20_result_json),
        "--p20-prelabel-json", str(args.p20_prelabel_json),
        "--output", str(rank_output),
    ]
    try:
        rc = union.main()
        require(rc in (None, 0), f"exact union ranker returned {rc}")
    finally:
        sys.argv = old_argv
        for obj, name, original in reversed(patched):
            setattr(obj, name, original)
    require("order" in captured, "failed to capture exact #839 selected order")
    require(order_sha(captured["order"]) == EXPECTED_ORDER_SHA, "captured order hash changed")
    return captured["order"]


def pair_distance(a: dict[str, Any], b: dict[str, Any], support: Any, base: Any) -> float:
    distances = []
    for year in YEARS:
        ca = a.get("centroids", {}).get(str(year))
        cb = b.get("centroids", {}).get(str(year))
        if ca is None or cb is None:
            return math.inf
        distances.append(float(support.centroid_distance(ca, cb, base)))
    return max(distances)


def build_edges(families: list[dict[str, Any]], support: Any, base: Any) -> list[tuple[float, int, int]]:
    bins: dict[int, list[int]] = defaultdict(list)
    for i, family in enumerate(families):
        c = family.get("centroids", {}).get("2022")
        require(c is not None, f"missing 2022 centroid: {family['family_id']}")
        bins[int(math.floor(float(c["sol"]))) % 360].append(i)
    edges: list[tuple[float, int, int]] = []
    seen: set[tuple[int, int]] = set()
    for i, family in enumerate(families):
        c = family["centroids"]["2022"]
        center = int(math.floor(float(c["sol"]))) % 360
        for offset in range(-7, 8):
            for j in bins.get((center + offset) % 360, []):
                if j <= i or (i, j) in seen:
                    continue
                seen.add((i, j))
                other = families[j]
                c2 = other["centroids"]["2022"]
                if circular_diff(c["sol"], c2["sol"]) > 7.0:
                    continue
                if abs(float(c["ecl_lat"]) - float(c2["ecl_lat"])) > 4.0:
                    continue
                if abs(float(c["vg"]) - float(c2["vg"])) > 4.0:
                    continue
                distance = pair_distance(family, other, support, base)
                if distance <= max(RADII):
                    edges.append((float(distance), i, j))
    return edges


def neighbors_by_index(n: int, edges: list[tuple[float, int, int]]) -> list[list[tuple[float, int]]]:
    out: list[list[tuple[float, int]]] = [[] for _ in range(n)]
    for distance, i, j in edges:
        out[i].append((distance, j))
        out[j].append((distance, i))
    for row in out:
        row.sort(key=lambda x: (x[0], x[1]))
    return out


def merged_event_ids(
    anchor_index: int,
    radius: float,
    mode: str,
    families: list[dict[str, Any]],
    sources: list[str],
    neighbors: list[list[tuple[float, int]]],
) -> list[str]:
    anchor_ids = set(map(str, families[anchor_index]["event_ids"]))
    local = [(0.0, anchor_index)] + [(d, j) for d, j in neighbors[anchor_index] if d <= radius]

    if mode in {"nearest_cross_source_union", "nearest_cross_source_consensus"}:
        selected = [anchor_index]
        for source in ("hard", "p19", "p20"):
            if source == sources[anchor_index]:
                continue
            options = [(d, j) for d, j in local if sources[j] == source]
            if options:
                selected.append(min(options, key=lambda x: (x[0], str(families[x[1]]["family_id"])))[1])
        selected = list(dict.fromkeys(selected))
        if mode == "nearest_cross_source_union":
            merged = set(anchor_ids)
            for j in selected[1:]:
                merged.update(map(str, families[j]["event_ids"]))
            return sorted(merged)
        counts: Counter[str] = Counter()
        for j in selected:
            counts.update(set(map(str, families[j]["event_ids"])))
        merged = set(anchor_ids)
        merged.update(eid for eid, count in counts.items() if count >= 2)
        return sorted(merged)

    local_indices = [j for _d, j in local]
    if mode == "local_fragment_support2":
        counts: Counter[str] = Counter()
        for j in local_indices:
            counts.update(set(map(str, families[j]["event_ids"])))
        merged = set(anchor_ids)
        merged.update(eid for eid, count in counts.items() if count >= 2)
        return sorted(merged)

    if mode == "local_source_support2":
        source_sets: dict[str, set[str]] = defaultdict(set)
        for j in local_indices:
            for eid in set(map(str, families[j]["event_ids"])):
                source_sets[eid].add(sources[j])
        merged = set(anchor_ids)
        merged.update(eid for eid, srcs in source_sets.items() if len(srcs) >= 2)
        return sorted(merged)

    raise RuntimeError(f"unknown membership mode {mode}")


def merge_variant(
    families: list[dict[str, Any]],
    sources: list[str],
    neighbors: list[list[tuple[float, int]]],
    radius: float,
    mode: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output: list[dict[str, Any]] = []
    inflations: list[float] = []
    added_counts: list[int] = []
    changed = 0
    for i, family in enumerate(families):
        old_ids = set(map(str, family["event_ids"]))
        ids = merged_event_ids(i, radius, mode, families, sources, neighbors)
        require(old_ids.issubset(ids), "membership merge removed an original member")
        item = copy.deepcopy(family)
        item["event_ids"] = ids
        item["event_count"] = len(ids)
        item["membership_merge"] = {
            "mode": mode,
            "radius": radius,
            "original_event_count": len(old_ids),
            "merged_event_count": len(ids),
        }
        output.append(item)
        added = len(ids) - len(old_ids)
        added_counts.append(added)
        inflations.append(len(ids) / max(len(old_ids), 1))
        changed += int(added > 0)
    return output, {
        "families_changed": changed,
        "total_added_memberships": int(sum(added_counts)),
        "mean_added_per_family": float(np.mean(added_counts)),
        "median_added_per_family": float(np.median(added_counts)),
        "mean_membership_inflation": float(np.mean(inflations)),
        "median_membership_inflation": float(np.median(inflations)),
        "p95_membership_inflation": float(np.quantile(inflations, 0.95)),
        "max_membership_inflation": float(max(inflations, default=1.0)),
    }


def annual_deltas(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for year in YEARS:
        y = str(year)
        out[y] = {
            name: float(current[y][name]["mean_f1"] - baseline[y][name]["mean_f1"])
            for name in ("4-9", "10-24", "25-49", "50-99", "100+", "all")
        }
    return out


def is_variant_pass(metrics: dict[str, Any], deltas: dict[str, Any], baseline_macro: float) -> bool:
    all_delta = [deltas[str(y)]["all"] for y in YEARS]
    sparse_delta = [deltas[str(y)]["4-9"] for y in YEARS]
    return bool(
        metrics["recovered_at_100"] >= 70
        and metrics["recovered_at_50"] >= 38
        and metrics["top100_dominant_precision"] >= 0.65
        and metrics["qualified_matches"] >= 220
        and metrics["best_membership_macro_f1_all_eligible"] >= baseline_macro + 0.02
        and min(all_delta) >= -0.002
        and float(np.mean(all_delta)) >= 0.005
        and min(sparse_delta) >= -0.005
        and float(np.mean(sparse_delta)) > 0.0
    )


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    for path, expected, name in (
        (args.union_reference_json, EXPECTED_UNION_RESULT_SHA, "#839 result"),
        (args.p19_result_json, EXPECTED_P19_RESULT_SHA, "P19 result"),
        (args.p19_prelabel_json, EXPECTED_P19_PRELABEL_SHA, "P19 prelabel"),
        (args.p20_result_json, EXPECTED_P20_RESULT_SHA, "P20 result"),
        (args.p20_prelabel_json, EXPECTED_P20_PRELABEL_SHA, "P20 prelabel"),
    ):
        require(sha(path) == expected, f"{name} hash changed")

    reference = json.loads(args.union_reference_json.read_text())
    require(reference["verdict"] == "PASS_URC_UNION_RANKING_FEASIBILITY", "#839 verdict changed")
    require(reference["best_cross_validated"]["order_sha256"] == EXPECTED_ORDER_SHA, "#839 order changed")
    require(reference["best_cross_validated"]["lambda"] == 0.8, "#839 lambda changed")
    require(reference["best_cross_validated"]["scale"] == 1.0, "#839 scale changed")

    union = load_module(args.union_ranker, "exact_urc_union_ranker")
    fixed_order = capture_fixed_union_order(union, args)

    p19 = json.loads(args.p19_prelabel_json.read_text())
    p20 = json.loads(args.p20_prelabel_json.read_text())
    hard = p19["hard_families"]
    p19_soft = p19["soft_families"]
    p20_soft = p20["soft_families"]
    require(hard == p20["hard_families"], "hard family universe differs between P19/P20")
    require(p19["hard_order"] == p20["hard_order"], "hard order differs between P19/P20")
    families = hard + p19_soft + p20_soft
    sources = ["hard"] * len(hard) + ["p19"] * len(p19_soft) + ["p20"] * len(p20_soft)
    require((len(hard), len(p19_soft), len(p20_soft), len(families)) == EXPECTED_COUNTS, "union counts changed")
    ids = [str(f["family_id"]) for f in families]
    require(len(ids) == len(set(ids)), "family IDs are not unique")
    require(set(fixed_order) == set(ids), "fixed #839 order does not cover exact union")

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
    scan_by_year, _calibration, hidden_labels, catalogue_sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development years changed")
    require([row["key"] for row in catalogue_sources] == list(MONTH_KEYS), "development months changed")

    # Membership construction below consumes only frozen family geometry/event IDs and source identities.
    # The hidden_labels object returned above is not passed into build_edges/merge_variant.
    edges = build_edges(families, support, base)
    neighbor_rows = neighbors_by_index(len(families), edges)

    eligible = v1.eligible_labels(hidden_labels)
    original_truths = {
        str(f["family_id"]): v1.family_truth(f, hidden_labels, eligible)
        for f in families
    }
    baseline_metrics = v1.monotone_metrics(families, fixed_order, original_truths, eligible)
    for key, expected in EXPECTED_BASELINE.items():
        value = baseline_metrics[key]
        if isinstance(expected, float):
            require(abs(float(value) - expected) < 1e-12, f"#839 metric mismatch {key}: {value}")
        else:
            require(value == expected, f"#839 metric mismatch {key}: {value}")
    baseline_annual = v1.annual_bins(families, hidden_labels)

    rows: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for mode in MODES:
        for radius in RADII:
            merged, merge_diag = merge_variant(families, sources, neighbor_rows, radius, mode)
            truths = {
                str(f["family_id"]): v1.family_truth(f, hidden_labels, eligible)
                for f in merged
            }
            metrics = v1.monotone_metrics(merged, fixed_order, truths, eligible)
            annual = v1.annual_bins(merged, hidden_labels)
            deltas = annual_deltas(annual, baseline_annual)
            passed = is_variant_pass(
                metrics, deltas, float(baseline_metrics["best_membership_macro_f1_all_eligible"])
            )
            row = {
                "mode": mode,
                "radius": radius,
                "pass": bool(passed),
                "metrics": {k: v for k, v in metrics.items() if k != "first_rank_by_label"},
                "annual_mean_f1_delta": deltas,
                "membership": merge_diag,
            }
            rows.append(row)
            key = (
                float(metrics["best_membership_macro_f1_all_eligible"] - baseline_metrics["best_membership_macro_f1_all_eligible"]),
                min(deltas["2022"]["all"], deltas["2023"]["all"]),
                float(np.mean([deltas["2022"]["4-9"], deltas["2023"]["4-9"]])),
                int(metrics["recovered_at_100"]),
                float(metrics["top100_dominant_precision"]),
                -float(merge_diag["mean_membership_inflation"]),
            )
            if best is None or key > best["key"]:
                best = {"key": key, "row": row}

    require(best is not None, "no membership variants evaluated")
    robust_modes: dict[str, list[list[float]]] = {}
    for mode in MODES:
        passing_radii = sorted(float(r["radius"]) for r in rows if r["mode"] == mode and r["pass"])
        adjacent: list[list[float]] = []
        for a, b in zip(passing_radii, passing_radii[1:]):
            if any(abs(a - x) < 1e-12 and abs(b - y) < 1e-12 for x, y in zip(RADII, RADII[1:])):
                adjacent.append([a, b])
        if adjacent:
            robust_modes[mode] = adjacent

    verdict = (
        "PASS_URC_FIXED_RANK_MEMBERSHIP_MERGE_FEASIBILITY"
        if robust_modes
        else "FAIL_URC_FIXED_RANK_MEMBERSHIP_MERGE_FEASIBILITY"
    )
    result = {
        "verdict": verdict,
        "scope": "GMN 2022/2023 target-excluded fixed-#839-ranking fragment-membership lab",
        "fixed_ranking": {
            "source": "PR #839 strict-group ExtraTrees quality regression + diversity",
            "lambda": 0.8,
            "scale": 1.0,
            "order_sha256": EXPECTED_ORDER_SHA,
            "changed": False,
        },
        "candidate_universe": {
            "hard": len(hard),
            "p19_soft": len(p19_soft),
            "p20_soft": len(p20_soft),
            "union": len(families),
        },
        "baseline": {
            "metrics": {k: v for k, v in baseline_metrics.items() if k != "first_rank_by_label"},
            "annual": baseline_annual,
        },
        "edge_count_within_1_0": len(edges),
        "grid": rows,
        "robust_modes": robust_modes,
        "best_diagnostic": best["row"],
        "integrity": {
            "candidate_existence_changed": False,
            "candidate_rank_changed": False,
            "ranking_reselected": False,
            "membership_construction_label_free": True,
            "membership_additive_only": True,
            "membership_recursive": False,
            "years": list(YEARS),
            "blind_exclusion": list(BLIND),
            "sonotaco_2013_2014_access": False,
            "maarsy_scientific_access": False,
            "target_information_access": False,
        },
        "claim_boundary": (
            "Development feasibility only. A PASS would justify freezing a single integrated URC "
            "membership rule before the one-shot SonotaCo 2013/2014 literature test; it does not "
            "revive P19/P20 or authorize final-test, external, or target access by itself."
        ),
    }
    (args.output / "urc_fixed_rank_membership_merge_lab_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    best_row = best["row"]
    (args.output / "URC_FIXED_RANK_MEMBERSHIP_MERGE_LAB_V1.md").write_text(
        "# URC fixed-rank membership merge lab v1\n\n"
        f"- verdict: `{verdict}`\n"
        f"- exact fixed #839 r100/r50: `{baseline_metrics['recovered_at_100']}/{baseline_metrics['recovered_at_50']}`\n"
        f"- best mode/radius: `{best_row['mode']}` / `{best_row['radius']}`\n"
        f"- best r100/r50: `{best_row['metrics']['recovered_at_100']}/{best_row['metrics']['recovered_at_50']}`\n"
        f"- baseline/best macro F1: `{baseline_metrics['best_membership_macro_f1_all_eligible']:.6f}` / "
        f"`{best_row['metrics']['best_membership_macro_f1_all_eligible']:.6f}`\n"
        f"- best top100 precision: `{best_row['metrics']['top100_dominant_precision']:.6f}`\n"
        f"- best qualified: `{best_row['metrics']['qualified_matches']}`\n"
        f"- passing variants: `{sum(int(r['pass']) for r in rows)}/{len(rows)}`\n"
        f"- robust modes with adjacent passing radii: `{len(robust_modes)}`\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "baseline_r100": baseline_metrics["recovered_at_100"],
        "best_mode": best_row["mode"],
        "best_radius": best_row["radius"],
        "best_r100": best_row["metrics"]["recovered_at_100"],
        "baseline_macro_f1": baseline_metrics["best_membership_macro_f1_all_eligible"],
        "best_macro_f1": best_row["metrics"]["best_membership_macro_f1_all_eligible"],
        "best_precision": best_row["metrics"]["top100_dominant_precision"],
        "best_qualified": best_row["metrics"]["qualified_matches"],
        "passing": sum(int(r["pass"]) for r in rows),
        "robust_modes": robust_modes,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
